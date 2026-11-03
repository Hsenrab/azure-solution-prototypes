# Quickstart: Validate the Two-Client Reproduction

The notebook and independent runners are implemented. Use this guide to validate
actual evidence; the customer's exact request and 257-page boundary remain unverified.

## Current validation outcome

On 2026-10-30, all six cases ran against the explicitly approved, recreated
service with unchanged Bicep. Evidence is local/ignored under
`demos/search02-hybrid-pagination/outputs/generated/reproduction/runs/20261030-live-v2/`.
Both clients reproduced the hybrid symptom: count 6,158, 1,039 unique reachable
IDs, 208 populated pages, first empty page 209, and 1,024 empty advertised pages.
Both vector cases reached 50 of 50. Both keyword cases returned 6,158 rows across
all 1,232 pages but only 6,111 unique IDs; therefore overall comparison remains
`blocked/incomplete` and the comparison CLI correctly exits nonzero. All six
reports exist; this is a failed baseline, not a missing-client placeholder.

Actual request/API parity, full scan coverage, exactly two observations per
selected boundary, and equal cross-client ID sets were independently checked.
The missing-count vector and short/empty continuation policies passed focused
offline checks in both languages; the live vector counts were present. Existing
18 local checks, Python/Pylance syntax, locked restore, zero-warning/error .NET
build, and notebook hygiene passed. No new test framework was added.

An audited Identity-version metadata correction (forwarded credential type versus
actual Identity assembly) left page evidence, query results, and timestamps
unchanged. The earlier interrupted `20261030-live-v1` remains incomplete, not
substituted into the final comparison. See the
[full record](../../demos/search02-hybrid-pagination/README.md#feature-2-live-observations---2026-10-30).

Do not silently relax the baseline or add sorting to force a pass; a follow-up
experiment change requires approval. The service remains running and billable
until separately authorized cleanup.

## Prerequisites

- Complete [Feature 1](../../demos/search02-hybrid-pagination/README.md) with a
  currently available Search service and generated deployment environment.
  Historical readiness/cleanup evidence is not proof the service exists now.
- Use the same authorized setup user, subscription, and tenant as that deployment.
  Retain keyless authentication and the existing roles/network configuration.
- Select `Python (search02-hybrid-pagination)` in VS Code; use the existing
  requirements installation from setup.
- Install a .NET 10 SDK if `dotnet --list-sdks` lists none. A runtime or `dotnet`
  executable alone is insufficient. Verify the SDK before starting the experiment.
- Keep the prepared index unchanged throughout both clients' scans. Budget several
  thousand sequential read requests; no embedding service is needed.

From the repository root, enter the demo directory:

```powershell
Set-Location .\demos\search02-hybrid-pagination
dotnet --list-sdks
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; print(version('azure-search-documents'))"
```

Expected Search Python version: `12.0.0`. Restore/build the .NET project and verify
pinned Search 12.0.0 / Identity 1.21.0:

```powershell
dotnet restore .\app\dotnet\HybridPagination.csproj --locked-mode
dotnet build .\app\dotnet\HybridPagination.csproj --no-restore
```

## Notebook journey

1. Follow existing setup and deployment only if a current environment is needed.
   This guide does not authorize an automatic deployment or subscription change.
2. Run the existing **infrastructure readiness** notebook before populating data.
   Its empty-service assertions are intentionally initial-only.
3. Open [04_reproduce](../../demos/search02-hybrid-pagination/notebooks/04_reproduce.ipynb)
   and run its small purpose-named steps:
   - **Load experiment prerequisites**: generated environment, same-user context,
     SDK/API versions, and .NET SDK availability.
   - **Generate the fixed synthetic fixture**: exactly 6,158 records, stable IDs,
     documented text, fixed vectors, and corpus hash.
   - **Prepare the shared Search index**: Python SDK schema and batched upload;
     every upload result must succeed.
   - **Confirm the corpus is indexed**: exactly 6,158 documents before scans.
     Incomplete visibility blocks the run; rerun this check after indexing settles.
   - **Run the Python keyword control**, **Run the Python vector control**,
     **Run the Python hybrid case**.
   - **Run the .NET keyword control**, **Run the .NET vector control**,
     **Run the .NET hybrid case**, directly through the independent .NET SDK.
   - **Compare observations and explain the finding**.

The notebook generates paths/run identity and displays concise metrics, not all
page bodies. It must surface failed subprocess output and leave failed page
evidence available. For independent runner commands, use the
[local interface contract](./contracts/experiment.md).

Do not rerun preparation while measuring. For a second full experiment reuse the
unchanged fixture/index with a new run directory; do not overwrite prior evidence.

## Required acceptance observations

1. **Fixture/readiness**: Hash, schema, dimensions, unique IDs, upload results, and
   indexed count agree. Neither client uses a model or private customer data.
2. **Keyword control in both clients**: Reach exactly the expected 6,158 IDs with
   no duplicates, 1,232 advertised/populated pages, and three rows on the final
   advertised page. Otherwise report a failed baseline before assigning a hybrid
   candidate-window cause.
3. **Full scans**: Every advertised offset is recorded at page size five, including
   empty pages after the first empty. Count drift, failed requests, or unexpected
   hidden continuation are incomplete results, not symptom evidence.
   For any scan, probe, or repeat with fewer than five rows AND continuation
   information, require `incomplete` / `service-continuation`, preserve the raw
   response, and do not classify it as exhausted/empty-page reproduction evidence.
   A partial final page without continuation remains valid.
4. **Vector control**: Actual IDs/count and keyword/hybrid overlap are measured.
   If the initial count is absent, measure all 10 candidate pages (`k=50`, size
   five) plus required boundaries with `scanBasis=vector-k`. A successful control
   has `status=complete`, `outcome=not-applicable`; reported count, advertised
   pages/coverage, and count gap stay null, never replaced by `k`. Show candidate
   metrics separately; failures/unfinished measurements still block completion.
5. **Boundaries**: Last populated, following, final advertised, and first empty
   offsets where applicable have two observations total. Additional probes and
   repeats must not inflate primary reachability metrics.
   For `vector-k`, use the final candidate scan page and first empty candidate
   page instead of advertised boundaries; retain the following-page probe.
6. **Classification**: Reproduced requires reported count greater than unique
   reachable IDs AND an empty advertised page. A valid not-reproduced outcome is
   equally acceptable. Failed/incomplete evidence is neither.
   Keyword/hybrid classification requires an initial count; `not-applicable` is
   restricted to successful vector controls without that count.
7. **Parity**: Six actual case reports plus comparison, same corpus/index/vector,
   aligned API/requests, explicit differences in counts/IDs/boundaries. Different
   observations are allowed; silently unmatched requests are not.
   Missing optional vector counts alone do not fail acceptance. Disclose any
   count comparisons unavailable and different scan bases rather than asserting
   equality or advertised coverage for a candidate-based scan.
8. **Explanation**: Separate facts, source-backed hypothesis, and limitations.
   Never label customer-reported 257 pages as measured here without evidence.

The [data model](./data-model.md) and [contract](./contracts/experiment.md) define
the evidence fields and completion rules. Review `comparison.md` together with
the six reports and their page-observation files; the summary alone must not
stand in for missing measurements.

## Local checks and cleanup

Run Python syntax checks, the focused existing local
validator where applicable, .NET build, and the existing notebook hygiene checks.
Do not add a test framework. These checks complement, not replace, live acceptance.

After evidence is saved, use the existing canonical destroy notebook when cleanup
is intended. Deleting the Search service/resource group removes the shared index
for both clients. Preserve the documented canonical individual-resource deletion
limitation; do not implement a separate Feature 2 cleanup path.

## Separately approved preview follow-on

The optional [preview notebook](../../demos/search02-hybrid-pagination/notebooks/05_compare_preview.ipynb)
reuses the stable Python hybrid evidence and reads the existing index with
isolated Python Search 12.1.0b2. The user selected two configured preview cases
(retrievable counts with text recall 1,000/6,158), not a full SDK/API isolation
matrix. See the [demo instructions](../../demos/search02-hybrid-pagination/README.md#optional-python-preview-comparison-preview).
This follow-on does not change the original six-case acceptance rules or complete
T029: the original keyword complete-ID control remains unresolved.
