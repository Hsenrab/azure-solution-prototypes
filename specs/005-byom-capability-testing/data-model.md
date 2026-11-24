# Resource and Environment Contract

No application data model or external API is introduced.

## Resource Relationships

- One selected subscription contains two demo resource groups.
- The consumer group contains APIM, the consumer Foundry account, and Search.
- The backend group in Sweden Central contains a second Foundry account and its
  account-level GPT-5.4 deployment; no backend project is needed.
- The Foundry project is a child of the Foundry account.
- APIM and search remain unconnected to Foundry in this slice.
- Globally unique service names derive from the resource-group ID and demo prefix.
  Reusing those inputs targets the same services.

## Generated Environment

`01_deploy_infra.ipynb` writes `demos/byom01-capability-testing/env/.env` after
successful deployment. The committed `.env.example` documents these fields:

| Variable | Value/source |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Explicit environment selection or selected CLI subscription |
| `AZURE_RESOURCE_GROUP` | Deployed resource-group name |
| `AZURE_LOCATION` | Deployment location |
| `AZURE_ACCOUNT_NAME` | Foundry account name |
| `AZURE_AI_RESOURCE_ID` | Foundry account ARM ID |
| `AZURE_AI_ENDPOINT` | Foundry account endpoint; also targets standard cleanup |
| `AZURE_AI_PROJECT_NAME` | Child project name |
| `AZURE_AI_PROJECT_ID` | Child project ARM ID |
| `AZURE_AI_PROJECT_ENDPOINT` | Project endpoint from deployed project properties |
| `AZURE_APIM_NAME` | APIM service name |
| `AZURE_APIM_RESOURCE_ID` | APIM ARM ID |
| `APIM_ENDPOINT` | Deployed APIM gateway URL |
| `AZURE_SEARCH_NAME` | Search service name |
| `AZURE_SEARCH_RESOURCE_ID` | Search ARM ID |
| `AZURE_SEARCH_ENDPOINT` | Deployed search endpoint |
| `AZURE_BACKEND_RESOURCE_GROUP` | Separate backend resource-group name |
| `AZURE_BACKEND_LOCATION` | Sweden Central (`swedencentral`) |
| `AZURE_BACKEND_ACCOUNT_NAME` | Backend Foundry account name |
| `AZURE_BACKEND_RESOURCE_ID` | Backend account ARM ID |
| `AZURE_BACKEND_ENDPOINT` | Backend Foundry endpoint; targets backend cleanup |
| `AZURE_BACKEND_OPENAI_ENDPOINT` | Backend OpenAI-compatible account endpoint |
| `AZURE_BACKEND_DEPLOYMENT_NAME` | GPT-5.4 deployment name |
| `AZURE_BACKEND_MODEL_VERSION` | Current default GA version selected from the live catalog |
| `AZURE_BACKEND_MODEL_SKU` | GlobalStandard |
| `AZURE_BACKEND_MODEL_CAPACITY` | 100 units (100,000 TPM) |

Read required outputs directly; do not substitute blank strings or infer success
from incomplete outputs. Endpoints must use HTTPS. No API keys, gateway route
paths, or evaluation variables belong in this contract.

## Lifecycle

Configured -> model/quota selected -> both templates compiled -> consumer
group/deployment succeeds -> backend group/deployment succeeds -> environment written.
Failure stops the journey before the environment-write step. A partial resource
group can be cleaned up by explicitly selecting its subscription, resource group,
and Foundry account before running the existing destroy flow.
Cleanup deletes resources, purges the Foundry account, deletes the resource group,
and then purges the saved APIM service name for the consumer. Run the unchanged
destroy notebook separately for each group, with explicit group/account endpoint
targeting as documented in the demo README.
