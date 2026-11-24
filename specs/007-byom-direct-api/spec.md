# Feature Specification: BYOM Direct Model API Examples

**Feature directory**: `specs/007-byom-direct-api`

**Created**: 2026-11-23

**Status**: Complete for the agreed prototype scope: manual Entra runs and built-in/source checks accepted; live API-key mode not tested

**Input**: Add a notebook with one SDK API call to write a poem. Approved follow-up:
read endpoint, model/deployment, and authentication from an externally supplied
`.env` file; do not assume repository-provisioned resources. Use a configured API
key when present, otherwise DefaultAzureCredential. The user's tenant uses Entra
only; other users may supply an existing key-authenticated gateway.
Further approved scope: independently show APIM and the consuming Foundry project
endpoint, through SDK or HTTPS. Each example makes one pure model request with no
agent. The example must work with the prior notebooks' deployment while also
accepting equivalent externally supplied settings. Allow the explicitly selected
notebook user's Entra identity at APIM alongside the existing project identity.
An earlier approved revision added runnable but explicitly unverified Foundry Responses
SDK/HTTPS examples using the exact supplied consuming resource or project base URL
and model reference. No agent/backend substitution, APIM changes, or live calls are
authorized by this local implementation revision.
Approved handoff correction: Configure also generates the Foundry base URL from
the consuming project endpoint, the registered connected-model name, and the
Foundry token scope, preserving keys and unrelated settings. External callers may
still supply equivalent file values. This does not verify model resolution.
Approved SDK addition: use `AIProjectClient.get_openai_client()` with the existing
`AZURE_AI_PROJECT_ENDPOINT` file setting for a fifth pure Responses example.
Reuse selected Foundry credentials through the documented `api_key` override,
without agent or project-management calls. The user-run OpenAI SDK and HTTPS
project examples provide successful Entra Responses evidence. Subsequent saved
outputs also show successful APIM SDK/HTTPS and Foundry Azure AI Projects SDK
requests. These user runs establish the recorded Entra configuration only;
live key authentication and an additional post-policy agent replay were not run.
The user accepted manual notebook runs plus built-in checks and source inspection
for this prototype, without a permanent test harness or duplicate paid requests.

## Problem and hypothesis

The existing connected-model test creates an agent and conversation, then performs
inference, cleanup, and gateway verification. An engineer needs a smaller example
that shows the inference call itself without that lifecycle.

**Hypothesis**: A pure Responses model request through either APIM or the consuming
Foundry endpoint, using SDK or HTTPS and file-supplied settings, can return an
original short poem without creating or invoking an agent. The prior deployment
must support the examples; equivalent externally deployed resources are also valid.

## User journey

1. Prepare the demo Python environment and supply an existing Responses-compatible
   endpoint, model/deployment, and authentication settings in `env/.env`.
   Previous notebooks can provide the configuration; externally supplied resources
   are also valid. Direct APIM access requires the approved caller-policy update.
2. Open `demos/byom01-capability-testing/notebooks/04_direct_api.ipynb` using the
   demo kernel and notebook working directory.
3. Read settings from the file and select authentication. Use a
   nonempty configured API key when present; otherwise use DefaultAzureCredential
   and the configured token scope. Never switch methods after a failed request.
4. Choose one SDK/HTTPS example for APIM or the supplied consuming Foundry endpoint.
   Run only that endpoint's settings/authentication and chosen request cells. Run
   that generation cell once, asking for an original short poem on a harmless topic.
   Create the SDK client inside its example; construct HTTP headers inside the
   HTTPS example, with neither example depending on running the other.
5. Display the poem and response ID. No agent/conversation cleanup is required
   because the example does not explicitly create either resource.

### Observable acceptance

- **SC-001**: The notebook targets exactly the endpoint and callable
  model/deployment supplied in `env/.env`, with no dependency on `gateway.json`,
  repository naming conventions, or resource provisioning.
- **SC-002**: Each execution of a chosen generation cell issues exactly one
  inference request, with explicit model/input and automatic retries disabled.
  Client setup/authentication is not an inference request. Examples do not invoke
  each other or switch endpoints after failure.
- **SC-003**: The response is completed, contains nonempty text that is an original
  short poem, and displays its response ID. The engineer reviews the poem; no
  evaluator, exact wording, or rigid formatting test is required.
- **SC-004**: The notebook makes no agent-management, explicit conversation-create,
  tool, or infrastructure calls. Service errors propagate rather than triggering
  an alternative model, route, protocol, or agent flow.
- **SC-005**: A nonempty API key selects key authentication. Without a key,
  DefaultAzureCredential and the endpoint's token scope select Entra authentication.
  Before each SDK/HTTPS request, print `Using API key` or
  `Using Microsoft Entra ID (DefaultAzureCredential)` to identify the attempted
  method. Credentials are not printed or saved in notebook output. Both branches are
  checked locally by source inspection and built-in tools; no synthetic runtime
  harness is required. Live validation uses Entra in the user's tenant, without
  enabling keys solely to test the other branch.
- **SC-006**: APIM/SDK, APIM/HTTPS, Foundry/OpenAI SDK, Foundry/HTTPS, and
  Foundry/Azure AI Projects SDK
  are independently runnable pure model examples. A backend-resource call or an
  agent-reference call does not substitute for the Foundry examples. Record the
  exact consuming resource or project endpoint tested; success at a resource
  endpoint does not establish project-endpoint support. Each example remains
  unverified until its supplied endpoint/model/authentication combination succeeds.
  The Projects SDK uses `AZURE_AI_PROJECT_ENDPOINT`, not a derived resource URL;
  its returned OpenAI client must reuse the selected key or Entra token provider.
- **SC-007**: Successful prior deployment/configuration produces file settings
  usable by this notebook: APIM settings and Foundry project OpenAI v1 base URL,
  connected-model reference, and `https://ai.azure.com/.default` scope. The writer
  preserves keys and unrelated fields. Externally supplied equivalent settings also work;
  inference code does not assume resource naming or provisioning origin.
- **SC-008**: APIM accepts the existing project identity and one explicitly
  authorized notebook user's object ID, still validating tenant/audience and using
  APIM managed identity for the backend. The policy does not authorize all users
  or enable backend keys. Routing traces identify the actual validated caller.

## Scope and constraints

### In scope

- One notebook with file/settings setup and five independently runnable
  SDK/HTTPS examples, each making one model call with a harmless poem prompt.
- The scoped Bicep caller-policy update and necessary settings handoff from
  successful prior configuration, retaining existing agent-based tests.
- Minimal README/metadata updates describing the example and paid invocation.
- File-based endpoint/model/auth settings, including the API-key header needed by
  an existing gateway when different from the SDK's standard bearer-key header.
- Apply this authentication selection and messaging convention to new BYOM
  notebooks from this direct-API notebook onward. Do not retrofit earlier notebooks.
  API keys apply only where the target API supports them; Azure deployment, RBAC,
  and resource cleanup still require Entra. Do not enable gateway keys to satisfy
  the client convention.
- Existing local notebook syntax/hygiene checks and separately approved live
  validation of the one-call scenario.

### Out of scope

- Agent orchestration, conversation management, tools, streaming, evaluation,
  retrieval, Foundry IQ, or additional gateway diagnostics.
- New infrastructure, model deployments, dependencies unless proven necessary,
  authentication-policy changes beyond the approved APIM caller addition, retries,
  fallback routes, or performance
  tests.
- New telemetry workflows or claiming a direct backend call proves the
  consuming-project connected-model path.
- Replacing the existing connected-model test/evidence notebook.

### Compatibility boundaries

- Leave existing repository-deployed infrastructure, managed-identity gateway
  connection, existing permitted project caller, backend key restrictions, regions,
  and GPT-5.4 capacity unchanged. Add only the approved explicit APIM user caller.
- Approved exception to the generated-settings convention for this standalone
  client: consume externally supplied `env/.env` endpoint/model/auth values.
  Do not require subscription/resource discovery or generate settings from an
  assumed deployment. The existing deployment notebook still generates its own
  settings as before. Real `.env` files and keys remain excluded from Git.
- Preserve existing setup/deployment/configure/test/destroy flows. Keep the example
  self-contained under the BYOM demo and strip notebook outputs before committing.
- Scope approval authorizes this specification only. Implementation and any paid
  live inference require explicit approval. Do not modify or delete existing Azure
  resources during discovery or feasibility planning.
- The supplied endpoint must already accept the chosen caller/authentication and
  support direct Responses inference. DefaultAzureCredential does not impersonate
  the consuming project's identity. The existing project-only APIM route cannot
  accept an ordinary notebook-user token without a separately approved policy
  change;   this feature plans the explicitly approved user addition in Bicep. Default
  credentials may select a different identity; the selected token must belong
  to the authorized caller.
- The user-run consuming-project OpenAI SDK, HTTPS, and Azure AI Projects SDK examples demonstrate
  agentless connected-model Responses with Entra for the recorded configuration.
  Other endpoint/model/authentication configurations still require verification using the
  exact file-supplied base URL and model name, including `<connection>/<model>`.
  Do not declare these examples supported or silently replace them with an agent,
  backend-resource endpoint, or gateway call. Surface native service errors.
  Infrastructure, connection scope, gateway routes, and authentication policies
  remain unchanged by this experiment. Live testing requires separate approval.

## Existing context

Bounded discovery follows
[the authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md).

- `demos/byom01-capability-testing/notebooks/03_test.ipynb` — existing
  Responses SDK request/output pattern and AIProjectClient construction. Reuse
  only the client factory and request/output patterns for the new Projects SDK
  example, not its agent lifecycle, gateway JSON dependency, or evidence workflow.
- `demos/byom01-capability-testing/infra/gateway.bicep` and
  `infra/gateway-policy.xml` — existing project-scoped Responses connection and
  project-identity-only gateway route; adapt only the caller allowlist and actual
  caller telemetry for the approved direct-user path.
- `demos/byom01-capability-testing/requirements.txt` — existing AI Projects SDK
  dependencies; no additional dependency is currently justified.
- `specs/006-byom-connected-model/` — existing verified agent-based gateway journey,
  not proof of direct model selection without an agent.
- [OpenAI/Azure OpenAI endpoint guidance](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/switching-endpoints)
  demonstrates an OpenAI client with explicit base URL, API key or Entra bearer
  provider, and `responses.create(model=..., input=...)`.
- [Connected-model guidance](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/connected-models)
  documents connected-model references for Agent Service and directs custom
  application code to the gateway runtime endpoint. This drove the approved scope
  research. It does not establish support for the now-required agentless
  consuming-project path.
- [Foundry endpoint shapes](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/model-router-apis#choose-an-endpoint)
  document resource/project OpenAI v1 URLs and Foundry token scope. These examples
  cover model router, not proof that this connected-model reference resolves.
  The user's portal Chat Completions sample motivates a Responses experiment,
  rather than establishing successful runtime support.
- [AIProjectClient reference](https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient?view=azure-python)
  documents the required TokenCredential, project endpoint, and `get_openai_client`
  API-key override. The installed SDK source also confirms the override is used
  without requesting a token; the factory itself makes no service calls.

## Assumptions

- The supplied endpoint must authorize the selected credential and support the
  requested Responses model resolution for a request to succeed. Saved Entra
  project calls verify the recorded connected-model configuration, not arbitrary
  external endpoints or authentication methods.
  Do not assume model names or auth audience from the repository's deployment.
- A new execution intentionally makes another paid request; the notebook will not
  invoke automatically or repeat a failed request.
