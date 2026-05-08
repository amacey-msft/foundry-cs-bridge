# Phase 3: Granite Peak Orders System Agent Integration

## Summary
- ✅ 6 agents cloned (orchestrator + 5 children) to Granite Peak schema
- ✅ Direct Line infrastructure tested (live chat works)
- ✅ Test scripts created for agent validation
- 🔄 **Next: Switch live chat to new agent**

## To Activate Phase 3 (Granite Peak Orders System Agent)

### In Azure Container Apps (ACA)
Update environment variable on `granite-peak-bridge` container app:

```bash
az containerapp update \
  --name granite-peak-bridge \
  --resource-group rg-cpv-aca \
  --environment cae-cpv \
  --set-env-vars CS_DIRECTLINE_TOKEN_ENDPOINT="<NEW_TOKEN_ENDPOINT_FOR_PHASE3_AGENT>" \
  --revision-suffix v$(date +%m%d%H%M)
```

**Token endpoint:** Should be specific to Granite Peak Orders System Agent in Copilot Studio.
To find: Ask Copilot Studio for the token endpoint for agent ID `5edfba3a-0e4b-f111-bec6-00224805f8f9`.

### Alternatively (Phase 3.1): A2A Tool in Foundry
Create A2APreviewTool in Foundry portal pointing to CS agent endpoint (see docs/08-a2a-endpoint-setup.md).
- This allows Foundry to route the call, not requiring a token endpoint change
- More flexible for multi-agent scenarios

## What Changes in Phase 3
| Aspect | Phase 2 | Phase 3 |
|--------|--------|--------|
| Agent | Granite Peak Orders Agent (single) | **Granite Peak Orders System Agent (orchestrator)** |
| Return flow | N/A (not built) | ✅ Auto-lookup (email) → Eligibility check → Item-level refund calc |
| Multi-agent | N/A | ✅ 5 specialist children handle order lookup, returns, fraud flags |
| Traces | Single call | **Multi-step delegation visible in Copilot Studio** |
| User experience | Basic order list | **Full order lifecycle: lookup → return eligibility → RMA + shipping label** |

## Testing After Activation
```bash
# Chat test
curl -X POST https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to return my mountain bike"}'

# Expected:
# - Agent auto-looks up Riley Carter (GP-1001)
# - Checks return eligibility
# - Issues RMA number + prepaid label
# - Calculates item-level refund amount
```

## Success Criteria
- ✅ Order lookup works (customer found → orders listed)
- ✅ Return eligibility checked (policy, fraud flags)
- ✅ RMA issued with shipping label + item-level refund amount
- ✅ Copilot Studio portal shows multi-agent delegation chain
- ✅ Foundry traces (if A2A used) show agent-to-agent delegation

## Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| New agent not yet "published" in CS | If unpublished: manually publish in Copilot Studio Studio UI |
| Token endpoint not mapped to new agent | Verify token endpoint points to correct agent ID (5edf...) |
| Multi-agent delegation fails silently | Enable DEBUG logging in CS; check Analytics > Agent sessions |
| Item-level refund amount off | Verify Process Return Agent maps product SKU to price (GP-SKI-BOOTS-ENTRY, etc.) |

## Next Steps
1. Get token endpoint for Granite Peak Orders System Agent from Copilot Studio
2. Update ACA `granite-peak-bridge` environment variable + deploy new revision
3. Test full return flow via chat UI
4. Verify traces in Copilot Studio
5. (Optional) Phase 3.1: Create A2A tool in Foundry portal for cleaner integration
6. Merge feat/phase-3-a2a-integration → main
