# Infrastructure Contract

Implements the infrastructure milestone in [plan.md](../plan.md). This is a resource/input/output contract, not an additional deployment service.

## Resource Boundary

One explicitly selected subscription and resource group contain:

1. One `Microsoft.CognitiveServices/accounts` resource, `kind: AIServices`, S0.
2. One child project with project management enabled on the account.
3. Three child model deployments with distinct model identities/versions.
4. Account-scoped Cognitive Services OpenAI User assignment for the developer.

The user initially approved a two-model verification with quota-blocked GPT-5.4
explicitly recorded as skipped. On 2026-11-09 the user freed quota and approved
restoring the original third model through Bicep. All three now pass native
text/strict-JSON checks; generated metadata has no skipped deployment.

Use stable API `2026-09-01` for all three resource types. No storage account, database, container app, proxy, hosted agent, registry, Key Vault, or web app is required.

## Bicep Inputs

| Input | Meaning |
|---|---|
| `location` | Confirmed account/project region; researched starting point is `eastus2` |
| `demoId` | Default `assert01` |
| `uniqueSuffix` | Existing deterministic resource-name pattern |
| `projectDisplayName` | Human-readable ASSERT lab project name |
| `modelDeployments` | Three records, or two for explicitly approved partial verification; alias, deployment name, model identity/version, SKU and capacity |
| `inferencePrincipalId` | Signed-in developer object ID for account-scoped inference RBAC |

Model versions have no baked-in Bicep defaults. Resolve them against the live selected-subscription catalog and provide them as deployment parameters. Do not copy the GPT-4o source version. Model names are not deployment names: ASSERT receives the documented provider route `azure/gpt5_series/<deployment-name>` for these three GPT-5 generations.

The public-catalog candidates are documented in [research.md](../research.md). They are not selectable deployment guarantees until subscription access, policy, SKU support, and quota checks pass.

Platform settings are defined in Bicep:

- Project management enabled.
- Local authentication disabled (`disableLocalAuth: true`) for the user-approved native Entra path, matching inherited policy.
- Developer inference role assignment; no new service principal or stored credential.
- Public network access as in the copied minimal demo.
- `GlobalStandard` deployment SKU, subject to live verification.
- `NoAutoUpgrade` deployment version policy.
- No custom content-filter bypass, tenant-policy exemption, network-rule mutation, or automatic substitute model.
- Deploy the project before model writes and serialize deployments with `@batchSize(1)`.

Capacity is provider-specific allocation, not universally thousands of tokens per minute. Select each model's supported minimum/increment and sufficient free quota; do not copy the source demo's `100` capacity value to all models.

## Deployment Outputs

Return non-secret values:

- Subscription/resource-group identity and location.
- AI Services account name and resource ID.
- AI endpoint for compatibility with the standard cleanup notebook.
- Azure OpenAI provider endpoint: `https://<account>.openai.azure.com/`.
- Foundry project name and endpoint: `https://<account>.services.ai.azure.com/api/projects/<project>`.
- Three deployment records with actual model identity/version, SKU, and capacity.

No account keys, tokens, or credential-bearing connection strings may be Bicep/ARM outputs or template parameters.

## Generated Environment

The deployment notebook writes git-ignored `env/.env` automatically after successful provisioning and SDK metadata retrieval. It must include:

| Variable | Purpose |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Explicit deployment subscription |
| `AZURE_RESOURCE_GROUP` | Standard cleanup resource group |
| `AZURE_LOCATION` | Deployment location |
| `AZURE_AI_ENDPOINT` | AI endpoint consumed by standard cleanup |
| `AZURE_AI_ACCOUNT_NAME` | Management-plane account lookup |
| `AZURE_AI_PROJECT_ENDPOINT` | Foundry project reference |
| `AZURE_API_BASE` | Native ASSERT/LiteLLM Azure provider endpoint |
| `ASSERT_AZURE_USE_AAD` | `1`, explicitly select native Entra rather than fallback |
| `AZURE_TOKEN_CREDENTIALS` | `AzureCliCredential`, restrict native credentials to the setup login |
| `AZURE_API_VERSION` | Explicit dated provider API version; planned GA compatibility value `2024-10-21`, subject to M1 connection validation |
| `ASSERT_TARGET_OLDER` | Older model deployment name |
| `ASSERT_TARGET_INTERMEDIATE` | Intermediate model deployment name |
| `ASSERT_TARGET_NEWER` | Newer model deployment name |

Store richer actual-model metadata in secret-free `outputs/generated/deployment.json`,
including `skipped_deployment` and `skip_reason` (both null for complete deployment).
An explicit partial state must account for all three planned aliases and may skip
only one; do not fabricate an active alias for it. Omit its generated environment
alias and clear any stale ambient value when loading.

The notebook displays paths/non-secret identities, not tokens or raw payloads.

Use management SDKs for resource-group lifecycle and nested `.properties` resource
metadata. No keys are retrieved. Use narrow captured CLI calls for Bicep and
signed-in-user lookup rather than adding a Graph SDK. Authentication stays in
setup; the native ASSERT provider refreshes Entra tokens from that Azure CLI login.

## Infrastructure Acceptance Gate

Before functionality is considered delivered:

1. Bicep builds successfully.
2. The selected subscription's catalog confirms all three exact model/version/SKU combinations and supported capacity increments.
3. Effective inherited Azure policy permits the planned authentication/network settings; do not infer this from an unfiltered empty assignment list.
4. Provisioning succeeds with exactly the intended account, project, and three deployments.
5. Generated environment and metadata match the deployed resources.
6. Each target returns one real response through the same provider path ASSERT will use. This connection smoke test precedes policy evaluation and is not an unreviewed candidate-test run.
7. All keys remain out of notebook output, native configs, command arguments, and tracked files.

No keys or bearer tokens may be persisted even in ignored demo settings. The
explicit Entra path supersedes the original key design; a successful two-model
smoke is recorded as partial and never satisfies the three-model gate.

Public documentation or a successful template build alone does not satisfy this live gate.

## Cleanup

Copy the speech source destroy notebook verbatim. Before running it, explicitly verify/select the subscription recorded in generated environment settings because the standardized notebook uses the Azure CLI's selected subscription.

The learner must understand that the source notebook's confirmation flags may already be true. Follow its resource deletion, Cognitive Services soft-delete purge, and resource-group deletion flow. Verify resource absence and successful purge through the existing flow, not by adding notebook fallback branches.
