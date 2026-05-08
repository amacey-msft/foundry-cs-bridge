"""Provision the Granite Peak Orders Agent (Copilot Studio) via Dataverse Web API.

Idempotent: if a bot with the target schemaName already exists, prints
its botid and exits 0.

Auth: AZ CLI access token for the org URL (DefaultAzureCredential would
also work but az is already cached).

What this creates:
- A `bot` row (generative orchestration enabled).
- That's it for v1: the orchestrator + system prompt are enough to wire
  HTTP tools later via separate scripts. Topics + tools land in follow-up
  scripts so each step is debuggable on its own.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from urllib.parse import quote

import requests

ORG_URL = "https://orga5bae564.crm.dynamics.com"
SCHEMA_NAME = "awm_granitepeakorders"
DISPLAY_NAME = "Granite Peak Orders Agent"
SOLUTION = "GenericOrderManagementSystem"
PUBLISHER = "DefaultPublisherorga5bae564"


def az_token(resource: str) -> str:
    out = subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"],
        shell=True,
    )
    return out.decode().strip()


def find_bot(headers: dict) -> dict | None:
    flt = quote(f"schemaname eq '{SCHEMA_NAME}'", safe="")
    r = requests.get(
        f"{ORG_URL}/api/data/v9.2/bots?$filter={flt}&$select=botid,name,schemaname,statecode,statuscode",
        headers=headers,
        timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("value") or []
    return items[0] if items else None


def create_bot(headers: dict) -> str:
    bot_id = str(uuid.uuid4())
    config = {
        "$kind": "BotConfiguration",
        "settings": {
            "GenerativeActionsEnabled": True,
            "SmartTaskCompletionEnabled": True,
        },
        "publishOnImport": True,
        "gPTSettings": {
            "$kind": "GPTSettings",
            "defaultSchemaName": f"{SCHEMA_NAME}.gpt.default",
        },
        "isLightweightBot": False,
        "aISettings": {
            "$kind": "AISettings",
            "useModelKnowledge": True,   # Allow ungrounded responses (per memory rule)
            "isFileAnalysisEnabled": True,
            "isSemanticSearchEnabled": True,
            "contentModeration": "Medium",
            "optInUseLatestModels": True,
        },
        "recognizer": {"$kind": "CLIAgentRecognizer"},
    }
    body = {
        "botid": bot_id,
        "name": DISPLAY_NAME,
        "schemaname": SCHEMA_NAME,
        "language": 1033,
        "authenticationmode": 1,        # No authentication
        "accesscontrolpolicy": 0,       # AccessibleToEveryoneInTenant
        "configuration": json.dumps(config),
    }
    create_headers = dict(headers)
    create_headers["MSCRM.SolutionUniqueName"] = SOLUTION
    create_headers["Prefer"] = "return=representation"
    r = requests.post(
        f"{ORG_URL}/api/data/v9.2/bots",
        headers=create_headers,
        json=body,
        timeout=60,
    )
    if r.status_code >= 400:
        print(f"[create] HTTP {r.status_code}", file=sys.stderr)
        print(r.text[:2000], file=sys.stderr)
        r.raise_for_status()
    return r.json().get("botid", bot_id)


def main() -> int:
    token = az_token(ORG_URL)
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
    }
    existing = find_bot(headers)
    if existing:
        print(f"Bot already exists: {existing['name']} ({existing['botid']})")
        print(f"  schemaname: {existing['schemaname']}")
        return 0
    bot_id = create_bot(headers)
    print(f"Created bot: {DISPLAY_NAME}")
    print(f"  botid:      {bot_id}")
    print(f"  schemaname: {SCHEMA_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
