// speech01: Foundry-aligned AI Services + Speech prototype infra

@description('Azure region for resources')
param location string = 'eastus2'

@description('Demo ID used for unique naming')
param demoId string = 'speech01'

@description('Optional suffix to avoid naming collisions')
param uniqueSuffix string = uniqueString(subscription().id, resourceGroup().id)

@description('Display name for Foundry project')
param projectDisplayName string = 'Speech Prototype Project'

@description('Optional principal object ID to grant Speech data-plane access on the AI Services account (for example, a Function managed identity). Leave empty to skip role assignment.')
param speechCallerPrincipalId string = ''

@description('Optional principal object ID to grant blob upload permissions on the Function storage account for local package deployment. Leave empty to skip role assignment.')
param deployerPrincipalId string = ''

@description('Optional package URL for Linux Consumption deploy-from-URL flow. Leave empty to set later from Notebook 2.')
param packageUri string = ''

var normalizedDemoId = toLower(replace(demoId, '-', ''))
var accountNameBase = 'ai${normalizedDemoId}${take(uniqueSuffix, 5)}'
var accountName = take(accountNameBase, 24)
var projectName = 'proj-${toLower(demoId)}'
var functionStorageName = take('stg${normalizedDemoId}${take(uniqueSuffix, 10)}', 24)
var functionPlanName = take('plan-${normalizedDemoId}-${take(uniqueSuffix, 5)}', 40)
var functionAppName = take('func-${normalizedDemoId}-${take(uniqueSuffix, 5)}', 60)
var appInsightsName = take('appi-${normalizedDemoId}-${take(uniqueSuffix, 5)}', 60)
var cognitiveServicesSpeechUserRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
var storageBlobDataOwnerRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
var storageBlobDataContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

resource aiServices 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
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
    dynamicThrottlingEnabled: false
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
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
    description: 'Prototype project for validating Azure Speech in a Foundry-aligned setup.'
    displayName: projectDisplayName
  }
}

resource functionStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: functionStorageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource functionPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: functionPlanName
  location: location
  kind: 'functionapp'
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: functionPlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage__blobServiceUri'
          value: 'https://${functionStorage.name}.blob.${environment().suffixes.storage}'
        }
        {
          name: 'AzureWebJobsStorage__queueServiceUri'
          value: 'https://${functionStorage.name}.queue.${environment().suffixes.storage}'
        }
        {
          name: 'AzureWebJobsStorage__tableServiceUri'
          value: 'https://${functionStorage.name}.table.${environment().suffixes.storage}'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AzureWebJobsFeatureFlags'
          value: 'EnableWorkerIndexing'
        }
        {
          name: 'AZURE_AI_ENDPOINT'
          value: aiServices.properties.endpoint
        }
        {
          name: 'AZURE_AUTH_MODE'
          value: 'function-key'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: packageUri
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID'
          value: 'SystemAssigned'
        }
      ]
    }
  }
}

resource functionStorageBlobOwnerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(functionStorage.id, functionApp.id, 'StorageBlobDataOwner')
  scope: functionStorage
  properties: {
    principalId: functionApp.identity.principalId
    roleDefinitionId: storageBlobDataOwnerRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

resource deployerStorageBlobContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(functionStorage.id, deployerPrincipalId, 'StorageBlobDataContributor')
  scope: functionStorage
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
    principalType: 'User'
  }
}

resource speechCallerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(speechCallerPrincipalId)) {
  name: guid(aiServices.id, speechCallerPrincipalId, 'CognitiveServicesSpeechUser')
  scope: aiServices
  properties: {
    principalId: speechCallerPrincipalId
    roleDefinitionId: cognitiveServicesSpeechUserRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

resource functionSpeechRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, functionApp.name, 'CognitiveServicesSpeechUser')
  scope: aiServices
  properties: {
    principalId: functionApp.identity.principalId
    roleDefinitionId: cognitiveServicesSpeechUserRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

output location string = location
output resourceGroupName string = resourceGroup().name
output aiServicesAccountName string = aiServices.name
output aiServicesEndpoint string = aiServices.properties.endpoint
output speechRegion string = location
output foundryProjectName string = foundryProject.name
output foundryProjectEndpoint string = foundryProject.properties.endpoints['AI Foundry API']
output functionAppName string = functionApp.name
output functionUrl string = 'https://${functionApp.name}.azurewebsites.net/api/speech-roundtrip'
output appInsightsName string = appInsights.name
