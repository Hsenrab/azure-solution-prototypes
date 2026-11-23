# ASSERT policy evaluation lab

Notebook-first introduction to Adaptive Spec-driven Scoring for Evaluation and
Regression Testing. Follow these notebooks to connect models, define a policy,
generate and review tests, evaluate model behavior, and compare results.

## Before you start

- Install Python **3.11+**, VS Code with notebook support (or Jupyter), Azure CLI,
  and Bicep.
- Choose an Azure subscription, region, and dedicated resource group.
- Ensure the selected model versions have sufficient Global Standard quota.
- Have permission to deploy resources and assign the account-scoped
  **Cognitive Services OpenAI User** role.
- Ensure your Azure policies permit the public endpoint with local
  authentication disabled.

The notebooks use your Azure CLI sign-in with **keyless Entra authentication**.
Never put keys or tokens in notebooks, policies, or test cases.

Model calls cost money, including connection checks and retries. Global Standard
may process requests outside the account region. Review the evaluation budget
before generating tests or evaluating models.

## Run the notebooks

Open notebooks from this demo's [notebooks](./notebooks/) folder. Their working
directory must be that folder. Run cells in order unless following the
[saved-results instructions](#resume-an-existing-comparison).

**Setup is notebooks 00-02. Your ASSERT experiment starts in notebook 03.**
Once setup is complete, reuse the flow notebook for each new policy; you do not
need to redeploy the models.

### 1. Setup

Open [00_setup.ipynb](./notebooks/00_setup.ipynb):

1. Run **Step 1** to create the virtual environment and register the kernel.
2. Select **Python (assert01-foundry-evaluation)** as the notebook kernel.
3. Run **Step 2** to sign in to Azure and select your subscription.
4. Run **Step 3** to install [requirements.txt](./requirements.txt).

Use this kernel for the remaining notebooks.

### 2. Deploy infrastructure

Open [01_deploy_infra.ipynb](./notebooks/01_deploy_infra.ipynb):

1. Set `AZURE_SUBSCRIPTION_ID` or edit `SUBSCRIPTION_ID` explicitly.
2. Review `RESOURCE_GROUP`, `LOCATION`, and `MODEL_PLAN`. The default target
   aliases are `older_model`, `intermediate_model`, and `newer_model`.
3. Run the catalog/quota checks and complete the notebook's Azure Policy review.
   Resolve any blocked selection before deploying.
4. Run the Bicep deployment and export the generated connection settings.

This creates the Foundry account/project and selected model deployments.
Do not hand-author `env/.env` or copy [.env.example](./env/.env.example): the notebook generates the
actual environment settings and deployment metadata.

### 3. Connect models - finish setup

Open [02_configure.ipynb](./notebooks/02_configure.ipynb):

1. Load the generated settings.
2. Run **Connect models** to check text and structured JSON responses.

**Setup complete.** The remaining work is the ASSERT experiment, not Azure setup.

### 4. Follow the ASSERT flow - from policy to results

Open [03_assert_flow.ipynb](./notebooks/03_assert_flow.ipynb):

1. Run **Load the lab**.
2. Under **Define the policy**, edit
   [customer-support.yaml](./data/policies/customer-support.yaml) to describe
   application context, prohibited behavior, and permitted help.
3. Under **Configure the evaluation**, review [lab.yaml](./data/lab.yaml):
   selected policy, generation counts, maximum turns, generator/tester/judge
   aliases, and comparison targets.

4. Under **Generate and review tests**, generate the taxonomy and inspect its
   categories and permitted/prohibited classifications. Set
   `TAXONOMY_REVIEWED = True` only after reviewing it.
5. Generate candidate cases, then run the cell under **Add your own tests**.
   ASSERT creates two additional prompts from this suite's policy and reviewed
   taxonomy. Open the linked suite-local `extra-tests.jsonl` to inspect,
   customize, or add cases.
6. Under **Review and combine tests**, check the main and extra tests, set
   `GENERATED_CASES_REVIEWED = True`, then run the following cell to combine them.
7. Inspect the combined set, then run **Run the evaluation**. It automatically
   freezes the reviewed inputs before calling models; no separate approval is
   required. Wait for ASSERT's CLI pipeline to finish.
8. Run **Show results** and **Inspect real failure evidence**.
9. Under **Compare models**, run the unpaid preview and review the remaining
   targets. Run **Evaluate missing targets (paid)**, then display the comparison.

Defaults are **8 generated prompts + 4 adaptive scenarios**, with at most
**3 user/target exchanges** per scenario. Two freshly generated editable starter
prompts bring the total to **14 cases per target**. These starters are
AI-generated examples, not handwritten tests. Their generation also uses paid
model calls.

Each suite has its own editable file. Reopening links or rerunning the merge
does not regenerate it. Rerunning **Add your own tests** reuses the saved editable
file and displays its table/link without paid calls, preserving your edits;
start a new suite for fresh examples. The earlier
`data/extra-tests.jsonl` is not used by this flow.

Do not use **Run All** to bypass review. Set each confirmation flag only after
completing the corresponding review. Each teaching-notebook flag has its own
cell: edit and run that cell, then run the following action cell. Compare models on the same approved test
set; do not regenerate tests between targets.

Generation cells show clickable links alongside their main-test and extra-test
table previews. Open those links to read full descriptions without table
truncation; clicking a link does not repeat generation. Do not rerun paid
generation merely to reopen a file. Taxonomy inspection also includes a link;
the separate merged-test links reopen files without repeating the merge.
Starting evaluation saves a frozen-input record (`approval.json`) automatically.
If inputs changed after combining, repeat **Review and combine tests** first.
Once evaluation starts, treat the policy, tests, settings, and frozen-input
record as read-only snapshots; use a new suite for changes. Results also link
to full transcripts and judge scores. Evaluation completion also displays
explicit transcript, score, and metric links, avoiding automatic detection of
printed Windows paths with spaces. Use **Show results** to reopen those files
without repeating paid evaluation.
Policy, native configuration, deployment records, connection evidence, and
comparison outputs also provide explicit file links instead of relying on
automatic detection of printed paths.

## View results in the ASSERT viewer (optional)

For a visual way to explore results, use the
[ASSERT Results Viewer](https://github.com/responsibleai/ASSERT/tree/main/viewer).
You can browse saved runs, inspect conversations and judge explanations, and
compare model results. The notebook summaries remain available without this
extra setup.

### One-time setup

Install a Node.js version supported by the viewer's dependencies, then clone
ASSERT if you have not already done so. In PowerShell, replace the example
checkout paths below with your own:

```powershell
git clone https://github.com/responsibleai/ASSERT.git 'C:\Git\ASSERT'
Set-Location 'C:\Git\ASSERT\viewer'
npm install
```

If ASSERT is already cloned, skip `git clone`. The viewer is maintained
separately from this lab's pinned Python package; check the viewer's setup
instructions when updating your checkout.

### Start the viewer

In the same PowerShell terminal, point the viewer at one policy/revision's
collection, not at an individual suite or model run. The notebook prints the
`ARTIFACTS_ROOT` setting when creating a suite and when selecting your own
policy. Copy that setting, or resolve the walkthrough's current collection:

```powershell
$selection = Get-Content -Raw 'C:\Git\azure-solution-prototypes\demos\assert01-foundry-evaluation\outputs\generated\active-suite.json' | ConvertFrom-Json
$env:ARTIFACTS_ROOT = Split-Path -Parent $selection.suite
npm run dev
```

Keep the paths quoted, especially if they contain spaces such as
`OneDrive - Microsoft`. Set `ARTIFACTS_ROOT` again whenever you start from a new
terminal.
To view a different collection, stop the viewer, change `ARTIFACTS_ROOT`, and
start it again. Older runs remain under `outputs/generated/suites`; use that
directory as the viewer root to browse those unmoved results.

Open [http://localhost:5174](http://localhost:5174), select your customer-support
suite (or the suite for your own policy), then choose a completed model run.
Explore the scores, conversations, and judge explanations. After evaluating
other targets in the notebook, select their saved runs for comparison.

Browsing saved results does not rerun models, require Azure redeployment, or
incur evaluation costs. Avoid viewer controls that launch new evaluations
unless you intend to make paid model calls. The viewer has no built-in
authentication; keep it local rather than exposing it on a public interface.

Leave the terminal running while using the viewer. Press **Ctrl+C** in that
terminal to stop it.

## Resume an existing comparison

For results only, run **Load the lab** followed by **Show results** in
[03_assert_flow.ipynb](./notebooks/03_assert_flow.ipynb). Use the comparison display cell to
show saved runs side by side. Skip generation and **Run the evaluation** to avoid
creating another suite or paying for another evaluation.

The saved selection in `outputs/generated/active-runs.json` identifies the suite
and runs to reopen. Select one completed run per target.

To evaluate another supported target on those same cases:

1. Ensure it is deployed and included in the generated connection settings.
   Use [01_deploy_infra.ipynb](./notebooks/01_deploy_infra.ipynb) if deployment
   is needed; reload and check connections in
   [02_configure.ipynb](./notebooks/02_configure.ipynb).
2. Add its alias to `comparison_targets` in [lab.yaml](./data/lab.yaml).
   Keep the policy, tester, judge, budgets, and maximum turns unchanged.
3. Reload **Load the lab**, then run **Compare models**' unpaid preview.
4. Run **Evaluate missing targets (paid)** only after reviewing the preview.

Completed matching runs are reused. Incomplete, duplicate, or mismatched
selections must be corrected before evaluating missing targets.

Existing results and connection files may use the earlier labels `older`,
`intermediate`, and `newer`. They are read without rewriting the saved evidence;
new settings use the `_model` labels. Start a new reviewed suite for future
evaluations with the renamed aliases rather than reusing an old approval.

## Create your own policy

After the customer-support walkthrough, open
[04_your_own_policy.ipynb](./notebooks/04_your_own_policy.ipynb). It follows the
same section order and evaluation flow, using the same deployed models.

1. Run **Load the lab** with **Python (assert01-foundry-evaluation)**.
2. Under **Choose your policy**, set `POLICY_ID` and `POLICY_REVISION`, then
   run the selection cell. Use a different ID for each use case and a new
   revision when changing its rules.
3. Under **Define the policy**, fill in the context, prohibited rules, and
   permitted rules in `my_policy`, then run the save cell. It validates and
   writes `data/policies/<id>-<revision>.yaml`. Rerunning with unchanged content
   reuses the file; different content requires a new ID or revision.
4. Continue through configuration, generation, review/combining, evaluation,
   and comparison, just as in the walkthrough. Generation and evaluation are
   paid; saving the policy and viewing results are not.

The notebook selects your policy in memory, leaving the customer-support
policy and shared `lab.yaml` unchanged. Model roles and budgets still come from
`lab.yaml`. It stores separate `active-suite.json` and `active-runs.json`
selection files inside its policy/revision collection under
`outputs/generated/collections/c-<hash>/`, alongside its suites, so each
policy/revision and the walkthrough keep their own saved selections.
New policy experiments create new suites; previous suites retain their policy
snapshots and results. To switch policies, restart the kernel, run **Load the
lab**, set the desired ID/revision under **Choose your policy**, and run the
selection cell. Then use **Show results** to reopen its last saved results
without resaving or regenerating. Earlier `my-policy.yaml` and
`own-active-*.json` and `outputs/generated/policies/` files are left untouched; new experiments use the
policy-specific paths above.

## Change the policy or add cases

Change inputs, not notebook execution code:

- **Policy:** edit [customer-support.yaml](./data/policies/customer-support.yaml),
  or create another policy file under `data/policies` and select it with
  `policy_path` in [lab.yaml](./data/lab.yaml). Set its ID/revision, context,
  prohibited behavior, and permitted behavior.
- **Generation and model settings:** edit counts, `max_turns`, model-role
  aliases, and `comparison_targets` in [lab.yaml](./data/lab.yaml).
- **Custom tests:** open the current suite's `extra-tests.jsonl` using the
  notebook's generated-file link. ASSERT generates one permitted and one
  prohibited starter prompt each time you create a new suite and run starter
  generation. Edit those examples or copy an entry to add your own. The file
  accepts prompt and scenario cases and may be empty. Keep the generated
  `starter-` IDs; give additional cases unique `manual-` IDs, the policy's `behavior` label, and a
  `dimensions.behavior` category matching the reviewed taxonomy exactly.
  Copy an existing entry and follow the guidance in
  [03_assert_flow.ipynb](./notebooks/03_assert_flow.ipynb).

For a different policy, generate and review a new taxonomy and fresh main and
editable starter tests, then review and combine them before evaluation. Changing frozen cases, the policy,
or shared evaluation settings requires fresh review; do not edit a frozen suite
to reuse its approval.

Return to **Define the policy** and **Configure the evaluation** in the flow
notebook to reload edited inputs. Model-connection setup does not need repeating.

## Evaluation budget and interpretation

Generator/judge calls allow up to **8,192 tokens**; tester/target calls allow up
to **4,096 tokens**, including reasoning. The default three-target evaluation
makes up to 66 target, 36 tester, and 42 judge logical calls, plus generation.
Connection checks make two requests per active model. Retries and additional
cases increase usage.

**Show results** separates prompts from conversations and reports:

- **Policy violations:** prohibited behavior among applicable scored cases.
- **Unnecessary refusals:** refusal of permitted help among applicable scored
  cases.
- **Missing, failed, or skipped outcomes:** inspect these before interpreting
  rates. An unavailable rate is not zero.

One conversation receives one verdict over its full transcript. Inspect the
linked failure evidence, not only the last response. Judge assessments need
human interpretation; the judge is itself a compared model. Comparisons are
descriptive, not production certification.

## Where files are saved

The deployment notebook generates `env/.env` and
`outputs/generated/deployment.json`. These hold connection settings, not keys.

Under `outputs/generated/`:

- `active-suite.json` and `active-runs.json` select saved inputs and runs.
- `collections/c-<hash>/` groups new suites for one policy/revision.
  `collection.json` identifies the policy; each `s-<id>/` subfolder holds a
  suite's policy/tests and model-run folders containing transcripts, scores,
  metrics, and configuration. Short folder names avoid Windows path limits.
- `suites/` retains older results in their original locations.
- `comparison.json` contains the displayed side-by-side results.

Generated collections, runs, selection files, and learner-created policy YAML
files are ignored by Git. The shipped `customer-support.yaml`, lab settings,
and notebook code remain version controlled. Keep local experiment files if
you want to reopen results; they will not be available from a fresh clone.

## Cleanup

When finished, open [X_destroy.ipynb](./notebooks/X_destroy.ipynb).
Its confirmation flags **may already be true**; inspect them before running.

The standard notebook uses Azure CLI's selected subscription. Verify/select the
**subscription recorded in generated settings** and confirm the dedicated group:

```powershell
az account set --subscription '<recorded-subscription-id>'
az account show --query '{subscription:id,name:name}' --output table
```

Follow the notebook's deletion, soft-delete purge, and resource-group cleanup
steps. Deletion is destructive; run cleanup only when you no longer need the
Azure resources.
