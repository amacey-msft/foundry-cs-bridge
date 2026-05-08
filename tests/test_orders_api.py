"""Smoke tests for the Granite Peak orders API.

Run with: ``pytest`` from repo root (after ``pip install -r requirements-dev.txt``).
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from orders_api.main import app

client = TestClient(app)


def test_healthz() -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_catalog_winter_filter() -> None:
    r = client.get("/catalog", params={"season": "winter"})
    assert r.status_code == 200
    skus = {item["sku"] for item in r.json()}
    assert "GP-SKI-001" in skus
    assert "GP-BIKE-001" not in skus


def test_get_order_known() -> None:
    r = client.get("/orders/ORD-2026-1001")
    assert r.status_code == 200
    body = r.json()
    assert body["customer_id"] == "GP-1001"
    assert body["status"] == "Delivered"
    assert any(line["sku"] == "GP-SKI-001" for line in body["lines"])


def test_get_order_unknown_404() -> None:
    r = client.get("/orders/BAD-ID")
    assert r.status_code == 404


def test_eligibility_in_window() -> None:
    r = client.get("/orders/ORD-2026-1001/return-eligibility")
    assert r.status_code == 200
    body = r.json()
    assert body["eligible"] is True
    assert body["return_window_days"] == 30


def test_eligibility_outside_window() -> None:
    r = client.get("/orders/ORD-2026-0998/return-eligibility")
    assert r.status_code == 200
    body = r.json()
    assert body["eligible"] is False
    assert body["days_since_delivery"] is not None and body["days_since_delivery"] > 30


def test_eligibility_processing_order() -> None:
    r = client.get("/orders/ORD-2026-1187/return-eligibility")
    assert r.status_code == 200
    assert r.json()["eligible"] is False


def test_create_return_happy() -> None:
    r = client.post(
        "/returns",
        json={
            "order_id": "ORD-2026-1001",
            "sku": "GP-BOOT-001",
            "reason": "Boots run small",
            "customer_id": "GP-1001",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["return_id"].startswith("RMA-")
    assert body["status"] == "Pending"
    assert body["refund_amount_usd"] == 399.0


def test_create_return_outside_window_400() -> None:
    r = client.post(
        "/returns",
        json={
            "order_id": "ORD-2026-0998",
            "sku": "GP-JKT-001",
            "reason": "Wrong color",
            "customer_id": "GP-1001",
        },
    )
    assert r.status_code == 400


def test_create_return_sku_not_in_order_400() -> None:
    r = client.post(
        "/returns",
        json={
            "order_id": "ORD-2026-1001",
            "sku": "GP-BIKE-001",
            "reason": "x",
            "customer_id": "GP-1001",
        },
    )
    assert r.status_code == 400


def test_return_policy() -> None:
    r = client.get("/policies/return")
    assert r.status_code == 200
    body = r.json()
    assert body["return_window_days"] == 30
    assert "30 days" in body["text"]


def test_list_customer_orders() -> None:
    r = client.get("/customers/GP-1001/orders")
    assert r.status_code == 200
    assert len(r.json()) >= 5
