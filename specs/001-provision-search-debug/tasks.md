# Tasks: Provision Search Debug Environment

**Input**: [Specification](./spec.md), [plan](./plan.md),
[research](./research.md), [data model](./data-model.md),
[handoff contract](./contracts/environment-handoff.md), and
[validation guide](./quickstart.md).

**Scope**: Feature 1 only. This file schedules work; generating it performs none of
the implementation, registration, deployment, or deletion described below.

**Validation**: The specification explicitly requires static and live acceptance
checks. Use existing Bicep, Python, Azure CLI, and pre-commit tools; do not add a
test framework or require TDD. Store generated evidence locally under the ignored
`outputs/generated/` directory. Never include tokens, keys, or authorization headers.

**Organization**: Setup, shared prerequisites, three user stories, then final review.
All paths below are repository-relative. Checkboxes record actual verified completion.
Separately approved deployment, redeployment, metadata readiness, and whole-group
cleanup completed on 2026-10-23. Latest lifecycle: `deleted`; readiness is historical,
export stale, and Feature 2 unimplemented. The canonical per-resource cleanup
command's unsupported `--yes` warning is preserved in actual cleanup evidence;
whole-group deletion and two independent absence checks succeeded.

## Format: `[ID] [P?] [Story] Description`

- `[P]` means independent of other tasks in the same batch after its listed
  prerequisites have completed; it never removes those prerequisites.
- `[US1]`, `[US2]`, and `[US3]` map to the specification's user stories.
- Tasks editing the same file must run sequentially even if they serve different stories.
- A live task remains blocked/unchecked until the user approves the relevant Azure
  action and its actual acceptance evidence exists. Code implementation does not
  imply permission to create paid resources, register a provider, or delete a group.

## Path Conventions

Implementation belongs only under `demos/search02-hybrid-pagination/`.
The source notebooks/helpers remain under `demos/speech01-foundry-speech/`.
Do not alter unrelated dirty demos, repository workflows, or the canonical notebook
sources to implement this feature.

## Phase 1: Setup

**Purpose**: Create the minimal standard demo layout and canonical setup journey.

- [X] T001 Create `demos/search02-hybrid-pagination/` from `demo-template/`, retaining the planned standard folders and replacing copied scenario content only as later tasks require; create `demos/search02-hybrid-pagination/outputs/generated/` for local compiler/evidence output, with no index/data/client implementation.
- [X] T002 [P] Define the minimal Python 3.11+ dependencies in `demos/search02-hybrid-pagination/requirements.txt`: compatible stable `azure-identity`, `azure-mgmt-resource`, `azure-mgmt-resource-deployments`, `azure-search-documents`, `python-dotenv`, and `ipykernel`; use the Search SDK only for metadata readiness, not either Feature 2 reproduction client, and do not add a hand-written HTTP dependency, embedding package, .NET project, or test framework.
- [X] T003 [P] Copy the existing CLI executable resolver from `demos/speech01-foundry-speech/app/notebook_helpers.py` into `demos/search02-hybrid-pagination/app/notebook_helpers.py` without adding authentication, deployment, or error-reformatting abstractions.
- [X] T004 Copy `demos/speech01-foundry-speech/notebooks/00_setup.ipynb` into `demos/search02-hybrid-pagination/notebooks/00_setup.ipynb`, changing only the demo kernel name, continuation text, and dependency substitutions; retain the ordered environment/kernel, Azure authentication/subscription, and dependency-installation steps.

**Checkpoint**: A runnable local setup exists without Azure resource creation.

## Phase 2: Foundational Prerequisites

**Purpose**: Establish cleanup safety, the execution gates, and baseline metadata
before implementing or exercising the cloud journey.

- [X] T005 [P] Copy `demos/speech01-foundry-speech/notebooks/X_destroy.ipynb` verbatim to `demos/search02-hybrid-pagination/notebooks/X_destroy.ipynb`; do not execute it, alter its confirmation flags, or add a demo-local cleanup fallback.
- [X] T006 [P] Add prerequisites and execution gates to `demos/search02-hybrid-pagination/README.md`: explicit subscription/user context, scoped Azure CLI policy/initiative/exemption review, resource-write/role-assignment privileges, approved Basic 1/1 in `northeurope`, current cost/capacity review, explicit provider-registration approval, and CLI subscription/group review before running the canonical destroy steps; distinguish earlier read-only findings from current readiness.
- [X] T007 [P] Populate `demos/search02-hybrid-pagination/metadata.json` with exactly the `demo-template/metadata.json` schema keys, the customer pagination problem, infrastructure-readiness hypothesis, synthetic-data-only future scope, proposed status, and a clearly identified demo owner or explicitly documented unassigned ownership; do not claim the bug is reproduced.

**Checkpoint**: T004-T007 complete constitute foundation **F**. No user-story
implementation starts before F; live execution has additional approval gates.

## Phase 3: User Story 1 - Provision One Shared Debugging Environment (Priority: P1)

**Goal**: Deploy the approved service and permissions into a newly owned group,
without creating an index or running the customer scenario.

**Independent Test**: With explicit execution approval and prerequisites satisfied,
deploy once and repeat with unchanged inputs. Observe one owned group, one Basic
service, the same two user-targeted role assignments, explicit context, and no
unrelated resources or duplicate services/assignments. This does not require a UI,
Search query SDK, or Feature 2.

### Implementation

- [X] T008 [P] [US1] Implement `demos/search02-hybrid-pagination/infra/search.bicep` using Search API `2025-05-01`: `"sku | Basic"`, `"replicas / partitions | 1 / 1"`, `"disableLocalAuth | true"`, and `"ipRules | no allowlist"` from the data model; enable public access using schema-valid casing, use a `"Globally unique valid name with stable group/subscription suffix"`, and add exactly the service-scoped Search Service Contributor (`7ca78c08-252a-4471-8644-bb5ff32d4ba0`) and Search Index Data Contributor (`8ebe5a00-799e-43f5-93ac-243d3dce84a7`) assignments with API `2022-04-01`, principal type `User`, and GUIDs derived from service ID, user object ID, and role ID; no other cloud resources or managed identity.
- [X] T009 [US1] Implement subscription-scoped `demos/search02-hybrid-pagination/infra/main.bicep` with resource-group API `2022-09-01`, a new exclusively demo-owned group, and the scoped Search module; enforce `"location | northeurope, explicitly approved; no fallback region"`, `"demoId | search02-hybrid-pagination; stable ownership tag value"`, and `"ownershipTag | demo=search02-hybrid-pagination; conflict/missing ownership blocks adoption"`; expose all nine outputs in `contracts/environment-handoff.md` and keep subscription/tenant context scope-derived.
- [X] T010 [P] [US1] Implement the input/identity steps of `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb`: `"subscriptionId | Explicitly selected subscription UUID; never first enabled subscription"`, `"tenantId | Tenant of the signed-in setup user and selected subscription"`, `"operatorObjectId | Object ID of that user; service-principal/client IDs are not substitutes"`, and `"deploymentName | Stable name for subscription-scope deployment records"`; prefer an explicit `AZURE_SUBSCRIPTION_ID`, otherwise confirm CLI context, keep a literal `RESOURCE_GROUP = "rg-search02-hybrid-pagination-ne"` for canonical cleanup discovery, and use the same setup user through `AzureCliCredential` without alternate-identity fallbacks.
- [X] T011 [US1] Add predeployment ownership and validation/what-if steps to `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb` using the Python management/deployments SDKs: reject an existing unrelated or unowned group, permit only known demo-owned redeployment, require the scoped policy/provider/permission prerequisites documented in the README, and stop on validation/conflict without changing tier, region, authentication, networking, or policies.
- [X] T012 [US1] Add local Bicep compilation and explicitly executed subscription deployment to `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb`, writing generated ARM to `demos/search02-hybrid-pagination/outputs/generated/main.json`; follow the existing inline CLI stderr/stdout failure pattern, await actual deployment completion through `azure-mgmt-resource-deployments`, and retain real outputs/failures without SDK-created resource groups, catch-and-explain wrappers, automatic provider registration, or fallback paths.

### Validation

- [X] T013 [US1] Compile `demos/search02-hybrid-pagination/infra/main.bicep` and inspect both wrapper and nested module in `demos/search02-hybrid-pagination/outputs/generated/main.json`; record diagnostics and assertions for exactly one resource group, one Basic 1/1 Search service, two correctly scoped deterministic user assignments, the required nine outputs, approved public/keyless settings, stable names, and no index/model/Storage/network/UI resources or notebook infrastructure toggles in `demos/search02-hybrid-pagination/outputs/generated/us1-static-validation.json`.
- [X] T014 [US1] Only after explicit execution approval, complete the current policy/cost/capacity/permission review in `demos/search02-hybrid-pagination/README.md`, obtain separate registration approval if Microsoft.Search remains unregistered, and execute `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb`; record actual provisioning status, resource/assignment IDs, scope, and any blocked/failed prerequisite in `demos/search02-hybrid-pagination/outputs/generated/us1-deployment.json`, without creating an index, uploading data, or submitting search requests.
- [X] T015 [US1] With continued execution approval, repeat `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb` using the same inputs and compare actual group/service/assignment IDs and counts with the first deployment; record zero additional services/duplicate assignments and refreshed real outputs, or the underlying failure, in `demos/search02-hybrid-pagination/outputs/generated/us1-redeployment.json`.

**Checkpoint**: US1 is accepted only with actual deployment/redeployment evidence;
successful compilation alone is implementation progress, not live acceptance.

## Phase 4: User Story 2 - Hand Off Usable Configuration to Both Clients (Priority: P1)

**Goal**: Export a complete language-neutral handoff and establish authorized metadata
readiness as the same user, without implementing either search client.

**Independent Test**: Against a successfully provisioned environment, validate all
nine exported keys and consistent identifiers, actual settings and role targets,
then successfully call `SearchIndexClient.get_service_statistics()` as the same
CLI user and validate zero initial indexes/documents through the SDK model.
Document uploads, queries, and cross-language execution remain
deferred to Feature 2.

### Implementation

- [X] T016 [P] [US2] Document the exact nine keys from `specs/001-provision-search-debug/contracts/environment-handoff.md` in `demos/search02-hybrid-pagination/env/.env.example`, using harmless placeholders and stating `"searchEndpoint | HTTPS endpoint, no credentials/query string"` and `"operatorObjectId | Signed-in setup user's object ID"`; no keys, tokens, client secrets, connection strings, or invented index names.
- [X] T017 [US2] Implement the output-export steps in `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb` to require all nine nonempty, mutually consistent successful-deployment outputs and write `demos/search02-hybrid-pagination/env/.env` as a complete UTF-8 `KEY=value` mapping in one file write; never append duplicate values, manually author missing deployment values, export credentials, or treat stale files as proof of the latest deployment.
- [X] T018 [P] [US2] Replace copied scenario content in `demos/search02-hybrid-pagination/notebooks/02_configure.ipynb` with an explanatory handoff to Feature 2, explicitly deferring index creation, synthetic data, Python/.NET search clients, count measurements, and distance sorting; no mutation cells or fake-success configuration step.
- [X] T019 [US2] Implement small readiness cells in `demos/search02-hybrid-pagination/notebooks/03_test.ipynb` to read the generated environment, verify `"resourceGroupId | Belongs to selected subscription and is exclusively demo-owned"` and `"searchResourceId | Child of the expected resource group"`, compare live security/capacity settings and both Bicep-owned assignment targets, then call stable `SearchIndexClient.get_service_statistics()` with the same user's `AzureCliCredential` for `https://search.azure.com/.default` and the selected SDK's supported stable API; require SDK success and exact zero `statistics.counters.index_counter.usage` and `statistics.counters.document_counter.usage` through its supported model, with no hand-written HTTP handling, queries, uploads, added retry loops, missing-counter defaults, or identity/key fallbacks.

### Validation

- [X] T020 [US2] Validate the exporter and readiness code in `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb` and `demos/search02-hybrid-pagination/notebooks/03_test.ipynb` locally with disposable synthetic deployment outputs and statistics models matching the selected stable SDK: cover all nine correct keys, missing/empty/mismatched outputs, stale-output nonacceptance, wrong identity/scope, SDK exceptions, and absent/nonzero model counters; keep validation outside notebook happy-path cells and record results in `demos/search02-hybrid-pagination/outputs/generated/us2-local-validation.json` without adding a framework or live writes.
- [X] T021 [US2] After the approved deployment/redeployment and local checks, execute the output-export/readiness steps in `demos/search02-hybrid-pagination/notebooks/01_deploy_infra.ipynb` and `demos/search02-hybrid-pagination/notebooks/03_test.ipynb`; record actual IDs/settings, policy review scope/time, metadata status, role targets, SDK/API versions, UTC observation time `observedAt`, and model counters in `demos/search02-hybrid-pagination/outputs/generated/readiness.json` using the data-model statuses `ready`, `blocked`, or `failed` and document-operation status `deferred-to-feature-2`; preserve underlying failures and do not claim readiness or reproduction while blocked.

**Checkpoint**: US2 accepts a usable infrastructure handoff, not proven document
operations or the customer's pagination symptom. Do not delete later Feature 2
data to force this initial zero-index acceptance condition.

## Phase 5: User Story 3 - Remove the Disposable Environment Safely (Priority: P2)

**Goal**: Use the canonical cleanup journey within the approved whole-group boundary.

**Independent Test**: Review the exact subscription/group/resources, explicitly
approve deletion, execute canonical cleanup, and verify the owned group is absent.
Opening the notebook causes zero deletion; resources outside the group are not
deletion targets. A repeat cleanup reports actual absence, not a new deletion.

### Implementation and Validation

- [X] T022 [P] [US3] Document cleanup ownership, partial-deployment recovery, generated subscription/group values, explicit CLI subscription alignment, review of current confirmation flags, and the prohibition on unattended Run All in `demos/search02-hybrid-pagination/docs/architecture-notes.md`; explain that verified cleanup leaves lifecycle state `deleted`, makes earlier readiness historical and the export stale, and requires a separately approved deployment/export/readiness rerun before Feature 2, never automatic reprovisioning or implicitly retained paid resources; explain that the canonical destroy notebook may report an already-missing group as an error, and do not implement a local fallback or source-notebook rewrite.
- [X] T023 [P] [US3] Verify byte-for-byte equality of `demos/search02-hybrid-pagination/notebooks/X_destroy.ipynb` with `demos/speech01-foundry-speech/notebooks/X_destroy.ipynb`, inspect that merely opening it executes no deletion, and validate the setup notebook's permitted substitutions/step order; record static cleanup/setup checks in `demos/search02-hybrid-pagination/outputs/generated/us3-static-validation.json` without executing destructive cells.
- [X] T024 [US3] Only after separate explicit deletion approval and preservation of prior deployment/readiness evidence, align CLI context, review the actual owned group/resources, and execute `demos/search02-hybrid-pagination/notebooks/X_destroy.ipynb`; independently verify group absence with an explicitly scoped Azure CLI check, confirm no outside-scope deletion targets, and record actual cleanup/partial-failure/already-absent state with `lifecycleState` and UTC `observedAt` in `demos/search02-hybrid-pagination/outputs/generated/us3-cleanup.json`, using `deleted` only after verified absence; preserve earlier readiness as historical, mark the export stale in the evidence, and do not alter the canonical notebook or automatically redeploy.

**Checkpoint**: Code and instructions alone do not complete live cleanup acceptance.
If deletion is not approved, retain this task as blocked and disclose continuing cost.

## Phase 6: Polish and Cross-Cutting Review

- [X] T025 [P] Finish `demos/search02-hybrid-pagination/README.md` with the exact notebook journey, generated handoff keys, paid Basic/region choice and continuously accruing costs, prerequisite/policy guidance, current validation evidence, limitations, and explicit Feature 2 boundary; link the architecture notes and reuse skill references rather than duplicate their procedures.
- [X] T026 [P] Reconcile `demos/search02-hybrid-pagination/metadata.json` with the final implementation and evidence, preserving the exact template schema and accurate proposed/validated status, setup estimate, ownership, security notes, and last-updated date; describe infrastructure readiness without claiming a reproduced bug or completed Python/.NET comparison.
- [X] T027 Run the focused existing pre-commit notebook checks and final compiled-template/notebook-content checks for `demos/search02-hybrid-pagination/`, reverify canonical destroy equality after metadata processing, and record results in `demos/search02-hybrid-pagination/outputs/generated/final-static-validation.json`; preserve existing `.github/workflows/notebook-metadata-check.yml` and `.pre-commit-config.yaml`, and fix tightly coupled failures without unrelated cleanup.
- [X] T028 Review evidence against FR-001 through FR-015 and SC-001 through SC-007 from `specs/001-provision-search-debug/spec.md`, reconcile actual passed/blocked/not-run outcomes in `demos/search02-hybrid-pagination/README.md`, and update completion states in `specs/001-provision-search-debug/tasks.md` only when each task's evidence exists; state the Bicep/shared/local change scope, remaining constraints, latest observed lifecycle state/cost, and that Feature 2 is still unimplemented; after verified cleanup explicitly report `deleted`, historical readiness, and a stale export, requiring separately approved deployment/export/readiness before Feature 2 rather than claiming a live handoff.

## Dependencies and Execution Order

**F** means completion of T004, T005, T006, and T007, including their dependencies.
The table records actual prerequisites rather than assuming list order.
Azure execution/deletion approval is an additional external gate, not a task ID.

| Task | Prerequisites |
|------|---------------|
| T001 | None |
| T002 | T001 |
| T003 | T001 |
| T004 | T002, T003 |
| T005 | T001 |
| T006 | T001 |
| T007 | T001 |
| T008 | F |
| T009 | T008 |
| T010 | F |
| T011 | T009, T010 |
| T012 | T011 |
| T013 | T009, T012 |
| T014 | T013; current prerequisites and explicit execution approval |
| T015 | T014; continued execution approval |
| T016 | T009 |
| T017 | T012, T016 |
| T018 | F |
| T019 | T009, T017 |
| T020 | T004, T005, T018, T019 |
| T021 | T015, T020 |
| T022 | F |
| T023 | F |
| T024 | T015, T021, T022, T023; explicit deletion approval |
| T025 | T006, T012, T017, T018, T019, T022 |
| T026 | T007, T019, T022 |
| T027 | T013, T020, T023, T025, T026 |
| T028 | T015, T021, T024, T027 |

### Story Completion Graph

```text
Setup -> Foundation F -> US1: provision and repeat
                     -> US2: handoff implementation --+
                     -> US3: cleanup preparation -----|---+
US1 live acceptance -> US2 live readiness ------------+   |
US1 + US2 evidence + US3 preparation -> US3 approved cleanup
All story acceptance + final static checks -> completion review
```

US2 implementation and US3 preparation can start when their individual prerequisites
are met; their live tests require the environment supplied by US1. They do not
require Feature 2 or a populated index.

## Parallel Execution Examples

### Shared Setup

After T001, T002 (requirements), T003 (helper), T005 (canonical cleanup copy),
T006 (README gates), and T007 (metadata) use distinct files and may run together.
T004 waits for T002 and T003.

### User Story 1

After F, run T008 (`infra/search.bicep`) alongside T010 (initial
`notebooks/01_deploy_infra.ipynb` input/identity cells). T009 then consumes T008's
module interface. T011/T012 must serialize edits to the deployment notebook.

### User Story 2

Once T009 and F are complete, T016 (`env/.env.example`) and T018
(`notebooks/02_configure.ipynb`) can run together. T017 waits for T012 and T016.
Do not parallelize T017 with any other edit to the deployment notebook.

### User Story 3

After F, T022 (`docs/architecture-notes.md`) and T023 (read-only canonical-copy
checks with a separate evidence file) can run alongside each other and US1 work.
T024 cannot run concurrently with deployment, readiness, or evidence capture.

## Implementation Strategy

### MVP First

Complete shared setup/safety foundations and US1 implementation/static checks first.
This is the infrastructure MVP; deployment remains an explicit approval checkpoint.
The canonical cleanup copy and basic safety instructions are already present before
the first paid deployment, even if US3's full acceptance is not yet exercised.

### Incremental Delivery

1. Implement and locally validate US1; do not deploy automatically.
2. Prefer finishing US2 handoff and US3 cleanup preparation before requesting paid
   execution, reducing the time a service waits idle.
3. On explicit approval, recheck live prerequisites, deploy/redeploy, and exercise
   US2 readiness against the same environment.
4. Preserve evidence, then obtain separate cleanup approval and validate deletion.
5. Run final local gates and reconcile all task states. If live execution or cleanup
   is withheld/blocked, report that limitation; do not mark the feature fully accepted.

## Requirement and Acceptance Coverage

| Requirements / criteria | Tasks |
|-------------------------|-------|
| FR-001, FR-011 | T001-T007, T018, T023, T025-T027 |
| FR-002, FR-003, FR-005; SC-001 | T008, T009, T012-T014 |
| FR-004, FR-009; SC-002 | T009-T015 |
| FR-006; SC-004 | T008, T010, T019-T021 |
| FR-007, FR-008; SC-003 | T009, T016, T017, T020, T021 |
| FR-010, FR-013; SC-006 | T001, T013, T018-T021, T028 |
| FR-012; SC-005 | T005, T006, T022-T024 |
| FR-014, FR-015; SC-007 | T006, T010-T014, T019-T021, T028 |

## Notes

No task implements a Search index, dummy corpus, reproduction query, .NET client,
beta-SDK comparison, distance sorting, production advice, or a release timeline.
Do not weaken errors or fabricate readiness to satisfy acceptance.
Task order is a dependency guide, not a request to switch Git branches or create commits.
