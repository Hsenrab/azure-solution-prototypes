# Validation Guide: BYOM Resource Setup

These are acceptance instructions for the planned implementation, not evidence
that the demo already exists or has been deployed.

## Prerequisites

- Python >=3.10, VS Code/Jupyter, Azure CLI, and an updated Bicep compiler.
- An explicitly selected Azure subscription with resource creation/deletion and
  Foundry/APIM purge permissions. No role-assignment creation is planned.
- UK South service availability and standard-tier capacity, or another supported
  region selected before deployment. Respect inherited Azure Policy; do not
  bypass it with tags or automatic network changes.
- The user has approved live validation with APIM Standard, Search S1, and Foundry
  S0. No model inference is run in this slice. Cleanup after validation is required.

## Local Authoring Checks

Run from the repository root after implementation:

```powershell
az bicep build --file .\demos\byom01-capability-testing\infra\main.bicep --stdout
```

Run notebook cleanup separately:

```powershell
pre-commit run --files demos\byom01-capability-testing\notebooks\00_setup.ipynb demos\byom01-capability-testing\notebooks\01_deploy_infra.ipynb demos\byom01-capability-testing\notebooks\X_destroy.ipynb --show-diff-on-failure
```

Also parse each notebook's Python code without executing Azure operations.
Confirm setup order and that destroy matches the speech source verbatim.
Require no execution outputs/counts or kernelspec display-name metadata in
committed notebooks. These checks do not prove live provisioning succeeds.

## Live Acceptance (Authorized; Cleanup Required)

Proceed with the agreed resources and SKUs without another cost/deployment
authorization request. Track resources created for this validation and clean them
up afterward, including after a failed or partial deployment. Never delete
unrelated or pre-existing resources. Preserve tool approval requirements.
Verify cleanup and explicitly report anything remaining.

1. Run **Step 1** in setup, select the demo kernel, then run **Step 2** and
   **Step 3**. Confirm the intended subscription explicitly.
2. Open deployment, review configuration and costs, then run its steps.
   Await the actual deployment result.
3. Verify the resource group contains APIM Standard (one unit), Foundry S0 with
   one child project, and search Standard (one replica/partition), with public
   authenticated endpoints.
4. Verify every field in [the environment contract](./data-model.md) is populated
   automatically, and no secrets or integration/test settings were generated.
5. Repeat deployment with unchanged inputs. Confirm the same resources are
   updated without duplicates.
6. Before cleanup, select the exact subscription recorded in the environment.
   Ensure the destroy kernel loads the intended resource group and Foundry
   endpoint. For partial deployment without a generated environment, follow the
   README's explicit targeting instructions before running destructive steps.
7. Run the standard destroy notebook, review its target/resources and confirmation
   flags, and complete deletion, Foundry purge, and resource-group removal.
8. Purge only this demo's APIM service using the saved values:

```powershell
az apim deletedservice purge --subscription "<saved-subscription-id>" --location "<saved-location>" --service-name "<saved-apim-name>"
```

Run the purge as its own command. Confirm that the resource group and the demo's
Foundry/APIM soft-deleted records no longer exist. Do not treat the standard
notebook's Cognitive Services-only verification as proof of APIM purging.

## Evidence to Report

Report local checks separately from live outcomes. If live checks have not been
executed or prerequisites block them, mark the corresponding SC-001 through
SC-004 outcomes as not run;
do not claim successful provisioning, idempotency, or cleanup.
