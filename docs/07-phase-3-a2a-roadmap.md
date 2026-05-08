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
- [x] Clone Order Management System Agent family (6 agents) to Granite Peak
- [ ] Create A2APreviewTool in Foundry project
- [ ] Set target endpoint: Granite Peak Orders System Agent `/api/agents/invoke`
- [ ] Configure managed identity (if Entra Agent ID)

### 2. Code Changes
- [ ] Remove `app/cs_directline.py` dependency (Direct Line fallback)
- [ ] Update `app/cs_tool.py` to invoke A2A instead
- [ ] Simplify `app/foundry_client.py` (remove DL state logic)
- [ ] Test multi-agent A2A dispatch

### 3. Testing
- [ ] Foundry portal traces show A2A tool invocation
- [ ] Full order flow: product Q&A → order lookup → return eligibility → RMA
- [ ] Multi-agent test (if second agent added)

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
