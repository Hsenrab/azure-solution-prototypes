param backendAccountName string
param apimPrincipalId string

var inferenceRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource backend 'Microsoft.CognitiveServices/accounts@2026-09-01' existing = {
  name: backendAccountName
}

resource inferenceAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: backend
  name: guid(backend.id, apimPrincipalId, inferenceRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', inferenceRoleId)
    principalId: apimPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = inferenceAccess.id
output backendResourceId string = backend.id
