# Foundry model prompt test (Sweden Central)

## Purpose

Deploy an Azure AI Foundry-compatible model endpoint in **Sweden Central**, then run a notebook prompt against that deployment to validate end-to-end feasibility.

## Components

- `infra/main.bicep` - minimal Azure OpenAI account + model deployment
- `env/.env.example` - environment variable template
- `notebooks/prompt_test.ipynb` - prompt execution against deployed model
- `scripts/` - helper commands
- `docs/architecture-notes.md` - assumptions and constraints

## Quick start

1. Prerequisites: Azure CLI, Bicep support, Python 3.10+.
2. Copy `env/.env.example` to `.env` and fill values.
3. Deploy infrastructure:
   - `az login`
   - `az account set --subscription <subscription-id>`
   - `az deployment group create --resource-group <rg> --template-file infra/main.bicep --parameters location=swedencentral accountName=<unique-name> modelName=gpt-4o-mini deploymentName=chat`
4. Open and run `notebooks/prompt_test.ipynb`.

## Recommendation

Recommendation: start with a low-cost model deployment for feasibility runs, then adjust model/version after confirming baseline behavior.

## Notebook usefulness

Yes. Notebook is useful for rapid prompt iteration and qualitative validation with customer-like prompts.

## Infrastructure needed

Yes. This demo requires an Azure OpenAI/Foundry deployment before notebook execution.
