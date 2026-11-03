# Tasks: Reproduce Hybrid Search Count/Pagination Discrepancy

**Input**: [Specification](./spec.md), [plan](./plan.md),
[research](./research.md), [data model](./data-model.md),
[local interface contract](./contracts/experiment.md), and
[quickstart](./quickstart.md).
**Working branch**: `feat/search-hybrid-pagination-infra`
**Feature identity**: `002-reproduce-hybrid-pagination`
**Generated**: 2026-10-30
**Status**: Implementation complete; all six cases measured. Full live acceptance
remains blocked at T029 because both keyword controls returned duplicate/missing IDs.
**Refined**: 2026-10-30 to resolve I1 (optional vector counts) and U1 (short-response continuation).

**Validation policy**: No new test framework or unit-test suite. Use the specified
scenario measurements, existing focused checks, .NET build, and notebook hygiene.
Independent validation criteria below are acceptance criteria, not claims that
the experiment has run.

**Organization**: Setup, foundation, P1 stories US1/US2/US4, P2 story US3, then
cross-cutting completion. Preserve the story numbers from the specification.

## Format and Scope

- Every checkbox has a sequential task ID, optional `[P]`, story label only within
  story phases, and explicit repository-relative file paths.
- `[P]` identifies different-file work that can run concurrently once its listed
  prerequisites are complete. It does not authorize parallel live measurements.
- Follow the [constitution](../../.specify/memory/constitution.md) and
  [authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md);
  load Azure Demo Authoring before implementation.
- Extend only the existing demo. Keep Feature 1 Bicep, keyless access, roles,
  setup/deployment behavior, and canonical destroy unchanged.
- Generated fixture/evidence paths below are local ignored outputs, not source
  files to commit. Do not edit attached notebook snapshots.
- Task generation does not authorize Azure execution, paid deployment, SDK
  installation, or resource deletion. Check current prerequisites and obtain any
  needed approval during implementation; never redeploy automatically.

## Phase 1: Setup

**Purpose**: Establish the approved tooling and keep generated/build files local.

- [X] T001 Verify Python 3.11+, the existing pins in `demos/search02-hybrid-pagination/requirements.txt`, and .NET 10 SDK availability; document the actual prerequisite checks in `demos/search02-hybrid-pagination/README.md`. Retain Search Python 12.0.0 and Identity 1.25.3 without adding Python dependencies; distinguish a missing SDK from a present runtime and record any blocker instead of installing or selecting another framework silently.
- [X] T002 [P] Scaffold `demos/search02-hybrid-pagination/app/dotnet/HybridPagination.csproj` and `demos/search02-hybrid-pagination/app/dotnet/Program.cs` as one `net10.0` console project; pin Azure.Search.Documents 12.0.0 and Azure.Identity 1.21.0, restore using the package manager, and retain `demos/search02-hybrid-pagination/app/dotnet/packages.lock.json` without adding a test project.
- [X] T003 [P] Check `.gitignore` coverage for `demos/search02-hybrid-pagination/outputs/generated/reproduction/`, the existing generated environment, and .NET `bin`/`obj` directories; add only missing scoped exclusions, preserving tracked project and NuGet lock files.

**Checkpoint**: Toolchain status is explicit; project pins and output exclusions
are ready. Missing prerequisites remain blockers, not completed execution evidence.

## Phase 2: Foundational Prerequisites

**Purpose**: Provide the shared immutable fixture, evidence contract, and
notebook preparation flow before implementing query stories.

- [X] T004 [P] Implement deterministic generation and manifest validation in `demos/search02-hybrid-pagination/app/fixture.py`: exactly 6,158 records; IDs "`doc-000001` through `doc-006158`; unique and stable."; content "Deterministic synthetic text containing the token `maths`; no customer content."; vectors "16 finite, integer-valued float32 components; nonzero norm." Follow the data model's SHA-256 byte rules for vectors, topic, keyword/filler repetitions; document fixed text order and compact JSON serialization; write ascending-ID UTF-8 JSONL with LF endings and hash exact corpus bytes. Include every manifest field from the data model, fixture version 1, the 16-component query vector `[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`, cosine, `k=50`, API `2025-09-01`, and page size five; exclude timestamps/environment identity from deterministic fixture identity.
- [X] T005 [P] Define typed query/page/report structures, required CLI arguments, and durable evidence serialization in `demos/search02-hybrid-pagination/app/reproduce.py` following `specs/002-reproduce-hybrid-pagination/contracts/experiment.md`. Preserve "One-based `pageNumber`, zero-based `skip`, `top`, and whether the page is advertised.", nullable counts, optional scores, actual request/response metadata, and phase values "`scan`, `boundary-probe`, or `boundary-repeat`". Reports require all contract members, UTC timestamps with null unfinished finish time, status values "`complete`, `blocked`, `incomplete`, or `unsupported`", and outcome values "`reproduced`, `not-reproduced`, `blocked/incomplete`, or `not-applicable`". Enforce the contract's `summary.scanBasis`/`scanPageCount`, nullable count/advertised/gap fields for `vector-k`, and nullable observation `incompleteReason=service-continuation`; restrict `not-applicable` to a complete vector-only case without an initial count. Initialize incomplete reports, append/flush observations, and refuse same-case/run overwrites.
- [X] T006 Add SDK index creation/population and indexed-count readiness to `demos/search02-hybrid-pagination/app/fixture.py`: index `hybrid-pagination-debug`; "`id`: `Edm.String`, key, retrievable, not searchable."; "`content`: `Edm.String`, searchable and retrievable; `standard.lucene` analyzer."; "`vector`: `Collection(Edm.Single)`, searchable, 16 dimensions" with exhaustive KNN/cosine. Save declared-schema hash and raw actual schema separately; check every batched upload result and exactly 6,158 indexed records. Reuse environment validation from `demos/search02-hybrid-pagination/app/notebook_helpers.py` and Feature 1 exports; never clear another index, silently delete unexpected documents, add a model/vectorizer, or substitute an empty corpus when indexing is incomplete.
- [X] T007 Create small purpose-headed prerequisite, fixture-generation, index-preparation, and indexed-count cells in `demos/search02-hybrid-pagination/notebooks/04_reproduce.ipynb`. Load the generated environment, verify setup-user/subscription context and both toolchains before mutations, use subscription-selected AzureCliCredential without a simultaneous tenant override, and generate shared fixture/run paths under `demos/search02-hybrid-pagination/outputs/generated/reproduction/`. Require existing infrastructure readiness before population, preserve its initial empty-service checks, and stop explicitly on incomplete indexing without flags, fallback data, or automatic redeployment.

**Checkpoint**: One fixture/index/environment contract serves both clients.
All query work depends on this foundation; neither language may regenerate a
different fixture or write during measurement.

## Phase 3: User Story 1 - Measure the Discrepancy (P1, MVP)

**Goal**: Obtain an honest single-client hybrid symptom measurement before making
customer-cause claims.

**Independent validation**: Against the prepared immutable index, run Python
hybrid at five results per page. Retain every advertised offset, count, ID,
failure, and required repeated boundary; independently recompute reachability.
Reproduced requires a positive count-minus-unique gap AND an empty advertised
page. A valid not-reproduced or explicit blocked result is acceptable; 257 pages
is never an expected boundary. Without controls, cause attribution is provisional.

- [X] T008 [P] [US1] Implement the direct Python hybrid request in `demos/search02-hybrid-pagination/app/reproduce.py`: `maths`, simple query, `content`, search mode `any`, one shared vector on `vector`, exhaustive `k=50`, count enabled, select `id`, `top=5`, and explicit `skip` under API `2025-09-01`. Exclude filters, sorting, semantic reranking, multiple vectors, and preview controls. Consume only the first `by_page()` service page and obtain count from that same response via a public response hook, not a second `get_count()` iterator or private SDK API.
- [X] T009 [US1] Add measured-request instrumentation and narrow failure persistence in `demos/search02-hybrid-pagination/app/reproduce.py`: disable Search retries; capture actual API/method/path, normalized nonsecret payload, send count, continuation presence, HTTP status, service request ID, and timestamp. Enforce one Search send per logical page. For any scan, probe, or repeat with `rowCount < top` and continuation information, preserve actual response values, set `incompleteReason=service-continuation`, and stop the case as incomplete with outcome `blocked/incomplete` and nonzero exit before counting it as exhausted/empty or reproduction evidence; never fetch continuation automatically. On SDK failure preserve original error and nonzero exit, with "failed row count and IDs are null, not zero and an empty array." Never log tokens/authorization headers or translate failures into empty pages.
- [X] T010 [US1] Implement complete offset scanning in `demos/search02-hybrid-pagination/app/reproduce.py`: request offset zero, require an initial count for keyword/hybrid, set `scanBasis=advertised-count`, compute `ceil(initialCount/5)`, and visit every advertised offset without stopping at the first valid empty page. Preserve nullable subsequent counts; compare available non-null values for drift, never treat null as zero or drift. Missing initial keyword/hybrid count or differing available counts makes the case incomplete; vector-only absence follows T014 instead. Handle zero advertised pages and partial final pages without continuation explicitly; retain the bootstrap observation without counting it as an advertised zero-count page.
- [X] T011 [US1] Implement summary metrics, boundary replays, and classification in `demos/search02-hybrid-pagination/app/reproduce.py`: reported count, total rows, unique IDs, duplicate IDs/occurrences, advertised/populated/empty pages, first empty and last populated pages, count drift, and start/end index counts. Compute primary metrics in the declared scan basis, with advertised-only fields null for `vector-k`. Select last populated, following, final advertised, and first empty offsets when applicable; use final/first-empty candidate pages for `vector-k`. Deduplicate targets, reuse scan observations, probe outside-range offsets once, then repeat once for exactly two observations per selected offset. Exclude probes/repeats and incomplete observations from primary totals; compare count/size/ID-set/order separately. Complete only a full stable scan with successful repeats; apply T014's `not-applicable` exception only after those checks pass, and preserve failed/partial-response precedence. Flag ties/mutation limits without claiming snapshot isolation.
- [X] T012 [US1] Add the **Run the Python hybrid case** cell and concise count/reachability/boundary display to `demos/search02-hybrid-pagination/notebooks/04_reproduce.ipynb`; invoke the independent Python runner using the shared manifest/environment/run directory, surface its failures, and link its JSON/JSONL evidence without embedding thousands of observations or claiming customer-specific causation.

**Checkpoint**: The Python hybrid experiment can run on its own. This is the
smallest MVP, not completion of the promised two-client feature.

## Phase 4: User Story 2 - Isolate Other Causes (P1)

**Goal**: Add independently executable keyword/vector controls and a valid-baseline
gate before attributing the hybrid observation to candidate retrieval.

**Independent validation**: Run each Python control without invoking hybrid.
Keyword must return exactly the known 6,158 IDs with no duplicates, 1,232
advertised/populated pages, and three final-page rows. Record actual vector IDs,
count when present, and overlap. Failed controls must prevent causal attribution.
A missing optional vector count alone is not a failed control: require its full
candidate-page budget and boundaries, keep count-based fields null, and use
`not-applicable` without claiming a count discrepancy classification.

- [X] T013 [P] [US2] Add keyword-only query selection and expected-ID validation to `demos/search02-hybrid-pagination/app/reproduce.py`, reusing the measured paging/evidence implementation with no vector contribution. Enforce "exactly the expected 6,158 IDs, no duplicates, 1,232 advertised/populated pages, and three results on the last advertised page." Record missing IDs and failed-baseline reasons rather than tuning scoring/sorting or asserting a hybrid cause.
- [X] T014 [US2] Add vector-only selection to `demos/search02-hybrid-pagination/app/reproduce.py`, omitting lexical search rather than injecting `search=*`, and retaining the shared vector/field/exhaustive `k=50`. Without an initial count, require all `ceil(k/5)=10` candidate pages plus boundaries with `scanBasis=vector-k`; keep reported count, advertised pages/coverage/gap, and advertised-only boundaries null. Compute actual rows/IDs/candidate-page metrics, using final/first-empty candidate pages for boundary selection. Successful stable measurement has `status=complete`, `outcome=not-applicable`, and reason `count-unavailable`; do not change scan basis if a later count appears or infer count from `k`. Any SDK failure, `service-continuation`, drift among available counts, or unfinished required measurement remains blocked/incomplete.
- [X] T015 [P] [US2] Implement local Python-control analysis in `demos/search02-hybrid-pagination/app/compare.py`: recompute per-case metrics from observation files, check fixture/index/input identity, calculate actual keyword/vector/hybrid ID intersections, and gate hypothesis attribution on the passing keyword baseline and immutable-input evidence. Keep observations separate from inferred candidate-window explanations; do not assume text/vector set sizes add or issue replacement Search queries.
- [X] T016 [US2] Add **Run the Python keyword control** and **Run the Python vector control** cells before hybrid in `demos/search02-hybrid-pagination/notebooks/04_reproduce.ipynb`; use one immutable index/manifest and shared run directory, show actual control validity and overlap, and explain that rerunning preparation during scans invalidates the comparison while a new full run needs a new directory.

**Checkpoint**: All three Python cases are independently runnable; an unsuccessful
keyword baseline is visible before interpreting a hybrid count gap.

## Phase 5: User Story 4 - Compare Python and .NET (P1)

**Goal**: Execute the same three cases directly through .NET and compare all six
actual case reports, without wrapping Python query results.

**Independent validation**: Run .NET keyword/vector/hybrid from its CLI against
the already prepared index without invoking the Python query runner. Combine its
reports with Python's reports and verify effective settings/API, counts, ID sets,
duplicates, boundaries, and outcomes. Actual differences are valid findings;
missing/unsupported cases are gaps, not a completed demonstration.

- [X] T017 [P] [US4] Implement .NET CLI parsing, typed evidence structures, manifest/hash validation, current setup-user/subscription checks, and direct generated `KEY=value` environment loading in `demos/search02-hybrid-pagination/app/dotnet/Program.cs`. Require `--case`, `--manifest`, `--env-file`, and `--run-dir`; independently enforce the same data-model field/nullability/state constraints as T005, select AzureCliCredential by exported subscription without a simultaneous tenant override, validate actual index/schema/count, preserve runtime/package metadata, and prevent overwrites without adding dotenv packages or reading Python result files as query output.
- [X] T018 [US4] Implement all three direct Search SDK requests and public pipeline instrumentation in `demos/search02-hybrid-pagination/app/dotnet/Program.cs` under explicit `V2025_09_01`, matching Python's keyword/vector/count/select/top/skip settings. Disable Search retries; use initial `TotalCount` and only the first `GetResultsAsync().AsPages()` page, disposing the enumerator without continuation traversal. For every scan/probe/repeat with fewer than `top=5` rows plus continuation information, retain actual response values, set `incompleteReason=service-continuation`, and stop incomplete with nonzero exit before exhaustion/empty-page classification; never fetch continuation automatically. Capture actual sends/API/payload/status/request ID/continuation without secrets; preserve unsupported or non-equivalent settings explicitly instead of substituting another query.
- [X] T019 [US4] Implement independent .NET full scans, append/flush evidence, incomplete initialization, narrow failure/nonzero handling, all summary metrics, baseline checks, and boundary repeats in `demos/search02-hybrid-pagination/app/dotnet/Program.cs`, reproducing the contract's algorithms from T009-T011/T013-T014 rather than invoking Python. Preserve null failed values, nullable counts, zero-count behavior, duplicates, valid partial pages, available-count drift, one send per offset, and exactly two observations per selected boundary. Require initial keyword/hybrid counts; a successful count-unavailable vector control must measure all 10 candidate pages and boundaries with `scanBasis=vector-k`, count/advertised fields null, and `status=complete` / `outcome=not-applicable`. Failures, `service-continuation`, drift, or unfinished measurement override that exception. Emit the three `dotnet-*.json` reports and corresponding `.pages.jsonl` files.
- [X] T020 [P] [US4] Extend `demos/search02-hybrid-pagination/app/compare.py` with the `--run-dir` CLI and six-case `comparison.json`: recompute observation-backed metrics; verify corpus/schema/index/environment identities and effective API/query settings including documented/observed defaults; normalize only equivalent wire forms; compare counts, unique counts, returned ID sets, duplicates, boundaries, outcomes, and vector overlaps pairwise. Expose all six expected slots with actual report references or missing/unsupported reasons, block incompatible/incomplete causal comparisons, and permit genuine result disagreement without demanding equal tied ordering. Accept complete `not-applicable` vector controls without failing solely for an optional missing count; disclose scan bases and unavailable count comparisons as null, not equal. Reject use of that exception for keyword/hybrid, failed/incomplete vector controls, or `service-continuation`.
- [X] T021 [US4] Add the .NET build/prerequisite checks, separate purpose-headed .NET case cells, and local JSON comparison cell in `demos/search02-hybrid-pagination/notebooks/04_reproduce.ipynb`. Invoke the console project independently with the shared manifest/environment/run directory; surface captured stdout/stderr and nonzero exits, avoid new confirmation flags or generic subprocess wrappers, and preserve sequential measurements without writes between clients.
- [X] T022 [US4] Execute the six contract CLI cases once against a currently authorized, prepared environment and retain six actual reports plus JSONL evidence in `demos/search02-hybrid-pagination/outputs/generated/reproduction/runs/<run-id>/`. Verify build/syntax, actual package/API versions, same-user context, indexed fixture, one-send paging, complete advertised-page coverage or the count-unavailable vector's full 10-page candidate budget, and repeated boundaries. Check actual optional-count and continuation behavior against the contract without inventing service observations. Obtain approval if fresh paid infrastructure or tooling installation is required; if a prerequisite/request fails, retain explicit blocked evidence and leave successful two-client acceptance incomplete instead of manufacturing missing reports.

**Checkpoint**: All six measurements exist, or their actual blockers remain
explicit. The .NET client is independently executable; matching SDK numbers are
not a substitute for observed request parity.

## Phase 6: User Story 3 - Customer-Safe Explanation (P2)

**Goal**: Produce a reusable, source-backed explanation grounded in the measured
reports and clearly bounded customer-parity limitations.

**Independent validation**: A reviewer reads one summary, follows its evidence
references, and identifies settings, counts/reachability/pages, boundaries, control
validity, language differences, hypothesis, and outstanding parity gaps without
customer data or new Search queries.

- [X] T023 [P] [US3] Render `comparison.md` from the existing machine comparison in `demos/search02-hybrid-pagination/app/compare.py`, with side-by-side six-case facts and separate observations, hypothesis, and limitations sections. Include corpus/index/query/runtime/package/API identity, reported versus reachable counts, advertised/populated/empty pages, duplicates, repeated boundaries, control validity, and request mismatches. Distinguish candidate-based vector scans and unavailable count comparisons; `not-applicable` is not proof of no discrepancy, and `service-continuation` is incomplete evidence, not an exhausted page. Cite and recheck the authoritative references in `specs/002-reproduce-hybrid-pagination/research.md`; label count/recall defaults as documented rather than observed, assess overlap without adding set sizes, and avoid unsupported customer-defect, production, beta-remediation, GA-date, or exact-257-page claims.
- [X] T024 [P] [US3] Update `demos/search02-hybrid-pagination/docs/architecture-notes.md` with the unchanged Feature 1 infrastructure, shared synthetic index, independent clients, effective-request capture, initial-only readiness ordering, and the difference between symptom reproduction and causal proof. Explain fixed-vector/exhaustive retrieval and tie/mutation/customer-setting limitations; identify this as data-plane experimentation with no Bicep remediation or temporary infrastructure workaround.
- [X] T025 [US3] Add **Compare observations and explain the finding** to `demos/search02-hybrid-pagination/notebooks/04_reproduce.ipynb`, rendering the locally generated comparison and exposing evidence links plus real gaps; do not rerun searches to create the explanation or turn blocked cases into success. Keep small cells and purpose/heading-based instructions.

**Checkpoint**: The explanation can be reviewed and regenerated locally from
evidence; it does not depend on claims about the inaccessible customer application.

## Phase 7: Polish and Cross-Cutting Completion

**Purpose**: Align the demo journey, existing quality gates, and final acceptance
record without adding unrelated hardening or new infrastructure.

**Actual acceptance blocker (2026-10-30)**: Local run
`demos/search02-hybrid-pagination/outputs/generated/reproduction/runs/20261030-live-v2/`
contains six real reports and six unchanged JSONL evidence files. Both hybrid
cases reproduced count 6,158 versus 1,039 unique IDs (208 populated/1,024 empty
advertised pages); both vector cases reached 50. Both keyword cases visited all
1,232 advertised offsets but returned 6,158 rows containing only 6,111 unique IDs.
Input/API/request parity and cross-client ID sets agree. T029 remains unchecked
because its required keyword baseline does not pass, not because implementation
or cases are missing. No sorting/data workaround was introduced. A follow-up
design decision is required before changing the experimental constraints.

Python measurements used the notebook/public runner entrypoint; .NET measurements
used its independent CLI. CLI parsing/overwrite contract and local renderer were
checked separately. Audited Identity metadata corrections reused valid unchanged
measurements, rather than repeating thousands of requests.

- [X] T026 [P] Update `demos/search02-hybrid-pagination/README.md` and the handoff text in `demos/search02-hybrid-pagination/notebooks/02_configure.ipynb` to cover the full preparation/readiness/reproduction journey, exact prerequisites/pins, standalone commands, several-thousand-read expectation, output locations, new run directories, and explicit no-writes rule. Explain that `demos/search02-hybrid-pagination/notebooks/03_test.ipynb` empty-service readiness runs before ingestion, never delete data to satisfy it afterward, and retain the existing setup/deployment/canonical cleanup instructions and known cleanup limitation.
- [X] T027 [P] Update `demos/search02-hybrid-pagination/metadata.json` using its existing schema to describe the two-client hybrid count/pagination investigation, synthetic fixture, reproduction notebook, required tooling, and evidence outcomes; do not add infrastructure/model requirements or unsupported reproduction claims.
- [X] T028 Adjust only obsolete infrastructure-only scenario assumptions in `demos/search02-hybrid-pagination/scripts/validate_local.py` as necessary for the new notebook/app scope; retain existing infrastructure, canonical notebook, environment-contract, and hygiene checks without introducing new tests/frameworks. Run the smallest relevant existing validation selections, Python syntax checks, .NET build for `demos/search02-hybrid-pagination/app/dotnet/HybridPagination.csproj`, and configured pre-commit notebook cleanup on changed notebooks; verify setup/destroy remain canonical and no generated evidence, environment values, tokens, `bin`, or `obj` files are staged.
- [ ] T029 Validate `demos/search02-hybrid-pagination/outputs/generated/reproduction/runs/<run-id>/comparison.json` and `comparison.md` against all acceptance observations in `specs/002-reproduce-hybrid-pagination/quickstart.md`, recomputing coverage/counts/IDs/duplicates/classification and replay counts from the six observation files. Regenerate the local explanation after renderer changes; reuse unchanged valid measurements rather than repeating thousands of requests unnecessarily. A not-reproduced result passes when evidence is complete; successful vector controls without initial counts also pass with full candidate budgets/boundaries, null count/advertised fields, and outcome `not-applicable`, without pretending unavailable counts agree. Keyword/hybrid missing initial counts, `service-continuation`, missing cases, baseline failures, changed inputs, count drift, or unfinished measurements remain blocked. Check the two refined policies with focused local reasoning/checks where service observations are absent; never fabricate a live partial-response or missing-count event.
- [X] T030 Reconcile actual implementation/validation status and any remaining blockers in `specs/002-reproduce-hybrid-pagination/spec.md`, `specs/002-reproduce-hybrid-pagination/quickstart.md`, and `specs/002-reproduce-hybrid-pagination/tasks.md`; distinguish local checks from live results and record the evidence location without committing ignored outputs. State data-plane fix/experiment scope, unchanged Bicep and canonical notebooks, no catch-and-explain workaround, and remaining customer-parity gaps. Do not mark unexecuted acceptance tasks complete, create a commit automatically, or run cleanup without authorization.

## Dependencies and Execution Order

### Story graph

```text
Setup -> Foundation -> US1 (Python hybrid MVP) -> US2 (Python controls)
                   \-> US4 .NET implementation --------------\
                              US2 + .NET + comparison -------> US4 acceptance
                                        |
                                        v
                               US3 explanation implementation
                                        |
                                        v
                               Polish checks + US4 evidence -> Final acceptance
```

US2 depends on US1's reusable paging implementation, not on executing hybrid
before its controls. US4's .NET implementation can begin after foundation; its
acceptance requires Python controls and six-case comparison. US3 renderer/docs
implementation can proceed after comparison support without waiting for Azure;
its acceptance requires actual reports, not a new experiment. No story may
silently omit the shared fixture or replace the other language's SDK execution.

### Task prerequisites

Only actual prerequisite edges are listed; list order does not create an edge.
When a prerequisite is blocked, do not mark dependent execution complete.

| Task | Prerequisite tasks |
|------|--------------------|
| T001 | None |
| T002, T003 | T001 |
| T004, T005 | T002, T003 |
| T006 | T004 |
| T007 | T005, T006 |
| T008 | T007 |
| T009 | T008 |
| T010 | T009 |
| T011 | T010 |
| T012 | T011 |
| T013 | T012 |
| T014 | T013 |
| T015 | T012 |
| T016 | T014, T015 |
| T017 | T007 |
| T018 | T017 |
| T019 | T018 |
| T020 | T015 |
| T021 | T016, T019, T020 |
| T022 | T021 |
| T023, T024 | T020 |
| T025 | T021, T023 |
| T026, T027 | T024, T025 |
| T028 | T026, T027 |
| T029 | T022, T028 |
| T030 | T029 |

### Parallel execution examples

- **Setup/foundation**: After T001, T002 (project) and T003 (ignore rules) are
  independent. After setup, T004 (fixture) and T005 (evidence structures) are
  independent; T006 must wait for T004.
- **US1**: No parallel edits within the shared Python runner. After T007, T008
  in the Python runner can execute alongside US4 T017 in `Program.cs`.
- **US2**: After T012, T013 in the Python runner and T015 in the local comparator
  can execute concurrently. T014 follows T013; notebook integration waits for both.
- **US4**: Once T007 and T015 are complete, T017-T019 in `Program.cs` and T020
  in the comparator can proceed independently. T021 integrates them afterward.
- **US3**: After T020, T023 (Markdown renderer) and T024 (architecture notes) can
  proceed in parallel without waiting for live execution; T025 waits for the
  renderer and T021's notebook integration. Acceptance still requires actual evidence.
- **Polish**: T026 (README/handoff) and T027 (metadata) are independent after
  US3 integration. All changes to the reproduction notebook itself remain serial.

Keep actual Search scans and boundary replays sequential on the unchanged index.
Parallel opportunities describe implementation work, not permission to change
query inputs or write during either client's run.

## Requirements Traceability

| Requirement | Implementation / acceptance tasks |
|-------------|-----------------------------------|
| FR-001 | T004, T006, T023 |
| FR-002 | T004, T006, T007, T022 |
| FR-003 | T004, T015, T023 |
| FR-004 | T008, T013, T014, T018, T022 |
| FR-005 | T008, T010, T018, T019 |
| FR-006 | T005, T009, T017, T018, T020 |
| FR-007 | T009, T010, T018, T019, T022, T029 |
| FR-008 | T005, T011, T014, T019, T020, T029 |
| FR-009 | T011, T014, T019, T022, T029 |
| FR-010 | T005, T011, T014, T019, T020, T029 |
| FR-011 | T015, T020, T023 |
| FR-012 | T011, T023, T024 |
| FR-013 | T006, T008, T014, T018, T021 |
| FR-014 | T006, T007, T021, T026, T027, T028 |
| FR-015 | T020, T023, T024 |
| FR-016 | T005, T013, T014, T017, T018, T019, T022 |
| FR-017 | T004, T008, T018, T020, T029 |
| FR-018 | T020, T023, T025 |
| FR-019 | T001, T002, T009, T018, T020 |
| SC-001 | T013, T019, T022, T029 |
| SC-002 | T010, T014, T019, T022, T029 |
| SC-003 | T011, T019, T022, T029 |
| SC-004 | T011, T019, T029 |
| SC-005 | T011, T019, T022, T029 |
| SC-006 | T023, T024, T025, T029 |
| SC-007 | T014, T019, T020, T021, T022, T029 |
| SC-008 | T020, T023, T029 |

## Implementation Strategy

1. **MVP first**: Complete setup, foundation, and US1 (T001-T012). Inspect a
   single Python hybrid measurement with full paging and boundary evidence.
   Do not present this as completed two-client acceptance or confirmed causation.
2. **Controls**: Add US2. A failed keyword baseline blocks cause attribution;
   never change fixture/ranking just to force the customer-reported boundary.
3. **Second client**: Implement .NET independently, integrate six-case comparison,
   then collect one complete evidence set under T022 when prerequisites permit.
4. **Explanation**: Complete US3 from evidence and current authoritative guidance;
   all missing settings or disagreement remain visible.
5. **Finish**: Run focused existing checks, recompute acceptance from saved
   observations, align docs/metadata, and report real completion/blockers.

No step implements beta remediation, distance sorting, production approval,
enterprise hardening, or a feature-local infrastructure/cleanup workaround.
Use existing canonical cleanup only when requested/authorized.
