"""Thin client for the Foundry Agent Service / Azure OpenAI Responses API.

For v1 we drive the chat loop ourselves rather than going through a
Foundry-hosted Agent Application. Reasons:

- The Granite Peak system prompt + tool descriptor are short and live in
  this repo, so there's no operational benefit to hosting them inside
  Foundry's Agent Application abstraction.
- Function-tool calls need to be dispatched in our own process (the tool
  delegates to Copilot Studio Direct Line, which holds per-session state
  in this Flask app's memory).
- The Responses API wire shape is identical between Azure OpenAI model
  deployments and Foundry Agent Service projects, so swapping in a hosted
  Foundry agent later is a config-only change.

If ``FOUNDRY_PROJECT_ENDPOINT`` is not set, ``handle_user_message`` falls
back to a deterministic stub that just echoes the orders-agent reply.
That keeps Phase 2 demo-able locally before the Foundry deployment exists,
and lets the front-end + DL plumbing be developed and tested
independently.
"""
from __future__ import annotations

import json
import logging
import pathlib
import re
import time
from collections.abc import Iterator
from typing import Any

from . import config, cs_directline, cs_tool, orders_tools
from .session import ChatSession

_log = logging.getLogger(__name__)

_SYSTEM_PROMPT_PATH = pathlib.Path(__file__).parent / "system_prompt.md"


def _load_system_prompt() -> str:
    try:
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return "You are the Granite Peak Outfitters website assistant."


SYSTEM_PROMPT = _load_system_prompt()


# ---------------------------------------------------------------------------
# Optional dependency: openai SDK. Loaded lazily so the orders API + DL
# plumbing can be tested without the Azure SDK installed.
# ---------------------------------------------------------------------------


_client: Any | None = None


def _azure_openai_client() -> Any:
    global _client
    if _client is not None:
        return _client
    try:
        from openai import AzureOpenAI  # type: ignore[import-not-found]
    except ImportError as exc:  # noqa: BLE001
        raise RuntimeError(
            "openai package not installed; add `openai>=1.55` to requirements.txt"
        ) from exc

    endpoint = config.FOUNDRY_PROJECT_ENDPOINT
    if not endpoint:
        raise RuntimeError("FOUNDRY_PROJECT_ENDPOINT is not set")
    # We use AAD via DefaultAzureCredential per the user-memory rule for
    # AI services in this account. API key auth is not wired.
    try:
        from azure.identity import (  # type: ignore[import-not-found]
            DefaultAzureCredential,
            get_bearer_token_provider,
        )
    except ImportError as exc:  # noqa: BLE001
        raise RuntimeError(
            "azure-identity not installed; add `azure-identity>=1.19` to requirements.txt"
        ) from exc

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    _client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_version=config.FOUNDRY_API_VERSION,
        azure_ad_token_provider=token_provider,
    )
    return _client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def handle_user_message(sess: ChatSession, user_text: str) -> Iterator[dict[str, Any]]:
    """Yield event dicts for one user turn, suitable for SSE.

    Event shapes:
      - ``{"kind": "text", "text": str}`` — assistant content delta.
      - ``{"kind": "source", "source": "concierge"|"orders_agent"}`` — UI
        badge hint. Emitted at most once per turn, before the final text
        deltas. ``orders_agent`` means the Copilot Studio Orders Agent
        was invoked (via ``ask_granite_peak_orders``); ``concierge``
        means the Foundry concierge answered itself (with or without the
        direct orders-API tools).

    Maintains ``sess.foundry_history`` so the model has multi-turn context.
    """
    user_text = (user_text or "").strip()
    if not user_text:
        yield {"kind": "text", "text": "(empty message)"}
        return

    sess.foundry_history.append({"role": "user", "content": user_text})

    # Stub path: no Foundry / Azure OpenAI endpoint configured. Hand
    # straight to Copilot Studio so the rest of the stack is testable.
    if not config.FOUNDRY_PROJECT_ENDPOINT or not config.FOUNDRY_MODEL_DEPLOYMENT:
        _log.info(
            "[foundry] FOUNDRY_PROJECT_ENDPOINT not set; stubbing to Copilot Studio"
        )
        try:
            reply = cs_directline.ask(sess, user_text) or "(orders agent did not reply)"
        except Exception as exc:  # noqa: BLE001
            _log.exception("[foundry] stub DL call failed")
            reply = f"(error contacting orders agent: {exc})"
        sess.foundry_history.append({"role": "assistant", "content": reply})
        yield {"kind": "source", "source": "orders_agent"}
        yield {"kind": "text", "text": reply}
        return

    yield from _stream_with_azure_openai(sess)


# ---------------------------------------------------------------------------
# Real Azure OpenAI / Foundry call path
# ---------------------------------------------------------------------------


def _build_messages(sess: ChatSession) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *sess.foundry_history,
    ]


def _stream_with_azure_openai(sess: ChatSession) -> Iterator[dict[str, Any]]:
    client = _azure_openai_client()
    tools = [cs_tool.TOOL_DESCRIPTOR, *orders_tools.TOOL_DESCRIPTORS]

    cs_tool_invoked = False
    source_emitted = False

    # Tool-loop: model may emit one or more tool calls before producing the
    # final user-facing assistant message. Cap at 4 hops (per user-memory
    # note about tool-call recursion depth).
    for hop in range(4):
        messages = _build_messages(sess)
        response = client.chat.completions.create(
            model=config.FOUNDRY_MODEL_DEPLOYMENT,
            messages=messages,
            tools=tools,
            stream=True,
            temperature=0.4,
        )

        assistant_chunks: list[str] = []
        tool_call_acc: dict[int, dict[str, Any]] = {}

        for event in response:
            if not event.choices:
                continue
            delta = event.choices[0].delta
            if delta is None:
                continue
            if delta.content:
                if not source_emitted:
                    yield {
                        "kind": "source",
                        "source": "orders_agent" if cs_tool_invoked else "concierge",
                    }
                    source_emitted = True
                assistant_chunks.append(delta.content)
                yield {"kind": "text", "text": delta.content}
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index or 0
                    slot = tool_call_acc.setdefault(
                        idx,
                        {"id": "", "name": "", "arguments": ""},
                    )
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function and tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        slot["arguments"] += tc.function.arguments

        assistant_text = "".join(assistant_chunks).strip()

        if not tool_call_acc:
            # Final assistant turn — record + return.
            if assistant_text:
                sess.foundry_history.append(
                    {"role": "assistant", "content": assistant_text}
                )
            return

        # Record the assistant message that requested tool calls (so the
        # follow-up turn can attach tool results to it).
        sess.foundry_history.append(
            {
                "role": "assistant",
                "content": assistant_text or None,
                "tool_calls": [
                    {
                        "id": slot["id"],
                        "type": "function",
                        "function": {
                            "name": slot["name"],
                            "arguments": slot["arguments"] or "{}",
                        },
                    }
                    for slot in tool_call_acc.values()
                ],
            }
        )

        # Dispatch each tool call and append its result.
        for slot in tool_call_acc.values():
            name = slot["name"]
            args = slot["arguments"] or "{}"
            if name in {d["function"]["name"] for d in orders_tools.TOOL_DESCRIPTORS}:
                result = orders_tools.dispatch(name, args)
            else:
                cs_tool_invoked = True
                result = cs_tool.dispatch(sess, name, args)
            sess.foundry_history.append(
                {
                    "role": "tool",
                    "tool_call_id": slot["id"],
                    "content": result,
                }
            )
        # Loop again so the model can produce its user-facing reply.

    # Hit the hop cap.
    fallback = (
        "(I'm having trouble finishing that request — please try again or "
        "rephrase.)"
    )
    sess.foundry_history.append({"role": "assistant", "content": fallback})
    if not source_emitted:
        yield {
            "kind": "source",
            "source": "orders_agent" if cs_tool_invoked else "concierge",
        }
    yield {"kind": "text", "text": fallback}
