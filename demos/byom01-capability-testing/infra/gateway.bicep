param foundryAccountName string
param projectName string
param apimName string
param backendResourceGroup string
param backendAccountName string
param backendOpenAIEndpoint string
param backendDeploymentName string
param backendModelVersion string
param location string = resourceGroup().location

@description('Optional tenant-local Entra user object ID for direct notebook calls; empty retains project-only access')
param allowedUserObjectId string = ''

var connectionName = 'byom01-gateway'
var apiName = 'byom01-responses'
var backendName = 'byom01-gpt54'
var apiPath = 'byom01/openai/v1'
var tokenAudience = 'https://cognitiveservices.azure.com'
var backendBaseUrl = uri(backendOpenAIEndpoint, 'openai/v1')
var backendResourceId = resourceId(backendResourceGroup, 'Microsoft.CognitiveServices/accounts', backendAccountName)
var metricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'
var allowedCallerIds = empty(allowedUserObjectId)
  ? [project.identity.principalId]
  : [project.identity.principalId, allowedUserObjectId]
var allowedCallerValues = join(map(allowedCallerIds, callerId => '<value>${callerId}</value>'), '')
var policyXml = replace(
  replace(
    replace(
      replace(
        replace(
          replace(
            replace(
              replace(loadTextContent('gateway-policy.xml'), '__TENANT_ID__', subscription().tenantId),
              '__ALLOWED_CALLER_VALUES__', allowedCallerValues),
            '__TOKEN_AUDIENCE__', tokenAudience),
          '__DEPLOYMENT_NAME__', backendDeploymentName),
        '__BACKEND_NAME__', backendName),
      '__API_NAME__', apiName),
    '__BACKEND_RESOURCE_ID__', backendResourceId),
  '__BACKEND_URL__', '${backendBaseUrl}/responses')
var messageDiagnostics = {
  request: {
    body: { bytes: 0 }
    headers: []
  }
  response: {
    body: { bytes: 0 }
    headers: []
  }
}

resource foundry 'Microsoft.CognitiveServices/accounts@2026-09-01' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' existing = {
  parent: foundry
  name: projectName
}

resource apim 'Microsoft.ApiManagement/service@2024-05-01' existing = {
  name: apimName
}

module backendAccess 'backend-access.bicep' = {
  name: 'byom01-gateway-backend-access'
  scope: resourceGroup(backendResourceGroup)
  params: {
    backendAccountName: backendAccountName
    apimPrincipalId: apim.identity.principalId
  }
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2026-03-01' = {
  name: 'logs-byom01-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    features: {
      disableLocalAuth: true
    }
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-byom01-${uniqueString(resourceGroup().id)}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
    DisableLocalAuth: true
  }
}

resource telemetryAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: insights
  name: guid(insights.id, apim.id, metricsPublisherRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', metricsPublisherRoleId)
    principalId: apim.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource logger 'Microsoft.ApiManagement/service/loggers@2024-05-01' = {
  parent: apim
  name: 'byom01-insights'
  properties: {
    loggerType: 'applicationInsights'
    resourceId: insights.id
    credentials: {
      connectionString: insights.properties.ConnectionString
      identityClientId: 'SystemAssigned'
    }
  }
  dependsOn: [telemetryAccess]
}

resource backend 'Microsoft.ApiManagement/service/backends@2024-05-01' = {
  parent: apim
  name: backendName
  properties: {
    protocol: 'http'
    url: backendBaseUrl
    tls: {
      validateCertificateChain: true
      validateCertificateName: true
    }
  }
}

resource api 'Microsoft.ApiManagement/service/apis@2024-05-01' = {
  parent: apim
  name: apiName
  properties: {
    displayName: 'BYOM GPT-5.4 Responses'
    path: apiPath
    protocols: ['https']
    subscriptionRequired: false
    apiType: 'http'
  }
}

resource operation 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' = {
  parent: api
  name: 'responses'
  properties: {
    displayName: 'Invoke GPT-5.4'
    method: 'POST'
    urlTemplate: '/responses'
  }
}

resource policy 'Microsoft.ApiManagement/service/apis/policies@2024-05-01' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'xml'
    value: policyXml
  }
  dependsOn: [backend, backendAccess, operation]
}

resource diagnostics 'Microsoft.ApiManagement/service/apis/diagnostics@2024-05-01' = {
  parent: api
  name: 'applicationinsights'
  properties: {
    loggerId: logger.id
    alwaysLog: 'allErrors'
    sampling: { samplingType: 'fixed', percentage: 100 }
    verbosity: 'information'
    frontend: messageDiagnostics
    backend: messageDiagnostics
    logClientIp: false
    metrics: false
    httpCorrelationProtocol: 'W3C'
  }
}

resource connection 'Microsoft.CognitiveServices/accounts/projects/connections@2026-09-01' = {
  parent: project
  name: connectionName
  properties: {
    category: 'ApiManagement'
    target: '${apim.properties.gatewayUrl}/${apiPath}'
    // Published Bicep types lag the runtime contract used by Microsoft's Foundry samples.
    #disable-next-line BCP036
    authType: 'ProjectManagedIdentity'
    audience: tokenAudience
    isSharedToAll: false
    credentials: {}
    metadata: {
      deploymentInPath: 'false'
      upstreamSurface: 'responses'
      customHeaders: '{}'
      models: string([
        {
          name: backendDeploymentName
          properties: {
            model: {
              name: 'gpt-5.4'
              version: backendModelVersion
              format: 'OpenAI'
            }
          }
        }
      ])
    }
  }
  dependsOn: [policy, diagnostics]
}

output connectionName string = connection.name
output connectionId string = connection.id
output modelReference string = '${connection.name}/${backendDeploymentName}'
output gatewayUrl string = connection.properties.target
output apiId string = api.name
output backendResourceId string = backendResourceId
output backendUrl string = '${backendBaseUrl}/responses'
output deploymentName string = backendDeploymentName
output projectPrincipalId string = project.identity.principalId
output apimPrincipalId string = apim.identity.principalId
output allowedUserObjectId string = allowedUserObjectId
output directTokenScope string = '${tokenAudience}/.default'
output workspaceId string = workspace.properties.customerId
output workspaceResourceId string = workspace.id
output applicationInsightsResourceId string = insights.id
output backendRoleAssignmentId string = backendAccess.outputs.roleAssignmentId
output telemetryRoleAssignmentId string = telemetryAccess.id
