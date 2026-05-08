<#
.SYNOPSIS
  Host the dev tunnel for the Granite Peak orders API (foreground).

.DESCRIPTION
  Prints the public HTTPS URL on startup. Ctrl-C to stop. The tunnel and its
  URL persist between hostings — Copilot Studio HTTP Request tools can
  reference the same URL across runs.
#>
[CmdletBinding()]
param(
  [string] $TunnelName = "foundry-cs-orders-api"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Hosting dev tunnel '$TunnelName' (Ctrl-C to stop)" -ForegroundColor Cyan
& devtunnel host $TunnelName
