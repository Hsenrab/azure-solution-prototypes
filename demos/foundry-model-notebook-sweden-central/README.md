# Foundry model prompt test (Sweden Central)

## Purpose

Deploy an Azure AI Foundry-compatible model endpoint in **Sweden Central**, then validate end-to-end feasibility by running prompts against it — entirely from notebooks.

## Notebook journey

The demo is driven by three numbered notebooks in `notebooks/`. Run them in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, log in to Azure, install Python packages, create `.env` |
| `01_deploy_infra.ipynb` | Create resource group and deploy Bicep template via Azure CLI; retrieve and save endpoint + key to `.env` |
| `02_prompt_test.ipynb` | Load `.env`, create OpenAI client, run baseline and scenario prompts |

## Infrastructure

Defined in `infra/main.bicep`. Deployed **from within `01_deploy_infra.ipynb`** — no separate shell scripts needed.

- Azure OpenAI account (`S0` tier) in Sweden Central
- Model deployment: `gpt-4o-mini` (configurable in notebook)

## Quick start

1. Open `notebooks/00_setup.ipynb` and follow each step.
2. Continue to `notebooks/01_deploy_infra.ipynb`.
3. Finish with `notebooks/02_prompt_test.ipynb`.

That's it. The notebooks guide you through every step.

## Recommendation

Recommendation: start with `gpt-4o-mini` for cost-effective feasibility testing, then swap the model name in `01_deploy_infra.ipynb` once baseline behaviour is confirmed.

## Cost note

Run the tear-down cell in `01_deploy_infra.ipynb` when finished to delete all resources and stop charges.
