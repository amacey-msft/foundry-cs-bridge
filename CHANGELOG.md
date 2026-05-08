# Changelog

All notable changes to this repo are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions track
demo milestones, not semver release cadence.

## [Unreleased]

### Added
- Architecture documentation pack:
  - `docs/00-architecture-overview.md` with plain-language logical and
    physical architecture diagrams for customer walkthroughs.
  - `docs/01-architecture.md` with detailed component responsibilities,
    runtime sequence diagrams, identity model, deployment inventory, and
    demo walkthrough map.
  - `docs/03-deployment-runbook.md` with build/push/deploy/verify/rollback
    procedure for ACA.
  - `docs/04-test-and-demo-guide.md` with acceptance criteria and demo
    script.
  - `docs/05-troubleshooting.md` with common failure patterns and fixes.
  - `docs/06-customer-one-pager.md` for customer-facing architecture
    storytelling.
  - `docs/README.md` documentation index.
  - `docs/diagrams/*.mmd` source + exported `docs/diagrams/*.svg`
    architecture assets.
  - `README.md` links to both architecture documents for quick discovery.
- **Phase 2.5 — Granite Peak retail website + concierge chat** (live):
  - Static site: `app/static/index.html`, `site.css`, `chat.js`,
    `catalog.js`. Vermont mountain-sport branding, hero, catalog grid
    (proxied from orders API `/catalog` via new bridge route
    `GET /api/catalog`), floating chat launcher, SSE-streamed assistant
    bubbles.
  - Bridge Flask routes added: `GET /` (serves index), `GET /api/catalog`
    (server-side proxy to orders API).
  - **Direct orders tools for the Foundry concierge** (`app/orders_tools.py`):
    `list_my_orders`, `get_order`, `check_return_eligibility`,
    `create_return`, `get_return_policy`. Foundry calls these directly
    against the ACA orders API and answers in-line. CS Direct Line tool
    (`ask_granite_peak_orders`) kept as fallback.
  - System prompt rewritten (`app/system_prompt.md`) to route order
    questions to the new dedicated tools first.
  - Bridge ACA app `granite-peak-bridge` deployed to ACR
    `acrcpvb0c139ea` / RG `rg-cpv-aca` / env `cae-cpv`. Image tag
    `v05081900` on revision `granite-peak-bridge--v05081900` (Healthy,
    100% traffic). Public URL:
    `https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/`.
  - System-assigned MI granted `Cognitive Services OpenAI User` on
    `awm-ai-svc` so Foundry calls succeed without an API key.
  - End-to-end smoke (2026-05-08): product question ("do you sell
    mountain bikes?") and order question ("can you list my orders?")
    both stream natural answers from the same chat widget.

### Known issue
- Copilot Studio MCP TaskDialog (`awm_granitepeakorders.action.GranitePeakOrdersMCPServer`)
  is provisioned + connection bound + bot republished, but the CS
  orchestrator does NOT dispatch to ACA `/mcp/` (zero CS-origin POSTs in
  ACA logs). Per repo memory rule, API-provisioned actions need a manual
  remove + re-add in the Studio Tools UI before the orchestrator picks
  them up. Until that is done, the CS DL escalation tool will fail; the
  direct Foundry orders tools cover the demo path in the meantime.

- Initial repo scaffold: `.gitignore`, `README.md`, `CHANGELOG.md`, `plan.md`
  (full delivery plan recovered from prior session).
- Phase 0 done: GitHub repo `amacey-msft/foundry-cs-bridge` (private), branch
  `feat/initial-scaffold`, draft PR #1.
- **Phase 1 mock orders API** (`orders_api/`): FastAPI app with Granite Peak
  Outfitters catalog (6 winter + 6 summer SKUs), single demo customer
  Riley Carter (`GP-1001`), 6 seeded orders covering all status paths
  (Delivered eligible, Delivered ineligible, Processing, Shipped), 1 seeded
  return. Endpoints: `/healthz`, `/catalog`, `/customers/{id}`,
  `/customers/{id}/orders`, `/customers/{id}/returns`, `/orders/{id}`,
  `/orders/{id}/return-eligibility`, POST `/returns`, `/returns/{id}`,
  `/returns?customer_id=&order_id=`, `/policies/return`. Smoke-tested
  against `uvicorn` (2026-05-08).
- `requirements.txt` (FastAPI + uvicorn + pydantic), `Dockerfile.orders_api`,
  `docker-compose.yml`, devtunnel scripts (`scripts/devtunnel-*.ps1` +
  README).
- `docs/02-cs-orders-setup.md` — manual Studio provisioning recipe for the
  Granite Peak Orders Agent (4 topics, 5 HTTP tools, system instructions,
  smoke prompts), targeting Power Platform env
  `63b4b29b-b3b0-ed70-9136-524a53a22e06`.
- `.env.sample` updated with env reference comments.
- **Phase 2 chat backend (in progress)**: Flask app (`app/app.py`) exposing
  `GET /healthz`, `GET /api/chat/session`, `POST /api/chat` (SSE).
  - `app/config.py` env-driven constants + `assert_directline_configured()`.
  - `app/session.py` thread-safe `SessionStore` keyed by browser session id.
  - `app/cs_directline.py` Direct Line REST polling client (regional
    gateway derived from `streamUrl`; activity-id echo filter; `ask()`
    one-turn convenience), ported from `copilot-studio-acs-voice`.
  - `app/system_prompt.md` Granite Peak concierge persona.
  - `app/cs_tool.py` `ask_granite_peak_orders` function tool descriptor +
    dispatcher.
  - `app/foundry_client.py` Azure OpenAI Responses-API tool loop with
    `DefaultAzureCredential`; falls back to a deterministic stub that
    delegates straight to Copilot Studio when `FOUNDRY_PROJECT_ENDPOINT`
    is unset (so the stack is demo-able before the Foundry deployment
    exists).
  - `Dockerfile.bridge` (gunicorn gthread) + `docker-compose.yml`
    `bridge` service depending on `orders_api` healthcheck.
  - `requirements.txt` adds `flask`, `gunicorn`, `requests`,
    `python-dotenv`, `openai`, `azure-identity`.
  - `tests/test_bridge.py` + `tests/test_cs_directline.py` (8 cases): SSE
    stub path, session cookie reuse, `/healthz`, empty-body 400,
    region-host derivation. Total suite: 20 passed.

### Reverted
- Briefly considered reusing the SterlingOMS_Template CS agents on
  2026-05-08 (commit `24c75b2`); reverted same day. Original plan stands:
  greenfield `awm_contosoorders` CS agent + in-repo mock orders API +
  Granite Peak ski/bike SKUs end-to-end. Sterling reuse blocked by data
  mismatch (Sterling product catalog ≠ Granite Peak ski/bike).
