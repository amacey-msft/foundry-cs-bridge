#!/usr/bin/env python3
"""Quick test: Call Granite Peak Orders System Agent via existing cs_directline infrastructure.

Uses the same Direct Line token endpoint as the live chat, but targets the new agent.
"""

import sys
import os

# Add parent dir to path so we can import from app/
sys.path.insert(0, os.path.dirname(__file__) + "/..")

from app import cs_directline, config
from app.session import ChatSession

def test_agent():
    print("Testing Granite Peak Orders System Agent\n")
    
    # Check if DL is configured
    if not config.CS_DIRECTLINE_TOKEN_ENDPOINT:
        print("⚠ CS_DIRECTLINE_TOKEN_ENDPOINT not set")
        print("  Run this in the ACA environment where the live chat works")
        return False
    
    print(f"Using token endpoint: {config.CS_DIRECTLINE_TOKEN_ENDPOINT[:80]}...\n")
    
    # Create a session
    sess = ChatSession(session_id="test-1", user_id="user-1")
    
    # Test messages
    test_cases = [
        "list my orders",
        "can I return my product",
    ]
    
    try:
        for msg in test_cases:
            print(f"User: {msg}")
            reply = cs_directline.ask(sess, msg)
            print(f"Agent: {reply[:200]}...\n" if len(reply) > 200 else f"Agent: {reply}\n")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_agent()
    print("✓ Test passed" if success else "✗ Test failed")
