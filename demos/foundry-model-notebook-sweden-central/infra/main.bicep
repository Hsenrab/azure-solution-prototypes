@description('Azure region for deployment')
param location string = 'swedencentral'

@description('Unique Azure OpenAI account name (3-24, lowercase alphanumeric)')
param accountName string

@description('Model name to deploy')
param modelName string = 'gpt-4o-mini'

@description('Model version')
param modelVersion string = '2024-07-18'

@description('Deployment name exposed to clients')
param deploymentName string = 'chat'

resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: accountName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
  }
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAi
  name: deploymentName
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    raiPolicyName: 'Microsoft.Default'
  }
}

output endpoint string = openAi.properties.endpoint
output deployment string = deploymentName
