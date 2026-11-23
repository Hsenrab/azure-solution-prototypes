# BYOM capability testing

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

Consumer region: **UK South**, unchanged. Backend region: **Sweden Central**,
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

For an existing backend, rerun **Configuration**, **Resolve Subscription and
Authentication**, **Select Backend Model and Check Quota**, **Compile Backend Bicep**,
and **Deploy Backend Bicep** in the deployment notebook with the original settings.
This adds the project while retaining the existing account and model configuration.
There is no need to rewrite `env/.env` or rerun Configure/Test just for this addition.
Refresh the Foundry project picker and select the backend project in
`rg-byom01-backend-swc`. Portal visibility remains a live verification step.

**Out of scope**: Search/RAG ingestion, knowledge bases, Foundry IQ connections,
tools, full Foundry tracing, evaluations, streaming tests, failover, and load testing.
Provisioning the search resource does not create a retrieval flow.

**Costs**: APIM Standard and Search S1 have ongoing capacity charges even when
idle. Foundry uses S0; the backend deploys a pay-per-token model, but this
deployment/configuration notebooks make no inference calls. The Test notebook
makes one paid Foundry Responses request, and telemetry ingestion has usage charges.
Check current
[APIM pricing](https://azure.microsoft.com/pricing/details/api-management/) and
[search pricing](https://azure.microsoft.com/pricing/details/search/), plus
[model pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/), before
deploying. This is a prototype, not a production availability configuration.

## Prerequisites

- Python >=3.10, VS Code with Jupyter support, Azure CLI, and an up-to-date Bicep
  compiler (`az bicep upgrade` if already installed).
- An explicitly selected Azure subscription with permission to create/delete the
  resources and purge Foundry and APIM soft-deleted services. Configuration also
    requires connection-write permissions and role-assignment permissions on the
    backend account and telemetry component.
- Available standard-tier capacity in UK South, or another region you choose
  for the consumer before deploying, and GPT-5.4 GlobalStandard quota in
  Sweden Central for the backend. The notebook resolves the current generally
  available default model version from the regional catalog. No automatic model,
  region, subscription, or SKU fallback is used.
- Subscription policy must permit the public-access design. Do not bypass policy
  with tags or change tenant networking from a notebook.
- **[PREVIEW]** Upstream Responses routing must be available in the consuming
  project. Creating a connection does not enable the feature flight. See the
  [Foundry gateway guide](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/ai-gateway).
- For testing, the signed-in identity needs **Foundry User** on the project and
  **Log Analytics Reader** or equivalent existing access on the generated workspace.
  Configuration does not automatically grant broader user permissions.

## Notebook journey

| Notebook | Purpose |
|---|---|
| [00_setup.ipynb](./notebooks/00_setup.ipynb) | Create the venv/kernel, authenticate/select subscription, install dependencies |
| [01_deploy_infra.ipynb](./notebooks/01_deploy_infra.ipynb) | Check backend model/quota, compile both templates, deploy both groups via the Python SDK, generate local settings |
| [02_configure.ipynb](./notebooks/02_configure.ipynb) | Configure the managed-identity route, scoped RBAC, connected model, and telemetry; generate gateway settings |
| [03_test.ipynb](./notebooks/03_test.ipynb) | Invoke the connected model through Foundry, save correlated gateway evidence, and clean up the test version/conversation |
| [X_destroy.ipynb](./notebooks/X_destroy.ipynb) | Standard resource deletion and Cognitive Services purge |

1. Open setup and run **Step 1**. Switch to **Python (byom01-capability-testing)**
   before running **Step 2** and **Step 3**.
2. Open deployment using that kernel. Notebook working directory must be
   `notebooks/`, as in the source demos.
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

The deployment journey is adapted from evalgw02; setup and destroy follow the
speech demo standards. The SDK dependency is kept on its 23.x API used here.
The Cognitive Services management SDK reads the model catalog/quota. AI Projects
2.x invokes the service-side prompt agent; Azure Monitor Query reads gateway traces.
Its OpenAI client follows the documented Foundry agent protocol, not direct
`AzureOpenAI` backend calls. If already set up, rerun setup's **Step 3** to install
the updated requirements.

### Existing deployment

To apply APIM identity without repeating backend quota/deployment checks, rerun
**Configuration**, **Resolve Subscription and Authentication**, **Compile Bicep**,
and **Deploy Bicep** in the deployment notebook with the original settings.
Existing names and base environment values remain unchanged. Do not run
**Write env/.env** after this consumer-only update: that step requires both
deployment results. Then run Configure and Test.

## Generated configuration and verification

[.env.example](./env/.env.example) lists the 25 fields generated
from deployment outputs. Do not fill it in or manually author `env/.env`.
The generated file is ignored by Git and contains no API keys.

After deployment, check the consumer SKUs, public network settings, and Foundry
child project. In the backend group, verify the second account is in Sweden
Central and its GPT-5.4 deployment has the selected version, GlobalStandard SKU,
and capacity 100. The `AZURE_BACKEND_*` settings identify the provider; the original
Foundry/project settings still identify the consumer. These resources alone do
not route requests through APIM until Configure completes.
Repeat deployment with unchanged configuration to
update the same resource names rather than duplicate resources. A previous
environment file records its previous successful run; it is not evidence that a
subsequent failed deployment succeeded.

Local validation and optional live acceptance are described in the
[validation guide](../../specs/005-byom-capability-testing/quickstart.md).

### Connected-model evidence

Configure generates ignored `env/gateway.json` containing connection/model/gateway
identifiers, workspace ID, and project context. Do not edit it manually.
The route is OpenAI v1 Responses, with no deployment path or `api-version`.
APIM accepts only the consuming project's Entra identity and the configured
deployment, then authenticates to the fixed backend using its own identity.
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

The connection uses the supported `ProjectManagedIdentity` value omitted from
published Bicep types. One documented, field-specific `BCP036` accommodation is
used; unrelated diagnostics remain enabled. Source verification does not prove
deployment, feature availability, or inference in this subscription.

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

The standard destroy notebook targets one group at a time. Keep it unchanged.
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
The consumer group contains the added Application Insights and Log Analytics
resources; deleting that group also removes them and the project connection.
The backend inference assignment is scoped to the backend account and is removed
with that account. For validation-only cleanup without deleting the backend, target
the exact assignment ID recorded in the generated gateway settings.

The unchanged notebook does **not** purge APIM. After it finishes, run this
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
