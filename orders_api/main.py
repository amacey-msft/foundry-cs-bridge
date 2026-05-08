"""Granite Peak Outfitters — mock orders backend.

Self-contained FastAPI app exposing a small read/write API used by the
Copilot Studio orders agent's HTTP Request tools, the Foundry chat backend,
and the Granite Peak retail web UI. No database — in-memory dict store
seeded at import time so the demo is deterministic and resettable.

Customer model (Phase 1 v1):
- Single demo customer ``GP-1001`` ("Riley Carter", Burlington VT).
- All seeded orders / returns belong to that customer.
- Order ids are passed by the user; customer scoping is implied
  (the CS agent always asks about Riley's orders for v1).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Iterable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .mock_data import (
    CATALOG,
    CUSTOMERS,
    ORDERS,
    RETURNS,
    RETURN_POLICY_TEXT,
    RETURN_WINDOW_DAYS,
)

app = FastAPI(
    title="Granite Peak Outfitters — Orders API (mock)",
    version="0.1.0",
    description=(
        "Mock backend for the foundry-cs-bridge demo. Serves catalog, "
        "customers, orders, returns, and return policy data for both the "
        "Copilot Studio agent (via HTTP Request tools) and the Granite "
        "Peak web front end."
    ),
)


# ---------------------------------------------------------------------------
# Response models (kept simple — these double as agent-friendly JSON shapes)
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    version: str


class CatalogItem(BaseModel):
    sku: str
    name: str
    category: str  # "ski" | "snowboard" | "boots" | "apparel" | "bike" | "helmet" | "accessory"
    season: str  # "winter" | "summer" | "all"
    price_usd: float
    short_description: str
    icon: str  # logical name; the web UI renders inline SVG by icon


class Customer(BaseModel):
    customer_id: str
    name: str
    email: str
    city: str
    state: str
    member_since: date


class OrderLine(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price_usd: float


class Order(BaseModel):
    order_id: str
    customer_id: str
    placed_on: date
    status: str  # "Processing" | "Shipped" | "Delivered" | "Cancelled"
    shipped_on: date | None = None
    delivered_on: date | None = None
    tracking_number: str | None = None
    carrier: str | None = None
    lines: list[OrderLine]
    subtotal_usd: float
    shipping_usd: float
    tax_usd: float
    total_usd: float

    @property
    def is_returnable(self) -> bool:
        if self.delivered_on is None:
            return False
        days = (date.today() - self.delivered_on).days
        return days <= RETURN_WINDOW_DAYS


class ReturnRecord(BaseModel):
    return_id: str
    order_id: str
    customer_id: str
    sku: str
    reason: str
    status: str  # "Pending" | "Approved" | "Refunded" | "Rejected"
    refund_status: str  # "NotStarted" | "Issued" | "FailedReview"
    refund_amount_usd: float
    created_on: datetime
    updated_on: datetime


class CreateReturnRequest(BaseModel):
    order_id: str = Field(..., description="Granite Peak order id, e.g. ORD-2026-1001")
    sku: str = Field(..., description="SKU from the order to return")
    reason: str = Field(..., description="Free-text reason from the customer")
    customer_id: str = Field(
        default="GP-1001",
        description="Customer id; defaults to the demo customer GP-1001.",
    )


class ReturnEligibilityResponse(BaseModel):
    order_id: str
    eligible: bool
    reason: str
    days_since_delivery: int | None
    return_window_days: int


class ReturnPolicy(BaseModel):
    return_window_days: int
    text: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _orders_for(customer_id: str) -> list[Order]:
    return [Order(**o) for o in ORDERS.values() if o["customer_id"] == customer_id]


def _returns_for(customer_id: str) -> list[ReturnRecord]:
    return [ReturnRecord(**r) for r in RETURNS.values() if r["customer_id"] == customer_id]


def _ensure_order(order_id: str) -> dict:
    raw = ORDERS.get(order_id.upper())
    if not raw:
        raise HTTPException(status_code=404, detail=f"Order {order_id!r} not found")
    return raw


def _ensure_customer(customer_id: str) -> dict:
    raw = CUSTOMERS.get(customer_id.upper())
    if not raw:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id!r} not found")
    return raw


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthz() -> HealthResponse:
    return HealthResponse(status="ok", version=app.version)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@app.get("/catalog", response_model=list[CatalogItem], tags=["catalog"])
def list_catalog(
    season: str | None = Query(default=None, pattern="^(winter|summer|all)$"),
    category: str | None = Query(default=None),
) -> list[CatalogItem]:
    items: Iterable[dict] = CATALOG.values()
    if season:
        items = (i for i in items if i["season"] in (season, "all"))
    if category:
        items = (i for i in items if i["category"].lower() == category.lower())
    return [CatalogItem(**i) for i in items]


@app.get("/catalog/{sku}", response_model=CatalogItem, tags=["catalog"])
def get_catalog_item(sku: str) -> CatalogItem:
    raw = CATALOG.get(sku.upper())
    if not raw:
        raise HTTPException(status_code=404, detail=f"SKU {sku!r} not found")
    return CatalogItem(**raw)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
def get_customer(customer_id: str) -> Customer:
    return Customer(**_ensure_customer(customer_id))


@app.get(
    "/customers/{customer_id}/orders",
    response_model=list[Order],
    tags=["customers"],
)
def list_customer_orders(customer_id: str) -> list[Order]:
    _ensure_customer(customer_id)
    return _orders_for(customer_id.upper())


@app.get(
    "/customers/{customer_id}/returns",
    response_model=list[ReturnRecord],
    tags=["customers"],
)
def list_customer_returns(customer_id: str) -> list[ReturnRecord]:
    _ensure_customer(customer_id)
    return _returns_for(customer_id.upper())


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


@app.get("/orders/{order_id}", response_model=Order, tags=["orders"])
def get_order(order_id: str) -> Order:
    return Order(**_ensure_order(order_id))


@app.get(
    "/orders/{order_id}/return-eligibility",
    response_model=ReturnEligibilityResponse,
    tags=["orders"],
)
def check_return_eligibility(order_id: str) -> ReturnEligibilityResponse:
    raw = _ensure_order(order_id)
    order = Order(**raw)
    if order.status == "Cancelled":
        return ReturnEligibilityResponse(
            order_id=order.order_id,
            eligible=False,
            reason="Order was cancelled and never delivered.",
            days_since_delivery=None,
            return_window_days=RETURN_WINDOW_DAYS,
        )
    if order.delivered_on is None:
        return ReturnEligibilityResponse(
            order_id=order.order_id,
            eligible=False,
            reason="Order has not been delivered yet.",
            days_since_delivery=None,
            return_window_days=RETURN_WINDOW_DAYS,
        )
    days = (date.today() - order.delivered_on).days
    if days > RETURN_WINDOW_DAYS:
        return ReturnEligibilityResponse(
            order_id=order.order_id,
            eligible=False,
            reason=(
                f"Outside the {RETURN_WINDOW_DAYS}-day return window "
                f"({days} days since delivery)."
            ),
            days_since_delivery=days,
            return_window_days=RETURN_WINDOW_DAYS,
        )
    return ReturnEligibilityResponse(
        order_id=order.order_id,
        eligible=True,
        reason=f"Within the {RETURN_WINDOW_DAYS}-day window.",
        days_since_delivery=days,
        return_window_days=RETURN_WINDOW_DAYS,
    )


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------


@app.post("/returns", response_model=ReturnRecord, status_code=201, tags=["returns"])
def create_return(req: CreateReturnRequest) -> ReturnRecord:
    raw = _ensure_order(req.order_id)
    order = Order(**raw)
    if order.customer_id != req.customer_id.upper():
        raise HTTPException(
            status_code=403,
            detail=(
                f"Order {order.order_id} does not belong to customer {req.customer_id}."
            ),
        )
    if not any(line.sku.upper() == req.sku.upper() for line in order.lines):
        raise HTTPException(
            status_code=400,
            detail=f"SKU {req.sku!r} is not part of order {order.order_id}.",
        )
    eligibility = check_return_eligibility(req.order_id)
    if not eligibility.eligible:
        raise HTTPException(status_code=400, detail=eligibility.reason)
    matching_line = next(line for line in order.lines if line.sku.upper() == req.sku.upper())
    now = datetime.now(timezone.utc)
    return_id = f"RMA-{now.strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    record = {
        "return_id": return_id,
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "sku": matching_line.sku,
        "reason": req.reason,
        "status": "Pending",
        "refund_status": "NotStarted",
        "refund_amount_usd": round(
            matching_line.unit_price_usd * matching_line.quantity, 2
        ),
        "created_on": now,
        "updated_on": now,
    }
    RETURNS[return_id] = record
    return ReturnRecord(**record)


@app.get("/returns/{return_id}", response_model=ReturnRecord, tags=["returns"])
def get_return(return_id: str) -> ReturnRecord:
    raw = RETURNS.get(return_id.upper())
    if not raw:
        raise HTTPException(status_code=404, detail=f"Return {return_id!r} not found")
    return ReturnRecord(**raw)


@app.get("/returns", response_model=list[ReturnRecord], tags=["returns"])
def list_returns(
    customer_id: str | None = Query(default=None),
    order_id: str | None = Query(default=None),
) -> list[ReturnRecord]:
    items: Iterable[dict] = RETURNS.values()
    if customer_id:
        items = (r for r in items if r["customer_id"] == customer_id.upper())
    if order_id:
        items = (r for r in items if r["order_id"] == order_id.upper())
    return [ReturnRecord(**r) for r in items]


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------


@app.get("/policies/return", response_model=ReturnPolicy, tags=["policies"])
def get_return_policy() -> ReturnPolicy:
    return ReturnPolicy(return_window_days=RETURN_WINDOW_DAYS, text=RETURN_POLICY_TEXT)
