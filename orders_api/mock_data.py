"""Granite Peak Outfitters seed data — pure dicts so a dev can edit by hand.

Categories used by the catalog (kept as plain strings for portability):
- ``ski``, ``snowboard``, ``boots``, ``apparel`` (winter)
- ``bike``, ``helmet``, ``accessory`` (summer)
"""
from __future__ import annotations

from datetime import date, datetime, timezone

RETURN_WINDOW_DAYS = 30

RETURN_POLICY_TEXT = (
    "Granite Peak Outfitters accepts returns within 30 days of delivery on "
    "any unworn, unused gear in original packaging. Items used outdoors "
    "(skied, ridden, washed) are accepted only if they have a manufacturing "
    "defect. Refunds issue to the original payment method within 5 business "
    "days of receiving the returned gear at our Stowe, VT warehouse. "
    "Bike frames damaged in shipping qualify for full replacement; contact "
    "support before returning. Customised or final-sale items cannot be "
    "returned."
)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

CATALOG: dict[str, dict] = {
    # --- Winter ---
    "GP-SKI-001": {
        "sku": "GP-SKI-001",
        "name": "Birch Ridge All-Mountain Skis",
        "category": "ski",
        "season": "winter",
        "price_usd": 649.00,
        "short_description": (
            "Versatile 88mm-waist all-mountain ski for groomed runs and the "
            "occasional powder day in the Greens."
        ),
        "icon": "ski",
    },
    "GP-SKI-002": {
        "sku": "GP-SKI-002",
        "name": "Notch Pass Alpine Touring Skis",
        "category": "ski",
        "season": "winter",
        "price_usd": 899.00,
        "short_description": (
            "Lightweight touring ski with skin-friendly tail notch — built "
            "for earning your turns up Smuggler's Notch."
        ),
        "icon": "ski-touring",
    },
    "GP-SKI-003": {
        "sku": "GP-SKI-003",
        "name": "Stowe Powder Skis",
        "category": "ski",
        "season": "winter",
        "price_usd": 749.00,
        "short_description": (
            "108mm-waist freeride ski for the deep days when Mansfield delivers."
        ),
        "icon": "ski-powder",
    },
    "GP-SNB-001": {
        "sku": "GP-SNB-001",
        "name": "Mansfield Freeride Snowboard",
        "category": "snowboard",
        "season": "winter",
        "price_usd": 549.00,
        "short_description": (
            "Directional twin freeride board with a poplar-birch core for "
            "all-mountain New England snow."
        ),
        "icon": "snowboard",
    },
    "GP-BOOT-001": {
        "sku": "GP-BOOT-001",
        "name": "Killington All-Mountain Ski Boots",
        "category": "boots",
        "season": "winter",
        "price_usd": 399.00,
        "short_description": (
            "100-flex all-mountain boot with heat-moldable liners — comfortable "
            "from first-chair to last-call."
        ),
        "icon": "ski-boot",
    },
    "GP-JKT-001": {
        "sku": "GP-JKT-001",
        "name": "Green Mountain Insulated Shell",
        "category": "apparel",
        "season": "winter",
        "price_usd": 329.00,
        "short_description": (
            "3-layer waterproof shell with light synthetic insulation — built "
            "for Vermont's wet, cold winters."
        ),
        "icon": "jacket",
    },
    # --- Summer ---
    "GP-BIKE-001": {
        "sku": "GP-BIKE-001",
        "name": "Burlington Trail Hardtail",
        "category": "bike",
        "season": "summer",
        "price_usd": 1899.00,
        "short_description": (
            "29er hardtail mountain bike — 120mm fork, dropper post, ready for "
            "Catamount and Kingdom Trails."
        ),
        "icon": "bike-mtb",
    },
    "GP-BIKE-002": {
        "sku": "GP-BIKE-002",
        "name": "Maple Ridge Full-Suspension MTB",
        "category": "bike",
        "season": "summer",
        "price_usd": 3499.00,
        "short_description": (
            "140/130mm trail bike with carbon front triangle — a do-it-all "
            "Green Mountain shredder."
        ),
        "icon": "bike-fs",
    },
    "GP-BIKE-003": {
        "sku": "GP-BIKE-003",
        "name": "Champlain Gravel Bike",
        "category": "bike",
        "season": "summer",
        "price_usd": 2299.00,
        "short_description": (
            "Carbon gravel bike with 700c x 45mm tires — perfect for the dirt "
            "roads around Lake Champlain."
        ),
        "icon": "bike-gravel",
    },
    "GP-BIKE-004": {
        "sku": "GP-BIKE-004",
        "name": "White River Road Bike",
        "category": "bike",
        "season": "summer",
        "price_usd": 2799.00,
        "short_description": (
            "Endurance road bike with relaxed geometry and disc brakes — "
            "made for Vermont's rolling Route 100."
        ),
        "icon": "bike-road",
    },
    "GP-HELM-001": {
        "sku": "GP-HELM-001",
        "name": "Notch Trail Helmet",
        "category": "helmet",
        "season": "summer",
        "price_usd": 179.00,
        "short_description": (
            "Trail-rated MIPS mountain bike helmet with extended rear coverage."
        ),
        "icon": "helmet",
    },
    "GP-PACK-001": {
        "sku": "GP-PACK-001",
        "name": "Catamount Hydration Pack",
        "category": "accessory",
        "season": "summer",
        "price_usd": 129.00,
        "short_description": (
            "12L hydration pack with 2L reservoir, tool roll, and a stash "
            "pocket sized for a mid-ride maple creemee."
        ),
        "icon": "pack",
    },
}


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

CUSTOMERS: dict[str, dict] = {
    "GP-1001": {
        "customer_id": "GP-1001",
        "name": "Riley Carter",
        "email": "riley.carter@example.com",
        "city": "Burlington",
        "state": "VT",
        "member_since": date(2022, 11, 4),
    },
}


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
#
# Mix of statuses + delivery dates so the demo exercises every CS topic path:
#   ORD-2026-1001 — delivered 12 days ago, eligible for return (happy path)
#   ORD-2026-1042 — delivered 22 days ago, eligible (edge of window)
#   ORD-2026-1187 — processing, not yet shipped (status query, no return)
#   ORD-2026-0998 — delivered 65 days ago, OUTSIDE return window (denial path)
#   ORD-2025-9912 — delivered 140 days ago, well outside window (denial path)
#   ORD-2026-1300 — shipped, in transit (status query, in-transit reply)


def _line(sku: str, quantity: int) -> dict:
    item = CATALOG[sku]
    return {
        "sku": sku,
        "name": item["name"],
        "quantity": quantity,
        "unit_price_usd": item["price_usd"],
    }


def _money(lines: list[dict], shipping: float, tax_rate: float = 0.06) -> tuple[float, float, float]:
    subtotal = round(sum(line["quantity"] * line["unit_price_usd"] for line in lines), 2)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + shipping + tax, 2)
    return subtotal, tax, total


def _build_order(
    order_id: str,
    placed_on: date,
    status: str,
    lines: list[dict],
    *,
    shipped_on: date | None = None,
    delivered_on: date | None = None,
    tracking_number: str | None = None,
    carrier: str | None = None,
    shipping_usd: float = 19.00,
) -> dict:
    subtotal, tax, total = _money(lines, shipping_usd)
    return {
        "order_id": order_id,
        "customer_id": "GP-1001",
        "placed_on": placed_on,
        "status": status,
        "shipped_on": shipped_on,
        "delivered_on": delivered_on,
        "tracking_number": tracking_number,
        "carrier": carrier,
        "lines": lines,
        "subtotal_usd": subtotal,
        "shipping_usd": shipping_usd,
        "tax_usd": tax,
        "total_usd": total,
    }


# Today is the demo's "now" — these dates are fixed so the demo is
# deterministic regardless of when it's run. They're intentionally in the
# past relative to ``date.today()`` so the eligibility math behaves.
_TODAY = date.today()


def _days_ago(n: int) -> date:
    from datetime import timedelta

    return _TODAY - timedelta(days=n)


ORDERS: dict[str, dict] = {
    "ORD-2026-1001": _build_order(
        "ORD-2026-1001",
        placed_on=_days_ago(20),
        status="Delivered",
        shipped_on=_days_ago(17),
        delivered_on=_days_ago(12),
        tracking_number="1Z999AA10123456784",
        carrier="UPS",
        lines=[_line("GP-SKI-001", 1), _line("GP-BOOT-001", 1)],
        shipping_usd=29.00,
    ),
    "ORD-2026-1042": _build_order(
        "ORD-2026-1042",
        placed_on=_days_ago(28),
        status="Delivered",
        shipped_on=_days_ago(25),
        delivered_on=_days_ago(22),
        tracking_number="1Z999AA10298765432",
        carrier="UPS",
        lines=[_line("GP-BIKE-002", 1)],
        shipping_usd=99.00,
    ),
    "ORD-2026-1187": _build_order(
        "ORD-2026-1187",
        placed_on=_days_ago(3),
        status="Processing",
        lines=[_line("GP-HELM-001", 1), _line("GP-PACK-001", 1)],
        shipping_usd=12.00,
    ),
    "ORD-2026-0998": _build_order(
        "ORD-2026-0998",
        placed_on=_days_ago(72),
        status="Delivered",
        shipped_on=_days_ago(70),
        delivered_on=_days_ago(65),
        tracking_number="9405511899223344556677",
        carrier="USPS",
        lines=[_line("GP-JKT-001", 1)],
        shipping_usd=14.00,
    ),
    "ORD-2025-9912": _build_order(
        "ORD-2025-9912",
        placed_on=_days_ago(150),
        status="Delivered",
        shipped_on=_days_ago(146),
        delivered_on=_days_ago(140),
        tracking_number="9405511899228899001122",
        carrier="USPS",
        lines=[_line("GP-SNB-001", 1)],
        shipping_usd=22.00,
    ),
    "ORD-2026-1300": _build_order(
        "ORD-2026-1300",
        placed_on=_days_ago(2),
        status="Shipped",
        shipped_on=_days_ago(1),
        tracking_number="1Z999AA10456789012",
        carrier="UPS",
        lines=[_line("GP-BIKE-003", 1), _line("GP-HELM-001", 1)],
        shipping_usd=99.00,
    ),
}


# ---------------------------------------------------------------------------
# Returns — start empty; the API populates this dict as customers create them.
# Pre-seed one historical return so the "track refund" path has something to
# query against on a fresh boot.
# ---------------------------------------------------------------------------

_seeded_return_created = datetime.now(timezone.utc).replace(microsecond=0)
RETURNS: dict[str, dict] = {
    "RMA-20260420-A7B3C9": {
        "return_id": "RMA-20260420-A7B3C9",
        "order_id": "ORD-2026-1042",
        "customer_id": "GP-1001",
        "sku": "GP-BIKE-002",
        "reason": "Frame size too large — need a medium instead of large.",
        "status": "Approved",
        "refund_status": "Issued",
        "refund_amount_usd": 3499.00,
        "created_on": _seeded_return_created,
        "updated_on": _seeded_return_created,
    },
}
