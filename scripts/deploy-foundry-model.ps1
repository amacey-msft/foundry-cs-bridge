# Deploy gpt-4.1-mini on the existing awm-ai-svc AI Services account.
# Idempotent: skip if a deployment with this name already exists.
$ErrorActionPreference = 'Stop'
$rg   = 'AWM_z2025_Demo_RG'
$acct = 'awm-ai-svc'
$dep  = 'gpt-4.1-mini-gp'   # Granite Peak deployment id

$existing = az cognitiveservices account deployment list -n $acct -g $rg -o json | ConvertFrom-Json
if ($existing | Where-Object { $_.name -eq $dep }) {
    Write-Host "Deployment '$dep' already exists; skipping." -ForegroundColor Yellow
    exit 0
}

Write-Host "Creating deployment '$dep' (gpt-4.1-mini, 2025-04-14, GlobalStandard, 50K TPM)..." -ForegroundColor Cyan
az cognitiveservices account deployment create `
    -n $acct -g $rg `
    --deployment-name $dep `
    --model-name 'gpt-4.1-mini' `
    --model-version '2025-04-14' `
    --model-format 'OpenAI' `
    --sku-name 'GlobalStandard' `
    --sku-capacity 50

Write-Host "Done." -ForegroundColor Green
