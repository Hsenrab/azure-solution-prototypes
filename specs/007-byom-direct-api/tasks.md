# Tasks: BYOM Direct Model API Examples

**Inputs**: [Specification](./spec.md), [plan](./plan.md).
The user authorized the APIM implementation and then runnable, explicitly
unverified Foundry Responses experiments using the supplied endpoint/model.
New assistant-run deployments, identity lookups, and paid requests are not authorized.
Saved user-run outputs now provide Entra Responses evidence for all five direct
examples, including the consuming-project Azure AI Projects SDK call. The user
accepted manual runs plus built-in checks and source inspection as sufficient
prototype verification, without new scripts or duplicate paid runs. Live key
mode and an additional post-policy agent replay were not performed; neither is
reported as passed. No agent/backend substitution is used for the direct examples.

## Tasks

- [x] T001 Adapt `demos/byom01-capability-testing/infra/gateway.bicep` and `infra/gateway-policy.xml` to permit an explicit Entra user alongside the project and trace the actual validated caller, retaining tenant/audience/backend identity behavior.
- [x] T002 Adapt **Load Deployment Settings**, **Deploy Gateway Configuration**, and **Write Gateway Settings** in `demos/byom01-capability-testing/notebooks/02_configure.ipynb` to consume the user object ID and preserve existing `.env` fields while generating APIM direct-call settings.
- [x] T003 Add `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` with independent APIM SDK/HTTPS poem requests, file-only settings, key-or-Entra authentication, and visible markdown-only consuming-project blockers. Reuse the existing dotenv and Responses output patterns.
- [x] T004 Update `demos/byom01-capability-testing/requirements.txt`, `env/.env.example`, `README.md`, and `metadata.json` for direct SDK/HTTP dependencies, explicit caller setup, externally supplied configuration, and partial implementation status.
- [x] T005 Validate changed Bicep and notebook syntax using built-in checks; inspect key/header/Entra branches, missing-setting guards, settings preservation, and request count/output handling in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` and `02_configure.ipynb`. Record source-level results here, not synthetic runtime passes. The user accepted this verification scope without a permanent harness; apply the configured notebook cleanup before commit.
- [x] T006 Record the user-run pure connected-model Responses proof for the consuming project OpenAI SDK/HTTPS examples in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb`. Record the exact endpoint/model tested without replaying inference; this does not verify other endpoints, key mode, or the new Azure AI Projects SDK example (SC-006).
- [x] T007 Resolve the project-path verification using recorded manual notebook runs, the earlier verified agent baseline for `demos/byom01-capability-testing/notebooks/03_test.ipynb`, and source inspection of retained project access in `infra/gateway.bicep` and `infra/gateway-policy.xml`. The user accepted inspection instead of another paid regression run for this prototype. No new post-policy agent replay is claimed; no redeployment or test resources are required.
- [x] T008 Apply the approved forward-looking authentication convention in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` and `README.md`: file key first, otherwise DefaultAzureCredential, with a non-secret method message before each SDK/HTTPS request. Align `specs/007-byom-direct-api/spec.md` and `plan.md`; validate with built-in notebook/editor tools without live calls.
- [x] T009 In `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb`, keep only credential selection shared; move SDK import/client creation into **APIM via SDK** and HTTP import/header construction into **APIM via HTTPS**. Preserve custom key headers, token-provider behavior, retries, and independent execution. Align `specs/007-byom-direct-api/spec.md` and `plan.md`; validate with built-in notebook/editor tools without inference.
- [x] T010 Replace the blocked Foundry sections in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` with unverified Responses SDK/HTTPS experiments using independent file-supplied endpoint/model/auth settings. Update `env/.env.example`, `README.md`, `metadata.json`, `specs/007-byom-direct-api/spec.md`, and `plan.md`; use built-in diagnostics without paid calls or APIM/infra changes.
- [x] T011 Complete the producer handoff in **Write Gateway Settings** in `demos/byom01-capability-testing/notebooks/02_configure.ipynb`: generate Foundry project OpenAI v1 URL, registered model reference, and Foundry scope alongside APIM settings, preserving keys/unrelated fields. Align `notebooks/04_direct_api.ipynb`, `env/.env.example`, `README.md`, `specs/007-byom-direct-api/spec.md`, and `plan.md`. Validate with built-in tools and, if its existing kernel state is available, run only the local writer and check the three non-secret fields. No Azure operations or inference.
- [x] T012 Add **Foundry via Azure AI Projects SDK** in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` using the existing project endpoint file setting, documented client factory/auth override, and one Responses request. Preserve selected authentication, retries, and user execution outputs; update `env/.env.example`, `README.md`, `metadata.json`, `specs/007-byom-direct-api/spec.md`, and `plan.md`. Validate with built-in tools; no new dependencies, direct `.env` edits, or live calls.
- [x] T013 Clean instructional prose in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb`: retain one opening deployment/configuration note, remove development-status commentary and other deployment instructions, and preserve code and saved outputs. Notebook diagnostics passed; a text scan found none of the removed status/deployment phrases. No execution or live calls.
- [x] T014 Fix custom-header API-key parity in all three SDK examples in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` by omitting the SDK's default Authorization header only in custom-header key mode. Remove the stale settings-output status without changing saved model responses. Use built-in notebook/editor checks and searches; no live calls.
- [x] T015 Correct T014's omission placement in all three SDK examples in `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` per SC-005: keep the key in client default headers and pass `extra_headers={"Authorization": omit}` on the request only in custom-header key mode. The installed SDK merges away default omissions before header validation; its validator requires the request-level omission. Verify with built-in diagnostics and installed-source inspection; no scripts or live calls.
- [x] T016 Reconcile saved user-run evidence in `specs/007-byom-direct-api/spec.md`, `plan.md`, `tasks.md`, `demos/byom01-capability-testing/README.md`, and `metadata.json`: record all five successful Entra direct calls and the successful Configure writer, distinguish the older agent baseline from the outstanding regression, and retain unexecuted local/live checks explicitly.

Dependencies: T002 depends on T001. T003 uses T002's settings contract, but accepts
externally supplied equivalents. T004 documents T001-T003. T005 covers T001-T004.
T006 uses saved user-run outputs rather than a new live call. T007 uses T005's
checks, existing evidence, and the user's accepted inspection-only scope.
T008 depends on T003 and T004, not the blocked live checks; it does not retrofit
earlier notebooks or change gateway authorization.
T009 depends on T008 and changes presentation only, not endpoint authorization.
T010 follows T009 and the approved Responses experiment revision. It adds the
request examples without claiming that T006 runtime verification has passed.
T011 depends on T002 and T010. It fixes the configuration producer, not inference
fallbacks or platform behavior.
T012 depends on T008, T010, and T011 and adds a fifth request example without
claiming its runtime verification passed.
T013 depends on T012 and changes only notebook prose.
T014 follows T013 and fixes request construction, not gateway authorization.
T015 follows T014 and completes the request-level omission needed by the SDK
validator. T016 uses saved outputs and does not authorize or perform live calls.

T014 validation: built-in notebook summary parsed all 19 cells and retained saved
request outputs; editor diagnostics reported no errors. Built-in searches found
exactly three custom-header Authorization omissions and no stale status phrases.
The attempted scripted check was interrupted and is not counted as passed.
Runtime key/Entra request parity was not re-executed; no live calls were made.

T011 initial assistant validation: built-in diagnostics reported no errors in Configure or the
direct API notebook. The built-in cell execution tool failed before Python
execution because its selected host model was unavailable, so the revised
writer's runtime execution is not claimed as passed. Direct local additions of
the three Foundry fields were subsequently removed at the user's request; only
Notebook 2 should generate this deployment's settings. Keys and unrelated local
fields were not changed. Subsequent saved user-run outputs now show a completed
writer after successful deployment/readback; see the current evidence below.
No assistant-run deployment, identity lookup, credential acquisition, or
inference was performed for this handoff correction.

T009 validation: built-in editor diagnostics reported no errors after the move,
and the built-in notebook summary confirmed the notebook remains unexecuted.
No live requests, credential acquisition, or terminal scripts were used.

## Validation

Use the existing built-in Bicep and notebook diagnostics and the configured
nbstripout gate. Focused offline checks may use synthetic settings and mocked
transports; no new test framework or persistent test suite. Preserve canonical
setup/destroy and historical feature evidence. Never enable keys in this tenant
just to exercise a client branch.

### Results (2026-11-24)

- Built-in Bicep compilation succeeded. Built-in editor diagnostics reported no
  errors in the changed Bicep, policy XML, Configure notebook, direct API notebook,
  or metadata. These checks do not prove APIM service acceptance.
- The configured nbstripout hook passed at initial implementation. The user later
  executed the direct API notebook; those outputs are preserved during this change.
- The built-in package installer failed; a targeted pip installation of the
  missing HTTPX dependency subsequently succeeded. Installed OpenAI 3.56.0 supports
  the required callable-token constructor.
- Scripted runtime/authentication and XML checks were interrupted and are not
  counted as passed. Per user direction, subsequent checks used built-in tools.
  T005 was initially left open for synthetic execution checks. The user later
  accepted built-in checks and source inspection instead; no synthetic execution
  is reported as passed.
- An empty optional user object ID retains project-only access. Direct Entra calls
  require an explicit permitted user and reapplying Configure. The authorization
  change is defined in Bicep/policy, not patched by inference code; no local
  workaround or catch-and-explain wrapper was added.
- T006 was initially blocked before executable Foundry examples were approved.
  The later T010 revision and saved user runs now provide direct Responses
  evidence. T007's post-policy agent regression has not been run by the assistant;
  saved Configure/direct-call outputs are user-run evidence, not assistant runs.
- T008: SDK and HTTPS request cells now print the selected authentication method
  before attempting the request. Built-in editor diagnostics reported no errors;
  the built-in notebook summary confirmed the notebook remains unexecuted.
  Selection behavior is unchanged; runtime branch checks remain under T005.
  No terminal scripts, live calls, or gateway changes were used for this update.
- T010: Foundry settings/authentication are independent of APIM. SDK and HTTPS
  each pass the exact supplied model name to one Responses request, with no
  agent/client-management call or fallback. Built-in editor diagnostics reported
  no errors in the notebook or metadata, and the built-in notebook summary
  confirmed all request cells remain unexecuted. The new cells have empty outputs
  and null execution counts. No terminal scripts or live operations were used.
- T006 user-run evidence: the saved settings output targets
  `https://foundry-byom01-xs7nwcodnbnn4.services.ai.azure.com/api/projects/byom01-project/openai/v1/`
  with model `byom01-gateway/gpt-5.4`. Both OpenAI SDK and HTTPS outputs show
  DefaultAzureCredential/Entra authentication, nonempty poem text, and response IDs
  after their completed-status assertions. SDK response:
  `resp_05ce0cc14807d674006b0561d570f48197a389d5f4ccd71556`; HTTPS response:
  `resp_0262718a881778a7006b0561dc47908197952c0c613713cab5`.
  This is saved user-run evidence, not an assistant-run replay or a new correlated
  gateway telemetry check. It does not validate resource-endpoint or key mode.
- T012 introduction validation: official AIProjectClient documentation and the installed SDK
  source confirm the required TokenCredential, local OpenAI factory, and explicit
  `api_key` override. Built-in diagnostics reported no notebook or metadata errors.
  At introduction, the notebook summary showed no execution output for the new example, while
  previous user outputs remain present. No new dependency, terminal script,
  environment-file edit, credential acquisition, or paid call was performed.

### Accepted evidence and limitations (2026-11-24)

- Before commit cleanup, all five direct request examples had saved nonempty poems, Entra authentication
  messages, and response IDs after their completed-status assertions. The APIM
  SDK/HTTPS IDs are `resp_06fa9594cad1b7c3006b055f69b5d48195875cc5fd56517359`
  and `resp_0061d9f265b3e28a006b055f75a9188193b7465dd5f782e38d`.
  Foundry OpenAI SDK/HTTPS IDs are recorded above. The Projects SDK ID is
  `resp_09f9146b5b3fb4ad006b0564d374bc8193baecdebbf227397f`, using the same
  consuming project and `byom01-gateway/gpt-5.4` model reference.
  These saved runs precede the custom-key correction; the Entra path is unchanged.
- Configure's saved **Write Gateway Settings** output confirms the user ran the
  writer after successful deployment/readback. Source inspection confirms only
  six URL/model/scope fields are passed to `set_key`. The installed dotenv
  implementation copies other keys/comments unchanged. This is source-level
  preservation evidence, not a synthetic before/after execution test.
- Built-in gateway Bicep compilation succeeded again. Editor diagnostics reported
  no errors in gateway Bicep/policy, Configure, the direct notebook, or metadata.
  The notebook summary parses all 19 cells and retains all saved request outputs.
  A built-in search confirms exactly three request-level Authorization omissions.
- T015 source inspection follows OpenAI's header merge and validation: request
  omissions remove the generated bearer header while remaining visible to the
  validator. Custom keys remain in their configured header. Without a custom
  header, key mode retains bearer-key authentication; without a key, the existing
  callable Entra provider is unchanged. Missing endpoint/model or missing scope
  without a key still raises before inference. No fallback or error wrapper was added.
- T005 is closed using completed source inspection and built-in diagnostics,
  together with the recorded manual runs, as accepted by the user. No synthetic
  request or settings-preservation script was run; runtime checks are not reported
  as passed. The configured notebook cleanup removes outputs and kernel display
  names before commit; the observed request results remain recorded here.
- The ignored existing agent evidence is a verified baseline from
  `2026-11-23T23:26:15.565478+00:00`, with a successful gateway record and both
  test cleanup flags true. It predates the policy update and is not a new
  regression pass. T007 is closed by the user's accepted verification scope:
  the original project identity remains in the explicit allowlist, tenant/audience
  validation remains active, and backend authentication remains managed identity.
  No new live request, redeployment, environment-file edit, or resource deletion
  was performed during this implementation pass.
- Commit preparation: the existing demo environment's `pre_commit` module ran
  the configured nbstripout hook on Configure and the direct API notebook.
  The first pass removed outputs and kernel display-name metadata; the second
  pass passed. Observed user-run response IDs remain recorded above.
