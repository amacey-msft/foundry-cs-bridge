# A2A Integration Setup for Granite Peak Orders System Agent

## Context
- **Foundry Model:** Azure OpenAI gpt-4.1-mini-gp (via Responses API)
- **CS Agent:** Granite Peak Orders System Agent (orchestrator + 5 children)
- **CS Agent ID:** 5edfba3a-0e4b-f111-bec6-00224805f8f9
- **CS Org URL:** https://orga5bae564.crm.dynamics.com

## A2A Endpoint Configuration

### CS Agent Invoke Endpoint
Copilot Studio agents expose an invoke endpoint (not documented publicly; proprietary API):
```
POST https://orga5bae564.crm.dynamics.com/api/agents/invoke?agentId=5edfba3a-0e4b-f111-bec6-00224805f8f9
Content-Type: application/json
Authorization: Bearer {token}

{
  "activity": {
    "type": "message",
    "text": "user message here",
    "from": {
      "id": "user-id",
      "name": "User Name"
    },
    "serviceUrl": "https://..." // optional
  },
  "conversationId": "..." // optional
}
```

### Foundry A2APreviewTool Configuration
Create tool in Foundry portal (AI Foundry or direct Responses API):

**Tool Name:** `ask_granite_peak_orders_a2a` (or `granite_peak_orders_assistant`)

**Tool Definition (OpenAI function schema):**
```json
{
  "type": "function",
  "function": {
    "name": "ask_granite_peak_orders_a2a",
    "description": "Delegate to Granite Peak Orders System Agent (orchestrator) for order management, returns, refunds, and shipping inquiries. Handles complex multi-step flows: customer auto-lookup via email, order listing, return eligibility checks, RMA processing.",
    "parameters": {
      "type": "object",
      "properties": {
        "user_message": {
          "type": "string",
          "description": "The customer's question or request verbatim (e.g., 'I want to return my order', 'Can you look up my orders?')"
        }
      },
      "required": ["user_message"]
    }
  }
}
```

**A2A Tool Binding (Foundry Portal / Agent Settings):**
- **Tool Type:** Agent-to-Agent (A2A) / MCP-based
- **Target Endpoint:** POST `https://orga5bae564.crm.dynamics.com/api/agents/invoke?agentId=5edfba3a-0e4b-f111-bec6-00224805f8f9`
- **Authentication:** 
  - Azure AD / Managed Identity (system-assigned MI of bridge ACA must have permissions on CS agent)
  - OR: Bot Framework connection (if CS agent uses classic app reg)
  - OR: Service Principal with federated credential

## Implementation Path (Preference Order)

### Option 1: Foundry Portal UI (Easiest)
1. Open AI Foundry project
2. Go to **Tools** or **Agent Settings** 
3. Create new tool type: **Agent-to-Agent**
4. Fill in:
   - Name: `ask_granite_peak_orders_a2a`
   - Target Agent: Granite Peak Orders System Agent (ID: 5edfba3a-0e4b-f111-bec6-00224805f8f9)
   - Endpoint: `https://orga5bae564.crm.dynamics.com/api/agents/invoke`
5. Test: invoke with `{"user_message": "list my orders"}`

### Option 2: Foundry REST API
POST to Foundry project to create A2APreviewTool

### Option 3: Direct Dataverse REST (Advanced)
Create msdyn_a2apreviewtool + connection reference directly in Dataverse

## Code Changes (Minimal)

### 1. Update system_prompt.md
Replace:
```
- ``ask_granite_peak_orders`` — the Granite Peak Orders Agent via Direct Line
```
With:
```
- ``ask_granite_peak_orders_a2a`` — the Granite Peak Orders System Agent (orchestrator) 
  delegates to 5 specialist agents for order lookup, return eligibility, RMA processing
```

### 2. Keep or remove cs_directline.py?
**Option A (Cleaner):** Remove `cs_directline.py` and `cs_tool.py` entirely. Foundry handles the A2A dispatch.
**Option B (Safer):** Keep as fallback. Foundry calls A2A; if timeout/error, fallback to Direct Line.

**Recommendation:** Option A for Phase 3. Foundry portal A2A is stable enough.

### 3. Update foundry_client.py tool loop
Remove the local tool dispatch for `ask_granite_peak_orders`. Let Foundry handle it.

```python
# Remove this:
if tool_name == "ask_granite_peak_orders":
    result = cs_tool.dispatch(sess, tool_name, tool_args)

# No changes needed; Foundry will call A2A directly
```

### 4. Keep fallback Foundry tools
Keep `list_my_orders`, `get_order`, etc. as direct API tools (no CS delegation needed; they call orders FastAPI directly).

## Testing Sequence

### Step 1: Verify A2A Tool Works
```bash
curl -X POST https://orga5bae564.crm.dynamics.com/api/agents/invoke?agentId=5edfba3a-0e4b-f111-bec6-00224805f8f9 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "activity": {
      "type": "message",
      "text": "list my orders",
      "from": {"id": "user-1", "name": "Test User"}
    }
  }'
```
Expected: Agent responds with order list.

### Step 2: Test Foundry A2A Tool
Ask Foundry model: **"Can you list my orders?"**
Expected: Model calls `ask_granite_peak_orders_a2a`, gets response, relays to user.

### Step 3: Full Flow Test
```
User: "I want to return my mountain bike"
→ Foundry routes to A2A tool
→ CS Orchestrator delegates to Lookup + Eligibility + Process Return agents
→ Returns RMA number + label + refund amount
```

Expected: End-to-end return processed in 5-10 seconds, traces visible in both Foundry + CS portals.

## Success Criteria (Phase 3 Acceptance)
- ✅ A2A tool created in Foundry + responds to test calls
- ✅ Full order flow works (product Q&A → lookup → return → RMA)
- ✅ Foundry portal traces show `ask_granite_peak_orders_a2a` invocation
- ✅ CS portal shows agent + child agent activity (in Copilot Studio > Analytics)
- ✅ Multi-agent delegation works (My Orders → Order Lookup → Return Eligibility → Process Return)
- ✅ System prompt updated; tests passing
- ✅ Code cleaned (cs_directline.py removed if Option A chosen)
