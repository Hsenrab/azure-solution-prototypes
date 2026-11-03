# Demo Workflow

## Goal
Create or extend a lightweight, runnable Azure demo that validates one clear hypothesis.

## Create Flow
1. Define one customer problem and one testable hypothesis.
2. Create `demos/<demo-name>/` from `demo-template/`.
3. Keep only the minimum infra/code needed for hypothesis validation.
4. Populate `metadata.json` using `demo-template/metadata.json` fields exactly.
5. Ensure plain-language setup and verification steps in `README.md`.

## Extend Flow
1. Confirm the next hypothesis and what minimal delta is needed.
2. Keep changes small and justify each change.
3. Update `README.md` and `metadata.json` when scope changes.
4. Prefer notebook changes over app code unless code is required.

## Spec Kit Workflow

Use Spec Kit for every new or extended demo. Before `/speckit-specify`, load this
reference and the applicable repository instructions. Treat the rules below as the
single detailed authoring procedure for Specify, Plan, Tasks, and Implement; the
Spec Kit command templates and examples are generic scaffolding, not requirements
to create application frameworks, tests, or extra artifacts.

### Bounded artifact discovery before Specify

First decide whether the request creates a demo or extends one. Discover only
artifacts compatible with the stated hypothesis and constraints; do not inventory
the whole repository.

- **New demo:** inspect `demo-template/` for the expected shape, the canonical
  setup/destroy notebooks named in the repository instructions, and up to three
  existing demos selected by service, identity/network constraints, or journey.
- **Extend demo:** inspect the target demo's relevant Bicep, notebooks, helpers,
  scripts, README, metadata, and existing feature artifacts; compare with at most
  two close examples only when a specific compatibility question remains.
- For each candidate, record its repository-relative path, what behavior it
  demonstrates, relevant compatibility constraints, and whether it is a plausible
  reuse candidate. Search further only to answer an unresolved question that could
  change scope, feasibility, or a hard constraint.
- Do not run notebooks, deploy or query Azure, access credentials, or change live
  resources during discovery. Reusing code or resource definitions does not
  authorize reusing, modifying, or deleting live Azure resources.

Specify remains about the user problem, hypothesis, observable outcomes, and
compatibility boundaries. Carry a short existing-context summary and concrete
source paths into the feature artifacts; do not turn discovery into a full
architecture inventory or retrospective specification.

### Plan and Tasks handoff

Plan records a source-and-decision table for relevant existing Bicep, notebooks,
helpers, scripts, demo metadata/docs, and prior specs/plans. For each, cite the
path and choose **reuse unchanged**, **adapt**, **do not reuse**, or **new**;
explain the decision briefly. Explicitly carry forward identity, authentication,
network, deployment, subscription, generated-environment, and live-operation
constraints where relevant. A proposed approach must satisfy these constraints
before it is selected. Prefer existing patterns and minimal deltas; keep each
demo self-contained under `demos/<demo-name>/` and do not introduce a shared
runtime framework by default.

Tasks name only work needed for the approved delta, including directly related
documentation/metadata and proportional validation. Do not add generic project
initialization, frameworks, dependencies, broad test matrices, or test-first/TDD
work by default. Add focused automated tests when requested or justified by
changed logic. Always preserve existing quality gates and provide one concise,
runnable hypothesis-validation journey with observable expected results. Include
the generated `env/.env` handoff, canonical setup/destroy flows, notebook hygiene,
and explicit live-Azure approval when applicable.

Implement follows the recorded reuse decisions and constraints. Run relevant
existing checks; distinguish offline validation from Azure-dependent acceptance.
Do not treat an unrun live scenario as passed, alter prior experiment results, or
weaken historical failures. Report which sources were reused/adapted/rejected,
what remains unverified, and any constraint that prevented reuse.

### Evidence and customization boundaries

The following research informs this workflow. These sources describe different
tools and are not evidence of identical behavior across coding agents:

- **Documented Spec Kit behavior:** The
  [existing-project guide](https://github.github.com/spec-kit/guides/existing-projects.html)
  recommends bounded changes and checking repository architecture during Plan;
  it does not prescribe a bounded artifact scan before Specify. The
  [customization guide](https://github.github.com/spec-kit/guides/customization.html)
  supports project-local template overrides, presets, and extensions for different
  customization needs. The
  [upgrade guide](https://github.github.com/spec-kit/upgrade.html) documents
  manifest-aware integration upgrades and warns that locally modified managed
  files require review.
- **Documented Copilot behavior:** GitHub recommends short, broadly applicable
  repository instructions and task-specific skills
  ([custom instructions](https://docs.github.com/en/copilot/concepts/prompting-and-context/custom-instructions),
  [agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)).
  Supported instruction types and precedence vary by Copilot client and surface;
  some combine instructions without a general precedence order. Do not assume
  Spec Kit skills, Copilot instructions, `AGENTS.md`, `CLAUDE.md`, or other
  agent-specific files load or override one another identically.
- **Demonstrated community patterns:** The
  [Radius multi-repository discussion](https://github.com/github/spec-kit/discussions/1119)
  reports accurate source paths and implementation patterns across a workspace,
  while requiring confirmation before editing the code repository. A
  [brownfield walkthrough](https://github.com/jbarbosa26/SpecKit/blob/main/docs/04-adapting-existing-projects.md)
  demonstrates naming existing modules in Specify and recording deviations in
  Plan. The
  [brownfield extension proposal and discussion](https://github.com/github/spec-kit/issues/1436)
  explores automated discovery, but community feedback identifies integration
  and bootstrap limitations; it is not evidence this repository needs an extension.
- **Repository fit (recommendation):** Keep the detailed procedure here, link it
  from the relevant Spec Kit skills, and use supported project-local template
  overrides for artifact-shape changes. This reuses the already-loaded Azure
  authoring skill and avoids a new agent, extension, or duplicated checklist.
  Overrides are preferable to editing managed core templates because their
  documented resolution layer is designed for local customization. Any locally
  changed managed skill still needs review when upgrading the Copilot integration.
  A preset could share more workflow behavior, but adds installation,
  compatibility, and maintenance work not justified for this single repository.

### Representative dry-run handoff

These are file-only examples of the expected authoring decisions, not Azure
validation or claims that a feature was implemented.

| Phase | New demo: hypothetical keyless Foundry scenario | Extend demo: Search pagination |
|---|---|---|
| Specify discovery | Inspect `demo-template/`, `demos/speech01-foundry-speech/notebooks/00_setup.ipynb`, `demos/speech01-foundry-speech/notebooks/X_destroy.ipynb`, and up to two relevant Foundry demos. Note which Bicep files set local auth/network properties before claiming a template is compatible. | Inspect `demos/search02-hybrid-pagination/infra/`, `app/notebook_helpers.py`, the relevant notebooks, README, metadata, and `specs/001-provision-search-debug/` plus `specs/003-vector-only-contribution/`. |
| Plan decision | Reuse the demo shape and canonical notebook flow with only permitted substitutions. Adapt a demo-owned Bicep file only after checking identity/network/deployment constraints; reject an otherwise similar Bicep pattern if its auth mode conflicts. Keep all runtime files in the new demo folder. | Reuse the target's Bicep and generated-environment contract unchanged unless the hypothesis requires a platform change; reuse its helper/notebook conventions. Adapt only identified scenario files. Do not redeploy or touch live resources as part of this authoring workflow. |
| Tasks/validation | List only required demo files and metadata/docs. Provide one runnable hypothesis journey and existing notebook checks; live Azure steps remain separately gated by explicit approval. | List only necessary app/notebook/docs/metadata deltas and focused checks justified by changed logic. Preserve existing notebook CI/pre-commit gates and identify prior acceptance evidence without editing it. |

## Required Demo Shape
- `README.md`
- `metadata.json`
- `infra/`, `env/`, `docs/`
- `notebooks/` with at least `00_setup.ipynb` through `03_test.ipynb`
- `app/` only when notebook-only implementation is insufficient

## Notebook Journey
1. `00_setup.ipynb`: prerequisites, `az login`, package install.
2. `01_deploy_infra.ipynb`: deploy infra, capture outputs, write `env/.env`.
3. `02_configure.ipynb`: post-deploy SDK/service configuration.
4. `03_test.ipynb`: execute the scenario and validate the hypothesis.

`env/.env` must be generated by `01_deploy_infra.ipynb`, not manually authored.

## Notebook Coding Conventions

### Python SDK first; CLI fallback
Prefer Python Azure SDKs for notebook and app operations whenever feasible. For function-centric demos, prefer `azure-identity`, `azure-storage-blob`, and `azure-mgmt-web` over shelling out to `az`.

When Azure CLI is still required, every `subprocess.run` call that invokes `az` must capture stderr and surface it in the error message. Never use `check=True` alone — it swallows the actual Azure error. Use this pattern inline in every cell that calls the CLI:

```python
result = subprocess.run([az_cmd, ...], capture_output=True, text=True)
if result.returncode != 0:
    raise RuntimeError(
        f"az ... failed (exit {result.returncode})\n"
        f"stderr: {result.stderr.strip()}\n"
        f"stdout: {result.stdout.strip()}"
    )
value = result.stdout.strip()
```

Do not extract this into a shared helper function — keep each notebook cell self-contained even if the pattern repeats.

## Scoped Azure Policy review

Include inherited assignments explicitly with the `atScope()` filter; disabling
strict scope matching alone does not reliably include management-group assignments.
Resolve initiatives, member definitions, effective parameters/effects, exemptions,
exclusions, overrides, and enforcement before approving an access pattern.

On Windows PowerShell, use stop-parsing with environment variables so `az.cmd`
receives the quoted parentheses intact:

```powershell
$env:AZURE_SUBSCRIPTION_ID = '<confirmed-subscription-id>'
$env:AZURE_POLICY_SCOPE = "/subscriptions/$env:AZURE_SUBSCRIPTION_ID"
az --% policy assignment list --subscription %AZURE_SUBSCRIPTION_ID% --scope %AZURE_POLICY_SCOPE% --filter "atScope()" --disable-scope-strict-match true --output json
az --% policy exemption list --subscription %AZURE_SUBSCRIPTION_ID% --scope %AZURE_POLICY_SCOPE% --filter "atScope()" --disable-scope-strict-match true --output json
```

Repeat for the intended/actual resource-group scope. An empty unfiltered result is
not proof of no inherited restrictions. Use the definition's actual management-group,
subscription, or built-in scope when resolving it; current CLI `show` commands use
`--name` and scope arguments rather than assuming `--id` is supported.
