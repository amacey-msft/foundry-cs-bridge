# foundry-cs-bridge

Foundry Agent Service → Copilot Studio (orders) demo. External-facing consumer
chat agent built on **Foundry Agent Service** delegates orders / returns /
refunds to a **Copilot Studio** orders agent via **A2A** (primary) or
**Direct Line** (fallback).

Demo retail front end: **Granite Peak Outfitters** — fictional New England
ski + bike retailer.

## Status
Phase 1 in progress. See [`plan.md`](plan.md) for full plan and
[`docs/02-cs-orders-setup.md`](docs/02-cs-orders-setup.md) for the manual
Copilot Studio provisioning recipe.

## Local dev quick start

```powershell
# 1. Run the mock orders API
docker compose up -d           # or: uvicorn orders_api.main:app --reload --port 8000
curl http://localhost:8000/healthz

# 2. Expose it to Copilot Studio
.\scripts\devtunnel-create.ps1
.\scripts\devtunnel-host.ps1   # prints public URL

# 3. Plug the public URL into the CS agent's HTTP Request tools
#    (one-time per tunnel; see docs/02-cs-orders-setup.md).
```

## Architecture (high level)

```
Browser (Granite Peak site)
   │
   ▼
Flask app  ──► Foundry Agent Service (Responses API)
   │             │
   │             ▼ A2A tool (or Direct Line fallback)
   │           Copilot Studio orders agent
   │             │
   │             ▼ HTTP Request tool
   └────────► Mock orders API (FastAPI, in-repo)
```

## Repo layout (target — populated across phases)

```
app/             Flask app, Foundry client, CS A2A/DL tool, session
orders_api/      FastAPI mock orders backend
templates/       Jinja2 retail site (Granite Peak)
static/          CSS, JS, inline-SVG product images
scripts/         Deploy + devtunnel helpers
docs/            Architecture, setup, troubleshooting
plan.md          Full delivery plan
CHANGELOG.md     Release notes
```

## Quick start
TBD — populated in Phase 2.

## Related repos (sibling references, not dependencies)
- [`copilot-studio-acs-voice`](../copilot-studio-acs-voice) — Direct Line client
  pattern + regional gateway logic (reused verbatim where possible).
- [`copilot-studio-servicenow-bridge`](../copilot-studio-servicenow-bridge) —
  ACA deploy script + devtunnel pattern + docs structure.
