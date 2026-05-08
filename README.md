# Foundry → Copilot Studio Bridge

**Pattern demo:** an Azure AI Foundry model calling a Copilot Studio agent as a
tool — both surfaced through a single chat widget with no visible seam.

The key integration: Foundry's Responses API defines `ask_copilot_studio_agent`
as an OpenAI function tool. When the model decides a Copilot Studio agent should
answer, it invokes that tool; the bridge starts a Direct Line conversation with
the CS agent, polls for the reply, and streams it back. The user sees one
continuous chat. A source badge (`CONCIERGE` vs `ORDERS AGENT`) makes the
routing visible for demo purposes.

The specific agents here — a general concierge and an orders agent for a
fictional retailer — are stand-ins. Replace them with your own Foundry model and
CS agent; the bridge pattern stays the same.

**Live demo:**
`https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/`

---

## How the integration works

```
User message
      │
      ▼
  Foundry model (Azure OpenAI Responses API)
      │
      ├─ General question ──► answers directly           [CONCIERGE badge]
      │
      └─ Domain-specific ──► calls ask_copilot_studio_agent()
                                       │
                                       ▼
                             Direct Line (token endpoint)
                                       │
                             Copilot Studio agent
                             (generative orchestration)
                                       │
                             reply streamed back to user  [ORDERS AGENT badge]
```

The bridge (`app/cs_tool.py` + `app/cs_directline.py`) handles:
- minting a scoped Direct Line token
- starting the conversation and posting the user message
- polling for the CS agent reply
- packaging the text back as a Foundry tool result

Auth: system-assigned managed identity on the bridge app; no API keys in code.

Key files:
- [`app/cs_tool.py`](app/cs_tool.py) — Foundry tool descriptor + dispatch
- [`app/cs_directline.py`](app/cs_directline.py) — Direct Line session management
- [`app/foundry_client.py`](app/foundry_client.py) — Responses API loop, tool-call dispatch, SSE streaming

Full architecture: [docs/00-architecture-overview.md](docs/00-architecture-overview.md) · [docs/01-architecture.md](docs/01-architecture.md)

---

## Demo scenario

Retail front-end: **Granite Peak Outfitters** (fictional ski + bike shop, Stowe VT).

| Message | Routed to | Badge |
|---|---|---|
| "Do you sell mountain bikes?" | Foundry concierge | `CONCIERGE` |
| "List my orders" | Copilot Studio orders agent | `ORDERS AGENT` |
| "Cancel order ORD-2026-1300" | Copilot Studio orders agent | `ORDERS AGENT` |

The CS orders agent and its FastAPI/MCP backend are example implementations
only — not the point of the repo.

---

## Stack

| Component | Technology |
|---|---|
| Chat UI + `/api/chat` SSE | Flask (Python 3.11) |
| AI orchestration | Azure OpenAI Responses API |
| CS integration | Direct Line v3 (token-scoped per session) |
| Example CS agent | Copilot Studio (generative orchestration) |
| Example domain backend | FastAPI + MCP server (streamable HTTP) |
| Hosting | Azure Container Apps (`eastus2`) |
| Auth | System-assigned managed identity + RBAC |

---

## Local dev quick start

**Prerequisites:** Python 3.11+, Docker, Azure CLI, a devtunnel install.

```powershell
# Clone and set up
git clone <this-repo>
cd foundry-cc-bridge
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Copy and fill in env vars
Copy-Item .env.sample .env
# Edit .env — set CS_DIRECTLINE_TOKEN_ENDPOINT, FOUNDRY_PROJECT_ENDPOINT, etc.

# Start both services locally
docker compose up -d
# Bridge: http://localhost:5000
# Orders: http://localhost:8000

# Expose orders API to Copilot Studio (needed for CS MCP tool calls)
.\scripts\devtunnel-create.ps1
.\scripts\devtunnel-host.ps1   # prints public URL — paste into CS tool config
```

See [docs/02-cs-orders-setup.md](docs/02-cs-orders-setup.md) for Copilot Studio
provisioning and tool configuration.

---

## Deploying to Azure

See [docs/03-deployment-runbook.md](docs/03-deployment-runbook.md) for the
full build / push / deploy / verify procedure.

Quick summary:

```powershell
# Build and push (replace vMMDDHHMM with timestamp tag)
docker build -f Dockerfile.orders_api -t acrcpvb0c139ea.azurecr.io/granite-peak-orders:vMMDDHHMM .
docker push acrcpvb0c139ea.azurecr.io/granite-peak-orders:vMMDDHHMM

docker build -f Dockerfile.bridge -t acrcpvb0c139ea.azurecr.io/granite-peak-bridge:vMMDDHHMM .
docker push acrcpvb0c139ea.azurecr.io/granite-peak-bridge:vMMDDHHMM

# Deploy (always use --revision-suffix to force a new revision)
az containerapp update -n granite-peak-orders -g rg-cpv-aca \
  --image acrcpvb0c139ea.azurecr.io/granite-peak-orders:vMMDDHHMM \
  --revision-suffix vMMDDHHMM

az containerapp update -n granite-peak-bridge -g rg-cpv-aca \
  --image acrcpvb0c139ea.azurecr.io/granite-peak-bridge:vMMDDHHMM \
  --revision-suffix vMMDDHHMM
```

---

## Repo layout

```
app/                    Flask app — UI, /api/chat SSE, Foundry client, CS tool, orders tools
orders_api/             FastAPI orders backend — catalog, orders, returns, MCP server
scripts/                Deploy helpers, devtunnel scripts, CS provisioning utilities
cs-templates/           Copilot Studio export/import templates
docs/                   Architecture, setup, runbook, troubleshooting, demo guide
  diagrams/             Mermaid source (.mmd) + exported SVG architecture diagrams
Dockerfile.bridge       Container image for granite-peak-bridge
Dockerfile.orders_api   Container image for granite-peak-orders
docker-compose.yml      Local dev stack
.env.sample             Environment variable reference (copy to .env, never commit)
CHANGELOG.md            Release and milestone notes
plan.md                 Delivery phases and task tracking
```

---

## Documentation

| Doc | Purpose |
|---|---|
| [docs/00-architecture-overview.md](docs/00-architecture-overview.md) | Customer-friendly architecture with logical + physical diagrams |
| [docs/01-architecture.md](docs/01-architecture.md) | Technical deep dive — sequence flows, component map, identity model |
| [docs/02-cs-orders-setup.md](docs/02-cs-orders-setup.md) | Copilot Studio provisioning and MCP tool configuration |
| [docs/03-deployment-runbook.md](docs/03-deployment-runbook.md) | Build / push / deploy / verify / rollback |
| [docs/04-test-and-demo-guide.md](docs/04-test-and-demo-guide.md) | Demo script and acceptance criteria |
| [docs/05-troubleshooting.md](docs/05-troubleshooting.md) | Common failures and fixes |
| [docs/06-customer-one-pager.md](docs/06-customer-one-pager.md) | One-page executive summary |
