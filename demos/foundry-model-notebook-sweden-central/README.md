# Foundry model prompt test (Sweden Central)

## Purpose

Deploy an **Azure AI Services** (new Azure AI Foundry) model endpoint in **Sweden Central**, then
validate end-to-end feasibility by running prompts against it — entirely from notebooks.

## Research basis

| Decision | Classic approach | This demo (new Foundry) |
|---|---|---|
| Bicep resource kind | `kind: 'OpenAI'` | `kind: 'AIServices'` |
| Endpoint format | `https://<name>.openai.azure.com/` | `https://<name>.services.ai.azure.com/` |
| Python SDK | `openai.AzureOpenAI` | `azure-ai-inference.ChatCompletionsClient` |
| Model scope | OpenAI models only | Multi-model (OpenAI + others in Foundry catalog) |
| Model | `gpt-4o-mini` *(deprecated Jul 2025)* | `gpt-4.1-mini` (2025-04-14) |
| Deployment SKU | implicit | `GlobalStandard` (explicit, required by API 2024-10-01) |

**Model note:** `gpt-4o-mini` deprecation date is July 2025, retirement March 2026.
`gpt-4.1-mini` is the designated replacement available in Sweden Central.

## Notebook journey

Run the notebooks in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, log in to Azure, install `azure-ai-inference` |
| `01_deploy_infra.ipynb` | Create resource group, deploy Bicep (`kind: AIServices`), write `env/.env` |
| `02_configure.ipynb` | Verify deployment is ready via CLI + API ping (new Foundry SDK) |
| `03_test.ipynb` | Load `.env`, create `ChatCompletionsClient`, run baseline and scenario prompts |

## Infrastructure

Defined in `infra/main.bicep`. Deployed **from within `01_deploy_infra.ipynb`** — no separate shell scripts needed.

- Azure AI Services account (`kind: AIServices`, S0 tier) in Sweden Central
- Model deployment: `gpt-4.1-mini` (configurable in notebook), `GlobalStandard` SKU

## Quick start

1. Open `notebooks/00_setup.ipynb` and follow each step.
2. Continue to `notebooks/01_deploy_infra.ipynb` — deploys infra and writes `env/.env`.
3. Run `notebooks/02_configure.ipynb` — verifies the deployment is ready.
4. Finish with `notebooks/03_test.ipynb`.

## Cost note

Run the tear-down cell in `01_deploy_infra.ipynb` when finished to delete all resources and stop charges.
