# Implementation Plan: BYOM Connected Model Through APIM

**Spec**: [Approved scope](./spec.md)

**Branch**: `005-byom-capability-testing`

**Status**: Local implementation authorized, including the field-specific compiler
accommodation. Live validation remains outstanding.

## Summary

Extend the existing BYOM demo with two small notebooks: configure the managed-identity
gateway and project connection, then invoke a minimal Foundry prompt agent and
correlate its request with successful APIM backend evidence. Reuse the existing
consumer, APIM Standard instance, and Sweden Central GPT-5.4 deployment.

The user subsequently authorized local implementation and the field-specific BCP036
accommodation. Live resource changes and paid inference are not authorized.
The managed-identity connection payload and Responses selector are verified from
retrievable source. This is not evidence of deployment or inference success in the
user's project; do not substitute API keys.

## Existing sources and reuse decisions

Paths below are relative to the repository root.

| Source path | Existing behavior / constraint | Decision | Rationale / delta |
|---|---|---|---|
| `demos/byom01-capability-testing/infra/main.bicep` | Consumer/project identities; APIM Standard without identity | Adapt | Enable APIM system-assigned identity in its authoritative resource definition; preserve names, region, networking, publisher settings, and SKU. |
| `demos/byom01-capability-testing/infra/backend.bicep` | Sweden Central GPT-5.4, capacity 100, keys disabled | Adapt | Approved follow-up adds a deterministic backend project using the consumer project's existing resource pattern, plus project name/ID outputs for portal navigation. Preserve account/model settings and gateway routing. |
| `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb` | Bicep compilation, SDK deployment, generated base settings | Reuse flow | Use its **Compile Bicep** and **Deploy Bicep** cells to apply the consumer identity change before configuration. Do not duplicate or partially redefine APIM in another template. |
| `demos/byom01-capability-testing/notebooks/00_setup.ipynb`, `notebooks/X_destroy.ipynb`, `app/notebook_helpers.py` | Canonical setup/destroy and CLI executable resolver | Reuse unchanged | Preserve setup order and cleanup implementation; no new authentication helper or fallback. |
| `demos/evalgw02-aoai-apim-eval/infra/main.bicep` | APIM API, operation, backend, and policy structure | Adapt structure only | Reject its API-key authentication, classic hosting, preview child API versions, and evaluation scenario. |
| `demos/byom01-capability-testing/README.md`, `metadata.json`, `requirements.txt` | Foundation-only instructions and management SDKs | Adapt | Explain configure/test, dependencies, telemetry permissions, rerun prerequisites, and cleanup. |
| `specs/005-byom-capability-testing/` | Earlier backend decisions and capacity-10 validation | Reuse evidence unchanged | Historical deployment success is not gateway or capacity-100 inference evidence. |

## Explicit test cleanup follow-up

- Reuse the existing **Clean Up Test Resources** cell as the only test deletion
  step. Remove invocation's automatic cleanup without changing its paid request,
  response assertions, or persisted identifiers. Keep the prior-test cleanup guard.
- Run cleanup explicitly after inspection, including on invocation failure.
  Preserve cleanup retry flags and error propagation. Validate notebook structure
  and Python syntax locally without invoking or deleting live resources.

## Technical decisions and constraints

### Infrastructure and authentication

- Approved backend-navigation follow-up: add one system-assigned-identity project
  under the existing backend account, using the same API version and structure as
  the consumer project. No additional roles, connections, model deployments, or
  notebook deployment flow changes. Compile the backend template locally; live
  project selection and model visibility remain unverified until applied.
- Keep runtime changes inside `demos/byom01-capability-testing/`.
- Enable APIM identity in `infra/main.bicep`. Existing deployments require applying
  that Bicep change; notebooks must not patch identity through a management API.
- Add consumer-scoped `infra/gateway.bicep` for one API/operation, fixed backend,
  caller-validation policy, telemetry, and the verified connection configuration.
  Reference the existing APIM and consuming project. Load `infra/gateway-policy.xml`
  with explicit Bicep substitutions; multiline Bicep strings do not interpolate.
- Add `infra/backend-access.bicep`, called as a module scoped to the generated
  backend resource group, for APIM's inference role assignment on the backend account.
  Use deterministic assignment names; do not grant subscription-wide access.
- Validate Entra tokens at APIM against the selected tenant, the verified connection
  audience, and the consuming project's principal `oid`. Required-claim validation
  avoids an unnecessary Microsoft Graph client-ID lookup.
- After caller validation, use `authentication-managed-identity` with resource
  `https://cognitiveservices.azure.com` to authenticate APIM to the fixed backend.
  Keep failure propagation enabled and APIM subscription-key requirements disabled
  for this Entra-protected API. Do not expose an anonymous inference route.
- Preserve UK South consumer resources, Sweden Central backend resources, public
  authenticated endpoints, disabled backend keys, and capacity 100. GlobalStandard
  does not guarantee Sweden-only processing.

### Verified connection and protocol contract

The selected single protocol is OpenAI v1 Responses: connection target
`https://<existing-apim-host>/<demo-api-path>/openai/v1`, operation `/responses`,
and backend `<generated-backend-openai-endpoint>/openai/v1/responses`.
Do not add deployment paths, `api-version` query parameters, or a second protocol.
The model reference must be `<connection-name>/<backend-deployment-name>`.

The project connection properties are:

```bicep
properties: {
  category: 'ApiManagement'
  target: gatewayOpenAIV1BaseUrl
  authType: 'ProjectManagedIdentity'
  audience: 'https://cognitiveservices.azure.com'
  isSharedToAll: false
  credentials: {}
  metadata: {
    deploymentInPath: 'false'
    upstreamSurface: 'responses'
    customHeaders: '{}'
    models: string([
      {
        name: backendDeploymentName
        properties: {
          model: {
            name: 'gpt-5.4'
            version: backendModelVersion
            format: 'OpenAI'
          }
        }
      }
    ])
  }
}
```

This is a property-contract illustration, not a standalone compilable template.
Use generated deployment/version values; omit inference/deployment API-version
metadata, discovery, and API-key `authConfig`. APIM must validate the same audience.
The model entry's `name` is the callable backend deployment name, not a new deployment.

Verification sources:

- The [Foundry gateway guide](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/ai-gateway)
  confirms APIM Standard/classic support, project managed identity, the audience,
  Responses routing, and `<connection-name>/<model-name>` invocation.
- The reachable [Foundry APIM connection module](https://github.com/microsoft-foundry/foundry-samples-pr/blob/142e5d0bc17b465d02bb2aa5485cc5808f3d31a5/infrastructure/infrastructure-setup-bicep/01-connections/apim/modules/apim-connection-common.bicep)
  explicitly creates a project-scoped `ApiManagement` connection with
  `authType: 'ProjectManagedIdentity'`, top-level `audience`, empty credentials,
  and metadata. The published guide's `foundry-samples` link returned 404, but
  the separately named `foundry-samples-pr` repository is retrievable.
- The [Azure gateway Foundry template](https://github.com/Azure/aigateway/blob/feac191bd69d7a2fa4fdba5c233f3a1d1c40fc65/labs/32-foundry-gateway-connection/infra/foundry-project.bicep)
  uses the same connection category/authentication and verifies
  `metadata.upstreamSurface: 'responses'` with serialized static models.
  Do not copy its standalone-gateway resource, alias URL, audience, or RBAC.
- The [Foundry Responses sample documentation](https://github.com/microsoft-foundry/foundry-samples-pr/blob/142e5d0bc17b465d02bb2aa5485cc5808f3d31a5/infrastructure/infrastructure-setup-bicep/01-connections/model-gateway/README.md)
  independently identifies `upstreamSurface: responses` and versionless v1 routing.
  It warns that the upstream Responses feature flight must be available; deployment
  does not enable it. Label this requirement `[PREVIEW]` in notebook guidance and
  verify availability in the consuming project before paid validation.
- The [Cognitive Services TypeSpec source](https://github.com/Azure/azure-rest-api-specs/blob/dc8116b1ae0b69b066a8f149962b2d88d3902bf6/specification/cognitiveservices/resource-manager/Microsoft.CognitiveServices/CognitiveServices/models.tsp)
  explicitly defines the `ProjectManagedIdentity` authentication enum member.

**Compiler accommodation, not an unsupported-auth workaround:** the published
stable connection reference and bundled Bicep types omit this real auth value.
The Azure template documents a narrowly scoped `BCP036` suppression at that field;
the Azure-Samples APIM module independently documents the same type lag.
The user approved that specific stale-type accommodation before implementation.
Do not use broad `any()` casts,
suppress unrelated diagnostics, change to `AAD`/`ManagedIdentity`, or move the
connection into Python. Keep the intended connection API `2026-09-01`; its deployment
and saved-property readback remain live checks, not results established by source review.

Responses feature availability, actual project-token caller validation, and
prompt-marker preservation remain acceptance checks. No fallback protocol is planned.

### Test and correlation

- Use `azure-ai-projects>=2.0.0`, `AIProjectClient`, and a no-tool
  `PromptAgentDefinition` referencing the connected model. Follow the documented
  explicit agent-version invocation path, verifying the selected SDK signature
  before authoring; do not modify an existing agent endpoint.
- Create a uniquely named test agent/version and conversation; send one short,
  harmless prompt through Foundry, not directly to APIM or the backend.
- Proposed correlation: put a generated `byom01-test:<uuid>` marker in the test
  prompt. The APIM policy reads the request with content preserved and extracts
  only that allowlisted marker. Its successful-forwarding trace records the marker,
  APIM request ID, API/backend identity, deployment, caller principal, and status.
  Do not record request/response bodies or authorization headers.
- This avoids assuming notebook headers propagate through Foundry or that Foundry's
  response ID equals the backend response ID. Confirm marker preservation in the
  actual forwarded request during authorized validation; absence blocks SC-004.
- Use one demo-owned workspace-based Application Insights instance in the consumer
  group, an APIM managed-identity logger, and diagnostics scoped to this API.
  Grant APIM Monitoring Metrics Publisher on that component. Configure diagnostic
  body bytes to zero and trace verbosity to include the evidence trace.
- Add `azure-monitor-query` for querying workspace `AppTraces` through
  `LogsQueryClient`. The notebook user needs appropriate log-query access; do not
  silently assign broader user permissions.
- Save compact ignored evidence under the demo's `env/` directory: test marker,
  UTC invocation time, project/model/agent/version/conversation identifiers,
  Foundry response ID and short test output, correlated gateway records, verification
  state, and cleanup state. Never save tokens or arbitrary prompts.
- Keep **Invoke Connected Model** separate from **Check Gateway Evidence**.
  Rechecking saved evidence performs only a log query. Delayed records remain
  pending/unverified; query errors propagate and partial results do not pass.

### Notebook and settings handoff

- `02_configure.ipynb`: **Load Deployment Settings**, **Compile Gateway Bicep**,
  **Deploy Gateway Configuration**, **Read Registered Connection**,
  **Write Gateway Settings**.
- `03_test.ipynb`: **Load Gateway Settings**, **Create Test Agent**,
  **Invoke Connected Model**, **Save Invocation Evidence**, **Clean Up Test Resources**,
  **Check Gateway Evidence**.
- Retain deployment-generated `env/.env` as the base-resource source of truth.
  Write additional non-secret connection/telemetry settings to ignored
  `env/gateway.json` only after successful configuration and connection readback.
  Include connection ID/name, callable model reference, gateway URL, and workspace ID.
  No manual environment population or arbitrary first-subscription selection.
- Preserve canonical setup/destroy notebooks. Add no hosted-agent scaffolding,
  debug-launch configuration, tracing framework, or evaluation suite for this
  service-side test harness.

## Changed files and validation

| Path | Necessary change | Observable check |
|---|---|---|
| `demos/byom01-capability-testing/infra/main.bicep` | APIM system-assigned identity | Bicep compilation; live identity readback without changing foundation settings. |
| `demos/byom01-capability-testing/infra/gateway.bicep` | API, backend/policies, project connection, telemetry | Compile supported schemas; connection readback and policy/diagnostic inspection satisfy SC-001/002. |
| `demos/byom01-capability-testing/infra/gateway-policy.xml` | Caller validation, fixed route, payload-marker-only trace | XML parsing and compiled substitutions; no logged bodies or token headers. |
| `demos/byom01-capability-testing/infra/backend-access.bicep` | Account-scoped inference role | Compile; verify assignment targets APIM principal and intended backend. |
| `demos/byom01-capability-testing/notebooks/02_configure.ipynb` | Deploy configuration and generate handoff | SC-001/002; rerun with unchanged settings reuses the same resources, SC-005. |
| `demos/byom01-capability-testing/notebooks/03_test.ipynb` | Foundry invocation, evidence, targeted test cleanup | Nonempty response SC-003; matching successful backend trace SC-004; cleanup SC-005. |
| `demos/byom01-capability-testing/requirements.txt`, `README.md`, `metadata.json` | Required SDKs and accurate configure/test/cleanup instructions | Existing setup installs dependencies; docs distinguish configured, invoked, and gateway-verified states. |
| Existing ignore configuration, only if needed | Exclude gateway settings and saved evidence | No generated evidence, credentials, or execution outputs enter tracked changes. |

**Offline:** compile changed Bicep using built-in tools, check notebook syntax using
available notebook/Pylance tools, and apply existing targeted notebook hygiene gates.
Verify current stable schemas for newly used resource types before implementation;
preserve existing foundation API versions. No new test framework or broad suite.

**Live, separately approved:** apply the consumer identity change, run Configure
twice, then run Test once. Pass only when the agent references the registered model,
returns output, and a trace with the same test marker identifies the intended backend
and successful forwarding. Reopen evidence and query again without another inference.
Verify test conversation/version deletion independently of telemetry availability.

Keep user-run configuration for later demos. For assistant-created validation
resources, record ownership before changes and remove only validation-created
resources/assignments, including applicable purges. Never delete pre-existing
consumer/backend groups as validation cleanup. Added telemetry resides in the
consumer group for documented full-demo destruction.

**Constitution check:** the proposed design follows the
[constitution](../../.specify/memory/constitution.md),
[authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md),
and [Foundry standards](../../.github/skills/azure-demo-authoring/references/azure-ai-foundry.md).
Changes remediate missing platform configuration in Bicep, not notebook error
wrappers. No local runtime workaround or authentication exception is approved.
The connection contract is source-verified; the narrow compiler accommodation was
approved. Live acceptance remains separately gated. No live checks were run
during planning or contract verification.

## Deferred artifacts

None. Keep verification findings in this plan; do not create parallel research,
contract, data-model, or quickstart documents. Implementation and live validation
still require their respective approvals.
