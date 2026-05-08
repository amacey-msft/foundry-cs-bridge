"""Copilot Studio agent configuration switcher.

Allows running the same chat app against different CS agents without code changes.
Set CS_AGENT_ID environment variable to switch agents.

Phase 2: Granite Peak Orders Agent (single-purpose, order tool)
Phase 3: Granite Peak Orders System Agent (orchestrator + 5 children)
"""

import os

# Phase 2: Single orders agent
PHASE2_AGENT_ID = "39a7ba9d-16e6-4879-a676-9bcf38490d16"  # Granite Peak Orders Agent
PHASE2_AGENT_NAME = "Granite Peak Orders Agent"

# Phase 3: Orchestrator + 5 children (return eligibility, RMA, etc.)
PHASE3_AGENT_ID = "5edfba3a-0e4b-f111-bec6-00224805f8f9"  # Granite Peak Orders System Agent
PHASE3_AGENT_NAME = "Granite Peak Orders System Agent"

# Current active agent (configurable via env)
ACTIVE_AGENT_ID = os.environ.get("CS_AGENT_ID", PHASE2_AGENT_ID).strip()
ACTIVE_AGENT_NAME = PHASE3_AGENT_NAME if ACTIVE_AGENT_ID == PHASE3_AGENT_ID else PHASE2_AGENT_NAME

print(f"Active Copilot Studio Agent: {ACTIVE_AGENT_NAME} ({ACTIVE_AGENT_ID})")
