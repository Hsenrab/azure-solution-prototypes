# Contract: Deployment Outputs and Feature 2 Handoff

This is a language-neutral deployment interface, not a hosted application API.
Feature 2 consumes it unchanged from Python and .NET.

## Bicep Input Boundary

The subscription wrapper accepts `resourceGroupName`, `location`, `operatorObjectId`,
and `demoId`. It obtains subscription and tenant context from the selected deployment
scope. A scoped module receives the identity and relevant naming inputs.
No password, Search key, client secret, network-mode switch, or alternate identity
is an input.

## Required Outputs and Environment Mapping

| Bicep output | Generated environment variable | Constraint |
|--------------|--------------------------------|------------|
| subscriptionId | AZURE_SUBSCRIPTION_ID | Actual deployment subscription |
| tenantId | AZURE_TENANT_ID | Actual subscription/operator tenant |
| resourceGroupName | AZURE_RESOURCE_GROUP | Exact demo-owned cleanup target |
| resourceGroupId | AZURE_RESOURCE_GROUP_ID | Full resource-group ID |
| location | AZURE_LOCATION | northeurope |
| searchServiceName | AZURE_SEARCH_SERVICE_NAME | Deployed service name |
| searchResourceId | AZURE_SEARCH_RESOURCE_ID | Full service resource ID |
| searchEndpoint | AZURE_SEARCH_ENDPOINT | HTTPS endpoint, no credentials/query string |
| operatorObjectId | AZURE_OPERATOR_OBJECT_ID | Signed-in setup user's object ID |

Output values must be nonempty and mutually consistent before export.
This file is a simple UTF-8 `KEY=value` environment file under the demo's `env/.env`.
`env/.env.example` documents the same keys with harmless placeholders only.
No SDK-specific connection string or per-language deployment is required.

The common `AZURE_*` names do not authorize an arbitrary default credential chain:
both clients must use the clarified CLI user. `AZURE_OPERATOR_OBJECT_ID` is metadata,
not a credential or an instruction to sign in as another user.

## Export Semantics

- Export only after the deployment's actual successful completion.
- Write the complete mapping in one file write; do not append competing values.
- Preserve failure if required outputs are missing; do not invent names or endpoints.
- Never export account keys, client secrets, tokens, or Authorization headers.
- Treat a previous run's environment/evidence as stale until the selected environment
  and actual deployment result are confirmed.
- The environment export is not a readiness-success assertion; metadata validation
  can still be blocked after successful provisioning.

## Feature 1 Readiness Interface

Read-only ARM inspection must show approved service settings and the two intended
role assignments. Use the stable Python SDK's
`SearchIndexClient.get_service_statistics()` with the same user's `AzureCliCredential`
and the selected SDK's supported stable API. The Search token audience is
`https://search.azure.com`; do not hand-write token or HTTP transport handling.

Expected: the SDK call succeeds, `statistics.counters.index_counter.usage = 0`, and
`statistics.counters.document_counter.usage = 0` for a new Feature 1 environment.
Use the selected SDK's supported model, not REST JSON field names. SDK exceptions
or missing/unexpected counters fail or block the check; they are not converted into
zero values or an empty success response. Record the observation time and SDK/API
versions with the readiness result. This metadata SDK version does not constrain
either Feature 2 reproduction client's SDK version.
Once Feature 2 has populated the environment, this zero-index baseline no longer
applies: do not delete Feature 2 data to make Feature 1's initial acceptance pass.

These checks do not prove effective document upload/query permissions. Feature 1
records the role assignments; Feature 2 executes document operations in both clients.

## Cleanup Interface

Before executing the canonical destroy notebook, align the Azure CLI subscription
with `AZURE_SUBSCRIPTION_ID` and review `AZURE_RESOURCE_GROUP` and the actual resources.
The destroy source currently relies on active CLI context. Do not assume loading
an environment file changes that context.

The entire dedicated group and its contents are the approved deletion boundary.
Explicit destructive-step confirmation is still required; no deletion is authorized
by reading this contract, opening the notebook, or approving the plan.

After verifying group absence, record lifecycle state `deleted` and its observation
time in cleanup evidence and report that state in the final README. Preserve prior
readiness evidence as historical observations; it no longer asserts current
availability, and the exported environment is stale.

Before Feature 2, obtain execution approval and rerun deployment, output export,
and readiness validation. Only that refreshed successful handoff is usable.
Do not automatically redeploy after cleanup or leave paid resources running
implicitly to maintain a handoff.
