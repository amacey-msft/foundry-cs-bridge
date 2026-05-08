"""Smoke-test Granite Peak CS bot via Direct Line.

Mints a DL token, opens a conversation, sends a user message, polls for
replies, prints them. Run with the orders mock API + devtunnel up.
"""
import json
import os
import time
import uuid

import requests

DL_TOKEN_URL = os.environ.get(
    "CS_DIRECTLINE_TOKEN_ENDPOINT",
    "https://63b4b29bb3b0ed709136524a53a22e.06.environment.api.powerplatform.com/powervirtualagents/botsbyschema/awm_granitepeakorders/directline/token?api-version=2022-03-01-preview",
)
USER_TEXT = os.environ.get("USER_TEXT", "hi, can you list my orders?")

print("Minting DL token from:", DL_TOKEN_URL)
r = requests.get(DL_TOKEN_URL, timeout=30)
r.raise_for_status()
tok = r.json()
print("token expires_in:", tok.get("expires_in"))
DL_TOKEN = tok["token"]

# CS hosted DL conversations live on the env api host
host = DL_TOKEN_URL.split("/powervirtualagents/")[0]
conv_url = f"{host}/powervirtualagents/botsbyschema/awm_granitepeakorders/directline/conversations?api-version=2022-03-01-preview"
hdr = {"Authorization": f"Bearer {DL_TOKEN}", "Content-Type": "application/json"}

# Try CS hosted conv start
r = requests.post(conv_url, headers=hdr, timeout=30)
print("CS conv start ->", r.status_code, r.text[:300])
if r.status_code >= 400:
    # Fallback to global directline (the token may still be valid there)
    r = requests.post(
        "https://directline.botframework.com/v3/directline/conversations",
        headers=hdr,
        timeout=30,
    )
    print("global DL conv start ->", r.status_code, r.text[:300])
    r.raise_for_status()
    j = r.json()
    base = "https://directline.botframework.com/v3/directline"
else:
    j = r.json()
    base = f"{host}/powervirtualagents/botsbyschema/awm_granitepeakorders/directline"

conv_id = j["conversationId"]
print("conversationId:", conv_id)

# post message
act = {
    "type": "message",
    "from": {"id": "smoke-user"},
    "text": USER_TEXT,
    "locale": "en-US",
}
post_url = f"{base}/conversations/{conv_id}/activities"
if "?api-version" in conv_url and "api-version" not in post_url:
    post_url += "?api-version=2022-03-01-preview"
r = requests.post(post_url, headers=hdr, json=act, timeout=30)
print("post activity ->", r.status_code, r.text[:300])

# poll
get_url = f"{base}/conversations/{conv_id}/activities"
if "?api-version" in conv_url and "api-version" not in get_url:
    get_url += "?api-version=2022-03-01-preview"
watermark = None
deadline = time.time() + 45
while time.time() < deadline:
    u = get_url + (f"&watermark={watermark}" if watermark else "")
    r = requests.get(u, headers=hdr, timeout=30)
    j = r.json()
    watermark = j.get("watermark")
    for a in j.get("activities", []):
        who = a.get("from", {}).get("id") or a.get("from", {}).get("role")
        t = a.get("type")
        text = a.get("text") or ""
        print(f"  [{t}] from={who}: {text[:300]}")
        # dump full event/value for trace
        if t == "event" or a.get("value") or a.get("name"):
            print("     name:", a.get("name"), "value:", json.dumps(a.get("value"))[:500])
    time.sleep(2)
