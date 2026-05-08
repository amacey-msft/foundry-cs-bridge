"""Environment-driven config for the foundry-cs-bridge app.

Pattern mirrored from ``copilot-studio-acs-voice/app/config.py`` and the SN
bridge: read ``os.environ`` once at import, expose plain module-level
constants. Uses python-dotenv so a local ``.env`` is auto-loaded in dev.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return default


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


# --- Copilot Studio (Direct Line) ---------------------------------------
CS_DIRECTLINE_TOKEN_ENDPOINT = os.environ.get("CS_DIRECTLINE_TOKEN_ENDPOINT", "").strip()
CS_AGENT_SCHEMA_NAME = os.environ.get("CS_AGENT_SCHEMA_NAME", "").strip()
CS_AGENT_APP_ID = os.environ.get("CS_AGENT_APP_ID", "").strip()
CS_ENVIRONMENT_API_HOST = os.environ.get("CS_ENVIRONMENT_API_HOST", "").strip()

# Polling tunables. Tighter than acs-voice because text turns finish faster
# than voice ones; we want the chat to feel snappy.
DIRECTLINE_TURN_TIMEOUT_S = _float("DIRECTLINE_TURN_TIMEOUT_S", 25.0)
DIRECTLINE_QUIET_PERIOD_S = _float("DIRECTLINE_QUIET_PERIOD_S", 1.5)
DIRECTLINE_POLL_INTERVAL_S = _float("DIRECTLINE_POLL_INTERVAL_S", 0.5)

# --- Mock orders API (used by Foundry tools, not by CS) -----------------
ORDERS_API_BASE_URL = os.environ.get(
    "ORDERS_API_BASE_URL", "http://localhost:8000"
).rstrip("/")

# --- Foundry Agent Service ----------------------------------------------
FOUNDRY_PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "").strip()
FOUNDRY_AGENT_ID = os.environ.get("FOUNDRY_AGENT_ID", "").strip()
FOUNDRY_MODEL_DEPLOYMENT = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4.1-mini").strip()

# --- Backend selector --------------------------------------------------
# "directline" = Phase 2 default (Foundry chat backend calls CS over DL).
# "a2a"        = Phase 3 primary path (left as a no-op stub for v1).
CS_BACKEND = os.environ.get("CS_BACKEND", "directline").strip().lower()

# --- Flask app ---------------------------------------------------------
PORT = _int("PORT", 5000)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper().strip()
BRIDGE_PUBLIC_URL = os.environ.get("BRIDGE_PUBLIC_URL", "").strip().rstrip("/")

# --- Tracing ------------------------------------------------------------
ENABLE_TRACE_HEADERS = _bool("ENABLE_TRACE_HEADERS", True)

# --- App Insights -------------------------------------------------------
APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get(
    "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
).strip()


def assert_directline_configured() -> None:
    if not CS_DIRECTLINE_TOKEN_ENDPOINT:
        raise RuntimeError(
            "CS_DIRECTLINE_TOKEN_ENDPOINT is not set. Provision the Granite "
            "Peak Orders agent first (docs/02-cs-orders-setup.md), then "
            "populate .env."
        )
