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

### 1. Portal Setup (Completed ✅)
- [x] Clone Order Management System Agent family (6 agents) to Granite Peak
- [x] Create A2APreviewTool research + endpoint findings
- [x] Set target endpoint: Granite Peak Orders System Agent invoke
- [x] Configure managed identity (if Entra Agent ID) — documented

### 2. Code Changes (Research Done, Awaiting Activation)
- [x] Create Direct Line client infrastructure (existing + documented)
- [x] Document cs_agents.py switcher (Phase 2 vs Phase 3)
- [ ] Get token endpoint for Granite Peak Orders System Agent
- [ ] Update ACA environment variable `CS_DIRECTLINE_TOKEN_ENDPOINT`
- [ ] Deploy new revision of `granite-peak-bridge`

### 3. Testing (Ready)
- [x] Created test-granite-peak-agent.py (Direct Line validation)
- [x] Created quick-test-agent.py (integration test)
- [ ] Run full flow test: product Q&A → order lookup → return eligibility → RMA
- [ ] Verify CS portal shows multi-agent delegation

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
