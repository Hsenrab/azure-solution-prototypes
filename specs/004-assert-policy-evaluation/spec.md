# Feature Specification: ASSERT Policy Evaluation Lab

**Feature Branch**: `004-assert-policy-evaluation`

**Created**: 2026-11-03

**Status**: M2 implemented; three-model M1, unchanged-suite 14-case comparison and fresh-kernel display verified on 2026-11-09. Live second-policy/replacement acceptance and destruction remain not run.

**Input**: Create a notebook-first ASSERT (Adaptive Spec-driven Scoring for Evaluation and Regression Testing) lab covering setup, secure model connections, policy definition, evaluation configuration, test generation and review, evaluation execution, results, and model comparison. Deliver infrastructure first by copying and adapting an existing Foundry demo, then add functionality. Make policies and handwritten tests easy to change. Deploy three different models spanning older and newer generations; global deployments are acceptable. Use environment-based credentials without embedding or displaying keys.

## Clarifications

### Third-target restoration approved - 2026-11-09

- Refreshed eastus2 GPT-5.4 GlobalStandard quota is 100 used / 250 limit.
  The user approved deploying the originally selected capacity-10 version
  2026-03-05 as `assert-intermediate` through the existing Bicep and completing
  its paid 14-case evaluation. Preserve both completed runs and the frozen suite;
  retain `newer` generation/tester/judge, with no regeneration or destruction.
- Verified: all three native text/strict-JSON checks and 14-case runs completed.
  Earlier runs and frozen inputs stayed byte-identical. The resume workflow
  previews remaining targets without paid calls and reuses only complete,
  matching selected runs. 52 focused tests and three-model fresh-kernel display
  passed; no new live customization or destruction was performed.

### Earlier approved implementation amendments - 2026-11-05

- The user subsequently authorized moving to M2 with only GPT-5.4 deferred:
  waive the three-model prerequisite for this implementation run, compare the
  two deployed targets, and use GPT-5.6-sol (`newer`) for generation, adaptive
  testing, and judging. Bounded paid evaluation is authorized. Do not mark the
  absent third-model acceptance passed or present this as a three-model result.

- Verify the two available models now and explicitly skip quota-blocked GPT-5.4.
  Preserve the three-generation requirement: partial verification does not pass
  full M1; that earlier approval alone did not authorize M2. The subsequent
  explicit M2 approval above supersedes the prerequisite for this run.
- Replace the initially selected key-based connection with explicit native Entra
  authentication after discovering inherited policy disables local auth.
  Bicep disables local auth and grants the developer account-scoped Cognitive
  Services OpenAI User access. ASSERT's native refreshable token provider uses the
  Azure CLI login; generated files contain no keys or bearer tokens.

### Session 2026-11-03

- Q: Should the starter lab test individual prompts, multi-turn conversations, or both? -> A: Both individual prompts and multi-turn conversations.
- Q: During a multi-turn test, should the next user message be fixed in advance or adapt to the model's previous answer? -> A: Adaptive follow-up messages, using the same approved scenario, tester settings, and turn limit for every model; transcripts may differ.
- Q: How should a failure anywhere in a multi-turn conversation affect its reported score? -> A: Count each conversation once; any applicable policy violation or unnecessary refusal flags it, with offending turns shown as evidence and separate summaries for individual prompts and conversations.
- Q: What default test size and conversation length should the starter lab use? -> A: 12 starter cases: 8 individual prompts and 4 conversations, with at most 3 user/assistant exchanges per conversation; both interaction types include permitted and prohibited cases.
- Q: Should the lab only show comparisons, or also identify regressions against a learner-selected saved baseline? -> A: Side-by-side comparison only; learners interpret differences without automatic regression flags, baseline selection, or pass/fail gates.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare the Lab and Three Models (Priority: P1)

An engineer follows the repository's familiar setup and deployment journey to prepare a learning environment with three distinct, usable model deployments.

**Why this priority**: A working, understandable environment is the prerequisite for testing policy adherence.

**Independent Test**: Complete setup and deployment, identify the three deployed models, and obtain a response from each without revealing credentials.

**Acceptance Scenarios**:

1. **Given** a supported local environment and an Azure subscription with the required permissions and quota, **When** the learner follows setup and deployment, **Then** the evaluation environment and three target models become available with their connection settings generated automatically.
2. **Given** the proposed model selection, **When** planning checks model lifecycle and regional availability, **Then** it identifies three distinct supported models spanning older, intermediate, and newer generations; different aliases of one model version do not qualify.
3. **Given** configured credentials, **When** the learner connects to each deployment, **Then** each responds without a literal secret appearing in notebook source, displayed output, or committed files.
4. **Given** deployed lab resources, **When** the learner follows the standard cleanup journey, **Then** the lab resources are removed using the repository's established cleanup process.

---

### User Story 2 - Define a Policy and Approve Tests (Priority: P1)

An engineer edits a clearly identified policy, configures a small evaluation, generates candidate cases, and reviews them alongside handwritten cases before testing the target models.

**Why this priority**: Policy clarity and human-reviewed tests determine whether evaluation results answer the intended question.

**Independent Test**: Starting from the included policy, generate and inspect candidate cases, add one permitted and one prohibited case, and approve a fixed test set without invoking target-model inference.

**Acceptance Scenarios**:

1. **Given** the starter policy, **When** the learner opens its editable inputs, **Then** prohibited behavior, permitted behavior, and application context are separately identifiable.
2. **Given** an evaluation definition, **When** the learner reviews it, **Then** it identifies the policy, generation settings, target model, generation and judging models, scoring rules, and output location.
3. **Given** generated cases, **When** generation finishes, **Then** the learner can inspect individual prompts or conversation scenarios, intended policy coverage, and expected permitted or prohibited classification before any evaluation of target responses begins. Adaptive follow-up messages are generated during execution, not approved in advance.
4. **Given** the documented handwritten-case format, **When** the learner adds one permitted and one prohibited case, **Then** both appear in the reviewed test set without changes to evaluation execution logic.
5. **Given** reviewed cases, **When** the learner explicitly approves them, **Then** the lab preserves the approved content and a content fingerprint for subsequent runs.
6. **Given** a changed policy or an edited approved case, **When** the learner prepares another evaluation, **Then** the lab requires a newly reviewed test set rather than silently reusing approval for different content.
7. **Given** the starter evaluation, **When** the learner reviews its tests, **Then** it includes both individual prompts and multi-turn conversation scenarios, with documented handwritten examples for each interaction type.
8. **Given** an approved multi-turn scenario, **When** the conversation runs, **Then** follow-up messages adapt to the target's previous answers within the approved scenario constraints and configured turn limit, and the complete transcript is saved.

---

### User Story 3 - Evaluate and Understand Results (Priority: P1)

An engineer executes the approved evaluation and reads an understandable summary backed by saved per-case evidence.

**Why this priority**: The primary learning outcome is connecting policy requirements to observed model behavior.

**Independent Test**: Evaluate one target on an approved set containing both permitted and prohibited cases, reopen its saved results, and reconcile the displayed rates with the scored cases.

**Acceptance Scenarios**:

1. **Given** approved tests and a configured target, **When** the learner starts evaluation, **Then** ASSERT evaluates those tests and saves the run's configuration, target responses, judgments, and aggregate results.
2. **Given** a completed run, **When** the learner views results, **Then** the lab displays policy-violation and unnecessary-refusal counts, applicable scored denominators, and rates, plus example failures with prompts, responses, and judge evidence.
3. **Given** a prohibited case, **When** a valid judgment identifies prohibited behavior in the response, **Then** that case contributes to the policy-violation numerator and its applicable scored denominator.
4. **Given** a permitted case, **When** a valid judgment identifies an unwarranted refusal, **Then** that case contributes to the unnecessary-refusal numerator and its applicable scored denominator.
5. **Given** incomplete execution, invalid judgments, or non-applicable cases, **When** results are summarized, **Then** those outcomes are separately visible and are not represented as compliant responses or silently included in scored denominators.
6. **Given** a scored multi-turn conversation with an applicable failure before its final response, **When** the lab summarizes results, **Then** that conversation is flagged once for the relevant metric even if a later response complies, and the offending turn is identified.
7. **Given** both interaction types, **When** results are displayed, **Then** individual-prompt rates and conversation-level rates have separately labeled counts and denominators; longer conversations do not contribute additional denominator units.

---

### User Story 4 - Compare Three Model Generations and Repeat (Priority: P2)

An engineer compares the three deployed models on the same approved tests and repeats the evaluation after changing a model or policy.

**Why this priority**: Controlled comparisons reveal behavioral differences and provide a reusable regression-testing workflow.

**Independent Test**: Run all three models against one approved set and verify identical test fingerprints, policy, and judging settings before interpreting the side-by-side results.

**Acceptance Scenarios**:

1. **Given** an approved test set and three configured targets, **When** the comparison runs, **Then** all three use the identical saved individual prompts and conversation scenarios, policy instructions, context, scoring rubrics, judging-model configuration, tester-model configuration, and turn limits without regenerating tests. Adaptive conversation transcripts may differ across targets.
2. **Given** completed comparable runs, **When** the learner opens the comparison, **Then** it shows all three model identities and versions, run identifiers, scored counts, violation rates, unnecessary-refusal rates, execution-failure counts, and example failures.
3. **Given** results with different test fingerprints or judging settings, **When** the learner attempts to compare them, **Then** they are identified as non-equivalent rather than presented as a controlled comparison.
4. **Given** an alternative supported target deployment, **When** the learner updates the documented model input, **Then** the same approved tests can evaluate it without editing execution logic.
5. **Given** a different policy, **When** the learner prepares its evaluation, **Then** it receives a separate suite and fresh test review while previous results remain distinguishable.
6. **Given** comparable saved results, **When** the learner views differences between runs, **Then** the lab presents descriptive side-by-side results without requiring baseline selection, automatically flagging regressions, or producing a pass/fail verdict.

### Edge Cases

- An older model is retired, unavailable, or lacks deployment quota: do not substitute a different model silently or count a renamed deployment as another generation; resolve a supported selection before declaring the lab runnable.
- Credentials or required deployment settings are missing: execution stops with the underlying failure and never substitutes fabricated responses.
- A handwritten case is malformed or has a duplicate identifier: it cannot enter the approved set until corrected.
- The candidate set lacks either permitted or prohibited cases: it cannot support both requested rates and must be corrected before approval.
- There are zero applicable scored cases for a metric: display the denominator and an unavailable rate, not zero percent.
- A model call or judging stage fails: preserve the failure separately and do not claim a completed three-model comparison.
- No semantic failures are observed: show that there are no observed failures rather than inventing examples.
- A policy, test, or rubric changes after review: invalidate the corresponding approval or comparison equivalence.
- Adaptive follow-up messages may differ across targets: compare the approved scenarios and fixed tester settings, not transcript fingerprints. Do not describe adaptive conversations as identical input-message replays.
- A conversation contains several violations or a later correction: count it once for the applicable failure metric, preserve offending-turn evidence, and do not erase an earlier failure because its final response complies.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The lab MUST deliver two ordered milestones: a usable infrastructure environment, then the policy-evaluation functionality.
- **FR-002**: The learner journey MUST explain and demonstrate all eight requested sections in order: setup, connect models, define policy, configure evaluation, generate and review tests, run evaluation, show results, and compare models.
- **FR-003**: The lab MUST provide three distinct supported target models spanning older, intermediate, and newer generations, with recorded model identities and versions. Global deployments are permitted.
- **FR-004**: The lab MUST load credentials from the environment, keep secrets out of notebook source and displayed outputs, and exclude secret-bearing local files from version control.
- **FR-005**: The policy MUST expose prohibited behavior, permitted behavior, and application context as editable inputs. Include a small synthetic customer-support starter policy.
- **FR-006**: The evaluation definition MUST expose the policy, test-generation settings, target, generation and judging model roles, scoring rules, and saved-result location.
- **FR-007**: Generated individual prompts and conversation scenarios MUST be inspectable before target-model inference, and inference MUST require explicit approval of the reviewed test content. Adaptive follow-up messages are generated only during execution within those approved scenarios.
- **FR-008**: Learners MUST be able to add handwritten permitted and prohibited cases using a documented format, without editing execution logic.
- **FR-009**: Approved cases MUST retain stable identifiers and a content fingerprint. Model comparisons MUST reuse the saved cases, not generate a fresh set for each target.
- **FR-010**: Each target MUST receive the same policy and application instructions being evaluated, with those instructions held constant across comparison runs.
- **FR-011**: Results MUST preserve configuration, responses, judgments, evidence, and aggregate metrics associated with identifiable suites and runs.
- **FR-012**: Results MUST separately show policy violations on prohibited cases and unnecessary refusals on permitted cases, including numerators and applicable scored denominators. Individual-prompt and multi-turn conversation summaries MUST be separately labeled. Missing, failed, and non-applicable judgments MUST be separately accounted for.
- **FR-013**: The lab MUST display example failures from actual saved evidence and explain that judge-generated assessments require human interpretation.
- **FR-014**: A controlled comparison MUST show all three models side by side and establish identical policy, approved test fingerprint, judging settings, tester settings, and conversation turn limits. For adaptive tests, the fingerprint covers approved scenario definitions, not execution transcripts.
- **FR-015**: Policy changes MUST create distinguishable suites with fresh review; repeated runs and model replacements MUST preserve enough provenance to identify comparable results.
- **FR-016**: Documentation MUST explain prerequisites, the generation/review/execution boundary, credential handling, policy replacement, handwritten-test addition, model replacement, costs, quota dependencies, result interpretation, and cleanup.
- **FR-017**: The starter evaluation MUST default to 12 cases: 8 individual prompts and 4 adaptive conversation scenarios, with permitted and prohibited cases in each interaction type. Each conversation MUST allow at most 3 user/assistant exchanges, where an exchange is one user message and one target-model response. Case counts and this limit MUST be editable inputs and visible before paid target inference. Handwritten additions increase the displayed total; no unbounded generation or evaluation loop is permitted.
- **FR-018**: Missing prerequisites and failed stages MUST surface as failures; the lab MUST NOT silently substitute models, use synthetic success results, or treat failures as compliance.
- **FR-019**: The initial lab MUST support both individual prompts and multi-turn conversation scenarios in generation, review, handwritten additions, execution, saved evidence, and model comparison. Results MUST identify the interaction type.
- **FR-020**: Multi-turn conversations MUST use adaptive follow-up messages constrained by the approved scenario and a finite configured turn limit. Runs MUST retain complete transcripts and tester-model identity and settings; comparisons MUST explain that equivalent scenarios can produce different messages across target models.
- **FR-021**: Multi-turn scoring MUST count each applicable scored conversation once per metric, flagging it when any response exhibits the corresponding applicable failure. Multiple failing responses MUST NOT increase that conversation's denominator weight; subsequent compliance MUST NOT erase earlier failures. Failure evidence MUST identify the offending turns.
- **FR-022**: Model and repeated-run comparisons MUST remain descriptive side-by-side displays. The initial lab MUST NOT require saved-baseline selection, automatically flag regressions, or impose pass/fail thresholds. Learners interpret differences using the displayed counts, rates, and evidence.

### Key Entities

- **Policy**: Named, revision-identifiable prohibited and permitted behavior plus application context; used by test generation, target instructions, and judging.
- **Model selection**: Three distinct target identities and versions, their deployment connections and generation positions, plus explicit generation and judging roles.
- **Evaluation definition**: Policy reference, generation settings, model roles, scoring rubrics, and result destination.
- **Approved test set**: Reviewed generated and handwritten individual prompts and adaptive multi-turn scenario definitions with stable identifiers, interaction type, expected policy classification, approval, and a content fingerprint. Runtime transcripts are separate evidence and are not part of this fingerprint.
- **Evaluation suite**: A policy-specific grouping sharing approved tests and retaining distinguishable runs.
- **Evaluation run**: One target's execution with saved configuration, responses, complete conversation transcripts, tester identity and settings, judgments, errors, evidence, and metrics.
- **Comparison**: Three runs with matching policy, approved test fingerprint, judging settings, tester settings, and turn limits, shown side by side; adaptive transcripts need not match.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A learner following the documented journey obtains a usable response from each of three distinct supported model generations, without manually copying credentials into learning materials.
- **SC-002**: A learner completes all eight sections in the stated order; target evaluation cannot begin before test approval.
- **SC-003**: With default settings, the starter journey produces 12 reviewed cases: 8 individual prompts and 4 adaptive conversation scenarios, with permitted and prohibited examples of each interaction type. No default conversation exceeds 3 user/assistant exchanges. A learner adds one case of each classification without changing execution logic, producing 14 cases evaluated against each of the three target models.
- **SC-004**: All three comparison runs have identical approved-test fingerprints, policy revisions, judging settings, tester settings, and conversation turn limits; no prompt or scenario regeneration occurs between target runs. Adaptive transcripts are retained but are not required to match.
- **SC-005**: Every displayed rate reconciles exactly to its displayed numerator and applicable scored denominator; execution failures and non-applicable cases are separately counted, and zero-denominator rates are unavailable. Individual-prompt and conversation rates are shown separately. A scored conversation with multiple applicable failures contributes exactly one flagged case and one denominator unit for the corresponding metric, including when its final response complies.
- **SC-006**: A learner changes to a second policy by editing documented policy/configuration inputs, obtains a separately identified evaluation suite, and retains distinguishable results for the first policy.
- **SC-007**: An inspection of tracked lab files and saved notebook outputs finds no credentials or secret values.
- **SC-008**: The final comparison displays results for all three models and links every shown failure example to saved case evidence; a failed run is visibly incomplete.

## Assumptions

- Learners are engineers with basic notebook familiarity, Python 3.11 or later as required by ASSERT, Azure access, sufficient deployment permissions, and quota for three supported models.
- The user approved this scope before specification files were written. Approval covers specification and its quality checklist, not implementation or deployment.
- Model families, versions, deployment region, and capacity will be validated during planning. "Older" means supported and deployable, not retired. No exact model availability is assumed by this specification.
- Global deployments are acceptable; a requirement for in-region-only processing is not assumed.
- Environment-based credentials are the approved authentication direction. No alternative authentication architecture is included by default.
- The initial policy and test data are synthetic; use of customer secrets or personal data is out of scope.
- Generation, adaptive conversation testing, and judging may reuse one of the three deployments. They do not require a fourth deployment, and their roles must remain explicit. Tester and judging settings remain fixed across compared target runs.
- This is a feasibility and learning lab, not a guarantee of safe behavior or production certification. Model and judge variability can affect repeated results.
- Default sample counts and conversation limits are for a small first run, not comprehensive policy coverage. Learners can increase them explicitly; handwritten additions are included in the visible evaluation count.
- CI integration, saved-baseline selection, automatic regression flags, pass/fail gates, a custom viewer, production hardening, additional hosted applications, and automatic model-selection fallbacks are out of scope.
- Regression-testing learning is limited to repeating approved tests and interpreting side-by-side results. Small-sample differences are observations, not proof of statistically significant degradation.

### User-Requested Delivery Constraints

- Keep the implementation self-contained under `demos/assert01-foundry-evaluation/` using the repository's demo layout.
- Start infrastructure from the existing minimal [Foundry demo](../../demos/gpt4o01-text-image-audio/infra/main.bicep), copying and adapting it rather than introducing a new deployment architecture. Define platform behavior in Bicep.
- Follow the repository's [setup](../../demos/speech01-foundry-speech/notebooks/00_setup.ipynb) structure and copy its [destroy notebook](../../demos/speech01-foundry-speech/notebooks/X_destroy.ipynb) verbatim, as required by repository guidance.
- Generate local deployment settings through the deployment notebook; never require manually authored connection settings as the normal path.
- Use ASSERT's command-line pipeline from notebook steps, with small single-purpose cells and Python-readable saved results.
- Keep detailed implementation choices in the subsequent plan rather than prescribing them here. The infrastructure milestone must be independently validated before functionality is declared complete.

### External Dependencies

- ASSERT installation, configuration, stage control, test schema, Azure provider integration, and saved artifact formats must be verified against a chosen package release during planning.
- Official references: [ASSERT documentation](https://responsibleai.github.io/ASSERT/docs/), [configuration schema](https://github.com/responsibleai/ASSERT/blob/main/docs/config/schema.md), and [results guide](https://github.com/responsibleai/ASSERT/blob/main/docs/guides/results.md).
- Live acceptance depends on Azure quota, supported model availability, network access, and paid model calls. Reports must distinguish local checks from Azure-dependent acceptance actually executed.
