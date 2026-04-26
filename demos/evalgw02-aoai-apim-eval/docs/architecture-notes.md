# Architecture Notes

## Demo Goal

This prototype validates a classic Azure OpenAI deployment fronted by Azure API Management (APIM) using a single stable gateway endpoint:
- APIM endpoint: POST /openai/chat/completions
- Backend API version forced by APIM policy: 2024-10-21

## Resource Topology

All resources are deployed in one resource group in UK South.

- Resource group: rg-evalgw02-uks
- Region: UK South
- Services:
  - Azure OpenAI account (kind OpenAI)
  - APIM (Developer tier)

## Model Deployments

The Azure OpenAI account includes two model deployments:

- Primary deployment: gpt-4o (deployment name chat4o)
- Secondary deployment: gpt-5.1 (deployment name chat51)

APIM routes the public gateway path to the primary deployment by default.

## APIM Gateway Behavior

The APIM operation policy for POST /openai/chat/completions performs:

1. Sets backend to the Azure OpenAI endpoint.
2. Injects Azure OpenAI API key from APIM named value.
3. Forces api-version=2024-10-21.
4. Rewrites URI to /openai/deployments/chat4o/chat/completions.

## Security and Prototype Scope

- This demo uses API key auth for speed and simplicity.
- For production, move to managed identity and tighter network controls.
- Keep env/.env local and never commit secrets.
