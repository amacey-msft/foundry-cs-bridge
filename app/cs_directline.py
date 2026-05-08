"""Per-browser-session Direct Line client for the Granite Peak Orders agent.

Adapted from ``copilot-studio-acs-voice/app/directline.py``. Two patterns
kept verbatim:

1. **Regional DL gateway**. Copilot Studio issues tokens bound to a regional
   Direct Line endpoint (e.g. ``unitedstates.directline.botframework.com``).
   The only reliable way to find the region is to read ``streamUrl`` from
   the response of ``POST /v3/directline/conversations`` and parse the host
   from it. Hitting the global ``directline.botframework.com`` with a
   CS-issued token returns 404.

2. **Activity-id echo filter**. Direct Line rewrites ``from.id`` on user
   activities to its own minted user id, so we cannot filter our own
   messages by ``from.id``. We track the activity ids we posted and discard
   matching ids from the poll instead.

Differences from the acs-voice port:

- This is text-only (no STT/TTS), so ``poll_replies`` returns plain
  message activities and the caller renders ``text``.
- One DL conversation per browser session (not per phone call).
- Slightly tighter timeouts (text turns are quicker than voice).
"""
from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import requests

from . import config
from .session import ChatSession


_log = logging.getLogger(__name__)

_DL_BASE_DEFAULT = "https://directline.botframework.com/v3/directline"


def _dl_base_from_stream_url(stream_url: str) -> str:
    if not stream_url:
        return _DL_BASE_DEFAULT
    try:
        host = urlparse(stream_url).netloc
        return f"https://{host}/v3/directline" if host else _DL_BASE_DEFAULT
    except Exception:  # noqa: BLE001
        return _DL_BASE_DEFAULT


def _mint_token() -> str:
    config.assert_directline_configured()
    r = requests.get(config.CS_DIRECTLINE_TOKEN_ENDPOINT, timeout=15)
    r.raise_for_status()
    payload = r.json()
    token = payload.get("token") or ""
    if not token:
        raise RuntimeError(f"CS token endpoint returned no token: {payload!r}")
    return token


def _start_conversation(token: str, user_id: str) -> tuple[str, str]:
    r = requests.post(
        f"{_DL_BASE_DEFAULT}/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"user": {"id": user_id}},
        timeout=15,
    )
    r.raise_for_status()
    payload = r.json()
    conv_id = payload["conversationId"]
    real_base = _dl_base_from_stream_url(payload.get("streamUrl") or "")
    return conv_id, real_base


def ensure_conversation(sess: ChatSession) -> None:
    if sess.dl_token and sess.dl_conversation_id and sess.dl_base:
        return
    token = _mint_token()
    conv_id, base = _start_conversation(token, sess.user_id)
    sess.dl_token = token
    sess.dl_conversation_id = conv_id
    sess.dl_base = base
    _log.info(
        "[dl] conversation started session=%s conv=%s base=%s",
        sess.session_id, conv_id, base,
    )


def post_user_text(sess: ChatSession, text: str) -> None:
    ensure_conversation(sess)
    r = requests.post(
        f"{sess.dl_base}/conversations/{sess.dl_conversation_id}/activities",
        headers={
            "Authorization": f"Bearer {sess.dl_token}",
            "Content-Type": "application/json",
        },
        json={"type": "message", "from": {"id": sess.user_id}, "text": text},
        timeout=15,
    )
    r.raise_for_status()
    try:
        posted_id = (r.json() or {}).get("id") or ""
    except ValueError:
        posted_id = ""
    if posted_id:
        sess.dl_sent_activity_ids.add(posted_id)
    _log.info("[dl] posted user text session=%s len=%d", sess.session_id, len(text))


def poll_replies(sess: ChatSession) -> list[dict[str, Any]]:
    """Drain the next batch of bot activities for one user turn."""
    deadline = time.time() + config.DIRECTLINE_TURN_TIMEOUT_S
    quiet_deadline = time.time() + config.DIRECTLINE_QUIET_PERIOD_S
    collected: list[dict[str, Any]] = []

    while time.time() < deadline and not sess.closed:
        url = f"{sess.dl_base}/conversations/{sess.dl_conversation_id}/activities"
        params = {"watermark": sess.dl_watermark} if sess.dl_watermark else {}
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {sess.dl_token}"},
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        body = r.json()
        progress = False
        for act in body.get("activities") or []:
            act_id = act.get("id") or ""
            if act_id and act_id in sess.dl_sent_activity_ids:
                sess.dl_sent_activity_ids.discard(act_id)
                continue
            if act.get("type") not in {"message", "typing"}:
                continue
            collected.append(act)
            progress = True
        new_watermark = body.get("watermark")
        if new_watermark is not None:
            sess.dl_watermark = str(new_watermark)
        if progress:
            quiet_deadline = time.time() + config.DIRECTLINE_QUIET_PERIOD_S
        if time.time() >= quiet_deadline and collected:
            break
        time.sleep(config.DIRECTLINE_POLL_INTERVAL_S)

    return collected


def ask(sess: ChatSession, user_text: str) -> str:
    """Convenience: post one user message, return concatenated bot reply text."""
    post_user_text(sess, user_text)
    activities = poll_replies(sess)
    parts: list[str] = []
    for act in activities:
        if act.get("type") == "message" and act.get("text"):
            parts.append(str(act["text"]))
    return "\n\n".join(parts).strip()
