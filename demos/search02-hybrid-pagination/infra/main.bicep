targetScope = 'subscription'

@minLength(1)
@maxLength(90)
param resourceGroupName string = 'rg-search02-hybrid-pagination-ne'

@allowed([
  'northeurope'
])
param location string = 'northeurope'

@minLength(36)
@maxLength(36)
param operatorObjectId string

@allowed([
  'search02-hybrid-pagination'
])
param demoId string = 'search02-hybrid-pagination'

resource demoGroup 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: resourceGroupName
  location: location
  tags: {
    demo: demoId
  }
}

module search './search.bicep' = {
  name: '${demoId}-search'
  scope: demoGroup
  params: {
    location: location
    demoId: demoId
    operatorObjectId: operatorObjectId
  }
}

output subscriptionId string = subscription().subscriptionId
output tenantId string = subscription().tenantId
output resourceGroupName string = demoGroup.name
output resourceGroupId string = demoGroup.id
output location string = location
output searchServiceName string = search.outputs.searchServiceName
output searchResourceId string = search.outputs.searchResourceId
output searchEndpoint string = search.outputs.searchEndpoint
output operatorObjectId string = operatorObjectId
