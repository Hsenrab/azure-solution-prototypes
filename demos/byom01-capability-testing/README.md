# BYOM capability testing

Test a Foundry connected model through an APIM gateway, explore non-LLM Foundry
Tools, and compare direct model API calls. Use the deployment notebooks to build
the demo or run the Tools/Direct API examples against independently deployed resources.

## Problem and hypothesis

Provisioning resources does not make a gateway-managed model usable from Foundry.
An engineer should be able to configure a connected model using managed identities,
invoke GPT-5.4 through APIM from Foundry, and correlate the response with successful
gateway backend evidence.

## Resource foundation and model backend

| Resource | SKU | Capacity |
|---|---|---|
| Azure API Management | Standard | 1 unit |
| Consumer Microsoft Foundry (`AIServices`) | S0 | One account with one project |
| Foundry IQ (Azure AI Search) | Standard (S1) | 1 replica, 1 partition |
| Backend Microsoft Foundry (`AIServices`) | S0 | Separate account with one project, hosting GPT-5.4 |
| Backend `gpt-5.4` deployment | GlobalStandard | 100 units (100,000 TPM) |
| Application Insights + Log Analytics | Workspace-based / PerGB2018 | One demo-owned telemetry destination, 30-day workspace retention |

Consumer region: **UK South**. Backend region: **Sweden Central**,
in a second resource group in the same selected subscription. GlobalStandard
inference may process outside Sweden; this is not a Sweden-only residency guarantee.
All service endpoints are public and authenticated.
Infrastructure is defined in [main.bicep](./infra/main.bicep).
The separate account/model are defined in [backend.bicep](./infra/backend.bicep).
The accounts, both projects, and APIM have system-assigned identities. The
[gateway template](./infra/gateway.bicep) defines the route, project connection,
Entra caller validation, and body-free telemetry. The
[backend access module](./infra/backend-access.bicep) grants APIM inference access
only on the backend account. Backend local
key authentication is disabled in Bicep, matching the current tenant-enforced
consumer behavior. The backend includes `byom01-backend-project` (with the default
demo ID) for Foundry portal navigation. GPT-5.4 remains an account-level deployment;
the backend project does not change the gateway route or host another model.

**Out of scope**: Search/RAG ingestion, knowledge bases, Foundry IQ connections,
agent tools, full Foundry tracing, evaluations, streaming tests, failover, and load testing.
Provisioning the search resource does not create a retrieval flow.

**Costs**: APIM Standard and Search S1 have ongoing capacity charges even when
idle. Foundry uses S0; the backend deploys a pay-per-token model, but the
deployment/configuration notebooks make no inference calls. The Test notebook
makes one paid Foundry Responses request, and telemetry ingestion has usage charges.
Each direct-model example in the API notebook makes one additional paid request.
Foundry Tools examples incur Speech, translation, Language, document analysis,
Content Safety, or Content Understanding usage charges when run.
Check current
[APIM pricing](https://azure.microsoft.com/pricing/details/api-management/) and
[search pricing](https://azure.microsoft.com/pricing/details/search/), plus
[model pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/), before
deploying. This is a prototype, not a production availability configuration.

## Prerequisites

- **Local setup:** Python >=3.10, VS Code with Jupyter support, and Azure CLI for
  the shared Azure sign-in step.
- **Notebook deployment:** an up-to-date Bicep compiler
  (`az bicep upgrade` if already installed), and an explicitly selected Azure
  subscription with permission to create/delete the
  resources and purge Foundry and APIM soft-deleted services. Configuration also
  requires connection-write permissions and role-assignment permissions on the
  backend account and telemetry component.
- **Deployment capacity:** available standard-tier capacity in UK South, or another region you choose
  for the consumer before deploying, and GPT-5.4 GlobalStandard quota in
  Sweden Central for the backend. The notebook resolves the current generally
  available default model version from the regional catalog. No automatic model,
  region, subscription, or SKU fallback is used.
- **Deployment policy:** subscription policy must permit the public-access design. Do not bypass policy
  with tags or change tenant networking from a notebook.
- **Connected-model gateway:** **[PREVIEW]** upstream Responses routing must be available in the consuming
  project. Creating a connection does not enable the feature flight. See the
  [Foundry gateway guide](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/ai-gateway).
- **Connected-model test:** the signed-in identity needs **Foundry User** on the project and
  **Log Analytics Reader** or equivalent existing access on the generated workspace.
  Configuration does not automatically grant broader user permissions.
- **Self-deployed resources:** an existing Foundry account and/or a
  Responses-capable gateway/model for the examples you choose. Supply their
  settings and authorize your credentials as described in the Tools/Direct API
  notebooks. Provisioning permissions and backend model quota are not required
  just to call existing services.

## Notebook journey

| Notebook | Purpose |
|---|---|
| [00_setup.ipynb](./notebooks/00_setup.ipynb) | Create the venv/kernel, authenticate/select subscription, install dependencies |
| [01_deploy_infra.ipynb](./notebooks/01_deploy_infra.ipynb) | Deploy the consumer/backend resources and generate settings, or follow the skip guidance for self-deployed resources |
| [02_configure.ipynb](./notebooks/02_configure.ipynb) | Configure the managed-identity route, scoped RBAC, connected model, and telemetry; generate gateway settings |
| [03_test.ipynb](./notebooks/03_test.ipynb) | Invoke the connected model through Foundry, save correlated gateway evidence, and clean up the test version/conversation |
| [04_foundry_tools.ipynb](./notebooks/04_foundry_tools.ipynb) | Six non-LLM service SDK examples using the existing Foundry account; Document Intelligence is key-only |
| [05_direct_api.ipynb](./notebooks/05_direct_api.ipynb) | Pure Responses calls through APIM/Foundry via OpenAI SDK or HTTPS, plus an Azure AI Projects SDK example |
| [06_prompt_agent.ipynb](./notebooks/06_prompt_agent.ipynb) | Create a no-tool prompt agent on the connected model with pirate-style instructions |
| [07_toolbox_agent.ipynb](./notebooks/07_toolbox_agent.ipynb) | Give the pirate agent file search (town documents in `data/brackenford/`) and code interpreter, directly (tool agent) and through a toolbox (toolbox agent, which fails intermittently in preview) |
| [X_destroy.ipynb](./notebooks/X_destroy.ipynb) | Standard resource deletion and Cognitive Services purge |

1. Open setup and run **Step 1**. Switch to **Python (byom01-capability-testing)**
   before running **Step 2** and **Step 3**.
2. Open deployment using that kernel and follow **Deployment Route**.
   For self-deployed resources, skip deployment/configuration/testing and go
   directly to Tools or Direct APIs with their required environment variables.
   Steps 3-6 below apply only to the notebook-deployment route.
   Notebook working directory must be `notebooks/`.
3. Review **Configuration**, then run the remaining steps in order. Deployment
   uses `AZURE_SUBSCRIPTION_ID` if supplied; otherwise it uses the CLI subscription
   selected during setup. The selected subscription's tenant is used for SDK auth.
4. Run **Select Backend Model and Check Quota**, then compile both templates.
   Await **Deploy Bicep** and **Deploy Backend Bicep** completion before running
   **Write env/.env**. Do not run the write step after either deployment fails.
5. Run Configure with the same generated settings. Wait for deployment and
   **Read Registered Connection** to succeed before **Write Gateway Settings**.
6. Run Test once, including **Clean Up Test Resources** and **Check Gateway Evidence**.
   A completed response and matching successful gateway trace are both required.

Default groups are `rg-byom01-uks` (consumer) and `rg-byom01-backend-swc`
(backend). Keep them distinct. Repeating deployment targets the same names;
changing a group name creates another set of resources.

## Generated configuration and verification

[.env.example](./env/.env.example) lists the configuration fields. Notebook
deployment generates `env/.env`; self-deployed users supply the variables listed
in their chosen Tools/Direct API notebook. Real `.env` files remain ignored.

After deployment, check the consumer SKUs, public network settings, and Foundry
child project. In the backend group, verify the second account is in Sweden
Central and its GPT-5.4 deployment has the selected version, GlobalStandard SKU,
and capacity 100. The `AZURE_BACKEND_*` settings identify the provider; the original
Foundry/project settings still identify the consumer. These resources alone do
not route requests through APIM until Configure completes.
Only write environment settings after both deployments succeed.

Local validation and optional live acceptance are described in the
[validation guide](../../specs/005-byom-capability-testing/quickstart.md).

### Connected-model evidence

Configure generates ignored `env/gateway.json` containing connection/model/gateway
identifiers, workspace ID, and project context. Do not edit it manually.
The route is OpenAI v1 Responses, with no deployment path or `api-version`.
APIM accepts the consuming project's Entra identity and, when explicitly configured,
one additional Entra user, for the configured deployment. It authenticates to the
fixed backend using its own identity and traces the actual validated caller.
No subscription key or backend key is used.

Test creates a unique no-tool prompt agent referencing
`byom01-gateway/<backend-deployment-name>`. The latest ignored
`env/test-evidence.json` records the harmless test output, test marker, Foundry
response ID, APIM request/routing records, verification state, and cleanup state.
APIM reads only the UUID marker for correlation; diagnostics log zero body bytes
and no authorization headers. The outer Foundry response ID is not assumed to
equal a backend response ID.

For a telemetry delay, reopen Test and run **Load Gateway Settings** and
**Check Gateway Evidence** only. This queries the original marker without paid
inference. Missing or incomplete evidence is pending/unverified, not success.
The agent/conversation remain available for inspection after invocation. Run
**Clean Up Test Resources** when finished, including after a failed or interrupted
invocation, and before creating another test.

### Prompt agent example

[06_prompt_agent.ipynb](./notebooks/06_prompt_agent.ipynb) is a focused prompt-agent
example using the same connected model and generated `env/gateway.json` settings.
It creates no tools or web-search capability, instructs the agent to speak like a
pirate, and asks it to explain Azure AI Foundry. The notebook makes one paid
Responses request and then deletes only its test conversation and agent version.
It does not create another connection or modify the gateway.

### Foundry Tools examples

[04_foundry_tools.ipynb](./notebooks/04_foundry_tools.ipynb) contains short
**Speech**, **Translator**, **Language**, **Document Intelligence**,
**Content Safety**, and **Content Understanding** examples. Expected outputs are
playable WAV audio, NMT-translated text, a detected ISO language code, extracted
document text, category/severity results, and asynchronous Read output.
Translator explicitly selects the `general` NMT system, and Content Understanding
uses extraction-only `prebuilt-read`, without language/embedding models.
Search, Vision, agents, and LLM calls are not part of this notebook.

Reuse the existing generated account endpoint/name/resource ID/location and
subscription/resource-group settings. No redeployment, project connection
registration, new resources, or gateway route is required. Dedicated service
SDKs use the account's documented service endpoints, not the project API URL;
Translator's global endpoint is authenticated with the account's region and
resource ID. The notebook's opening sections list the setup/configuration needed
for notebook-deployed and self-deployed resources. Reuse the verified demo venv;
there is no further setup when the preceding notebooks and dependencies are complete.

Run **Load Account Settings**, then your chosen examples. Both Read examples
also need **Load the OCR Sample**, which fetches one public Azure sample PDF
into memory. Each service execution incurs usage charges. Speech writes only
`outputs/foundry-tools-speech.wav`; delete that exact file when finished.
No new Azure resources need cleanup.

The five dual-auth examples prefer `FOUNDRY_API_KEY` when configured, otherwise
DefaultAzureCredential, announcing the method without exposing credentials or
retrying another method. A configured key must be a native key for the same
consuming account identified by `AZURE_AI_ENDPOINT` and `FOUNDRY_BASE_URL`, not
an APIM key or a key for another account. Entra needs the applicable Cognitive
Services data-plane permissions on the account (for example **Cognitive Services
User**, and **Cognitive Services Speech User** for Speech); project access alone
does not grant these. The notebook does not grant roles.

**Document Intelligence is key-only on this multi-service route.** It retrieves
the account key with the management SDK using Entra, requiring
`Microsoft.CognitiveServices/accounts/listKeys/action`, then runs `prebuilt-read`
with that key. It is blocked on the current tenant's key-disabled deployment.
Run the other examples independently. Successful Document Intelligence analysis
requires an already policy-compatible key-enabled account; the notebook does
not enable keys, bypass policy, create a separate resource, or attempt an Entra
analysis fallback. Keys are not printed, saved, or added to configuration.

See the [tools verification record](../../specs/008-byom-foundry-tools/tasks.md)
for recorded checks and live acceptance status.

### Direct model API examples

[05_direct_api.ipynb](./notebooks/05_direct_api.ipynb) contains independent **APIM via
SDK**, **APIM via HTTPS**, **Foundry via OpenAI SDK**, **Foundry via HTTPS**, and
**Foundry via Azure AI Projects SDK** poem examples.
Each makes one pure Responses model request, with no agent or conversation lifecycle.
Run the chosen endpoint's settings/authentication cells, then its request example.
Each request is paid. No Azure resources are created, and Responses retention
follows the endpoint's existing policy.

**Settings and authentication**

The notebook lists required, optional, and example-specific variables.
Notebook deployment generates endpoint/model/scope settings; self-deployed users
supply equivalent values in `env/.env`. Use the complete OpenAI v1 base URL
ending in `/openai/v1/`, not `/responses`, and an accepted model reference.

Keep API keys empty for this demo's Entra-only deployment. External endpoints
can use a supported endpoint-specific key or DefaultAzureCredential with the
correct token scope. Foundry v1 uses `https://ai.azure.com/.default`; this demo's
APIM route uses `https://cognitiveservices.azure.com/.default`. Optional key-header
settings support endpoints requiring headers such as `api-key` or
`Ocp-Apim-Subscription-Key`. An APIM key does not bypass an independent JWT policy.
Each request announces the selected method without printing credentials and
does not retry another method on failure.

The Azure AI Projects SDK example additionally needs `AZURE_AI_PROJECT_ENDPOINT`
without `/openai/v1/` and Entra project access, even when inference uses a key.
All selected endpoints must already support Responses and authorize the supplied
identity/key and model.

**Direct APIM user access**

Before running Configure, set `APIM_ALLOWED_USER_OBJECT_ID` to your user object ID
in the deployment tenant. Obtain it with
`az ad signed-in-user show --query id -o tsv`, confirming the tenant first.
Configure applies the user allowlist while retaining the project identity's access.
An empty value permits project-only calls, not direct user calls.
DefaultAzureCredential must select the authorized identity; environment or
service-principal credentials may select a different caller.

Deployment's **Write env/.env** overwrites the base file. Preserve your user-ID
setting before rerunning that step, then rerun Configure. Configure's
**Write Gateway Settings** updates URL/model/scope fields while preserving keys
and unrelated settings.

**Verification**

Recorded user-run outputs verify all five examples with Entra, including the
consuming Foundry project. API-key authentication and other endpoint/model
combinations are not established by those runs. The
[direct API verification record](../../specs/007-byom-direct-api/tasks.md)
retains the detailed evidence. Direct model responses do not replace the
connected-model test's gateway telemetry verification.

## Cleanup

The Test notebook's **Clean Up Test Resources** cell deletes only its own conversation
and agent version. Invocation does not automatically delete them; run cleanup even
on inference failure. It retains the connection and gateway. For assistant-run
validation against pre-existing resources, record which configuration resources
and assignments were newly created and remove only those; never delete existing
groups as validation cleanup.

**Destructive:** the standard destroy notebook ships with its confirmation flags
enabled. Review the resource group and listed resources before running deletion.
Do not run all cells blindly.

First, select the subscription recorded in the generated environment file in a
terminal:

```powershell
az account set --subscription "<saved-subscription-id>"
```

### Delete the backend

The standard destroy notebook targets one group at a time.
In a fresh demo kernel, run this before its **Step 1** (do not save it in the
notebook):

```python
import os
from dotenv import dotenv_values

settings = dotenv_values("../env/.env")
os.environ["AZURE_RESOURCE_GROUP"] = settings["AZURE_BACKEND_RESOURCE_GROUP"]
os.environ["AZURE_AI_ENDPOINT"] = settings["AZURE_BACKEND_ENDPOINT"]
```

Run the review, deletion, Foundry purge, and resource-group removal steps.
Confirm the backend group and its soft-deleted Foundry account are gone.

### Delete the consumer

Restart the kernel and explicitly target the consumer before **Step 1**:

```python
import os
from dotenv import dotenv_values

settings = dotenv_values("../env/.env")
os.environ["AZURE_RESOURCE_GROUP"] = settings["AZURE_RESOURCE_GROUP"]
os.environ["AZURE_AI_ENDPOINT"] = settings["AZURE_AI_ENDPOINT"]
```

Its **Step 1** loads the generated
environment; ensure the loaded resource group and `AZURE_AI_ENDPOINT` belong to
this demo, not inherited values from another demo. Run its review, deletion,
Foundry purge, and resource-group removal steps.
The consumer group contains Application Insights and Log Analytics
resources; deleting that group also removes them and the project connection.
The backend inference assignment is scoped to the backend account and is removed
with that account. For validation-only cleanup without deleting the backend, target
the exact assignment ID recorded in the generated gateway settings.

The destroy notebook does **not** purge APIM. After it finishes, run this
separate command using `AZURE_SUBSCRIPTION_ID`, `AZURE_LOCATION`, and
`AZURE_APIM_NAME` saved in the environment file:

```powershell
az apim deletedservice purge --subscription "<saved-subscription-id>" --location "<saved-location>" --service-name "<saved-apim-name>"
```

APIM's name is reserved for 48 hours after soft deletion unless purged. Confirm
that this demo's resource group and Foundry/APIM soft-deleted records are gone;
the notebook's Cognitive Services verification alone does not verify APIM.

### Cleanup after a partial deployment

If backend deployment failed before settings were written, use
`BACKEND_RESOURCE_GROUP` and `BACKEND_LOCATION` from deployment configuration.
List that exact group, record the actual backend account name/endpoint, and use
the explicit environment targeting below to run the standard destroy flow.
Handle the consumer group separately; do not use its endpoint to purge the backend.

If the resource group was not created, there is nothing to delete. Otherwise,
select the exact deployment subscription as above and list that group's
resources before deleting anything:

```powershell
az resource list --subscription "<deployment-subscription-id>" --resource-group "<deployment-resource-group>" --output table
```

Record the actual Foundry and APIM names and locations from that group. With no
generated environment file, explicitly set the following in the destroy
notebook's kernel before running **Step 1** (do not save them in the notebook):

```python
import os
os.environ["AZURE_RESOURCE_GROUP"] = "<deployment-resource-group>"
os.environ["AZURE_AI_ENDPOINT"] = "https://<actual-foundry-account-name>.services.ai.azure.com/"
```

Then use the normal cleanup flow and the targeted APIM purge command. If no
Foundry account was created, skip **Step 4 - Purge soft-deleted AI resources**;
never run it without a target endpoint. If no APIM service was created, there is
no APIM service to purge. These are manual recovery instructions, not fallback
branches in the deployment notebook.
