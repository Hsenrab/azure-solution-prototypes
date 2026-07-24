# copilotcli01: GitHub Copilot CLI code review powered by a Foundry model

## Problem statement

Teams want to run the GitHub Copilot CLI headlessly against their own Azure AI Foundry model deployment (bring-your-own-key), invoked from a service endpoint, so they can trigger repository reviews from an internal button/UI without giving each user a GitHub Copilot subscription.

## Hypothesis

If we host the `@github/copilot` CLI inside a custom-container Azure Function, wire it to a Foundry `gpt-5.4-mini` deployment via the `COPILOT_PROVIDER_*` environment variables, and expose it behind a function key, then a single button click in a notebook can produce a Copilot-generated code review of a public Git repository — with no GitHub identity required at runtime (the CLI's `-p` programmatic mode is login-free when BYOK env vars are set).

## Scope

- In scope:
	- One Azure AI Services account (`kind: AIServices`) with a `gpt-5.4-mini` deployment.
	- **Validate the model + version against the target region before deploying** (`az cognitiveservices model list -l <region>`). The Bicep default is a starting point; regions vary in availability and version strings.
	- One Azure Container Registry (Basic).
	- One Elastic Premium (EP1) Linux plan hosting a **custom-container Python Function App** built from `mcr.microsoft.com/azure-functions/python:4-python3.12` + `git` + Node 20 + `@github/copilot`.
	- A single HTTP function (`POST /api/review`) that shallow-clones a hardcoded public sample repo into `/tmp` and runs `copilot -p "..."` in BYOK mode.
	- An `ipywidgets.Button` in `03_test.ipynb` that fires the function and renders the returned markdown inline.
- Out of scope:
	- Private repositories, GitHub authentication, or Copilot subscription entitlements.
	- Streaming responses, review persistence, or PR comment posting.
	- Production networking, private endpoints, or vNet integration.
	- Retry/backoff hardening (relies on generous TPM to avoid `429` — see "Known limitations").

## Scoped exception to the repo's MI-only convention

The GitHub Copilot CLI's BYOK mode sends a static API key header to the model provider — it cannot present an AAD bearer token. This demo therefore deploys the AIServices account with `disableLocalAuth: false` and hands the CLI an account key via the `COPILOT_PROVIDER_API_KEY` app setting.

Everything else in the demo still uses managed identity: the Function App pulls its container image from ACR via MI (`acrUseManagedIdentityCreds: true`) and reads/writes its Function storage via MI (`AzureWebJobsStorage__credential: managedidentity`). Only the Foundry AIServices data plane relaxes to API-key auth.

## Notebook journey

Run notebooks in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Create isolated venv, register kernel, `az login`, install Python packages |
| `01_deploy_infra.ipynb` | Deploy Bicep (AIServices + `gpt-5.4-mini` + ACR + EP1 plan + custom-container Function App) and write bootstrap values to `env/.env` |
| `02_configure.ipynb` | Build the container image in ACR (`az acr build`), point the Function App at the new image, restart, and fetch the function key |
| `03_test.ipynb` | Click a button to trigger a Copilot review of the sample repo and render the returned markdown |
| `X_destroy.ipynb` | Delete all resources and purge the soft-deleted AI Services account |

## Folder map

```text
infra/       # Bicep for AIServices + model deployment + ACR + EP1 plan + custom-container Function App
functionapp/ # Python Function code, host.json, requirements.txt, Dockerfile (with git + node + @github/copilot)
notebooks/   # numbered notebook flow
env/         # .env auto-written by notebook 01
app/         # notebook helpers (Azure CLI resolver)
docs/        # architecture notes + BYOK env-var mapping
outputs/     # captured review markdown from notebook 03
```

## Quick start

1. Run `notebooks/00_setup.ipynb`.
2. Run `notebooks/01_deploy_infra.ipynb` — deploys infra (~6-10 minutes).
3. Run `notebooks/02_configure.ipynb` — builds the container in ACR and swaps the Function App to it (~5-8 minutes for the first image build).
4. Run `notebooks/03_test.ipynb` — click **Run Copilot Review** and wait for the markdown to render (~30-90 seconds for the sample repo).
5. Run `notebooks/X_destroy.ipynb` when done.

## Known limitations

- **230-second HTTP timeout.** Azure Load Balancer imposes a hard 230s ceiling on all Azure Functions HTTP responses (all plans). This demo defaults to a small hardcoded sample repo (`Hsenrab/CodeReviewExample`) and a tightly scoped prompt to stay under this ceiling. If reviews start timing out, tighten the prompt in `functionapp/function_app.py` (`REVIEW_PROMPT`) or switch to a smaller repo.
- **BYOK Azure retry behavior is fragile** ([copilot-cli #3679](https://github.com/github/copilot-cli/issues/3679)) — the CLI burns 5 retries in ~0.15s on `429`. We provision the deployment with generous TPM to avoid tripping this. If the review returns "Failed to get response from the AI model", re-run: it's almost always a transient throttle.
- **Foundry endpoint URL shape.** The CLI accepts the AIServices endpoint of the form `https://<account>.openai.azure.com`. If the deployment endpoint changes shape in future Foundry versions ([copilot-cli #3208](https://github.com/github/copilot-cli/issues/3208) tracks related api-version quirks), `COPILOT_PROVIDER_BASE_URL` may need to be adjusted in the Bicep.
- **Cold-start image pull** (~15-30s) on EP1 after long idle.
- Prototype only — no auth on the function beyond the function key; no persistence of reviews.

## Why Foundry-aligned here

- Uses new `kind: AIServices` + `GlobalStandard` model deployment pattern (not the classic Azure OpenAI + hub setup).
- The `COPILOT_PROVIDER_TYPE=azure` path of the Copilot CLI targets Azure OpenAI-compatible endpoints, which Foundry AIServices exposes natively at the account subdomain.
