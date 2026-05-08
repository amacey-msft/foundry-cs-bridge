# Troubleshooting

## 1) Order actions fail but product chat works

Symptoms:
- `CONCIERGE` path works
- `ORDERS AGENT` path returns access/connection error

Likely cause:
- Copilot Studio MCP tool uses per-user credential and anonymous Direct Line user has no consent.

Fix:
- In Copilot Studio tool config, use shared maker credential.
- Save and publish the agent again.

## 2) CS test pane works but website flow fails

Likely cause:
- Test pane runs as maker identity; website runs as anonymous DL user.

Fix:
- Same as above: shared credential config for MCP tool.

## 3) Bridge health is OK but model responses fail

Check:
- Bridge MI role on AI resource (`Cognitive Services OpenAI User`).
- `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL_DEPLOYMENT` values.

## 4) Old code still served after deploy

Likely cause:
- image tag updated but no new ACA revision or browser cache stale.

Fix:
- Deploy with `--revision-suffix vMMDDHHMM`.
- Verify new revision active + traffic 100.
- Browser hard refresh (Ctrl+F5).

## 5) Orders API tool calls fail from CS

Check:
- Orders app `/healthz` reachable.
- MCP endpoint `/mcp` reachable from CS connector config.
- CS connector still points to current orders endpoint.

## 6) Chat stream hangs or partial text only

Check:
- Bridge logs for exceptions in `foundry_client` or `cs_directline`.
- Confirm gunicorn still running with gthread worker.

## 7) Useful commands

Bridge logs:

```powershell
az containerapp logs show -n granite-peak-bridge -g rg-cpv-aca --tail 200
```

Orders logs:

```powershell
az containerapp logs show -n granite-peak-orders -g rg-cpv-aca --tail 200
```

Revision status:

```powershell
az containerapp revision list -n granite-peak-bridge -g rg-cpv-aca --query "[].{name:name,active:properties.active,health:properties.healthState,traffic:properties.trafficWeight}" -o table
```
