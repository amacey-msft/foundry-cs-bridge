# Phase 3: Foundry A2A Integration Roadmap

## Overview
Replace Direct Line fallback with Foundry A2APreviewTool connection to Copilot Studio agent endpoint.

## Why A2A (vs Direct Line in Phase 2)

| Aspect | Direct Line (Phase 2) | A2A (Phase 3) |
|--------|----------------------|---|
| Config | Code changes (`cs_tool.py`) | Portal UI only |
| Multi-agent | Branch logic needed | Portal endpoint swap |
| Traces | Opaque ("tool returned text") | Native Foundry visibility |
| State | Per-session DL conv in memory | Stateless |
| Scale | Requires sticky sessions | Scales to multiple replicas |
| Foundry upgrade | Code refactor | No changes |

## Implementation Tasks

### 1. Portal Setup
- [ ] Create A2APreviewTool in Foundry project
- [ ] Set target endpoint: CS agent `/api/agents/invoke`
- [ ] Configure managed identity + grant Entra Agent ID role (if needed)

### 2. Code Changes
- [ ] Remove `app/cs_directline.py`
- [ ] Update `app/cs_tool.py` to invoke A2A instead of DL fallback
- [ ] Simplify `app/foundry_client.py` tool dispatch (remove DL token/session logic)
- [ ] Update `app/system_prompt.md` if needed

### 3. Testing
- [ ] Foundry portal traces show A2A tool invocation
- [ ] Order flow still works end-to-end
- [ ] Multi-agent test: orders + support agent dispatch

### 4. Documentation
- [ ] Add A2A architecture to `docs/01-architecture.md`
- [ ] Update deployment runbook (`docs/03-deployment-runbook.md`)
- [ ] Update troubleshooting (`docs/05-troubleshooting.md`) with A2A debugging

## Dependencies
- Foundry A2APreviewTool support (stable as of 2026-05)
- Entra Agent ID workaround (federated credential OR classic app reg fallback)

## Success Criteria
- ✅ Foundry portal shows A2A tool invocation in traces
- ✅ Order flow responds correctly
- ✅ Two separate CS agents dispatch correctly via portal config
- ✅ No per-session state in bridge memory
- ✅ Documentation updated
