// ─────────────────────────────────────────────────────────────────────────────
// Research notes (April 2026)
// ─────────────────────────────────────────────────────────────────────────────
// • This uses kind: 'AIServices' — the *new* Azure AI Foundry resource type.
//   Classic demos used kind: 'OpenAI', which is scoped to OpenAI models only.
//   kind: 'AIServices' is the Foundry resource that exposes a unified
//   multi-model endpoint (https://<name>.services.ai.azure.com/) and supports
//   the azure-ai-inference SDK alongside the classic OpenAI-compatible endpoint.
//
// • Model: gpt-4.1-mini (2025-04-14) replaces gpt-4o-mini which is deprecated
//   as of July 2025 and retires March 2026. Replacement path: gpt-4o-mini →
//   gpt-4.1-mini → gpt-5.1-mini (long-term).
//
// • Deployment SKU 'GlobalStandard' with explicit capacity is required by
//   API version 2024-10-01 and later (older templates omitted it).
//
// • API version 2024-10-01 is the current stable CognitiveServices ARM API.
// ─────────────────────────────────────────────────────────────────────────────

@description('Azure region for deployment')
param location string = 'swedencentral'

@description('Unique AI Services account name (3-24, lowercase alphanumeric)')
param accountName string

@description('Model name to deploy (see Azure AI Foundry model catalog for current options)')
param modelName string = 'gpt-4.1-mini'

@description('Model version')
param modelVersion string = '2025-04-14'

@description('Deployment name exposed to clients')
param deploymentName string = 'chat'

@description('Tokens-per-minute capacity in thousands (e.g. 10 = 10 000 TPM)')
param deploymentCapacityK int = 10

// New Azure AI Foundry resource (AIServices kind).
// Endpoint format: https://<accountName>.services.ai.azure.com/
resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
  }
}

// GlobalStandard SKU is the pay-as-you-go tier for new Foundry model deployments.
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: deploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: deploymentCapacityK
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
}

output endpoint string = aiServices.properties.endpoint
output accountName string = accountName
output deployment string = deploymentName
