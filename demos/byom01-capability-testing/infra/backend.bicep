@description('Azure region for the separate model backend')
param location string = 'swedencentral'

@description('Demo naming prefix')
@maxLength(20)
param demoId string = 'byom01'

@description('Current gpt-5.4 version resolved from the regional catalog')
@minLength(1)
param modelVersion string

@description('Model deployment name exposed by the backend')
param deploymentName string = 'gpt-5.4'

@description('GlobalStandard capacity in thousands of tokens per minute')
@minValue(1)
param modelCapacity int = 100

var accountName = 'foundry-${toLower(demoId)}-backend-${uniqueString(resourceGroup().id)}'

resource backend 'Microsoft.CognitiveServices/accounts@2026-09-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' = {
  parent: backend
  name: '${toLower(demoId)}-backend-project'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'BYOM GPT-5.4 backend'
    description: 'Project for navigating the backend account and model deployment in Foundry'
  }
}

resource model 'Microsoft.CognitiveServices/accounts/deployments@2026-09-01' = {
  parent: backend
  name: deploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-5.4'
      version: modelVersion
    }
    versionUpgradeOption: 'NoAutoUpgrade'
  }
}

output backendResourceGroupName string = resourceGroup().name
output backendLocation string = location
output backendAccountName string = backend.name
output backendResourceId string = backend.id
output backendProjectName string = project.name
output backendProjectResourceId string = project.id
output backendEndpoint string = 'https://${backend.name}.services.ai.azure.com/'
output backendOpenAIEndpoint string = 'https://${backend.name}.openai.azure.com/'
output backendDeploymentName string = model.name
output backendModelVersion string = modelVersion
output backendModelSku string = model.sku.name
output backendModelCapacity int = modelCapacity
