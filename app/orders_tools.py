"""Direct tools the Foundry agent calls against the orders backend.

Phase 2.5 addition: while the Copilot Studio MCP integration is being
unblocked end-to-end, the Foundry concierge needs working order/return
behavior for the live demo. These thin function tools call the same
orders backend (FastAPI on ACA) the CS bot would.

The CS Direct Line tool (``ask_granite_peak_orders``) remains registered
as a fallback so we can flip back to the CS-orchestrated path once the
MCP TaskDialog dispatches reliably.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import requests

from . import config

_log = logging.getLogger(__name__)

# Single-customer demo (mirror of orders_api.main.DEFAULT_CUSTOMER_ID).
DEFAULT_CUSTOMER_ID = "GP-1001"
HTTP_TIMEOUT_S = 15


def _base() -> str:
    return config.ORDERS_API_BASE_URL.rstrip("/")


# OpenAI-style descriptors. Foundry / Azure OpenAI consume this shape.
TOOL_DESCRIPTORS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_my_orders",
            "description": (
                "List the customer's recent Granite Peak orders (id, "
                "status, total, placed date)."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": (
                "Get full details for one Granite Peak order (line items, "
                "shipping, status, tracking)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order id, e.g. ORD-2026-1001.",
                    },
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": (
                "Check whether items on an order can still be returned "
                "(within the 30-day post-delivery window, not cancelled, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_return",
            "description": (
                "File a return (RMA) for a specific item on an order. "
                "Returns the RMA id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "sku": {"type": "string"},
                    "reason": {
                        "type": "string",
                        "description": "Short free-text reason from the customer.",
                    },
                },
                "required": ["order_id", "sku", "reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_return_policy",
            "description": "Return Granite Peak Outfitters' written return policy.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]


def _http(method: str, path: str, **kw: Any) -> Any:
    url = f"{_base()}{path}"
    try:
        r = requests.request(method, url, timeout=HTTP_TIMEOUT_S, **kw)
    except requests.RequestException as exc:
        _log.warning("[orders_tool] %s %s failed: %s", method, url, exc)
        return {"error": f"orders backend unreachable: {exc}"}
    if r.status_code >= 400:
        return {"error": f"orders backend {r.status_code}: {r.text[:200]}"}
    try:
        return r.json()
    except ValueError:
        return {"raw": r.text}


def dispatch(name: str, arguments_json: str) -> str:
    """Execute one of the orders tools by name; return JSON text."""
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except (TypeError, ValueError):
        args = {}

    if name == "list_my_orders":
        result = _http("GET", f"/customers/{DEFAULT_CUSTOMER_ID}/orders")
    elif name == "get_order":
        oid = (args.get("order_id") or "").strip()
        if not oid:
            return json.dumps({"error": "order_id is required"})
        result = _http("GET", f"/orders/{oid}")
    elif name == "check_return_eligibility":
        oid = (args.get("order_id") or "").strip()
        result = _http("GET", f"/orders/{oid}/return-eligibility")
    elif name == "create_return":
        result = _http(
            "POST",
            "/returns",
            json={
                "order_id": (args.get("order_id") or "").strip(),
                "customer_id": DEFAULT_CUSTOMER_ID,
                "sku": args.get("sku"),
                "reason": args.get("reason"),
            },
        )
    elif name == "get_return_policy":
        result = _http("GET", "/policies/return")
    else:
        return json.dumps({"error": f"unknown tool: {name}"})

    return json.dumps(result, ensure_ascii=False, default=str)
