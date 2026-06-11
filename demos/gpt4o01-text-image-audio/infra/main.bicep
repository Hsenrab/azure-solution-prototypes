// gpt4o01: minimal Foundry-aligned AI Services account for multimodal notebook validation

@description('Azure region for resources')
param location string = 'swedencentral'

@description('Demo ID used for deterministic naming')
param demoId string = 'gpt4o01'

@description('Optional suffix to avoid naming collisions')
param uniqueSuffix string = uniqueString(subscription().id, resourceGroup().id)

@description('Model deployment name used by notebooks')
param deploymentName string = 'gpt-4o'

@description('Model name for the deployment')
param modelName string = 'gpt-4o'

@description('Model version for the deployment')
param modelVersion string = '2024-11-20'

@description('Deployment capacity in thousands of tokens per minute')
param deploymentCapacityK int = 100

var normalizedDemoId = toLower(replace(demoId, '-', ''))
var accountName = take('ai${normalizedDemoId}${take(uniqueSuffix, 5)}', 24)
var disableLocalAuthForDemo = false

resource aiServices 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: accountName
    disableLocalAuth: disableLocalAuthForDemo
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
}

resource aiDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: deploymentName
  parent: aiServices
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

output location string = location
output resourceGroupName string = resourceGroup().name
output aiServicesAccountName string = aiServices.name
output aiServicesEndpoint string = aiServices.properties.endpoint
output aiDeploymentName string = aiDeployment.name
