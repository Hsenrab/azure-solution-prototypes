# Feature Specification: BYOM Connected Model Through APIM

**Feature directory**: `specs/006-byom-connected-model`

**Created**: 2026-11-23

**Status**: Approved scope; ready for planning

**Input**: Configure gateway authentication, a backend route, and connected-model
registration in the consuming Foundry project. Invoke that connected model and
show evidence that the request passed through APIM to GPT-5.4.

## Problem and hypothesis

The BYOM demo provisions a consumer Foundry project, APIM, Search, and a separate
GPT-5.4 backend, but provisioning alone does not make a gateway-managed model
usable from Foundry.

**Hypothesis**: An engineer can configure the existing resources and invoke a
project-scoped connected model from Foundry using managed identities, receiving a
GPT-5.4 response and correlated APIM evidence that the request reached the
configured backend.

## User journey

One P1 journey completes the next slice:

1. Finish the existing setup/deployment journey and use its generated settings.
2. Open `demos/byom01-capability-testing/notebooks/02_configure.ipynb`.
   Load the selected subscription, consuming project, APIM, and backend settings.
   Apply Bicep-defined gateway identity, authentication policies, backend inference
   permission, route, connected-model registration, and minimal gateway diagnostics.
   Display the registered connection, callable model reference, and gateway URL.
3. Open `demos/byom01-capability-testing/notebooks/03_test.ipynb`.
   Create a minimal prompt agent whose model is
   `<connection-name>/<model-name>`, referencing the registered connected model.
   Send one harmless prompt through the consuming project's Foundry client.
4. Display the returned response and correlate that invocation with an APIM
   diagnostic record identifying the gateway API, intended backend, and successful
   backend outcome. Save compact, non-secret evidence so it can be reopened without
   another paid inference call.
5. Delete the test conversation and test-created agent version. Retain the
   configured connection and gateway for subsequent demo runs; document full-demo
   cleanup and any added telemetry resources.

### Observable acceptance

- **SC-001**: Configuration exposes a project-scoped connected model targeting
  the existing APIM runtime endpoint and the separate GPT-5.4 deployment.
  The notebook displays its registered identity and callable reference; adding
  the connection does not create another backend model deployment.
- **SC-002**: The Foundry project's managed identity is the allowed caller at
  APIM. APIM validates the tenant, audience, and permitted identity; it uses its
  own managed identity with backend inference permission to reach GPT-5.4.
  No gateway subscription key, backend key, or anonymous-access path is required.
- **SC-003**: The minimal Foundry prompt agent references the connected model and
  returns a nonempty model response. A direct backend/APIM call is not a substitute
  for this acceptance test.
- **SC-004**: Saved test evidence correlates the Foundry invocation with a gateway
  diagnostic record using a request/response identifier or equivalent supported
  correlation mechanism, identifying the intended GPT-5.4 backend and successful
  backend result. Response text, a configured URL, or aggregate request counts
  alone do not pass. Missing or delayed telemetry is reported as pending/unverified,
  never successful; reopening evidence does not repeat inference.
- **SC-005**: Repeating configuration with unchanged settings reuses the same
  gateway API, backend, connection/model reference, permissions, and telemetry
  resources. Test cleanup removes only its own conversation/agent version in a
  separate, explicit cell, leaving them available for inspection after invocation.

## Scope and constraints

### In scope

- Two small, notebook-first configure/test journeys.
- One project-scoped APIM connected model for the existing GPT-5.4 deployment.
- One project under the existing backend account for Foundry portal navigation,
  approved as a follow-up. The existing model stays account-scoped; verify that
  the backend project can be selected in the portal after deployment.
- Managed identity on the Foundry-to-APIM and APIM-to-backend hops, necessary
  inference RBAC, and gateway caller validation.
- One supported model protocol/route; choose and verify its exact URL contract
  during planning, rather than implement multiple protocol alternatives.
- A minimal prompt agent with no tools, used only to exercise the documented
  connected-model invocation path.
- Minimal APIM diagnostics using a suitable demo-owned Application Insights
  resource, or a new instance and its required Log Analytics workspace if none
  exists. Capture only the fields needed for routing/correlation evidence; do not
  enable broad prompt/response body logging.
- Generated connection/test settings, compact ignored evidence, directly related
  README/metadata/dependency changes, and cleanup instructions.

### Out of scope

- Standalone Azure AI Gateway; continue using the existing APIM Standard instance.
- Search ingestion, indexes, knowledge bases, Foundry IQ, agent tools, or RAG.
- Full Foundry tracing integration, dashboards, evaluation suites, model
  comparisons, safety-policy experiments, token-governance demonstrations,
  streaming tests, routing pools, failover, and load/performance testing.
- New model hosting, additional projects beyond the backend navigation project, model/region/SKU changes, or
  alterations to the existing GPT-5.4 capacity allocation.
- Production hardening, private networking, alternative authentication paths,
  generic application scaffolding, or a new test framework.

### Compatibility boundaries

- Keep the consumer in UK South and the backend in Sweden Central in the same
  explicitly selected subscription. Backend GlobalStandard capacity remains
  100 units (100,000 TPM). This is not a Sweden-only inference residency guarantee.
- Preserve public authenticated endpoints and backend `disableLocalAuth: true`.
  Do not enable keys or bypass tenant policy to simplify gateway setup.
- Define infrastructure/platform behavior, gateway policies, RBAC, connection
  resources where supported, and telemetry destinations in Bicep first.
  Notebooks deploy/consume that behavior through Python SDKs, using CLI only
  where the existing flow or missing SDK support requires it.
- Consume deployment-generated settings; any new connection/telemetry values
  must be generated from successful resource operations, not manually entered.
  Missing prerequisites and invalid configuration fail through their underlying
  errors; no fallback infrastructure or catch-and-explain-only remediation.
- Retain canonical setup ordering and the unchanged destroy notebook. Update
  cleanup documentation for new demo-owned resources without broadening deletion
  to unrelated or pre-existing resources.
- Keep dependencies minimal and changes self-contained in the BYOM demo.
  Preserve existing notebook hygiene checks and use built-in file tools for
  agent reading/inspection.
- Specification approval does not authorize implementation or live Azure changes
  for this slice. Obtain explicit live-operation approval before configuration,
  paid test calls, or modifying pre-existing resources. Validation-created
  resources require targeted cleanup; never delete pre-existing resources as
  validation cleanup.

## Existing context

Bounded discovery follows
[the Azure Demo Authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md).

- `demos/byom01-capability-testing/infra/main.bicep` — consumer Foundry account
  and project have system-assigned identities; APIM Standard currently has no
  configured managed identity, model route, or backend permissions. Search is
  provisioned but unconnected. Reuse the resources; adapt only gateway-dependent
  platform settings.
- `demos/byom01-capability-testing/infra/backend.bicep` — separate
  AIServices account and GPT-5.4 deployment in Sweden Central, public access with
  keys disabled, capacity 100. Reuse hosting unchanged; scope gateway inference
  access to this backend.
- `demos/byom01-capability-testing/notebooks/01_deploy_infra.ipynb` and
  `env/.env.example` — generated consumer/backend settings provide the source of
  truth for identifiers and endpoints; no keys are retrieved.
- `demos/byom01-capability-testing/app/notebook_helpers.py` — existing CLI
  executable resolver only; not a gateway/inference framework.
- `demos/byom01-capability-testing/requirements.txt` — currently management and
  identity dependencies only; connected-model invocation/telemetry SDK needs
  must be resolved during planning.
- `demos/byom01-capability-testing/README.md`, `metadata.json`, and
  `specs/005-byom-capability-testing/spec.md` — foundation and separate backend
  are the prior slice; connected models, routes, and inference were deferred.
- `demos/evalgw02-aoai-apim-eval/infra/main.bicep` — API/operation/backend
  definitions are a limited structural reuse candidate. Do not copy its classic
  OpenAI resource, Developer APIM tier, API-key backend authentication, or
  policy-bypass tags; these conflict with this demo's constraints. Its evaluation
  scenario does not prove Foundry connected-model registration.

Official capability evidence:

- [Foundry BYOM through APIM](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/ai-gateway)
  documents APIM classic/v1 support, project managed-identity authentication,
  managed-identity caller validation, model connections, and a minimal prompt
  agent using `<connection-name>/<model-name>`.
- [Gateway configuration in Foundry](https://learn.microsoft.com/en-us/azure/foundry/configuration/enable-ai-api-management-gateway-portal)
  distinguishes APIM from standalone Azure AI Gateway. Only requests using the
  connected model are routed through its gateway.
- The connection sample linked by the BYOM article returned HTTP 404 during
  discovery. Planning must verify the current supported connection schema/sample,
  SDK versions, route contract, and minimal diagnostic correlation mechanism.
  Do not infer these from the older evaluation demo or claim live feasibility
  has been validated for this slice.

## Assumptions

- The user approved two notebooks, managed identities, the minimal prompt-agent
  harness, and gateway diagnostics as specification scope.
- Existing resources/settings are prerequisites, not authorization to modify
  them. The latest user-shared output confirms the environment-write step ran;
  it is not verification of gateway readiness or current runtime permissions.
- Runtime permissions for the signed-in notebook user and ability to assign
  roles/manage connections must be available before live testing.
- APIM telemetry ingestion can be delayed. The test journey must let the engineer
  recheck the original invocation's evidence without another model call.
- No connection protocol, SDK version, or correlation implementation is locked
  by this specification; planning must select one supported happy path within
  the approved boundaries and surface any blocking platform limitation.
