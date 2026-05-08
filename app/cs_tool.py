"""Function tool the Foundry agent can call to delegate to Copilot Studio.

Single tool for v1 (``ask_granite_peak_orders``). The Foundry agent's
system prompt instructs the LLM to use this tool for any order/return
question, then return the result to the user.

The exact wire format depends on which Foundry path the bridge uses:

- **Direct Line fallback (Phase 2 default).** The Foundry chat backend
  ``foundry_client.handle_user_message`` invokes this Python function
  directly when the LLM emits a ``tool_calls`` chunk for it.

- **A2A primary path (Phase 3, parked).** Replaced by an
  ``A2APreviewTool`` connection configured in the Foundry portal. The
  function below stays as the working fallback.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from . import cs_directline
from .session import ChatSession

_log = logging.getLogger(__name__)


# OpenAI-style tool descriptor; both the Foundry Responses API and the
# Azure OpenAI chat completions API consume this shape.
TOOL_DESCRIPTOR: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "ask_granite_peak_orders",
        "description": (
            "Ask the Granite Peak Orders Agent (Copilot Studio) about an "
            "order, return, refund, or the return policy. Use for ANY "
            "question about a specific order id, the customer's order "
            "history, return eligibility, filing a return, refund status, "
            "or the return policy text. Returns the orders agent's reply, "
            "which you should relay verbatim or with only minor smoothing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_text": {
                    "type": "string",
                    "description": (
                        "The user's request, paraphrased so the orders "
                        "agent can act on it. Include any order id, item "
                        "SKU, or reason text the user has provided."
                    ),
                },
            },
            "required": ["user_text"],
            "additionalProperties": False,
        },
    },
}


def dispatch(sess: ChatSession, name: str, arguments_json: str) -> str:
    """Execute a tool call by name and return the textual result."""
    if name != "ask_granite_peak_orders":
        return f"(unknown tool: {name})"
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except (TypeError, ValueError):
        args = {}
    user_text = (args.get("user_text") or "").strip()
    if not user_text:
        return "(empty user_text; please rephrase)"

    try:
        return cs_directline.ask(sess, user_text) or "(orders agent did not reply)"
    except Exception as exc:  # noqa: BLE001
        _log.exception("[tool] Direct Line call failed")
        return f"(error contacting orders agent: {exc})"
