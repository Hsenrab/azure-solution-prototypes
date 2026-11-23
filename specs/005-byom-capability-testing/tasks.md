# Tasks: BYOM Capability Testing - Resource Setup

**Input**: [spec.md](./spec.md), [plan.md](./plan.md),
[research.md](./research.md), [data-model.md](./data-model.md), and
[quickstart.md](./quickstart.md).

**Scope**: The approved provisioning-only slice. No service connections, models,
gateway routes, search indexes, BYOM functionality, or evaluations.

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
