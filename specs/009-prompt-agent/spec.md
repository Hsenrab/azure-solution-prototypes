# Feature Specification: Connected Model Prompt Agent

**Feature directory**: `specs/009-prompt-agent`

**Created**: 2026-11-24

**Status**: Approved scope; ready for planning

**Input**: Create a prompt agent on the connected model, without web search, with
pirate-style system instructions and a simple Azure AI Foundry question.

## Problem and hypothesis

The BYOM demo currently verifies that a connected model can answer through the
Foundry project, but it does not provide a focused example of prompt-agent
instructions controlling the model's response style.

**Hypothesis**: An engineer can create and invoke a no-tool Foundry prompt agent
that uses the existing connected model and returns an answer to a simple Azure
AI Foundry question in a pirate voice.

## User journey

1. Complete the existing setup, deployment, and connected-model configuration
   notebooks, or use their generated settings.
2. Open the new prompt-agent notebook and load the existing project and connected
   model settings from `env/gateway.json`.
3. Create a prompt agent whose model is the registered
   `<connection-name>/<model-name>` reference, with system instructions to speak
   like a pirate and no tools.
4. Send the user query, “Explain what Azure AI Foundry is.”
5. Display the response and clean up only the test conversation and agent version.

### Observable acceptance

- [ ] The notebook creates a prompt agent using the existing connected-model
  reference and no web-search or other tools.
- [ ] The invocation returns non-empty text answering the Azure AI Foundry query
  with observable pirate-style language.
- [ ] The notebook cleanup removes only the test conversation and agent version;
  it leaves the connected model and gateway configuration intact.

## Scope and constraints

### In scope

- One new notebook in `demos/byom01-capability-testing/notebooks/`.
- Reuse of the existing project client, generated gateway settings, prompt-agent
  SDK pattern, and targeted test cleanup.
- Directly related README, metadata, and feature-artifact updates.

### Out of scope

- Web search, browsing, agent tools, RAG, or additional connections.
- New Azure resources, Bicep changes, dependencies, authentication paths, or
  deployment changes.
- Changes to the existing gateway verification notebook or live Azure validation
  unless separately authorized.

### Compatibility boundaries

- Preserve the existing connected model, APIM route, project endpoint, Entra
  authentication, generated `env/gateway.json` handoff, and public authenticated
  resource design.
- Use the verified demo venv and existing `azure-ai-projects` dependency.
- Keep the notebook small and fail fast on missing generated settings.
- Do not persist credentials or request/response bodies beyond the notebook's
  displayed response.

## Existing context

- `demos/byom01-capability-testing/notebooks/03_test.ipynb` — creates a no-tool
  `PromptAgentDefinition`, invokes the connected model through the Foundry
  project's OpenAI client, and deletes only the test conversation and agent
  version.
- `demos/byom01-capability-testing/notebooks/02_configure.ipynb` — writes the
  generated `env/gateway.json` settings used to address the connected model.
- `demos/byom01-capability-testing/notebooks/00_setup.ipynb` and
  `notebooks/01_deploy_infra.ipynb` — establish the canonical venv, Entra
  authentication, and generated environment handoff.
- `demos/byom01-capability-testing/README.md` and `metadata.json` — document the
  existing connected-model journey and must remain aligned with the added
  prompt-agent example.
- `specs/006-byom-connected-model/` — records the connected-model protocol,
  identity, cleanup, and live-validation boundaries that this example reuses.

## Assumptions

- The connected model and `env/gateway.json` already exist because configuration
  is a prerequisite; this notebook does not create or modify them.
- Pirate-style wording is demonstrated by the returned text rather than by a
  brittle exact-string assertion.
- The user has approved the local implementation scope but has not authorized a
  paid live inference run.
