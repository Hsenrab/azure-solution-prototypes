# Copilot instructions for this repository

## Intent
Help engineers create and extend lightweight Azure prototype demos quickly.

## Always-on Guardrails
- Optimize for feasibility and learning, not production hardening.
- Keep each demo self-contained under `demos/<demo-name>/`.
- Keep dependencies minimal and setup language plain.
- Prefer smaller notebook cells with one task per cell instead of large multi-purpose cells.
- Prefer Python Azure SDK usage over Azure CLI subprocess calls in notebooks/app code whenever the SDK supports the required operation; use CLI only as a fallback.
- Before changing deployment methods, authentication patterns, or core tooling, validate the proposed approach against the demo's hard constraints (for example managed-identity-only storage, disabled shared keys, network restrictions, or no-local-auth settings). If the approach violates those constraints, do not propose or implement it as the default path.
- Prioritize root-cause fixes that make the end-to-end flow succeed. Avoid adding extra defensive checks for temporary blockers unless the user explicitly asks for hardening or diagnostics.
- Prefer clean happy-path flows for learning: fail fast on missing prerequisites instead of adding fallback or backup paths.
- For Azure operations in multi-subscription contexts, do not assume the first enabled subscription. Prefer `AZURE_SUBSCRIPTION_ID` when present, or resolve the subscription by locating the target resource group/resource.
- When local deployment is blocked by storage network rules, do not auto-apply tenant-specific network changes in notebooks; direct users to run the local script in `demos/<demo>/scripts/` and include the exact command in the error message.
- No backward compatibility requirement by default; prefer simpler forward-looking changes unless compatibility is explicitly requested.
- Avoid enterprise-scale architecture unless explicitly requested.
- If uncertain, provide a sensible recommendation and label it as a recommendation.

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
- When deciding what to do next, explicitly state the key assumptions driving that decision (for example environment state, user intent, or dependency availability) so the user can quickly validate or correct them.
- When dismissing or not choosing an option, explicitly state that it is being ruled out and why (for example platform limitations, hard constraints, missing capabilities, or incompatible configuration).

## Source of Truth
- Keep reusable procedures in skill references under `.github/skills/.../references/`.
- Avoid duplicating detailed workflow checklists in prompt files.
