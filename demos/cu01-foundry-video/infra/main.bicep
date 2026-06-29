// cu01-foundry-video: Azure AI Content Understanding for video analysis
// Deploys a Foundry AIServices resource with configurable model deployment

@description('Azure region for resources')
param location string = 'uksouth'

@description('Demo ID used for deterministic naming')
param demoId string = 'cu01'

@description('Optional suffix to avoid naming collisions')
param uniqueSuffix string = uniqueString(subscription().id, resourceGroup().id)

@description('Model deployment name used by notebooks')
param deploymentName string = 'gpt-4.1-mini'

@description('Model name for the deployment')
param modelName string = 'gpt-4.1-mini'

@description('Model version for the deployment')
param modelVersion string = '2024-12-01'

@description('Deployment capacity in thousands of tokens per minute')
param deploymentCapacityK int = 100

@description('Display name for Foundry project')
param projectDisplayName string = 'CU01 Prototype Project'

@description('Optional deployer principal ID for RBAC (e.g., your user object ID)')
param deployerPrincipalId string = ''

var normalizedDemoId = toLower(replace(demoId, '-', ''))
var accountName = take('ai${normalizedDemoId}${take(uniqueSuffix, 5)}', 24)
var projectName = 'proj-${toLower(demoId)}'
var disableLocalAuth = true

resource aiServices 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: disableLocalAuth
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
  identity: {
    type: 'SystemAssigned'
  }
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: projectName
  location: location
  parent: aiServices
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'Prototype project for validating Content Understanding workflows in a Foundry-aligned setup.'
    displayName: projectDisplayName
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

// RBAC: Cognitive Services User role for deployer principal (if provided)
resource deployerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  scope: aiServices
  name: guid(aiServices.id, deployerPrincipalId, 'a97b65f3-24c8-4991-ab36-1fd38e6f3882') // Cognitive Services User role ID
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c8-4991-ab36-1fd38e6f3882')
    principalId: deployerPrincipalId
    principalType: 'User'
  }
}

output location string = location
output resourceGroupName string = resourceGroup().name
output aiServicesAccountName string = aiServices.name
output aiServicesEndpoint string = aiServices.properties.endpoint
output aiDeploymentName string = aiDeployment.name
output foundryProjectName string = foundryProject.name
output foundryProjectEndpoint string = foundryProject.properties.endpoints['AI Foundry API']
