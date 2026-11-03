# Search hybrid pagination - two-client debugging experiment

## Problem statement

A customer reports that searching for "maths" advertises 6,158 matches and 1,232
five-result pages, while only the first 257 pages return results. The bounded hybrid
candidate set is a hypothesis, not a confirmed explanation.

## Hypothesis

A hybrid count can describe more matching documents than the distinct candidates
available for paging. Measure this with independent Python and .NET clients over
one immutable synthetic corpus; do not assume the customer's boundary or an SDK defect.

## Scope

- In scope: one dedicated demo-owned resource group, one paid Basic Search service,
  one replica/partition in North Europe, public access without an IP allowlist,
  disabled key authentication, two service-scoped assignments to the setup user,
  automatic non-secret output export, initial metadata readiness, 6,158 deterministic
  synthetic records, one vector-enabled index, independent keyword/vector/hybrid
  measurements, durable evidence, local comparison, configured Python preview cases,
  a separately prepared mixed-fixture index, and canonical cleanup.
- Out of scope: embedding/model services, UI hosting, private endpoints/VPN/DNS, distance sorting,
  isolated SDK-only attribution, production approval, and GA timelines.

## Prerequisites and approval

- Python **3.11+**, VS Code/Jupyter, Azure CLI, Bicep, and a **.NET 10 SDK**.
  `dotnet --list-sdks` must list a `10.*` SDK; an installed runtime alone is insufficient.
  Setup retains Python Search **12.0.0** and Identity **1.25.3**; .NET uses Search
  **12.0.0** and Identity **1.21.0**, `net10.0`, and a committed NuGet lock file.
  Both explicitly select service API **2025-09-01**, not SDK defaults.
  Implementation preflight verified Python 3.12.10 and installed the approved
  .NET SDK 10.0.403. These are local observations, not the minimum Python requirement.
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
| `02_configure.ipynb` | Explain initial readiness and reproduction ordering; no executable configuration |
| `03_test.ipynb` | Initial-only live settings/assignments and zero-index/document statistics |
| `04_reproduce.ipynb` | Generate/prepare the shared fixture, run six independent cases, compare saved evidence |
| `05_compare_preview.ipynb` | Reuse the stable evidence and compare two configured Python preview scenarios without writes |
| `06_vector_contributions.ipynb` | Preserve the original experiment and measure genuine non-keyword vector contributions on a separate mixed index |
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
   [readiness](notebooks/03_test.ipynb) **before ingestion**. Its empty-service
   assertion is intentionally not a post-ingestion check. Never delete data to satisfy it.
5. Open [reproduction](notebooks/04_reproduce.ipynb): check both toolchains and
   current setup-user context; generate the fixture; prepare the index; confirm
   exactly 6,158 indexed records. If indexing visibility has not settled, wait and
   rerun **Confirm the corpus is indexed**, not the upload.
6. Run the three Python and three .NET cases, then **Compare observations and
   explain the finding**. Expect several thousand sequential reads. Do not write
   documents or alter the index during any scans/replays. Keep the fixture/index
   unchanged and create a new run directory for another full experiment.

## Mixed-fixture vector contributions

Open [the mixed-fixture notebook](notebooks/06_vector_contributions.ipynb) with the
existing demo kernel. Implementation, offline checks, and the separately approved
eight-case live run are complete. **Full acceptance remains blocked by failed
keyword controls**, not missing cases.
The existing service remains billable; no additional service or deployment is introduced.

The version-2 fixture has 6,183 deterministic documents: 6,133 keyword-only,
25 full-keyword/vector shared, and 25 vector-only members for `maths` and `k=50`.
Exactly 6,158 still match the keyword. Engineered vectors select the shared and
vector-only groups; they do not demonstrate embedding quality or semantic understanding.
The original fixture/index/evidence and original notebook journeys remain unchanged.

### Measured mixed-fixture outcome

The approved run `20261102T233019Z-bee9da5d` ran on 2026-11-02/03 UTC.
See the retained [contribution report](outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/contribution-comparison.md)
and [acceptance findings](outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/acceptance.json).

| Case | Reported | Unique reachable | Populated / empty advertised pages |
|---|---:|---:|---|
| Stable Python and .NET keyword controls | 6,158 | 6,094 | 1,232 / 0 |
| Stable Python and .NET vector controls | 50 | 50 | 10 / 0 |
| Stable Python and .NET hybrid | 6,183 | 1,046 | 210 / 1,027 |
| Preview recall 1,000 | 1,046 | 1,046 | 210 / 0 |
| Preview recall 6,158 | 6,183 | 6,183 | 1,237 / 0 |

Both vector controls returned exactly the intended 25 shared and 25 vector-only IDs.
All four hybrid cases returned all 25 **declared** vector-only IDs, with real-ID
fixture-text examples. However, each keyword control had 64 duplicate excess rows
and 64 missing expected IDs. Verified non-keyword additions remain unestablished
under the agreed complete-control rule; the renderer correctly exits nonzero and
keeps overall acceptance blocked.

The expanded preview met its exact coverage/count target, including three final
rows, zero duplicates/empty advertised pages, and no positive following-page probe.
Both preview counts aligned with their unique reachable IDs. This is measured
configuration behavior, not an isolated SDK fix or production approval.
All 54 protected original files were byte-unchanged after the live run; original-index identity,
schema, and count matched before/after. Hidden vectors and snapshot isolation
were not remotely proved. The mixed index is now populated: **skip one-time
preparation** and use read-only reuse with a fresh run directory for another scan.

Publishing cleanup on 2026-11-03 was separately approved: a local backup of the
original reproduction notebook was retained outside the repository, then the
standard hook removed its saved outputs, execution counts, and kernel display-name
metadata. Notebook code/markdown and all separate measurement files are unchanged.
All 40 local validator checks now pass; the live keyword-control blocker remains.

Follow the [mixed experiment commands and acceptance guide](../../specs/003-vector-only-contribution/quickstart.md):

1. Generate the separate fixture locally and build the existing independent .NET reader.
2. Obtain approval before the notebook's one-time preparation heading. Only an
   absent/empty correctly defined `hybrid-pagination-mixed-v2` may be populated;
   a populated target is refused before upload/schema updates. The original
   `hybrid-pagination-debug` is never a mixed write target.
3. Use **Read-only reuse and fresh run** for subsequent measurements. A matching
   receipt, every successful upload result, exact count, schema, and complete
   ID/content inventory gate both clients. Indexing delay can finalize an
   all-successful upload read-only; partial uploads cannot become ready.
4. Collect six stable cases and two `[PREVIEW]` cases sequentially, keeping the index
   unchanged. Expect roughly 6,400 primary reads plus inventory/boundaries.
   Preview recall remains 1,000/6,158, not the indexed total 6,183.
5. Deliberately run **Local contribution review**, including after a failed case.
   Its local-only JSON/Markdown report preserves gaps and exits nonzero unless
   all eight compatible cases, both clients' controls, all 25 vector-only
   contributions, and expanded coverage/count requirements pass.

Declared groups and observed membership are separate. Shared full-keyword matches
are not necessarily in the smaller internal text window; its membership is
`not-observed` with null IDs. Text examples use actual hybrid-returned IDs and
verified local fixture text, not additional fields in the ID-only measured response.
Count alignment requires complete evidence, equal reported/unique counts, no
duplicates or empty advertised pages, and no positive following-page probes.

The upstream change is in shared version-aware fixture/measurement/inspection helpers
and equivalent independent .NET validation: indexed membership is no longer conflated
with keyword membership. No Bicep/authentication change, temporary workaround, or
catch-and-explain-only fix is needed. The original failed keyword control remains
unresolved; this follow-on cannot waive it. Existing canonical cleanup remains the
only cleanup journey and requires separate approval.

## Independent commands and evidence

From the demo root, after notebook preparation:

```powershell
dotnet restore .\app\dotnet\HybridPagination.csproj --locked-mode
dotnet build .\app\dotnet\HybridPagination.csproj --no-restore
.\.venv\Scripts\python.exe -m app.reproduce --case keyword --manifest outputs\generated\reproduction\fixture\manifest.json --env-file env\.env --run-dir outputs\generated\reproduction\runs\<new-run-id>
dotnet run --no-build --project app\dotnet\HybridPagination.csproj -- --case keyword --manifest outputs\generated\reproduction\fixture\manifest.json --env-file env\.env --run-dir outputs\generated\reproduction\runs\<new-run-id>
.\.venv\Scripts\python.exe -m app.compare --run-dir outputs\generated\reproduction\runs\<new-run-id>
```

Run each language command separately for `keyword`, `vector`, and `hybrid` with
the **same** run directory. The clients refuse same-case overwrites. Six reports,
six append-only `.pages.jsonl` files, actual schema evidence, `comparison.json`,
and `comparison.md` stay under ignored `outputs/generated/reproduction/runs/`.
No credentials are included; do not commit generated outputs or the environment.

Every advertised offset is read, even after an empty response. Counts/IDs/rows
are recomputed without probes/repeats inflating totals. Selected boundaries have
exactly two observations. Failed requests have null IDs/rows, never empty results.
A short response with continuation stops the case as incomplete. A vector-only
case without an initial count scans all ten candidate pages plus boundaries:
count/advertised metrics remain null and successful completion is `not-applicable`.
Keyword/hybrid require an initial count. Reproduction requires **both** a positive
count-minus-unique gap and an empty advertised page. A valid `not-reproduced`
outcome is equally acceptable. Baseline failure, request mismatch, count drift,
and unfinished measurements block causal attribution.

See the [acceptance guide](../../specs/002-reproduce-hybrid-pagination/quickstart.md)
and [evidence contract](../../specs/002-reproduce-hybrid-pagination/contracts/experiment.md).

## Optional Python preview comparison [PREVIEW]

Open [05_compare_preview.ipynb](notebooks/05_compare_preview.ipynb) using the
**original** demo Python kernel. The second notebook creates an isolated
`.venv-preview` from [requirements-preview.txt](requirements-preview.txt), pinned
to Python Search **12.1.0b2**, Identity **1.25.3**, and python-dotenv **1.2.2**.
It invokes that interpreter as a subprocess; no new kernel or .NET project is
needed. Stable dependencies, the original reproduction notebook, original
evidence, and infrastructure remain unchanged.

The user-selected shorter comparison has three scenarios:

| Scenario | SDK / API | Hybrid settings |
|---|---|---|
| Existing stable evidence | Python 12.0.0 / 2025-09-01 | Original defaults |
| Retrievable count | Python 12.1.0b2 / 2026-08-01-preview | `countRetrievableResults`, text recall 1,000 |
| Expanded recall | Same preview SDK/API | `countRetrievableResults`, text recall 6,158 |

This tests the service capabilities through Python, **not** the exact .NET
`Azure.Search.Documents 12.1.0-beta.2` package. Baseline versus preview changes
SDK/API/settings together and cannot isolate a package-only fix. The two preview
cases isolate recall size from each other. Larger recall can cost more service
work and latency; it does not guarantee complete unique-ID coverage.

Use the existing immutable fixture/index, generated environment, and completed
stable Python hybrid baseline. The notebook never deploys, populates, or deletes
anything. If the service is absent, stop rather than redeploy automatically.
Keep the index unchanged during both scans. Existing keyword-baseline failures
remain visible; preview behavior does not retrospectively validate that control.

For standalone runs from the demo root after installing the isolated requirements:

```powershell
.\.venv-preview\Scripts\python.exe -m app.preview run --scenario retrievable --baseline outputs\generated\reproduction\runs\20261030-live-v2\python-hybrid.json --manifest outputs\generated\reproduction\fixture\manifest.json --env-file env\.env --run-dir outputs\generated\reproduction\preview-runs\<new-run-id>
.\.venv-preview\Scripts\python.exe -m app.preview run --scenario expanded --baseline outputs\generated\reproduction\runs\20261030-live-v2\python-hybrid.json --manifest outputs\generated\reproduction\fixture\manifest.json --env-file env\.env --run-dir outputs\generated\reproduction\preview-runs\<new-run-id>
.\.venv\Scripts\python.exe -m app.preview compare --baseline outputs\generated\reproduction\runs\20261030-live-v2\python-hybrid.json --run-dir outputs\generated\reproduction\preview-runs\<new-run-id>
```

Each preview case preserves full advertised scans, actual requests/API/counts/IDs,
one-send checks, failure/continuation rules, and exactly two observations per
selected boundary through the shared measurement engine. The original CLI keeps
its stable defaults. Local comparison writes `preview-comparison.json` and
`preview-comparison.md` with explicit gaps and differences. It rejects an
accurate-count claim if a boundary probe finds results beyond the advertised range.
Case files cannot be overwritten; a new comparison uses a new directory.

Preview features do not imply production approval or a GA date. References:
[Python preview package](https://pypi.org/project/azure-search-documents/12.1.0b2/)
and [HybridSearch controls](https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.models.hybridsearch?view=azure-python-preview).

### Observed preview comparison

The read-only `20261030-preview-v1` run measured:

| Scenario | Reported count | Unique IDs | Populated / empty advertised pages |
|---|---:|---:|---|
| Original stable hybrid | 6,158 | 1,039 | 208 / 1,024 |
| Preview, recall 1,000 | 1,039 | 1,039 | 208 / 0 |
| Preview, recall 6,158 | 6,158 | 6,158 | 1,232 / 0 |

Both preview scans had zero duplicate IDs and no results in the following-page
boundary probes. Expanded recall reached every expected fixture ID, adding 5,119
IDs versus stable. The smaller preview window shared 1,033 IDs with stable and
returned six different IDs; equal-sized windows do not prove identical membership
across historical requests. Both scans began/ended with 6,158 indexed documents;
that is not snapshot isolation.

The generated [preview comparison](outputs/generated/reproduction/preview-runs/20261030-preview-v1/preview-comparison.md)
retains actual SDK/API/settings, requests, boundaries, and these limitations.
All original evidence remained byte-unchanged. This demonstrates the configured
preview behavior for this fixture, not an isolated SDK fix or production approval.
Original causal acceptance remains blocked by the keyword complete-ID control.

## Local validation

From the repository root, using the demo environment created during setup:

```powershell
az bicep build --file .\demos\search02-hybrid-pagination\infra\main.bicep --outfile .\demos\search02-hybrid-pagination\outputs\generated\main.json
& .\demos\search02-hybrid-pagination\.venv\Scripts\python.exe .\demos\search02-hybrid-pagination\scripts\validate_local.py
dotnet build .\demos\search02-hybrid-pagination\app\dotnet\HybridPagination.csproj
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

**Feature 1 historical lifecycle: `deleted`.** The service was subsequently
recreated with explicit approval on 2026-10-30 for Feature 2 measurements using
the unchanged Bicep. It is now running and billing continues until separately
approved cleanup. The historical table above is not a current empty-index claim.
Charges for validation runs may appear; the
indicative public USD 0.101/hour meter is not a subscription bill or cost guarantee.
`Microsoft.Search` was explicitly registered and remains registered; registration
is not a running billable Search service.

Local-only evidence is under ignored `outputs/generated/`: `us1-deployment.json`,
`us1-redeployment.json`, `readiness.json`, `us3-cleanup.json`, policy snapshots,
and static-check results. No credentials or service keys were exported.
Feature 2 implementation and actual measurement acceptance are tracked separately
in [its task list](../../specs/002-reproduce-hybrid-pagination/tasks.md).
Customer-request parity and the exact customer boundary remain unverified.

### Feature 2 live observations - 2026-10-30

All six independent cases completed their required requests in local run
`outputs/generated/reproduction/runs/20261030-live-v2/`. Comparison recomputed
every scan and deduplicated boundary from the JSONL evidence. Both clients used
the same corpus/schema, API 2025-09-01, and equivalent captured requests; all
three pairwise ID sets agreed. Every advertised offset was measured, and each
selected boundary has exactly two observations.

| Case (same result in Python and .NET) | Reported | Returned rows | Unique IDs | Populated / empty advertised pages | Outcome |
|---|---:|---:|---:|---|---|
| Keyword | 6,158 | 6,158 | 6,111 | 1,232 / 0 | Blocked baseline: duplicate/missing IDs |
| Vector | 50 | 50 | 50 | 10 / 0 | Not reproduced |
| Hybrid | 6,158 | 1,039 | 1,039 | 208 / 1,024 | Symptom reproduced |

Hybrid's first empty page was **209**, not the customer-reported 257-page
boundary. Its last populated page contained four rows. The keyword scans had
47 excess duplicate occurrences and failed the required complete-ID baseline,
despite visiting every advertised offset. **Overall acceptance remains
blocked/incomplete**: these observations reproduce the symptom, but do not
establish its cause or prove a customer SDK defect. Do not silently add sorting
or tune the fixture to manufacture a passing control; changing that experiment
requires an explicit follow-up design decision.

Local validation passed: 18 existing infrastructure/handoff/canonical checks,
Python/Pylance syntax, locked NuGet restore, .NET build (zero warnings/errors),
and configured notebook cleanup. Focused offline checks in both languages also
verified missing vector counts and short/empty continuation handling; neither
condition was invented as a live observation. Live vector counts were available.

An initial run (`20261030-live-v1`) remains incomplete after a missing local CA
bundle interrupted it. The same installed certifi/pip packages were restored
using an intact package manager with normal TLS verification; no TLS bypass or
notebook fallback was added. The fresh run above retained all six evidence files.

.NET Identity package metadata initially reported Azure.Core's 1.54.0 because
`AzureCliCredential` is type-forwarded to that assembly. The shared .NET metadata
producer now loads `Azure.Identity` explicitly and reports the verified package
1.21.0. The three reports retain an audited metadata correction with DLL-hash
proof; page evidence, requests, results, and measurement timestamps were not
rewritten, and no replacement searches were needed.

The implementation is a shared data-plane experiment, not a platform workaround:
Bicep/authentication/network settings and canonical setup/destroy are unchanged.
Narrow SDK/transport failure recording preserves and rethrows original failures;
no catch-and-explain notebook wrapper was added. The service remains billable
until separately approved cleanup.

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
