# Architecture notes

- One `Microsoft.CognitiveServices/accounts` resource (`kind: AIServices`) is used as the shared AI account.
- A child Foundry project (`accounts/projects`) is deployed to keep the setup Foundry-aligned.
- The Azure Function endpoint uses function-key auth and is part of the required end-to-end flow.
- The Function service calls the Speech endpoint using AAD / managed identity.
- The direct notebook speech roundtrip remains in place to show minimal change in Speech usage on `AIServices` compared with prior Cognitive Services account patterns.
- Notebook-first flow writes all runtime values to `env/.env` from deployment outputs.
- Non-goal: production security hardening (managed identity, private networking, and key vault integration).
