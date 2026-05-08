<#
.SYNOPSIS
  Delete the Granite Peak orders API dev tunnel.

.DESCRIPTION
  Removes the named tunnel and all of its port forwards. Confirms first.
#>
[CmdletBinding()]
param(
  [string] $TunnelName = "foundry-cs-orders-api"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Deleting dev tunnel '$TunnelName'" -ForegroundColor Yellow
& devtunnel delete $TunnelName
