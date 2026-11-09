# Data Model: ASSERT Policy Evaluation Lab

This design supports [spec.md](./spec.md). All persistence is local to the demo; there is no database, hosted evaluation service, or new public API.

## Authoring Inputs

### Policy

Location: `data/policies/<policy-id>.yaml`.

| Field | Type | Rule |
|---|---|---|
| `id` | string | Stable non-secret identifier, valid as part of an ASSERT suite name |
| `revision` | string | Learner-controlled revision; content hashes still detect edits without a revision change |
| `context` | string | Non-empty application context and capabilities |
| `prohibited` | list of strings | At least one concrete prohibited behavior |
| `permitted` | list of strings | At least one concrete permitted behavior |

Render the same policy into the target system prompt and evaluation behavior description. Application capabilities must be explicit; the starter customer-support assistant explains refund rules but has no tool that actually issues refunds. Permitted examples ask for explanations; prohibited examples ask the assistant to claim it has performed an unavailable action. Use synthetic orders and no sensitive customer data.

### Lab Settings

Location: `data/lab.yaml`.

| Field | Type | Default / rule |
|---|---|---|
| `policy_path` | path | Selected policy under the demo's data directory |
| `extra_tests_path` | path | Editable native JSONL additions; initially empty |
| `prompt_count` | positive integer | `8` generated individual prompts |
| `scenario_count` | positive integer | `4` generated adaptive scenarios |
| `max_turns` | positive integer | `3`; one turn is one user/target exchange |
| `generation_target` | string | `newer`, explicitly approved and retained when restoring intermediate |
| `tester_target` | string | `newer`, same across compared runs |
| `judge_target` | string | `newer`, same across compared runs; not independent of targets |
| `comparison_targets` | list of strings | `older`, `intermediate`, `newer`; three-model unchanged-suite acceptance verified |

These are demo-owned authoring settings, not invented ASSERT configuration keys. A small shared helper resolves them into native ASSERT configuration. Credentials must never be fields in this document.

A target-list addition does not invalidate unchanged shared approval inputs.
Retain the frozen policy/tests, tester/judge identities and budgets, turn limit,
rubrics and package/provider settings. The unpaid comparison preview reuses only
complete selected runs matching the current approval and deployment identities;
duplicate, incomplete or mismatched selections fail before paid inference.

### Deployment Selection

Produced by infrastructure deployment, not hand-authored connection strings.

Fields: subscription, resource group, location, account/project identities and
endpoints, plus three deployment records containing alias, deployment name,
model name, actual version, SKU, and capacity for full acceptance. The explicitly
approved partial state has two actual records plus `skipped_deployment` and
`skip_reason`; both skip fields are null for the full state. The union still
contains exactly the three distinct planned generations. Generated settings
select native Entra/Azure CLI credentials; no keys or bearer tokens are stored
in demo files. ASSERT's native credential provider manages token refresh.

Model names and actual versions must be distinct across the three comparison generations. A generation label such as `older` is a demo label, not a provider model identifier.

## Native ASSERT Artifacts

### Taxonomy

Native `taxonomy.json` contains:

- `behavior.name` and `behavior.definition`.
- `definition_of_terms`.
- `behavior_categories[]` with `name`, `definition`, `examples`, and boolean `permissible`.
- Native provenance metadata where emitted.

`behavior_categories[].name` is the case-to-taxonomy join key. `permissible` is authoritative here, not a custom field added to input cases. Review category definitions and labels before generating the candidate set. The small starter policy should retain a concise taxonomy with both permitted and prohibited categories.

Unknown behavior references, duplicate category names, missing labels, or non-boolean permissibility prevent test approval; they must not silently become unclassified scored cases.

### Test Case

Each line of native `test_set.jsonl` is one object:

| Field | Type | Rule |
|---|---|---|
| `type` | enum | `prompt` or `scenario` |
| `test_case_id` | string | Unique and stable; generated IDs retained, handwritten IDs use a clearly distinct prefix |
| `behavior` | string | Native top-level policy label |
| `dimensions.behavior` | string | Exact category name in the approved taxonomy; released native classification accessor |
| `seed.title` | string | Human-readable review label |
| `seed.description` | string | Full user prompt or adaptive scenario definition |
| `seed.system_prompt` | string, optional | Omit for this lab; the shared target policy prompt is authoritative |
| `dimensions` | object, optional | Native generation dimensions where emitted |

Do not add `permissible`, `api_key`, arbitrary policy fields, or a second conversation execution format to this input contract. Runtime inference may attach resolved permissibility as part of ASSERT's native output.

For prompts, the approved input is a user message. For scenarios, it is the user's role/objective and constraints, not a prewritten transcript. Generated follow-ups may differ by target.

### Approved Test Set

An immutable-by-convention suite directory holds the reviewed taxonomy and merged generated/handwritten native JSONL. Approval records exact file hashes rather than trying to infer whether an edit was meaningful.

Fields in demo-owned `approval.json`:

- `suite_id`, `policy_id`, `policy_revision`.
- `approved_at` and explicit `reviewed: true`.
- SHA-256 hashes of the policy file, taxonomy file, and approved test-set file.
- Expected case identifiers, interaction-type counts, and permissibility counts per type.
- Shared evaluation-settings hash and effective target-policy-prompt hash.
- ASSERT package version.

Hash file bytes for the three source artifacts; hash canonical, secret-free JSON for shared settings. Transcript hashes are not approval or comparison keys.

Coverage rules:

- Initial generation uses 8 prompts and 4 scenarios.
- Both permissibility values must occur within each interaction type before approval.
- Adding one permitted and one prohibited handwritten case increases the total to 14 without regenerating the original 12.
- Any policy, taxonomy, case-content, tester/judge setting, rubric, or turn-limit change invalidates corresponding approval. Generation-only settings need not invalidate an unchanged frozen set.

### Evaluation Suite and Run

Suite identity combines policy identity/revision with a content-derived suffix; changing policy content must create a distinguishable suite even when a learner forgets to increment its revision.

After approval, do not overwrite that suite's policy/taxonomy/test/settings snapshot. Subsequent content or shared-setting edits start a distinguishable candidate suite; retain the old approved artifacts with their runs. Adding cases may copy the existing approved native inputs into the new candidate suite for editing without regenerating them. A manual in-place edit to an approved file blocks execution rather than silently updating its approval.

Run identity combines a deployment alias with a unique run suffix. Never overwrite another target's run or silently reuse a cached earlier run as a new evaluation.

Native per-run files: `manifest.json`, `config.yaml`, `inference_set.jsonl`, `scores.jsonl`, and `metrics.json`. Preserve them unmodified; store demo provenance in a separate `provenance.json`.

Provenance includes:

- Approved artifact hashes and shared-settings hash.
- Actual deployment model/version before evaluation.
- Effective policy prompt, rubric, tester and judge identities/settings, and turn limit.
- Native configuration file path, ASSERT version, and run identity.
- Completion state and comparison eligibility, without credentials.

### Normalized Case Result

A demo-local loader joins the approved test set, taxonomy, native inference records, and native score records by `test_case_id`. It does not replace ASSERT inference or judging.

Fields:

- Case ID, interaction type, behavior, resolved permissibility.
- Native response/transcript reference.
- Inference status and error, judge status and error, missing-record state.
- Boolean or unavailable violation/refusal verdicts.
- Judge justifications and references to offending target-message turns.

Reject duplicate IDs and invalid schema values. Missing responses, missing scores, and malformed/non-applicable judgments are not clean results.

## Metric Semantics

Summarize separately for `prompt` and `scenario`:

| Display metric | Numerator | Denominator |
|---|---|---|
| Policy-violation rate | Prohibited cases with a valid applicable violation verdict of true | Prohibited cases with valid applicable boolean violation verdicts |
| Unnecessary-refusal rate | Permitted cases with a valid applicable overrefusal verdict of true | Permitted cases with valid applicable boolean overrefusal verdicts |

For each metric, also show failed-inference, failed-judge, missing, and semantic-not-applicable counts separately from the denominator. A zero denominator yields an unavailable rate, not `0%`.

An adaptive conversation is one case. A valid verdict flags the conversation if any applicable target response fails, including an earlier failure followed by a compliant response. Multiple failing responses do not increase its weight. Preserve the full transcript and offending-turn evidence.

## State Transitions

1. `policy selected` -> `taxonomy generated/reviewed`.
2. `taxonomy reviewed` -> `candidate tests generated`.
3. `candidate tests edited/merged` -> `reviewed and approved`, only when schema and coverage checks pass.
4. `approved` -> `inference + judging`, only if approval hashes still match.
5. `run finished` -> `comparable`, only if native completion, case accounting, and shared provenance agree.
6. Editing approved content -> `review required`; changing policy -> separate suite.
7. Any execution failure -> `incomplete`, with preserved evidence and no success-shaped comparison.

Comparison has no baseline state, automatic regression label, pass/fail threshold, or CI gate.
