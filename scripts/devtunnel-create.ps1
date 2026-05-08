<#
.SYNOPSIS
  Create a persistent dev tunnel for the Granite Peak orders API (port 8000).

.DESCRIPTION
  Idempotent. Reuses the named tunnel if it already exists. Anonymous access
  enabled because Copilot Studio HTTP Request tools call out without auth.
#>
[CmdletBinding()]
param(
  [string] $TunnelName = "foundry-cs-orders-api",
  [int]    $Port       = 8000
)

$ErrorActionPreference = "Stop"

Write-Host "==> Creating dev tunnel '$TunnelName' for port $Port" -ForegroundColor Cyan

$existing = & devtunnel list 2>$null | Select-String -Pattern $TunnelName
if ($existing) {
  Write-Host "    Tunnel already exists; skipping create."
} else {
  & devtunnel create $TunnelName --allow-anonymous | Out-Host
}

# Add the port forward (idempotent — devtunnel returns non-zero if it
# already exists; that's fine).
& devtunnel port create $TunnelName --port-number $Port --protocol https 2>$null | Out-Null

Write-Host "    Done. Run scripts/devtunnel-host.ps1 to start hosting."
