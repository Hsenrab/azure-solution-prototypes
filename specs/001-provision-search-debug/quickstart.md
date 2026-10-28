# Planned Validation Guide: Feature 1

**Status**: Implemented. The current workflow uses Azure validation/what-if rather
than a manually maintained policy-review approval file. Historical acceptance and
the latest observed lifecycle are recorded in the
[demo README](../../demos/search02-hybrid-pagination/README.md#validation-status).
Do not interpret commands or expected results as evidence of a new deployment.

## Prerequisites and Approval

- Use the existing VS Code/Jupyter notebook workflow, Python 3.11+, Azure CLI, and Bicep.
- Select the intended subscription explicitly. The signed-in user must be able to
  deploy at subscription scope, create a resource group/Search service, and create
  the required service-scoped role assignments.
- Approve the actual cost before execution: paid Basic, one search unit, North Europe.
  The indicative public lookup was USD 0.101/hour; reconfirm actual pricing.
- Confirm provider registration; run the notebook's Azure validation/what-if for
  the target scope before deployment. Resolve policy/permission errors rather than
  bypassing them. No `policy-review.json` file is required.
- No .NET installation or reproduction client is required for Feature 1 acceptance.
  The stable Python Search SDK is used only for read-only metadata readiness.

## 1. Set Up the Demo

Open `demos/search02-hybrid-pagination/notebooks/00_setup.ipynb`.
Run the canonical environment/kernel step, switch to that kernel, authenticate and
select the subscription, then install the demo requirements. Do not reorder the steps.

## 2. Review Azure Policy and Provider State

In the deployment notebook, confirm prerequisites, compile Bicep, and run
**Validate and review what-if**. The SDK checks the actual template and selected
subscription before the paid-deployment step, then saves `what-if.json`.
Export and readiness do not read a manual policy-review file. A successful preview
is not a full advisory-policy audit or guaranteed deployment success.

The following deeper CLI policy inspection is **optional**, for investigating a
restriction or auditing recommendations. It is not a notebook execution gate.
Use PowerShell with an explicitly supplied subscription:

```powershell
$subscriptionId = '<confirmed-subscription-id>'
$scope = "/subscriptions/$subscriptionId"
az account show --subscription $subscriptionId --output table
az provider show --namespace Microsoft.Search --subscription $subscriptionId --query registrationState --output tsv
$env:AZURE_SUBSCRIPTION_ID = $subscriptionId
$env:AZURE_POLICY_SCOPE = $scope
az --% policy assignment list --subscription %AZURE_SUBSCRIPTION_ID% --scope %AZURE_POLICY_SCOPE% --filter "atScope()" --disable-scope-strict-match true --output json
az --% policy exemption list --subscription %AZURE_SUBSCRIPTION_ID% --scope %AZURE_POLICY_SCOPE% --filter "atScope()" --disable-scope-strict-match true --output json
```

For this optional audit, follow the [shared scoped-policy procedure](../../.github/skills/azure-demo-authoring/references/workflow.md#scoped-azure-policy-review).
The explicit filter includes inherited assignments: identify those actually applicable to
the intended group, resolve referenced initiatives and member definitions, apply
parameters, enforcement modes, overrides, exclusions, and exemptions. Review region,
SKU, authentication, and network restrictions; do not use a compliance-state summary
or an empty result as automatic approval.
For a complete audit, review the intended target-group scope as well. If it does not
yet exist, record that limitation and review applicable inherited restrictions;
validate actual target scope when the group exists.
For that query, set `$env:AZURE_POLICY_SCOPE` to the full group resource ID and
repeat the same filtered commands. `--disable-scope-strict-match` without
`atScope()` omitted management-group assignments during the initial inspection.

**Only after explicit execution approval**, an authorized operator can register the
provider if needed:

```powershell
az provider register --namespace Microsoft.Search --subscription $subscriptionId --wait
```

This changes subscription state and is not authorized by reading this guide.
Stop on Azure validation policy errors, registration failure, or missing permissions.

## 3. Compile and Review the Deployment

From the repository root, after the Bicep implementation exists:

```powershell
az bicep build --file .\demos\search02-hybrid-pagination\infra\main.bicep --outfile .\demos\search02-hybrid-pagination\outputs\generated\main.json
```

The generated-output directory must exist before running this command. Bicep build
performs its configured diagnostics. Inspect the compiled wrapper/module to verify:

- One new owned group and one Search service.
- Basic, one replica/partition, North Europe.
- Public access enabled, no IP allowlist, local authentication disabled.
- Exactly two deterministic user-targeted service-scoped role assignments.
- No index, Storage account, model, managed identity, private networking, or UI host.

Run the deployment notebook's SDK validation/what-if before applying changes.
Stop if a proposed group already exists without valid demo ownership.

## 4. Deploy and Verify the Handoff

Review the selected target and preview, then deliberately execute the paid-deployment
step in `01_deploy_infra.ipynb`. There are no prerequisite/deployment confirmation
flags; running that step submits the deployment. Do not use unattended Run All.
Expect the SDK
deployment to complete, not merely return a polling handle. Check that `env/.env`
was generated from outputs and matches the
[handoff contract](./contracts/environment-handoff.md). Do not populate it manually.

`02_configure.ipynb` is an explanatory Feature 2 handoff, not index creation.
Run the infrastructure-readiness steps in `03_test.ipynb`:

- Match actual resource settings and assignment targets to the plan.
- As the same setup user, call `SearchIndexClient.get_service_statistics()` using
  `AzureCliCredential` and the selected stable SDK's supported API.
- Verify `statistics.counters.index_counter.usage` and
  `statistics.counters.document_counter.usage` are zero on this initial fresh
  environment, using the SDK model rather than REST JSON field names.
- Record the readiness observation time and SDK/API versions.
- Record document execution and cross-client validation as deferred to Feature 2.

If role propagation is incomplete, report blocked and retain the underlying error.
Resolve/wait for that prerequisite and rerun the explicit check; do not enable keys
or add a silent alternative identity.

## 5. Prove Repeatability

Repeat the same approved deployment with unchanged inputs. Inspect the resulting
IDs and resource counts: one owned group, one service, the same two assignment
identities, and refreshed matching outputs. No additional service or assignments
may be created. Re-run metadata readiness before handing off to Feature 2.

## 6. Confirm and Execute Cleanup

Review the cost/ownership context and all resources in the exact group. The canonical
destroy notebook uses the current CLI subscription, so explicitly align it first:

```powershell
az account set --subscription $subscriptionId
az account show --query id --output tsv
az resource list --subscription $subscriptionId --resource-group '<demo-resource-group>' --output table
```

Only after explicit approval, review the confirmation flags and execute the standard
`X_destroy.ipynb` deletion steps. Do not use Run All without reviewing them.
Opening a notebook performs no deletion.
Verify absence using an explicitly scoped read-only check:

```powershell
az group exists --subscription $subscriptionId --name '<demo-resource-group>'
```

Expected: `false`. Confirm unrelated resources were not deletion targets.
The canonical notebook can report an already-missing group as an error on repeat;
record the actual absent state, not a new successful deletion. No local workaround
or destroy-source change belongs to this feature.

Record the verified lifecycle state `deleted` and its UTC observation time in
cleanup evidence and the final README. Earlier readiness evidence is historical,
not proof that an environment is still available; the exported `env/.env` is stale.
Before starting Feature 2, obtain execution approval and repeat deployment, output
export, and readiness validation to produce a fresh usable handoff. Do not
automatically redeploy after cleanup or leave paid resources running implicitly.

## Local Quality Gate

After implementation, run existing checks from repository root:

```powershell
pre-commit run --files demos\search02-hybrid-pagination\notebooks\00_setup.ipynb demos\search02-hybrid-pagination\notebooks\01_deploy_infra.ipynb demos\search02-hybrid-pagination\notebooks\02_configure.ipynb demos\search02-hybrid-pagination\notebooks\03_test.ipynb demos\search02-hybrid-pagination\notebooks\X_destroy.ipynb --show-diff-on-failure
```

The existing GitHub workflow still runs its all-files check on configured events.
Record static and live checks separately; none of these planned demo checks have
been run as part of the planning phase.
