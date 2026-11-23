# BYOM capability testing

## Problem and hypothesis

Bring-your-own-model experiments need a repeatable resource foundation.
An engineer should be able to provision the gateway, AI resource/project, and
search service, and a separately hosted model backend through notebooks without
manually creating resources or copying connection values.

## Resource foundation and model backend

| Resource | SKU | Capacity |
|---|---|---|
| Azure API Management | Standard | 1 unit |
| Consumer Microsoft Foundry (`AIServices`) | S0 | One account with one project |
| Foundry IQ (Azure AI Search) | Standard (S1) | 1 replica, 1 partition |
| Backend Microsoft Foundry (`AIServices`) | S0 | Separate account hosting GPT-5.4 |
| Backend `gpt-5.4` deployment | GlobalStandard | 100 units (100,000 TPM) |

Consumer region: **UK South**, unchanged. Backend region: **Sweden Central**,
in a second resource group in the same selected subscription. GlobalStandard
inference may process outside Sweden; this is not a Sweden-only residency guarantee.
All service endpoints are public and authenticated.
Infrastructure is defined in [main.bicep](./infra/main.bicep).
The separate account/model are defined in [backend.bicep](./infra/backend.bicep).
The accounts and consumer project have system-assigned identities, but no
cross-service connections or runtime permissions are configured. Backend local
key authentication is disabled in Bicep, matching the current tenant-enforced
consumer behavior. No backend project is needed to host the model deployment.

**Out of scope**: connected-model registration, BYOM testing, APIM routes and
backends, search indexes/ingestion, knowledge bases, Foundry IQ connections, and
evaluations. Provisioning the search resource does not create a retrieval flow.

**Costs**: APIM Standard and Search S1 have ongoing capacity charges even when
idle. Foundry uses S0; the backend deploys a pay-per-token model, but this
provisioning journey makes no inference calls. Check current
[APIM pricing](https://azure.microsoft.com/pricing/details/api-management/) and
[search pricing](https://azure.microsoft.com/pricing/details/search/), plus
[model pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/), before
deploying. This is a prototype, not a production availability configuration.

## Prerequisites

- Python >=3.10, VS Code with Jupyter support, Azure CLI, and an up-to-date Bicep
  compiler (`az bicep upgrade` if already installed).
- An explicitly selected Azure subscription with permission to create/delete the
  resources and purge Foundry and APIM soft-deleted services. No role assignments
  are created by this demo.
- Available standard-tier capacity in UK South, or another region you choose
  for the consumer before deploying, and GPT-5.4 GlobalStandard quota in
  Sweden Central for the backend. The notebook resolves the current generally
  available default model version from the regional catalog. No automatic model,
  region, subscription, or SKU fallback is used.
- Subscription policy must permit the public-access design. Do not bypass policy
  with tags or change tenant networking from a notebook.

## Notebook journey

| Notebook | Purpose |
|---|---|
| [00_setup.ipynb](./notebooks/00_setup.ipynb) | Create the venv/kernel, authenticate/select subscription, install dependencies |
| [01_deploy_infra.ipynb](./notebooks/01_deploy_infra.ipynb) | Check backend model/quota, compile both templates, deploy both groups via the Python SDK, generate local settings |
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

Default groups are `rg-byom01-uks` (consumer) and `rg-byom01-backend-swc`
(backend). Keep them distinct. Repeating deployment targets the same names;
changing a group name creates another set of resources.

The deployment journey is adapted from evalgw02; setup and destroy follow the
speech demo standards. The SDK dependency is kept on its 23.x API used here.
The Cognitive Services management SDK reads the model catalog/quota. No
inference/evaluation/search SDK is needed yet. If already set up, rerun setup's
**Step 3** to install the added management dependency.

## Generated configuration and verification

[.env.example](./env/.env.example) lists the 25 fields generated
from deployment outputs. Do not fill it in or manually author `env/.env`.
The generated file is ignored by Git and contains no API keys.

After deployment, check the consumer SKUs, public network settings, and Foundry
child project. In the backend group, verify the second account is in Sweden
Central and its GPT-5.4 deployment has the selected version, GlobalStandard SKU,
and capacity 100. The `AZURE_BACKEND_*` settings identify the provider; the original
Foundry/project settings still identify the consumer. These resources alone do
not yet route requests through APIM or create a connected model.
Repeat deployment with unchanged configuration to
update the same resource names rather than duplicate resources. A previous
environment file records its previous successful run; it is not evidence that a
subsequent failed deployment succeeded.

Local validation and optional live acceptance are described in the
[validation guide](../../specs/005-byom-capability-testing/quickstart.md).

## Cleanup

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
