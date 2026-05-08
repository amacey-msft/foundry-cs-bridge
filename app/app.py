"""Flask app for the Granite Peak Outfitters chat backend.

Phase 2 routes:
    GET  /healthz              liveness
    POST /api/chat             SSE stream of assistant tokens for one turn
    GET  /api/chat/session     mint or return the per-browser session id

Phase 2.5 will add the Granite Peak retail site routes (``/``, ``/product/``,
``/account``).
"""
from __future__ import annotations

import json
import logging
import uuid

from flask import Flask, Response, jsonify, request, stream_with_context

from . import config, foundry_client, session

_log = logging.getLogger("foundry_cs_bridge")

SESSION_COOKIE = "gp_session_id"


def create_app() -> Flask:
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app = Flask(__name__)

    @app.get("/healthz")
    def healthz() -> Response:
        return jsonify(
            {
                "status": "ok",
                "cs_directline_configured": bool(config.CS_DIRECTLINE_TOKEN_ENDPOINT),
                "foundry_configured": bool(config.FOUNDRY_PROJECT_ENDPOINT),
                "cs_backend": config.CS_BACKEND,
            }
        )

    @app.get("/api/chat/session")
    def chat_session() -> Response:
        existing = request.cookies.get(SESSION_COOKIE)
        sess = session.STORE.get_or_create(existing)
        resp = jsonify({"session_id": sess.session_id})
        resp.set_cookie(
            SESSION_COOKIE,
            sess.session_id,
            httponly=True,
            samesite="Lax",
            max_age=60 * 60 * 8,
        )
        return resp

    @app.post("/api/chat")
    def chat() -> Response:
        payload = request.get_json(silent=True) or {}
        user_text = (payload.get("message") or "").strip()
        if not user_text:
            return jsonify({"error": "message is required"}), 400

        session_id = (
            payload.get("session_id")
            or request.cookies.get(SESSION_COOKIE)
            or None
        )
        sess = session.STORE.get_or_create(session_id)
        correlation_id = request.headers.get("x-correlation-id") or uuid.uuid4().hex
        _log.info(
            "[chat] session=%s correlation=%s len=%d",
            sess.session_id, correlation_id, len(user_text),
        )

        @stream_with_context
        def event_stream():
            yield _sse({"type": "session", "session_id": sess.session_id})
            try:
                for chunk in foundry_client.handle_user_message(sess, user_text):
                    yield _sse({"type": "delta", "text": chunk})
                yield _sse({"type": "done"})
            except Exception as exc:  # noqa: BLE001
                _log.exception("[chat] stream failed")
                yield _sse({"type": "error", "message": str(exc)})

        resp = Response(event_stream(), mimetype="text/event-stream")
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["X-Accel-Buffering"] = "no"  # disable proxy buffering
        resp.set_cookie(
            SESSION_COOKIE,
            sess.session_id,
            httponly=True,
            samesite="Lax",
            max_age=60 * 60 * 8,
        )
        if config.ENABLE_TRACE_HEADERS:
            resp.headers["x-correlation-id"] = correlation_id
        return resp

    return app


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# WSGI entrypoint
app = create_app()


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
