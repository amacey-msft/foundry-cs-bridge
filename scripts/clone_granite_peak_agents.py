#!/usr/bin/env python3
"""Clone Order Management System Agent family to Granite Peak Orders Agent family.

Clones 6 agents (orchestrator + 5 children), updates names and instructions:
  - RL- product SKUs → GP- equivalents
  - "Order Management Agent" → "Granite Peak Orders Agent"
  - API references updated in instructions
"""

import json
import os
import subprocess
import sys
import uuid
from typing import Any

import requests

ORG_URL = "https://orga5bae564.crm.dynamics.com"
API = f"{ORG_URL}/api/data/v9.2"

# Source agent IDs (Order Management System Agent family)
AGENT_IDS = {
    "812147d0-3c69-4d6c-bd8e-7c4c086c50c4": "Order Management System Agent",
    "84e89eb3-333b-417a-bac6-4c775838d948": "My Orders Agent",
    "1657cd75-bf3c-f111-bec6-000d3a5c574a": "Order Management Agent",
    "16418819-1163-456c-8717-36fc63d758ce": "Order Lookup Agent",
    "c0d865c8-b9be-4c3f-b9df-b60085c2fd4d": "Return Eligibility Agent",
    "814f03c8-7cf5-479b-b930-30ff808d7860": "Process Return Agent",
}

# Product SKU mappings: RL- → GP-
SKU_MAP = {
    "RL-SKIN-START-KIT": "GP-SKI-BOOTS-ENTRY",
    "RL-HAIR-ESS-KIT": "GP-MTN-BIKE-29ER",
}


def get_token() -> str:
    """Get Dataverse access token."""
    out = subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", ORG_URL, "--query", "accessToken", "-o", "tsv"],
        shell=True,
        text=True,
    ).strip()
    if not out:
        raise SystemExit("Failed to get access token")
    return out


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def rename_agent(orig_name: str) -> str:
    """Map original agent name to Granite Peak clone name."""
    if orig_name == "Order Management System Agent":
        return "Granite Peak Orders System Agent"
    return "Granite Peak Orders - " + orig_name


def update_data(data_str: str) -> str:
    """Update agent instructions YAML: replace RL- SKUs with GP-, update names."""
    # Replace product names
    result = data_str.replace("Order Management Agent", "Granite Peak Orders Agent")
    
    # Replace specific SKU mappings
    for old_sku, new_sku in SKU_MAP.items():
        result = result.replace(old_sku, new_sku)
    
    # Fallback: RL- → GP- for any remaining RL- references
    result = result.replace("RL-", "GP-")
    
    # Update order number examples
    result = result.replace('starts with "RL-"', 'starts with "GP-"')
    result = result.replace('"RL', '"GP')
    
    return result


def clone_agent(token: str, orig_id: str, orig_name: str) -> dict:
    """Clone a single agent."""
    new_name = rename_agent(orig_name)
    print(f"  Cloning: {orig_name} → {new_name}")
    
    # GET original agent
    url = f"{API}/botcomponents({orig_id})"
    r = requests.get(url, headers=headers(token), timeout=30)
    r.raise_for_status()
    orig = r.json()
    
    # Generate unique schema name (required field)
    unique_id = str(uuid.uuid4()).replace("-", "")[:20].lower()
    schemaname = f"gp_orders_{unique_id}"
    
    # Prepare clone - include required schemaname
    clone_body = {
        "name": new_name,
        "componenttype": orig.get("componenttype"),
        "data": update_data(orig.get("data", "")),
        "schemaname": schemaname,
    }
    
    # POST clone
    try:
        r = requests.post(f"{API}/botcomponents", json=clone_body, headers=headers(token), timeout=30)
        if r.status_code >= 400:
            print(f"    Status: {r.status_code}")
            print(f"    Response: {r.text[:500]}")
            r.raise_for_status()
        result = r.json()
    except requests.exceptions.RequestException as e:
        print(f"    ERROR: {e}")
        raise
    
    new_id = result.get("botcomponentid")
    print(f"    Created: {new_id}")
    return {"origId": orig_id, "newId": new_id, "origName": orig_name, "newName": new_name, "schemaname": schemaname}


def main():
    print("Cloning Order Management System Agent family to Granite Peak...\n")
    
    token = get_token()
    clones = []
    
    for orig_id, orig_name in AGENT_IDS.items():
        try:
            result = clone_agent(token, orig_id, orig_name)
            clones.append(result)
        except Exception as e:
            print(f"  FAILED to clone {orig_name}: {e}", file=sys.stderr)
            # Continue with other agents
            continue
    
    if not clones:
        print("No agents cloned successfully", file=sys.stderr)
        return 1
    
    # Save mapping
    mapping = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "clones": clones,
    }
    
    with open("scripts/clone-agent-mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\n✓ Cloned {len(clones)}/{len(AGENT_IDS)} agents")
    print(f"Saved mapping to scripts/clone-agent-mapping.json\n")
    
    print("Cloned Agents:")
    for clone in clones:
        print(f"  {clone['newName']}: {clone['newId']}")
    
    print("\nNext steps:")
    print("1. Manually edit agent instructions in Copilot Studio to map API endpoints")
    print("2. Test multi-step flow (orders → returns → RMA)")
    print("3. Configure A2APreviewTool in Foundry to target Granite Peak Orders System Agent")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
