# Plan: Foundry Agent → Copilot Studio (Orders) Demo

**New repo, new workspace folder.** Sibling to `copilot-studio-servicenow-bridge` and
`copilot-studio-acs-voice` under `c:\Users\alanmacey\OneDrive - Microsoft\source\`.

## Working name
**`foundry-cs-bridge`** (locked). Folder + GitHub repo both use this name.

## TL;DR
External-facing **Foundry Agent Service** consumer chat agent (intent gatherer +
front end) delegates orders / returns / refunds to a **Copilot Studio** agent via
**A2A**. Repo shows two wiring options because A2A maturity varies per tenant:
- **Primary path:** Foundry Agent Service `A2APreviewTool` → CS agent's A2A
  endpoint (Direct Engine). Microsoft-native, preview but recommended.
- **Fallback path:** Foundry agent function-tool → Direct Line REST wrapper
  around CS (lifted from `copilot-studio-acs-voice/app/directline.py`). Works
  on any CS license tier. Use when A2A blocked.

Web-only consumer UI (no Teams, no voice, no SN handoff in v1 — backlog).

## Reference repos already in user's source tree
- `copilot-studio-servicenow-bridge` — current repo. Reuse: ACA deploy script
  pattern, devtunnel scripts, docs structure (00-architecture-overview / 01-
  architecture / etc.), `bridge/.env`-driven config, `BRIDGE_PUBLIC_URL` sync
  helper, Dockerfile + compose mounts, two-CS-agent topology lessons,
  `teams_a2a/` empty-200 monkey-patch (only relevant if we ever go reverse
  direction).
- `copilot-studio-acs-voice` — closest analog. Foundry realtime model already
  delegates to CS via Direct Line. Reuse VERBATIM where possible:
  - `app/directline.py` — regional DL gateway parser + activity-id echo filter
  - `app/realtime_tools.py` — `ask_copilot_studio` function tool shape
  - `app/system_prompt.md` — delegation prompt style
  - `app/config.py` — env loader pattern
  - `app/session.py` — per-session state
  - `Dockerfile` + `docker-compose.yml` + `scripts/devtunnel-*.ps1`
  - `docs/` 5-file structure (architecture / setup / CS / e2e / troubleshooting)

## Key prior-art memory (reload before coding)
- User memory `copilot-studio-skill-handoff.md` — A2A empty-200 bug, CS Entra
  Agent ID auth quirks
- User memory `debugging.md` — DL token regional gateway, DL `from.id`
  rewrite, CS agent topic visibility for orchestration, ACA `--revision-suffix`
  rule for secret rotation
- User memory `preferences.md` — Phase 0 branch + draft PR rule, doc updates in
  every plan, post-deploy revision/health verify, generative orchestration
  default, scripts not ad-hoc terminal blocks
- Repo memory of `copilot-studio-servicenow-bridge` (cs-agent-ids.md,
  web-channel-agent.md) — reference only; new repo gets its own

## Blockers identified in deep-dive (all addressable)
1. Connected Agents (classic) deprecated — use A2A tool / workflow path
2. Foundry hosted agent doesn't natively expose A2A — irrelevant (we consume CS, not the reverse)
3. Identity rebind on Foundry publish — re-grant role to distinct identity post-publish
4. Audience mismatch on Entra A2A token — must match CS agent resource id, not URL
5. User-scoped CS topics need OAuth identity passthrough (multi-hop OBO undocumented end-to-end). v1 use shared identity / read-only demo data; OBO is v2.
6. Foundry Agent Application = stateless Responses API — client tracks history
7. Long-running CS topics > sync A2A timeout — tighten CS topics, defer slow work
8. No proactive push from CS back into Foundry — async events use callback webhook (v2)
9. M365 Agents SDK empty-200 bug — does NOT affect Foundry A2A tool (different stack)
10. CS Studio "Add an agent" picker auth ≠ Foundry connection auth — asymmetric, OK since direction is fixed
11. CS agent-as-A2A-endpoint requires CS Standalone license + tenant flag
12. No shared trace correlation — pass `x-correlation-id` custom header
13. Tool-call recursion depth — set tool_choice rules

## Phases

### Phase 0 — Repo bootstrap (per user rule)
1. Create new folder `copilot-studio-foundry-orders-bridge` sibling to current repo.
2. Switch VS Code workspace; reload plan from `/memories/session/plan.md`.
3. `git init`, push to `amacey-msft/copilot-studio-foundry-orders-bridge` (new GH repo).
4. Create branch `feat/initial-scaffold`, push, open draft PR.

### Phase 1 — Copilot Studio orders agent
1. Create new CS agent (working name in plan: `awm_contosoorders`; actual
   display name once provisioned: **Granite Peak Orders Agent** — see
   `docs/02-cs-orders-setup.md` for the full provisioning recipe).
   Generative orchestration (per user preferences rule). Topics:
   OrderStatus, MyOrders, ReturnRequest, ReturnPolicy. Each topic uses
   HTTP Request tool against the in-repo `orders_api/` (FastAPI) reachable
   over devtunnel.
2. Stub orders API returns deterministic mock data keyed by order id (no
   real Power Platform connectors in v1; keeps demo self-contained).
3. Topic instructions tightened to short responses (avoid sync A2A timeout).
4. Enable "Allow ungrounded responses" on agent (per repo memory rule for
   multi-turn).
5. Capture: agent schema name, env id, agent app id, DL token endpoint,
   A2A endpoint URL (when Direct Engine A2A enabled — see Phase 3).
6. Save to new `/memories/repo/cs-orders-agent.md`.

### Phase 2 — Foundry agent (fallback path: Direct Line tool wrapper)
1. New Foundry project + agent definition. Model: `gpt-4.1-mini` (cheap; bump
   later if needed).
2. `app/` mirrors acs-voice layout but text-only. Files:
   - `app/app.py` — Flask, routes `/`, `/healthz`, `/api/chat` (SSE stream),
     `/directline/token` (mints CS DL token for client if we ever expose
     direct mode).
   - `app/foundry_client.py` — Foundry Responses API client (DefaultAzureCredential,
     stateless threading by client-passed history per limitation #6).
   - `app/cs_directline.py` — verbatim port of acs-voice's `directline.py`.
   - `app/cs_tool.py` — function tool `ask_copilot_studio_orders` (mirrors
     acs-voice `realtime_tools.py` shape).
   - `app/session.py` — in-memory per-session conversation store
     (single-replica caveat documented like SN bridge).
   - `app/system_prompt.md` — front-end persona, delegation rules.
   - `app/config.py` — env loader.
3. Front-end **retail demo site** (see Phase 2.5).
4. Local dev via `docker-compose.yml` + `Dockerfile` (mirrored from acs-voice).
5. Devtunnel scripts copied verbatim; `BRIDGE_PUBLIC_URL` pattern for any
   webhook (none in v1, but scaffold).

### Phase 2.5 — Retail demo web front end
**Reference:** `c:\Users\alanmacey\OneDrive - Microsoft\source\GovSite-amd-copy\`
(Flask + Jinja templates + themed pages + Direct Line WebChat). Concept reused;
implementation diverges because Foundry Agent Service exposes **Responses API**,
not Direct Line — so botframework-webchat can't be dropped in. We ship a custom
chat widget that streams from our `/api/chat` SSE.

1. **Retail brand: "Granite Peak Outfitters"** — fictional New England ski &
   bike retailer (Vermont/New Hampshire vibe). Catalog split between winter
   (skis, snowboards, boots, jackets) and summer (mountain bikes, road bikes,
   helmets, bike packs). Tagline candidate: "Gear for the Green Mountains."
   Alternative names if user reject: Birchline Sports, Stowe & Stone,
   Mt. Mansfield Outfitters, Notch & Trail.
2. **Page set** (Jinja templates under `templates/`):
   - `home.html` — hero banner (seasonal: ski lead in winter / bike lead in
     summer; for v1 ship the ski hero), two-column "Shop Skis" / "Shop Bikes"
     promo, featured products grid (3 ski + 3 bike), footer with fake store
     locations (Stowe VT, North Conway NH, Killington VT)
   - `product.html` — single product detail (price, description, "Add to
     cart", "Returns" link, spec table)
   - `account.html` — fake "Your Orders" page with mock order list (the data
     mirrors what the CS orders agent's mock backend serves, so when the user
     asks the chat about ORD-1234 it lines up with what they see on screen).
     Mix of ski + bike orders.
   - `base.html` — shared header/nav/footer, includes chat widget partial
3. **Static assets** under `static/`:
   - `css/site.css` — New England retail theme. Palette: deep forest green
     (#1f3a2e), birch white (#f4efe6), maple red accent (#a8341f), slate
     (#3c4a52). Serif display font for headings (e.g. Playfair Display via
     Google Fonts), sans-serif body (Inter). Rounded cards, generous
     whitespace.
   - `css/chat.css` — chat widget styling (lifted/adapted from SN bridge
     `web/intranet.html` panel)
   - `js/chat.js` — custom chat widget. Opens SSE to `/api/chat`, posts
     messages, renders markdown replies, shows typing indicator. NO
     botframework-webchat dependency.
   - `images/` — **inline SVG placeholders only**, no binary assets. Best for
     a shareable GitHub solution (no LFS, no licensing question, no broken
     CDN links, deterministic appearance, lighter clone). Each product card
     gets an SVG built from the brand palette with a stylized icon
     (ski/snowboard/jacket/bike/helmet) over a textured background. One
     hero SVG (mountain silhouette + pine trees + sky gradient). Keep SVGs
     under `static/images/*.svg`, served as static files. No external image
     CDN dependency.
4. **Flask routes** (`app/app.py` extensions):
   - `GET /` → `home.html`
   - `GET /product/<sku>` → `product.html`
   - `GET /account` → `account.html`
   - `POST /api/chat` (SSE) → already in scope from Phase 2; widget posts here
   - `GET /api/chat/session` → mints/returns a stable session id (cookie)
5. **Chat widget UX** (matches SN bridge intranet pattern):
   - Floating launcher button bottom-right with unread badge
   - Slide-up panel with greeting "Welcome to Granite Peak. Ask me about
     orders, returns, or gear."
   - Quick-reply chips: "Track an order", "Start a return", "Refund status",
     "Ski boot sizing"
   - Markdown rendering for agent replies (use `marked` from CDN)
   - Persist conversation in sessionStorage so panel close/open preserve
6. **No Direct Line on the client.** All traffic flows browser → our Flask
   backend → Foundry Agent Service → CS A2A. Foundry RBAC stays server-side.
   This is the key divergence from GovSite: GovSite mints DL tokens for the
   browser to talk straight to CS; we can't because Foundry has no DL.
7. **Mobile responsive** — full-width chat panel below 768px, otherwise
   400px panel.
8. **Mock catalog data** in `app/catalog.py` — list of ~12 products
   (6 ski + 6 bike) with sku, name, price, category, hero color, icon name.
   Same data feeds the home grid, product detail page, and the orders mock
   (so an order references real catalog SKUs).

### Phase 3 — Foundry agent (primary path: A2A tool to CS)
1. Enable Copilot Studio Direct Engine A2A on the CS orders agent (verify
   tenant/license; if blocked, document blocker and stick with Phase 2
   Direct Line fallback).
2. Foundry portal: Tools → Connect tool → Custom → Agent2Agent (A2A). Set
   endpoint to CS agent card URL. Auth: agent identity (Entra). Save
   connection name as `cs_orders_a2a`.
3. Replace `cs_tool.py` with `A2APreviewTool` configuration. Keep
   `cs_directline.py` as backup module enabled by env flag
   `CS_BACKEND=a2a|directline`.
4. Grant Foundry shared project agent identity invoke role on CS agent
   resource. Smoke test unpublished.
5. Publish Foundry agent as Agent Application. Re-grant role to NEW distinct
   agent identity (blocker #3 — easy to forget).
6. Verify with `curl` against Agent Application Responses API endpoint.

### Phase 4 — Tracing + correlation
1. Add `x-correlation-id` header propagation through Foundry → CS A2A.
2. Structured logging with the correlation id in every log line.
3. Wire Application Insights (per `appinsights-instrumentation` skill).

### Phase 5 — Deploy to ACA
1. `scripts/deploy-foundry-bridge-aca.ps1` — adapted from existing
   `scripts/deploy-bridge-aca.ps1`. ACR build + ACA create/update with
   env-from-secret bindings. `--revision-suffix vMMDDHHMM` per user rule.
2. Post-deploy verify: revision Healthy, 100% traffic, old drained, `/healthz`
   green. REPORT before user tests.
3. Document single-replica caveat (in-memory session state) — matches SN
   bridge precedent.

### Phase 6 — Docs + CHANGELOG
Mirror acs-voice 5-file docs layout:
- `docs/00-architecture-overview.md` (high-level diagram)
- `docs/01-architecture.md` (component detail)
- `docs/02-cs-orders-setup.md` (CS agent provision + A2A enable)
- `docs/03-foundry-setup.md` (project, agent, A2A connection, publish)
- `docs/04-end-to-end-test.md` (smoke + happy path + 3 failure modes)
- `docs/05-troubleshooting.md` (the 13 blockers with fix recipes)
- `README.md` quickstart
- `CHANGELOG.md` initial

## Verification (Phase-by-phase)

Phase 1 (CS agent):
- CS test pane: "what's my order status for ORD-1234?" → returns mock data
- CS test pane: "I want to return ORD-9999" → returns mock return flow
- HTTP request tool latency p95 < 2s

Phase 2 (Foundry + DL fallback):
- `python -m app.foundry_client "track order ORD-1234"` → Foundry agent
  routes to `ask_copilot_studio_orders` tool → CS reply piped back
- Web UI happy path
- Failure: stop orders API → graceful "(error contacting orders agent)"

Phase 3 (A2A primary):
- Smoke: `curl Foundry Agent Application Responses endpoint` with
  `Authorization: Bearer <ai.azure.com token>`
- Confirm distinct agent identity has invoke on CS post-publish (azqr or
  manual `az role assignment list`)
- Check trace shows two-hop: Foundry → A2A → CS

Phase 5 (deploy):
- `az containerapp revision list` shows new suffix Healthy / 100%
- `/healthz` 200
- Real chat turn via deployed URL

## Decisions / scope
- **Demo, not production.** Single-replica ACA, mock orders API, no OBO.
- **Web only.** No Teams, no voice, no ServiceNow handoff in v1.
- **Generative orchestration** for CS agent (per user rule).
- **Fallback Direct Line path** kept in code so demo works even if A2A blocked
  by tenant/license — switchable by env flag.
- **No OBO** v1; all CS calls under shared agent identity. v2 if user-scoped
  data needed.

## Files to create (full paths once new folder named)
```
<root>/
  README.md
  CHANGELOG.md
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.sample
  .gitignore
  app/
    __init__.py
    app.py
    foundry_client.py
    cs_directline.py
    cs_tool.py
    session.py
    system_prompt.md
    config.py
  orders_api/
    __init__.py
    main.py            # FastAPI stub
    mock_data.py
  templates/           # Jinja2 retail site
    base.html
    home.html
    product.html
    account.html
    _chat_widget.html  # included in base.html
  static/
    css/
      site.css
      chat.css
    js/
      chat.js
    images/
      hero-mountains.svg
      ski-1.svg ... ski-6.svg
      bike-1.svg ... bike-6.svg
      logo.svg
  web/                 # legacy/spare; or remove if templates/ covers all
  scripts/
    deploy-foundry-bridge-aca.ps1
    devtunnel-create.ps1
    devtunnel-host.ps1
    devtunnel-delete.ps1
    devtunnel-README.md
    sync-bridge-url.ps1
  docs/
    00-architecture-overview.md
    01-architecture.md
    02-cs-orders-setup.md
    03-foundry-setup.md
    04-end-to-end-test.md
    05-troubleshooting.md
```

## Context restoration on folder switch
After user creates folder + switches workspace:
1. Read this plan file.
2. Read `/memories/session/` for any updates.
3. Read user memory `copilot-studio-skill-handoff.md`, `debugging.md`,
   `preferences.md` (auto-loaded).
4. If acs-voice patterns needed, read directly from
   `c:\Users\alanmacey\OneDrive - Microsoft\source\copilot-studio-acs-voice\app\`
   (path exists outside new workspace).
5. Reference SN bridge ACA deploy script at
   `c:\Users\alanmacey\OneDrive - Microsoft\source\copilot-studio-servicenow-bridge\scripts\deploy-bridge-aca.ps1`.

## Further considerations to confirm with user
1. **A2A enabled in tenant?** If unknown, start with Direct Line fallback
   (Phase 2 only) and tackle A2A as Phase 3 once confirmed.
2. **Mock orders API vs real connector?** Plan assumes self-contained mock for
   demo simplicity. If user wants real Dataverse/D365, scope expands.
3. **Voice demo?** acs-voice already covers voice. v1 here = web text. Voice
   could be unified later by pointing acs-voice at this Foundry agent
   instead of CS directly.
4. **Repo name confirm.** ~~`copilot-studio-foundry-orders-bridge` long;
   alternatives: `foundry-cs-orders`, `foundry-cs-bridge`.~~ **LOCKED:
   `foundry-cs-bridge`.**
5. **Retail brand name.** Default **Granite Peak Outfitters** (New England
   ski + bike retailer). Alternatives: Birchline Sports, Stowe & Stone,
   Mt. Mansfield Outfitters, Notch & Trail.
6. **Product images.** **Inline SVG only** — best for shareable GitHub
   solution (no LFS, no licensing, no CDN). Decision locked unless user
   override.
