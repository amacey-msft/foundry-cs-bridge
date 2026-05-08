# Deployment Runbook

This runbook covers build, push, deploy, and verification for both runtime apps.

## 1) Target environment

- Subscription: `b0c139ea-82e8-4e26-94cc-d8e6dda0c4ec`
- Resource group: `rg-cpv-aca`
- ACA environment: `cae-cpv`
- Region: `eastus2`
- ACR: `acrcpvb0c139ea.azurecr.io`

Runtime apps:
- `granite-peak-orders` (FastAPI + MCP, port 8000)
- `granite-peak-bridge` (Flask UI + chat, port 5000)

## 2) Prerequisites

- Azure CLI logged in (`az login`)
- Acr push rights
- Container Apps contributor rights
- Copilot Studio agent already published

## 3) Build and push images

Orders API image:

```powershell
docker build -f Dockerfile.orders_api -t acrcpvb0c139ea.azurecr.io/granite-peak-orders:vMMDDHHMM .
docker push acrcpvb0c139ea.azurecr.io/granite-peak-orders:vMMDDHHMM
```

Bridge image:

```powershell
docker build -f Dockerfile.bridge -t acrcpvb0c139ea.azurecr.io/granite-peak-bridge:vMMDDHHMM .
docker push acrcpvb0c139ea.azurecr.io/granite-peak-bridge:vMMDDHHMM
```

## 4) Deploy with revision suffix

Always force a new revision using `--revision-suffix`.

Orders:

```powershell
az containerapp update `
  -n granite-peak-orders `
  -g rg-cpv-aca `
  --image acrcpvb0c139ea.azurecr.io/granite-peak-orders:vMMDDHHMM `
  --revision-suffix vMMDDHHMM
```

Bridge:

```powershell
az containerapp update `
  -n granite-peak-bridge `
  -g rg-cpv-aca `
  --image acrcpvb0c139ea.azurecr.io/granite-peak-bridge:vMMDDHHMM `
  --revision-suffix vMMDDHHMM
```

## 5) Required bridge configuration

Set as ACA env vars/secrets for `granite-peak-bridge`:

- `CS_DIRECTLINE_TOKEN_ENDPOINT`
- `CS_AGENT_SCHEMA_NAME`
- `CS_AGENT_APP_ID`
- `CS_ENVIRONMENT_API_HOST`
- `ORDERS_API_BASE_URL` (orders ACA FQDN)
- `FOUNDRY_PROJECT_ENDPOINT` (`https://awm-ai-svc.openai.azure.com/`)
- `FOUNDRY_MODEL_DEPLOYMENT` (`gpt-4.1-mini-gp`)
- `FOUNDRY_API_VERSION` (`2024-10-21`)
- `CS_BACKEND` (`directline`)

Managed identity requirement:
- Bridge system-assigned MI must have `Cognitive Services OpenAI User` role on `awm-ai-svc`.

## 6) Post-deploy verification (mandatory)

Revision status:

```powershell
az containerapp revision show -n granite-peak-bridge -g rg-cpv-aca --revision <latest-revision> --query "{active:properties.active,health:properties.healthState,traffic:properties.trafficWeight}" -o json
az containerapp revision show -n granite-peak-orders -g rg-cpv-aca --revision <latest-revision> --query "{active:properties.active,health:properties.healthState,traffic:properties.trafficWeight}" -o json
```

Expected:
- `active=true`
- `health=Healthy` (or transitional `None` briefly during start)
- `traffic=100`

Health checks:

```powershell
curl.exe -s https://granite-peak-orders.happyhill-34f7f143.eastus2.azurecontainerapps.io/healthz
curl.exe -s https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/healthz
```

## 7) End-to-end smoke

Product path:

```powershell
curl.exe -s -N -X POST "https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/api/chat" -H "Content-Type: application/json" -d "{\"message\":\"do you sell mountain bikes?\"}" --max-time 30
```

Order path:

```powershell
curl.exe -s -N -X POST "https://granite-peak-bridge.happyhill-34f7f143.eastus2.azurecontainerapps.io/api/chat" -H "Content-Type: application/json" -d "{\"message\":\"list my orders\"}" --max-time 60
```

## 8) Rollback

List revisions:

```powershell
az containerapp revision list -n granite-peak-bridge -g rg-cpv-aca --query "[].{name:name,active:properties.active,health:properties.healthState,traffic:properties.trafficWeight,created:properties.createdTime}" -o table
```

Switch traffic to prior stable revision if needed.
