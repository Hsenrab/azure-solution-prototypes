# Architecture notes

- One `Microsoft.CognitiveServices/accounts` resource (`kind: AIServices`) is used as the shared AI account.
- A child Foundry project (`accounts/projects`) is deployed to keep the setup Foundry-aligned.
- The Azure Function endpoint uses function-key auth for fast prototype validation.
- Speech SDK uses AAD / managed identity with the deployed AI Services account.
- Notebook-first flow writes all runtime values to `env/.env` from deployment outputs.
- Non-goal: production security hardening (managed identity, private networking, and key vault integration).
