<#
.SYNOPSIS
Clone Order Management System Agent family and reseed with Granite Peak data.

.DESCRIPTION
1. Clone 6 agents: Order Management System Agent (orchestrator) + 5 children
2. Rename to Granite Peak Orders Agent family
3. Update instructions: RL- → GP-, reseed product SKUs
4. Map API endpoints to granite-peak-orders FastAPI

.PARAMETER OrgUrl
Dataverse org URL (default: https://orga5bae564.crm.dynamics.com)

.PARAMETER SolutionName
Solution to add cloned components (default: GenericOrderManagementSystem)
#>

param(
    [string]$OrgUrl = "https://orga5bae564.crm.dynamics.com",
    [string]$SolutionName = "GenericOrderManagementSystem"
)

$ErrorActionPreference = "Stop"

# Get token
Write-Host "Getting Dataverse token..." -ForegroundColor Cyan
$token = az account get-access-token --resource $OrgUrl --query 'accessToken' -o tsv

if (-not $token) {
    throw "Failed to get token"
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
    "Prefer" = "return=representation"
}

$API = "$OrgUrl/api/data/v9.2"

# Agent IDs to clone (source OMS agents)
$agentMap = @{
    "812147d0-3c69-4d6c-bd8e-7c4c086c50c4" = "Order Management System Agent"
    "84e89eb3-333b-417a-bac6-4c775838d948" = "My Orders Agent"
    "1657cd75-bf3c-f111-bec6-000d3a5c574a" = "Order Management Agent"
    "16418819-1163-456c-8717-36fc63d758ce" = "Order Lookup Agent"
    "c0d865c8-b9be-4c3f-b9df-b60085c2fd4d" = "Return Eligibility Agent"
    "814f03c8-7cf5-479b-b930-30ff808d7860" = "Process Return Agent"
}

Write-Host "`nCloning Order Management System Agent family to Granite Peak..." -ForegroundColor Cyan

$clonedIds = @{}

foreach ($origId in $agentMap.Keys) {
    $origName = $agentMap[$origId]
    
    # Rename: "Order Management Agent" → "Granite Peak Orders Agent"
    #         "My Orders Agent" → "Granite Peak Orders - My Orders Agent"
    if ($origName -eq "Order Management System Agent") {
        $newName = "Granite Peak Orders System Agent"
    } else {
        $newName = "Granite Peak Orders - " + $origName
    }
    
    Write-Host "  Cloning: $origName → $newName" -ForegroundColor Yellow
    
    # GET original agent full record
    $url = "$API/botcomponents($origId)"
    $orig = Invoke-RestMethod -Uri $url `
        -Headers @{Authorization = $headers["Authorization"]; "Content-Type" = "application/json"} `
        -Method Get
    
    # Prepare clone: replace product references and names
    $newData = $orig.data `
        -replace "Order Management Agent", "Granite Peak Orders Agent" `
        -replace "RL-\w+", {
            # Map sample product SKUs
            $map = @{
                "RL-SKIN-START-KIT" = "GP-SKI-BOOTS-ENTRY"
                "RL-HAIR-ESS-KIT" = "GP-MTN-BIKE-29ER"
                "RL-" = "GP-"
            }
            $orig = $_.Value
            foreach ($k in $map.Keys) {
                if ($orig.StartsWith($k) -and $k -ne "RL-") {
                    return $map[$k]
                }
            }
            return $map["RL-"] + $orig.Substring(3)
        }
    
    $cloneBody = @{
        name = $newName
        componenttype = $orig.componenttype
        data = $newData
        language = $orig.language
    }
    
    # POST new agent to Dataverse
    $postUrl = "$API/botcomponents"
    $result = Invoke-RestMethod -Uri $postUrl `
        -Headers $headers `
        -Method Post `
        -Body (ConvertTo-Json $cloneBody -Depth 10)
    
    $newId = $result.botcomponentid
    $clonedIds[$origId] = @{newId = $newId; newName = $newName}
    Write-Host "    Created: $newId" -ForegroundColor Green
}

Write-Host "`n✓ Cloned 6 agents successfully" -ForegroundColor Green

# Save mapping for reference
$mapping = @{
    timestamp = (Get-Date -Format 'yyyy-MM-dd HHmmss')
    clones = $clonedIds
}

$mappingFile = "scripts\clone-agent-mapping.json"
ConvertTo-Json $mapping -Depth 10 | Set-Content $mappingFile
Write-Host "Saved mapping to $mappingFile`n" -ForegroundColor Green

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Map API endpoints in cloned agents to granite-peak-orders FastAPI"
Write-Host "2. Update return policy, product SKUs in agent instructions"
Write-Host "3. Test multi-step flow: auto-lookup → order list → return eligibility"
Write-Host "4. Set up A2APreviewTool in Foundry to target Granite Peak Orders System Agent`n"
