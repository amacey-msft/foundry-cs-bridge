"""Provision the Granite Peak Orders Agent's GPT (system instructions) component.

Idempotent: PATCH if exists, POST otherwise. Updates `data` with
the YAML-flavored `GptComponentMetadata`.

Run AFTER cs-provision-bot.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from urllib.parse import quote

import requests

ORG_URL = "https://orga5bae564.crm.dynamics.com"
BOT_SCHEMA = "awm_granitepeakorders"
GPT_SCHEMA = f"{BOT_SCHEMA}.gpt.default"
DISPLAY_NAME = "Granite Peak Orders Agent"

INSTRUCTIONS = """You are the Granite Peak Outfitters orders specialist. You help customers \
with order status, return eligibility, filing returns, refund status, and the \
return policy.

Tone: friendly New England voice, concise. Short sentences. No marketing fluff.

Customer identity: For this demo there is one customer, **Riley Carter** \
(customer id GP-1001). Don't ask the user to identify themselves.

Formatting:
- Prices as $X.XX
- Dates as "Apr 26"
- Order ids exactly as the API returns them (e.g. ORD-2026-1001)
- Return ids exactly as the API returns them (e.g. RMA-20260420-A7B3C9)

When a customer asks about an order they haven't named, use the **list_my_orders** \
tool to fetch Riley Carter's orders first.

When a customer asks about a specific order, use **get_order_status**.

For returns:
1. Always call **check_return_eligibility** before offering to file a return.
2. If eligible, summarize the eligibility result and ask the customer to confirm \
   the SKU + reason + condition.
3. On confirmation, call **create_return**. Quote the returned RMA id and refund amount.
4. If not eligible, explain why (use the reason from the eligibility response) and \
   offer the **get_return_policy** text.

For policy questions, call **get_return_policy** and quote it.

Never invent order ids, prices, ship dates, tracking numbers, refund amounts, \
or RMA ids. If a tool call fails, say so plainly and offer to try again.
"""


def az_token(resource: str) -> str:
    out = subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"],
        shell=True,
    )
    return out.decode().strip()


def find_bot_id(headers: dict) -> str:
    flt = quote(f"schemaname eq '{BOT_SCHEMA}'", safe="")
    r = requests.get(
        f"{ORG_URL}/api/data/v9.2/bots?$filter={flt}&$select=botid",
        headers=headers, timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("value") or []
    if not items:
        raise SystemExit(f"Bot '{BOT_SCHEMA}' not found. Run cs-provision-bot.py first.")
    return items[0]["botid"]


def find_gpt(headers: dict) -> dict | None:
    flt = quote(f"schemaname eq '{GPT_SCHEMA}'", safe="")
    r = requests.get(
        f"{ORG_URL}/api/data/v9.2/botcomponents?$filter={flt}&$select=botcomponentid,name,componenttype",
        headers=headers, timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("value") or []
    return items[0] if items else None


def build_data() -> str:
    # YAML body. CS treats `data` as a YAML doc with `kind`, `displayName`,
    # `instructions`. Use literal-block scalar (|-) so newlines are preserved.
    instructions_indented = "\n".join("  " + line for line in INSTRUCTIONS.splitlines())
    return (
        "kind: GptComponentMetadata\n"
        f"displayName: {DISPLAY_NAME}\n"
        "instructions: |-\n"
        f"{instructions_indented}\n"
    )


def upsert(headers: dict, bot_id: str) -> None:
    data = build_data()
    existing = find_gpt(headers)
    if existing:
        comp_id = existing["botcomponentid"]
        r = requests.patch(
            f"{ORG_URL}/api/data/v9.2/botcomponents({comp_id})",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            json={"data": data},
            timeout=60,
        )
        if r.status_code >= 400:
            print(r.text[:1500], file=sys.stderr); r.raise_for_status()
        print(f"Updated GPT component: {comp_id}")
        return

    body = {
        "botcomponentid": str(uuid.uuid4()),
        "name": DISPLAY_NAME,
        "schemaname": GPT_SCHEMA,
        "componenttype": 15,            # GPT
        "parentbotid@odata.bind": f"/bots({bot_id})",
        "data": data,
    }
    r = requests.post(
        f"{ORG_URL}/api/data/v9.2/botcomponents",
        headers={**headers, "Content-Type": "application/json; charset=utf-8", "Prefer": "return=representation"},
        json=body,
        timeout=60,
    )
    if r.status_code >= 400:
        print(r.text[:1500], file=sys.stderr); r.raise_for_status()
    print(f"Created GPT component: {r.json()['botcomponentid']}")


def main() -> int:
    token = az_token(ORG_URL)
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
    }
    bot_id = find_bot_id(headers)
    upsert(headers, bot_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
