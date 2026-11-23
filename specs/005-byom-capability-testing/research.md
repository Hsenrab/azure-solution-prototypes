# Research: BYOM Resource Setup

Checked on 2026-11-19 using the Bicep stable-schema catalog and Microsoft Learn.
Schemas establish valid resource shapes, not capacity or policy approval in a
particular subscription.

## Resource Selection

| Resource | Stable API | Tier/capacity |
|---|---|---|
| `Microsoft.ApiManagement/service` | `2024-05-01` | `Standard`, capacity 1 |
| `Microsoft.CognitiveServices/accounts` | `2026-09-01` | `S0`, kind `AIServices` |
| `Microsoft.CognitiveServices/accounts/projects` | `2026-09-01` | Child project; no independent SKU |
| `Microsoft.Search/searchServices` | `2026-11-01` | `standard` (S1), one replica and partition |

**Decision**: Use these stable versions and standard paid tiers, with UK South as
the editable default location.
**Rationale**: Matches the approved scope and evaluation demo location. Foundry
supports projects in UK South. One search unit is sufficient for an empty
prototype; no production availability target was requested.
**Alternatives ruled out**: Developer/Free/Basic conflict with the requested
standard tiers. APIM StandardV2 is a separate tier choice with no required benefit
for this unconnected slice. Premium, multiple replicas, private networking, and
agent capability hosts add unrequested scope.

References: [APIM schema](https://learn.microsoft.com/azure/templates/microsoft.apimanagement/2024-05-01/service),
[Foundry account schema](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/2026-09-01/accounts),
[project schema](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/2026-09-01/accounts/projects),
[search schema](https://learn.microsoft.com/azure/templates/microsoft.search/2026-11-01/searchservices),
[Foundry regions](https://learn.microsoft.com/azure/foundry/reference/region-support),
[search tiers](https://learn.microsoft.com/azure/search/search-sku-tier).

## Foundry and Deployment Flow

**Decision**: Create an AIServices account with project management enabled and a
child project. Export its project endpoint; do not use a classic OpenAI account or
hub. Current documentation calls the search service Foundry IQ (Azure AI Search);
its ARM resource type remains `Microsoft.Search/searchServices`.

**Decision**: Use the Python resource-management SDK for deployment and Azure CLI
only for Bicep compilation and the existing setup/cleanup flows.
**Rationale**: Retains the evaluation notebook's learning journey while following
the repository's SDK-first rule. Bicep defines all platform behavior. Reuse the
setup CLI login through `AzureCliCredential`, not a new authentication flow.
**Alternatives ruled out**: CLI-only deployment duplicates SDK-supported
operations; azd scaffolding adds tooling and infrastructure not needed here.

References: [Foundry Bicep setup](https://learn.microsoft.com/azure/foundry/how-to/create-resource-template),
[Python ARM deployment](https://learn.microsoft.com/azure/azure-resource-manager/templates/deploy-python).
Repository prior art: [evaluation deployment](../../demos/evalgw02-aoai-apim-eval/notebooks/01_deploy_infra.ipynb),
[speech setup](../../demos/speech01-foundry-speech/notebooks/00_setup.ipynb),
[CLI resolver](../../demos/speech01-foundry-speech/app/notebook_helpers.py).

## Cleanup

**Decision**: Copy the speech destroy notebook unchanged and document a targeted
APIM purge command afterward, as explicitly approved during planning.
**Rationale**: The notebook purges Cognitive Services accounts, not APIM.
APIM soft-delete applies across tiers and reserves its name for 48 hours unless
purged. Passing the saved account endpoint and selecting the correct subscription
also keeps the copied cleanup flow targeted; partial-deployment recovery belongs
in README instructions, not new notebook fallback branches.
**Alternative ruled out**: Editing the shared destroy source affects other demos
and expands this task. Silently waiting 48 hours fails the requested purge outcome.

References: [speech destroy](../../demos/speech01-foundry-speech/notebooks/X_destroy.ipynb),
[APIM soft-delete](https://learn.microsoft.com/azure/api-management/soft-delete),
[APIM purge command](https://learn.microsoft.com/cli/azure/apim/deletedservice#az-apim-deletedservice-purge).
