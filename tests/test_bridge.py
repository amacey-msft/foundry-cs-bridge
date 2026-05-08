"""Unit tests for the bridge layer.

Covers:
- /healthz returns config flags
- /api/chat in stub mode (no Foundry, no DL configured) returns a 200 SSE
  stream with deterministic structure.
- Session cookie is set + reused.
- cs_directline.ask() is patched so the test doesn't hit the network.
"""
from __future__ import annotations

import json

import pytest

import app.app as bridge_app
from app import cs_directline


@pytest.fixture
def client():
    return bridge_app.app.test_client()


def _parse_sse(data: bytes) -> list[dict]:
    events: list[dict] = []
    for line in data.decode().splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: "):]))
    return events


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert body["cs_backend"] == "directline"


def test_chat_stub_mode_yields_dl_reply(client, monkeypatch):
    monkeypatch.setattr(
        cs_directline, "ask", lambda sess, text: "(stubbed orders reply)"
    )
    # Force the stub branch in foundry_client regardless of .env state.
    from app import config, foundry_client
    monkeypatch.setattr(config, "FOUNDRY_PROJECT_ENDPOINT", "")
    monkeypatch.setattr(foundry_client.config, "FOUNDRY_PROJECT_ENDPOINT", "")

    r = client.post("/api/chat", json={"message": "track ORD-2026-1001"})
    assert r.status_code == 200
    events = _parse_sse(r.data)

    types = [e["type"] for e in events]
    assert "session" in types
    assert "delta" in types
    assert "done" in types
    deltas = [e["text"] for e in events if e["type"] == "delta"]
    assert "(stubbed orders reply)" in "".join(deltas)


def test_chat_session_cookie_reused(client):
    r1 = client.get("/api/chat/session")
    sid1 = r1.get_json()["session_id"]
    client.set_cookie("gp_session_id", sid1, domain="localhost")
    r2 = client.get("/api/chat/session")
    sid2 = r2.get_json()["session_id"]
    assert sid1 == sid2


def test_chat_empty_message_400(client):
    r = client.post("/api/chat", json={"message": "   "})
    assert r.status_code == 400
