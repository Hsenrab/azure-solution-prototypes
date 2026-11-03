# Tasks: Vector-Only Hybrid Contributions

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [interface contract](./contracts/experiment.md), and [quickstart.md](./quickstart.md).
**Created**: 2026-11-02
**Branch**: `feat/search-hybrid-pagination-infra` (unchanged).

**Organization**: Setup, shared foundations, then user stories in specification order: US1 (P1), US2 (P1), US3 (P2), followed by cross-cutting validation and separately approved live acceptance.

**Tests**: The specification explicitly requires reproducibility, membership, isolation, and incomplete-evidence checks. Extend the existing local validator and use focused runtime/CLI checks; do not introduce a test framework, dependency, generic fixture platform, or new .NET test project. Writing checks first does not authorize Azure execution.

## Format and Path Conventions

- Every task uses `- [ ] Tnnn [P?] [USn?] Description with exact file paths`.
- `[P]` means work can overlap another identified task on different files **after its listed prerequisites pass**; it is not permission to bypass prerequisites.
- All paths below are repository-relative Windows paths. Generated artifacts remain under existing exclusions; baseline integrity records belong in this session's `files` directory, not committed source.
- Use the existing [Copilot guidance](../../.github/copilot-instructions.md), [authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md), and [constitution](../../.specify/memory/constitution.md). Setup/destroy notebooks, infrastructure, SDK/API pins, authentication, and original experimental inputs remain unchanged.
- Offline implementation is approved. T029 separately gates live preparation and measurement; implementation approval does not grant live execution approval.

## Phase 1: Setup

**Purpose**: Establish the original baseline and protection boundaries before modifying shared consumers.

- [x] T001 Record an offline preservation snapshot of `demos\search02-hybrid-pagination\outputs\generated\reproduction\fixture`, existing `runs` and `preview-runs`, original `notebooks\00_setup.ipynb` through `05_compare_preview.ipynb`, `notebooks\X_destroy.ipynb`, `requirements.txt`, `requirements-preview.txt`, `app\dotnet\HybridPagination.csproj`, and `app\dotnet\packages.lock.json`; store exact existing-file hashes and the starting validator outcome in this session's `files` directory. Do not clear original notebook metadata, change dependencies, read credentials into the snapshot, or make Azure calls.

**Checkpoint**: Existing evidence and protected sources are identifiable; pre-existing failures are distinguishable from regressions.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Separate fixture identity, total index membership, and expected query membership before implementing story-specific consumers.

- [x] T002 [P] Add minimal fixed-version expectation/schema helpers in `demos\search02-hybrid-pagination\app\fixture.py`: support only versions 1 and 2, preserve all original public defaults and version-1 schema/bytes, resolve version 2 only to `hybrid-pagination-mixed-v2`, and expose separate total IDs/count, keyword IDs/count, and optional expected vector IDs. Use the exact ranges `doc-000001` to `doc-006133` (`keywordOnly`), `doc-006134` to `doc-006158` (`shared`), and `doc-006159` to `doc-006183` (`vectorOnly`); the schema changes only its name. Do not add a generic registry or make vectors retrievable.
- [x] T003 [P] Introduce the equivalent fixed version/expectation model independently in `demos\search02-hybrid-pagination\app\dotnet\Program.cs`, preserving version-1 behavior while separating indexed count 6,183, keyword count 6,158, and vector candidate count 50 for version 2; reject unsupported versions and arbitrary index targets without calling Python or adding packages.

**Checkpoint**: Both clients have compatible fixed expectations without equating every indexed ID with a keyword match. No live preparation is permitted.

## Phase 3: User Story 1 - Observe Additional Vector Results (Priority: P1)

**Goal**: Produce the mixed fixture and make both independent clients plus existing preview scenarios measure actual keyword, vector, and hybrid membership.

**Independent Test**: Locally generate two identical fixtures and exercise both validators. Once separately authorized and prepared, either stable client can demonstrate the three query cases without the new presentation layer. Full story acceptance still requires both clients' controls, the required hybrid cases, and the expanded-preview target.

### Checks and implementation

- [x] T004 [US1] Add focused mixed-fixture checks to `demos\search02-hybrid-pagination\scripts\validate_local.py` for deterministic double generation, disjoint/complete 6,133/25/25 membership, the exact 50 selected vector IDs, a separated cosine cutoff, exclusion of the `maths` token from vector-only text, and original version-1 identity. Include rejection of altered vectors/content, bad memberships/counts/hashes, unsupported versions, and a substituted original index; observe the missing mixed-generator/loader checks fail before their implementation, using temporary local directories only.
- [x] T005 [US1] Extend deterministic generation and the existing parser in `demos\search02-hybrid-pagination\app\fixture.py` with `--fixture-version` choices `1` and `2`, default `1`, preserving existing options and version-1 bytes. Implement version-2 content and vectors exactly as `data-model.md`: shared `[100, r, 0, ..., 0]` with `r = ordinal - 6108`, vector-only with `r = ordinal - 6158`, 16 components, original keyword-only SHA-256 vectors/content, the four specified non-keyword topics, and deterministic `lesson` repetition. Retain "ascending, unique, and zero-padded" IDs, "integer-valued floats", "compact UTF-8 JSONL, terminal LF, and key order `id`, `content`, `vector`"; refuse differing existing fixture bytes and the original fixture destination.
- [x] T006 [US1] Extend strict manifest/corpus loading in `demos\search02-hybrid-pagination\app\fixture.py`: enforce `fixtureVersion` "`2`; only versions 1 and 2 are supported", `recordCount` "`6183`", `indexName` "`hybrid-pagination-mixed-v2`; never arbitrary input", `keywordMatchCount` "`6158`; must equal the expected keyword ID-set cardinality", and `membership` "Exact ascending ID arrays for `keywordOnly`, `shared`, and `vectorOnly`". Validate the exact generator rules, corpus bytes/hash, canonical schema hash, `corpusPath` `corpus.jsonl`, keyword `maths`, existing query vector, `vectorDimensions`/`similarityMetric` `16`/`cosine`, `candidateCount`/`pageSize` `50`/`5`, and `serviceApi` `2025-09-01`; reject malformed input before mutation and do not add fields to version-1 manifests.
- [x] T007 [P] [US1] Update `demos\search02-hybrid-pagination\app\reproduce.py` to use validated manifest-derived index names, total counts, allowed IDs, keyword sets, and optional expected vector sets throughout client construction, readiness counters, summaries, and classification. Version-2 keyword validation requires exactly 6,158 expected IDs across 1,232 pages with three final rows, while index counts must be 6,183; vector validation requires exactly the 25 shared and 25 vector-only IDs. Preserve actual counts, request hooks, retry policy, ID-only selection, scan/probe/repeat semantics, missing-count vector handling, and version-1 behavior.
- [x] T008 [P] [US1] Implement independent version-2 deterministic corpus/schema validation and version-derived summaries/classification in `demos\search02-hybrid-pagination\app\dotnet\Program.cs`, reproducing the exact manifest, ID, content, vector, group, and hash constraints from T005-T006. Replace relevant fixed `Records`/all-ID keyword assumptions without changing the existing CLI, version-1 recipe, package/API pins, actual request capture, or measurement policies; reject wrong vector membership and keep keyword total 6,158 distinct from index total 6,183.
- [x] T009 [US1] Make shared evidence inspection in `demos\search02-hybrid-pagination\app\compare.py` resolve version-specific schema, allowed IDs, expected controls, and completeness from each report's verified fixture; recompute rather than trust saved summaries, preserve effective-request/profile/package checks, and reject fixture/index/environment/query/run mismatches without rewriting original evidence.
- [x] T010 [US1] Update `demos\search02-hybrid-pagination\app\preview.py` to use the validated fixture's keyword membership count for expanded recall, keeping `retrievable` at 1,000 and `expanded` at 6,158 even when the index total is 6,183. Require the mixed run's completed stable Python hybrid baseline, retain lazy preview-only model construction and filenames `preview-retrievable-1000`/`preview-retrievable-6158`, reject original-fixture baselines, and preserve existing version-1 preview behavior and exact SDK/API settings.
- [x] T011 [P] [US1] Run and complete the recipe/loader checks in `demos\search02-hybrid-pagination\scripts\validate_local.py` against two temporary generated version-2 fixtures and the preserved original fixture; verify exact corpus/manifest/schema byte reproducibility, group arithmetic, offline top-50 membership and numerical separation, and every malformed-input refusal from T004. Record these as local design/generator checks, not observed Azure results.
- [x] T012 [US1] Exercise the modified Python/.NET summary, classification, CLI, and inspector paths using `demos\search02-hybrid-pagination\scripts\validate_local.py`, `app\reproduce.py`, `app\compare.py`, `app\preview.py`, and `app\dotnet\Program.cs`: cover both fixture versions, actual request/profile parity, wrong vector members, missing initial vector count with ten candidate pages, continuation-bearing short/empty responses, duplicates, count drift, repeated boundaries, and evidence overwrite refusal. Use focused offline inputs/transport checks and existing tooling, retaining explicit incomplete outcomes rather than introducing fallback counts or a new test project.

**Checkpoint**: US1 implementation and offline checks are complete; live acceptance remains unverified until T029-T036. Never mark the story accepted solely from engineered vectors or fixture declarations.

## Phase 4: User Story 2 - Preserve the Original Reproduction (Priority: P1)

**Goal**: Ensure mixed preparation/reuse cannot replace or mutate the original experiment and each client independently checks the selected fixture's readiness.

**Independent Test**: Use SDK fakes/target-call recording and local receipt/inventory inputs to prove original-target refusal, populated-target refusal, correct readiness transitions, cross-fixture rejection, and unchanged original files. No successful live mixed search is needed for these protection checks.

### Checks and implementation

- [x] T013 [US2] Add pre-implementation protection checks in `demos\search02-hybrid-pagination\scripts\validate_local.py` for absent/empty versus populated mixed targets, incorrect schema/identity, missing or mismatched receipts, partial upload failure, indexing delay, bad ID/content inventory, wrong-state promotion, and attempts to write the original index. Record intended SDK mutation targets and require zero original-index/service/authentication mutations.
- [x] T014 [US2] Add the version-2 one-time preparation branch in `demos\search02-hybrid-pagination\app\fixture.py`: validate the fixture/environment first, allow only an absent or empty correctly defined `hybrid-pagination-mixed-v2`, and refuse a populated target before upload or schema update. Retain 500-document batches and verify all 6,183 individual upload results; persist fixture/service/schema-bound `preparation.json` with timestamps/counts/evidence references and states "`uploading`, `uploaded`, `ready`, and `incomplete`". Never upsert a populated mixed target, delete unexpected data, alter version-1 preparation, recreate the service, or conceal underlying errors.
- [x] T015 [P] [US2] Implement `verify_prepared_fixture(manifest_path, env_file)` in `demos\search02-hybrid-pagination\app\fixture.py`: check the matching receipt, actual schema/count, and complete ordered ID/content inventory using existing retrievable fields; normal inventory pagination is distinct from measured first-page-only requests. Enforce "`uploaded` means every document upload succeeded but readiness may still be pending" and only promote that local state to `ready` after every check passes; reject `uploading`/`incomplete` or missing evidence, perform no Azure writes, and do not claim remote hidden-vector verification.
- [x] T016 [P] [US2] Independently implement the mixed ready-receipt, service/fixture/schema identity, indexed count, and ordered ID/content inventory gate in `demos\search02-hybrid-pagination\app\dotnet\Program.cs` before measured searches. Require an already `ready` receipt, reject unready or altered targets, keep inventory pagination separate from measured requests, do not call Python or change hidden-vector retrievability, and leave the original version-1 path usable.
- [x] T017 [US2] Wire version-2 Python measurements through the shared read-only readiness gate in `demos\search02-hybrid-pagination\app\reproduce.py`, so stable and preview cases both consume only the selected prepared mixed index; retain original environment/subscription behavior, profile APIs, case-file overwrite protection, and version-1 readiness without imposing a new receipt on historical fixtures.
- [x] T018 [US2] Complete and run target/receipt/mismatch tests in `demos\search02-hybrid-pagination\scripts\validate_local.py` against the implementation in `app\fixture.py`, `app\reproduce.py`, `app\compare.py`, `app\preview.py`, and `app\dotnet\Program.cs`; prove no schema/upload call occurs on a populated or original target, no failed upload can become ready through count equality, missing services are explicit blockers, and cross-fixture reports/baselines are rejected.
- [x] T019 [US2] Reinspect preserved version-1 stable and preview evidence through `demos\search02-hybrid-pagination\app\compare.py` and `app\preview.py`, compare protected-file hashes from T001, and validate original notebook/CLI default bindings to the original fixture/index without executing notebooks or replacement searches. Record preserved existing blockers and verify package manifests, lockfile, canonical notebooks, and original evidence remain unchanged.

**Checkpoint**: Isolation and original-flow regression checks pass before any live mixed preparation. A ready receipt plus ID/content checks is not asserted to prove hidden vectors or snapshot isolation.

## Phase 5: User Story 3 - Explain Membership and Count Scope (Priority: P2)

**Goal**: Present actual vector-only contributions and count scope in the notebook without inventing internal keyword-window attribution or silently accepting incomplete controls.

**Independent Test**: Render complete and deliberately incomplete local case fixtures with network operations disabled; check groups, text provenance, unknown window membership, count alignment, and exit status without replacement searches.

### Checks and implementation

- [x] T020 [US3] Add local contribution-contract checks to `demos\search02-hybrid-pagination\scripts\validate_local.py` for eight required slots, compatible/incompatible identities, complete and incomplete controls, missing cases, altered evidence, missing vector-only IDs, duplicates, positive beyond-advertised probes, and text provenance. Assert `keywordWindowMembership` exactly `{ "status": "not-observed", "ids": null }`; unknown membership must not become an empty set or an inferred inside/outside label.
- [x] T021 [P] [US3] Create `demos\search02-hybrid-pagination\app\contributions.py` to load the verified mixed fixture and inspect six stable plus two preview slots through shared helpers; preserve evidence references/hashes, expected groups, observed-set provenance, actual overlap, missing/duplicate IDs, and explicit incompatibility/missing reasons. Verified vector-only additions must remain null/unestablished when required controls are incomplete; never infer non-keyword status from absence in a partial scan or issue replacement/diagnostic queries.
- [x] T022 [US3] Complete the local CLI and JSON/Markdown rendering in `demos\search02-hybrid-pagination\app\contributions.py` with `--manifest` and `--run-dir`, outputs `contribution-comparison.json`/`.md`, distinct `measurementsComplete`, `contributionAcceptance`, and per-case `countAlignmentVerified`, and durable blocked findings/nonzero exit when acceptance fails. Require all eight valid compatible cases, both clients' valid controls, 25 additions in every required hybrid case, and the expanded target for success. Show at least three actual hybrid-returned vector-only IDs with local verified text and `textSource: "verified-fixture"`; do not imply ID-only responses returned that text or hard-code the smaller union to 1,025.
- [x] T023 [P] [US3] Create `demos\search02-hybrid-pagination\notebooks\06_vector_contributions.ipynb` using the original kernel and small purpose-headed cells for prerequisites/explicit paths, local generation/group preview, explicitly confirmed one-time preparation, read-only reuse/fresh run identity, six independent stable cases, two `[PREVIEW]` cases, and local review/evidence links. Reuse the existing isolated preview interpreter and generated environment, surface stdout/stderr and nonzero failures, keep partial review deliberate after failed cases, and do not automatically prepare a populated target, change original notebooks, or introduce an alternative cleanup or attribution query.
- [x] T024 [US3] Validate syntax and command/path wiring for `demos\search02-hybrid-pagination\notebooks\06_vector_contributions.ipynb` with explicit offline subprocess/SDK mocks and saved local case fixtures; prove preparation is opt-in, reruns create fresh evidence paths and can skip preparation, selected query settings remain unchanged, failures are visible, and the final review uses the actual selected fixture/run rather than historical version-1 evidence.
- [x] T025 [US3] Run the complete contribution checks in `demos\search02-hybrid-pagination\scripts\validate_local.py` against `app\contributions.py` and the notebook review heading, with network use disabled: verify all eight slots, at least three measured-ID text examples, exact unknown-window/null representation, no accepted membership from incomplete controls, and rejection of count alignment when following probes return rows. Clearly label synthetic local test evidence and do not present it as live acceptance.

**Checkpoint**: The notebook can explain saved evidence, including honest partial findings; original keyword-control failures and unobservable window attribution remain explicit.

## Phase 6: Polish, Cross-Cutting Validation, and Gated Live Acceptance

**Purpose**: Align documentation, validate all changed surfaces, and obtain actual acceptance evidence only after explicit approval.

- [x] T026 Update `demos\search02-hybrid-pagination\README.md`, `docs\architecture-notes.md`, `metadata.json`, and `specs\003-vector-only-contribution\quickstart.md` for the mixed fixture, preserved original journey, exact commands, one-time preparation/read-only reuse distinction, request-volume warning, synthetic vector meaning, three full-query groups, and `not-observed` internal membership. Preserve metadata keys and label all not-yet-run live outcomes as pending, not measured success.
- [x] T027 [P] Run focused Python syntax/runtime checks and the existing validator for `demos\search02-hybrid-pagination\app` and `scripts\validate_local.py`; build `app\dotnet\HybridPagination.csproj` without restoration first, using locked restoration only if missing dependencies require it, and run configured notebook hygiene only on the new `notebooks\06_vector_contributions.ipynb`. Keep pins/lockfile/CI unchanged and report the known original-notebook metadata baseline failure separately rather than weakening checks or editing protected notebooks.
- [x] T028 [P] Compare T001 hashes for protected files in `demos\search02-hybrid-pagination\notebooks` and original `outputs\generated\reproduction` fixture/runs/preview-runs, verify new environments/generated outputs/build artifacts remain ignored, and review recorded SDK target-call checks. Confirm source changes are limited to the planned shared consumers/new notebook/renderer/docs and no original evidence was rewritten.
- [x] T029 Obtain and record explicit approval for both new-index preparation and the full read-only eight-case experiment described in `specs\003-vector-only-contribution\quickstart.md` before executing its commands; identify target `hybrid-pagination-mixed-v2`, preservation of `hybrid-pagination-debug`, unchanged paid service, and roughly 6,400 primary reads plus inventory/boundaries. If approval is absent, mark dependent live tasks blocked and stop without provisioning, index writes, or remote validation.
- [x] T030 After T029 approval, follow the one-time preparation and read-only readiness headings in `demos\search02-hybrid-pagination\notebooks\06_vector_contributions.ipynb` to create/populate only the approved new target and persist `outputs\generated\reproduction\fixtures\mixed-v2\preparation.json` plus actual schema evidence. Require every upload result and ready-state schema/count/ID-content checks; reuse an already prepared target only through readiness, and stop on missing service or unexpected populated data without automatic repair/deletion.
- [x] T031 Under the approved immutable-index run, collect the six independent stable cases through `demos\search02-hybrid-pagination\app\reproduce.py` and `app\dotnet\Program.cs` into one fresh `outputs\generated\reproduction\mixed-runs\<run-id>` directory, preserving full primary scans, exact requests/SDK/API metadata, errors, and two observations per selected boundary. Record each attempt and any blocked/failed case explicitly; a failed keyword control does not become an empty result or prevent deliberate collection of independent evidence.
- [x] T032 Collect both configured preview cases through `demos\search02-hybrid-pagination\app\preview.py` using that mixed run's completed stable Python hybrid baseline, recall 1,000/6,158, SDK 12.1.0b2, and actual API 2026-08-01-preview; preserve their case/page/schema files in the same mixed run. If that baseline is incomplete or a preview fails, record the blocker/missing case rather than substituting version-1 evidence or marking the scenario passed.
- [x] T033 Render and review real `outputs\generated\reproduction\mixed-runs\<run-id>\contribution-comparison.json` and `.md` via `demos\search02-hybrid-pagination\app\contributions.py` and the new notebook, recomputing actual controls/contributions/count findings. Verify expected versus observed groups, actual text-example IDs/provenance, repeated boundaries, and explicit gaps/exit status; retain a blocked report when any required measurement or control fails.
- [x] T034 Perform approved read-only original-index identity/schema/count checks and audit mutation targets for `demos\search02-hybrid-pagination\app\fixture.py` and `app\dotnet\Program.cs`; compare original local evidence/fixture/notebook hashes against T001. Record any preservation discrepancy without overwriting/reverting original artifacts, and do not claim metadata/count checks prove unchanged remote hidden vectors or snapshot isolation.
- [x] T035 Reconcile actual observed outcomes and limitations into `demos\search02-hybrid-pagination\README.md`, `docs\architecture-notes.md`, `metadata.json`, and `specs\003-vector-only-contribution\quickstart.md`, linking retained real reports and recording failed/unrun checks honestly. Leave the original `specs\002-reproduce-hybrid-pagination\tasks.md` T029 and its acceptance status unchanged; state shared-helper fix scope, why no Bicep/auth change was needed, absence of temporary workarounds/error-only fixes, and that service cleanup remains separately approved.
- [ ] T036 Verify every SC-001 through SC-007 outcome from `specs\003-vector-only-contribution\spec.md` against the actual mixed reports: both exact keyword/vector controls, all 25 vector-only additions in every required hybrid case, expanded 6,183 reported/unique IDs across 1,237 populated pages with three final rows, zero duplicates/empty advertised pages/positive following-page probes, original preservation, and honest failure handling. Keep this final acceptance task unchecked with specific blockers if any requirement is unmet; do not relax inputs, add sorting, erase evidence, or relabel incomplete controls to finish.

**Checkpoint**: Implementation completion, collection attempts, and successful live acceptance are separate states. T031-T035 may document blocked evidence; that does not make T036 complete.

## Dependencies & Execution Order

### Phase and story graph

```text
T001 Setup
  -> T002 + T003 Foundations
  -> US1 (T004-T012)
  -> US2 (T013-T019)
  -> US3 (T020-T025)
  -> documentation + local validation (T026-T028)
  -> explicit live approval (T029)
  -> preparation + actual case collection/review (T030-T034)
  -> outcome documentation (T035)
  -> strict final acceptance (T036)
```

US1 owns retrieval behavior; US2 owns preparation safety, readiness/reuse, and baseline regression; US3 consumes the common case contract. US2's critical live protections are mandatory before any remote experiment. US3 can be tested independently with local case fixtures, but its final implementation integrates the completed US1/US2 consumers. This shared-helper demo therefore deliberately serializes story integration rather than claiming fully independent implementation.

### Task prerequisites

Unlisted execution-order neighbors are not implicit prerequisites; use this graph. All foundational tasks finish before story work starts.

| Task | Prerequisites |
|---|---|
| T001 | None |
| T002 | T001 |
| T003 | T001 |
| T004 | T002, T003 |
| T005 | T004 |
| T006 | T005 |
| T007 | T006 |
| T008 | T006 |
| T009 | T007, T008 |
| T010 | T009 |
| T011 | T006 |
| T012 | T007, T008, T009, T010, T011 |
| T013 | T012 |
| T014 | T013 |
| T015 | T014 |
| T016 | T014 |
| T017 | T015 |
| T018 | T015, T016, T017 |
| T019 | T018, T001 |
| T020 | T019 |
| T021 | T020 |
| T022 | T021 |
| T023 | T020 |
| T024 | T022, T023 |
| T025 | T024 |
| T026 | T012, T019, T025 |
| T027 | T026 |
| T028 | T026, T001 |
| T029 | T027, T028 |
| T030 | T029 |
| T031 | T030 |
| T032 | T031 |
| T033 | T031, T032 |
| T034 | T033, T001 |
| T035 | T033, T034 |
| T036 | T035 |

T032 depends on the recorded stable collection attempt; actual preview execution additionally requires a completed, compatible Python hybrid baseline. T033 must still render explicit gaps after a blocked preview attempt. No collection task is a substitute for T036's acceptance check.

### Parallel opportunities

- After T001: T002 (Python expectations) and T003 (.NET expectations).
- After T006: T007 (Python measurements), T008 (.NET measurements), and T011 (local fixture checks).
- After T014: T015 (Python readiness) and T016 (.NET readiness).
- After T020: T021/T022 (renderer) can overlap T023 (notebook authoring against the fixed contract); their integrated validation waits for both.
- After T026: T027 (build/syntax/hygiene checks) and T028 (integrity/exclusion checks).
- Do not concurrently edit the same helper or `scripts\validate_local.py`. Do not overlap preparation with measurements or automatically parallelize live queries; preserve the planned sequential evidence flow.

## Parallel Examples per User Story

### User Story 1

After T006, implement T007 in `app\reproduce.py` and T008 in `app\dotnet\Program.cs` while running T011's fixture checks in `scripts\validate_local.py`. Join before T009-T012 integration.

### User Story 2

After T014 defines receipt production, implement T015 in `app\fixture.py` and T016 in `app\dotnet\Program.cs` independently against the same receipt/inventory contract. T017 and combined refusal/regression checks follow.

### User Story 3

After T020, author the renderer in `app\contributions.py` (T021-T022) alongside the new notebook (T023). Run T024-T025 only when both sides implement the agreed CLI/finding shape.

## Implementation Strategy

### MVP first

The smallest useful retrieval slice is US1: a deterministic mixed fixture and one client's keyword/vector/hybrid evidence. The full requested MVP includes the second stable client and the two existing preview profiles; US3's polished explanation is not needed to inspect raw results.

US1-only implementation is **not permission to run live**: complete the mandatory US2 safety checks and T029 approval before creating or measuring the mixed index. A CLI-only demonstration can omit US3 presentation while retaining those protections, both clients' controls, and explicit acceptance limits.

### Incremental delivery

1. Establish baseline identity and two fixed fixture versions.
2. Deliver US1 generation and version-aware measurement with offline regressions.
3. Deliver US2 protected preparation/readiness and original-flow preservation.
4. Deliver US3 local findings/notebook explanation without new retrieval settings.
5. Pass local checks, obtain specific live approval, and collect real evidence.
6. Publish actual outcomes; accept only when all specification criteria pass.

### Coverage summary

| Scope | Tasks | Specification outcomes |
|---|---|---|
| Setup/foundations | T001-T003 | Version identity and preservation prerequisites |
| US1 | T004-T012 (9 tasks) | FR-001-FR-005, FR-008-FR-010, FR-012; SC-001-SC-004 |
| US2 | T013-T019 (7 tasks) | FR-006-FR-007, FR-016, FR-018; SC-006-SC-007 |
| US3 | T020-T025 (6 tasks) | FR-011, FR-013-FR-016; SC-003, SC-005, SC-007 |
| Cross-cutting/live | T026-T036 | FR-017-FR-019; actual SC-001-SC-007 validation |

**Total**: 36 tasks; T001-T035 complete, T036 unchecked because the measured keyword controls failed. No new infrastructure, auth mode, package, model, diagnostic attribution query, original-notebook rewrite, or cleanup workflow is authorized.

## Execution Record - 2026-11-02

- T001-T028: implemented and validated. The shared fixture/measurement/inspection helpers and independent .NET validator now distinguish indexed, keyword, and vector membership. No Bicep/authentication change or temporary local workaround was needed; no catch-and-explain-only fix was added.
- All 22 mixed-fixture offline tests pass, including deterministic recipes in both clients, the actual .NET ready gate with a local SDK transport, preparation mutation targets, partial-upload refusal, count/identity/evidence checks, CLI exit status, and heading-based notebook wiring.
- The complete existing validator ran 40 tests: 39 passed and the same pre-existing original-notebook kernel display-name check failed. The protected original notebook was not rewritten and the gate was not weakened.
- The .NET build passed without restoration, with zero warnings/errors. Configured notebook hygiene passed on the new notebook. Python syntax and Pylance checks found no errors in changed application files.
- All 54 protected original fixture/evidence/notebook/dependency/project files match the initial byte hashes. Reinspection preserves both original failed keyword controls, complete stable hybrid/vector cases, and complete configured preview cases.
- The implementation does not claim live acceptance. No Azure operations were performed; synthetic saved cases and transport tests are explicitly offline evidence. The original feature's T029 remains unresolved.
- T029 is awaiting an explicit decision covering new-index preparation and all eight live cases. T030-T036 are blocked by that decision; leave final acceptance unchecked if any live criterion fails.
- Subsequent explicit approval: the user selected **"Approve new-index preparation and all eight live cases"** on 2026-11-02. T029 is now complete and live execution may proceed only within that scope; missing service, unexpected target data, or failed acceptance remains a blocker.

### Approved live execution - 2026-11-02/03 UTC

- Run: `20261102T233019Z-bee9da5d`. Only the new mixed index was prepared; all 6,183 individual uploads succeeded and ready-state schema/count/ID-content checks passed. All eight case attempts and report/page/schema files are retained.
- Stable Python/.NET keyword: 6,158 reported/rows, 6,094 unique, 64 duplicate excess rows and 64 missing expected IDs. Both controls failed; their failure is not an empty-page success.
- Both vector controls: exactly 25 shared plus 25 vector-only IDs, no duplicates. Both stable hybrids: 6,183 reported, 1,046 unique, 210 populated and 1,027 empty advertised pages.
- Preview recall 1,000: 1,046 reported/unique, 210 populated pages, no empties. Preview recall 6,158: 6,183 reported/unique, 1,237 populated pages, three final rows, no duplicates/empties/positive following-page probes. Both count-alignment findings passed.
- All four hybrids returned all 25 declared vector-only IDs. Actual-ID fixture-text examples and exact unknown-window/null representation were verified. Accepted additions remain null because both required keyword controls failed.
- The [contribution report](../../demos/search02-hybrid-pagination/outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/contribution-comparison.md) deliberately exits nonzero, with no missing/invalid cases or identity mismatches. [Acceptance findings](../../demos/search02-hybrid-pagination/outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/acceptance.json) record failed SC-002 and blocked SC-003; SC-004 met its measured thresholds.
- [Preservation](../../demos/search02-hybrid-pagination/outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/preservation.json): all 54 protected original files are byte-unchanged; original service/index identity, schema, and count 6,158 matched before/after. No hidden-vector readback or snapshot-isolation claim.
- T036 remains unchecked. Correcting keyword pagination, adding ordering, or weakening acceptance is separate work, not an automatic workaround. The original feature's T029 remains unchanged. The service remains billable; no cleanup was authorized or performed.

### Publishing approval - 2026-11-03

- The user requested a new branch and commit, then explicitly selected **"Back up the notebook, allow standard cleanup, and commit"** after being told the hook would remove original notebook outputs, execution counts, and kernel display-name metadata.
- A byte-identical pre-publish notebook backup is retained outside the repository. Standard cleanup preserved notebook code/markdown and all 53 other protected files, including separate measurement evidence. This approved publishing-only exception does not alter the recorded live-run preservation result.
- All 40 local validator checks now pass; the notebook hook is enabled and passes. No ignored environments, generated evidence, caches, or build outputs are intended for the commit.
- Publication branch: `feat/search-vector-contributions`. T036 remains unchecked because live keyword-control acceptance is still blocked; publishing hygiene does not resolve it.
