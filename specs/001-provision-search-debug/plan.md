# Implementation Plan: Provision Search Debug Environment

**Feature ID**: `001-provision-search-debug` | **Date**: 2026-10-23
**Spec**: [Feature specification](./spec.md)
**Git branch**: `feat/litellm-foundry-claude`; no branch created or switched.
Spec Kit's reported `BRANCH` is the feature identifier, not the actual Git branch.

## Summary

Create one self-contained demo, `demos/search02-hybrid-pagination/`, with a new
demo-owned resource group, one Basic Search service, and service-scoped permissions
for the user who signs in during setup. The user approved `northeurope`, one replica,
one partition, public access without IP restrictions, and disabled key authentication.

Bicep owns all Azure resource creation and security settings, including the resource
group. The notebook compiles Bicep locally and submits a subscription-scope deployment
using the Python Azure management SDK. It exports non-secret outputs automatically.
An authenticated read-only SDK service-statistics call proves metadata connectivity;
no index, documents, search queries, or .NET example are created by Feature 1.

This document is a design, not authorization to provision or incur charges.
Implementation and separately approved live acceptance completed on 2026-10-23:
deployment, unchanged-input redeployment, metadata readiness, and whole-group cleanup.
Latest lifecycle is `deleted`; prior readiness is historical and export stale.
See [actual validation status](../../demos/search02-hybrid-pagination/README.md#validation-status).

## Technical Context

**Language/Version**: Python 3.11+ notebook environment; Bicep; PowerShell for local CLI commands.
**Primary Dependencies**: `azure-identity`, `azure-mgmt-resource`,
`azure-mgmt-resource-deployments`, `azure-search-documents`, `python-dotenv`, `ipykernel`.
Use the dedicated deployments package, as existing demos do. Resolve compatible
stable package versions during implementation (now pinned in the demo's requirements). Use `azure-search-documents` only for
metadata readiness; its version does not select either Feature 2 reproduction client's version.
**Storage**: Local generated environment and evidence files only; no Storage account.
**Testing**: Bicep compile/lint; static template/notebook checks; existing pre-commit
notebook hygiene; explicitly authorized live deployment/metadata/redeployment/cleanup checks.
**Target Platform**: Local VS Code notebooks with Azure CLI user login; Azure public cloud.
**Project Type**: Notebook-first Azure debugging demo, not an application or hosted API.
**Performance Goals**: No throughput/SLA target; this is a disposable single-unit
experiment. Do not set an unsupported provisioning-time acceptance threshold.
**Constraints**: No keys, credentials in artifacts, private networking, model
deployment, UI, index creation, synthetic-data ingestion, or search-query execution.
**Scale/Scope**: One resource group; one Basic service; two role assignments; zero indexes.
Feature 2 later supplies 6,158 synthetic records and both language clients.
**Paid Default**: Basic, one search unit in North Europe; stop rather than substitute
another tier or region if unavailable. Billing continues while the service exists.

## Constitution Check

*GATE: evaluated before research and again after design.*

| Gate | Before research | After design |
|------|-----------------|--------------|
| Existing instructions and Azure Demo Authoring govern this work | Pass | Pass: linked procedures retained |
| One lightweight demo; no production architecture | Pass | Pass: Search only, no supporting cloud services |
| Bicep defines platform behavior | Pass | Pass: subscription wrapper plus resource-group module |
| Canonical setup and destroy flow | Pass | Pass: minimal setup substitutions; destroy copied verbatim |
| Python SDK first; CLI only where required | Pass | Pass: SDK deployment and metadata readiness; CLI login, Bicep compilation, user-requested policy checks |
| Hypothesis and measurable acceptance | Pass | Pass: infrastructure readiness enables, but does not claim, reproduction |
| Existing workflow and metadata checks remain active | Pass | Pass: unchanged pre-commit/GitHub Actions |
| Significant decisions have user approval | Pass | Pass: public/keyless access, dedicated group, user identity, paid Basic/region |
| Feature boundaries preserved | Pass | Pass: Feature 2 owns index, data, and both search clients |

No constitutional exception is required. Basic is a user-approved paid choice, not
a claim that Free lacks vector search or Entra support.

## Project Structure

### Documentation (this feature)

```text
specs/001-provision-search-debug/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/
    environment-handoff.md
  checklists/
    requirements.md
```

Task generation and execution are complete; [tasks.md](./tasks.md) records actual
verified completion rather than design intent.

### Source Code (implemented)

```text
demos/search02-hybrid-pagination/
  README.md
  metadata.json
  requirements.txt
  app/
    notebook_helpers.py
  env/
    .env.example
  infra/
    main.bicep
    search.bicep
  notebooks/
    00_setup.ipynb
    01_deploy_infra.ipynb
    02_configure.ipynb
    03_test.ipynb
    X_destroy.ipynb
  docs/
    architecture-notes.md
  data/
  outputs/
  scripts/
    validate_local.py
```

**Structure Decision**: Start from the existing demo template. Empty standard folders
remain placeholders; do not fill them with premature feature code. The one helper
copies the canonical Azure CLI executable resolver, not a new deployment framework.
Generated ARM JSON is a compiler output, not another infrastructure source of truth.

## Phase 0 - Research Decisions

See [research](./research.md) for sources and alternatives.

- Stable Search ARM API: `2025-05-01`, advertised by the selected subscription.
- Resource-group API: `2022-09-01`, also advertised; role-assignment API: `2022-04-01`.
- Basic/one unit/North Europe is explicitly approved; actual provisioning succeeded
  during the acceptance run. This does not guarantee capacity for future runs.
- Use Search Service Contributor and Search Index Data Contributor at service scope.
- Bind SDK operations to the CLI user with `AzureCliCredential`, not an unrestricted
  credential chain that could silently select another cached or environment identity.
- Use the stable Python SDK's read-only `SearchIndexClient.get_service_statistics()`
  for the handoff check, with `AzureCliCredential` and the selected SDK's stable API.
- Microsoft.Search was `NotRegistered` during planning. It was later explicitly
  approved and registered for acceptance; it remains registered after group cleanup.
  Registration is not an automatic side effect of research or planning.

## Phase 1 - Deployment and Notebook Design

1. **Setup**: Copy the canonical speech setup notebook, changing only kernel name,
   continuation text, and demo dependencies. Preserve environment/kernel, Azure
   authentication/subscription selection, and dependency-installation order.
2. **Inputs and policy review**: Explicitly resolve the subscription, tenant, signed-in
   user, resource-group name, location, and deployment name. Prefer an explicit
   `AZURE_SUBSCRIPTION_ID` when supplied; otherwise confirm the CLI selection.
   Use CLI account context and signed-in-user lookup for the actual setup user;
   do not select the first subscription or switch identities.
   Perform the required read-only CLI policy review at subscription and intended
   target scope, including initiatives, parameters, effects, and exemptions.
   A future resource group's absence is not evidence of policy permission.
3. **Ownership boundary**: Choose a fixed demo group name such as
   `rg-search02-hybrid-pagination-ne`. On first use, an existing unrelated group is a
   conflict, not an invitation to adopt it. A demo ownership tag with stable value
   `demo=search02-hybrid-pagination` identifies legitimate redeployment. Reuse only a
   known demo-owned group; fail if ownership is missing or conflicts.
4. **Bicep structure**: `main.bicep` has subscription target scope and creates the
   resource group; `search.bicep` targets that group. Two files are required by the
   scope boundary, not by an abstraction framework. Service naming uses a stable
   subscription/group-derived suffix and valid Search naming rules.
   The Search module fixes public access, disabled local authentication, Basic,
   one replica and one partition. There are no notebook auth/network toggles.
   Do not enable a Search managed identity: no outbound resource access requires it.
5. **Access**: Create exactly two deterministic service-scoped role assignments,
   keyed by service resource ID, user object ID, and role definition ID, with
   principal type `User`. Do not create an index to scope a role assignment.
   Do not add Data Reader because Data Contributor already covers querying.
   Deployment requires resource-write and role-assignment privileges; lacking
   those privileges is a prerequisite failure, not grounds for using keys.
6. **Compile, preview, deploy**: Compile Bicep using the canonical resolver and CLI.
   Surface stdout/stderr for compiler failures following the authoring reference.
   Use the Python deployments SDK to validate/preview the subscription deployment
   and, only on explicit execution approval, apply it. The wrapper defines the group;
   notebook code does not separately create the group with another set of defaults.
7. **Handoff**: Wait for actual deployment completion; then consume its outputs and
   write the [environment contract](./contracts/environment-handoff.md) to `env/.env`.
   Never write keys/tokens or manufacture successful outputs after failure.
   A partial deployment can be cleaned up using the known group input even when
   environment output generation never completed.
8. **Configure**: Keep `02_configure.ipynb` as an explanatory handoff for Feature 2,
   with no index/configuration mutations. No success-shaped fake configuration step.
9. **Test readiness**: `03_test.ipynb` verifies deployed security/capacity settings,
   role-assignment targets, and calls `SearchIndexClient.get_service_statistics()`
   using the same user's `AzureCliCredential` for `https://search.azure.com/.default`.
   Require `statistics.counters.index_counter.usage` and
   `statistics.counters.document_counter.usage` to be zero using the selected stable
   SDK's supported model. Record the observation time and SDK/API versions. This verifies metadata
   access, not effective document upload/query execution. Record the latter as
   deferred to Feature 2. Let underlying failures surface; propagation delays are
   recorded as blocked/pending, not masked by retries or key fallbacks.
10. **Cleanup**: Copy the canonical speech destroy notebook verbatim. Before running
    its destructive steps, the operator must align the active CLI subscription with
    the generated subscription ID and review the exact group/resources. Its current
    CLI-context dependency is documented, not silently patched in this demo.
    Opening the notebook is not confirmation to execute it; explicitly review
    confirmation flags and run deletion steps only when approved.
    Verify the group is absent after deletion. Repeating cleanup may report the
    group's absence as a raw error in the canonical notebook; do not claim a new
    deletion or add a local fallback to change that behavior.
    Record the observed lifecycle state as `deleted` in cleanup evidence and the
    final README. Earlier readiness evidence is historical and the exported
    environment is stale, not a live Feature 2 handoff. Before Feature 2, rerun the
    approved deployment, output export, and readiness checks; do not automatically
    redeploy or leave paid resources running to preserve a handoff.

## Validation and Traceability

| Requirement area | Planned evidence |
|------------------|------------------|
| FR-001, FR-011 | Template structure, exact metadata keys, canonical notebook comparisons, pre-commit |
| FR-002, FR-003, FR-005 | Compiled Bicep: one group, one Basic Search service, no other billable resources |
| FR-004, FR-009 | Ownership check, explicit context, stable names, second deployment creates no duplicates |
| FR-006 | Public/keyless settings; two user-targeted service-scoped assignments; metadata access |
| FR-007, FR-008 | Required non-secret outputs and language-neutral environment contract |
| FR-010, FR-013 | Zero indexes/documents, no reproduction search requests; accurate readiness result |
| FR-012 | Reviewed canonical destroy steps, correct CLI context, group absence |
| FR-014, FR-015 | Explicit failures and current scoped CLI policy-review evidence |

Static checks must inspect compiled resource properties/counts and actual notebook
operations, not merely assert that files exist. Use existing tools; do not introduce
a testing framework just to validate this small demo.
Live checks required separate explicit execution approval and current prerequisites;
deployment, redeployment, metadata access, and whole-group cleanup all completed.
The [validation status](../../demos/search02-hybrid-pagination/README.md#validation-status)
records the deleted lifecycle and the canonical per-resource cleanup limitation.

## Complexity Tracking

No unjustified violations. Two Bicep files represent subscription/resource-group
scopes. No new cloud service, workflow framework, deployment abstraction, or local
infrastructure workaround is introduced.
