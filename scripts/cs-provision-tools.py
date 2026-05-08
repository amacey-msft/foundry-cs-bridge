"""Provision Granite Peak Orders HTTP tools as Copilot Studio botcomponents.

Each tool is an AdaptiveDialog with modelDescription + inputType/outputType so
the generative orchestrator can dispatch it. The dialog body is a single
HttpRequestAction calling the Granite Peak orders mock API exposed through a
public devtunnel URL (ORDERS_API_BASE_URL). Customer id GP-1001 (Riley Carter)
is hard-coded per the demo persona.

Idempotent: PATCH if the schemaname already exists, POST otherwise.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from textwrap import dedent

import requests

ORG_URL = os.environ.get("DATAVERSE_ORG_URL", "https://orga5bae564.crm.dynamics.com").rstrip("/")
API = f"{ORG_URL}/api/data/v9.2"
SOLUTION = os.environ.get("CS_SOLUTION", "GenericOrderManagementSystem")

BOT_ID = "b6159d14-2485-4369-b65c-dafde20997d3"
BOT_SCHEMA = "awm_granitepeakorders"
ORDERS_API_BASE_URL = os.environ.get(
    "ORDERS_API_BASE_URL",
    "https://t31qztdv-8000.use.devtunnels.ms",
).rstrip("/")
CUSTOMER_ID = os.environ.get("DEMO_CUSTOMER_ID", "GP-1001")


def az_token(resource: str) -> str:
    out = subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"],
        shell=True,
        text=True,
    ).strip()
    if not out:
        raise SystemExit("az account get-access-token returned empty")
    return out


def headers(token: str, *, prefer_return: bool = True) -> dict:
    h = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "MSCRM.SolutionUniqueName": SOLUTION,
    }
    if prefer_return:
        h["Prefer"] = "return=representation"
    return h


def find_component(token: str, schemaname: str) -> dict | None:
    r = requests.get(
        f"{API}/botcomponents",
        params={"$filter": f"schemaname eq '{schemaname}'", "$select": "botcomponentid,schemaname,name"},
        headers=headers(token, prefer_return=False),
        timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("value", [])
    return items[0] if items else None


# ---------------------------------------------------------------------------
# Tool YAML builders
# ---------------------------------------------------------------------------

def yaml_list_my_orders() -> str:
    return dedent(f"""\
        kind: AdaptiveDialog
        modelDescription: |-
          List all orders for the signed-in customer (Riley Carter, GP-1001).
          Returns an array of orders with order_id, status, ordered_on,
          delivered_on, lines (sku, name, quantity, unit_price_usd) and
          total_usd. Call this when the user asks about their orders, what
          they bought, or to see order history.
        beginDialog:
          kind: OnRecognizedIntent
          id: main
          intent: {{}}
          actions:
            - kind: HttpRequestAction
              id: httpListOrders
              method: Get
              url: {ORDERS_API_BASE_URL}/customers/{CUSTOMER_ID}/orders
              response: Topic.orders
              responseSchema: Any
            - kind: SendActivity
              id: emitOrders
              activity: =JSON(Topic.orders)
        inputType:
          properties: {{}}
        outputType: {{}}
        """)


def yaml_get_order_status() -> str:
    return dedent(f"""\
        kind: AdaptiveDialog
        modelDescription: |-
          Get the current status and full details of a specific order by id
          (e.g. ORD-2026-1001). Returns order_id, status, ordered_on,
          delivered_on, lines, total_usd, shipping_address.
        inputs:
          - kind: AutomaticTaskInput
            propertyName: orderId
            description: The order id, e.g. ORD-2026-1001.
            shouldPromptUser: true
        beginDialog:
          kind: OnRecognizedIntent
          id: main
          intent: {{}}
          actions:
            - kind: HttpRequestAction
              id: httpGetOrder
              method: Get
              url: =Concatenate("{ORDERS_API_BASE_URL}/orders/", Topic.orderId)
              response: Topic.order
              responseSchema: Any
            - kind: SendActivity
              id: emitOrder
              activity: =JSON(Topic.order)
        inputType:
          properties:
            orderId:
              displayName: orderId
              description: The order id, e.g. ORD-2026-1001.
              type: String
        outputType: {{}}
        """)


def yaml_check_return_eligibility() -> str:
    return dedent(f"""\
        kind: AdaptiveDialog
        modelDescription: |-
          Check whether a given order is eligible to be returned under the
          30-day return window. Returns eligible (bool), reason,
          days_since_delivery, return_window_days. Always call this BEFORE
          create_return.
        inputs:
          - kind: AutomaticTaskInput
            propertyName: orderId
            description: The order id to check.
            shouldPromptUser: true
        beginDialog:
          kind: OnRecognizedIntent
          id: main
          intent: {{}}
          actions:
            - kind: HttpRequestAction
              id: httpCheckEligibility
              method: Get
              url: =Concatenate("{ORDERS_API_BASE_URL}/orders/", Topic.orderId, "/return-eligibility")
              response: Topic.eligibility
              responseSchema: Any
            - kind: SendActivity
              id: emitEligibility
              activity: =JSON(Topic.eligibility)
        inputType:
          properties:
            orderId:
              displayName: orderId
              description: The order id to check.
              type: String
        outputType: {{}}
        """)


def yaml_create_return() -> str:
    # Build POST body via Power Fx JSON() over a record literal — much
    # safer than Concatenate with hand-escaped quotes.
    body_expr = (
        '=JSON({customer_id:"' + CUSTOMER_ID + '",'
        ' order_id: Topic.orderId,'
        ' sku: Topic.sku,'
        ' reason: Topic.reason})'
    )
    return dedent(f"""\
        kind: AdaptiveDialog
        modelDescription: |-
          Create a return (RMA) for a specific SKU on a specific order. Only
          call this AFTER check_return_eligibility returns eligible=true and
          the user has confirmed. Returns the new return record (return_id,
          status, refund_amount_usd, etc).
        inputs:
          - kind: AutomaticTaskInput
            propertyName: orderId
            description: The order id the return is against.
            shouldPromptUser: true
          - kind: AutomaticTaskInput
            propertyName: sku
            description: The SKU from that order being returned.
            shouldPromptUser: true
          - kind: AutomaticTaskInput
            propertyName: reason
            description: Short free-text reason for the return.
            shouldPromptUser: true
        beginDialog:
          kind: OnRecognizedIntent
          id: main
          intent: {{}}
          actions:
            - kind: SetVariable
              id: setBody
              variable: Topic.RequestBody
              value: {body_expr}
            - kind: HttpRequestAction
              id: httpCreateReturn
              method: Post
              url: {ORDERS_API_BASE_URL}/returns
              body:
                kind: RawRequestContent
                contentType: application/json
                content: =Topic.RequestBody
              response: Topic.return
              responseSchema: Any
            - kind: SendActivity
              id: emitReturn
              activity: =JSON(Topic.return)
        inputType:
          properties:
            orderId:
              displayName: orderId
              description: The order id.
              type: String
            sku:
              displayName: sku
              description: The SKU being returned.
              type: String
            reason:
              displayName: reason
              description: Reason for the return.
              type: String
        outputType: {{}}
        """)


def yaml_get_return_policy() -> str:
    return dedent(f"""\
        kind: AdaptiveDialog
        modelDescription: |-
          Get Granite Peak's official return policy: window_days,
          restocking_fee_pct, eligible_categories, exclusions, and a
          summary string. Use this to answer policy questions.
        beginDialog:
          kind: OnRecognizedIntent
          id: main
          intent: {{}}
          actions:
            - kind: HttpRequestAction
              id: httpGetPolicy
              method: Get
              url: {ORDERS_API_BASE_URL}/policies/return
              response: Topic.policy
              responseSchema: Any
            - kind: SendActivity
              id: emitPolicy
              activity: =JSON(Topic.policy)
        inputType:
          properties: {{}}
        outputType: {{}}
        """)


TOOLS = [
    ("ListMyOrders", "Granite Peak - List My Orders", yaml_list_my_orders),
    ("GetOrderStatus", "Granite Peak - Get Order Status", yaml_get_order_status),
    ("CheckReturnEligibility", "Granite Peak - Check Return Eligibility", yaml_check_return_eligibility),
    ("CreateReturn", "Granite Peak - Create Return", yaml_create_return),
    ("GetReturnPolicy", "Granite Peak - Get Return Policy", yaml_get_return_policy),
]


def upsert_tool(token: str, action_name: str, display_name: str, data_yaml: str) -> str:
    schemaname = f"{BOT_SCHEMA}.topic.{action_name}"
    existing = find_component(token, schemaname)
    body = {
        "name": display_name,
        "componenttype": 9,
        "schemaname": schemaname,
        "data": data_yaml,
    }
    if existing:
        cid = existing["botcomponentid"]
        r = requests.patch(
            f"{API}/botcomponents({cid})",
            data=json.dumps({"name": display_name, "data": data_yaml}),
            headers=headers(token, prefer_return=False),
            timeout=60,
        )
        r.raise_for_status()
        print(f"  PATCH ok -> {cid}")
        return cid
    body["botcomponentid"] = str(uuid.uuid4())
    body["parentbotid@odata.bind"] = f"/bots({BOT_ID})"
    r = requests.post(
        f"{API}/botcomponents",
        data=json.dumps(body),
        headers=headers(token),
        timeout=60,
    )
    if r.status_code >= 300:
        print(f"  POST FAILED {r.status_code}: {r.text[:1500]}", file=sys.stderr)
        r.raise_for_status()
    cid = r.json().get("botcomponentid", body["botcomponentid"])
    print(f"  POST ok -> {cid}")
    return cid


def main() -> int:
    print(f"Dataverse: {ORG_URL}")
    print(f"Bot:       {BOT_SCHEMA} ({BOT_ID})")
    print(f"Orders API: {ORDERS_API_BASE_URL}")
    token = az_token(ORG_URL)
    for action_name, display_name, builder in TOOLS:
        print(f"-> {action_name}")
        upsert_tool(token, action_name, display_name, builder())
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
