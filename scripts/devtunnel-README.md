# Devtunnel scripts (Granite Peak orders API)

Local dev needs the mock orders API reachable from Copilot Studio (HTTP
Request tools call out, can't reach `localhost`). We use **Microsoft Dev
Tunnels** for a stable public HTTPS URL during development. ACA hosting
replaces this in Phase 5.

## One-time install

```powershell
winget install Microsoft.devtunnel
devtunnel user login
```

## Scripts

| Script | Purpose |
|---|---|
| `devtunnel-create.ps1` | Create a persistent named tunnel + port forward 8000 |
| `devtunnel-host.ps1`   | Host the tunnel (foreground; prints public URL) |
| `devtunnel-delete.ps1` | Remove the tunnel + port forward |

## Typical flow

```powershell
# 1. Start orders API locally (separate terminal)
docker compose up -d
# or: uvicorn orders_api.main:app --host 0.0.0.0 --port 8000

# 2. Create + host tunnel
.\scripts\devtunnel-create.ps1
.\scripts\devtunnel-host.ps1
# -> prints https://<slug>-8000.use.devtunnels.ms

# 3. Plug that URL into Copilot Studio HTTP Request tools (one-time per
#    tunnel). Save it to ORDERS_API_BASE_URL in your local .env.

# 4. When you're done for the day, Ctrl-C the host process. The tunnel
#    persists; rerun devtunnel-host.ps1 next session and the URL is the
#    same.

# 5. To rotate / wipe:
.\scripts\devtunnel-delete.ps1
```

## Important quirks (per prior project memory)

- The **tunnel id** (e.g. `jolly-river-lw1s3ms.use`) and the **public URL
  slug** (e.g. `pbqgkr6d`) are different. Only the slug appears in the URL.
  Always derive the URL from `devtunnel host` output, not from the id.
- `--allow-anonymous` makes the tunnel callable without auth. Required for
  Copilot Studio HTTP Request tools (no auth header is sent on simple
  unauthed CS topics).
