# Architecture notes

## Component overview

```
┌────────────────────────┐    button click     ┌───────────────────────────────────────────┐
│ notebooks/03_test.ipynb│ ─────────────────▶ │ Custom-container Python Function App      │
│  ipywidgets.Button     │  POST /api/review  │ (Elastic Premium EP1, Linux)              │
│                        │  x-functions-key   │                                           │
│                        │ ◀───── markdown ── │  Python function:                         │
└────────────────────────┘                    │   1. git clone --depth 1 <SAMPLE_REPO_URL>│
                                              │      → /tmp/repo                          │
                                              │   2. subprocess: copilot -p "..."         │
                                              │      env: COPILOT_PROVIDER_*              │
                                              │   3. return { review, duration_s, ... }   │
                                              └──────────────────┬────────────────────────┘
                                                                 │ HTTPS + API key
                                                                 ▼
                                              ┌───────────────────────────────────────────┐
                                              │ Foundry AIServices (kind: AIServices)     │
                                              │  disableLocalAuth: false                  │
                                              │  Deployment: gpt-5.4-mini (GlobalStandard)│
                                              └───────────────────────────────────────────┘
```

Supporting resources (Bicep):
- **Azure Container Registry (Basic)** — hosts the `copilot-review:latest` image. Function App pulls with managed identity (`acrUseManagedIdentityCreds: true`, `AcrPull` role).
- **Function Storage (StorageV2, MI-only, no shared keys)** — `AzureWebJobsStorage__credential: managedidentity`, `Storage Blob Data Owner` role for the Function App identity.
- **App Insights** — connection string wired to the Function App.

## BYOK env-var mapping

The container's Python function passes these environment variables to the `copilot` subprocess (all sourced from Function App app settings, populated by Bicep):

| App setting / subprocess env var | Value | Source |
|---|---|---|
| `COPILOT_PROVIDER_BASE_URL` | `https://<account>.openai.azure.com` (the AIServices endpoint) | Bicep `listKeys` + `endpoint` |
| `COPILOT_PROVIDER_TYPE` | `azure` | Bicep literal |
| `COPILOT_PROVIDER_API_KEY` | AIServices account key 1 | Bicep `listKeys(aiServices.id, ...).key1` |
| `COPILOT_MODEL` | `gpt-5.4-mini` (deployment name) | Bicep parameter |

Reference: [GitHub Docs → About Copilot CLI → Using your own model provider](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli#using-your-own-model-provider).

The `-p` (programmatic) invocation mode is **login-free** when the `COPILOT_PROVIDER_*` vars are set. Only interactive `--acp` mode still gates on a GitHub identity ([copilot-cli issue #4016](https://github.com/github/copilot-cli/issues/4016)), which we do not use.

## Model choice

`gpt-5.4-mini` is a current, cost-effective default that satisfies the Copilot CLI's requirements:
- Supports tool calling (required by CLI)
- Supports streaming (required by CLI)
- ≥128k context window (recommended by CLI docs)

Swappable via the `deploymentName`, `modelName`, and `modelVersion` Bicep parameters. Other viable choices: newer `gpt-5.5` / `gpt-5.6` family variants, or an equivalent from a different family that supports tool calling + streaming. (`gpt-5.6-mini` does not currently exist in the eastus2 catalog as of 2026-07-15 — the 5.6 line ships as `sol`/`luna`/`terra` codenames only.)

**Version pinning caveat:** the repo's Foundry standards discourage hardcoding a model version. The Bicep sets `modelVersion` to a starting default; validate against the target region's catalog before deployment:

```powershell
az cognitiveservices model list --location <region> --query "[?kind=='AIServices' && model.name=='gpt-5.4-mini'].model.version" -o tsv
```

## Why custom container + EP1

- **Custom container** is required because the stock Python Functions base image ships without `git` or Node.js. The Dockerfile adds `apt-get install git nodejs` and `npm install -g @github/copilot`.
- **EP1 (Elastic Premium)** is required because Consumption Y1 and Flex Consumption do not support custom containers. See [Azure Functions hosting plans → Operating system support](https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale#operating-system-support).
- **`az acr build`** builds the image in ACR without a local Docker daemon — the demo runs on any dev box with just `az` installed.

## Hard constraints called out

- **230-second HTTP timeout** (Azure Load Balancer, all Functions plans) — the review must complete inside this ceiling. Mitigation: small hardcoded sample repo + tightly scoped prompt.
- **BYOK Azure retry bug** ([copilot-cli #3679](https://github.com/github/copilot-cli/issues/3679)) — 5 retries burn in ~0.15s on `429`. Mitigation: generous TPM (default 100k) on the deployment.
- **Scoped exception**: AIServices `disableLocalAuth: false` — needed because the CLI's BYOK mode cannot present AAD tokens.

## What is intentionally NOT included

- Retry/backoff wrapper around the subprocess call (relies on happy path per repo convention).
- CORS/browser UI (notebook button avoids the need).
- Private-repo cloning or GitHub authentication (out of scope).
- Durable Functions async pattern for reviews >230s (would be the fallback if the ceiling becomes a problem).
