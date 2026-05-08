# Test and Demo Guide

This guide is for customer-facing demo runs and regression checks.

## 1) Demo objective

Show one chat UX that can:
- answer product questions (Foundry concierge)
- complete order tasks (Copilot Studio Orders Agent)
- keep one continuous user conversation

## 2) Pre-demo checklist

- Bridge latest revision active + healthy + 100% traffic.
- Orders latest revision active + healthy + 100% traffic.
- Copilot Studio agent published.
- MCP tool configured with shared maker credential.
- Browser hard refresh to load latest chat.js and styles.

## 3) In-app demo script (recommended)

1. Open site URL.
2. Ask: `Do you sell mountain bikes for trail riding?`
3. Explain badge `CONCIERGE`.
4. Ask: `List my orders.`
5. Explain badge `ORDERS AGENT`.
6. Ask: `Cancel order ORD-2026-1300.`
7. Explain business policy response from order-domain agent.
8. Ask follow-up product question to show return to concierge path.

## 4) Acceptance criteria

- User sees one chat widget only.
- Product prompt returns product-focused answer.
- Order prompt returns real order data (6 seeded orders).
- Source badge changes correctly by path.
- No request hangs or tool errors in UI.

## 5) API smoke set

Bridge health:

```powershell
curl.exe -s https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/healthz
```

Catalog proxy:

```powershell
curl.exe -s https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/api/catalog
```

Orders health:

```powershell
curl.exe -s https://granite-peak-orders.happyhill-34f7f143.eastus2.azurecontainerapps.io/healthz
```

## 6) Troubleshoot quickly during demo

- If order prompt fails with connection-required text, recheck CS MCP shared credential config and republish.
- If all chat prompts fail, check bridge revision health and container logs.
- If model calls fail, verify MI role assignment on `awm-ai-svc`.
