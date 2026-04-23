# Foundry model prompt test (Sweden Central)

## Purpose

Deploy an Azure AI Foundry-compatible model endpoint in **Sweden Central**, then validate end-to-end feasibility by running prompts against it — entirely from notebooks.

## Notebook journey

The demo is driven by three numbered notebooks in `notebooks/`. Run them in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, log in to Azure, install Python packages, check `.env` |
| `01_deploy_infra.ipynb` | Create resource group and deploy Bicep template via Azure CLI; retrieve and write endpoint + key to `env/.env` automatically |
| `02_configure.ipynb` | Use Python SDK to verify the model deployment is ready (for richer demos: create indexes, upload data, configure services) |
| `03_test.ipynb` | Load `.env`, create OpenAI client, run baseline and scenario prompts |

## Infrastructure

Defined in `infra/main.bicep`. Deployed **from within `01_deploy_infra.ipynb`** — no separate shell scripts needed.

- Azure OpenAI account (`S0` tier) in Sweden Central
- Model deployment: `gpt-4o-mini` (configurable in notebook)

## Quick start

1. Open `notebooks/00_setup.ipynb` and follow each step.
2. Continue to `notebooks/01_deploy_infra.ipynb` — deploys infra and writes `env/.env`.
3. Run `notebooks/02_configure.ipynb` — verifies the deployment is ready.
4. Finish with `notebooks/03_test.ipynb`.

That's it. The notebooks guide you through every step.

## Recommendation

Recommendation: start with `gpt-4o-mini` for cost-effective feasibility testing, then swap the model name in `01_deploy_infra.ipynb` once baseline behaviour is confirmed.

## Cost note

Run the tear-down cell in `01_deploy_infra.ipynb` when finished to delete all resources and stop charges.
