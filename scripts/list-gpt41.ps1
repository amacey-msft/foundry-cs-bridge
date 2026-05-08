# List gpt-4.1 models on the AI Services account.
$json = az cognitiveservices account list-models -n awm-ai-svc -g AWM_z2025_Demo_RG -o json
$models = $json | ConvertFrom-Json
$models | Where-Object { $_.name -like "gpt-4.1*" } | Select-Object name, version, @{n='sku';e={$_.skus[0].name}} | Format-Table -AutoSize
