# Copilot instructions for this repository

## Intent
Help engineers create and extend lightweight Azure prototype demos quickly.

## Always-on Guardrails
- Optimize for feasibility and learning, not production hardening.
- Keep each demo self-contained under `demos/<demo-name>/`.
- Keep dependencies minimal and setup language plain.
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

## Source of Truth
- Keep reusable procedures in skill references under `.github/skills/.../references/`.
- Avoid duplicating detailed workflow checklists in prompt files.
