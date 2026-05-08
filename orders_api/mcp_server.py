"""MCP server for Granite Peak Outfitters orders.

Exposes the orders API as a Model Context Protocol Streamable HTTP server
so Copilot Studio (via a custom connector with `mcp-streamable-1.0`
protocol) can discover and invoke the same operations the FastAPI HTTP
endpoints expose.

Mounted onto the FastAPI app at `/mcp` (see orders_api/main.py).
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .main import (
    check_return_eligibility as _check_return_eligibility,
    create_return as _create_return,
    get_order as _get_order,
    get_return_policy as _get_return_policy,
    list_customer_orders as _list_customer_orders,
)
from .main import CreateReturnRequest

DEFAULT_CUSTOMER_ID = "GP-1001"

mcp = FastMCP(
    name="granite-peak-orders",
    instructions=(
        "Tools for the Granite Peak Outfitters orders backend. Use these to "
        "look up orders, check return eligibility, create returns (RMAs), "
        "and read the official return policy."
    ),
    stateless_http=True,
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


def _dump(obj: Any) -> Any:
    """Convert a Pydantic model (or list of them) to JSON-friendly dict."""
    if isinstance(obj, list):
        return [_dump(o) for o in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return obj


@mcp.tool(
    name="list_my_orders",
    description=(
        "List all orders for the signed-in Granite Peak customer (Riley "
        "Carter, GP-1001). Returns an array of orders with order_id, "
        "status, placed_on, delivered_on, lines (sku, name, quantity, "
        "unit_price_usd) and total_usd. Call this when the user asks "
        "about their orders, what they bought, or for order history."
    ),
)
def list_my_orders() -> list[dict]:
    return _dump(_list_customer_orders(DEFAULT_CUSTOMER_ID))


@mcp.tool(
    name="get_order_status",
    description=(
        "Get the current status and full details of a specific order by "
        "id (e.g. ORD-2026-1001). Returns order_id, status, placed_on, "
        "shipped_on, delivered_on, tracking_number, carrier, lines, and "
        "total_usd."
    ),
)
def get_order_status(order_id: str) -> dict:
    return _dump(_get_order(order_id))


@mcp.tool(
    name="check_return_eligibility",
    description=(
        "Check whether a given order is eligible to be returned under the "
        "30-day return window. Returns eligible (bool), reason, "
        "days_since_delivery, and return_window_days. Always call this "
        "BEFORE create_return."
    ),
)
def check_return_eligibility(order_id: str) -> dict:
    return _dump(_check_return_eligibility(order_id))


@mcp.tool(
    name="create_return",
    description=(
        "Create a return (RMA) for a specific SKU on a specific order. "
        "Only call this AFTER check_return_eligibility returns "
        "eligible=true and the user has confirmed. Returns the new return "
        "record (return_id, status, refund_amount_usd, etc)."
    ),
)
def create_return(order_id: str, sku: str, reason: str) -> dict:
    req = CreateReturnRequest(
        order_id=order_id,
        sku=sku,
        reason=reason,
        customer_id=DEFAULT_CUSTOMER_ID,
    )
    return _dump(_create_return(req))


@mcp.tool(
    name="get_return_policy",
    description=(
        "Get Granite Peak's official return policy: return_window_days "
        "and the full policy text. Use this to answer policy questions."
    ),
)
def get_return_policy() -> dict:
    return _dump(_get_return_policy())
