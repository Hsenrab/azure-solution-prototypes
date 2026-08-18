# LiteLLM + Foundry GPT-5.4 for Claude Code

## Problem statement

Developers want to keep using Claude Code's Anthropic Messages API while routing requests to a GPT-5.4 model deployed in Azure AI Foundry.

## Hypothesis

If LiteLLM is hosted behind a public HTTPS Azure Container App, configured with a Foundry GPT-5.4 deployment, then Claude Code can use the generated proxy URL and API key without a local adapter or Anthropic model endpoint.

## What this deploys

- Azure AI Services account using the current Foundry `AIServices` pattern.
- Foundry project and a parameterized `gpt-5.4` `GlobalStandard` deployment.
- Basic Azure Container Registry for the custom LiteLLM image.
- Azure Container Apps environment with Log Analytics.
- Azure Database for PostgreSQL Flexible Server (`Standard_B1ms`, 32 GiB, no HA) for LiteLLM authentication state.
- Public HTTPS Container App running LiteLLM on port 4000.
- LiteLLM model alias `azure-gpt-5.4`, exposed through `/v1/messages`.

The Foundry account deliberately has `disableLocalAuth: false`: LiteLLM needs the account API key for this API-key-enabled prototype. The key is retrieved after the first deployment and passed as a Container App secret; it is never stored in Bicep source. PostgreSQL is required by the current LiteLLM image for bearer-key authentication, including `/v1/messages`.

The PostgreSQL configuration is intentionally the lowest-cost practical prototype shape: Burstable `Standard_B1ms`, 32 GiB storage, seven-day backup retention, no high availability, and public access limited to Azure services. It is not a production database configuration.

## Quick start

Run notebooks in order with the demo kernel:

1. `notebooks/00_setup.ipynb` creates the virtual environment, logs into Azure, and installs the notebook requirements.
2. `notebooks/01_deploy_infra.ipynb` validates the model parameters, deploys Foundry and the Container Apps environment, builds the LiteLLM image in ACR, enables the public proxy, and writes the URL and keys to `env/.env`.
3. `notebooks/02_configure.ipynb` checks public HTTPS health and sends an authenticated Claude-compatible `/v1/messages` request.
4. `notebooks/03_test.ipynb` sends an Anthropic Messages API request and saves the response to `outputs/last-message.json`.
5. `notebooks/X_destroy.ipynb` deletes the resource group and purges the soft-deleted Foundry account.

Before running the deployment notebook, verify `MODEL_NAME` and `MODEL_VERSION` against the target region. The default values match the current prototype convention but model availability and versions change by region.

## Configure Claude Code

After notebook 01, load the generated values into the shell where Claude Code runs. PowerShell example:

```powershell
$env:ANTHROPIC_BASE_URL = "https://<container-app-fqdn>"
$env:ANTHROPIC_AUTH_TOKEN = "<LITELLM_MASTER_KEY>"
$env:CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY = "1"
claude --model azure-gpt-5.4
```

Use the exact `LITELLM_PROXY_URL` and `LITELLM_MASTER_KEY` values from `env/.env`. The proxy serves Claude Code's Anthropic Messages API at `https://<container-app-fqdn>/v1/messages` and model discovery at `/v1/models`.

## Public API test

The equivalent request is:

```powershell
$headers = @{ Authorization = "Bearer $env:ANTHROPIC_AUTH_TOKEN" }
$body = @{ model = "azure-gpt-5.4"; max_tokens = 120; messages = @(@{ role = "user"; content = "Say hello from Foundry." }) } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "$env:ANTHROPIC_BASE_URL/v1/messages" -Method Post -Headers $headers -ContentType "application/json" -Body $body
```

## Prototype limitations

This is an internet-facing feasibility demo. The generated LiteLLM master key is the only proxy access control. It does not add Entra authentication, rate limiting, per-user virtual keys, budgets, private networking, WAF protection, or automated secret rotation. Add those controls before production use.

The Container App uses a single LiteLLM replica by default and the Foundry model deployment uses a parameterized version. A deployment failure caused by model availability should be fixed by selecting a supported model/version for the region, not by changing the proxy code.