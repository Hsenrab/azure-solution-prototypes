@description('Azure region for the demo resources')
param location string = 'uksouth'

@description('Lowercase letters, digits, and hyphens used as the demo naming prefix')
@maxLength(20)
param demoId string = 'byom01'

@description('API Management publisher email')
param publisherEmail string = 'admin@example.com'

@description('API Management publisher name')
param publisherName string = 'Prototype Team'

var suffix = uniqueString(resourceGroup().id)
var prefix = toLower(demoId)
var foundryName = 'foundry-${prefix}-${suffix}'
var apimName = 'apim-${prefix}-${suffix}'
var searchName = 'search-${prefix}-${suffix}'

resource foundry 'Microsoft.CognitiveServices/accounts@2026-09-01' = {
  name: foundryName
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
    customSubDomainName: foundryName
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' = {
  parent: foundry
  name: '${prefix}-project'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'BYOM capability testing'
    description: 'Resource foundation for later BYOM capability tests'
  }
}

resource apim 'Microsoft.ApiManagement/service@2024-05-01' = {
  name: apimName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Standard'
    capacity: 1
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
    publicNetworkAccess: 'Enabled'
    virtualNetworkType: 'None'
  }
}

resource search 'Microsoft.Search/searchServices@2026-11-01' = {
  name: searchName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'Default'
    publicNetworkAccess: 'Enabled'
  }
}

output subscriptionId string = subscription().subscriptionId
output resourceGroupName string = resourceGroup().name
output location string = location
output foundryAccountName string = foundry.name
output foundryResourceId string = foundry.id
output foundryEndpoint string = 'https://${foundry.name}.services.ai.azure.com/'
output projectName string = project.name
output projectResourceId string = project.id
output projectEndpoint string = project.properties.endpoints['AI Foundry API']
output apimServiceName string = apim.name
output apimResourceId string = apim.id
output apimGatewayUrl string = apim.properties.gatewayUrl
output searchServiceName string = search.name
output searchResourceId string = search.id
output searchEndpoint string = 'https://${search.name}.search.windows.net'
