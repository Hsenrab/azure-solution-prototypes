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
   aliases are `older`, `intermediate`, and `newer`.
3. Run the catalog/quota checks and complete the notebook's Azure Policy review.
   Resolve any blocked selection before deploying.
4. Run the Bicep deployment and export the generated connection settings.

This creates the Foundry account/project and selected model deployments.
Do not hand-author `env/.env` or copy [.env.example](./env/.env.example): the notebook generates the
actual environment settings and deployment metadata.

### 3. Connect models and configure the policy

Open [02_configure.ipynb](./notebooks/02_configure.ipynb):

1. Load the generated settings.
2. Run **Connect models** to check text and structured JSON responses.
3. Under **Define the policy**, edit
   [customer-support.yaml](./data/policies/customer-support.yaml) to describe
   application context, prohibited behavior, and permitted help.
4. Under **Configure the evaluation**, review [lab.yaml](./data/lab.yaml):
   selected policy, generation counts, maximum turns, generator/tester/judge
   aliases, and comparison targets.

Defaults are **8 generated prompts + 4 adaptive scenarios**, with at most
**3 user/target exchanges** per scenario. The two included handwritten prompts
bring the total to **14 cases per target**.

### 4. Generate, review, evaluate, and compare

Open [03_test.ipynb](./notebooks/03_test.ipynb):

1. Run **Load the lab**.
2. Under **Generate and review tests**, generate the taxonomy and inspect its
   categories and permitted/prohibited classifications. Set
   `TAXONOMY_REVIEWED = True` only after reviewing it.
3. Generate candidate cases and inspect every prompt and scenario. Edit
   [extra-tests.jsonl](./data/extra-tests.jsonl) if you want additional cases.
4. After reviewing the cases, set `GENERATED_CASES_REVIEWED = True` and run the
   review/merge steps.
5. Under **Approve frozen inputs**, set `APPROVE_REVIEWED_SUITE = True` only
   after inspecting the final cases, policy, and settings.
6. Run **Run the evaluation** and wait for ASSERT's CLI pipeline to finish.
7. Run **Show results** and **Inspect real failure evidence**.
8. Under **Compare models**, run the unpaid preview and review the remaining
   targets. Run **Evaluate missing targets (paid)**, then display the comparison.

Do not use **Run All** to bypass review. Set each confirmation flag only after
completing the corresponding review. Compare models on the same approved test
set; do not regenerate tests between targets.

## Resume an existing comparison

For results only, run **Load the lab** followed by **Show results** in
[03_test.ipynb](./notebooks/03_test.ipynb). Use the comparison display cell to
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

## Change the policy or add cases

Change inputs, not notebook execution code:

- **Policy:** edit [customer-support.yaml](./data/policies/customer-support.yaml),
  or create another policy file under `data/policies` and select it with
  `policy_path` in [lab.yaml](./data/lab.yaml). Set its ID/revision, context,
  prohibited behavior, and permitted behavior.
- **Generation and model settings:** edit counts, `max_turns`, model-role
  aliases, and `comparison_targets` in [lab.yaml](./data/lab.yaml).
- **Handwritten tests:** edit [extra-tests.jsonl](./data/extra-tests.jsonl).
  It accepts prompt and scenario cases and may be empty. Each case needs a
  unique `manual-` ID, the policy's `behavior` label, and a
  `dimensions.behavior` category matching the reviewed taxonomy exactly.
  Both formats are demonstrated in
  [03_test.ipynb](./notebooks/03_test.ipynb).

For a different policy, generate and review a new taxonomy, update handwritten
category names, and approve a new suite. Changing approved cases, the policy,
or shared evaluation settings requires fresh review; do not edit a frozen suite
to reuse its approval.

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
- `suites/` contains approved policy/tests and each target's transcripts,
  scores, metrics, and configuration.
- `comparison.json` contains the displayed side-by-side results.

Generated files are ignored by Git. Keep them if you want to reopen results.

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
