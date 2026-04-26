# evalgw02: Azure OpenAI + APIM Gateway + Evaluation

## Problem statement

Teams want a single governed gateway endpoint for Azure OpenAI chat completions while keeping model deployment and evaluation workflows simple and repeatable.

## Hypothesis

A classic Azure OpenAI resource and APIM in one UK South resource group can expose a stable chat-completions endpoint and support evaluation of gateway responses with Azure AI Evaluation SDK.

## Scope

- In scope:
  - Deploy one Azure OpenAI account with gpt-4o and gpt-5.1 deployments.
  - Deploy one APIM service in the same resource group and region.
  - Expose APIM POST /openai/chat/completions and force backend api-version=2024-10-21.
  - Validate APIM endpoint calls.
  - Run evaluations on APIM-generated responses.
- Out of scope:
  - Production networking, private endpoints, and managed identity hardening.
  - Multi-region failover and enterprise scale configuration.

## Notebook journey

Run notebooks in order:

| Notebook | What it does |
|---|---|
| 00_setup.ipynb | Verify prerequisites, Azure login, and install Python packages |
| 01_deploy_infra.ipynb | Create one UK South resource group, deploy Bicep, and write env/.env from outputs |
| 02_configure.ipynb | Validate direct Azure OpenAI and APIM gateway connectivity |
| 03_test.ipynb | Send chat prompts to APIM endpoint and save test outputs |
| 04_evaluate.ipynb | Evaluate APIM responses with Azure AI Evaluation SDK |

## Folder map

```text
infra/      # Bicep for Azure OpenAI + APIM
notebooks/  # numbered notebook flow
env/        # .env.example contract; .env auto-written by notebook 01
app/        # optional app code (unused in this demo)
data/       # synthetic evaluation dataset
docs/       # architecture notes
outputs/    # notebook outputs and evaluation artifacts
```

## Quick start

1. Open notebooks/00_setup.ipynb and run all cells.
2. Run notebooks/01_deploy_infra.ipynb to provision resources and generate env/.env.
3. Run notebooks/02_configure.ipynb and notebooks/03_test.ipynb to verify APIM chat completions.
4. Run notebooks/04_evaluate.ipynb to score APIM responses.

## Known limitations

- APIM routes to the primary deployment (chat4o) by default.
- APIM subscription key retrieval can vary by tenant policy; notebook includes fallback instructions.
- This prototype uses API keys and public network access for speed.

## Cleanup

After validation, delete the resource group to stop charges:

```bash
az group delete --name rg-evalgw02-uks --yes
```
