targetScope = 'resourceGroup'

param location string
param demoId string
param operatorObjectId string

var serviceName = 'srch-hybrid-${uniqueString(subscription().subscriptionId, resourceGroup().id)}'
var serviceContributorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
var dataContributorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')

resource search 'Microsoft.Search/searchServices@2025-05-01' = {
  name: serviceName
  location: location
  tags: {
    demo: demoId
  }
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    publicNetworkAccess: 'enabled'
    disableLocalAuth: true
    networkRuleSet: {
      bypass: 'None'
      ipRules: []
    }
  }
}

resource serviceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, operatorObjectId, serviceContributorRoleId)
  scope: search
  properties: {
    roleDefinitionId: serviceContributorRoleId
    principalId: operatorObjectId
    principalType: 'User'
  }
}

resource dataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, operatorObjectId, dataContributorRoleId)
  scope: search
  properties: {
    roleDefinitionId: dataContributorRoleId
    principalId: operatorObjectId
    principalType: 'User'
  }
}

output searchServiceName string = search.name
output searchResourceId string = search.id
output searchEndpoint string = 'https://${search.name}.search.windows.net'
