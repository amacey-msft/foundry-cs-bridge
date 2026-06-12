#!/usr/bin/env python3
"""A2A HTTP client for Copilot Studio agents.

Calls Granite Peak Orders System Agent via the `/api/agents/invoke` endpoint
(proprietary CS API). More direct than Direct Line; no conversation sessions needed.
Each call is independent.
"""

import json
import subprocess
import requests

ORG_URL = "https://orga5bae564.crm.dynamics.com"
AGENT_ID = "5edfba3a-0e4b-f111-bec6-00224805f8f9"  # Granite Peak Orders System Agent


def get_token() -> str:
    """Get Dataverse access token via az CLI."""
    out = subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", ORG_URL, "--query", "accessToken", "-o", "tsv"],
        shell=True,
        text=True,
    ).strip()
    if not out:
        raise SystemExit("Failed to get access token")
    return out


def invoke_granite_peak_agent(user_message: str, user_id: str = "user-1", user_name: str = "Test User") -> str:
    """Invoke Granite Peak Orders System Agent via A2A invoke endpoint.
    
    Args:
        user_message: The user's question/request verbatim
        user_id: User identifier (for multi-user scenarios)
        user_name: User display name
    
    Returns:
        Agent response text
    """
    token = get_token()
    
    url = f"{ORG_URL}/api/agents/invoke?agentId={AGENT_ID}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "activity": {
            "type": "message",
            "text": user_message,
            "from": {
                "id": user_id,
                "name": user_name,
            },
        },
    }
    
    print(f"Invoking Granite Peak Orders System Agent...")
    print(f"  Endpoint: {url}")
    print(f"  Message: {user_message}")
    
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    result = r.json()
    
    # CS invoke returns activity in response
    response_text = result.get("text", "")
    if not response_text and "activities" in result:
        # Some CS versions return activities array
        activities = result["activities"]
        if activities:
            response_text = activities[0].get("text", "")
    
    print(f"  Response: {response_text[:200]}..." if len(response_text) > 200 else f"  Response: {response_text}")
    return response_text


if __name__ == "__main__":
    # Test calls
    test_cases = [
        "List my orders for customer GP-1001",
        "I want to check the return policy for mountain bikes",
        "Can I return my order?",
    ]
    
    for msg in test_cases:
        try:
            resp = invoke_granite_peak_agent(msg)
            print(f"✓ Success\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
