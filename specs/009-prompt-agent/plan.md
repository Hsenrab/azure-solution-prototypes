# Implementation Plan: Connected Model Prompt Agent

**Date**: 2026-11-24 | **Spec**: [spec.md](./spec.md)

## Summary

Add a focused prompt-agent notebook to the existing BYOM demo. Reuse the
connected-model settings, `AIProjectClient` setup, `PromptAgentDefinition`
construction, and targeted cleanup from `03_test.ipynb`, changing only the
agent instructions and user query. The notebook will prove that the existing
connected model can follow a pirate-style system prompt without any tools.

## Existing sources and reuse decisions

| Source path | Existing behavior / constraint | Decision | Rationale / delta |
|---|---|---|---|
| `demos/byom01-capability-testing/notebooks/03_test.ipynb` | Loads `env/gateway.json`, creates a no-tool prompt agent, invokes the connected model, and deletes only test resources. | Adapt | Copy the working notebook structure into a new focused notebook. Change the title, instructions, query, and explanatory text; retain generated settings and cleanup boundaries. |
| `demos/byom01-capability-testing/notebooks/00_setup.ipynb` | Creates the verified venv/kernel and installs the existing requirements. | Reuse unchanged | The feature adds no dependencies or setup behavior. |
| `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb` | Establishes the deployment route and generated environment handoff. | Reuse unchanged | The new notebook requires completed deployment/configuration but does not deploy resources. |
| `demos/byom01-capability-testing/notebooks/02_configure.ipynb` | Writes the connected-model and project settings to `env/gateway.json`. | Reuse unchanged | Use the existing connection rather than registering another connection. |
| `demos/byom01-capability-testing/README.md` | Documents the current notebook journey and connected-model prerequisites. | Adapt | Add the new prompt-agent notebook and its purpose without duplicating setup instructions. |
| `demos/byom01-capability-testing/metadata.json` | Describes the demo scenario, services, and data. | Adapt | Mention the no-tool prompt-agent behavior and benign question. |
| `demos/byom01-capability-testing/requirements.txt` | Already contains `azure-ai-projects`. | Reuse unchanged | The SDK required by the copied pattern is already installed. |
| `specs/006-byom-connected-model/` | Defines the connected-model identity, protocol, generated settings, and cleanup boundaries. | Reuse constraints | Preserve the existing APIM route, Entra project access, and no-live-operation boundary. |

## Technical decisions and constraints

- **Demo location**: `demos/byom01-capability-testing/`; keep runtime files self-contained.
- **Infrastructure and platform behavior**: No Bicep change is needed. The feature
  consumes the already registered connected model and does not add a resource,
  route, connection, or tool.
- **Identity, authentication, and network**: Reuse the existing
  `AzureCliCredential`, Foundry project endpoint, Entra access, and APIM-backed
  connected model. No API keys or web-search credentials are introduced.
- **Deployment, subscription, and live resources**: Deployment and configuration
  remain prerequisites. Local implementation and notebook hygiene validation do
  not authorize a paid inference call or other live Azure operation.
- **Environment handoff and notebooks**: The new notebook reads generated
  `env/gateway.json`, uses the existing demo kernel and `notebooks/` working
  directory, and deletes only its own conversation and agent version. The
  canonical setup and destroy notebooks remain unchanged.
- **Dependencies and architecture**: Keep the current `azure-ai-projects`
  dependency and notebook-first architecture. Do not add a web-search tool,
  agent framework, helper abstraction, or test suite.

## Changed files and validation

| Path | Necessary change | Observable hypothesis check / existing gate |
|---|---|---|
| `demos/byom01-capability-testing/notebooks/06_prompt_agent.ipynb` | New focused prompt-agent journey adapted from `03_test.ipynb`; no tools, pirate instructions, and the Azure AI Foundry question. | Notebook parses, has no tool definitions, references the existing model, and contains targeted cleanup. A live run should return non-empty pirate-style text. |
| `demos/byom01-capability-testing/README.md` | Add notebook purpose and ordering. | Documentation matches the notebook journey. |
| `demos/byom01-capability-testing/metadata.json` | Update scenario/data description. | Metadata remains aligned with the feature scope. |
| `specs/009-prompt-agent/spec.md` | Record approved scope and acceptance evidence. | Spec/plan remain traceable to the hypothesis. |
| `specs/009-prompt-agent/tasks.md` | Track implementation and checks. | All required local tasks are marked complete when verified. |

Run setup/configuration first, then open `06_prompt_agent.ipynb`, load the
generated gateway settings, create the no-tool agent, invoke it with
“Explain what Azure AI Foundry is.”, and run the cleanup section. The expected
live result is a non-empty answer with pirate language while the connected model
and gateway remain unchanged. Local validation consists of notebook parsing,
source checks for no tools and the expected prompt/instructions, and the
existing notebook hygiene hook. Live inference remains unrun unless separately
authorized.

## Deferred artifacts

None.
