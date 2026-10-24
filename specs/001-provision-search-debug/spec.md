# Feature Specification: Provision Search Debug Environment

**Feature Branch**: Not created; specification directory is independent of the current branch.

**Created**: 2026-10-23

**Status**: Implemented and validated - Feature 1 deployment, redeployment, metadata
readiness, and cleanup accepted on 2026-10-23. Latest lifecycle: `deleted`;
readiness is historical and the export is stale. Feature 2 remains unimplemented.

**Input**: Split the debugging demo into two features. Feature 1 provisions all shared
infrastructure needed for an Azure AI Search hybrid count/pagination investigation
using Bicep. Feature 2 creates the index and dummy data, then reproduces and explains
the symptom using Python and .NET against that same environment.

**Enables**: [Feature 2 - Reproduce Hybrid Search Count/Pagination Discrepancy](../002-reproduce-hybrid-pagination/spec.md).

## Clarifications

### Session 2026-10-23

- Q: How should we resolve the tenant network restrictions before choosing Feature 1's access pattern? -> A: Private endpoints are not a requirement. First verify applicable Azure Policy restrictions using Azure CLI in the confirmed deployment scope, then select compliant networking; retain keyless Microsoft Entra authentication.
- Q: Should Azure Policy be inspected for the currently selected subscription? -> A: Yes; inspect the explicitly confirmed current subscription using read-only Azure CLI checks.
- Q: Based on the policy check, should Feature 1 use a public Search endpoint with keyless Microsoft Entra authentication? -> A: Yes; enable the public endpoint without an IP allowlist or private endpoints, require Entra authorization, and disable key authentication, subject to final target-scope validation.
- Q: Should this demo create and own a new dedicated resource group? -> A: Yes; create a new demo-only group and permit explicitly confirmed deletion of that group and its contents.
- Q: Who should receive permission to create the demo index, upload dummy data, and run both language examples? -> A: The user who signs in during setup receives access and runs both Python and .NET clients locally.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Provision One Shared Debugging Environment (Priority: P1)

As an engineer, I want a small, isolated Search environment provisioned from a
repeatable definition, so that both language examples can investigate the same
service rather than differ because of separately configured infrastructure.

**Why this priority**: A shared environment is the prerequisite for the reproduction
and avoids unnecessary resources and configuration differences.

**Independent Test**: Provision the environment in an explicitly selected subscription,
inspect its deployment result, and verify the declared service configuration and
required access without creating a search index or executing the reproduction.

**Acceptance Scenarios**:

1. **Given** an authorized subscription, target location, and operator identity,
   **When** the engineer provisions the environment, **Then** one dedicated demo
   resource group is created and contains a successfully provisioned Search service with the capacity
   and capabilities required for Feature 2's synthetic vector/hybrid experiment.
2. **Given** the same deployment inputs and an existing deployment,
   **When** provisioning is repeated, **Then** the same intended environment is updated
   without creating an additional Search service or duplicate access assignments.
3. **Given** unavailable capacity, unsupported configuration, or insufficient permission,
   **When** provisioning fails, **Then** the failure remains visible and no successful
   environment handoff is reported.
4. **Given** the confirmed deployment scope, **When** networking is selected,
   **Then** read-only Azure CLI policy inspection has established applicable
   constraints or explicitly identified gaps that block the decision.

---

### User Story 2 - Hand Off Usable Configuration to Both Clients (Priority: P1)

As an engineer, I want non-secret connection details and the necessary permissions
recorded automatically, so that Python and .NET can use one environment without
manual endpoint entry or credential copying.

**Why this priority**: Resource creation alone is insufficient if Feature 2 cannot
create/populate its index or query the service.

**Independent Test**: Inspect deployment outputs, generated local configuration,
and effective access. Verify authorized data-plane connectivity without creating
an index, uploading records, or running search queries.

**Acceptance Scenarios**:

1. **Given** a successful deployment, **When** configuration is exported,
   **Then** the selected subscription, resource group, service identity, location,
   and endpoint are unambiguous and available to both future clients.
2. **Given** the user who signed in during setup and completed permission propagation,
   **When** authorized service/index metadata access is checked, **Then** connectivity
   succeeds and the assigned permissions cover Feature 2's index-management,
   document-upload, and query operations for that same user in both local clients.
3. **Given** exported configuration, **When** a reviewer inspects it,
   **Then** it contains no credentials or service keys, and users do not need to
   manually populate the generated local environment file.
4. **Given** the deployed environment, **When** network and authentication settings
   are inspected, **Then** they match the policy-validated design, local/key
   authentication is disabled, and authorized metadata access succeeds through
   the approved network path.

---

### User Story 3 - Remove the Disposable Environment Safely (Priority: P2)

As an engineer, I want the standard cleanup journey to remove only this demo's
resources, so that the investigation does not leave ongoing costs or affect
unrelated environments.

**Why this priority**: This is a disposable debugging environment, not a production service.

**Independent Test**: After provisioning, execute explicitly confirmed cleanup and
verify the dedicated resources are gone while unrelated resources remain untouched.

**Acceptance Scenarios**:

1. **Given** an explicitly confirmed cleanup targeting the dedicated demo environment,
   **When** cleanup completes, **Then** the demo resources are removed without deleting
   resources outside that scope.
2. **Given** cleanup has not been confirmed, **When** the destroy journey is opened,
   **Then** no resources are deleted solely by opening it.
3. **Given** the environment is already removed, **When** cleanup is reviewed or repeated,
   **Then** its actual state is reported accurately rather than mistaken for a new deployment.

### Edge Cases

- Multiple accessible subscriptions: require explicit selection or resolve the intended
  target using repository guidance; never choose the first enabled subscription.
- An existing name belongs to another resource: report the conflict rather than
  adopt, overwrite, or delete unrelated infrastructure.
- A proposed resource-group name already belongs to an unrelated group: stop rather
  than adopt it. Redeployment may reuse only the group already owned by this demo.
- The requested region or service tier is unavailable: fail visibly; do not silently
  substitute a different region or more expensive tier.
- Permission propagation is incomplete: report access validation as pending/blocked,
  not proof that Feature 2 is ready.
- The setup user's tenant or principal cannot be resolved, or later execution uses
  another identity: stop with the underlying identity/access error rather than grant
  a different identity access or switch to application credentials.
- Policy assignments or definitions cannot be fully inspected: record the access or
  evidence gap; do not assume public access is permitted or private access is required.
- The selected network path is unavailable: report the handoff as blocked rather
  than silently change network policy or enable key authentication.
- Partial deployment: preserve failure information and provide the standard scoped
  cleanup path; do not report a successful handoff.
- Local configuration is stale after redeployment: regenerate it from the actual
  deployment outputs rather than rely on manually maintained values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The environment MUST be a self-contained demo under
  `demos/<demo-name>/`, using the repository template, minimal dependencies, and
  directly related documentation/metadata.
- **FR-002**: Bicep MUST be the source of truth for shared infrastructure and platform
  behavior, including the Search service configuration and required role assignments.
- **FR-003**: There MUST be one shared Search service for the Python and .NET
  reproduction examples, capable of supporting a vector-enabled index with at least
  6,158 synthetic records and keyword, vector, and hybrid queries.
- **FR-004**: Deployment MUST identify the target subscription, resource group,
  location, operator identity, and selected service capacity explicitly.
  It MUST create a new dedicated demo-only resource group on first deployment;
  existing unrelated or shared groups MUST NOT be adopted. Redeployment MUST reuse
  the same demo-owned group.
- **FR-005**: Following the user's planning decision, the design MUST use Basic with
  one replica and one partition in North Europe, and document expected costs before
  execution. Free was considered but the user explicitly selected paid Basic.
  It MUST NOT deploy
  an embedding model, Foundry resource, UI host, or unrelated service for this feature.
  The approved design MUST NOT add private endpoints, VPN, private DNS, or an IP
  allowlist. If target-scope validation reveals a conflicting policy, deployment
  MUST stop for a user-approved scope/design decision rather than add those resources.
- **FR-006**: Access MUST use the repository's Azure identity conventions without
  stored service keys. Search MUST disable local/key authentication.
  The user who signs in during setup is the intended operator and MUST receive the permissions
  necessary for Feature 2 to create/manage its index, upload records, and query it.
  The role-assignment target MUST be resolved from that user's tenant and principal;
  it MUST NOT silently select a different identity. Both local language clients
  MUST use the same authorized user. A separate application identity, client secret,
  or team/group access model is not required for this feature.
  Following the subscription policy check, Search MUST enable its public endpoint
  without an IP allowlist and require Entra authorization through assigned roles.
  Final target-scope policy validation MUST precede deployment. A conflicting policy
  requires a user-approved design decision; it MUST NOT be bypassed.
  Key authentication MUST NOT be used as a fallback.
- **FR-007**: Deployment outputs MUST expose non-secret resource identifiers,
  subscription/resource-group context, location, service endpoint, and the authorized
  user's tenant/principal identifiers. The deployment
  journey MUST generate local `env/.env` from those outputs automatically.
- **FR-008**: Both clients MUST be able to consume the same environment handoff;
  provisioning MUST NOT depend on either client's chosen Search data-plane SDK version.
- **FR-009**: The deployment MUST be repeatable with stable inputs without duplicating
  the intended service or access assignments.
- **FR-010**: Handoff evidence MUST include actual deployment status, deployed
  configuration, and authorized metadata-access validation. Provisioning success
  MUST NOT be presented as evidence of a reproduced pagination symptom.
  Readiness evidence MUST be timestamped and distinguished from current
  availability after cleanup.
- **FR-011**: The feature MUST follow the canonical setup and destroy notebook
  structures, deployment-output flow, and notebook metadata checks referenced below.
  Non-applicable configuration/test steps MUST state that index and experiment work
  belongs to Feature 2 rather than execute that work prematurely.
- **FR-012**: Cleanup MUST require the standard confirmation and target only this
  demo's dedicated environment, following the repository destroy source of truth.
  Confirmed cleanup MUST delete the demo-owned resource group and all its contents;
  no unrelated resources may be placed in that group.
  Verified cleanup MUST record lifecycle state `deleted`; prior readiness evidence
  is historical and the environment export is stale. Feature 2 MUST use a refreshed
  handoff after explicitly approved deployment, export, and readiness validation;
  cleanup MUST NOT trigger automatic reprovisioning.
- **FR-013**: This feature MUST NOT create a Search index, generate/upload dummy
  records, implement either search client, or run the reproduction. Those are
  explicitly owned by Feature 2.
  Metadata-only SDK access for readiness is permitted; neither language's
  reproduction client is implemented here.
- **FR-014**: Failures and partial completion MUST remain visible. Notebook code MUST
  NOT silently change infrastructure policy or add fallback paths to mask deployment
  or access failures.
- **FR-015**: Before selecting networking or authorizing deployment, read-only Azure
  CLI checks MUST inspect applicable policy assignments, including inherited
  assignments, their policy/initiative definitions, effective parameters/effects,
  enforcement settings, and applicable exemptions/exclusions. Inspection MUST use
  the explicitly confirmed subscription and intended resource-group scope when
  known. Evidence MUST distinguish enforced restrictions from audit-only findings
  and identify incomplete visibility. Existing demo settings or an empty compliance
  report MUST NOT be treated as proof that the proposed deployment is allowed.

### Key Entities

- **Debug environment**: The dedicated resource scope and Search service shared
  by both clients.
- **Deployment inputs**: Selected subscription, resource group, location, service
  naming/capacity, and operator identity.
- **Access assignment**: Permissions granted to the user who signs in during setup,
  identified by tenant and principal, for later index-management, upload, and query
  operations from both local language clients.
- **Environment handoff**: Non-secret deployment outputs, generated local
  configuration, and readiness evidence consumed by Feature 2.
- **Cleanup scope**: The new demo-owned resource group and all its contents,
  eligible for deletion only through explicitly confirmed cleanup.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One deployment yields exactly one intended shared Search service,
  in exactly one new dedicated demo-owned resource group, with its selected
  subscription, resource group, location, and status recorded.
- **SC-002**: Repeating the deployment with unchanged inputs creates zero additional
  intended Search services or duplicate access assignments.
- **SC-003**: All required non-secret handoff values are generated automatically;
  zero credentials or service keys appear in the handoff or committed artifacts.
- **SC-004**: The signed-in setup user passes authorized metadata-access validation.
  Evidence identifies that user's tenant/principal and assigned permissions for all
  three later operation categories: index management, document upload, and querying.
  Actual document operations and language-client execution remain Feature 2 acceptance.
- **SC-005**: Explicitly confirmed cleanup leaves zero demo resources in the
  declared cleanup scope, removes the demo-owned resource group itself, and deletes
  zero resources outside it.
- **SC-006**: Feature 1 acceptance creates zero search indexes, uploads zero test
  documents, and makes zero reproduction search requests.
- **SC-007**: Policy-check evidence records the confirmed scope, relevant effective
  restrictions and exemptions, and any visibility gaps. Networking is not finalized
  while a relevant restriction remains unresolved; deployed settings match the
  resulting approved design and keep local/key authentication disabled.

## Assumptions

- Requirements and planning approval do not authorize creating demo implementation
  files, deploying Azure resources, registering providers, or deleting resources.
- The user approved the two-feature split. Feature 2 depends on this environment;
  either client alone is not a reason to provision an additional service.
- The resource group is newly created for this demo and remains exclusively demo-owned.
  Whole-group deletion is the approved cleanup boundary, with explicit confirmation
  required at execution time; this is not authorization to delete anything now.
- Bicep is an explicit user requirement. During planning the user selected Basic,
  one replica and one partition, in `northeurope`, accepting ongoing usage charges.
  Exact API versions, naming, and identity roles are documented in the plan.
  Public access without an IP allowlist, Entra authorization, and disabled key
  authentication are confirmed requirements, subject to final target-scope validation.
- Local authorized execution is the baseline user journey; a CI/CD deployment
  pipeline and unrelated production controls are not additional scope requirements.
  Public access was approved after subscription-level policy inspection.
  Its target-scope compliance still requires confirmation before deployment.
  An existing private-only demo does not establish a tenant-wide restriction.
- The operator has, or can obtain, rights to provision resources and assign the
  required permissions. Missing rights block execution rather than justify key-based
  credential workarounds.
- The signed-in setup user is also the local Python and .NET operator; delegated
  access to other identities, unattended execution, and group-based sharing are
  outside this feature's requirements. Exact role definitions and credential APIs
  remain planning decisions, not additional user-identity choices.
- Basic 1/1 in North Europe is the approved configuration. Planning alone does not
  establish runtime capacity, an actual subscription price, or deployment success;
  those require execution evidence. The approved acceptance run succeeded, but
  future runs must recheck their current prerequisites.
- No provisioning or cleanup is authorized by approval of this specification alone.
- The initial read-only CLI inspection on 2026-10-23 returned three subscription
  initiatives with eleven database-related definitions and no exemptions. That query
  omitted inherited management-group assignments and was incomplete; it is not the
  final policy evidence. Before deployment, an explicit `atScope()` review resolved
  ten inherited assignments: seven initiatives/330 member references plus three
  direct policies, covering 321 distinct definitions, with no visible exemptions.
  Search networking recommendations were audit-only; user write/delete MFA policies
  remained enforced. Actual-group assignments matched that reviewed evidence.
- This is not a tenant-wide compliance guarantee or authorization for future runs.
  The implemented group is `rg-search02-hybrid-pagination-ne`. Its deployment and
  cleanup were separately approved and verified; read-only policy inspection itself
  made no Azure changes. See [acceptance evidence and current lifecycle](../../demos/search02-hybrid-pagination/README.md#validation-status).

### Applicable Repository Guidance

- [Constitution](../../.specify/memory/constitution.md)
- [Copilot instructions](../../.github/copilot-instructions.md)
- [Azure Demo Authoring](../../.github/skills/azure-demo-authoring/SKILL.md)
- [Authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md)
- [Demo template](../../demo-template/)
- [Notebook Metadata Check](../../.github/workflows/notebook-metadata-check.yml)
- [Existing private-endpoint Search demo](../../demos/search01-private-endpoints/README.md):
  reference only if the policy-validated design needs private connectivity.
