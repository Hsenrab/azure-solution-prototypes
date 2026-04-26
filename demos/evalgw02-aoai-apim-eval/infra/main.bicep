// evalgw02: Classic Azure OpenAI + APIM Gateway + Evaluation
// Both services deploy in one resource group in UK South.

@description('Azure region for all resources')
param location string = 'uksouth'

@description('Demo ID for naming resources, e.g. evalgw02 or evalgw02-1')
param demoId string = 'evalgw02'

@description('Primary model name')
param modelName string = 'gpt-4o'

@description('Primary model version')
param modelVersion string = '2024-11-20'

@description('Primary deployment name')
param deploymentName string = 'chat4o'

@description('Secondary model name')
param secondaryModelName string = 'gpt-5.1'

@description('Secondary model version')
param secondaryModelVersion string = '2025-11-13'

@description('Secondary deployment name')
param secondaryDeploymentName string = 'chat51'

@description('Tokens-per-minute capacity in thousands for each deployment')
param deploymentCapacityK int = 100

var normalizedDemoId = toLower(replace(demoId, '-', ''))
var openAiName = 'aoai${normalizedDemoId}uks'
var apimName = 'apim-${toLower(demoId)}-uks'

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  tags: {
    SecurityControl: 'Ignore'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
  }
}

resource primaryDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: deploymentName
  parent: openAi
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

resource secondaryDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: secondaryDeploymentName
  parent: openAi
  sku: {
    name: 'GlobalStandard'
    capacity: deploymentCapacityK
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: secondaryModelName
      version: secondaryModelVersion
    }
  }
  dependsOn: [
    primaryDeployment
  ]
}

resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: 'Developer'
    capacity: 1
  }
  properties: {
    publisherEmail: 'admin@example.com'
    publisherName: 'Prototype Team'
  }
}

resource openAiKeyNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  parent: apim
  name: 'openai-api-key'
  properties: {
    displayName: 'openai-api-key'
    secret: true
    value: openAi.listKeys().key1
  }
}

resource openAiBackend 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = {
  parent: apim
  name: 'aoai-backend'
  properties: {
    title: 'Azure OpenAI backend'
    description: 'Backend for classic Azure OpenAI account'
    url: 'https://${openAi.name}.openai.azure.com/openai/deployments/${deploymentName}'
    protocol: 'http'
  }
}

resource openAiApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: apim
  name: 'azure-openai'
  properties: {
    displayName: 'Azure OpenAI Gateway'
    description: 'APIM gateway for Azure OpenAI chat completions'
    path: 'openai'
    protocols: [
      'https'
    ]
    subscriptionRequired: true
  }
}

resource unlimitedProduct 'Microsoft.ApiManagement/service/products@2023-09-01-preview' existing = {
  parent: apim
  name: 'unlimited'
}

resource openAiApiOnUnlimitedProduct 'Microsoft.ApiManagement/service/products/apis@2023-09-01-preview' = {
  parent: unlimitedProduct
  name: openAiApi.name
}

resource chatCompletionsOperation 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' = {
  parent: openAiApi
  name: 'chat-completions-post'
  properties: {
    displayName: 'POST chat/completions'
    method: 'POST'
    urlTemplate: '/chat/completions'
    request: {
      representations: [
        {
          contentType: 'application/json'
        }
      ]
    }
    responses: [
      {
        statusCode: 200
      }
    ]
  }
}

resource chatCompletionsPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2023-09-01-preview' = {
  parent: chatCompletionsOperation
  name: 'policy'
  properties: {
    format: 'xml'
    value: '''<policies>
  <inbound>
    <base />
    <set-backend-service backend-id="aoai-backend" />
    <set-header name="api-key" exists-action="override">
      <value>{{openai-api-key}}</value>
    </set-header>
    <set-query-parameter name="api-version" exists-action="override">
      <value>2024-10-21</value>
    </set-query-parameter>
  </inbound>
  <backend>
    <forward-request />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>'''
  }
  dependsOn: [
    openAiKeyNamedValue
    openAiBackend
  ]
}

output location string = location
output resourceGroupName string = resourceGroup().name
output openAiAccountName string = openAi.name
output openAiEndpoint string = 'https://${openAi.name}.openai.azure.com/'
output primaryDeploymentName string = deploymentName
output secondaryDeploymentName string = secondaryDeploymentName
output apimServiceName string = apim.name
output apimGatewayUrl string = apim.properties.gatewayUrl
output apimChatCompletionsUrl string = '${apim.properties.gatewayUrl}/openai/chat/completions'
output legacyApiVersion string = '2024-10-21'
