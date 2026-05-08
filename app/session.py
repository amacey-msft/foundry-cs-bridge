"""Per-browser session state.

In-memory only — single-process / single-replica caveat (matches the SN
bridge precedent). Documented in README and `docs/05-troubleshooting.md`.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class ChatSession:
    """One browser session = one CS Direct Line conversation."""

    session_id: str
    user_id: str  # stable id we send as DL ``from.id``
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)

    # Direct Line state (populated by app.cs_directline.ensure_conversation)
    dl_token: str = ""
    dl_conversation_id: str = ""
    dl_base: str = ""
    dl_watermark: str = ""
    dl_sent_activity_ids: set[str] = field(default_factory=set)

    # Foundry conversation history (the Responses API is stateless, so we keep
    # a per-session message history client-side and replay it each turn).
    foundry_history: list[dict] = field(default_factory=list)

    closed: bool = False

    @property
    def correlation_id(self) -> str:
        """Reuse the session id for tracing — keeps logs grep-able."""
        return self.session_id


class SessionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_id: dict[str, ChatSession] = {}

    def get_or_create(self, session_id: str | None) -> ChatSession:
        with self._lock:
            if session_id and session_id in self._by_id:
                sess = self._by_id[session_id]
                sess.last_active_at = time.time()
                return sess
            new_id = session_id or f"gp-{uuid.uuid4().hex[:12]}"
            sess = ChatSession(session_id=new_id, user_id=new_id)
            self._by_id[new_id] = sess
            return sess

    def get(self, session_id: str) -> ChatSession | None:
        with self._lock:
            return self._by_id.get(session_id)

    def drop(self, session_id: str) -> None:
        with self._lock:
            self._by_id.pop(session_id, None)


STORE = SessionStore()
