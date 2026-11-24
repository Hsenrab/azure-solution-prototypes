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
Each direct-model example in the API notebook makes one additional paid request.
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
| [04_direct_api.ipynb](./notebooks/04_direct_api.ipynb) | Pure Responses calls through APIM/Foundry via OpenAI SDK or HTTPS, plus an Azure AI Projects SDK example |
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

[.env.example](./env/.env.example) lists deployment-generated fields and the
direct-client settings. The resource journey generates its base `env/.env`;
do not manually populate its resource IDs/endpoints. The direct-client exception
below also permits equivalent external settings. Real `.env` files remain ignored.

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

The connection uses the supported `ProjectManagedIdentity` value omitted from
published Bicep types. One documented, field-specific `BCP036` accommodation is
used; unrelated diagnostics remain enabled. Source verification does not prove
deployment, feature availability, or inference in this subscription.

### Direct model API examples

[04_direct_api.ipynb](./notebooks/04_direct_api.ipynb) contains independent **APIM via
SDK**, **APIM via HTTPS**, **Foundry via OpenAI SDK**, **Foundry via HTTPS**, and
**Foundry via Azure AI Projects SDK** poem examples.
Each makes one pure Responses model request, with no agent or conversation lifecycle.
Run only the selected endpoint's settings/authentication and chosen request cells;
every request cell makes an additional paid request. No retries or alternate
authentication after failure. Recorded user-run outputs show completed poems and
response IDs with Entra authentication for all five examples, including the
Azure AI Projects SDK against the consuming Foundry project. These runs precede
the custom-key header correction; the Entra request path is unchanged. Other
endpoint/model or authentication combinations, including live API-key calls,
are not established by those runs.
The [verification record](../../specs/007-byom-direct-api/tasks.md) retains the
results; notebook outputs are removed by the normal pre-commit cleanup.

**Authentication convention for new BYOM notebooks:** from this notebook onward,
read endpoint-specific settings from `env/.env`. Use a nonempty configured API key
when present; otherwise use `DefaultAzureCredential` with the endpoint's token
scope. SDK and HTTPS examples use the same selection and print `Using API key` or
`Using Microsoft Entra ID (DefaultAzureCredential)` before each request, without
printing credentials. Failures do not trigger a retry with another method.
When a custom key header is configured, SDK and HTTPS requests send that header
without an additional Authorization bearer header. SDK examples omit Authorization
on the request so the SDK recognizes the deliberate override.
Keys apply only to APIs that support them; Azure deployment, RBAC, and resource
cleanup still require Entra. Earlier notebooks are unchanged by this convention,
and this deployment's gateway remains Entra-only.

For **this repo's deployment**, set `APIM_ALLOWED_USER_OBJECT_ID` in `env/.env` to
your user object ID in the deployment tenant. Confirm your tenant, then obtain the
ID with `az ad signed-in-user show --query id -o tsv`. This is a configuration input,
not a secret. Rerun Configure from **Load Deployment Settings** through **Write
Gateway Settings** to deploy the Bicep allowlist and generate `APIM_BASE_URL`,
`APIM_MODEL_NAME`, and `APIM_TOKEN_SCOPE` from successful outputs. The write step
preserves unrelated `.env` fields, comments, and API keys. An empty user ID keeps
project-only access and cannot authorize direct user calls.

The new notebook uses **DefaultAzureCredential**, which must select that permitted
user. Existing environment/service-principal credentials may select another caller;
they are not automatically authorized. No user lookup, role grant, backend key
enabling, or policy patch occurs in the inference notebook. The gateway still
validates tenant and audience, and the original project caller stays permitted.
Re-running deployment's **Write env/.env** overwrites the base file: retain your
user-ID setting before doing so and rerun Configure afterward.

For an **external gateway**, supply `APIM_BASE_URL` (complete HTTPS OpenAI v1 route,
not ending in `/responses`) and `APIM_MODEL_NAME` directly in `env/.env`; no repo
deployment is required. A nonempty `APIM_API_KEY` selects key mode, optionally with
`APIM_API_KEY_HEADER` for an endpoint expecting `Ocp-Apim-Subscription-Key` or
`api-key`. Without a key, supply the endpoint's `APIM_TOKEN_SCOPE` for Entra.
The external endpoint must already support Responses and authorize that credential.
An APIM subscription key alone does not bypass an independent JWT policy.
Do not set a key for this repo's Entra-only gateway. Never commit or print keys.

For the **Foundry Responses examples**, Configure's **Write Gateway Settings**
generates `FOUNDRY_BASE_URL` from the consuming project endpoint, appending
`/openai/v1/`, plus `FOUNDRY_MODEL_NAME` from the registered connected-model
reference and `FOUNDRY_TOKEN_SCOPE=https://ai.azure.com/.default` in `env/.env`.
If Configure's successful readback is still available in the kernel, rerun only
**Write Gateway Settings**; generating these fields requires no redeployment.
It updates only the APIM/Foundry URL/model/scope fields, preserving keys and
unrelated settings.

External users may instead supply equivalent settings documented in
[.env.example](./env/.env.example), with either an API key or token scope. Use the
complete consuming resource or project OpenAI v1 base URL, not the backend
resource; rerunning Configure replaces the direct URL/model/scope fields with
this deployment's values. The model reference, for example
`byom01-gateway/gpt-5.4`, is passed unchanged. Foundry authentication is independent
of APIM authentication. The documented Foundry v1 token scope is
`https://ai.azure.com/.default`; do not assume APIM's scope applies. An optional
`FOUNDRY_API_KEY_HEADER` selects a custom key header. Leave keys empty for Entra-only
deployments.

The **Azure AI Projects SDK** example uses the existing
`AZURE_AI_PROJECT_ENDPOINT` file setting, without `/openai/v1/`, instead of
`FOUNDRY_BASE_URL`. Deployment already generates this field; external users can
supply their consuming project endpoint directly. `AIProjectClient` creates the
OpenAI client through `get_openai_client()` without querying the project or
creating an agent. Its required TokenCredential is supplied with
DefaultAzureCredential, while the documented `api_key` override reuses the
selected key or token provider for the model request. This does not give API keys
access to project-management operations or acquire an additional Entra token in
key mode. No new dependency is required.

The [documented endpoint shapes](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/model-router-apis#choose-an-endpoint)
and a portal Chat Completions example do not prove that the supplied connected-model
name resolves through Responses. Only a successful invocation verifies the tested
endpoint/model combination; a resource-endpoint result does not verify the project
endpoint. Errors propagate without agent, backend, or APIM fallback. These examples
make no changes to gateway routes, connection scope, authentication policies, or keys.
The recorded user-run project examples establish that tested Responses combination,
not independent gateway telemetry verification or support for arbitrary endpoints.

Run setup's **Step 3** to install the explicit OpenAI and HTTPX dependencies. Read
the chosen endpoint's settings/authentication first, then select its request example. Responses may
be stored under the endpoint's existing policy; the notebook makes no retention
changes. No new Azure resources are needed for direct calls.

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
