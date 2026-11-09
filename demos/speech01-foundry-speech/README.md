# speech01: Azure AI Foundry + Speech Roundtrip

## Problem statement

Teams want to validate that a hosted service can call Azure Speech with managed identity in a Foundry-aligned setup, without rewriting speech code for the newer `AIServices` resource model.

## Hypothesis

If we deploy one `AIServices` account with Foundry project support enabled, an Azure Function using managed identity can call Speech with minimal code changes compared to the previous Cognitive Services account pattern.

## Scope

- In scope:
	- Deploy one Azure AI Services account (`kind: AIServices`) with project management enabled.
	- Deploy one Foundry project under that account.
	- Deploy and publish an Azure Function that calls Speech using managed identity.
	- Write deployment outputs to `env/.env` automatically.
	- Run direct notebook Speech SDK synthesis/recognition and service-based invocation against the same deployed account.
- Out of scope:
	- Real-time streaming agents and conversation orchestration.
	- Production networking, private endpoints, and managed identity hardening.
	- Human-recorded audio capture from microphone.

## Notebook journey

Run notebooks in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, Azure login, and install Python packages |
| `01_deploy_infra.ipynb` | Deploy Bicep for AIServices + Foundry project and write bootstrap values to `env/.env` |
| `02_configure.ipynb` | Publish the Function App code, capture the function key, and preview available voices |
| `03_test.ipynb` | Synthesize text to WAV, run speech recognition on the WAV, and save output |
| `04_function.ipynb` | Invoke Azure Function with function-key auth, verify managed-identity Speech call output, and inspect recent logs |

## Folder map

```text
infra/      # Bicep for AIServices account + Foundry project
notebooks/  # numbered notebook flow
env/        # .env.example contract; .env auto-written by notebook 01
app/        # demo-scoped helper scripts and notebook utilities
data/       # optional inputs
docs/       # architecture notes
outputs/    # generated WAV and JSON test output
```

## Quick start

1. Open `notebooks/00_setup.ipynb` and run all cells.
2. Run `notebooks/01_deploy_infra.ipynb` to create resources and generate the bootstrap `env/.env` file.
3. Run `notebooks/02_configure.ipynb` to publish the function code, write the function key, and choose a voice.
4. Run `notebooks/03_test.ipynb` to execute the end-to-end speech roundtrip.
5. Run `notebooks/04_function.ipynb` to validate service-hosted managed-identity Speech access and view function traces.

## GitHub Actions journey

The `Notebook journey selection` workflow runs this demo on affected main
pushes and manual dispatch. It executes `00_setup.ipynb`, `01_deploy_infra.ipynb`,
`02_configure.ipynb`, `03_test.ipynb`, `04_function.ipynb`, then
`X_destroy.ipynb`, using a separate Python kernel for each notebook. The setup,
deployment, roundtrip-recognition, and Function-response checks must all
succeed. Other discovered demos are reported as unsupported until enabled.

Before enabling live runs, configure a `speech01-ci` GitHub Environment with
these variables:

| Variable | Value |
|---|---|
| `AZURE_CLIENT_ID` | Client ID of a dedicated service principal |
| `AZURE_TENANT_ID` | Entra tenant containing that application |
| `AZURE_SUBSCRIPTION_ID` | Existing subscription for temporary test resources |
| `AZURE_DEPLOYER_OBJECT_ID` | Object ID of the service principal |

Configure an Azure federated credential with issuer
`https://token.actions.githubusercontent.com`, audience
`api://AzureADTokenExchange`, and subject
`repo:Hsenrab/azure-solution-prototypes:environment:speech01-ci`. Restrict the
GitHub Environment to the `main` branch and do not require reviewers; main-merge
and manual runs then proceed without another per-run approval. No client secret
is used or stored.

The workflow names its resource group
`rg-speech01-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`. The Bicep deployment
creates run-scoped `Cognitive Services Speech User`, `Storage Blob Data
Contributor`, and `Monitoring Reader` assignments for the runner, plus the
Function managed identity's required Speech and Storage assignments. The
workflow refuses an existing resource group, tags the new group with its run
identity, and requires those tags before cleanup. Its fallback cleanup uses the
same run-specific ownership check.

The service principal needs resource-group creation/deletion and read,
resource-group deployments, CRUD for the Bicep-managed Cognitive Services
accounts and projects, Storage accounts, Function Apps/plans, and Application
Insights, plus the Function config/list-keys/restart/trigger-sync operations
used to publish the package and retrieve its function key. The runner also
reads subscription and deployment metadata, queries Application Insights, and
lists/purges soft-deleted Cognitive Services accounts scoped to its run group.
The list API requires `Microsoft.CognitiveServices/deletedAccounts/read` at
subscription scope; the purge action is
`Microsoft.CognitiveServices/locations/resourceGroups/deletedAccounts/delete`
and receives the run resource-group name.

In particular, `Microsoft.Authorization/roleAssignments/write` and role
definition read must be effective at a parent scope that covers each new run
resource group. The Bicep deployment grants only run-scoped
`Cognitive Services Speech User`, `Storage Blob Data Contributor`, and
`Monitoring Reader` roles to the runner; it grants the Function managed
identity its run-scoped Speech and Storage roles. The Storage data-plane upload
uses the Blob Data Contributor assignment. Use a least-privilege custom
management role for the required operations and scope data-plane access to the
run resources; do not grant `Owner`. Tenant policy or assignment conditions may
further constrain this setup and must be checked by the subscription owner.

Identity, federation, and Azure role provisioning are owner-supplied
prerequisites and are not created by this repository. No subscription,
application, federated credential, or effective RBAC configuration has been
verified here; live deployment and cleanup remain unverified until the owner
configures them.

Execution results and sanitized failure/cleanup statuses are written to the
GitHub Actions run summary. Executed notebook outputs, `.env`, function keys,
and generated audio are not uploaded. The journey always attempts the actual
destroy notebook, then retries cleanup only against that run's resource group
and soft-deleted Cognitive Services accounts identified by that group.

## Known limitations

- Speech synthesis and recognition are single-shot in this prototype.
- The test uses generated audio, not human microphone input.
- The function path is part of the main scenario, not optional.
- This demo uses function-key auth for the Function endpoint and AAD/managed identity for Speech calls from both notebooks and the Function service.

## Why Foundry-aligned here

- The demo keeps a Foundry-aligned `AIServices` + project topology while exercising Speech from a hosted service.
- The key behavior being demonstrated is that Speech invocation remains mostly unchanged when moving from older Cognitive Services account usage to this Foundry-aligned `AIServices` setup.
