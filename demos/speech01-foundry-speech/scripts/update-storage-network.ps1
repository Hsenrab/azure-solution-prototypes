param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$StorageAccountName,

    [string[]]$IpAddresses = @(),

    [switch]$UpdateStorage
)

function Get-PublicIpAddress {
    $endpoints = @(
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://ipv4.icanhazip.com"
    )

    foreach ($endpoint in $endpoints) {
        try {
            $value = (Invoke-RestMethod -Method Get -Uri $endpoint -TimeoutSec 10).ToString().Trim()
            if ($value -match '^\d{1,3}(\.\d{1,3}){3}$') {
                return $value
            }
        }
        catch {
            # Try next endpoint
        }
    }

    return $null
}

if (-not $UpdateStorage) {
    Write-Host "No changes made. Re-run with -UpdateStorage to apply network updates." -ForegroundColor Yellow
    return
}

$resolvedIpAddresses = @($IpAddresses | Where-Object { $_ -and $_ -notmatch '^<.*>$' })
if ($resolvedIpAddresses.Count -eq 0) {
    $detectedIp = Get-PublicIpAddress
    if (-not $detectedIp) {
        throw "Could not detect public IP automatically. Re-run with -IpAddresses @('x.x.x.x')."
    }

    $resolvedIpAddresses = @($detectedIp)
    Write-Host "Detected public IP: $detectedIp" -ForegroundColor Cyan
}

$currentStorage = az storage account show --name $StorageAccountName --resource-group $ResourceGroup -o json | ConvertFrom-Json
if (-not $currentStorage) {
    throw "Could not read storage account $StorageAccountName in resource group $ResourceGroup."
}

$currentStorageRules = @()
if ($currentStorage.networkRuleSet -and $currentStorage.networkRuleSet.ipRules) {
    $currentStorageRules = @($currentStorage.networkRuleSet.ipRules | ForEach-Object { $_.ipAddressOrRange })
}

az storage account update --name $StorageAccountName --resource-group $ResourceGroup --public-network-access Enabled --default-action Deny --min-tls-version TLS1_2 | Out-Null

foreach ($ip in $resolvedIpAddresses) {
    if ($currentStorageRules -notcontains $ip) {
        az storage account network-rule add --account-name $StorageAccountName --resource-group $ResourceGroup --ip-address $ip | Out-Null
    }
}

$updatedStorage = az storage account show --name $StorageAccountName --resource-group $ResourceGroup -o json | ConvertFrom-Json
$updatedStorageRules = @()
if ($updatedStorage.networkRuleSet -and $updatedStorage.networkRuleSet.ipRules) {
    $updatedStorageRules = @($updatedStorage.networkRuleSet.ipRules | ForEach-Object { $_.ipAddressOrRange })
}

Write-Host ""
Write-Host "Storage account network settings updated successfully." -ForegroundColor Green
Write-Host "Access is set to selected networks using the allowed IP list below." -ForegroundColor Green
Write-Host "  Public Network Access: $($updatedStorage.publicNetworkAccess)"
Write-Host "  Default Action:        $($updatedStorage.networkRuleSet.defaultAction)"
Write-Host "  Allowed IP Rules:      $([string]::Join(', ', $updatedStorageRules))"
