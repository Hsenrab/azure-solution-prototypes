// Adapted from gpt4o01-text-image-audio: platform settings belong in Bicep.

@description('Azure region for resources')
param location string = 'eastus2'

@description('Demo ID used for deterministic naming')
param demoId string = 'assert01'

@description('Optional suffix to avoid naming collisions')
param uniqueSuffix string = uniqueString(subscription().id, resourceGroup().id)

type deploymentInput = {
  alias: 'older_model' | 'intermediate_model' | 'newer_model'
  @minLength(1)
  deploymentName: string
  @minLength(1)
  modelName: string
  @minLength(1)
  modelVersion: string
  sku: 'GlobalStandard'
  @minValue(1)
  capacity: int
}

@description('Three distinct models, or two for explicitly approved partial verification. Resolve versions, SKU and capacity from the live catalog.')
@minLength(2)
@maxLength(3)
param modelDeployments deploymentInput[]

@description('Display name for Foundry project')
param projectDisplayName string = 'ASSERT Policy Evaluation Lab'

@description('Object ID of the signed-in developer granted account-scoped inference access')
@minLength(1)
param inferencePrincipalId string

var normalizedDemoId = toLower(replace(demoId, '-', ''))
var accountName = take('ai${normalizedDemoId}${take(uniqueSuffix, 5)}', 24)
var projectName = 'proj-${toLower(demoId)}'
resource aiServices 'Microsoft.CognitiveServices/accounts@2026-09-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
}

resource inferenceRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, inferencePrincipalId, 'Cognitive Services OpenAI User')
  scope: aiServices
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: inferencePrincipalId
    principalType: 'User'
  }
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' = {
  name: projectName
  location: location
  parent: aiServices
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'Notebook-first lab for policy evaluation across three supported model generations.'
    displayName: projectDisplayName
  }
}

@batchSize(1)
resource aiDeployment 'Microsoft.CognitiveServices/accounts/deployments@2026-09-01' = [for model in modelDeployments: {
  name: model.deploymentName
  parent: aiServices
  sku: {
    name: model.sku
    capacity: model.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: model.modelName
      version: model.modelVersion
    }
    versionUpgradeOption: 'NoAutoUpgrade'
  }
  dependsOn: [
    foundryProject
  ]
}]

output subscriptionId string = subscription().subscriptionId
output location string = location
output resourceGroupName string = resourceGroup().name
output aiServicesAccountName string = aiServices.name
output aiServicesResourceId string = aiServices.id
output aiServicesEndpoint string = aiServices.properties.endpoint
output azureOpenAIEndpoint string = 'https://${accountName}.openai.azure.com/'
output modelDeployments array = modelDeployments
output foundryProjectName string = foundryProject.name
output foundryProjectEndpoint string = foundryProject.properties.endpoints['AI Foundry API']
