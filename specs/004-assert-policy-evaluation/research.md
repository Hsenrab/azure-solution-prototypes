# Research: ASSERT Policy Evaluation Lab

**Date**: 2026-11-05

**Scope**: Planning evidence for [spec.md](./spec.md); no resources deployed or model requests submitted.

## 1. Repository Integration

**Decision**: Create the demo from [demo-template](../../demo-template/), adapt the minimal [GPT-4o Bicep](../../demos/gpt4o01-text-image-audio/infra/main.bicep), retain the [speech setup](../../demos/speech01-foundry-speech/notebooks/00_setup.ipynb) structure, and copy the [speech destroy](../../demos/speech01-foundry-speech/notebooks/X_destroy.ipynb) notebook verbatim.

**Rationale**: The existing template, Foundry resource shape, and notebook lifecycle satisfy the approved infrastructure-first journey without introducing another architecture.

**Alternatives considered**:

- The LiteLLM hosted-proxy demo is ruled out as an infrastructure source: its container app, registry, and database are unnecessary. ASSERT's in-process model-provider dependency does not require hosting a proxy.
- Copying the source deployment notebook's ARM/Bicep toggle is ruled out: this lab needs one Bicep-defined happy path, not two deployment strategies.
- Changing setup order or editing the standardized destroy implementation is ruled out by repository guidance.

**Repository evidence**:

- [Authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md): demo layout, deployment-generated environment, notebook conventions.
- [Foundry standards](../../.github/skills/azure-demo-authoring/references/azure-ai-foundry.md): AIServices, stable APIs, model validation, no baked-in model versions.
- [Constitution](../../.specify/memory/constitution.md): infrastructure-first fixes and existing quality gates.
- [Pre-commit configuration](../../.pre-commit-config.yaml) and [notebook metadata workflow](../../.github/workflows/notebook-metadata-check.yml): output stripping and removal of kernel display-name metadata.

## 2. Infrastructure API Versions

**Decision**: Use stable `2026-09-01` for `Microsoft.CognitiveServices/accounts`, `accounts/projects`, and `accounts/deployments`. Keep an `AIServices` account with project management enabled, a project, and exactly three `GlobalStandard` target deployments.

**Rationale**: Official schema references expose this stable version for all three resource types. There is no need to adopt the newer preview API or preserve the source demo's older mixed API versions.

**Platform behavior defined in Bicep**:

- `disableLocalAuth: true` for the subsequently approved policy-compliant native Entra authentication, with account-scoped developer inference RBAC.
- Public access as in the source demo; no tenant-specific network mutations.
- Model deployment names, model identities, versions, and capacities as explicit inputs.
- `versionUpgradeOption: NoAutoUpgrade` to avoid silent changes within an evaluation comparison. Retirement still requires an explicit new model selection.
- Secret-free outputs: account/project identity, endpoints and deployment configuration. No account keys are retrieved or persisted under the approved native Entra path.

**Alternatives considered**: Preview APIs add no required feature; notebook-driven changes to authentication, upgrade policy, or networking would violate infrastructure-first rules.

**Sources**:

- [Account schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2026-09-01/accounts).
- [Project schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2026-09-01/accounts/projects).
- [Deployment schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2026-09-01/accounts/deployments), including `versionUpgradeOption` and SKU capacity.

## 3. Three Model Generations

**Decision**: Use the following public-catalog selection as the implementation starting point, with `eastus2` as the account region and `GlobalStandard` deployments:

| Role in comparison | Model | Public version snapshot | Evidence |
|---|---|---|---|
| Older | `gpt-5` | `2025-08-07` | GA in lifecycle schedule; Global Standard available in eastus2 |
| Intermediate | `gpt-5.4` | `2026-03-05` | GA in lifecycle schedule; Global Standard available in eastus2 |
| Newer | `gpt-5.6-sol` | `2026-07-09` | GA in lifecycle schedule; Chat Completions and structured outputs documented; Global Standard available in eastus2 |

These are researched candidates, not evidence of subscription entitlement or free quota. Versions are a dated research snapshot, not defaults to hardcode into Bicep.

**Rationale**: This spans distinct releases while avoiding deprecated models.
The original plan reused intermediate for generation/tester/judge. After its
quota block, the user explicitly approved `newer` for those roles and bounded M2
evaluation on the two deployed targets, without a fourth deployment.

**Alternatives considered**:

- GPT-4.1 and GPT-4o-mini are ruled out as new defaults because the current lifecycle schedule marks them deprecated.
- GPT-4o `2024-11-20` is marked Legacy, not retired, but offers less longevity than the chosen older GA candidate.
- GPT-6.1-terra is ruled out for this region because the current Global Standard table does not list eastus2 support.
- GPT-6.1-sol is a documented newer supported model, but is ruled out as the starter default because the researched LiteLLM Azure provider explicitly documents the GPT-5 family route, not a GPT-6.1-specific transformation. The selected GPT-5, GPT-5.4, and GPT-5.6 releases still span three distinct older-to-newer generations without adding an unverified provider-family assumption.
- `gpt-chat-latest` is ruled out because it is a moving preview target, which weakens versioned comparisons.
- A fourth dedicated judge deployment is ruled out for the initial learning lab. Reusing an evaluated model as judge may introduce bias; document that limitation rather than claiming independence.

**Live prerequisite**: Before provisioning, resolve the explicitly selected subscription and validate each exact model/version/SKU, supported capacity increment, access restrictions, and available quota. If any candidate fails, stop and obtain an explicit supported selection; do not silently substitute models, regions, or deployment names.

**Sources**:

- [Current Azure model catalog](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure).
- [Regional availability](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability), Global Standard Americas table.
- [Retirement schedule](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirement-schedule).
- [Reasoning-model guidance](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/reasoning), including supported API and request parameters.

## 4. Credentials, Management Operations, and Dependencies

**Decision (amended after policy investigation)**: Use the selected Azure CLI
identity for management SDK calls and native ASSERT's refreshable Entra token
provider. Generate git-ignored non-secret endpoint/alias/auth-mode settings.
Never retrieve account keys or persist bearer tokens, literal YAML credentials
or credential-bearing command arguments.

**Rationale**: This follows the approved authentication direction and source infrastructure while avoiding notebook-embedded keys. The notebook consumes Bicep-defined behavior instead of enabling local authentication after deployment.

**Management dependencies verified on PyPI**:

| Package | Current stable release observed | Python requirement |
|---|---|---|
| `azure-mgmt-resource` | `26.0.0` | `>=3.10` |
| `azure-mgmt-cognitiveservices` | `14.1.0` | `>=3.9` |
| `azure-identity` | `1.27.0` | `>=3.10` |
| `python-dotenv` | `1.2.4` | `>=3.10` |

Use the isolated demo environment; validate the final dependency resolution during implementation, not by installing packages into the shared planning environment.

**Operational constraints**:

- Prefer `AZURE_SUBSCRIPTION_ID`; otherwise locate an existing target resource group or require explicit subscription selection for a new group. Never select the first enabled subscription.
- Use the Python management SDK for resource-group operations, account keys, and deployment metadata. Azure CLI/Bicep remains the narrow compilation/provisioning path inherited from the source demo.
- Use argument lists, not shell interpolation. New Azure CLI notebook invocations must expose captured stdout/stderr on failure according to the authoring workflow.
- Do not print account-key objects, dump the environment, enable credential-bearing debug logs, or save secrets in frozen evaluation configurations.
- Existing `.env` ignore rules cover generated credentials. Put generated ASSERT artifacts under `outputs/generated/`, which is already recursively ignored.
- The verbatim destroy notebook uses the Azure CLI's selected subscription. Require learners to verify/select the recorded deployment subscription before cleanup; do not modify that standardized notebook to compensate.
- If inherited policy forbids the approved access pattern, stop rather than changing tenant/network policy or adding an authentication fallback.

**Sources**:

- [Management SDK account operations](https://learn.microsoft.com/en-us/python/api/azure-mgmt-cognitiveservices/azure.mgmt.cognitiveservices.operations.accountsoperations?view=azure-python).
- Public package metadata: [resource](https://pypi.org/pypi/azure-mgmt-resource/json), [Cognitive Services](https://pypi.org/pypi/azure-mgmt-cognitiveservices/json), [identity](https://pypi.org/pypi/azure-identity/json), [dotenv](https://pypi.org/pypi/python-dotenv/json).
- [Repository ignore rules](../../.gitignore).

## 5. Evidence Limits

- Azure Foundry MCP discovery failed because no usable Azure credential was available to that tool. Public Microsoft documentation was used for API schemas and model capabilities instead; this does not establish access to a particular subscription.
- No live regional quota, effective subscription policy, resource provisioning, model response, cleanup, or paid evaluation has been validated during planning.
- No package installation was performed. Public release metadata is not a dependency-resolution or runtime compatibility test.
- Working Git branch observed: `feat/search-vector-contributions`. Spec Kit resolves the active feature to `004-assert-policy-evaluation`; this planning operation does not switch branches or claim that a matching Git branch exists.

## 6. ASSERT Release and Native Integration

**Decision**: Pin `assert-ai==0.3.0`, requiring Python >=3.11. Use source at commit `04b713fe73879208369750b3bd5ad53544f3eecc` (release `v0.3.0`) for the implementation contracts.

**Rationale**: The PyPI release and immutable source support the needed hosted model, adaptive scenario, taxonomy, stage-control, and saved-artifact interfaces. Current `main` is ahead of the release and must not silently become the API contract.

**Verified release behavior**:

- The console script is `assert-ai`; the equivalent selected-interpreter invocation is `python -m assert_ai.cli`. There is no package-level `assert_ai.__main__`.
- The native pipeline is chronological: `systematize`, `test_set`, `inference`, `judge`. Each stage accepts enable/disable control. There is no stop-after-generation CLI flag.
- `suite`-level taxonomy/test artifacts are shared; `run`-level inference/judge artifacts are distinct. Explicitly disabled generation stages and approved input paths are stronger than relying only on a cache hit.
- `--force-stage` cascades to configured downstream stages. It is not part of this lab's normal evaluation path because approved artifacts must not be regenerated between targets.
- `pipeline.inference.target.model` selects the hosted deployment; `target.system_prompt` supplies policy instructions. `tester.model` drives adaptive scenarios, and `inference.max_turns: 3` caps exchanges.
- Native input cases identify their taxonomy category with `behavior`. The authoritative boolean classification is `taxonomy.behavior_categories[].permissible`; unknown categories can otherwise lose classification, so the lab validates this join before approval.
- Built-in boolean dimensions are `policy_violation` and `overrefusal`. The latter is displayed as unnecessary refusal. Native full-transcript judging and citation handling support offending-message evidence.
- Failed judging and skipped scoring are distinct from semantic N/A. Valid scored applicability, not attempted-case count, determines each displayed metric denominator.
- `ModelConfig` exposes only `name`, `temperature`, `max_tokens`, and `reasoning_effort`. Endpoint/key/version configuration is not an arbitrary YAML extension, and `${VARIABLE}` interpolation is not supported.
- Native run `config.yaml` is a literal copy of the input YAML, not a credential-injected document. Keep input strings and configs secret-free.
- ASSERT passes chat request options through LiteLLM. Temperature defaults to omitted; do not add `temperature: 0` indiscriminately to reasoning models. Token-option adaptation is provider-library behavior, so exercise each actual deployment through the same provider path at the connection gate.
- Adaptive transcript content is generated at execution time. Approval fingerprints cover reviewed scenario definitions and shared tester settings, not identical runtime messages.

**Alternatives considered**:

- Replacing generation with an entirely handwritten test set is ruled out because it removes the requested generate/review learning step. Handwritten cases supplement actual generated cases.
- A custom conversation or judge engine is ruled out: the native tester and transcript judge already satisfy the behavior.
- A hosted LiteLLM proxy, ACS policy export extra, local web viewer, and Foundry-hosted agent are unnecessary. In particular, ACS is not a required installable PyPI extra for this lab.
- Blindly displaying a single native aggregate is ruled out when it does not match the requested interaction-type and permissibility-specific denominator.

### Provider and Sampling Details

**Updated decision, user-approved 2026-11-05**: Use the native Azure Chat
Completions provider, endpoint root `https://<account>.openai.azure.com/`,
`AZURE_API_BASE` / `AZURE_API_VERSION`, explicit `ASSERT_AZURE_USE_AAD=1` and
`AZURE_TOKEN_CREDENTIALS=AzureCliCredential`. The installed ASSERT 0.3.0 already
injects a refreshable Entra callback for `azure/*`; no custom adapter/static token
is needed. Bicep disables local auth and grants account-scoped inference RBAC,
complying with discovered inherited policy without exemptions. This supersedes
the initial key-authentication choice.

Keep the documented `azure/gpt5_series/<deployment-name>` route and separate human
aliases from deployment names. The user initially approved partial older/newer
verification while GPT-5.4 quota was blocked. Actual text and
structured checks passed for both using API `2024-10-21`. A 1,024-token request
exhausted its reasoning budget; a fixed 4,096-token budget passed without changing
reasoning effort, provider, or API. See the demo's architecture notes for evidence.

On 2026-11-09, GPT-5.4 GlobalStandard quota was revalidated at 100 used / 250
limit; its exact GA version 2026-03-05 and catalog default capacity 10 passed.
The user approved restoring that target through existing Bicep. All three
deployments passed the same native text/strict-JSON API 2024-10-21 path, and
GPT-5.4 completed the original frozen 14 cases without changing shared roles
or rerunning older/newer. This resolves the original third-model deferral.

ASSERT itself performs no reasoning-model-specific token-option conversion. LiteLLM owns that conversion; its documented GPT-5 route avoids relying on arbitrary deployment names to infer model capabilities. Omit explicit temperature and reasoning-effort settings unless needed and verified; do not silently drop unsupported parameters.

Set the dated provider API version explicitly to the GA `2024-10-21` compatibility path rather than relying on a LiteLLM default. Keep systematization web search disabled; the lab needs no Responses-only or preview features. The exact deployed models must pass the same Chat Completions/token-options/structured-output smoke path at M1. If this path is rejected, the prerequisite is blocked: do not auto-switch providers or API versions. Microsoft's newer v1 API is documented, but switching to a generic OpenAI provider is not the selected path.

**Decision**: Review the starter taxonomy to exactly two categories, one with `permissible: true` and one with `permissible: false`. Generate both case types with native `sampling.method: stratified` and `stratify_by: [behavior]`.

The released sampler divides an evenly divisible sample count across behavior strata: 8 prompts assign 4 to each category; 4 scenarios assign 2 to each. This guarantees assignment counts, not semantic quality. The learner still reviews generated content and corrects errors before approval. Generation/provider failures must surface rather than being filled with fabricated cases.

**Corrected native path finding**: `file_path` is accepted by the shared loader but is not consumed as a stage input override. Do not use it to bind approved files. Consumed keys are `test_set.taxonomy_path`, `inference.test_set_path`, `judge.inference_set_path`, and `judge.taxonomy_path`; enabled stages also support their documented save paths/directories.

**Corrected native score finding**: Read judge outputs from `scores.jsonl`'s `verdict.dimensions`, not the top-level `dimensions` field, which contains test-generation factors. `test_case_id`, `type`, `behavior`, `judge_status`, and `judge_error` are row-level fields. Hard judge exceptions may omit a score row entirely; reconcile expected IDs against inference and score records rather than merely counting `judge_failed`.

**Additional sources**:

- [LiteLLM Azure/GPT-5 routing](https://docs.litellm.ai/docs/providers/azure#gpt-5-models).
- [Azure API lifecycle and v1 distinction](https://learn.microsoft.com/en-us/azure/foundry/openai/api-version-lifecycle) and [dated GA API reference](https://learn.microsoft.com/en-us/azure/foundry/openai/reference).
- [Released sampling implementation](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/assert_ai/stages/test_set.py).
- [Released stage configuration](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/assert_ai/config.py) and [judge artifact writer](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/assert_ai/stages/judge.py).

**Pinned sources**:

- [PyPI package](https://pypi.org/project/assert-ai/0.3.0/) and [release metadata](https://github.com/responsibleai/ASSERT/releases/tag/v0.3.0).
- [Package/entry point/dependencies](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/pyproject.toml).
- [Config schema](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/docs/config/schema.md).
- [CLI contract](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/docs/cli/commands.md).
- [Model config](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/assert_ai/core/config_model.py), [provider client](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/assert_ai/core/model_client.py), and [judge](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/assert_ai/core/judge.py).
- [Results guide](https://github.com/responsibleai/ASSERT/blob/04b713fe73879208369750b3bd5ad53544f3eecc/docs/guides/results.md).
