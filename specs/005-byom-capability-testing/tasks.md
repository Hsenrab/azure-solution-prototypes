# Tasks: BYOM Capability Testing - Resource Setup

**Input**: [spec.md](./spec.md), [plan.md](./plan.md),
[research.md](./research.md), [data-model.md](./data-model.md), and
[quickstart.md](./quickstart.md).

**Scope**: The approved provisioning-only slice. No service connections, models,
gateway routes, search indexes, BYOM functionality, or evaluations.

The original tasks/evidence below describe the first slice. The approved
2026-11-23 extension adds model hosting only; integrations remain deferred.

## Backend Extension Tasks

- [X] T009 [US1] Add `demos/byom01-capability-testing/infra/backend.bicep`: deterministic AIServices/S0 account and gpt-5.4 deployment in Sweden Central, current stable APIs, catalog-supplied version, GlobalStandard capacity 10, and backend outputs; reuse the ASSERT account/deployment pattern without its unrelated RBAC/project.
- [X] T010 [US1] Extend `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb`, `requirements.txt`, and `env/.env.example`: SDK catalog/quota selection, backend compilation/group/deployment, and generated backend fields after both deployments succeed.
- [X] T011 Update `demos/byom01-capability-testing/README.md`, `metadata.json`, `specs/005-byom-capability-testing/data-model.md`, and `quickstart.md` for scope, charges, two-group settings, and targeted backend cleanup using the unchanged canonical destroy notebook.
- [X] T012 Validate both templates and changed notebook locally; execute backend notebook steps live, verify SC-005/SC-006 and unchanged consumer inventory, then delete/purge only validation-created backend resources and verify SC-007. Record actual evidence in `specs/005-byom-capability-testing/tasks.md`.

Dependencies: T010 follows T009; T011 follows T010; T012 follows T010/T011.

Capacity follow-up approved on 2026-11-23: change backend Bicep and notebook
defaults to 100 units (100,000 TPM), and align current instructions/contracts.
The historical capacity-10 evidence below remains unchanged. No live deployment
at capacity 100 was requested in this follow-up.

### Backend Extension Evidence (2026-11-23)

- Built-in Bicep compilation passed for both templates with zero diagnostics.
  Notebook Python 3.10 syntax and unique IDs passed before hygiene formatting;
  unchanged destroy notebook matched the canonical source byte-for-byte.
- Targeted existing pre-commit hook stripped execution output/display-name
  metadata; its subsequent run passed. A redundant final Python syntax/hygiene
  check was interrupted and is not claimed as additional evidence.
- SC-005 **passed live**: the actual backend notebook steps deployed AIServices/S0
  in Sweden Central with GPT-5.4 version `2026-03-05`, GlobalStandard capacity 10,
  public access, disabled local authentication, and NoAutoUpgrade.
- SC-006 **passed live**: repeat deployment retained one account/model and identical
  outputs. Actual environment-write code produced all 25 contract fields in a
  temporary file; missing backend outputs failed without overwriting it.
  Existing consumer deployment outputs were read, not redeployed; its existing
  local environment file was not overwritten. No inference was performed.
- SC-007 **passed live**: deleted only the newly created backend group and purged
  its Foundry account. Group existence returned false and the targeted
  soft-deleted account query returned an empty list. Pre-existing consumer
  inventory matched before deployment and after cleanup.
- Backend infrastructure/model hosting is implemented in Bicep; notebook steps
  consume it using the SDK. No local workaround or catch-and-explain wrapper was
  added. Setup and destroy remain unchanged; cleanup targeting is documented.
- No validation-created resources remain. The pre-existing consumer resources
  remain. Gateway routes and connected-model registration are still deferred.
- No Spec Kit extension hooks are configured.

**Validation**: Use existing local checks; no new test framework or test suite.
Live Azure acceptance is authorized for the agreed resources and standard paid
SKUs. Clean up resources created for validation, including Foundry/APIM purges,
and verify cleanup. Preserve unrelated and pre-existing resources and report
anything remaining.

## Format: `[ID] [P?] [Story?] Description`

`[P]` identifies independent file work after its stated prerequisites.
`[US1]` maps to the spec's only user story. Paths are repository-relative.

## Phase 1: Setup

- [X] T001 Create the minimal demo layout under `demos/byom01-capability-testing/` from `demo-template/`, retaining the planned directories and `demos/byom01-capability-testing/docs/.gitkeep`; do not copy virtual environments, generated files, or configure/test placeholder notebooks.

## Phase 2: Foundational

- [X] T002 Add only `azure-identity`, `azure-mgmt-resource`, and `python-dotenv` to `demos/byom01-capability-testing/requirements.txt`, and copy the speech demo's CLI executable-path resolver into `demos/byom01-capability-testing/app/notebook_helpers.py`; keep authentication in notebook cells.

**Checkpoint**: The minimal layout and shared prerequisites are ready.

## Phase 3: User Story 1 - Prepare the Resource Foundation (P1, MVP)

**Goal**: Prepare the local environment, provision the three services and project,
save their identifiers/endpoints, and provide complete cleanup.

**Independent acceptance**: Follow the setup/deployment journey in
[quickstart.md](./quickstart.md). Verify the three requested services and one
project, automatic configuration, unchanged-input redeployment without duplicates,
and cleanup including Foundry/APIM purge. Live outcomes remain unverified until
executed.

- [X] T003 [P] [US1] Create `demos/byom01-capability-testing/infra/main.bicep` using the stable APIs in `specs/005-byom-capability-testing/research.md`: APIM `Standard` capacity 1, Foundry `AIServices`/`S0` with project management enabled and system-assigned account/project identities, and Search `standard` with one replica/partition; enable public authenticated endpoints, default to `uksouth`, derive deterministic globally unique service names from the resource-group ID/demo prefix, and output all resource names, IDs, and endpoints needed by the environment contract. Do not add models, integrations, cross-service RBAC, or policy-bypass tags.
- [X] T004 [P] [US1] Copy the speech source-of-truth setup notebook to `demos/byom01-capability-testing/notebooks/00_setup.ipynb`, changing only the demo kernel/continuation text as needed; preserve Step 1 environment/kernel creation, Step 2 Azure authentication and optional subscription selection, and Step 3 installation from the demo's requirements.
- [X] T005 [US1] Adapt the evaluation demo's deployment journey into small single-purpose steps in `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb`, using a literal `RESOURCE_GROUP` assignment compatible with standard cleanup; prefer `AZURE_SUBSCRIPTION_ID`, otherwise use the CLI subscription selected during setup, compile Bicep with captured CLI stderr, and create the group/deploy incrementally with `AzureCliCredential` and `ResourceManagementClient`. Await successful deployment before writing the complete contract in `specs/005-byom-capability-testing/data-model.md` to ignored `env/.env`, and document those fields in `demos/byom01-capability-testing/env/.env.example`. Apply the contract exactly: "Read required outputs directly; do not substitute blank strings or infer success from incomplete outputs." and "Endpoints must use HTTPS." Do not retrieve keys, silently switch subscriptions/regions/SKUs, or add fallback/catch-and-explain wrappers.
- [X] T006 [P] [US1] Copy `demos/speech01-foundry-speech/notebooks/X_destroy.ipynb` verbatim to `demos/byom01-capability-testing/notebooks/X_destroy.ipynb`; retain the standard confirmation flags and Cognitive Services purge flow without local modifications.
- [X] T007 [US1] Write `demos/byom01-capability-testing/README.md` and populate `demos/byom01-capability-testing/metadata.json` using the template's exact fields: explain provisioning-only scope, prerequisites, standard paid SKUs/costs, the three-notebook journey, and generated configuration. Document exact subscription selection and resource-group/Foundry-endpoint targeting before cleanup, including partial deployment without an environment file, and the separately executed `az apim deletedservice purge --subscription "<saved-subscription-id>" --location "<saved-location>" --service-name "<saved-apim-name>"` command after the unchanged destroy notebook.

**Checkpoint**: US1 implementation and its runnable acceptance instructions exist;
local validation follows. Live validation is authorized and requires cleanup.

## Phase 4: Validation and Completion

- [X] T008 Run Bicep compilation for `demos/byom01-capability-testing/infra/main.bicep`, parse Python code in the three notebooks and `demos/byom01-capability-testing/app/notebook_helpers.py` without executing Azure operations, and run the existing targeted pre-commit notebook checks. Verify speech setup order, verbatim destroy reuse, the 15-field environment contract, template metadata fields, ignored generated configuration, and absence of out-of-scope infrastructure. Fix directly related failures and record concise evidence in `specs/005-byom-capability-testing/tasks.md`; keep SC-001 through SC-004 explicitly not run until the live journey in `specs/005-byom-capability-testing/quickstart.md` is actually executed, including required cleanup.

### Validation Evidence (2026-11-20)

- Built-in Bicep compilation passed with zero diagnostics: exactly four ARM
  resources (Foundry account/project, APIM, Search), the requested SKUs and public
  network settings, and 15 string outputs; no out-of-scope infrastructure.
- Built-in Pylance execution parsed all three notebooks and the helper for
  Python 3.10 syntax without executing their Azure operations.
- Offline execution of the actual environment-write step produced exactly the
  15 example fields. A missing required output raised before writing a file.
  A mocked deployment failure propagated and cleared stale in-memory outputs.
  Temporary environment files were automatically removed.
- Earlier targeted pre-commit notebook checks passed. Setup matches the speech
  source after the permitted kernel-text substitution; destroy is byte-for-byte
  identical. Notebook outputs/counts/display-name metadata are absent.
- Template metadata fields match; generated environment and virtual environment
  paths are ignored. SDK imports, construction, and operation signatures passed
  using the demo-local environment, without requesting a token.
- Platform behavior is defined in Bicep; the notebook consumes it through the
  SDK. No local infrastructure workaround or catch-and-explain wrapper was added.
  Standard destroy remains unchanged, with the approved separate APIM purge
  command documented in the README.
- SC-001: **not run**. SC-002: **not run**. SC-003: **not run**.
  SC-004: **not run**. No live Azure provisioning, redeployment, or cleanup was
  executed; local checks do not prove these outcomes.
- No implementation extension hooks are configured.

## Dependencies and Execution Order

| Task | Prerequisites |
|---|---|
| T001 | None |
| T002 | T001 |
| T003 | T002 |
| T004 | T002 |
| T005 | T003, T004 |
| T006 | T002 |
| T007 | T005, T006 |
| T008 | T007 |

US1 is the only story and the complete MVP; it has no other story dependencies.
All US1 work starts after the foundational phase.

## Parallel Example: US1

After T002, T003 (Bicep), T004 (setup), and T006 (destroy copy) can proceed
independently in different files. Complete T003 and T004 before T005; complete
T005 and T006 before T007. No simultaneous edits to the same notebook.

## Implementation Strategy

Complete the single resource-setup MVP, then run local checks and report their
results separately from live Azure acceptance. Preserve Bicep-first platform
configuration, SDK-first deployment, and the standard notebook patterns.
Do not implement the later BYOM/Foundry IQ functionality or create Azure resources
as part of completing this authoring slice.

## Generation Checks

Eight tasks: one setup, one foundational, five US1, and one final validation task.
All use sequential IDs, checkboxes, exact paths, and phase-appropriate story
labels. Three independent US1 file tasks are marked `[P]`.
No before/after task-generation extension hooks are configured.
