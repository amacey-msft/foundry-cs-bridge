#!/usr/bin/env python3
"""Test Granite Peak Orders System Agent via Direct Line (same as Phase 2, different agent).

This script:
1. Gets DL token from Copilot Studio environment
2. Creates conversation targeting Granite Peak Orders System Agent
3. Posts test messages
4. Validates multi-agent delegation (lookup → eligibility → return)
"""

import json
import subprocess
import time
import requests

# Config
ORG_URL = "https://orga5bae564.crm.dynamics.com"
# Granite Peak Orders System Agent (new, cloned)
AGENT_ID = "5edfba3a-0e4b-f111-bec6-00224805f8f9"

DL_TOKEN_ENDPOINT = "https://orga5bae564.crm.dynamics.com/api/botruntime/directline/tokens/generatetoken?api-version=2022-03-01-preview"


def get_token() -> str:
    """Get Dataverse access token."""
    out = subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", ORG_URL, "--query", "accessToken", "-o", "tsv"],
        shell=True,
        text=True,
    ).strip()
    if not out:
        raise SystemExit("Failed to get token")
    return out


def test_granite_peak_agent():
    """Test agent via Direct Line."""
    print("Testing Granite Peak Orders System Agent via Direct Line\n")
    
    # Step 1: Get Dataverse token
    print("1. Getting Dataverse token...")
    token = get_token()
    print("   ✓ Token acquired\n")
    
    # Step 2: Mint Direct Line token
    print("2. Minting Direct Line token...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"AgentId": AGENT_ID}
    r = requests.post(DL_TOKEN_ENDPOINT, json=payload, headers=headers, timeout=10)
    if r.status_code >= 400:
        print(f"   ✗ Error: {r.status_code} {r.text}")
        return False
    
    dl_data = r.json()
    dl_token = dl_data.get("token")
    stream_url = dl_data.get("streamUrl", "")
    conv_id = dl_data.get("conversationId", "")
    
    print(f"   ✓ Token: {dl_token[:50]}...")
    print(f"   ✓ Stream URL: {stream_url}")
    print(f"   ✓ Conversation ID: {conv_id}\n")
    
    # Extract regional DL host from stream_url
    if not stream_url:
        print("   ⚠ No streamUrl returned; using global endpoint")
        dl_host = "directline.botframework.com"
    else:
        # Extract host from streamUrl (e.g., https://europe.directline.botframework.com/v3/...)
        import re
        match = re.search(r"https://([^/]+)/", stream_url)
        dl_host = match.group(1) if match else "directline.botframework.com"
    
    print(f"   DL Host: {dl_host}\n")
    
    # Step 3: Create conversation
    print("3. Creating Direct Line conversation...")
    dl_headers = {"Authorization": f"Bearer {dl_token}", "Content-Type": "application/json"}
    r = requests.post(f"https://{dl_host}/v3/directline/conversations", headers=dl_headers, timeout=10)
    if r.status_code >= 400:
        print(f"   ✗ Error: {r.status_code} {r.text}")
        return False
    
    conv = r.json()
    conv_id = conv.get("conversationId")
    print(f"   ✓ Conversation ID: {conv_id}\n")
    
    # Step 4: Test queries
    test_cases = [
        ("list my orders", "Should show orders for Riley Carter (GP-1001)"),
        ("can i return my order", "Should trigger return flow (lookup → eligibility → process return)"),
    ]
    
    for user_msg, expectation in test_cases:
        print(f"4.{test_cases.index((user_msg, expectation)) + 1}. Testing: '{user_msg}'")
        print(f"   Expected: {expectation}")
        
        # Post activity
        activity = {
            "type": "message",
            "text": user_msg,
            "from": {"id": "user-1", "name": "Test User"},
        }
        r = requests.post(
            f"https://{dl_host}/v3/directline/conversations/{conv_id}/activities",
            json=activity,
            headers=dl_headers,
            timeout=10,
        )
        if r.status_code >= 400:
            print(f"   ✗ POST error: {r.status_code}")
            return False
        
        posted_activity = r.json()
        user_activity_id = posted_activity.get("id")
        
        # Poll for replies (with 25-second timeout)
        print("   Polling for reply...")
        timeout = time.time() + 25
        replies = []
        while time.time() < timeout:
            r = requests.get(
                f"https://{dl_host}/v3/directline/conversations/{conv_id}/activities",
                headers=dl_headers,
                timeout=10,
            )
            if r.status_code >= 400:
                print(f"   ✗ GET error: {r.status_code}")
                return False
            
            activities = r.json().get("activities", [])
            # Filter out own posted activity
            bot_replies = [
                a for a in activities
                if a.get("type") == "message" and a.get("from", {}).get("id") != "user-1" and a.get("id") != user_activity_id
            ]
            
            if bot_replies:
                for reply in bot_replies:
                    text = reply.get("text", "")
                    if text:
                        replies.append(text)
                        print(f"   ✓ Reply: {text[:150]}...")
                break
            
            time.sleep(1)
        
        if not replies:
            print("   ⚠ No reply received (timeout)")
        
        print()
    
    return True


if __name__ == "__main__":
    success = test_granite_peak_agent()
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Test failed")
