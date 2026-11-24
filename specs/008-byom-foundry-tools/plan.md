# Implementation Plan: BYOM Foundry Tools

**Date**: 2026-11-24 | **Spec**: [spec.md](./spec.md)

**Git branch**: `005-byom-capability-testing`. The setup script reported the resolved feature identifier `008-byom-foundry-tools`; it did not switch the Git branch.

## Summary

Add a small notebook demonstrating six non-LLM service families through dedicated service clients using the existing generated Foundry account settings. No infrastructure changes, new project connections, accounts, models, resource groups, or gateway route. Search is explicitly out of scope and remains unchanged.

User decisions during planning: omit deprecated Vision Image Analysis; keep Document Intelligence on the multi-service resource with normal SDK key retrieval and explicitly document that this route has no Entra option. Do not enable keys to bypass the current tenant restrictions. That example remains blocked on a key-disabled deployment.

## Existing sources and reuse decisions

Paths below are relative to the repository root; implementation stays within `demos/byom01-capability-testing/`.

| Source path | Existing behavior / constraint | Decision | Rationale / delta |
|---|---|---|---|
| `demos/byom01-capability-testing/infra/main.bicep`, `infra/gateway.bicep` | Existing account/project and gateway foundation | Reuse unchanged | No connection registration or platform changes are required. |
| `demos/byom01-capability-testing/notebooks/02_configure.ipynb` | Existing SDK configuration and generated settings | Adapt prose only | Update the direct notebook link; retain gateway settings, configuration producers, and auth flow. |
| `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb` | Python SDK deployment and generated account environment | Reuse unchanged | Consume its existing account/resource/endpoint settings; no new output contract. |
| `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` and `specs/007-byom-direct-api/plan.md` | Independent clients, visible key/Entra choice, minimal validation | Adapt / reuse decisions | Rename notebook to 05 and update its title/current references; preserve request code and historical evidence. |
| User-provided Speech SDK example; `demos/speech01-foundry-speech/notebooks/03_test.ipynb`, **Step 3 - Synthesize text to audio** | Direct account custom-domain endpoint and short SDK synthesis flow | Inspiration / adapt output idiom | Demonstrate the same direct-account capability using existing generated settings and current supported SDK authentication. Do not prescribe the sample's voice, manual token formatting, default-speaker output, or exact code. Reuse the repository's WAV-output idiom where suitable, not its authentication assumptions, REST alternative, or STT. |
| Target `requirements.txt`, `env/.env.example`, `README.md`, `metadata.json` | Existing dependency, generated configuration, and journey contracts | Adapt | Add only service packages, six-example scope, key-only limitation, and notebook-order references; no new connection-name settings. |
| Target `00_setup.ipynb`, `X_destroy.ipynb`, `app/notebook_helpers.py` | Canonical setup/destroy and CLI path helper | Reuse unchanged | Dependencies remain installed from requirements; no extra resources require new destruction logic. |
| Target `notebooks/04_foundry_tools.ipynb` | No existing tools implementation | New | One notebook; no connection module, new services, or shared runtime framework. |

## Technical decisions and constraints

### Existing configuration; no infrastructure changes

- Load existing `AZURE_AI_ENDPOINT`, `AZURE_AI_RESOURCE_ID`, `AZURE_ACCOUNT_NAME`, `AZURE_LOCATION`, `AZURE_SUBSCRIPTION_ID`, and `AZURE_RESOURCE_GROUP` from the generated environment as required by each service client. No new environment fields or connections are needed.
- Use documented service endpoint forms for the existing account; validate exact SDK endpoint requirements during implementation. Endpoint address adaptation is client configuration, not a change to deployed platform behavior.
- `AZURE_AI_PROJECT_ENDPOINT` remains the project API URL. It is not a Speech/Translator inference URL. Do not construct an unused `AIProjectClient`, call invented service factories, or claim service requests are project-proxied.
- Document Intelligence reuses the existing account identity and retrieves its account key. Translator uses the non-LLM NMT API, not the newer LLM translation modes.
- Leave Search resources, authentication, connections, and permissions unchanged.
- No new role assignments. Document Cognitive Services data-plane access on the account. Project-only access does not automatically grant service data access. Key retrieval additionally requires `Microsoft.CognitiveServices/accounts/listKeys/action`.

### SDK examples

| Heading | Client / package | Minimal operation and output |
|---|---|---|
| Speech | Speech SDK / `azure-cognitiveservices-speech` | Use existing account settings and current supported key/Entra authentication. Synthesize one short sentence with a supported standard voice and display playable WAV audio; surface native cancellation details on failure. The user sample illustrates the capability, not the required implementation. |
| Translator | `TextTranslationClient` / `azure-ai-translation-text` | NMT translation of one sentence; print translated text. Set supported NMT API/options explicitly where required by the selected SDK. |
| Language | `TextAnalyticsClient` / `azure-ai-textanalytics` | Detect the language of one sentence; print its ISO code. Surface per-document error results. |
| Document Intelligence | `DocumentIntelligenceClient` / `azure-ai-documentintelligence` | Use `CognitiveServicesManagementClient.accounts.list_keys` to retrieve the existing configured account's key, then prebuilt Read; print extracted text. Key retrieval uses Entra management credentials, but analysis is key-only on this multi-service route. |
| Content Safety | `ContentSafetyClient` / `azure-ai-contentsafety` | Analyze benign text and print returned categories/severities. No groundedness, custom training, or agent guardrails. |
| Content Understanding | `ContentUnderstandingClient` / `azure-ai-contentunderstanding` | `prebuilt-read` using the stable asynchronous analysis operation; print extracted content. Do not configure default language/embedding models. |

Keep setup/configuration and each operation in small headed cells. Use the existing kernel and Python minimum. Resolve dependencies to compatible stable releases during implementation; do not upgrade unrelated packages. No Vision package is needed.

For OCR, reuse a small documented public Azure sample input for Document Intelligence and Content Understanding where their supported formats overlap; fetch once with existing `httpx`, without adding a dataset framework. Use no customer documents.

### Authentication and configuration handoff

- Use visible service client construction with the existing account settings and `DefaultAzureCredential` where supported. No Projects SDK configuration call is required.
- Speech uses the existing account's documented custom-domain endpoint and generated resource identity where required by the selected SDK. Prefer direct `TokenCredential` support for Entra when available; do not mandate manual token construction from the sample. Verify the selected SDK's authentication contract and never print credentials.
- For service SDKs supporting both methods, use a nonempty service-appropriate configured key when present, otherwise `DefaultAzureCredential`, and announce the selected method. Do not assume an OpenAI/gateway key is valid for another service; no retry with a different authentication mode after failure.
- Document Intelligence retrieves its account key normally through the management SDK using the existing generated resource identity. It has no Entra analysis branch, manual-key-only workaround, or catch-and-explain wrapper. If policy, permissions, or disabled local authentication prevent retrieval/inference, surface the original failure and record the example as blocked.
- Preserve the existing `.env` contract and direct-client keys. Do not edit the real file, add connection-name settings, or copy retrieved keys into committed files, logs, or notebook outputs.
- The approved onboarding refinement uses prominent **Deployed via Notebooks** and **Self deployed** opening sections in Tools and Direct APIs. Define both paths, reuse a verified existing venv without extra setup for notebook deployments (Entra), and list notebook-specific required/optional/example-specific environment variables plus canonical local setup steps for independent deployments. Do not duplicate setup code or add platform toggles.
- Simplify Tools authentication to one selected `credential` plus its `auth_method` label. Speech consumes the selected typed credential; Document Intelligence constructs its Entra management credential locally. Preserve key precedence, announcements, and the key-only analysis limitation.
- The deployment-route guidance belongs at the top of `01_deploy_infra.ipynb`: continue through deployment/configuration/testing, or skip directly to Tools/Direct APIs for independently deployed resources. `00_setup.ipynb` remains the shared, unchanged local setup. Later notebook introductions refer back to this established route. This is a markdown/navigation change only; deployment code remains unchanged.
- The approved first-reader wording review removes migration/implementation commentary and repeated route explanations from the README and notebook markdown. Setup's introductory prerequisites distinguish deployment permissions from existing-service access; its code and canonical step order remain unchanged. Keep the required environment-variable tables, Entra/key limitations, costs, cleanup instructions, and links to historical verification records.
- Retain canonical setup/destroy flows, explicit subscription targeting, and the existing gateway/backend architecture. This plan does not authorize live Azure reads, deployments, inference, key retrieval, or cleanup.

### Feasibility evidence and limitations

- [Foundry resource guidance](https://learn.microsoft.com/en-us/azure/ai-services/multi-service-resource) includes Speech, Language, Translator, Content Safety, and Document Intelligence in the shared resource. [SDK overview](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview) requires dedicated Tools SDKs/endpoints.
- [Speech regions](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions), [Language regions](https://learn.microsoft.com/en-us/azure/ai-services/language-service/concepts/regional-support), [Translator regions](https://learn.microsoft.com/en-us/azure/ai-services/translator/region-support), [Content Safety regions](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/region-availability), and [Content Understanding regions](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/language-region-support) support keeping UK South for these examples. Documentation is not a tenant-level live availability test.
- [Content Understanding analyzers](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/prebuilt-analyzers) explicitly state that `prebuilt-read` requires neither language nor embedding models. Use its extraction-only path, not RAG/domain analyzers.
- [Document Intelligence SDK guidance](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-documentintelligence-readme?view=azure-python) requires a single-service resource for Entra. The user chose the existing multi-service/key-only example instead. The existing tenant's key-disabled deployment cannot provide a successful analysis run without a separately approved policy-compatible environment; no key enablement is planned.
- [Image Analysis retirement](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/overview-image-analysis) prompted the approved Vision exclusion. Do not substitute a face-recognition or LLM example.
- The user confirmed existing project/account settings and dedicated service clients instead of new connection registration. No project connection feasibility check or infrastructure deployment is needed for this feature.
- The user supplied a direct-account Speech example as inspiration, not a request to copy it exactly. [Speech Entra guidance](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-configure-azure-ad-auth) confirms the custom-domain endpoint and current `TokenCredential` support. Use the simplest supported SDK flow during implementation. The pasted example has not been run as part of authoring.

### Constitution check

Apply [the constitution](../../.specify/memory/constitution.md), [Azure Demo Authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md), and [Foundry standards](../../.github/skills/azure-demo-authoring/references/azure-ai-foundry.md).

Design passes the applicable boundaries: one hypothesis, self-contained extension, approved service-endpoint strategy, no platform changes or new resource topology, preserved authentication/network restrictions and canonical flows, existing generated environment handoff, and notebook hygiene. Bicep-first remediation is not needed because no deployed behavior changes. Document Intelligence's supported-auth limitation is an explicit user-approved scope boundary, not a policy exception. No runtime workaround remains to remove.

## Changed files and validation

All target paths below are under `demos/byom01-capability-testing/`.

| Path | Necessary change | Check |
|---|---|---|
| `notebooks/02_configure.ipynb`, `env/.env.example` | Update current direct-notebook references only | Targeted link/source inspection; configuration code remains unchanged. |
| `notebooks/04_foundry_tools.ipynb` | Six examples and authentication/coverage notes | Built-in notebook summary and editor diagnostics; source-check SDK signatures and absence of LLM calls. |
| `notebooks/04_direct_api.ipynb` -> `notebooks/05_direct_api.ipynb` | Rename and title only | Confirm request code remains unchanged and current links resolve. |
| `requirements.txt`, `README.md`, `metadata.json` | Necessary SDKs, journey, permissions, costs, and limitations | Dependency resolution after manifest edit; inspect documentation against actual coverage. |

**Offline validation:** use built-in notebook/editor tools and the existing pre-commit hook on changed notebooks, including output/kernel-display-name cleanup. Check documented SDK endpoint requirements and current references; no Bicep validation is needed for unchanged infrastructure. Do not rewrite completed historical specs or create Python validation scripts, permanent tests, or broad regression runs.

**Azure acceptance, only after explicit approval:** use the already-deployed account and existing generated settings from the [README journey](../../demos/byom01-capability-testing/README.md#notebook-journey), without redeployment or connection registration. Install new dependencies through setup's existing dependency step, then open the tools notebook and check the six outputs above. A manual user-run scenario is sufficient; do not replay paid calls merely for bookkeeping.

Record actual results per family. The five non-key-only examples should be verified with the configured authentication. Document Intelligence requires permitted key retrieval and local authentication; record it as blocked on the current deployment, not as passed or silently skipped. Confirm service clients consume the existing generated settings. No new agent/direct-model paid regression is required for unchanged request code.

Delete only generated local sample/audio files after validation when no longer needed. Do not delete existing services/accounts/groups or run full-demo destruction for this extension's test cleanup. Report any validation artifacts left behind.

## Deferred artifacts

None. This plan contains the necessary feasibility decisions; the existing README/notebook journey supplies run instructions. Generate tasks next, without extra research, contract, data-model, or quickstart files.
