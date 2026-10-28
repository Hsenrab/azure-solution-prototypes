# Data Model: Search Debug Environment

This feature has deployment/configuration entities, not application tables or migrations.
No search-index schema or synthetic-record model is created here.

## Deployment Inputs

| Field | Meaning and validation |
|-------|------------------------|
| subscriptionId | Explicitly selected subscription UUID; never first enabled subscription |
| tenantId | Tenant of the signed-in setup user and selected subscription |
| operatorObjectId | Object ID of that user; service-principal/client IDs are not substitutes |
| resourceGroupName | New demo-only group name; suggested `rg-search02-hybrid-pagination-ne` |
| location | `northeurope`, explicitly approved; no fallback region |
| deploymentName | Stable name for subscription-scope deployment records |
| demoId | `search02-hybrid-pagination`; stable ownership tag value |

Basic tier, one replica/partition, public networking, and disabled local authentication
are Bicep-defined behavior, not notebook toggles.

## Debug Environment

One subscription contains one newly created demo group. That group contains one
Search service; the service has two role assignments for one user.

| Field | Invariant |
|-------|-----------|
| resourceGroupId | Belongs to selected subscription and is exclusively demo-owned |
| ownershipTag | `demo=search02-hybrid-pagination`; conflict/missing ownership blocks adoption |
| searchServiceName | Globally unique valid name with stable group/subscription suffix |
| searchResourceId | Child of the expected resource group |
| searchEndpoint | HTTPS public Search endpoint for that service |
| sku | Basic |
| replicas / partitions | 1 / 1 |
| disableLocalAuth | true |
| publicNetworkAccess | enabled using the selected ARM schema's enum spelling |
| ipRules | no allowlist |

## Access Assignment

Two assignments target `operatorObjectId` with principal type `User`. Names are stable
GUIDs derived from service resource ID, principal ID, and role definition ID.

- Search Service Contributor: index/object management and metadata.
- Search Index Data Contributor: future document upload/query.

Both are service-scoped. No index exists yet. Inherited pre-existing permissions
are not evidence that the Bicep-owned assignments were created correctly.

## Environment Handoff

The authoritative export is defined by the
[handoff contract](./contracts/environment-handoff.md). It contains identifiers and
endpoint values, never credentials. Regenerate it from successful deployment outputs;
do not manually edit it to repair a deployment or retain stale success evidence.

## Readiness Evidence

Record the subscription/group/service IDs, actual
provisioning/security/capacity settings, operator tenant/object ID, assignment IDs,
metadata status, SDK/API versions, observation time (`observedAt`, UTC), and
zero-index/document counters from the SDK's supported statistics model.
Include a clear overall status:
`ready`, `blocked`, or `failed`, with the underlying failure available.

Evidence is local and generated, for example under `outputs/generated/`, already
ignored by the repository. It must not contain access tokens or request auth headers.
Document-operation validation remains `deferred-to-feature-2`, not `passed`.
Azure deployment validation/what-if precedes deployment; save the actual preview
as `outputs/generated/what-if.json`. No manually maintained policy-review file is
an input to export or readiness, and those records do not claim a full policy audit.

## Lifecycle

`specified -> prerequisites-ready -> validated/previewed -> deploying -> deployed -> ready`

- Compilation/validation failure prevents deployment.
- A resource or permission failure produces `failed` or `blocked`, not `ready`.
- Successful deployment can be `blocked` on RBAC propagation; rerun the explicit
  metadata check once the prerequisite is resolved, without silent automatic fallback.
- Redeployment reuses the same owned group/service and assignment identities.
- Explicit cleanup: `deployed/ready/blocked/failed -> deleting -> deleted`.
  Failed/partial deployments can still have billable resources requiring cleanup.
- `deleted` is established by actual group absence. Missing resources on a later
  cleanup run are a reported state, not proof a new deletion occurred.
- Cleanup evidence in `outputs/generated/us3-cleanup.json` records the observed
  `lifecycleState` and `observedAt` (UTC); use `deleted` only after verified group
  absence. The final README reports this latest observed lifecycle state.
- Retain `outputs/generated/readiness.json` as the timestamped outcome of its check.
  After deletion it is historical, not current availability; `env/.env` is stale.
- Before Feature 2, separately approve and rerun deployment, export, and readiness
  validation. Refresh the evidence for that deployment; do not automatically
  recreate resources after cleanup or implicitly keep paid resources running.
