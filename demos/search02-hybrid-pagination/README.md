# Search hybrid pagination - shared debugging environment

## Problem statement

A customer reports that searching for "maths" advertises 6,158 matches and 1,232
five-result pages, while only the first 257 pages return results. The bounded hybrid
candidate set is a hypothesis, not a confirmed explanation.

## Hypothesis

One repeatable, keyless Search environment can provide the same authorized foundation
for later Python and .NET experiments. **Feature 1 prepares infrastructure only; it
does not reproduce the discrepancy.**

## Scope

- In scope: one dedicated demo-owned resource group, one paid Basic Search service,
  one replica/partition in North Europe, public access without an IP allowlist,
  disabled key authentication, two service-scoped assignments to the setup user,
  automatic non-secret output export, read-only metadata readiness, and confirmed cleanup.
- Out of scope: indexes, synthetic-data ingestion, queries, reproduction clients,
  embedding/model services, UI hosting, private endpoints/VPN/DNS, distance sorting,
  beta-SDK comparisons, production approval, and GA timelines.

## Prerequisites and approval

- Python **3.11+**, VS Code/Jupyter, Azure CLI, and Bicep.
- Run notebooks with their working directory set to `notebooks/`.
- The setup user needs subscription deployment/resource-group/Search write access
  and permission to create the required service-scoped role assignments. Contributor
  alone does not grant role-assignment write permission.
- Explicitly select the subscription with `az account set --subscription <id>`.
  When `AZURE_SUBSCRIPTION_ID` is supplied in the kernel environment, deployment
  and readiness automatically run `az account set` if needed, reread the selected
  account, and validate context before continuing. This changes the CLI default
  for other terminals/notebooks too. Without that variable they use the current
  CLI selection; they never choose the first enabled subscription or sign in as
  another identity. The generated `env/.env` is an output, not an automatically
  loaded deployment input; editing it does not refresh the kernel environment.
- Run the notebook's Azure deployment validation and what-if for the selected
  template and subscription before deployment. They check applicable enforced
  deployment policies, not a full audit of advisory policies. Resolve raw policy
  or permission errors; do not bypass them or change networking/authentication
  automatically. No manually maintained policy-review file is required.
- Review actual pricing/capacity before paid execution. Planning found an indicative
  Basic meter of USD 0.101/hour, **not a guaranteed regional quote**.
  Billing continues while the service exists, including idle time. No automatic
  deletion, alternate tier, or alternate region is provided.

Provider registration is a separate subscription mutation. **Only after explicit
registration approval**, if needed:

```powershell
az provider register --namespace Microsoft.Search --subscription '<confirmed-id>' --wait
```

The deployment notebook writes `outputs/generated/what-if.json` from the actual
SDK preview. Export and readiness use actual deployment outputs and live resource
checks; neither reads `policy-review.json`. Earlier manually generated policy
snapshots may be kept as historical evidence, but do not gate another subscription.
For an optional in-depth policy audit, follow the
[scoped CLI review guide](../../specs/001-provision-search-debug/quickstart.md#2-review-azure-policy-and-provider-state).

## Notebook journey

The demo is driven by numbered notebooks in `notebooks/`. Run them in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, log in to Azure, install Python packages |
| `01_deploy_infra.ipynb` | Compile Bicep locally, validate/preview through the Python SDK, explicitly deploy and export all nine non-secret values |
| `02_configure.ipynb` | Explanatory Feature 2 handoff only; no executable configuration |
| `03_test.ipynb` | Verify live settings/assignments and zero-index/document statistics through the stable Python SDK |
| `X_destroy.ipynb` | Unmodified canonical cleanup; review context and confirm before executing |

## Folder map

```text
infra/      # infrastructure as code (Bicep)
notebooks/  # numbered step-by-step notebooks (primary interface)
env/        # .env.example documents expected vars; .env is written by notebook
app/        # app or script code (if needed beyond notebooks)
data/       # sample/mock data
docs/       # architecture notes and assumptions
outputs/    # screenshots and sample outputs
```

## Quick start

1. Open [setup](notebooks/00_setup.ipynb): create/register the environment and kernel,
   authenticate/select the subscription, then install requirements in that order.
2. Open [deployment](notebooks/01_deploy_infra.ipynb). Review the printed user/scope,
   complete the current prerequisites, compile, and inspect SDK validation/what-if.
   There are no prerequisite/deployment confirmation flags. Running **Explicitly
   deploy the paid environment** submits the paid deployment after a successful
   what-if. Review the target and preview before running it; avoid unattended
   Run All. Resource creation is defined in Bicep, not Python.
3. Successful deployment exports [the nine-key contract](env/.env.example) to
   `env/.env` in one UTF-8 write. Never populate that file manually.
4. Read [the handoff](notebooks/02_configure.ipynb), then run
   [readiness](notebooks/03_test.ipynb). Effective index/upload/query execution in
   both languages remains deferred to Feature 2.
5. Repeat the approved deployment with unchanged inputs. Preserve first/second
   deployment and readiness evidence and verify identical group/service/assignment
   IDs, one service, and no duplicate assignments.

## Local validation

From the repository root, using the demo environment created during setup:

```powershell
az bicep build --file .\demos\search02-hybrid-pagination\infra\main.bicep --outfile .\demos\search02-hybrid-pagination\outputs\generated\main.json
& .\demos\search02-hybrid-pagination\.venv\Scripts\python.exe .\demos\search02-hybrid-pagination\scripts\validate_local.py
& .\demo-template\.venv\Scripts\python.exe -m pre_commit run --files demos\search02-hybrid-pagination\notebooks\00_setup.ipynb demos\search02-hybrid-pagination\notebooks\01_deploy_infra.ipynb demos\search02-hybrid-pagination\notebooks\02_configure.ipynb demos\search02-hybrid-pagination\notebooks\03_test.ipynb demos\search02-hybrid-pagination\notebooks\X_destroy.ipynb --show-diff-on-failure
```

The last command uses this checkout's existing pre-commit environment; use your
installed `pre-commit` command if you installed it through the contributor setup.
No new test framework is needed. Validation includes compiled resource properties,
real SDK model parsing with synthetic responses, negative handoff cases, and
canonical notebook comparisons. Synthetic local results are **not live evidence**.

## Cleanup

This group is exclusively demo-owned. Whole-group deletion is the approved boundary,
but requires separate deletion confirmation. Do not use unattended Run All: the
canonical notebook's confirmation flags are already **True**.

1. Review the exact subscription and group, even after a partial deployment:

   ```powershell
   az account set --subscription '<confirmed-id>'
   az account show --query id --output tsv
   az resource list --subscription '<confirmed-id>' --resource-group rg-search02-hybrid-pagination-ne --output table
   ```

2. Open [canonical cleanup](notebooks/X_destroy.ipynb). Loading `.env` does not
   change its active CLI subscription. Its group fallback comes from the literal
   `RESOURCE_GROUP` in the deployment notebook if output export never completed.
3. After approval, run **Load environment**, **Review resources**, and
   **Delete resources** deliberately. Search creates no Cognitive Services accounts:
   skip the **optional soft-delete purge** step, then run **Delete resource group**.
   The final Cognitive Services verification is subscription-wide informational
   output, not Search group-absence acceptance.
   In the validated CLI environment, the canonical individual-resource command
   rejects `--yes`. Its printed "All resources deleted" message is not proof of
   success after that warning. The canonical **Delete resource group** step
   successfully removes this Search-only environment; verify actual absence below.
   The canonical source remains unchanged, with the command issue recorded as a
   shared cleanup limitation rather than a demo-local workaround.
4. Independently verify the exact group is absent:

   ```powershell
   az group exists --subscription '<confirmed-id>' --name rg-search02-hybrid-pagination-ne
   ```

   Expected: `false`. Preserve actual cleanup evidence with `lifecycleState: "deleted"`
   and UTC `observedAt` in `outputs/generated/us3-cleanup.json`. Record any error or
   partial state honestly. A repeated cleanup may raise the source notebook's raw
   already-absent error; it is not a new successful deletion.

After verified deletion, earlier readiness is **historical**, `env/.env` is
**stale**, and no live Feature 2 handoff exists. Before Feature 2, obtain execution
approval and rerun deployment, export, and readiness. Never automatically redeploy
or implicitly keep paid resources running.

## Validation status

Local validation and live acceptance are tracked separately in
[the feature tasks](../../specs/001-provision-search-debug/tasks.md).
Acceptance completed on **2026-10-23**, with explicit deployment, provider-registration,
and cleanup approval:

| Check | Observed result |
|---|---|
| Local validation | Bicep compilation and 19 checks passed; existing notebook hygiene passed |
| Scoped policy review | 10 inherited assignments, seven initiatives/330 member references, 321 distinct definitions, no visible exemptions; actual group matched the reviewed scope |
| Deployment | One Basic service, one replica/partition, North Europe; public endpoint, disabled keys, no IP allowlist |
| Unchanged-input redeployment | Same group/service/two direct assignment IDs and all nine outputs; zero additional services or duplicate assignments |
| Metadata readiness | Same CLI user; stable Python Search SDK 12.0.0, API 2025-09-01; zero indexes and documents |
| Cleanup | Canonical whole-group deletion succeeded; two explicitly scoped absence checks returned `false`; no outside-group deletion targets |

**Latest lifecycle: `deleted`.** Earlier readiness is historical and `env/.env`
is stale, not a live Feature 2 handoff. No demo Search service remains to accrue
ongoing charges. Charges for the short validation run may still appear; the
indicative public USD 0.101/hour meter is not a subscription bill or cost guarantee.
`Microsoft.Search` was explicitly registered and remains registered; registration
is not a running billable Search service.

Local-only evidence is under ignored `outputs/generated/`: `us1-deployment.json`,
`us1-redeployment.json`, `readiness.json`, `us3-cleanup.json`, policy snapshots,
and static-check results. No credentials or service keys were exported. Feature 2
is **not implemented**, and the customer discrepancy is **not reproduced**.

## Known limitations

- Basic/one unit is a disposable experiment, not a high-availability design.
- Current registration, permissions, regional capacity, policy compatibility, price,
  and RBAC propagation must be rechecked for a future run; this acceptance is a
  timestamped observation, not a permanent guarantee.
- An existing unrelated or unowned group is rejected; only this demo's known-owned
  group may be reused. ARM deployment does not itself enforce this ownership gate:
  use the notebook journey, not a direct bypass of its predeployment review.
- Metadata readiness does not prove document access in either language or reproduce
  the count discrepancy. Do not clear Feature 2 data to force the zero-index baseline.
- [Architecture and cleanup constraints](docs/architecture-notes.md).
- [Reusable authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md).
