"""Copy Copilot Studio system topics from a template bot to Granite Peak.

Generative-orchestration bots created blank from the API don't get the
default system topics auto-created (Greeting, ConversationStart, Fallback,
OnError, Escalate, EndofConversation, Goodbye, MultipleTopicsMatched,
StartOver, ResetConversation, ThankYou). This script reads them from a
template bot and POSTs them under Granite Peak with re-prefixed schema
names.

Idempotent: skips topics that already exist on the target bot (matched by
suffix after the schema prefix).
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid

import requests

ORG_URL = "https://orga5bae564.crm.dynamics.com"
API = f"{ORG_URL}/api/data/v9.2"
SOLUTION = "GenericOrderManagementSystem"

SOURCE_BOT_ID = "757c2a0a-22dc-4c44-b3e6-b91da31554ea"
SOURCE_PREFIX = "new_bot_206f73d90439f11188b36045bdf0ef76"
TARGET_BOT_ID = "b6159d14-2485-4369-b65c-dafde20997d3"
TARGET_PREFIX = "awm_granitepeakorders"

SYSTEM_TOPIC_SUFFIXES = {
    "ConversationStart",
    "Greeting",
    "Goodbye",
    "OnError",
    "Fallback",
    "Escalate",
    "EndofConversation",
    "MultipleTopicsMatched",
    "StartOver",
    "ResetConversation",
    "ThankYou",
}


def az_token(resource: str) -> str:
    out = subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"],
        shell=True, text=True,
    ).strip()
    return out


def headers(token: str, prefer: bool = False) -> dict:
    h = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "MSCRM.SolutionUniqueName": SOLUTION,
    }
    if prefer:
        h["Prefer"] = "return=representation"
    return h


def list_topics(token: str, bot_id: str) -> list[dict]:
    r = requests.get(
        f"{API}/botcomponents",
        params={
            "$filter": f"_parentbotid_value eq {bot_id} and componenttype eq 9",
            "$select": "name,schemaname,data,botcomponentid",
            "$top": "200",
        },
        headers=headers(token),
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("value", [])


def main() -> int:
    token = az_token(ORG_URL)
    src = list_topics(token, SOURCE_BOT_ID)
    tgt = list_topics(token, TARGET_BOT_ID)
    tgt_suffixes = {c["schemaname"].split(".", 1)[-1] for c in tgt}

    copied = 0
    skipped = 0
    for c in src:
        suffix = c["schemaname"].split(".", 1)[-1]
        # only "topic.<Name>" entries
        if not suffix.startswith("topic."):
            continue
        topic_name = suffix.removeprefix("topic.")
        if topic_name not in SYSTEM_TOPIC_SUFFIXES:
            continue
        new_suffix = f"topic.{topic_name}"
        if new_suffix in tgt_suffixes:
            print(f"  exists: {new_suffix}")
            skipped += 1
            continue
        new_data = (c.get("data") or "").replace(SOURCE_PREFIX, TARGET_PREFIX)
        body = {
            "botcomponentid": str(uuid.uuid4()),
            "name": c["name"],
            "componenttype": 9,
            "schemaname": f"{TARGET_PREFIX}.{new_suffix}",
            "data": new_data,
            "parentbotid@odata.bind": f"/bots({TARGET_BOT_ID})",
        }
        r = requests.post(
            f"{API}/botcomponents",
            data=json.dumps(body),
            headers=headers(token, prefer=True),
            timeout=60,
        )
        if r.status_code >= 300:
            print(f"  FAIL {topic_name}: {r.status_code} {r.text[:600]}", file=sys.stderr)
            continue
        print(f"  copied: {new_suffix}")
        copied += 1
    print(f"Done. copied={copied} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
