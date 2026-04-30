# Copilot instructions for this repository

## Intent

Help engineers create and extend lightweight Azure prototype demos quickly.

## Guardrails

- Optimize for feasibility and learning, not production hardening.
- Keep each demo self-contained under `demos/<demo-name>/`.
- Do not introduce enterprise-scale architecture unless explicitly requested.
- Prefer plain language, minimal dependencies, and readable setup steps.
- For teaching-oriented notebooks, prefer explicit repeated code in separate cells over helper functions or abstractions when repetition makes the flow easier to follow.

## Required demo shape

When creating a new demo, always include:

- `README.md`
- `metadata.json`
- `infra/`, `env/`, `docs/`
- `notebooks/` with the standard 4-notebook journey (see below)
- `app/` only when code is needed beyond what the notebooks cover

## Notebook standard

Every demo uses numbered notebooks as the primary interface. The standard structure is:

| Notebook | Purpose |
|---|---|
| `00_setup.ipynb` | Prerequisites, `az login`, `pip install` |
| `01_deploy_infra.ipynb` | Deploy Bicep via Azure CLI; retrieve outputs; write `env/.env` automatically |
| `02_configure.ipynb` | Python SDK post-deploy setup (create indexes, upload data, etc.) — skip steps not applicable |
| `03_test.ipynb` | Load `env/.env`, exercise scenario, validate hypothesis |

`env/.env` is **never filled in manually**. It is always written by `01_deploy_infra.ipynb` from the deployed resource outputs.

## Metadata

Always populate the fields from `demo-template/metadata.json` exactly.

## Recommendations style

If uncertain, provide a sensible recommendation and clearly label it as a recommendation.

## Research requirement

Before implementing or extending a demo, **always research the current best practice** for the Azure services involved:

- Differentiate between **classic Azure AI (Azure OpenAI, hub-based Foundry)** and **new Azure AI Foundry** — use new Foundry only.
- Check the Azure AI Foundry model catalog for the latest non-deprecated model and version for the target region.
- Identify the current stable Bicep API version for each resource type.
- Note any features that are still in preview and label them `[PREVIEW]` in notebook markdown.

## New Azure AI Foundry standard

| Concern | Classic | New Foundry (use this) |
|---|---|---|
| Bicep resource kind | `kind: 'OpenAI'` | `kind: 'AIServices'` |
| Bicep deployment SKU | omitted | `GlobalStandard` (explicit, required by API 2024-10-01+) |
| Endpoint format | `https://<name>.openai.azure.com/` | `https://<name>.services.ai.azure.com/` |
| Python inference SDK | `openai.AzureOpenAI` | `azure-ai-inference.ChatCompletionsClient` |
| Env variable prefix | `AZURE_OPENAI_*` | `AZURE_AI_*` |

`gpt-4o-mini` is deprecated (Jul 2025) and retires Mar 2026. Default to `gpt-4.1-mini` (version `2025-04-14`) or the current recommended model at research time.
