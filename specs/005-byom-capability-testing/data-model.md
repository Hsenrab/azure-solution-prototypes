# Resource and Environment Contract

No application data model or external API is introduced.

## Resource Relationships

- One selected subscription contains one demo resource group.
- The resource group contains APIM, the Foundry account, and the search service.
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

Read required outputs directly; do not substitute blank strings or infer success
from incomplete outputs. Endpoints must use HTTPS. No API keys, model deployment
names, gateway route paths, or evaluation variables belong in this contract.

## Lifecycle

Configured -> resource group created -> deployment succeeds -> environment written.
Failure stops the journey before the environment-write step. A partial resource
group can be cleaned up by explicitly selecting its subscription, resource group,
and Foundry account before running the existing destroy flow.
Cleanup deletes resources, purges the Foundry account, deletes the resource group,
and then purges the saved APIM service name.
