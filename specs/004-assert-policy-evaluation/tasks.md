# Tasks: ASSERT Policy Evaluation Lab

**Input**: Design documents in `specs\004-assert-policy-evaluation\`.

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [infrastructure contract](./contracts/infrastructure.md), [evaluation contract](./contracts/evaluation.md), and [quickstart.md](./quickstart.md).

**Organization**: One feature, two separately requested implementation runs.
The original graph required the full three-model M1 gate before M2. The explicit
exception below authorized M2 on the two deployed targets, reusing the same
infrastructure/settings. A later explicitly approved third-target restoration
completed the original three-model connections and unchanged-suite comparison.
Live-customization acceptance and destruction remain not run.

**Validation**: Use focused standard-library checks and acceptance scenarios; no new runner, CI integration, or production-hardening program. T001-T015 are complete: all three models passed native text/JSON checks; 52 tests and notebook hygiene passed.

**Approved third-target restoration (2026-11-09)**: After quota was freed, the
user approved deploying the originally planned GPT-5.4 version/capacity through
the existing Bicep and evaluating only it on the existing 14-case frozen suite.
All three runs completed with matching approval and unchanged `newer` roles.
Earlier run artifacts and frozen suite inputs remained byte-identical.
Fresh-kernel three-model rendering and zero-paid-call completed-target resume
passed. Only the three-model portion of T041 is complete; separate live
second-policy/replacement exercises and T045 deletion are still not run.

**Approved M2 amendment (2026-11-05)**: The user explicitly authorized proceeding
without GPT-5.4, with `newer` as generator/tester/judge and bounded paid evaluation
of `older` and `newer` on the same reviewed 14 cases. This overrides the original
three-model prerequisite and role choices below for this run; original
three-model acceptance was deferred at that stage. The later amendment above
authorizes only the original third deployment/evaluation, not destructive
cleanup. Record separate live second-policy/replacement exercises
as not run unless separately executed.

**Verified native release corrections**: category joins use
`dimensions.behavior`, while top-level `behavior` is the policy label; generated
scenario `seed.system_prompt` is removed only in the explicit reviewed copy.
The native test-set stage enables by default and rejects `enabled: true`;
disabled stages use `enabled: false`. Native versioned cache outputs are preserved
before merging. Tests are split across focused `test_*.py` files using the same
standard-library runner, not a new framework.

**Approved amendments (2026-11-05)**: The user authorized two-model verification
while retaining the full three-model M1 gate, then approved replacing key auth
with native Entra after inherited-policy investigation. Bicep disables local auth,
declares developer inference RBAC, and serializes project/model writes. Generated
settings contain no keys/tokens. See the specification clarifications and the
demo's architecture notes for actual state and evidence.

## Format and Path Conventions

- Checklist format: `- [ ] Tnnn [P?] [USn?] Description with exact file path`.
- `[P]` identifies different-file work that can run together after its stated prerequisites. It does not override milestone gates.
- `[US1]` through `[US4]` identify the specification's user stories. Setup, foundational, and polish tasks have no story label.
- Implementation paths are repository-relative Windows paths. All demo changes stay in `demos\assert01-foundry-evaluation\`.
- Keep repeated behavior in `app\assert_lab.py`; serialize edits to that module, each notebook, and `tests\test_assert_lab.py`.
- Use the pinned `assert-ai==0.3.0` release contract, not current-main behavior. ASSERT owns generation, adaptive follow-ups, target inference, and judging.
- Live tasks require explicitly confirmed subscription/model inputs, adequate quota, and authorization for paid calls. Record blockers; never substitute models, providers, authentication, API versions, or fabricated results silently.

## Phase 1: Setup

**Purpose**: Establish the self-contained demo and its dependency manifest without implementing evaluation behavior.

- [x] T001 Copy `demo-template\` into `demos\assert01-foundry-evaluation\`, retaining the planned layout, `demos\assert01-foundry-evaluation\outputs\.gitkeep`, and `demos\assert01-foundry-evaluation\scripts\.gitkeep`; add the planned `data\`, `tests\`, and `tests\fixtures\` directories without adding services or a generic framework.
- [x] T002 Author `demos\assert01-foundry-evaluation\requirements.txt` for Python 3.11 or later with `assert-ai==0.3.0`, the Azure identity/resource/Cognitive Services management SDKs, python-dotenv, and pandas; use ASSERT's existing YAML/provider dependencies and standard-library unittest rather than adding another runner or proxy. Install only after this manifest exists.
- [x] T003 [P] Populate `demos\assert01-foundry-evaluation\metadata.json` using exactly the fields in `demo-template\metadata.json`; describe one hypothesis: reviewed policy tests can reveal violations and unnecessary refusals across three supported model generations, without claiming production certification or completed live validation.

**Checkpoint**: Demo skeleton and manifest exist. After T001, T002 and T003 can run independently.

## Phase 2: Foundational

**Purpose**: Provide the shared executable-resolution and local artifact/environment boundaries needed by every story.

- [x] T004 [P] Create `demos\assert01-foundry-evaluation\app\notebook_helpers.py` from the speech demo's executable-path-only Azure CLI resolver pattern; keep authentication in setup cells and do not add a shared Azure subprocess wrapper.
- [x] T005 [P] Establish `demos\assert01-foundry-evaluation\app\assert_lab.py` with deterministic demo-root/artifact-path resolution, generated-environment loading, and secret-free deployment metadata/alias loading; resolve runtime artifacts to absolute paths under `outputs\generated\`, fail on missing prerequisites, and never print credential-bearing mappings or provide alternate connection fallbacks.

**Checkpoint**: Both foundations are complete before US1. Do not add policy generation, inference, or judging here.

## Phase 3: User Story 1 - Prepare the Lab and Three Models (Priority: P1) - MVP

**Goal**: A learner can prepare the environment, provision the copied Foundry design, and obtain real responses from three distinct supported model generations without exposing credentials.

**Independent Test**: Complete setup and deployment using confirmed Azure inputs; identify actual model names/versions and obtain one native-provider response per deployment. Verify infrastructure documentation, credential-output inspection, and notebook hygiene before handoff, then stop. Verify the standard cleanup notebook is unchanged; execute its destructive acceptance only after the dependent evaluation exercises finish.

### Implementation and Validation

- [x] T006 [P] [US1] Copy/adapt `demos\speech01-foundry-speech\notebooks\00_setup.ipynb` into `demos\assert01-foundry-evaluation\notebooks\00_setup.ipynb`, preserving the ordered environment/kernel, Azure authentication/optional subscription selection, and dependency-installation steps; change only demo identity, dependency-required prerequisite text, and continuation links, with small single-purpose cells.
- [x] T007 [P] [US1] Adapt `demos\gpt4o01-text-image-audio\infra\main.bicep` into `demos\assert01-foundry-evaluation\infra\main.bicep`: one AIServices S0 account/project, stable `2026-09-01` Cognitive Services APIs, full three-model selection or explicitly approved two-model subset, public access, `disableLocalAuth: true`, scoped developer inference RBAC, verified GlobalStandard, and NoAutoUpgrade. Require explicit versions/capacities, serialize project/model writes, and emit no credentials.
- [x] T008 [P] [US1] Copy `demos\speech01-foundry-speech\notebooks\X_destroy.ipynb` verbatim to `demos\assert01-foundry-evaluation\notebooks\X_destroy.ipynb`; do not change its confirmation flags, subscription behavior, deletion sequence, or purge logic.
- [x] T009 [P] [US1] Document non-secret generated variables in `demos\assert01-foundry-evaluation\env\.env.example`: subscription/group/location/account/project/endpoints/API version, `ASSERT_AZURE_USE_AAD=1`, `AZURE_TOKEN_CREDENTIALS=AzureCliCredential`, and the three target alias names. Clearly document that an explicitly skipped alias is omitted; never store keys/tokens.
- [x] T010 [US1] Implement subscription/model selection and the single Bicep deployment path in `demos\assert01-foundry-evaluation\notebooks\01_deploy_infra.ipynb`. Prefer explicit `AZURE_SUBSCRIPTION_ID`; otherwise locate an existing target group or require explicit subscription selection, never the first enabled subscription. Confirm current lifecycle, catalog/version/SKU support, capacity units/increments, quota, and effective inherited policy for the selected scope before provisioning. Use SDKs where supported and the existing narrow CLI/Bicep pattern with captured failure output; do not mutate network rules or silently replace blocked inputs.
- [x] T011 [US1] Export actual nested SDK resource/deployment metadata from `demos\assert01-foundry-evaluation\notebooks\01_deploy_infra.ipynb` to ignored `env\.env` and `outputs\generated\deployment.json` under the demo. Generate only non-secret Entra settings; do not fetch account keys. Enforce three distinct planned identities and explicitly record any skipped deployment/reason; never fabricate its active alias.
- [x] T012 [US1] Implement **Connect models** in `demos\assert01-foundry-evaluation\notebooks\02_configure.ipynb` and `app\assert_lab.py`: load generated explicit Entra/Azure CLI settings before native imports, show actual identities, and verify native `azure/gpt5_series/<deployment-name>` text/structured output with API `2024-10-21`. Use a finite 4,096-token reasoning-inclusive budget and native token refresh, with no custom client, auth fallback, or catch-and-explain wrapper.
- [x] T013 [US1] Cover the infrastructure/environment contracts in `demos\assert01-foundry-evaluation\tests\test_assert_lab.py`: generated required settings and aliases, distinct model metadata, absolute artifact paths, missing-prerequisite failures, and absence of credential fields in non-secret outputs. Check setup flow against the speech source and destroy-notebook byte equality; keep these local checks independent of paid calls.
- [x] T014 [US1] Validate M1 locally using `demos\assert01-foundry-evaluation\requirements.txt`, `demos\assert01-foundry-evaluation\tests\test_assert_lab.py`, and `demos\assert01-foundry-evaluation\infra\main.bicep`: install in the demo environment, run `pip check`, `python -m assert_ai.cli --help`, focused unittest discovery, and Bicep compilation to `demos\assert01-foundry-evaluation\outputs\generated\main.json`. Inspect execution outputs before existing pre-commit cleanup on all five notebooks; rerun hooks/tests after normalization. Provide usable M1 README instructions and actual versions/evidence in `docs\architecture-notes.md`; local checks do not pass the live three-model gate.
- [x] T015 [US1] Complete full live M1 acceptance through `demos\assert01-foundry-evaluation\notebooks\01_deploy_infra.ipynb` and **Connect models** in `notebooks\02_configure.ipynb`: verify inherited policy, all three actual identities/settings and real native responses, inspect output streams including metadata export before stripping, verify ignored artifacts, repeat hygiene/source checks, and record actual evidence in `docs\architecture-notes.md`. **Verified 2026-11-09:** all three actual models passed native text/strict-JSON using the approved Entra path; account/project and earlier identities were preserved; source/hygiene and credential inspection passed. M2 and this third-target follow-up were separately authorized.

**Milestone M1 gate and mandatory stop**: T001-T015 must pass, including live T015, infrastructure documentation, credential-output inspection, and applicable notebook-hygiene checks. Public catalog research, fixture tests, and successful Bicep compilation alone cannot pass this gate. End Run 1 here even when M1 passes; US2-US4 require a separate explicit implementation request. Preserve the recorded environment and ignored generated settings for M2 rather than running destruction here; do not put credentials in the handoff report.

## Phase 4: User Story 2 - Define a Policy and Approve Tests (Priority: P1)

**Goal**: A learner can edit policy/settings, generate and inspect prompts and adaptive scenarios, add handwritten cases, and explicitly approve immutable inputs before target test inference.

**Independent Test**: Generate 8 prompts and 4 scenarios with both classifications in each type; inspect the reviewed taxonomy, add one permitted and one prohibited case, and approve all 14 without starting target test inference. Editing approved inputs must require fresh review.

### Implementation and Validation

- [x] T016 [P] [US2] Author `demos\assert01-foundry-evaluation\data\policies\customer-support.yaml` with the data-model rules: `id` is a "Stable non-secret identifier, valid as part of an ASSERT suite name"; `revision` is a "Learner-controlled revision; content hashes still detect edits without a revision change"; `context` is "Non-empty application context and capabilities"; `prohibited` has "At least one concrete prohibited behavior"; `permitted` has "At least one concrete permitted behavior". Use synthetic refund explanations and explicitly state that no refund-issuing tool exists.
- [x] T017 [P] [US2] Author `demos\assert01-foundry-evaluation\data\lab.yaml` and an initially empty `demos\assert01-foundry-evaluation\data\extra-tests.jsonl`. Preserve `policy_path`: "Selected policy under the demo's data directory"; `extra_tests_path`: "Editable native JSONL additions; initially empty"; positive-integer defaults `prompt_count: 8`, `scenario_count: 4`, and `max_turns: 3`, where "one turn is one user/target exchange". Use "Intermediate deployment alias" for generation/tester/judge roles and "Exactly three distinct deployed model identities for initial acceptance" for `comparison_targets`; include no credentials.
- [x] T018 [P] [US2] Create small pinned-release taxonomy and native-case fixtures in `demos\assert01-foundry-evaluation\tests\fixtures\taxonomy.json` and `demos\assert01-foundry-evaluation\tests\fixtures\test_set.jsonl`, covering both case types/classifications and clearly identified synthetic invalid variations for later checks; do not present fixtures as live generation results.
- [x] T019 [US2] Implement policy/settings/taxonomy/case validation in `demos\assert01-foundry-evaluation\app\assert_lab.py`, covering the quoted authoring constraints in T016-T017. For native cases enforce `type`: "`prompt` or `scenario`"; `test_case_id`: "Unique and stable; generated IDs retained, handwritten IDs use a clearly distinct prefix"; `behavior`: "Exact category name in the approved taxonomy"; `seed.title`: "Human-readable review label"; `seed.description`: "Full user prompt or adaptive scenario definition"; `seed.system_prompt`: "Omit for this lab; the shared target policy prompt is authoritative"; optional `dimensions`: "Native generation dimensions where emitted". Reject empty descriptions, tools, invented input permissibility/credential fields, duplicate categories/IDs, unknown joins, and missing/non-boolean taxonomy labels; extend `demos\assert01-foundry-evaluation\tests\test_assert_lab.py` with focused invalid-input checks.
- [x] T020 [US2] Implement secret-free policy rendering and native taxonomy/generation configuration emission in `demos\assert01-foundry-evaluation\app\assert_lab.py`. Render one policy into behavior/context and the effective target prompt; use only supported `ModelConfig` fields (`name`, `temperature`, `max_tokens`, `reasoning_effort`), omit unverified temperature/reasoning overrides, set role mappings explicitly, and write absolute paths under `demos\assert01-foundry-evaluation\outputs\generated\configs\`. Use the evaluation contract's consumed path keys, not `file_path` or `${...}` interpolation.
- [x] T021 [US2] Add **Define the policy** and **Configure the evaluation** sections to `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`, exposing editable input locations, model roles, selected target, native boolean `policy_violation`/`overrefusal` rules, any-applicable-response meaning, counts, turn limit, and saved-result paths before paid inference; explain that scenarios are objectives/constraints, not fixed transcripts.
- [x] T022 [US2] Implement the separate native taxonomy and generation passes in `demos\assert01-foundry-evaluation\app\assert_lab.py` and **Generate and review tests** in `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`. Invoke `sys.executable -m assert_ai.cli run --config <absolute-path> --concurrency 1` from the demo root with the generated process environment and visible failures. Disable inference/judging in both passes; disable test generation during taxonomy review and systematization during case generation. Pause to review exactly two starter categories, one boolean label of each kind; disable web search and use native behavior-stratified sampling to generate 8 prompts (4/4 assignments) and 4 scenarios (2/2). Inspect actual semantics/counts without fabricated rows or unbounded regeneration.
- [x] T023 [US2] Implement handwritten-case merging in `demos\assert01-foundry-evaluation\app\assert_lab.py` and explain the native prompt/scenario JSONL format in **Generate and review tests** in `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`; preserve the separately saved generated 12 cases, retain stable IDs, validate additions against the reviewed taxonomy, and show one permitted plus one prohibited addition producing 14 without regenerating or editing execution logic.
- [x] T024 [US2] Implement immutable candidate/approved suite snapshots and `approval.json` in `demos\assert01-foundry-evaluation\app\assert_lab.py`: policy identity/revision plus content-derived suite suffix, explicit `reviewed: true`, timestamp, byte SHA-256 hashes of policy/taxonomy/tests, canonical secret-free shared-settings hash, effective policy-prompt hash, expected IDs/type/classification counts, and ASSERT version. Require both classifications within each type. Changed policy/taxonomy/cases/shared tester/judge/rubric/turn settings require a distinguishable candidate and fresh approval; generation-only changes need not invalidate an unchanged frozen set. Preserve old snapshots/runs; never silently reseal an in-place edit.
- [x] T025 [US2] Wire explicit review/approval and snapshot selection into **Generate and review tests** in `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`; make the generated-candidate versus approved-input boundary visible and add focused checks to `demos\assert01-foundry-evaluation\tests\test_assert_lab.py` for exactly 8+4 generated cases, 14 after additions, coverage rejection, stable IDs, hash changes without revision changes, retained earlier suites, and approval invalidation. Do not hash adaptive transcripts or enable target inference here.
- [x] T026 [US2] Validate US2 locally and through real native generation using `demos\assert01-foundry-evaluation\tests\test_assert_lab.py` and **Define the policy**, **Configure the evaluation**, and **Generate and review tests** in `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`: inspect taxonomy and generated content, add the two cases through inputs, approve the 14-case snapshot, and verify no target test inference ran. Record actual outcomes/blockers in `demos\assert01-foundry-evaluation\docs\architecture-notes.md`.

**Checkpoint**: One reviewed 14-case suite exists with immutable snapshots and explicit approval. Adaptive runtime messages have not been generated or approved in advance.

## Phase 5: User Story 3 - Evaluate and Understand Results (Priority: P1)

**Goal**: A learner runs ASSERT on one approved target, reopens saved artifacts, and understands correct prompt/conversation metrics and real failure evidence.

**Independent Test**: Execute one 14-case approved run, reopen it from disk, reconcile every displayed numerator/denominator, and identify saved evidence for any actual failure. Local fixtures must verify earlier conversational failure followed by compliance and incomplete/N/A accounting without requiring a live model to exhibit those edge cases.

### Implementation and Validation

- [x] T027 [P] [US3] Add pinned-release native-result fixtures in `demos\assert01-foundry-evaluation\tests\fixtures\inference_set.jsonl`, `demos\assert01-foundry-evaluation\tests\fixtures\scores.jsonl`, and `demos\assert01-foundry-evaluation\tests\fixtures\metrics.json`; include full transcript/citation shapes, both classifications/types, early failure then compliance, multiple failures in one conversation, inference errors/missing rows, judge failures/skips/omitted rows, semantic N/A, zero denominators, and no-failure variants.
- [x] T028 [P] [US3] Extend native run-configuration emission in `demos\assert01-foundry-evaluation\app\assert_lab.py` for explicit disabled systematization/test generation, approved `inference.test_set_path`, shared `target.system_prompt`, fixed tester/judge routes/settings, `max_turns: 3`, target-specific `inference.save_dir`, and explicit `judge.inference_set_path`, `judge.taxonomy_path`, and `judge.save_dir`. Use native boolean policy-violation/overrefusal full-transcript judging with the same policy-based any-applicable-response rubric; do not build a replacement conversation or scoring engine.
- [x] T029 [US3] Implement the pre-inference approval/provenance gate in `demos\assert01-foundry-evaluation\app\assert_lab.py`: recompute approved artifact/settings/prompt hashes, validate IDs/counts and actual target deployment/version, and verify tester/judge/rubric/turn-limit/ASSERT/provider settings. Allocate a unique target/run ID and secret-free `provenance.json` beside native outputs; refuse unapproved or changed inputs before invoking target inference, preserve prior runs, and do not rely on cache hits or `--force-stage`.
- [x] T030 [US3] Add **Run the evaluation** to `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`, using the gate and selected-interpreter CLI boundary from `demos\assert01-foundry-evaluation\app\assert_lab.py`. Run only native inference/judging with finite configured turns, retain native `manifest.json`, literal secret-free `config.yaml`, `inference_set.jsonl`, `scores.jsonl`, and `metrics.json`, and preserve complete adaptive transcripts and native errors. Surface nonzero CLI exits without fake completion, automatic retries/fallbacks, or catch-and-explain-only wrappers.
- [x] T031 [US3] Implement the saved-result loader in `demos\assert01-foundry-evaluation\app\assert_lab.py`, joining approved tests/taxonomy, inference, and scores by case ID; reject duplicates/unknown schema and read booleans from `verdict.dimensions`, not row-level generation `dimensions`. Reconcile expected IDs against missing inference and scores, recognize `ok`, `judge_failed`, `scoring_skipped`, and `filter_skipped`, and preserve native errors, applicability, justifications, transcript identities, and citations. Extend `demos\assert01-foundry-evaluation\tests\test_assert_lab.py` with fixture-based contract checks.
- [x] T032 [US3] Implement interaction-type-specific metrics in `demos\assert01-foundry-evaluation\app\assert_lab.py` and verify them in `demos\assert01-foundry-evaluation\tests\test_assert_lab.py`. Violation numerator: "Prohibited cases with a valid applicable violation verdict of true"; denominator: "Prohibited cases with valid applicable boolean violation verdicts". Unnecessary-refusal numerator: "Permitted cases with a valid applicable overrefusal verdict of true"; denominator: "Permitted cases with valid applicable boolean overrefusal verdicts". Count each conversation once, retain earlier failures despite later compliance, separately show failed/missing/skipped/N/A outcomes, and show zero-denominator rates as unavailable rather than `0%`.
- [x] T033 [US3] Implement real failure-evidence selection in `demos\assert01-foundry-evaluation\app\assert_lab.py` and cover it in `demos\assert01-foundry-evaluation\tests\test_assert_lab.py`; link saved prompts/scenarios and responses/full transcripts to native justifications and offending-turn references, preserve multiple relevant turns without multiplying case weight, and return no invented examples when no failures exist. Explain judge assessments require human interpretation; do not flatten conversations to their final answer or rescore them in custom code.
- [x] T034 [US3] Add **Show results** to `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`, loading saved artifacts into Python and displaying separate prompt/conversation tables with actual model/version/run, approved/attempted/scored counts, numerators, applicable denominators, rates, distinct error/missing/N/A accounting, and reopenable real failure evidence. Show native aggregate metrics as supporting evidence only; do not substitute them for the required filtered rates or claim a partial run completed.
- [x] T035 [US3] Run focused US3 checks from `demos\assert01-foundry-evaluation\tests\test_assert_lab.py` and a real first-target 14-case evaluation through **Run the evaluation** and **Show results** in `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`; reopen the saved run, reconcile all displayed counts/rates, verify adaptive transcripts stay within the configured maximum, and record actual outcomes/blockers in `demos\assert01-foundry-evaluation\docs\architecture-notes.md`. Fixture verification, not fabricated live examples, proves the early-failure edge case.

**Checkpoint**: One identifiable native run can be inspected independently from disk, with correctly weighted metrics and explicit incomplete-result handling.

## Phase 6: User Story 4 - Compare Three Model Generations and Repeat (Priority: P2)

**Goal**: A learner compares three real models on identical approved inputs and can change policy or target through documented inputs without changing execution logic.

**Independent Test**: Complete the remaining targets on the same 14 approved IDs; verify shared provenance and show all three models side by side. A changed policy creates a separate reviewed suite; mismatched or incomplete runs must not appear as an equivalent completed comparison.

### Implementation and Validation

- [x] T036 [US4] Implement comparison eligibility and shared-provenance checks in `demos\assert01-foundry-evaluation\app\assert_lab.py`: require matching approved policy/taxonomy/test/settings/prompt hashes, policy revision, tester/judge identities/settings, rubric, turn limit, ASSERT/provider versions, and native completion/case accounting; allow only target identity to differ. Do not compare adaptive transcript hashes or mutate earlier snapshots/runs.
- [x] T037 [US4] Add **Compare models** to `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`, retaining complete matching selected runs and previewing missing targets without paid calls; execute native inference/judging only for missing targets in the separately run paid cell, using the same frozen suite. Display the reused approval and case counts first, never regenerate tests between targets, and assign fresh run IDs for intentional repeats.
- [x] T038 [US4] Wire descriptive side-by-side presentation through `demos\assert01-foundry-evaluation\app\assert_lab.py` and **Compare models** in `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`: show all three actual model identities/versions and run IDs, separate prompt/conversation counts/rates, failure accounting, and saved evidence links; visibly label incomplete and non-equivalent runs. Do not introduce baseline selection, automatic regression labels, pass/fail thresholds, or significance claims.
- [x] T039 [P] [US4] Document policy replacement, both handwritten interaction formats, and explicit supported-target replacement in `demos\assert01-foundry-evaluation\README.md` and `demos\assert01-foundry-evaluation\notebooks\02_configure.ipynb`. Keep all changes in the documented policy/settings/deployment inputs: a second policy gets new taxonomy/tests/review and a distinct suite, while a target-only replacement reuses the original frozen tests and fixed tester/judge settings. Preserve previous results and require explicit selection of an available supported alternative, not a silent fallback or an unplanned fourth deployment.
- [x] T040 [P] [US4] Extend `demos\assert01-foundry-evaluation\tests\test_assert_lab.py` with matching/mismatching comparison provenance, incomplete native runs, retained original suites, policy-content changes without revision changes, configuration-only target replacement, and adaptive transcripts that legitimately differ under matching scenario/tester settings; verify descriptive output has no baseline/regression/pass-fail behavior.
- [ ] T041 [US4] Execute live M2/customization acceptance through `demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb`: verify all three initial targets evaluated the same 14 IDs without regeneration, default conversations never exceed 3 exchanges, rates reconcile, and real failure examples link to saved evidence. Exercise a second policy with fresh review and distinguishable saved results, then an explicitly available supported target replacement on the original frozen suite. Record each executed, blocked, or unexecuted exercise separately in `demos\assert01-foundry-evaluation\docs\architecture-notes.md`; do not provision another model silently or call partial comparison success.

**Original Milestone M2 gate**: The three-model comparison passed; separate live
second-policy/replacement exercises remain not run, so T041 stays unchecked.
**Approved current M2 verification passed on 2026-11-09**: all three models scored
the same 14 reviewed cases, with matching provenance and reconciled metrics;
fresh-kernel HTML result/comparison rendering and 49 focused tests passed.

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Finish the learning materials and existing quality gates, verify credential handling, and clean up resources only after dependent live work ends.

- [x] T042 [P] Extend the M1 documentation from T014 in `demos\assert01-foundry-evaluation\README.md`, `demos\assert01-foundry-evaluation\metadata.json`, and `demos\assert01-foundry-evaluation\docs\architecture-notes.md` with the completed eight-section journey in order, hypothesis/outcomes, source-copy provenance, prerequisites, budget/role/quota costs, review/execution boundary, synthetic-data and judge limitations, customization, immutable artifacts, and cleanup. Retain the standard destroy notebook's recorded-subscription prerequisite and confirmation-flag warnings; distinguish researched candidates, M1 handoff evidence, and later live acceptance actually run.
- [x] T043 [P] Repeat final focused local validation against `demos\assert01-foundry-evaluation\requirements.txt`, `demos\assert01-foundry-evaluation\tests\test_assert_lab.py`, `demos\assert01-foundry-evaluation\infra\main.bicep`, and all five notebooks under `demos\assert01-foundry-evaluation\notebooks\`: demo-environment `pip check`, native CLI help, unittest discovery, Bicep build, setup-flow verification, and verbatim destroy comparison. Before clearing/stripping outputs, inspect all available notebook execution outputs for credentials using the full scope in T044, explicitly including deployment outputs; fix exposure at its source and rerun affected steps without echoing secret values. Then run the existing pre-commit notebook cleanup, retain required output/execution-count/kernel-display-name stripping, and rerun hooks if they modify notebooks; do not defer checks to this task when an earlier milestone needs its own handoff.
- [x] T044 Inspect tracked demo inputs plus `demos\assert01-foundry-evaluation\env\.env`, `demos\assert01-foundry-evaluation\outputs\generated\configs\`, native run `config.yaml` snapshots, and all five notebooks under `demos\assert01-foundry-evaluation\notebooks\` (`00_setup.ipynb`, `01_deploy_infra.ipynb`, `02_configure.ipynb`, `03_assert_flow.ipynb`, and `X_destroy.ipynb`) for credential exposure without echoing secret values. Verify execution outputs were inspected before clearing/stripping at the applicable M1/T015 and M2/T043 checks; stripped outputs alone are not evidence of no earlier exposure. Verify existing ignore rules cover environment/generated artifacts recursively; fix any exposure at its source and rerun affected checks rather than adding messaging-only wrappers.
- [ ] T045 After live evaluation/customization work finishes, explicitly verify/select the subscription recorded in `demos\assert01-foundry-evaluation\env\.env` and run the unchanged `demos\assert01-foundry-evaluation\notebooks\X_destroy.ipynb` flow; verify resource absence, Cognitive Services soft-delete purge, and group cleanup. Inspect its new execution outputs for credentials before stripping, then rerun the existing focused notebook-cleanup check so the final handoff remains clean after destruction. Preserve local ignored run evidence and record actual cleanup outcomes/blockers in `demos\assert01-foundry-evaluation\docs\architecture-notes.md`; never run destruction against an assumed subscription.
- [x] T046 Finalize the acceptance evidence in `demos\assert01-foundry-evaluation\docs\architecture-notes.md` against every FR/SC row below: list local checks, live M1, reviewed generation, each target/run, customization, secret inspection, and cleanup as passed, blocked, or not run. Identify the Bicep/shared/local scope of upstream fixes, justify any remaining workaround and removal plan, and confirm no catch-and-explain-only fix replaced remediation; do not mark unexecuted live acceptance complete.

## Dependencies and Execution Order

### Story and Milestone Graph

```text
Setup (T001-T003)
  -> Foundations (T004-T005)
  -> US1 infrastructure (T006-T015)
  -> LIVE M1 GATE + documentation / output inspection / notebook hygiene
  -> END RUN 1: STOP EVEN ON SUCCESS
  -> SEPARATE EXPLICIT REQUEST FOR RUN 2; reuse recorded M1 resources/settings
  -> US2 policy / generation / approval (T016-T026)
  -> US3 one-target execution / results (T027-T035)
  -> US4 three-target comparison / customization (T036-T041)
  -> LIVE M2 GATE
  -> Polish / quality / secret inspection (T042-T044)
  -> Cleanup (T045)
  -> Evidence handoff (T046)
```

Stories are separately verifiable increments, not independent code branches: US2 needs deployed models; US3 needs an approved suite; US4 needs working saved-run loading. No generic "all stories in parallel" assumption applies.

### Task Prerequisites

All tasks in a later phase require the preceding phase's checkpoint. Entering US2 additionally requires a separate explicit request for Run 2; a passed M1 gate does not authorize continuing automatically. Reuse M1's recorded infrastructure and generated settings rather than automatically redeploying. Within each phase, use these additional prerequisites:

| Phase | Prerequisite edges |
|---|---|
| Setup | T001 -> T002 and T003 |
| Foundations | T004 and T005 are independent after setup |
| US1 | T006/T007/T008/T009 -> T010 -> T011 -> T012 -> T013 -> T014 -> T015 |
| US2 | Passed M1 gate + separate Run 2 request -> T016/T017/T018 -> T019 -> T020 -> T021 -> T022 -> T023 -> T024 -> T025 -> T026 |
| US3 | T027 and T028 can start together; T028 -> T029 -> T030; T027/T030 -> T031 -> T032 -> T033 -> T034 -> T035 |
| US4 | T036 -> T037 -> T038 -> T039 and T040; T039/T040 -> T041 |
| Polish | T042 and T043 can start together; T042/T043 -> T044 -> T045 -> T046 |

These are conservative integration checkpoints as well as file/data dependencies. Do not overlap edits to shared helpers/notebooks/tests merely because the tasks concern different stories.

### Parallel Execution Examples

- **Setup/foundations**: After T001, author requirements (T002) while filling metadata (T003). After setup, implement the CLI resolver (T004) and root/environment boundary (T005) in separate modules.
- **US1**: After foundations, adapt setup (T006), Bicep (T007), destroy copy (T008), and environment example (T009) concurrently; join before the deployment notebook.
- **US2**: After live M1 and a separate explicit Run 2 request, author the starter policy (T016), lab settings/empty additions (T017), and native input fixtures (T018) concurrently; then serialize shared validation/configuration/notebook work.
- **US3**: After approved-suite acceptance, prepare result fixtures (T027) while extending run-config emission (T028); join both before loader validation. Serialize later helper and notebook edits.
- **US4**: After comparison presentation (T038), write customization instructions (T039) while extending comparison checks (T040); both finish before live customization.
- **Polish**: Complete prose/metadata (T042) while running code/notebook-focused checks (T043); join before secret inspection and cleanup.

## Requirement and Acceptance Coverage

| Specification | Implementation / validation tasks |
|---|---|
| FR-001 | T001-T015; mandatory validated M1 handoff and separate Run 2 request before T016 |
| FR-002 | T006, T012, T021-T022, T025, T030, T034, T037-T038, T042 |
| FR-003 | T007, T010-T012, T015, T038, T041 |
| FR-004 | T005, T007, T009, T011-T015, T020, T029-T030, T043-T045 |
| FR-005 | T016-T017, T019-T021, T039, T041 |
| FR-006 | T017, T020-T021, T028-T029 |
| FR-007 | T022, T024-T026, T029-T030 |
| FR-008 | T017-T019, T023, T025-T026, T039 |
| FR-009 | T019, T023-T025, T029, T036-T037 |
| FR-010 | T020-T021, T028-T029, T036 |
| FR-011 | T024, T029-T031, T034-T035 |
| FR-012 | T027, T031-T032, T034-T035 |
| FR-013 | T033-T035, T038, T042 |
| FR-014 | T029, T036-T038, T040-T041 |
| FR-015 | T024-T025, T029, T036, T039-T041 |
| FR-016 | T006, T009, T014-T015, T021-T023, T034, T039, T042, T045 |
| FR-017 | T017, T019, T021-T026, T028, T030, T035, T041 |
| FR-018 | T005, T010, T012-T015, T019, T022, T029-T035, T038 |
| FR-019 | T018-T019, T022-T028, T030-T035, T038-T041 |
| FR-020 | T021, T028-T031, T033, T035-T036, T041 |
| FR-021 | T027-T028, T031-T035 |
| FR-022 | T036, T038, T040-T042 |
| SC-001 | T011-T015: three real responses with generated credentials and recorded identities |
| SC-002 | T006, T012, T021-T026, T029-T030, T034, T037, T042: ordered sections and approval gate |
| SC-003 | T022-T026, T028, T035, T041: exact 8+4 -> 14 counts, both classifications/types, bounded turns, 14 per target |
| SC-004 | T024, T029, T036-T037, T040-T041: identical frozen/shared provenance, no regeneration |
| SC-005 | T027, T031-T035, T041: exact case-weighted denominators/rates and separate failed/N/A outcomes |
| SC-006 | T024-T025, T039-T041: second policy requires a distinct reviewed suite, preserving original results |
| SC-007 | T011-T015, T020, T029-T030, T043-T045: no tracked or notebook-output credentials; inspect before stripping at each handoff |
| SC-008 | T033-T038, T040-T041: three-model display, saved failure evidence, explicit incomplete state |

## Implementation Strategy

1. **Run 1 - Infrastructure MVP only**: Complete T001-T015, including usable infrastructure documentation, real three-model connectivity, generated settings, pre-strip credential-output inspection, notebook hygiene, and a non-secret handoff report. Stop after T015 even on success. If live M1 is blocked, report the blocker instead of starting functionality or declaring the environment delivered.
2. **Run 2 - Functionality, only on a separate explicit request**: Reuse the infrastructure and generated settings recorded at M1; do not automatically redeploy. Complete US2 and demonstrate generated content, the two handwritten additions, and explicit approval without target test inference.
3. **Single-target evaluation increment**: Complete US3 and demonstrate saved, reopenable evidence with reconciled prompt/conversation metrics.
4. **Controlled comparison increment**: Complete US4 on the frozen suite, then demonstrate policy/model-input customization while retaining prior results.
5. **Finish and clean up**: Complete existing quality gates, inspect credential handling, run the standard delete/purge path after all live consumers finish, and leave an honest evidence report.

No automatic baseline, regression gate, CI integration, fourth-model provisioning, hosted proxy/application, database, custom conversation engine, or generic evaluation framework is part of this task list.
