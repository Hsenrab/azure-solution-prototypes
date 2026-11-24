# Tasks: BYOM Foundry Tools

**Inputs**: [spec.md](./spec.md), [plan.md](./plan.md)

## Task-generation rules

- Implement only the approved six-family notebook journey; omit Search, Vision, LLM calls, new resources, frameworks, and permanent validation scripts/tests.
- Preserve resource names, UK South, SKUs, networking/local-auth restrictions, canonical setup/destroy, and existing gateway/direct API behavior.
- Consume existing generated Foundry account settings; no new connections, infrastructure changes, or unused `AIProjectClient`. Service SDK calls are not project-proxied. Document Intelligence retrieves its account key normally and has no Entra analysis option on this multi-service route.
- Do not edit the real environment file directly, expose keys, add authentication fallbacks, or bypass policy. Live Azure operations require separate explicit approval.

## Tasks

- [X] T001 Confirm the existing account settings in `demos/byom01-capability-testing/env/.env.example` and their producer in `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb`; map these to documented SDK endpoint forms for the six examples in `demos/byom01-capability-testing/notebooks/04_foundry_tools.ipynb`. Use the existing account endpoint/name/resource ID/location/subscription/group fields. Do not read real credentials, query live Azure, register connections, change infrastructure, or add environment fields.

- [X] T002 Add only the six required service SDK packages to `demos/byom01-capability-testing/requirements.txt`: Speech, Translator text, Text Analytics, Document Intelligence, Content Safety, and Content Understanding. Resolve compatible stable versions for the existing Python/runtime dependencies; retain unrelated dependency ranges and install through the existing setup flow after the manifest change.

- [X] T004 Rename `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` to `demos/byom01-capability-testing/notebooks/05_direct_api.ipynb`, changing its title only. Update its current references in `demos/byom01-capability-testing/notebooks/02_configure.ipynb` and `demos/byom01-capability-testing/env/.env.example`; preserve direct request code and completed historical feature evidence.

- [X] T005 Create `demos/byom01-capability-testing/notebooks/04_foundry_tools.ipynb` with small headed cells: load existing generated account settings, visibly construct dedicated service clients, and run the six SDK examples below. Use the existing account endpoint/resource identity and documented endpoint forms with typed credentials; announce key-or-Entra selection where supported without printing secrets. Do not construct an unused project client or retrieve project connections. Treat the user-provided Speech example as inspiration for a short direct-account synthesis flow, not code to copy. Reuse the WAV-output idiom from **Step 3 - Synthesize text to audio** in `demos/speech01-foundry-speech/notebooks/03_test.ipynb` where suitable, verifying authentication against the selected current SDK. Reuse one small public Azure OCR sample fetched through existing `httpx`. Include one opening configuration paragraph, the service-endpoint boundary, and the Document Intelligence key-only limitation; no deployment-notebook references elsewhere, status commentary, fallback branches, or catch-and-explain wrappers.

  Required example outputs:
  - Speech: use existing generated account settings, a supported standard voice, and current SDK key/Entra authentication; prefer direct `TokenCredential` support where available rather than prescribing the sample's manual token formatting. One short sentence produces playable WAV audio; surface native cancellation details if synthesis fails. Do not hard-code the sample's account, voice, or resource-ID placeholder, or print credentials.
  - Translator: explicit non-LLM NMT translation displays translated text.
  - Language: one sentence displays its detected ISO language code; surface per-document errors.
  - Document Intelligence: `CognitiveServicesManagementClient.accounts.list_keys` retrieves the existing configured account's key, then prebuilt Read displays extracted text. Key retrieval uses Entra management access; analysis uses the key only. Surface policy/auth failures without attempting an Entra analysis fallback.
  - Content Safety: benign text displays category/severity results.
  - Content Understanding: stable asynchronous `prebuilt-read` displays extracted content, without language/embedding model configuration.

- [X] T006 Update `demos/byom01-capability-testing/README.md` and `demos/byom01-capability-testing/metadata.json` for the six examples and 04/05 ordering. Document service usage costs, project/service access requirements, and `Microsoft.CognitiveServices/accounts/listKeys/action`. State that Search remains outside this feature and Document Intelligence cannot run on the current key-disabled deployment, without proposing policy bypass or a new resource. Remove newly obsolete scope exclusions and current links; retain historical verification results accurately.

## Validation

- [X] T011 Apply the approved first-reader CSA wording review to the README and notebook markdown: remove migration/internal implementation commentary and repeated route explanations, distinguish deployment prerequisites from existing-service access, and retain configuration tables, authentication constraints, costs, cleanup, and verification links. No code or historical verification records changed. The existing notebook hygiene hook passed for 00/01/02/04/05, `git diff --check` passed, and the targeted stale-wording search returned no matches.

- [X] T010 Place the deployment-route guidance in the opening markdown of `01_deploy_infra.ipynb`, leaving shared Setup and all deployment code unchanged. Link the later Tools/Direct APIs introductions back to the established route and align README navigation. The existing notebook hygiene hook passed for 01/04/05; the built-in deployment notebook summary parsed successfully. No Azure operations were run.

- [X] T009 Apply the approved onboarding refinement to the opening of `04_foundry_tools.ipynb` and `05_direct_api.ipynb`: define **Deployed via Notebooks** and **Self deployed**, reuse verified venv/dependencies/generated settings with Entra for notebook deployments, and list all required/optional/example-specific environment variables and canonical local setup steps for independent deployments. Align the README. Simplify Tools to one selected credential plus its authentication label, with a local Entra credential for Document Intelligence management. Preserve service/request behavior and user edits; validate with editor diagnostics and the existing notebook hygiene hook, without live calls or new test scripts.

- [X] T007 Validate `demos/byom01-capability-testing/notebooks/02_configure.ipynb`, `04_foundry_tools.ipynb`, and `05_direct_api.ipynb` using built-in editor/notebook tools and the existing pre-commit hook on changed notebooks. Check SDK signatures/endpoints/authentication, use of existing generated settings, absence of LLM calls, unchanged direct/configuration code, and current notebook links. Confirm no infrastructure or project-connection changes. Preserve output/kernel-display-name cleanup. Record offline results in `specs/008-byom-foundry-tools/tasks.md`; add no Python validation scripts, test suite, or duplicate paid regression calls.

- [ ] T008 After explicit live-Azure approval, use the existing account and generated settings from `demos/byom01-capability-testing/README.md`, with no redeployment or connection registration, and manually run the applicable examples in `demos/byom01-capability-testing/notebooks/04_foundry_tools.ipynb`. Verify the six output shapes listed in T005. Record actual results in `specs/008-byom-foundry-tools/tasks.md`: verify the five dual-auth families with configured credentials; report Document Intelligence as blocked on key-disabled resources, not passed or silently skipped. Its successful analysis requires a policy-compatible key-enabled environment and permitted key retrieval, not key enablement by this task. Service calls incur usage charges; no new agent/model regression is required. Clean up exact generated local sample/audio paths when no longer needed, and report anything remaining without deleting existing services/groups.

## Dependencies and completion

### Offline evidence (2026-11-24)

- Installed Speech 1.53.1, Translator 2.0.0, Text Analytics 5.4.0, Document Intelligence 1.0.2, Content Safety 1.0.0, and Content Understanding 1.1.0 in the existing Python 3.12 demo environment. `pip check` reports no broken requirements. Speech's minimum is the inspected 1.53.1 release supporting synthesis TokenCredential callbacks.
- Inspected installed SDK signatures and response models. Translator explicitly sets `deployment_name="general"` and `allow_fallback=False`; Content Understanding uses stable `begin_analyze_binary` with `prebuilt-read`. Speech's custom-domain/TokenCredential construction matches current official guidance. No AI Projects factory, connection registration, or LLM/default-model calls were added.
- Optional `FOUNDRY_API_KEY` is scoped to the native consuming account; a same-account hostname prerequisite prevents reusing another configured Foundry endpoint's key. APIM keys are never consumed. Document Intelligence separately retrieves the existing account key using explicitly targeted Entra management access.
- The public Azure sample PDF returned HTTP 200 to a HEAD request (212,406 bytes). The notebook fetches it once into memory; no sample file or audio was generated during authoring.
- Built-in notebook summaries successfully parsed all three changed notebooks and reported no persisted executions/outputs. Editor diagnostics reported no errors for those notebooks or metadata. These checks are not live execution or a standalone full type-check.
- Existing `pre_commit run --files` notebook hygiene hook passed for all three changed notebooks. A Git comparison against the original direct notebook showed only the 04-to-05 title change (diff exit 1 denotes that expected difference); Configure's Git diff showed only its direct-notebook link change. Current demo references contain no old direct-notebook path.
- Git status confirms no Bicep, setup/destroy, helper, or configuration-producer changes. No extension hooks are registered. No new validation scripts/tests or live Azure calls/key retrieval were performed.
- T008 remains pending explicit live approval. Document Intelligence remains blocked on the existing key-disabled environment; none of the six output shapes is claimed as live-verified.
- T009 refinement checks: editor diagnostics report no errors in either notebook, both built-in notebook summaries parse successfully, the existing notebook hygiene hook passes, and `git diff --check` passes. All dual-auth Tools clients now consume the selected `credential`; Speech narrows its type for key/Entra construction, and Document Intelligence uses a local Entra management credential. No new Azure calls or permanent validation code were added; this does not claim live verification of the refactored code.

- T001 and T002 have no implementation prerequisites.
- T003 was removed when new configuration production and connection registration were excluded; retain the other task IDs.
- T004 is independent of the endpoint/dependency work and frees the 04 notebook path.
- T005 depends on T001, T002, and T004 for endpoint/dependency decisions and notebook naming.
- T006 depends on T004-T005. T007 follows the implementation/documentation tasks. T008 follows T007 and explicit live approval plus required permissions.
- T009 follows T005-T006 and includes renewed targeted offline checks; it does not authorize T008.
- T010 refines T009's navigation wording; route selection is in the deployment notebook, not Setup or the later examples.
- T011 follows T009-T010 and refines user-facing wording only.
- Offline implementation/validation and live acceptance are separate. Manual user-run evidence is sufficient; leave unrun verification pending and describe blocked outcomes explicitly. No live operations are authorized by generating this list.
