# Implementation Plan: BYOM Capability Testing - Resource Setup

**Branch**: `005-byom-capability-testing` | **Date**: 2026-11-19 | **Spec**: [spec.md](./spec.md)

**Input**: Approved provisioning-only scope and public-endpoint clarification.

The original plan below records the first slice. The following extension plan
supersedes its one-group/no-model limits; original validation evidence is retained.

## Backend Extension Plan (2026-11-23)

Use a second resource-group-scoped template and small additional deployment
notebook steps, not a subscription-wide rewrite. Default backend group:
`rg-byom01-backend-swc`; location: `swedencentral`. No backend project, cross-service
RBAC, gateway routes, or connected-model registration in this slice.

| Source | Decision | Reason |
|---|---|---|
| `demos/byom01-capability-testing/infra/main.bicep` | Reuse unchanged | Preserve current consumer resources and UK South location |
| `demos/assert01-foundry-evaluation/infra/main.bicep` | Adapt account/deployment pattern into `demos/byom01-capability-testing/infra/backend.bicep` | Current AIServices account and account-level OpenAI deployment; omit unrelated project/RBAC and preserve BYOM auth defaults |
| `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb` | Adapt | Add backend catalog/quota, compilation, group/deployment, and environment output steps using the existing SDK journey |
| `demos/byom01-capability-testing/requirements.txt` | Adapt | Add Cognitive Services management SDK for catalog/quota discovery |
| `demos/byom01-capability-testing/notebooks/00_setup.ipynb`, `notebooks/X_destroy.ipynb`, `app/notebook_helpers.py` | Reuse unchanged | Preserve canonical flows and unrelated local edits |
| BYOM README, metadata, environment example; existing spec/contract/validation guide | Adapt | Describe two groups, model charges, generated backend fields, and targeted cleanup |

Model research: live Sweden Central catalog lists generally available `gpt-5.4`,
default version `2026-03-05`, supporting GlobalStandard. Subscription quota has
890 units available at discovery. Use 100 units (100,000 TPM), as approved in the
capacity follow-up; the original live validation used 10 units.
resolve the version and recheck quota in the notebook before creating resources.
GlobalStandard may process outside Sweden; this is not a Sweden-only residency claim.
Stable Bicep schemas for account/deployment are `2026-09-01`. AVM discovery found
an account module using older `2025-06-01` types; retain the repository's current
raw-resource pattern instead of changing deployment tooling for this small delta.

Live policy review confirms the consumer already has `disableLocalAuth: true`.
Define that same behavior explicitly for the new backend in Bicep; do not rely on
tenant Modify policy to patch an omitted property. Existing consumer Bicep is
unchanged under the approved scope.

Validation: compile both templates, parse notebook code, run targeted notebook
hygiene, exercise generated output/failure behavior, then execute actual backend
notebook steps in the selected subscription. Verify model properties and
idempotency. Reuse existing consumer deployment outputs for the environment-write
check without redeploying existing services; preserve the existing local environment
file during validation. Delete/purge only the newly created backend and verify both
cleanup and the unchanged consumer inventory. No inference/RBAC changes are needed
to prove this provisioning slice. No new test framework or production hardening.

Constitution check: approved two-group extension, self-contained Bicep-first
platform definitions, SDK-first consumers, explicit subscription, unchanged public
authentication patterns, no fallbacks/catch wrappers, canonical setup/destroy
unchanged, docs/metadata aligned, and existing notebook hygiene preserved.

## Summary

Create `demos/byom01-capability-testing/` with setup, deployment, and cleanup
notebooks. Reuse the evaluation demo's configuration/deployment/output journey,
replace its classic OpenAI infrastructure with a current Foundry account/project,
and provision APIM Standard plus Foundry IQ (Azure AI Search) Standard.
Do not connect the services or deploy models.

Use one resource-group-scoped Bicep file. Compile it locally with Azure CLI and
submit the resulting ARM template through the Python resource-management SDK.
Generate `env/.env` only after deployment succeeds. Preserve the speech demo's
setup and destroy standards; document the approved APIM purge command separately.

## Technical Context

**Language/Version**: Python >=3.10, matching the setup notebook; Bicep.

**Primary Dependencies**: `azure-identity`, `azure-mgmt-resource`,
`python-dotenv`; setup installs `ipykernel`. Azure CLI with a Bicep compiler that
recognizes the selected stable APIs. No inference, evaluation, or search SDK yet.

**Storage**: Generated, ignored `env/.env`; no datasets or application storage.

**Testing**: Bicep compilation, Python syntax checks for notebook code, existing
targeted pre-commit notebook cleanup, and the manual acceptance journey in
[quickstart.md](./quickstart.md). No new test framework.

**Target Platform**: VS Code/Jupyter on Windows; Azure public cloud.

**Project Type**: Self-contained notebook prototype, not an application scaffold.

**Performance Goals**: None for this resource-only slice. Await actual deployment
completion; do not promise a fixed APIM provisioning duration.

**Constraints**: Standard paid SKUs, public authenticated endpoints, no private
networking, models, gateway routes, search content, or service connections.
Do not copy the evaluation demo's policy-exemption-style tags or key retrieval.

**Scale/Scope**: One resource group, three services, one Foundry project.
Default location `uksouth`, matching the evaluation demo; editable before
deployment, with no automatic region/SKU fallback.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
|---|---|---|
| Authoring and Foundry guidance | Pass: loaded relevant skills/references | Pass: current Foundry pattern and stable APIs |
| One hypothesis, self-contained, minimal | Pass: provisioning-only spec | Pass: three notebooks; no app runtime or extra services |
| Bicep first; SDK consumers | Pass: platform settings belong in Bicep | Pass: SDK deploys compiled template, no infrastructure patches |
| Setup/destroy source of truth | Pass: speech notebooks required | Pass: minimal setup substitutions; destroy copied verbatim |
| Documentation and metadata | Pass: template shape retained | Pass: README, exact metadata fields, environment contract |
| Existing quality gates | Pass: no workflow changes | Pass: targeted pre-commit plus scenario acceptance |

The user approved omitting configure/test placeholder notebooks for this initial
slice and a separate APIM purge command after the unchanged destroy notebook.
No other exceptions or temporary workarounds are planned.

## Project Structure

### Documentation (this feature)

```text
specs/005-byom-capability-testing/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  checklists/requirements.md
```

### Source Code (repository root)

```text
demos/byom01-capability-testing/
  README.md
  metadata.json
  requirements.txt
  app/notebook_helpers.py
  infra/main.bicep
  env/.env.example
  docs/.gitkeep
  notebooks/00_setup.ipynb
  notebooks/01_deploy_infra.ipynb
  notebooks/X_destroy.ipynb
```

**Structure Decision**: Start from the demo template's shape but retain only
needed content. `app/notebook_helpers.py` supplies the existing CLI path resolver
required by setup; it is not an application. The local environment contract is
in [data-model.md](./data-model.md); there is no external API to justify a
separate contracts directory. Tasks are generated by `/speckit-tasks`, not here.

## Implementation Approach

1. **Infrastructure**: Use the resource types, versions, and tiers in
   [research.md](./research.md). Set Foundry `kind: AIServices`,
   `allowProjectManagement: true`, a custom subdomain, and system-assigned account
   and project identities. Public access is enabled in Bicep. Retain authenticated
   service defaults; do not add cross-service RBAC or change to identity-only
   data-plane access in this slice.
2. **Names and outputs**: Derive globally unique service names deterministically
   from the resource-group ID and demo prefix in Bicep. Return names, IDs, location,
   account/project endpoints, APIM gateway URL, and search endpoint. No secrets.
3. **Setup**: Copy speech setup; substitute only its demo kernel text and
   continuation text as needed. Copy its CLI resolver. Preserve the environment,
   authentication/subscription, dependency-installation sequence.
4. **Deployment**: Adapt the evaluation notebook into small configuration,
   subscription/authentication, Bicep compilation, resource-group creation,
   deployment, environment-write, and summary steps. Prefer
   `AZURE_SUBSCRIPTION_ID`; otherwise use the CLI subscription explicitly selected
   during setup. Use `AzureCliCredential` with `ResourceManagementClient` so
   deployment consumes that login. Compile with `az bicep build --stdout`, capture
   stderr, then submit an incremental deployment and await its result. Surface
   SDK failures directly. Do not retrieve keys or add catch-and-explain wrappers.
5. **Configuration and cleanup**: Write the contract only after successful
   deployment. Use the literal `RESOURCE_GROUP` configuration naming expected by
   the copied destroy notebook. Document selecting the exact subscription before
   cleanup, and supplying the exact Foundry account endpoint before cleanup after
   a partial deployment, rather than allowing the notebook's untargeted purge
   path. Keep the destroy notebook verbatim. After it finishes, run the approved
   APIM purge command using the saved service name, region, and subscription.
6. **Docs and validation**: Explain costs, prerequisites, the three-notebook
   journey, and the lack of BYOM/Foundry IQ integration. Use the template metadata
   fields exactly. Perform local checks, then report live acceptance separately
   as not run until executed. Live validation is authorized for the agreed
   resources and standard paid SKUs; clean up resources created for validation,
   including Foundry/APIM purges, and verify cleanup. Preserve unrelated and
   pre-existing resources and explicitly report anything remaining.

## Planning Outcome

Stable resource schemas and reuse patterns were checked; no unresolved design
questions remain. No extension hooks are configured. This phase produces design
documents only: no demo implementation, Azure deployment, or cleanup was executed.
