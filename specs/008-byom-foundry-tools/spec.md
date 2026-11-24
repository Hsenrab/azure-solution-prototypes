# Feature Specification: BYOM Foundry Tools

**Feature directory**: `specs/008-byom-foundry-tools`

**Created**: 2026-11-24

**Status**: Draft - ready for planning

**Input**: Add a notebook before the direct API examples showing short examples of Foundry Tools, formerly Azure AI Services, without requiring an LLM. The user confirmed reuse of existing generated project/account settings and dedicated service SDKs, with no new connections or infrastructure changes.

## Problem and hypothesis

The BYOM demo demonstrates agents and model inference but does not show the standalone AI capabilities available alongside them in Foundry.

**Hypothesis**: An engineer can use the existing Foundry account configuration and run short service SDK examples for the applicable Foundry Tools without configuring or invoking an LLM or adding infrastructure.

## User journey

Open `04_foundry_tools.ipynb` after the existing setup and configuration flow. Load the existing generated account settings, then run each small, clearly headed service SDK example and inspect its result. The notebook explains once that service calls use the existing account's service endpoints, not the project API URL. Do not construct an unused `AIProjectClient` merely to imply project-routed execution.

### Observable acceptance

- [ ] Each included family below has a short SDK example producing the stated result when its authentication prerequisites are satisfied, with no agent, model Responses request, or language/embedding model deployment required. Document Intelligence is key-only on the multi-service resource; explicitly record it as blocked, not passed, on a key-disabled deployment.
- [ ] Service configuration uses the existing generated Foundry account settings and documented endpoint forms, with no new project connections or infrastructure changes. The notebook does not claim that `AIProjectClient` performs these calls or proxies them through the project.
- [ ] The existing environment handoff supplies the required account/project settings; no new configuration producer or manual repair of the real `env/.env` is needed.
- [ ] The notebook order and current demo references are consistent: Foundry Tools is 04 and direct model APIs is 05. Existing agent and direct API examples retain their behavior.

## Scope and constraints

### In scope

One example per service family, not every operation exposed by each service:

| Family | Minimal example and observable result |
|---|---|
| Speech | Synthesize a short sentence; produce playable audio. |
| Translator | Translate a short sentence; display the translated text. |
| Language | Detect the language of a short sentence; display its language code. |
| Document Intelligence | Retrieve the account key normally through the Azure SDK and use prebuilt Read on a small document; display extracted text. Document that this multi-service route has no Entra option. |
| Content Safety | Analyze benign sample text; display the returned category/severity results. |
| Content Understanding | Use `prebuilt-read`, which requires no language or embedding model; display extracted text. |

Use small, non-sensitive inputs and reuse input samples where practical. Keep service client construction and the example operation visible. Update only the required dependencies, notebook, README, metadata, and current notebook-order references.

### Out of scope

- LLM-dependent tool modes, agent orchestration, MCP/toolbox proxies, and a new application or runtime framework.
- Foundry IQ / Azure AI Search, including Search connections, configuration, dependencies, and examples.
- New project connections, infrastructure changes, and unnecessary project SDK calls.
- Custom Vision: a new custom-model training/provisioning workflow is outside this short-example journey; the service is also scheduled for retirement.
- Vision Image Analysis: omitted by user decision because it is deprecated and scheduled for retirement. Content Understanding retains the image/document OCR example.
- Immersive Reader: its embeddable browser experience is outside this server-side Python SDK notebook.
- Retired services and a separate example for every service operation.
- New permanent validation scripts, test harnesses, benchmarks, or production hardening.

### Compatibility boundaries

- Reuse the current Foundry account/project where supported. Planning must confirm service, region, SDK, and connection compatibility before implementation; unsupported coverage must be surfaced, not silently omitted or replaced by an LLM.
- Additional resources or a change of region, deployment strategy, or authentication constraints require explicit approval. Define required platform settings and connections in Bicep first; notebooks consume them.
- Keep project access through Entra authentication. For service calls, retain the existing explicit key-if-configured, otherwise Entra convention where supported. The user requested normal SDK key retrieval for Document Intelligence, not manual key entry or an Entra alternative; key retrieval and inference still require permission and enabled local authentication. Do not enable local authentication or weaken identity/network restrictions to make an example work. Announce the selected authentication method without exposing credentials, with no fallback after failure.
- Consume the existing generated configuration without changing its deployment/configuration flow or patching the real `env/.env` directly. Preserve subscription targeting and the canonical setup/destroy flows.
- Keep examples small and fail fast on missing prerequisites. Do not add catch-and-explain wrappers or defensive fallback branches.
- Preserve existing notebook hygiene checks. Built-in checks, source inspection, and manual notebook runs are sufficient evidence; distinguish offline checks from service calls actually run. Specify authorizes no live Azure operations or paid calls.

## Existing context

- [Main infrastructure](../../demos/byom01-capability-testing/infra/main.bicep) provides an AIServices Foundry account/project and Azure AI Search; the current consumer region is `uksouth`.
- [Configuration notebook](../../demos/byom01-capability-testing/notebooks/02_configure.ipynb) supplies the existing handoff; only its current direct-notebook reference needs updating.
- [Direct API notebook](../../demos/byom01-capability-testing/notebooks/04_direct_api.ipynb) is the current 04 notebook to move to 05; preserve its independent examples and authentication behavior.
- [Requirements](../../demos/byom01-capability-testing/requirements.txt), [README](../../demos/byom01-capability-testing/README.md), and [metadata](../../demos/byom01-capability-testing/metadata.json) are the existing dependency and journey contracts.
- [Speech example](../../demos/speech01-foundry-speech/notebooks/03_test.ipynb) offers reusable Entra-authenticated Speech SDK/audio patterns, but is not evidence of project-proxied execution.
- [Foundry SDK guidance](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview) distinguishes project APIs from dedicated Foundry Tools SDKs and endpoints. The approved approach uses existing account settings and service clients, not nonexistent native Speech/Translator methods on `AIProjectClient`.
- The [Foundry Tools catalog](https://learn.microsoft.com/en-us/azure/ai-services/what-are-ai-services) bounds the family inventory. [Content Understanding extraction analyzers](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/prebuilt-analyzers) explicitly support `prebuilt-read` without language or embedding models. [Custom Vision](https://learn.microsoft.com/en-us/azure/ai-services/Custom-Vision-Service/overview) is scheduled to retire on September 25, 2028; [Immersive Reader](https://learn.microsoft.com/en-us/azure/ai-services/immersive-reader/overview) is an embeddable web experience.

## Assumptions

- "Each tool" means one representative operation for each applicable service family in the catalog, rather than an exhaustive API catalog.
- Existing generated project/account settings and dedicated service SDK execution satisfy the requested integration, as explicitly confirmed by the user after clarifying the endpoint distinction.
- During planning the user omitted Vision and retained Document Intelligence with normal key retrieval and a documented lack of Entra support on the existing multi-service route. No separate Document Intelligence resource is required.
- The user explicitly excluded Search; the feature covers six service families.
