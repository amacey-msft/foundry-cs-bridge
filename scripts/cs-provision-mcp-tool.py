"""Provision the MCP connection reference + TaskDialog botcomponent for the
Granite Peak Orders Agent.

Microsoft documentation followed:
- Custom MCP connector swagger pattern: x-ms-agentic-protocol: mcp-streamable-1.0
  https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent
- TaskDialog YAML with InvokeExternalAgentTaskAction +
  ModelContextProtocolMetadata is the only orchestrator-discoverable shape
  for MCP tools (verified against the OOB msdyn_CEOnboardingAgent's
  Microsoft Dataverse MCP Server botcomponent).

Pre-req: pac connector create has already produced a connector row.
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
SOLUTION = "GenericOrderManagementSystem"
BOT_ID = "b6159d14-2485-4369-b65c-dafde20997d3"
BOT_SCHEMA = "awm_granitepeakorders"
PUBLISHER_PREFIX = "awm"

CONNECTOR_ID = "30c0c71b-fe4a-f111-bec6-00224805f8f9"
# pac connector create produced this internal id; format from Dataverse
CONNECTOR_INTERNAL_ID = "shared_new-5fgranite-20peak-20orders-20mcp-5faa7a483b23563fd5"

# Connection reference logical name pattern from msdyn_CEOnboardingAgent:
#   <bot_schema>.shared_<short_name>
CONN_REF_LOGICAL = f"{BOT_SCHEMA}.shared_granitepeakordersmcp"
CONN_REF_DISPLAY = "Granite Peak Orders MCP"

# Matches Microsoft's reference botcomponent schemaname pattern:
#   <bot_schema>.action.<PascalCaseName>
TOOL_SCHEMA = f"{BOT_SCHEMA}.action.GranitePeakOrdersMCPServer"
TOOL_NAME = "Granite Peak Orders - MCP Server"

TOOL_YAML = f"""kind: TaskDialog
modelDisplayName: Granite Peak Orders MCP Server
modelDescription: Tools for the Granite Peak Outfitters orders backend. Use these to look up the customer's orders, get order status, check return eligibility, create returns (RMAs), and read the official return policy.
action:
  kind: InvokeExternalAgentTaskAction
  connectionReference: {CONN_REF_LOGICAL}
  connectionProperties:
    mode: Invoker

  operationDetails:
    kind: ModelContextProtocolMetadata
    operationId: InvokeMCP
"""


def az_token(resource: str) -> str:
    out = subprocess.check_output(
        [
            "az", "account", "get-access-token",
            "--resource", resource,
            "--query", "accessToken", "-o", "tsv",
        ],
        shell=True,
    )
    return out.decode().strip()


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_solution_id(h: dict) -> str:
    flt = quote(f"uniquename eq '{SOLUTION}'", safe="")
    r = requests.get(
        f"{ORG_URL}/api/data/v9.2/solutions?$filter={flt}&$select=solutionid,uniquename",
        headers=h, timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("value") or []
    if not items:
        raise SystemExit(f"Solution {SOLUTION!r} not found")
    return items[0]["solutionid"]


def find_connection_ref(h: dict) -> dict | None:
    flt = quote(f"connectionreferencelogicalname eq '{CONN_REF_LOGICAL}'", safe="")
    r = requests.get(
        f"{ORG_URL}/api/data/v9.2/connectionreferences?$filter={flt}",
        headers=h, timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("value") or []
    return items[0] if items else None


def create_connection_ref(h: dict) -> str:
    body = {
        "connectionreferencelogicalname": CONN_REF_LOGICAL,
        "connectionreferencedisplayname": CONN_REF_DISPLAY,
        "connectorid": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR_INTERNAL_ID}",
    }
    # Force into the target solution
    h2 = dict(h)
    h2["MSCRM.SolutionUniqueName"] = SOLUTION
    r = requests.post(
        f"{ORG_URL}/api/data/v9.2/connectionreferences",
        headers=h2, data=json.dumps(body), timeout=60,
    )
    if r.status_code >= 400:
        raise SystemExit(f"create connectionreference failed {r.status_code}: {r.text}")
    return r.json()["connectionreferenceid"]


def find_botcomponent(h: dict) -> dict | None:
    flt = quote(f"schemaname eq '{TOOL_SCHEMA}'", safe="")
    r = requests.get(
        f"{ORG_URL}/api/data/v9.2/botcomponents?$filter={flt}",
        headers=h, timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("value") or []
    return items[0] if items else None


def create_botcomponent(h: dict) -> str:
    body = {
        "name": TOOL_NAME,
        "schemaname": TOOL_SCHEMA,
        "componenttype": 9,  # action / tool
        "data": TOOL_YAML,
        "parentbotid@odata.bind": f"/bots({BOT_ID})",
    }
    h2 = dict(h)
    h2["MSCRM.SolutionUniqueName"] = SOLUTION
    r = requests.post(
        f"{ORG_URL}/api/data/v9.2/botcomponents",
        headers=h2, data=json.dumps(body), timeout=60,
    )
    if r.status_code >= 400:
        raise SystemExit(f"create botcomponent failed {r.status_code}: {r.text}")
    return r.json()["botcomponentid"]


def main() -> int:
    token = az_token(ORG_URL)
    h = headers(token)

    sol = get_solution_id(h)
    print(f"solution {SOLUTION} id={sol}")

    cr = find_connection_ref(h)
    if cr:
        cr_id = cr["connectionreferenceid"]
        print(f"connectionreference exists id={cr_id}")
    else:
        cr_id = create_connection_ref(h)
        print(f"connectionreference created id={cr_id}")

    bc = find_botcomponent(h)
    if bc:
        bc_id = bc["botcomponentid"]
        print(f"botcomponent exists id={bc_id} (use --replace to recreate)")
    else:
        bc_id = create_botcomponent(h)
        print(f"botcomponent created id={bc_id}")

    print()
    print("Next: pac copilot publish --bot " + BOT_ID)
    print("Then run scripts/cs-smoke-test.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
