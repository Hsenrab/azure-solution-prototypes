# Architecture notes

## Request path

```text
Claude Code
  -> HTTPS + ANTHROPIC_AUTH_TOKEN
  -> Azure Container Apps (LiteLLM proxy, /v1/messages)
  -> Azure AI Services endpoint + Azure API key
  -> Foundry GPT-5.4 deployment
```

LiteLLM exposes the Anthropic Messages API and translates requests to the Azure OpenAI-compatible provider. The public Container App uses a generated proxy master key, while the Foundry account key and PostgreSQL `DATABASE_URL` are stored as Container App secrets. PostgreSQL stores LiteLLM authentication state required to validate bearer keys.

## Model contract

The public alias is `azure-gpt-5.4`. It maps to the deployment name supplied to Bicep (`gpt-5.4` by default). Model name and version remain parameters because Foundry availability and version strings vary by region.

## Prototype boundary

External ingress is intentional for this feasibility demo. The API key is an access credential, not a complete production security boundary. Add Entra authentication, rate limiting, usage budgets, private networking, and secret rotation before exposing this gateway to untrusted users or valuable workloads.