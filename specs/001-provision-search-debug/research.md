# Research: Search Debug Environment

**Date**: 2026-10-23
**Scope**: Feature 1 planning research, with the execution corrections below.
Planning itself performed no deployment or provider registration. Subsequent,
separately approved acceptance deployed/redeployed the service, verified metadata
access, and deleted the owned group; Microsoft.Search registration remains in place.

## 1. Service Tier, Region, and Cost

**Decision**: Basic, one replica and one partition, in `northeurope`. The user
explicitly chose this paid option during planning after Free was offered.

**Rationale**: One search unit is the minimum Basic footprint and provides capacity
for the subsequent small synthetic experiment without introducing other resources.
Single-unit configuration is for experimentation, not a high-availability claim.

**Alternatives considered**: Free supports Entra authentication and core search
capabilities; it was not rejected as technically unsupported. Its shared capacity,
small quotas, and one-service-per-subscription constraint were disclosed. The user
selected Basic instead. Standard is unnecessary without the existing private demo's
outbound shared-private-link requirements.

Public Retail Prices research returned a Basic meter entry for North Europe of
USD 0.101/hour per unit: approximately USD 2.42/24 hours or USD 73.73/730 hours.
That entry was not marked a primary-meter region; treat it as indicative, not a
binding regional quote. Reconfirm current regional/currency/subscription pricing
before provisioning. Billing continues while the service exists, even when idle.
No budget-alert resources or automated deletion are included.

**Sources**:
- [Tier selection](https://learn.microsoft.com/en-us/azure/search/search-sku-tier)
- [Role-based access prerequisites](https://learn.microsoft.com/en-us/azure/search/search-security-enable-roles)
- [Limits and quotas](https://learn.microsoft.com/en-us/azure/search/search-limits-quotas-capacity)
- [Pricing](https://azure.microsoft.com/en-us/pricing/details/search/)
- [Retail Prices API](https://prices.azure.com/api/retail/prices)

## 2. ARM APIs and Deployment Scope

**Decision**: Use Search `2025-05-01`, resource groups `2022-09-01`, and role assignments
`2022-04-01`. A subscription-scope Bicep wrapper creates the group and a scoped module
creates Search and its roles. No resource group is separately created in notebook code.

**Rationale**: Read-only provider metadata in the confirmed subscription advertised
both selected Search and group API versions. Search metadata listed North Europe.
A later/future-dated schema appearing in documentation is not sufficient evidence
of deployment support; the provider-advertised stable API is the chosen baseline.

**Alternatives considered**: Existing Search uses `2023-11-01`; it remains prior art
but a newer advertised stable API is available. Preview APIs are unnecessary.
Group-scope-only deployment plus SDK group creation would split infrastructure
ownership; the subscription wrapper keeps the requested infrastructure in Bicep.

**Sources**:
- [Search 2025-05-01 schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.search/2025-05-01/searchservices)
- [Resource group schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.resources/2022-09-01/resourcegroups)
- [Role assignment schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.authorization/2022-04-01/roleassignments)
- [Subscription deployments](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-to-subscription)

## 3. User Identity and RBAC

**Decision**: Use the setup user's CLI login via `AzureCliCredential`. Resolve its
tenant and user object ID explicitly; assign these two roles at service scope:

| Role | Definition ID | Purpose |
|------|---------------|---------|
| Search Service Contributor | `7ca78c08-252a-4471-8644-bb5ff32d4ba0` | Index/object management and service metadata |
| Search Index Data Contributor | `8ebe5a00-799e-43f5-93ac-243d3dce84a7` | Upload and query documents in Feature 2 |

**Rationale**: Neither role alone supplies both index-definition management and
document operations. An index-scoped role is premature because Feature 1 creates no
index. Deterministic assignment names prevent duplicate assignments on redeployment.
Disabled local authentication means neither client needs a Search key.

**Alternatives considered**: No Data Reader assignment is needed in addition to
Data Contributor. Owner/Contributor does not substitute for document data-plane
access. A managed identity or application secret is unnecessary for local execution.
An unrestricted `DefaultAzureCredential` chain could choose a different identity;
the explicit CLI credential preserves the user's clarified requirement. This is
credential selection within the approved CLI-user auth strategy, not a new login flow.

**Sources**:
- [Search roles and permissions](https://learn.microsoft.com/en-us/azure/search/search-security-rbac)
- [Azure CLI credential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.azureclicredential)

## 4. Non-Mutating Readiness Check

**Decision**: Use stable `azure-search-documents` and
`SearchIndexClient.get_service_statistics()` with `AzureCliCredential` and its
supported stable API. Validate `statistics.counters.index_counter.usage` and
`statistics.counters.document_counter.usage` through the SDK model without creating
an index or submitting any document query. Record the selected SDK/API versions.

**Rationale**: Service statistics is read-only and available to the assigned Search
Service Contributor. Document roles alone would not authorize this operation.
The Python SDK supports this operation, so using it follows the constitution's
SDK-first rule. This metadata dependency does not choose either Feature 2 client's
reproduction SDK version; no .NET implementation is needed to establish the handoff.

**Alternatives considered**: A test index/upload/query would violate the feature
boundary. Treating an expected 403/404 as a successful connectivity probe would
misrepresent readiness. An ARM-only status check would not prove data-plane access.
A hand-written REST request adds token/transport/response handling for an operation
already supported by the SDK, so it is not the chosen implementation.

**Sources**:
- [SearchIndexClient and get_service_statistics](https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.searchindexclient?view=azure-python)
- [Search service statistics model](https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.searchservicestatistics?view=azure-python)
- [Search service counters model](https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.searchservicecounters?view=azure-python)
- [Service statistics REST API](https://learn.microsoft.com/en-us/rest/api/searchservice/get-service-statistics/get-service-statistics?view=rest-searchservice-2025-09-01)

## 5. Tenant Policy and Runtime Prerequisites

**Decision**: Preserve the approved public endpoint with disabled local authentication.
Recheck scoped policies before deployment; stop for user direction on any conflict.
Explicitly require provider registration before resource deployment.

**Initial evidence (superseded)**: The earlier read-only CLI review found three
initiatives with eleven database/SQL-related definitions and no exemptions. Its
unfiltered query omitted inherited management-group assignments. Planning also
found Microsoft.Search `NotRegistered` and zero visible Search services; no
registration or capacity test was performed during that research.

**Execution correction**: Before deployment, Windows-safe `atScope()` assignment
and exemption queries found ten inherited assignments: seven initiatives with 330
member references plus three direct policies, covering 321 distinct definitions.
All referenced definitions and effective effects were resolved. Search networking,
private-link, and logging recommendations were Audit/AuditIfNotExists; no enforced
private-network requirement conflicted with the approved design. Other mutating
initiative rules did not target Search/group/role resources. The direct classic
resource Deny did not apply; user write/delete MFA requirements remained enforced.
No visible exemptions were found. Actual-group assignments matched the full review.
This is scoped evidence, not proof of tenant-wide compliance. The
[shared policy procedure](../../.github/skills/azure-demo-authoring/references/workflow.md#scoped-azure-policy-review)
now includes inherited-query and Windows quoting requirements.

**Rationale**: Successful metadata listing is not capacity, policy-validation, or
deployment success. An absent future group cannot have its existence assumed during
policy inspection; review inherited scope now and actual target scope when available.

**Alternatives considered**: No private endpoint/VPN infrastructure is required.
No automatic registration, region/tier substitution, policy exemption, or key fallback.

## 6. Canonical Notebook and Cleanup Constraints

**Decision**: Preserve the canonical setup ordering, minimal CLI executable helper,
and verbatim destroy notebook. Use explicit subscription alignment before cleanup.

**Rationale**: The source destroy notebook uses active CLI context rather than
`AZURE_SUBSCRIPTION_ID` for its commands. Therefore the run guide must require
checking the current subscription and exact group before deletion. Its existing
confirmation defaults must be reviewed explicitly; opening a notebook is not deletion.
No local catch-and-explain wrapper or cleanup rewrite is planned.
After verified deletion, record lifecycle state `deleted` with its observation time.
Preserve earlier readiness as historical evidence, not current availability; the
environment export is stale. Feature 2 requires a separately approved rerun of
deployment, export, and readiness. Cleanup acceptance does not implicitly authorize
reprovisioning or keeping paid resources running.

**Sources**:
- [Setup source](../../demos/speech01-foundry-speech/notebooks/00_setup.ipynb)
- [Destroy source](../../demos/speech01-foundry-speech/notebooks/X_destroy.ipynb)
- [CLI resolver](../../demos/speech01-foundry-speech/app/notebook_helpers.py)
- [Existing Search deployment flow](../../demos/search01-private-endpoints/notebooks/01_deploy_infra.ipynb)

## Resolution

All design questions are resolved. Separately approved deployment/redeployment and
same-user metadata access succeeded, followed by verified whole-group cleanup.
The SDK credential must bind only the subscription because Azure CLI rejects
simultaneous tenant/subscription token arguments. The Search control plane returns
`North Europe`, requiring display-name normalization in the read-only comparison.
Both corrections have regression coverage; neither changes deployed infrastructure.
The canonical per-resource cleanup command's unsupported `--yes` error was preserved;
the canonical group-deletion step succeeded without a demo-local cleanup fork.

See [current lifecycle and evidence](../../demos/search02-hybrid-pagination/README.md#validation-status).
Readiness is historical, the export is stale, and Feature 2 is not implemented.
Future execution must recheck pricing, policy, capacity, privileges, and propagation.
