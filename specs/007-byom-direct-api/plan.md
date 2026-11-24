# Implementation Plan: BYOM Direct Model API Examples

**Date**: 2026-11-24 | **Spec**: [Approved revised scope](./spec.md)

**Branch**: `005-byom-capability-testing`

## Summary

Add one notebook that reads supplied endpoint/model/authentication settings
from `env/.env` and offers five independently runnable Responses examples:
APIM/SDK, APIM/HTTPS, Foundry/OpenAI SDK, Foundry/HTTPS, and Foundry/Azure AI Projects SDK.
Each makes one pure model request for an original short poem, without agents.
An API key in the file selects key authentication; otherwise use
DefaultAzureCredential with the endpoint's configured token scope.

The prior notebooks' deployment must work after the scoped approved APIM user
allowlist update, but inference code must also accept externally supplied settings.
The user subsequently authorized implementing the feasible subset. Live changes
remain separately gated.

**Readiness:** saved user-run outputs for all five direct examples show completed
poems and response IDs with Entra, including the consuming-project Azure AI
Projects SDK call. These runs precede the custom-key header correction; the
Entra path is unchanged. Live key mode, other endpoint/model combinations, and
an additional post-policy agent replay are not established by these outputs.
The user accepted manual runs plus built-in checks and source inspection as
sufficient prototype verification; no duplicate paid run or test harness is required.

## Existing sources and reuse decisions

| Source path | Existing behavior / constraint | Decision | Rationale / delta |
|---|---|---|---|
| `demos/byom01-capability-testing/notebooks/02_configure.ipynb`, **Load Deployment Settings** | Uses `dotenv_values` to read a file | Adapt | Reuse file-reading and demo-root pattern; consume only standalone endpoint/model/auth fields, not resource IDs or `gateway.json`. |
| `demos/byom01-capability-testing/notebooks/03_test.ipynb`, **Load Gateway Settings** and **Invoke Connected Model** | AIProjectClient factory, Responses request, output text/status/ID, retries disabled | Adapt | Retain factory construction and response checks; use file settings/selected credentials and omit agent reference, conversation, gateway JSON, test markers, evidence files, and cleanup. |
| `demos/byom01-capability-testing/infra/gateway.bicep`, `infra/gateway-policy.xml` | Project-identity-only APIM connection | Adapt | Allow the explicit notebook user alongside the project; retain tenant/audience validation and backend managed identity. Trace the validated caller rather than a fixed project ID. |
| `demos/evalgw02-aoai-apim-eval/notebooks/03_test.ipynb` | APIM requests use `Ocp-Apim-Subscription-Key` | Adapt header convention only | Allow an existing key gateway's configured header; do not copy HTTP requests, resource assumptions, or evaluation flow. |
| `demos/byom01-capability-testing/requirements.txt` | AI Projects already brings the OpenAI client; dotenv and identity available | Adapt | Declare OpenAI as a direct dependency because this notebook imports it directly; retain existing SDKs and compatible version constraints. |
| `demos/byom01-capability-testing/env/.env.example` | Generated deployment settings contract | Adapt | Append optional standalone-client fields and clearly distinguish externally supplied configuration from deployment outputs. |
| `demos/byom01-capability-testing/README.md`, `metadata.json` | Existing gateway scenario and prerequisites | Adapt | Add independent poem example and caller/endpoint prerequisites without replacing the verified gateway journey. |
| `demos/byom01-capability-testing/notebooks/00_setup.ipynb`, `notebooks/X_destroy.ipynb` | Existing canonical flows | Reuse unchanged | No new setup order or cleanup flow. |
| `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb`, `notebooks/02_configure.ipynb` | Generated settings and gateway deployment | Adapt | Carry an explicit allowed-user object ID into the gateway parameter and generate direct-call settings after successful configuration; preserve existing settings. |
| `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` | Direct OpenAI SDK/HTTPS examples | Adapt | Add one AI Projects SDK factory example alongside the four existing request examples, reusing Foundry settings/authentication. |

## Technical decisions and constraints

### Endpoint feasibility

- For direct OpenAI SDK examples use `openai.OpenAI` with file-supplied settings. Supply the complete
  Responses-compatible base URL ending in `/openai/v1/`; the SDK appends
  `responses`. Do not infer the route or model from repository resources.
- The Azure AI Projects SDK example uses `AIProjectClient` with the explicit
  `AZURE_AI_PROJECT_ENDPOINT` file setting, without `/openai/v1/`. Its
  `get_openai_client(api_key=foundry_auth, ...)` factory supplies the project
  OpenAI v1 base URL. Do not pass an agent name or call project-management APIs.
  The constructor requires DefaultAzureCredential as a TokenCredential, but the
  factory's documented API-key override selects the existing string key or
  token-provider callable for inference. No token is acquired by the factory.
- The model field is the supplied deployment name or gateway alias understood by
  that endpoint, not automatically `gpt-5.4` or `<connection>/<model>`.
- [Microsoft endpoint examples](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/switching-endpoints)
  show explicit OpenAI `base_url`, API-key/Entra token-provider authentication,
  and the Responses `model`/`input` call.
- [Connected-model documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/connected-models#use-a-connected-model-in-an-agent)
  documents the connection/model reference for agents and directs custom code to
  the gateway runtime endpoint. The originally proposed agentless connected-model
  project call is now required but not established by that documentation.
- Do not substitute the backend resource for the consuming Foundry endpoint.
  Pass the exact supplied model reference, including `<connection>/<model>`,
  unchanged to `responses.create` or the HTTPS JSON body. Test the service contract
  as a hypothesis without `agent_reference`; never claim support from SDK syntax.
  A successful resource request does not verify a project endpoint. No live call
  without explicit approval.
- SDK compatibility does not prove arbitrary endpoint support or authorization.
  The approved APIM caller-policy change below resolves direct-user authorization,
  but does not itself establish agentless project-connected-model inference.

### Approved APIM user authorization

- Add one explicit `allowedUserObjectId` parameter to gateway Bicep. The
  configuration journey reads the supplied user object ID from its file settings;
  do not guess it, grant tenant-wide access, or treat DefaultAzureCredential as the
  project identity. Confirm the correct object ID before live configuration.
  An empty optional value preserves the existing project-only flow.
- Keep the tenant and Cognitive Services audience validation. Set the required
  `oid` claim to `match="any"` with the existing project principal and supplied
  user object ID. This admits either specific caller, not every tenant user.
- Add `output-token-variable-name` and use the successfully validated token's
  `oid` for `callerPrincipalId` in the existing trace. Preserve the existing agent
  test's project-identity evidence and backend managed-identity hop.
- [APIM policy documentation](https://learn.microsoft.com/en-us/azure/api-management/validate-azure-ad-token-policy)
  documents multiple required-claim values with `match="any"` and the validated
  Jwt output variable. No key branch is added to this tenant's gateway policy.
- External key gateways retain their own existing policy. Client key support does
  not enable APIM/backend keys or bypass independent JWT validation.

### File settings and authentication

Read only `dotenv_values(demo_root / "env" / ".env")`; do not merge unrelated process
environment variables into the endpoint/model/key settings. DefaultAzureCredential
may still use its normal credential-chain environment or local sign-in sources.

| Setting | Requirement |
|---|---|
| `APIM_BASE_URL`, `FOUNDRY_BASE_URL` | Complete HTTPS OpenAI v1 base URLs. Foundry is the supplied consuming resource or project endpoint, not the backend resource. |
| `APIM_MODEL_NAME`, `FOUNDRY_MODEL_NAME` | Exact callable names accepted by each endpoint; recorded Entra project runs resolve the saved connected-model reference. |
| `APIM_API_KEY`, `FOUNDRY_API_KEY` | Optional endpoint-specific keys; never print. |
| `APIM_API_KEY_HEADER`, `FOUNDRY_API_KEY_HEADER` | Optional header required by the external endpoint; for example `Ocp-Apim-Subscription-Key` or `api-key`. |
| `APIM_TOKEN_SCOPE`, `FOUNDRY_TOKEN_SCOPE` | Required in Entra mode for that endpoint; no assumed shared audience. |
| `APIM_ALLOWED_USER_OBJECT_ID` | Infrastructure/configuration input for the explicitly authorized user; not a credential and not consumed by inference code. |
| `AZURE_AI_PROJECT_ENDPOINT` | Consuming project endpoint without `/openai/v1/` for the AI Projects SDK example. Already deployment-generated; external users may supply it directly. |

- Key mode: construct OpenAI with the key. When a key-header setting is supplied,
  add that header using `default_headers` and omit Authorization with request-level
  `extra_headers={"Authorization": omit}`. The installed SDK's validator recognizes
  an explicit request omission, not an omission lost while merging client defaults.
  The endpoint must already accept this contract. An APIM subscription key alone
  does not bypass an independent JWT policy.
- Entra mode: use `get_bearer_token_provider(DefaultAzureCredential(),
  configured_scope)` as the OpenAI `api_key` callable. No key lookup, key enabling,
  project-identity impersonation, or first-subscription selection.
- Set `max_retries=0`. Select one authentication method before the request; do not
  catch a 401/403 and attempt the other method.
- Record a non-secret authentication label when selecting the credential. Print
  `Using API key` or `Using Microsoft Entra ID (DefaultAzureCredential)` before
  each SDK/HTTPS request, including before HTTPS token acquisition. Use this
  convention for new BYOM notebooks; leave earlier notebooks unchanged. It does
  not add key support to Entra-only Azure management APIs or the deployed gateway.
- Require nonempty base URL/model and Entra scope when applicable. Missing settings
  fail clearly; no success-shaped defaults, auto-discovery, or alternate endpoint.
- Successful Configure generates APIM direct-call URL/model/scope from its deployed
  outputs. It also generates `FOUNDRY_BASE_URL` from the saved consuming
  `projectEndpoint` plus `/openai/v1/`, `FOUNDRY_MODEL_NAME` from `modelReference`,
  and `FOUNDRY_TOKEN_SCOPE=https://ai.azure.com/.default`. Update only these six
  fields, preserving keys and unrelated `.env` settings. A current successful
  readback permits rerunning only the local writer, not deployment.
  These generated inputs do not establish successful model resolution.
- External users may supply equivalent file settings without running our
  deployment. No discovery or repository-name assumptions in inference code.

### Notebook flow

- **Load Endpoint Settings**: read the file and show only endpoint/model.
- **Configure Authentication**: select the shared credential and authentication
  label only. Each request example prints the method, never the key or token.
- **APIM via SDK**: import OpenAI and create its client, including any SDK custom
  key headers, immediately before the model call.
- **APIM via HTTPS**: import the HTTP client and construct the HTTP headers inside
  this example. Do not depend on SDK-client creation or shared header variables.
- **Load Foundry Settings** and **Configure Foundry Authentication**:
  read Foundry-specific file values and select credentials independently of APIM.
  Do not require APIM settings, authentication, or request cells to run first.
- Five request steps: **APIM via SDK**, **APIM via HTTPS**, **Foundry via OpenAI SDK**,
  **Foundry via HTTPS**, and **Foundry via Azure AI Projects SDK**. Each shows one request, checks
  completed status/nonempty output, and prints poem/response ID. Foundry SDK client
  creation stays in its SDK cell and HTTP header construction in its HTTPS cell.
  The new Projects SDK cell reads its explicit project endpoint, constructs the
  project client and returned OpenAI client locally, and makes one model call.
  Record verification status in the feature records, not notebook instructional
  prose. Never replace a failed connected-model request with an agent or another endpoint.
- HTTPS uses an existing HTTP client such as `httpx`, with retries disabled,
  explicit URL, headers, and JSON `model`/`input`. Use `raise_for_status()` and parse
  Responses output text items. Send an Entra bearer token or configured key/header.
  Use the same scope, endpoint, model, and prompt as the corresponding SDK example.
- No tools, streaming, `agent_reference`, conversation creation, history, saved
  evidence, or additional HTTP calls for diagnostics. Re-execution intentionally
  makes another paid request.
- No response deletion is required by this scope; do not promise that the endpoint
  retains no responses. Respect its existing storage/retention behavior.

### Dependencies and governing constraints

- Keep runtime changes inside the BYOM demo. Add a direct `openai` requirement
  compatible with the existing AI Projects dependency and supporting Responses
  and callable-token authentication; verify the installed SDK contract at
  implementation rather than pinning a speculative version.
- Declare the HTTP client directly if imported; the installed OpenAI 3.56.0 uses
  `httpx2` internally, so the HTTPS example declares its own `httpx` dependency.
  No new HTTP framework or duplicated authentication helpers.
- Infrastructure-first: change the caller allowlist and telemetry source in Bicep/
  its policy XML, never patch policy in an inference cell. Preserve all other
  tenant restrictions, canonical setup/destroy, and the existing gateway scenario.
- Follow the [constitution](../../.specify/memory/constitution.md) and
  [authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md).
  The approved external-file exception is limited to this standalone client; it
  does not replace the deployment notebook's generated-settings contract.
- Neither endpoint reuse nor planning approval authorizes live queries, inference,
  role assignment, policy changes, or resource deletion.

## Changed files and validation

| Path | Necessary change | Observable hypothesis check / existing gate |
|---|---|---|
| `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` | File-based client setup and one poem request | SC-001 through SC-005; notebook/editor syntax diagnostics and configured nbstripout hook. |
| `demos/byom01-capability-testing/env/.env.example` | Standalone field descriptions/placeholders, no real keys | Settings contract matches code and clearly states external endpoint authorization prerequisites. |
| `demos/byom01-capability-testing/requirements.txt` | Direct OpenAI dependency if absent | Existing setup dependency installation and selected-kernel imports/signatures. |
| `demos/byom01-capability-testing/README.md`, `metadata.json` | Independent scenario, configuration/auth/cost guidance | No dependency on repo deployment or misleading claim that notebook users can call project-only APIM. |
| `demos/byom01-capability-testing/infra/gateway.bicep`, `infra/gateway-policy.xml` | Explicit user caller and actual validated-caller trace | Bicep compile/policy inspection; user requests succeed while the existing project path is retained. |
| `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb`, `notebooks/02_configure.ipynb` | User-ID parameter and file handoff | Prior notebook deployment provides usable settings without assumptions in inference code. |

**Local checks:** inspect the SDK configuration paths and installed SDK behavior
with built-in tools, without acquiring credentials or sending requests. Check key-present,
key-absent with scope, and missing required settings. Confirm retries disabled and
only one inference call in the generation step. Use existing notebook/Pylance
tools and the configured pre-commit hook; no new test framework, scripts, or test files.

**Live, separately approved:** use an explicitly supplied Responses endpoint and
model that already authorize DefaultAzureCredential in the user's Entra-only
tenant. Apply the scoped user policy only with explicit live approval. Run each
approved SDK/HTTPS example once; require completed response, nonempty original
poem, and response ID. The recorded manual runs supply this evidence. Existing
project access is also retained by inspection of the caller allowlist and policy;
the user accepted that inspection with the earlier verified agent baseline rather
than requiring another paid agent replay. Any new paid call requires separate
approval. Record whether the supplied endpoint is resource- or
project-scoped; do not mark the whole feature passed based only on APIM examples.
Live key-mode proof remains unrun unless a key-capable endpoint and separate
approval are supplied; never enable backend keys just to exercise that branch.

**Evidence status:** the APIM notebook, scoped Bicep/policy authorization change,
Configure handoff, dependencies, and related documentation are implemented.
Built-in Bicep compilation and editor diagnostics passed, as did the configured
notebook hygiene hook. HTTPX installation succeeded after the built-in installer
failed. Scripted branch/settings checks were interrupted and are not counted as
passed; source-level branch and settings-preservation checks were subsequently
completed with built-in tools and accepted by the user.
No new assistant-run live operation was performed. Saved user-run notebook
outputs show successful Entra Responses calls for all five direct examples,
including the Projects SDK with the connected-model name. Configure also has
saved successful deployment, connection readback, and settings-writer outputs.
Source inspection confirms the writer updates only the six URL/model/scope
fields using `set_key`; a synthetic before/after preservation test was not run.
The existing agent evidence is a pre-change baseline, not a post-policy replay.
The retained project caller and unchanged managed-identity backend path were
checked by inspection; no new live regression is claimed.
No infrastructure, gateway policy, or direct local `.env` edit is required for
this addition. Execution evidence is recorded in the tasks; notebook outputs and
kernel display-name metadata are removed by the configured hook before commit.
See [task results](./tasks.md#results-2026-11-24) for checks and limitations.

## Deferred artifacts

None. No separate research, contract, data-model, or quickstart artifact is needed.
