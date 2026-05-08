# Phase 1c — Copilot Studio orders agent setup

This is the manual provisioning recipe for `awm_contosoorders`, the consumer
front-of-house orders agent the Foundry chat backend will delegate to. Use
**Studio UI** (not Dataverse `/botcomponents` script), per the user-memory
note that scripted flow-action bindings need a UI re-add anyway.

## Target Power Platform environment

| Field | Value |
|---|---|
| Organization URL | `https://orga5bae564.crm.dynamics.com` |
| Organization ID | `1870688f-653b-f111-83fa-6045bd023806` |
| Environment ID | `63b4b29b-b3b0-ed70-9136-524a53a22e06` |
| Region | United States |
| Type | Sandbox |
| Refresh cadence | Frequent |

## Prerequisites

- Mock orders API running locally **and reachable from Copilot Studio**
  (devtunnel — see [`scripts/devtunnel-README.md`](../scripts/devtunnel-README.md)).
- Public URL of the orders API in hand, e.g.
  `https://<slug>-8000.use.devtunnels.ms`.
- You can sign in to <https://copilotstudio.microsoft.com> in the target env.

## Step 1 — Create the agent

1. Go to <https://copilotstudio.microsoft.com>, switch to the env above.
2. **Create → New agent → Skip to configure.**
3. Settings:
   - **Name:** `Granite Peak Orders Agent`
   - **Description:** `Front-line orders, returns, and refund support for Granite Peak Outfitters customers.`
   - **Schema name:** Studio derives one (will be `awm_grantitePeakOrdersAgent` or similar — record exact value once created).
   - **Solution:** create or reuse a solution called `Granite Peak Orders` (publisher `awm`). Keeps the agent + topics export-cleanly later.
   - **Generative orchestration:** **Enabled** (per user preference rule — generative not classic).
4. After creation, open **Settings → Generative AI**:
   - **Allow ungrounded responses:** **On** (per user-memory rule for
     multi-turn agents; otherwise the agent fails over to fallback when
     asking follow-up questions).
   - **Content moderation:** High (default).
5. **Settings → Security → Authentication:** **No authentication** for v1.
6. **Channels → Web channel:** keep enabled (we mint Direct Line tokens
   from this).

## Step 2 — Capture the references

After save + first publish, collect from **Settings → Advanced**:

- Schema name (e.g. `awm_xyz123`)
- Bot id (Dataverse `bot.botid` GUID — visible in URL or Settings)
- AAD application id (under **Advanced → App registration** if visible)
- Direct Line token endpoint
  (`https://<env-host>/powervirtualagents/botsbyschema/<schema>/directline/token?api-version=2022-03-01-preview`)

Add them to your local `.env` (NOT committed):

```
CS_AGENT_SCHEMA_NAME=awm_xxxxx
CS_AGENT_APP_ID=<guid>
CS_ENVIRONMENT_API_HOST=63b4b29bb3b0ed709136524a53a22e.06.environment.api.powerplatform.com
CS_DIRECTLINE_TOKEN_ENDPOINT=https://63b4b29bb3b0ed709136524a53a22e.06.environment.api.powerplatform.com/powervirtualagents/botsbyschema/awm_xxxxx/directline/token?api-version=2022-03-01-preview
```

Then update `/memories/repo/cs-orders-agent.md` (file created in Phase 1c
once values exist).

## Step 3 — System instructions (agent-level)

In **Settings → Agent description / Instructions**, paste:

```
You are the Granite Peak Outfitters customer support assistant.
You help customers with order status, returns, refunds, and return policy
questions for Granite Peak Outfitters — a New England ski and bike retailer
based in Stowe, Vermont.

The current customer is always Riley Carter (customer id GP-1001) for v1
of this demo. Do not ask the customer to identify themselves.

Tone: friendly, concise, confident. Use plain language; no marketing
fluff. Use customer-facing phrases like "your order" rather than
internal jargon. Format prices as $X.XX. Format dates as "Apr 26".

When a customer asks about an order, returns, refunds, or the return
policy, use the available HTTP tools to look up real data. Do not
invent order ids, statuses, dates, tracking numbers, or prices.

If a request is unrelated to orders, returns, refunds, or the return
policy, politely say it's outside what you can help with and suggest
they contact a Granite Peak rep.
```

## Step 4 — HTTP Request tools (5 tools, one per data path)

Create under **Tools → Add a tool → New tool → HTTP request**. Replace
`<ORDERS_API_BASE_URL>` with the devtunnel URL from
`scripts/devtunnel-README.md` (or the ACA FQDN once Phase 5 deploys).

### Tool 1 — `get_order_status`

| Field | Value |
|---|---|
| Display name | Get order status |
| Description (LLM-facing) | Look up the current status, ship/delivery dates, tracking number, and contents of a customer's order by order id. Call this whenever the user asks about an order. |
| Method | GET |
| URL | `<ORDERS_API_BASE_URL>/orders/{order_id}` |
| Path inputs | `order_id` (string, required) — Granite Peak order id, e.g. `ORD-2026-1001` |
| Authentication | None |
| Response | Full JSON pass-through (the LLM reads the fields it needs). |

### Tool 2 — `list_my_orders`

| Field | Value |
|---|---|
| Display name | List my orders |
| Description | Return all of the current customer's orders. Use when the user says "my orders" or "what have I bought lately". |
| Method | GET |
| URL | `<ORDERS_API_BASE_URL>/customers/GP-1001/orders` |
| Inputs | none |
| Auth | None |

### Tool 3 — `check_return_eligibility`

| Field | Value |
|---|---|
| Display name | Check return eligibility |
| Description | Decide whether a given order is still inside the 30-day return window. Always call this BEFORE creating a return so the user gets accurate feedback if denied. |
| Method | GET |
| URL | `<ORDERS_API_BASE_URL>/orders/{order_id}/return-eligibility` |
| Path inputs | `order_id` (string, required) |
| Auth | None |

### Tool 4 — `create_return`

| Field | Value |
|---|---|
| Display name | Create return |
| Description | File a return for one item from one of the customer's orders. ALWAYS call check_return_eligibility first; if not eligible, do NOT call this and explain the reason to the user. |
| Method | POST |
| URL | `<ORDERS_API_BASE_URL>/returns` |
| Body (application/json) | `{"order_id": "{order_id}", "sku": "{sku}", "reason": "{reason}", "customer_id": "GP-1001"}` |
| Inputs | `order_id` (string), `sku` (string), `reason` (string) |
| Auth | None |

### Tool 5 — `get_return_policy`

| Field | Value |
|---|---|
| Display name | Get return policy |
| Description | Return Granite Peak's plain-text return policy. Use when the user asks about return rules, refund timing, exceptions, or the return window. |
| Method | GET |
| URL | `<ORDERS_API_BASE_URL>/policies/return` |
| Auth | None |

After every tool save: **Test → Tools** in Studio, invoke once with a
sample input, verify a 200 response.

## Step 5 — Topics (4 topics, generative orchestration trigger)

Generative orchestration picks topics by their **description**, not by
intent phrases or keywords. Each topic ends by formatting the tool result
back to the user. Keep responses short — large bodies cause the orchestrator
to truncate.

### Topic A — `OrderStatus`

| Field | Value |
|---|---|
| Trigger | `On agent — generative orchestration` |
| Description (LLM-facing) | The customer is asking about the status, shipping, delivery, contents, or tracking number of a specific order. |
| Inputs | `order_id` (string, required) — Granite Peak order id |
| Behavior | Call `get_order_status({order_id})`. Reply with one short paragraph: status, key date(s), tracking number if any, and a one-line list of items. |

### Topic B — `MyOrders`

| Field | Value |
|---|---|
| Trigger | `On agent — generative orchestration` |
| Description | The customer wants to see all their recent orders, e.g. "what have I bought" or "show me my orders". |
| Inputs | none |
| Behavior | Call `list_my_orders()`. Reply with up to 5 most recent orders as a markdown bullet list: `- ORD-..., placed Apr 18, status Delivered, $1,139.88`. |

### Topic C — `ReturnRequest`

| Field | Value |
|---|---|
| Trigger | `On agent — generative orchestration` |
| Description | The customer wants to start a return for a specific item from one of their orders. |
| Inputs | `order_id` (string, required), `sku` (string, optional) |
| Behavior | If `sku` is missing, call `get_order_status({order_id})` and ask the user which item to return. Then call `check_return_eligibility({order_id})`. If `eligible == false`, apologise and quote `reason`. If eligible, ask the user for a one-sentence reason, then call `create_return({order_id, sku, reason})`. Reply with the new `return_id` and refund amount. |

### Topic D — `ReturnPolicy`

| Field | Value |
|---|---|
| Trigger | `On agent — generative orchestration` |
| Description | The customer is asking about the return policy, return window, refund timing, or exceptions. |
| Behavior | Call `get_return_policy()` and answer in 2-3 short sentences, mentioning the 30-day window explicitly. |

## Step 6 — Smoke tests in the Studio Test pane

Use these prompts after publish. Expected behaviour annotated.

| # | Prompt | Expected |
|---|---|---|
| 1 | "What's the status of ORD-2026-1001?" | `OrderStatus` topic; replies with Delivered + UPS tracking + ski + boots line. |
| 2 | "Show me my orders." | `MyOrders` topic; bullet list, 6 orders. |
| 3 | "I want to return the boots from ORD-2026-1001." | `ReturnRequest`; eligibility 12 days, asks for reason, then files return. |
| 4 | "Return ORD-2026-0998." | `ReturnRequest`; eligibility check fails (65 days), denial message. |
| 5 | "What's your return policy?" | `ReturnPolicy`; ~2 sentences mentioning 30 days. |
| 6 | "What's the weather?" | Off-topic decline. |

## Step 7 — Publish

1. **Publish** the agent.
2. Confirm Direct Line token endpoint mints a token via
   `Invoke-RestMethod` (see Phase 0 verification pattern in
   `/memories/repo/cs-orders-agent.md` once we capture it).
3. Update `.env.sample` doc-only entries and capture working values in
   local `.env`.

## Step 8 — Capture into repo memory

Once values exist, create `/memories/repo/cs-orders-agent.md` with the same
shape as the Sterling-OMS-recovery file we used briefly:

```
- Display name, schema, bot id, AAD app id
- DL token endpoint
- Region suffix (will be -us)
- Tool names + URLs
- Topic names + descriptions
- Verification timestamp
```

That file is the source of truth for Phase 2 wiring.
