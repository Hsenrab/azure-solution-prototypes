# Quickstart: Validate Vector-Only Hybrid Contributions

The mixed fixture, independent clients, local contribution renderer, and
[notebook](../../demos/search02-hybrid-pagination/notebooks/06_vector_contributions.ipynb)
are implemented with offline checks. The separately approved mixed-index preparation
and all eight live cases have run. **Overall acceptance remains blocked by the
keyword controls**. The populated target must be reused read-only, not prepared again.

## Prerequisites

- Follow the existing [demo setup](../../demos/search02-hybrid-pagination/README.md) and [original validation guide](../002-reproduce-hybrid-pagination/quickstart.md).
- The same exported environment and setup user must have access to the existing running service. If it is absent, stop; this feature does not authorize paid reprovisioning.
- Retain stable Python/.NET dependencies and the existing isolated preview environment. No package upgrade or new notebook kernel is required.
- Preserve version-1 local fixture/evidence hashes and leave its index untouched.
- Live creation/upload of the additional index requires separate explicit approval. No live operations run as part of Plan.

## Primary notebook journey

After implementation, open `06_vector_contributions.ipynb` in the demo's notebook directory with the original demo kernel. It generates the mixed fixture locally, prepares only the new target when explicitly approved, and separates measurement from read-only review.

For repeated measurements, reuse the prepared mixed index and a **fresh run directory**; skip the one-time preparation heading. A populated index is never silently overwritten. If any case fails, inspect its retained evidence and deliberately run other independent cases or the final partial-review heading; do not interpret failure as empty-page reproduction or accepted contribution.

Original setup, destroy, and reproduction notebooks retain their existing purpose. Do not rerun empty-service readiness on a populated service or delete data to make that assertion pass.

## Local generation and preflight

From `demos\search02-hybrid-pagination`:

```powershell
$manifest = 'outputs\generated\reproduction\fixtures\mixed-v2\manifest.json'
$runDir = 'outputs\generated\reproduction\mixed-runs\' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
.\.venv\Scripts\python.exe -m app.fixture --fixture-version 2 --directory outputs\generated\reproduction\fixtures\mixed-v2
```

Check the [data model](./data-model.md): 6,183 unique records, 6,158 keyword matches, exact 6,133/25/25 groups, and offline vector top 50 containing 25 shared and 25 vector-only IDs. Generate again in a separate empty local directory; exact corpus, manifest, and declared-schema bytes must agree.

Local checks must reject altered vectors/content, bad group partitions, unexpected keyword tokens, wrong counts, unsupported versions, and a version-1 target substituted into the mixed manifest.

Build the existing .NET project before the local independent-client runtime checks:

```powershell
dotnet build app\dotnet\HybridPagination.csproj --no-restore
.\.venv\Scripts\python.exe -m unittest scripts.validate_local.MixedFixtureChecks scripts.validate_local.MixedMeasurementChecks scripts.validate_local.MixedPreparationChecks scripts.validate_local.MixedContributionChecks scripts.validate_local.MixedNotebookChecks -v
```

These checks use temporary fixtures, saved synthetic cases, SDK transports/mocks,
and deliberately absent environment files for .NET recipe validation; they do not
contact Azure. They are not substitutes for SC-002 through SC-004 live acceptance.

## Separately approved one-time preparation

Only after explicit approval:

```powershell
.\.venv\Scripts\python.exe -m app.fixture --fixture-version 2 --directory outputs\generated\reproduction\fixtures\mixed-v2 --prepare --env-file env\.env
```

Require all 6,183 checked upload results, a completed matching preparation receipt, exact indexed count, and verified schema/ID/content readiness. The target is `hybrid-pagination-mixed-v2`, never `hybrid-pagination-debug`.

Do not rerun preparation against a populated target. For indexing delay, complete the read-only readiness checks after the service reflects all successful uploads; do not remove or reupload documents automatically. Missing receipt, unexpected data, or wrong identity blocks reuse.

The notebook's read-only readiness heading calls the planned `verify_prepared_fixture(manifest_path, env_file)` helper. It may finalize an all-successful `uploaded` receipt to `ready`; it cannot promote an incomplete upload. Both clients independently gate measurements on ready receipt/schema/count/ID-content checks.

## Independent stable cases

Keep the index unchanged throughout measurement. For each client, run `keyword`, `vector`, and `hybrid` as separate commands so a failed control does not silently skip or replace another case:

```powershell
.\.venv\Scripts\python.exe -m app.reproduce --case keyword --manifest $manifest --env-file env\.env --run-dir $runDir
dotnet run --project app\dotnet\HybridPagination.csproj --no-build -- --case keyword --manifest $manifest --env-file env\.env --run-dir $runDir
```

Repeat those two commands with `--case vector`, then `--case hybrid`. Restore/build the existing .NET project before using `--no-build`, following its existing guide; package pins remain unchanged.

Expected controls:

| Case | Indexed count | Unique result IDs | Advertised/populated pages when count available |
|---|---:|---:|---:|
| Keyword | 6,183 | 6,158 expected keyword IDs | 1,232; final page has 3 rows |
| Vector | 6,183 | 50: 25 shared + 25 vector-only | 10 |

Keyword duplicates/missing IDs remain failed control evidence. A missing initial vector count uses the existing ten-page candidate scan and null count metrics, not an invented count of 50.

Stable hybrid must retain all actual advertised pages, including empties. Do not prescribe its count or smaller-window union size as a fixed number; observe the reported scope and the 25 additional vector-only IDs.

## Configured preview cases [PREVIEW]

After the same run's stable Python hybrid case completes:

```powershell
.\.venv-preview\Scripts\python.exe -m app.preview run --scenario retrievable --baseline "$runDir\python-hybrid.json" --manifest $manifest --env-file env\.env --run-dir $runDir
.\.venv-preview\Scripts\python.exe -m app.preview run --scenario expanded --baseline "$runDir\python-hybrid.json" --manifest $manifest --env-file env\.env --run-dir $runDir
```

Both use Python Search 12.1.0b2 and API 2026-08-01-preview with retrievable-result counting. Recall is 1,000 and 6,158 respectively; the latter is the keyword count, not the indexed total.

Expanded acceptance requires 6,183 reported and unique IDs, 1,237 populated pages, three rows on the final advertised page, no duplicates/empty advertised pages, and no positive following-page probe. These are acceptance targets, not results already observed.

## Local review and acceptance

```powershell
.\.venv\Scripts\python.exe -m app.contributions --manifest $manifest --run-dir $runDir
```

Review both generated contribution reports and the eight actual case/observation/schema files. Require:

- Exact fixture/index/environment/request identity, successful primary scans, and two observations per selected boundary.
- Both complete keyword/vector controls and all 25 verified vector-only additions in each required hybrid case.
- Expected versus observed groups, at least three actual vector-only hybrid IDs with fixture text, and full-query shared candidates.
- Internal smaller-window membership explicitly `not-observed`, not an assumed inside/outside classification.
- Actual count gaps, duplicates, missing IDs, page coverage, and out-of-range probes; a blocked report remains blocked.
- Clear separation between fixture declaration, observed contributions, count alignment, and overall acceptance.

## Preservation and implementation validation

- Reinspect the six original stable reports and the original preview comparison without rewriting them. Their existing completeness/blockers remain unchanged.
- Compare original local fixture/evidence byte hashes before/after; audit mutation calls so only the new target can be written.
- Check original index identity/count/schema read-only. These checks supplement the no-write-target invariant; hidden vectors are not remotely hash-verified.
- Exercise both fixture versions, both clients, mismatch/overwrite refusal, missing-count vector handling, partial continuation, incomplete controls, unknown window membership, and positive following-page probes with focused existing checks.
- Run Python syntax/runtime checks, locked .NET restore/build, the existing local validator, and configured notebook hygiene hooks. Do not add a test framework or change CI.
- Existing kernel display-name metadata in the original reproduction notebook previously caused one full-validator failure. Report that baseline issue separately; do not rewrite original notebooks during unrelated validation.

The original feature's failed keyword-control acceptance remains unresolved. The service remains billable; cleanup requires separately intended/approved use of the existing canonical destroy journey, not a new mixed-fixture cleanup path.

## Recorded live outcome

Run `20261102T233019Z-bee9da5d` completed on 2026-11-03 UTC after explicit approval:
[contribution report](../../demos/search02-hybrid-pagination/outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/contribution-comparison.md),
[acceptance criteria](../../demos/search02-hybrid-pagination/outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/acceptance.json),
and [preservation checks](../../demos/search02-hybrid-pagination/outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/preservation.json).

- SC-001 passed offline; all 22 new local checks pass. At the live-run stage the
  full validator had 39 passes and the pre-existing original-notebook metadata failure.
  Subsequent user-approved publishing cleanup removed notebook outputs/execution
  counts/kernel display-name metadata after a local backup, without changing code
  or separate measurements. All 40 local checks now pass.
- SC-002 failed: both keyword controls returned 6,158 rows but only 6,094 unique
  IDs, with 64 duplicate excess rows and 64 missing expected IDs. Both vector
  controls returned the exact intended 50 IDs.
- All four hybrids returned all 25 declared vector-only members, but SC-003's
  verified contribution finding remains blocked by the incomplete keyword controls.
- SC-004 passed: expanded preview reported/reached all 6,183 IDs across 1,237
  populated pages with three final rows, no duplicates/empty advertised pages,
  and no positive following-page probe.
- Stable Python/.NET hybrids each reported 6,183 and reached 1,046 IDs, with 1,027
  empty advertised pages. Smaller preview reported/reached 1,046 with no empties.
- Expected/observed groups, three actual-ID text examples per hybrid, explicit
  unknown internal-window membership, failures, and source hashes are retained.
- All 54 protected files and original-index metadata/count matched before/after;
  no hidden-vector hash or snapshot-isolation guarantee is asserted.

T001-T035 are complete; T036 remains unchecked with these concrete blockers.
Do not add sorting, weaken controls, rewrite original evidence, or relabel the
experiment successful to close that task.
