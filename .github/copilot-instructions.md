# Copilot instructions for this repository

## Intent
Help engineers create and extend lightweight Azure prototype demos quickly.

## Always-on Guardrails
- Optimize for feasibility and learning, not production hardening.
- Keep each demo self-contained under `demos/<demo-name>/`.
- Keep dependencies minimal and setup language plain.
- Prefer smaller notebook cells with one task per cell instead of large multi-purpose cells.
- Prefer Python Azure SDK usage over Azure CLI subprocess calls in notebooks/app code whenever the SDK supports the required operation; use CLI only as a fallback.
- Prefer Bicep as the default place for infrastructure and platform behavior changes (resource properties, auth mode, networking, deployment defaults) instead of patching notebooks/app code to work around infra drift.
- Before changing deployment methods, authentication patterns, or core tooling, validate the proposed approach against the demo's hard constraints (for example managed-identity-only storage, disabled shared keys, network restrictions, or no-local-auth settings). If the approach violates those constraints, do not propose or implement it as the default path.
- Prioritize root-cause fixes that make the end-to-end flow succeed. Avoid adding extra defensive checks for temporary blockers unless the user explicitly asks for hardening or diagnostics.
- Prefer global fixes over local fixes when feasible: if an issue reflects shared behavior, update the common source (infra template, shared helper, or repository-level convention) rather than only patching a single notebook/cell.
- Prefer clean happy-path flows for learning: fail fast on missing prerequisites instead of adding fallback or backup paths.
- For Azure operations in multi-subscription contexts, do not assume the first enabled subscription. Prefer `AZURE_SUBSCRIPTION_ID` when present, or resolve the subscription by locating the target resource group/resource.
- When local deployment is blocked by storage network rules, do not auto-apply tenant-specific network changes in notebooks; direct users to run the local script in `demos/<demo>/scripts/` and include the exact command in the error message.
- No backward compatibility requirement by default; prefer simpler forward-looking changes unless compatibility is explicitly requested.
- Avoid enterprise-scale architecture unless explicitly requested.
- If uncertain, provide a sensible recommendation and label it as a recommendation.

## Enforcement Rules (Infra-first, Global-first)
- MUST implement infrastructure and platform behavior changes in Bicep first (for example auth mode, network mode, SKU, deployment defaults, resource settings).
- MUST treat notebook/app changes as consumers of deployed behavior, not the primary place to define infrastructure behavior.
- MUST prefer one happy-path flow for learning demos unless the user explicitly asks for alternatives or hardening.
- MUST align with existing demo patterns when they already satisfy the request; do not introduce new behavior patterns without an explicit user ask.
- DO NOT add local toggles/branches in notebooks for behavior that can be defined in Bicep.
- DO NOT patch around infra drift only in one notebook when the root cause is an infra template value.
- DO NOT add in-cell fallback handling for missing data, invalid configuration, or deployment drift.
- DO NOT add proactive diagnostic or verification branches in notebooks unless the user explicitly asks for diagnostics.
- DO NOT add catch-and-explain wrappers in notebooks just to reformat errors. Prefer raw underlying errors and fix the upstream cause.
- DO NOT ship "catch-and-explain only" changes as a fix. If the code only catches/reports an error without removing the upstream cause, the task is not complete.
- MUST prefer global/root-cause fixes over local fixes: shared helper, shared template, or repo-level convention before single-cell workaround.
- If a local workaround is temporarily unavoidable, explicitly mark it temporary, explain why global fix was not possible yet, and include the follow-up global fix.

### Destroy Notebook Standardization
- ALL demos MUST use the `speech01-foundry-speech/notebooks/X_destroy.ipynb` as the source of truth.
- Copy `speech01/X_destroy.ipynb` verbatim into new demos: `demos/<demo-name>/notebooks/X_destroy.ipynb`.
- In the `demo-template/notebooks/X_destroy.ipynb`, keep all confirmation flags set to `False` (conservative defaults for template safety).
- For production demos (in `demos/<demo-name>/`), confirmation flags may be `True`.
- This ensures: (1) standardized soft-delete purge pattern across all demos, (2) deterministic cleanup that works reliably, (3) resource names become immediately reusable after purge.

### Setup Notebook Standardization
- ALL demos MUST use `speech01-foundry-speech/notebooks/00_setup.ipynb` as the source-of-truth structure and flow.
- For new demos, copy `speech01/00_setup.ipynb` and only apply minimal demo-specific substitutions:
	- demo kernel display name (for example `Python (<demo-name>)`)
	- final "Continue with" notebook path/text when needed
	- dependencies implied by each demo's own `requirements.txt`
- DO NOT split or reorder the setup flow steps unless explicitly requested:
	- Step 1: create venv + register kernel
	- Step 2: authenticate Azure + optional subscription selection
	- Step 3: install dependencies from `requirements.txt`
- Keep Azure CLI resolution behavior aligned with `speech01` helper pattern (resolve executable path only; auth flow in setup cells).

### Decision Order
1. Fix in Bicep or shared infra source.
2. Fix in shared helper/module used by multiple notebooks.
3. Fix in one notebook cell only if (1) and (2) are not feasible.

### PR/Change Check
Before finalizing changes, verify and state:
1. Where the root cause was fixed (Bicep/shared/local).
2. Why that scope was chosen.
3. Whether any local workaround remains and the plan to remove it.
4. For notebook errors, confirm no catch-and-explain wrapper was added unless it is required for a true upstream remediation.
5. Confirm the change does more than error messaging by identifying the upstream remediation that was implemented.

## Skill-first Routing
- For create/extend demo workflows, load `azure-demo-authoring` first:
	`.github/skills/azure-demo-authoring/SKILL.md`
- Then load supporting skills only if relevant:
	- `vscode-microsoft-foundry` for end-to-end Foundry agent lifecycle.
	- `microsoft-foundry` for Foundry resources, RBAC, and deployment operations.
	- `cosmosdb-best-practices` for Cosmos DB data model and query changes.
	- `foundrytk-quick-start` for onboarding/feature-discovery requests.
	- `use-winml-cli` for non-generative ONNX/Windows ML scenarios.

## Communication
- When referring to a notebook cell, never use cell numbers. Instead refer to it by its markdown heading (e.g. "the **Step 3** cell") or by what it does (e.g. "the Bicep deployment cell"). Cell numbers are invisible to users and change as cells are added or removed.
- If inferred or previously requested constraints make a solution materially more complex, explicitly call that out before implementation and summarize the simpler alternative.
- For any significant shift in architecture, workflow, tooling, deployment pattern, or authentication strategy requested by the user, provide a concise pros/cons list so the user can make an informed decision before proceeding.
- For any significant strategy decision (for example architecture, workflow, deployment pattern, authentication mode, or major trade-off choice), MUST ask for explicit user confirmation before implementing.
- If a user provides a raw error, treat it as an explicit request for diagnosis: explain what the error means in plain language and provide the concrete fix (prefer upstream/root-cause fix over local workaround).
- When a user reports a raw error, first provide meaning + concrete fix, then propose code changes only if they are required for the upstream remediation.
- When deciding what to do next, explicitly state the key assumptions driving that decision (for example environment state, user intent, or dependency availability) so the user can quickly validate or correct them.
- When dismissing or not choosing an option, explicitly state that it is being ruled out and why (for example platform limitations, hard constraints, missing capabilities, or incompatible configuration).

## Source of Truth
- Keep reusable procedures in skill references under `.github/skills/.../references/`.
- Avoid duplicating detailed workflow checklists in prompt files.
