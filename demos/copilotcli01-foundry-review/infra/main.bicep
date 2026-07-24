// copilotcli01: Foundry AIServices + custom-container Function App running the GitHub Copilot CLI

@description('Azure region for resources')
param location string = 'eastus2'

@description('Demo ID used for unique naming')
param demoId string = 'copilotcli01'

@description('Optional suffix to avoid naming collisions')
param uniqueSuffix string = uniqueString(subscription().id, resourceGroup().id)

@description('Display name for Foundry project')
param projectDisplayName string = 'Copilot CLI Review Prototype Project'

@description('Foundry model deployment name — must be a chat/completions-capable OpenAI-format model that supports tool calling + streaming (>=128k context recommended). Validate current availability for the target region before deploying.')
param deploymentName string = 'gpt-5.4-mini'

@description('Foundry model name (must match the deploymentName by convention for this demo). Validate against the region model catalog.')
param modelName string = 'gpt-5.4-mini'

@description('Foundry model version — MUST validate the current non-deprecated version string for the target region before deployment. See `az cognitiveservices model list -l <region>`.')
param modelVersion string = '2026-03-17'

@description('Model deployment capacity, in thousands of TPM. Set generously to avoid tripping the copilot-cli #3679 429-backoff bug.')
param deploymentCapacityK int = 100

@description('Container image tag deployed to the Function App. Notebook 02 rebuilds this tag via `az acr build` and restarts the Function App.')
param containerImageTag string = 'latest'

@description('Public sample repository the Function App clones and reviews. Keep it small to fit under the 230s Azure Load Balancer HTTP timeout.')
param sampleRepoUrl string = 'https://github.com/Hsenrab/CodeReviewExample.git'

@description('Optional principal object ID to grant AcrPush on the container registry for building images from the notebook. Leave empty to skip role assignment.')
param deployerPrincipalId string = ''

var normalizedDemoId = toLower(replace(demoId, '-', ''))
var accountName = take('ai${normalizedDemoId}${take(uniqueSuffix, 5)}', 24)
var projectName = 'proj-${toLower(demoId)}'
var acrName = take('acr${normalizedDemoId}${take(uniqueSuffix, 10)}', 50)
var functionStorageName = take('stg${normalizedDemoId}${take(uniqueSuffix, 10)}', 24)
var functionPlanName = take('plan-${normalizedDemoId}-${take(uniqueSuffix, 5)}', 40)
var functionAppName = take('func-${normalizedDemoId}-${take(uniqueSuffix, 5)}', 60)
var appInsightsName = take('appi-${normalizedDemoId}-${take(uniqueSuffix, 5)}', 60)

var containerImageName = 'copilot-review'
var containerImageReference = '${acrName}.azurecr.io/${containerImageName}:${containerImageTag}'

// Common tags applied to every taggable resource. SecurityControl=Ignore suppresses
// Defender for Cloud / SFI recommendations on this prototype demo.
var commonTags = {
  SecurityControl: 'Ignore'
}

var storageBlobDataOwnerRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var acrPushRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8311e382-0749-4cb8-b61a-304f252e45ec')

// ---------------------------------------------------------------------------
// Foundry AIServices account + model deployment
// ---------------------------------------------------------------------------
// NOTE: disableLocalAuth is intentionally FALSE for this demo. The GitHub
// Copilot CLI's BYOK mode sends a static API key header — it cannot present an
// AAD bearer token. This is documented as a scoped exception in README.md.
resource aiServices 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  tags: commonTags
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
    disableLocalAuth: false
    dynamicThrottlingEnabled: false
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: projectName
  location: location
  tags: commonTags
  parent: aiServices
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'Prototype project hosting the model the Copilot CLI uses via BYOK.'
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

// ---------------------------------------------------------------------------
// Container Registry (Basic, admin off — MI pull only)
// ---------------------------------------------------------------------------
resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  // acrName base = 'acr' + demoId (default 'copilotcli01') + take(uniqueSuffix, 10) = min 25 chars.
  // Suppress BCP334: Bicep static analyzer cannot see the concrete minimum from take().
  #disable-next-line BCP334
  name: acrName
  location: location
  tags: commonTags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

// ---------------------------------------------------------------------------
// Function storage (MI-only, no shared keys)
// ---------------------------------------------------------------------------
resource functionStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: functionStorageName
  location: location
  tags: commonTags
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
    // Pin public network access so tenant "secure-by-default" policy or
    // future Azure default changes cannot silently flip this to Disabled and
    // break the Functions host's access to the azure-webjobs-secrets blob
    // container (which uses MI, not shared keys). The demo is not
    // network-isolated by design; the SecurityControl=Ignore tag lets the
    // tenant policy allow this exception.
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ---------------------------------------------------------------------------
// Elastic Premium (EP1) Linux plan — required for custom containers.
// Consumption Y1 and Flex Consumption do NOT support custom containers.
// ---------------------------------------------------------------------------
resource functionPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: functionPlanName
  location: location
  tags: commonTags
  kind: 'elastic'
  sku: {
    name: 'EP1'
    tier: 'ElasticPremium'
  }
  properties: {
    reserved: true
    maximumElasticWorkerCount: 3
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: commonTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

// ---------------------------------------------------------------------------
// Custom-container Function App
// ---------------------------------------------------------------------------
// On first `az deployment group create`, the ACR image tag will not exist yet.
// The Function App may report "container start failure" until notebook 02 runs
// `az acr build` to publish the image and restart the app. This is by design.
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  tags: commonTags
  kind: 'functionapp,linux,container'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: functionPlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerImageReference}'
      acrUseManagedIdentityCreds: true
      alwaysOn: false
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
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${acrName}.azurecr.io'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        // ------- Copilot CLI BYOK contract (see docs/architecture-notes.md) -------
        {
          name: 'COPILOT_PROVIDER_BASE_URL'
          value: aiServices.properties.endpoint
        }
        {
          name: 'COPILOT_PROVIDER_TYPE'
          value: 'azure'
        }
        {
          name: 'COPILOT_PROVIDER_API_KEY'
          value: aiServices.listKeys().key1
        }
        {
          name: 'COPILOT_MODEL'
          value: aiDeployment.name
        }
        {
          name: 'SAMPLE_REPO_URL'
          value: sampleRepoUrl
        }
      ]
    }
  }
}

// ---------------------------------------------------------------------------
// Role assignments
// ---------------------------------------------------------------------------
resource functionStorageBlobOwnerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(functionStorage.id, functionApp.id, 'StorageBlobDataOwner')
  scope: functionStorage
  properties: {
    principalId: functionApp.identity.principalId
    roleDefinitionId: storageBlobDataOwnerRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

resource functionAcrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, functionApp.id, 'AcrPull')
  scope: acr
  properties: {
    principalId: functionApp.identity.principalId
    roleDefinitionId: acrPullRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

resource deployerAcrPushRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(acr.id, deployerPrincipalId, 'AcrPush')
  scope: acr
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: acrPushRoleDefinitionId
    principalType: 'User'
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output location string = location
output resourceGroupName string = resourceGroup().name
output aiServicesAccountName string = aiServices.name
output aiServicesEndpoint string = aiServices.properties.endpoint
output foundryProjectName string = foundryProject.name
output aiDeploymentName string = aiDeployment.name
output acrName string = acr.name
output acrLoginServer string = '${acr.name}.azurecr.io'
output containerImageName string = containerImageName
output containerImageReference string = containerImageReference
output functionAppName string = functionApp.name
output functionUrl string = 'https://${functionApp.name}.azurewebsites.net/api/review'
output appInsightsName string = appInsights.name
output sampleRepoUrl string = sampleRepoUrl
