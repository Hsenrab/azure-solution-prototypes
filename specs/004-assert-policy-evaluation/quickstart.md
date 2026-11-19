# Quickstart Validation Guide

This is the acceptance guide for [plan.md](./plan.md). M1 and M2 functionality
are implemented; all three native connections and unchanged-suite 14-case
evaluations passed. The original frozen cases and earlier completed runs were
retained when adding GPT-5.4. Live second-policy/replacement acceptance and
destruction remain not run. See the demo architecture notes for actual evidence.

## Prerequisites

- Python 3.11, VS Code notebook support, Azure CLI/Bicep, and an explicitly selected Azure subscription.
- Permission to create account/project/deployments and account-scoped developer inference RBAC; a valid Azure CLI developer login.
- Access and quota for three supported models and permission for the Bicep-defined network/authentication settings.
- Synthetic data only. Review expected generation, tester, inference, and judge usage before paid calls.
- The approved native Entra path disables local authentication and stores no keys/tokens. A successful two-model smoke does not pass full M1.

See [research.md](./research.md) for the public model/version candidates and evidence limits. See the [infrastructure contract](./contracts/infrastructure.md) for live deployment prerequisites.

## Two Separately Requested Implementation Runs

- **Run 1 - Infrastructure**: Complete T001-T015 in [tasks.md](./tasks.md), including infrastructure documentation, live connections, credential-output inspection, notebook hygiene, and handoff evidence. Stop after T015 even on success.
- **Run 2 - Evaluation**: Start T016-T046 only on a separate explicit request after M1 passes. Reuse the recorded infrastructure and generated settings rather than automatically redeploying; complete evaluation, repeat checks, and finish cleanup.

## Milestone 1 - Infrastructure

### Setup

Open the demo setup notebook and follow these headings in order:

1. **Step 1 - Create Isolated Virtual Environment and Register Kernel**.
2. **Step 2 - Authenticate to Azure**, after selecting the new kernel.
3. **Step 3 - Install Python dependencies in virtual environment**.

Expected: ASSERT is installed in the selected demo interpreter, not merely in another global Python environment.

### Deploy and Connect

Open the deployment notebook:

- Confirm subscription, resource group, location, and the three model selections.
- Verify model/version/SKU support, capacity units, current quota, and effective inherited policy before provisioning.
- Build and deploy the single Bicep path.
- Retrieve non-secret resource/deployment metadata and generate `env/.env` without displaying its content.
- In the configure notebook's **Connect models** section, obtain one real response from each target using ASSERT's provider path.

Expected: three distinct deployed model identities/versions, three real connection responses, and a generated environment file. Do not mark this milestone complete from a successful template build alone.

### Handoff and Mandatory Stop

Before handing off M1, provide usable setup/deployment/connection instructions, credential handling, cost/quota notes, and cleanup instructions covering the recorded-subscription prerequisite and potentially enabled destroy confirmation flags. Keep the M1-only handoff distinct from separately authorized M2 evaluation.

Inspect all execution outputs for credential exposure before stripping, including
deployment/metadata export; no keys are retrieved under the approved Entra path.
Never print secrets while checking. Verify ignored artifacts, remediate any
exposure at its source, and repeat notebook cleanup after live execution.

Record non-secret actual model identities/versions, subscription/resource identities, provider/API and dependency versions, generated-file locations, resource state, and check outcomes/blockers in the demo's architecture notes. Keep credentials out of the report. Stop even when all M1 checks pass; retain resources and local generated settings for a separately requested Run 2.

## Local Validation

At each implementation-run handoff, after standard setup, run from the repository root in PowerShell:

```powershell
Set-Location .\demos\assert01-foundry-evaluation
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -m assert_ai.cli --help
& .\.venv\Scripts\python.exe -m unittest discover -s .\tests -p "test_*.py"
az bicep build --file .\infra\main.bicep --outfile .\outputs\generated\main.json
```

The generated directory is created by the implemented setup/deployment flow before the build command. Tests and `--help` require no paid model calls. The Bicep build does not verify quota, policy, entitlement, or deployment success.

Before clearing/stripping outputs, inspect all available outputs from all five demo notebooks, including `01_deploy_infra.ipynb`, for credential exposure without echoing secret values. Then, from the repository root, run the existing configured notebook cleanup against changed demo notebooks:

```powershell
pre-commit run --files demos\assert01-foundry-evaluation\notebooks\00_setup.ipynb demos\assert01-foundry-evaluation\notebooks\01_deploy_infra.ipynb demos\assert01-foundry-evaluation\notebooks\02_configure.ipynb demos\assert01-foundry-evaluation\notebooks\03_assert_flow.ipynb demos\assert01-foundry-evaluation\notebooks\X_destroy.ipynb
```

If a hook modifies notebook metadata, retain those changes and rerun the same focused check. Do not weaken the existing workflow.

## Milestone 2 - Evaluation

The user initially authorized M2 without GPT-5.4, then explicitly approved its
original Bicep deployment and paid evaluation after freeing quota. Consume the
existing three-model settings; keep `newer` generator/tester/judge and the same
frozen 14-case suite. Retain older/newer completed runs and evaluate only the
missing intermediate target. The three-model comparison is verified. Do not
regenerate or repeat completed targets automatically; inspect the unpaid
comparison preview before running its separate paid cell.

### Define the Policy and Configuration

Setup ends with **Connect models** in `02_configure.ipynb`. Start the experiment in `03_assert_flow.ipynb`: under **Define the policy**, edit the selected policy's context, prohibited behavior, and permitted behavior.

In **Configure the evaluation**, inspect:

- The same effective policy supplied to all target system prompts.
- The default 8-prompt/4-scenario budget and maximum 3 exchanges.
- Explicit generator, tester, judge, and target deployment identities.
- Native violation and overrefusal dimensions and their meaning.
- Secret-free generated configuration locations.

Expected: changing a policy or model role requires input changes, not edits to evaluation execution logic.

### Generate, Review, and Add Cases

After completing the customer-support walkthrough, use
[04_your_own_policy.ipynb](../../demos/assert01-foundry-evaluation/notebooks/04_your_own_policy.ipynb)
for the second-policy exercise. It keeps the same evaluation cells and section
order, adding an ID/revision selection step, an editable policy dictionary,
and a validation/save cell for `data/policies/<id>-<revision>.yaml`. It selects
that policy in memory and retains the shared model/budget settings. Saved
selections live alongside suites in
`outputs/generated/collections/c-<hash>/active-suite.json` and `active-runs.json`,
keeping different policies and revisions separate. `collection.json` records
the policy identity; the viewer's `ARTIFACTS_ROOT` is the collection directory.
Unchanged policy content can be saved again; different content requires a new
ID/revision. Learner-created policies and generated artifacts are Git-ignored;
the shipped example is tracked. Existing fixed-name policy, selection files,
and older suites are not moved or changed.

In the flow notebook's **Generate and review tests** section:

1. Run native taxonomy generation without target evaluation.
2. Review/correct category definitions and boolean permissibility labels.
3. Run native test generation on that reviewed taxonomy, still with target inference and judging disabled.
4. Inspect the 8 prompts and 4 adaptive scenario definitions. Confirm both permitted and prohibited cases in each interaction type.
5. Run the cell under **Add your own tests** to generate one additional permitted and one prohibited prompt from the same policy and reviewed taxonomy. Open the suite-local `extra-tests.jsonl` link to customize these AI-generated examples or add handwritten cases using the native format documented in the [evaluation contract](./contracts/evaluation.md). Do not use the legacy fixed file under `data/`.
6. Confirm review and combine the tests under **Review and combine tests**, then inspect all 14 cases. There is no separate final approval step.

Expected: no target test-set responses exist before evaluation starts. Combining saves hashes in `review.json`; starting evaluation verifies that the reviewed inputs are unchanged and automatically saves the frozen-input record in `approval.json`. Adaptive runtime follow-ups are not fixed messages; the frozen inputs cover scenario definitions, constraints, tester settings, and the turn limit.

### Run the First Target

In **Run the evaluation**, invoke native ASSERT through the notebook interpreter on the first target's generated run configuration. The notebook loads `env/.env` into the child process environment.

Expected:

- Systematization/test-generation stages are disabled in this configuration.
- All 14 approved identifiers appear in the run's case accounting.
- No conversation exceeds 3 user/target exchanges.
- Native inference, score, metric, manifest, and configuration artifacts are saved.
- Invalid/missing credentials and failed stages remain errors, never compliant or fabricated responses.

Do not invoke a global `assert-ai` executable from an unrelated environment or run an unconfigured shell command that has not loaded the generated environment.

### Inspect Results

In **Show results**:

- Reopen saved artifacts in a fresh kernel to prove that display does not depend on unsaved in-memory responses.
- Show separate individual-prompt and conversation summaries.
- Reconcile violation rates to applicable scored prohibited cases and unnecessary-refusal rates to applicable scored permitted cases.
- Show scored counts, failure/missing/N/A accounting, and unavailable rates when a denominator is zero.
- Open real failure evidence and its transcript turn when failures exist. If none are observed, explicitly show that rather than synthesizing an example.

Use local fixtures to verify the edge case where a conversation fails early and later complies: it must still count once as a failure. No live model is required to produce that particular behavior for the fixture test to pass.

### Compare the Remaining Models

In **Compare models**, run inference and judging against the remaining configured
target using the same approved files and shared settings.

Expected:

- Both approved current runs contain the same 14 case identifiers and artifact hashes.
- Policy, rubric, judging model/settings, tester model/settings, and turn limit agree.
- Actual deployment identities/versions are displayed.
- Conversation transcripts may differ, but approved scenario definitions do not.
- The output is descriptive side-by-side results, not an automatic regression flag or pass/fail gate.
- A partial run is visibly incomplete, not a successful controlled comparison.

## Customization Acceptance

1. Copy/edit the synthetic starter policy into a second policy input.
2. Select it through the documented settings.
3. Generate and review fresh taxonomy/tests; obtain a separate suite and approval.
4. Confirm previous suite results remain distinguishable.
5. Replace a target with an explicitly chosen supported deployment through settings, then rerun the original frozen tests without changing pipeline logic.

The replacement exercise is not permission to silently substitute a model when the three-model starter deployment is blocked.

## Negative and Accounting Checks

Verify locally with focused tests:

- Inputs without a completed review/merge, or edited since review, cannot start target inference. Previously frozen suites must still match their saved hashes; they are never automatically resealed.
- Unknown category names, duplicate IDs, or missing permissibility fail approval.
- Both interaction types and both policy classifications are present in the default reviewed set.
- Multiple failing turns count once; later compliance does not erase the failure.
- Missing rows, judge failure/skipped status, semantic N/A, and zero denominators are not counted as clean successes.
- Changing tester/judge/rubric/turn settings makes runs non-equivalent.
- No generated native configuration, captured notebook output, or tracked file contains credential values.

## Cleanup and Evidence Report

Explicitly verify/select the recorded deployment subscription before opening the unchanged standard destroy notebook. Follow its delete/purge/resource-group flow, noting that source confirmation flags may already be true.

Inspect new destroy-notebook execution outputs for credentials before stripping them, then rerun its existing focused notebook-cleanup check so cleanup does not leave outputs or execution metadata in the final handoff.

Record which local checks, deployment/connection checks, full three-model runs, second-policy exercise, and cleanup actually ran. List blocked or unexecuted live checks separately. Preserve local artifacts only under the ignored generated path.
