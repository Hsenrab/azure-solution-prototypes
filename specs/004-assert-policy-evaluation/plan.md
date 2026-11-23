# Implementation Plan: ASSERT Policy Evaluation Lab

**Feature**: `004-assert-policy-evaluation` | **Date**: 2026-11-05 | **Spec**: [spec.md](./spec.md)

**Working Git branch observed**: `feat/search-vector-contributions`. Spec Kit's active feature identity is independent of the current Git branch; planning does not switch branches.

## Summary

**Approved implementation amendment (2026-11-05):** Use native Entra authentication,
not the initial key-based path: Bicep sets `disableLocalAuth: true` and declares
developer inference RBAC; generated settings select `ASSERT_AZURE_USE_AAD=1` and
`AZURE_TOKEN_CREDENTIALS=AzureCliCredential`. No keys/tokens are stored. The user
also approved two-model verification with GPT-5.4 explicitly skipped for quota.
Full three-model M1 acceptance was incomplete at that stage. Bicep supports this explicit
two-model subset; metadata must identify the skipped model/reason. Serialize
project/model writes in Bicep, and use a finite 4,096-token native connection budget.
These decisions supersede the original key-authentication details below.

**Approved third-target restoration (2026-11-09):** GPT-5.4 quota was freed and
the user approved the original version 2026-03-05 / GlobalStandard capacity 10
through the existing Bicep. All three native connections and 14-case evaluations
now pass. Reuse the original frozen suite and earlier completed runs, retaining
`newer` generator/tester/judge. The unpaid preview identifies only missing
targets; the separate paid cell does not reevaluate completed matching runs.
Live second-policy/replacement acceptance and destruction remain not run.

Create one self-contained notebook-first demo under `demos/assert01-foundry-evaluation/`, delivered as two ordered milestones:

1. Copy and adapt the existing minimal Foundry infrastructure; deploy an account, project, and three supported model generations; generate connection settings and demonstrate a real response from each.
2. Add the eight-section ASSERT learning journey, including editable policies, generated and handwritten tests, explicit review/approval, adaptive conversations, native CLI evaluation, Python result tables, and descriptive three-model comparison.

**Customer problem**: Engineers need an understandable, repeatable way to evaluate a policy against model behavior without rebuilding the evaluation flow for each policy or model.

**Hypothesis**: A learner can prepare three target models, edit a policy, review a small reusable test set, run the same approved prompts/scenarios against each model, and explain policy violations and unnecessary refusals using saved evidence.

Use native ASSERT stages and file formats. A small demo-local helper handles authoring inputs, approval/provenance, and result presentation; it must not become a replacement generation, conversation, or judging engine.

## Technical Context

**Language/Version**: Python >=3.11; implementation verified Python 3.12.10, not every supported runtime; Bicep; YAML/JSON/JSONL.

**Primary Dependencies**: `assert-ai==0.3.0`, its native LiteLLM/Pydantic/PyYAML dependencies, `azure-identity`, `azure-mgmt-resource`, `azure-mgmt-cognitiveservices`, `python-dotenv`, and pandas for small readable result tables. Jupyter kernel setup follows the source notebook. Avoid an additional inference SDK: ASSERT owns the provider client.

**Storage**: Committed synthetic policy/settings; git-ignored generated environment, native artifacts, and editable starter cases inside each suite. The legacy committed extra-test examples are retained but no longer read. No cloud storage or database.

**Testing**: Standard-library `unittest` for demo-local logic and native-contract fixtures; Bicep build; repository `pre-commit` notebook cleanup; focused live smoke/acceptance runs only after explicit subscription and deployment selection.

**Target Platform**: Local VS Code/Jupyter on Windows, with argument-list CLI invocation and paths based on the demo root. Azure hosts model deployments only.

**Project Type**: Learning demo, not a hosted application or evaluation service.

**Performance Goals**: Small bounded first run: 8 prompts + 4 adaptive scenarios; at most 3 exchanges per conversation; initial evaluation concurrency 1. No unsupported wall-clock or dollar-cost guarantee.

**Constraints**: Exactly three distinct supported generations for full initial acceptance; global deployment allowed; native refreshable Entra credentials with no keys/tokens in demo files; explicit test approval; matching comparison provenance; no model/region/authentication fallback, CI integration, automatic regression flags, or pass/fail gates.

**Scale/Scope**: One learner, one synthetic starter policy, one configurable second-policy exercise, three target runs. At defaults, each target receives at most 20 target responses from the 12 main cases (8 + 4 x 3), or 60 across three targets, excluding connection smoke tests. Tester, generation, judging, and provider retry calls incur additional usage. Two fresh editable starter prompts increase case totals to 14 and the default target-response budget to 22 per target; the same approved additions must appear in all three runs.

## Constitution Check

| Principle | Before research | Post-design decision |
|---|---|---|
| I. Existing guidance remains active | Pass: authoring and Foundry skills loaded; repository guidance read | Pass: use the same skills and references during implementation; preserve CI |
| II. Lightweight hypothesis-driven demos | Pass: one customer problem and hypothesis; approved scope | Pass: template-based self-contained demo; no new hosted components |
| III. Infrastructure-first root-cause fixes | Pass: copied Bicep source identified | Pass: auth/network/SKU/version policy in Bicep; notebooks consume outputs |
| IV. Consistent notebook journeys | Pass: setup and destroy sources identified | Pass: setup retains its three ordered steps; destroy copied verbatim; deployment generates environment |
| V. Evidence-based validation | Pass: SC-001 through SC-008 defined | Pass: concrete local checks and independently gated live milestones; no claim that research proves runtime success |

No constitutional exception is requested. The narrowly scoped helper is required because approval fingerprints, custom authoring inputs, and notebook result tables are not complete native ASSERT interfaces; inference, adaptive testing, and scoring remain native.

## Project Structure

### Documentation for This Feature

```text
specs/004-assert-policy-evaluation/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  checklists/
    requirements.md
  contracts/
    infrastructure.md
    evaluation.md
```

`tasks.md` is produced by `/speckit-tasks`, not this planning command.

### Planned Demo Layout

```text
demos/assert01-foundry-evaluation/
  README.md
  metadata.json
  requirements.txt
  app/
    notebook_helpers.py
    assert_lab.py
  data/
    lab.yaml
    policies/
      customer-support.yaml
  docs/
    architecture-notes.md
  env/
    .env.example
  infra/
    main.bicep
  notebooks/
    00_setup.ipynb
    01_deploy_infra.ipynb
    02_configure.ipynb
    03_assert_flow.ipynb
    X_destroy.ipynb
  outputs/
    .gitkeep
    generated/                 # runtime only; already recursively ignored
  scripts/
    .gitkeep
  tests/
    test_assert_lab.py
    fixtures/                  # tiny source-contract fixtures, not claimed live results
```

**Structure decision**: Start from the repository template. Reuse the CLI path resolver pattern. Keep repeated approval, configuration, and results logic in one demo-local module instead of duplicating it across notebooks or creating a repository-wide framework.

## Phase 0: Research Decisions

Detailed evidence, rationale, rejected alternatives, and limits are in [research.md](./research.md).

- Pin ASSERT to a released package and use release-specific source contracts rather than assuming current `main` documentation applies.
- Use a new Foundry account/project pattern and stable resource APIs; adapt the minimal GPT-4o source, not a hosted proxy deployment.
- Select three supported dated model versions spanning older-to-newer releases. The researched public-catalog candidates and runtime access checks are documented separately.
- Use native per-stage enable/disable controls to separate generation from evaluation; do not invent a CLI stop-after flag.
- Keep policy permissibility in native taxonomy categories and join cases by behavior name; reject unknown labels before approval.
- Invoke the native CLI using the selected notebook interpreter: `sys.executable -m assert_ai.cli`. `python -m assert_ai` is not a supported entry point.
- Keep keys/tokens out of demo files and native YAML snapshots. Generated non-secret environment settings select native Entra; ASSERT's provider handles tokens and refresh internally.
- Use the researched `gpt-5`, `gpt-5.4`, and `gpt-5.6-sol` candidates on the documented native `azure/gpt5_series/<deployment-name>` provider route. This preserves three generations without assuming undocumented GPT-6 provider transformations. Exact regional quota/access remains a live prerequisite.

## Phase 1: Design

### Milestone 1 - Infrastructure and Connections

1. Scaffold from the demo template; fill metadata with its exact existing field set.
2. Copy/adapt the minimal Foundry Bicep. Define one account/project and three explicit model inputs, allowing the user-approved two-model partial subset. Declare Entra settings/RBAC and serialized child operations in Bicep.
3. Keep the setup notebook's ordered environment/kernel, Azure authentication/optional subscription selection, and dependency installation steps. Only change demo identity, dependency-driven prerequisite text, and continuation text.
4. In deployment, resolve the explicit subscription, confirm the planned model/version/SKU/capacity inputs against current access and quota, compile/deploy Bicep, and read actual resource/deployment metadata with Python SDKs.
5. Generate ignored non-secret Entra environment settings and actual SDK deployment metadata; do not retrieve keys or persist tokens. Record any explicit skipped model/reason, not a fake active alias.
6. Smoke-test active connections through ASSERT's native text/structured path. These are prerequisites, not policy inference. The two-model verification is partial; full M1 still needs all three.
7. Preserve the standardized cleanup path and document its selected-subscription prerequisite and destructive confirmation flags.
8. Deliver infrastructure instructions and a non-secret handoff report. Inspect execution outputs before stripping, including deployment/metadata export; no keys are retrieved under the approved Entra path. Repeat existing notebook-hygiene checks after live execution.

**Gate M1**: Successful Bicep build plus real deployment and responses from all three selected identities, usable infrastructure documentation, credential-output inspection, and applicable notebook-hygiene checks. If Azure access is unavailable, report M1 blocked/not run; do not mark infrastructure complete from compilation alone.

**Implementation Run 1 ends here**: Scope the first run to T001-T015 in [tasks.md](./tasks.md), then stop even when M1 passes. Preserve the recorded subscription/resource identities, actual deployment/model versions, provider/API and dependency versions, generated-file locations, and resource state in the non-secret handoff report; credentials remain only in ignored environment settings and process environment. Keep resources available for M2 rather than running destruction at this boundary.

Contract: [infrastructure.md](./contracts/infrastructure.md).

### Milestone 2 - Eight-Section Evaluation Journey

**Implementation Run 2**: Explicitly authorized on 2026-11-05 with a narrow
exception to the M1 gate: GPT-5.4 was deferred; evaluate the two deployed
targets and use `newer` for generator/tester/judge. Reuse existing resources and
settings without redeployment. Bounded paid evaluation is authorized. Keep
three-model acceptance visibly deferred for that original run. The later
approved restoration above completes the third target without regenerating
cases or rerunning the earlier targets; destructive cleanup still needs consent.

| Learning section | Notebook / learner action | Persistent output |
|---|---|---|
| 1. Setup | Standard setup; install the pinned ASSERT package in the demo kernel | Isolated environment and registered kernel |
| 2. Connect models | Configure notebook: load generated environment and display non-secret model identities | Deployment metadata consumed |
| 3. Define policy | ASSERT flow notebook: edit the selected policy's context, prohibited behavior, and permitted behavior | Policy YAML |
| 4. Configure evaluation | ASSERT flow notebook: inspect generation budget, model roles, target prompt, rubric, and stage configurations | Secret-free native YAML configs |
| 5. Generate and review tests | ASSERT flow notebook: generate/review taxonomy, generate 8 prompts + 4 adaptive scenarios, generate two editable starters, inspect/customize, confirm review and combine | Reviewed native taxonomy/test set and review hashes |
| 6. Run evaluation | Verify review hashes and automatically freeze inputs on first evaluation; reuse the matching frozen record for native inference + judging across targets | One distinct native run directory per target |
| 7. Show results | Read saved artifacts into Python; show counts, rates, errors, transcripts, and evidence | Native artifacts and small descriptive tables |
| 8. Compare models | Repeat inference + judging on the same approved set for the remaining targets | Three-model comparison with shared-provenance checks |

The infrastructure notebook runs between setup and connections as the prerequisite milestone, not as an alternative evaluation section.

The learner-facing setup ends after model connections in `02_configure.ipynb`.
Policy selection and all evaluation steps live together in `03_assert_flow.ipynb`,
which can be reused for new policies without repeating setup.

#### Authoring and Generation

`data/lab.yaml` selects the policy and exposes counts/model roles/turn limit. The policy is the only source of prohibited/permitted/application instructions; render it into both target instructions and ASSERT's behavior/context.

Use ASSERT systematization and test-generation stages, not an all-handwritten substitute. Pause to inspect taxonomy labels because `permissible` belongs to taxonomy categories, not test input rows. Keep exactly two reviewed starter categories, one permitted and one prohibited. Native stratified behavior sampling assigns 4/4 prompt cases and 2/2 scenarios to those categories. Then inspect generated content. Approval requires exactly the requested generated counts, valid native records, unique IDs, valid taxonomy references, and semantically correct examples of both classifications in both interaction types.

Each new suite has a separate paid native generation pass for two editable starter prompts, stratified against its reviewed taxonomy. Preserve the native output in `generated-extra-tests.jsonl`, and populate the suite-local `extra-tests.jsonl` with distinct `starter-` IDs. The examples are generated from the current policy rather than copied or relabeled from a fixed file. Before approval, rerunning the starter cell validates and reuses existing editable tests with an explicit no-generation message and redisplays their table/link without paid calls or writes. Never overwrite editable tests or approved suites; file links and merging never regenerate them.

Learners may customize those examples or append handwritten additions with `manual-` IDs using ASSERT's native JSONL shape. Do not silently drop malformed cases or reinterpret unknown categories as permitted. Correct review inputs rather than launching an unbounded regeneration loop. Learners can raise the documented budgets explicitly.

#### Execution and Reproducibility

Use one approved suite and new target-specific run IDs. Evaluation configurations explicitly disable systematization/test generation and point inference at the approved artifacts; do not rely only on cache hits or use `--force-stage`.

Preserve approved suite inputs with their runs. Later test/policy/shared-setting edits start a distinguishable candidate suite and fresh approval; do not overwrite the artifacts needed to understand previous runs.

Before each paid run, verify the approved hashes, effective target policy, shared tester/judge/rubric settings, turn limit, and actual deployment metadata. Only the target deployment changes between the three comparison configurations.

Native adaptive testing owns follow-ups and stops within the configured maximum. Save complete transcripts. Identical reviewed scenarios and tester settings do not imply identical messages or deterministic conversations.

#### Judging and Display

Use native `policy_violation` and `overrefusal` boolean dimensions and full-transcript judging. Apply explicit policy-based rubrics: any applicable failing target response flags the case, even if a later response complies. Preserve native rationale/citation evidence.

The small results loader derives the requested display counts by joining native records with the approved taxonomy/test set. Native score verdicts live under `verdict.dimensions`; row-level `dimensions` are generation factors. Show prompt and conversation summaries separately. Cross-check native aggregate results where corresponding metrics are available; do not relabel an unfiltered native aggregate as the requested permitted/prohibited rate.

Missing/failed/non-applicable outcomes remain outside valid scored denominators and visibly distinct from compliant cases. Unknown schema or duplicate records are errors, not silent defaults. A zero denominator is unavailable. An incomplete run cannot masquerade as a completed comparison.

Show side-by-side results and real failure examples only. Do not introduce a baseline selector, statistical-significance claim, automatic regression flag, pass/fail threshold, or CI gate.

Contracts: [data-model.md](./data-model.md) and [evaluation.md](./contracts/evaluation.md).

## Validation and Requirement Traceability

### Local Checks During Implementation

- Run applicable checks before each implementation-run handoff, not only after M2. Inspect all available notebook execution outputs for credentials before clearing/stripping them, explicitly including deployment outputs; repeat notebook hygiene after live M1 execution and after final cleanup. Stripped outputs alone do not prove that earlier displayed outputs contained no secrets.
- Resolve/install dependencies only in the demo environment after its manifest is authored. Record installed ASSERT and provider versions.
- Run `python -m unittest discover -s tests -p "test_*.py"` from the demo root.
- Fixtures must cover both native case kinds and labels; duplicate/unknown behavior IDs; policy changes without revision changes; approval invalidation; exactly 8+4 generated cases and 14 after additions; matching versus mismatching comparison provenance.
- Results fixtures must cover an earlier conversational failure followed by compliance, multiple failures counted once, missing inference/scores, judge failure/skipped status, semantic N/A, zero denominators, and no observed failure examples.
- Verify that the raw CLI configuration snapshots contain no secret fields or credential values and that execution uses the selected interpreter/environment rather than a global CLI.
- Build the demo Bicep. Use existing pre-commit cleanup on changed notebooks; keep output/execution-count metadata stripped and kernel display-name metadata removed.
- Compare the destroy notebook with the speech source verbatim; verify setup retains the source flow and only authorized substitutions.

### Acceptance Matrix

| Spec coverage | Evidence required |
|---|---|
| FR-001, FR-003, FR-004; SC-001 | Gate M1: real three-model deployment/responses, recorded versions, no secret exposure |
| FR-002, FR-016; SC-002 | Walk through all eight sections using documented headings, no target test execution before approval |
| FR-005 through FR-010, FR-017, FR-019; SC-003 | Edit policy; generate/review 8+4 cases; add two; all 14 appear in every target run |
| FR-014, FR-015, FR-020; SC-004 | Identical policy/test/settings hashes and max-turn bounds; no regenerated scenarios between runs |
| FR-011 through FR-013, FR-018, FR-021; SC-005 | Reconcile displayed numerators/denominators with saved records and errors; validate any-turn conversation scoring |
| FR-005, FR-015; SC-006 | Select a second synthetic policy through inputs; obtain a new distinguishable suite and fresh approval |
| FR-004; SC-007 | Inspect tracked files and notebook/native outputs for secret leakage |
| FR-014, FR-022; SC-008 | Completed descriptive three-model comparison with real evidence; incomplete runs visibly incomplete |

**Gate M2**: A learner completes the default and handwritten-addition path against all three real targets, with matching provenance and reconciled metrics. Run the separate second-policy exercise to prove configuration-only customization.

The [quickstart validation guide](./quickstart.md) distinguishes local checks from live checks. No live gate is claimed passed by this plan.

## Complexity Tracking

No constitutional violations or extra platform components. Added complexity is limited to the approved adaptive conversations, explicit review/approval, provenance checks, and correct denominator/evidence presentation. Keep these shared demo-local concerns out of large notebook cells; add no generic orchestration framework.
