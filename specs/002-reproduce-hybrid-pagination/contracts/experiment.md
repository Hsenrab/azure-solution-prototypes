# Local Experiment Contract

This is the implemented local file/CLI contract, not a hosted API. Run the
independent clients against a prepared index; saved evidence is not a substitute
for matching the customer's actual request.

## Inputs and invocation

Run commands from the demo root. The notebook generates the fixture, prepares the
index using the Python SDK, then invokes each client independently.

```powershell
.\.venv\Scripts\python.exe -m app.reproduce --case keyword --manifest outputs\generated\reproduction\fixture\manifest.json --env-file env\.env --run-dir outputs\generated\reproduction\runs\<run-id>
dotnet run --project app\dotnet\HybridPagination.csproj -- --case keyword --manifest outputs\generated\reproduction\fixture\manifest.json --env-file env\.env --run-dir outputs\generated\reproduction\runs\<run-id>
```

Repeat with `--case vector` and `--case hybrid`. Both runners:

- Require `--case`, `--manifest`, `--env-file`, and `--run-dir`; no implicit
  environment selection or fallback API/package version.
- Read the existing nine-key deployment-output contract. .NET supports the
  generated plain `KEY=value` file directly, without another dotenv dependency.
- Validate the manifest and current setup-user/subscription context; use Entra
  credentials, not keys. CLI identity checks follow existing error-surfacing
  conventions, not a new general command-wrapper framework.
- Verify the same index/schema and expected indexed count before queries.
- Derive language/package/API metadata from the actual runtime/configuration.
- Refuse to overwrite an existing report for the same language/case/run directory.
  A repeat full experiment uses a new run directory; boundary replays stay inside
  the original case.
- Return nonzero for failed/blocked/unsupported measurements. A valid completed
  not-reproduced result or completed vector control with outcome `not-applicable`
  is not a process failure.

Comparison is local and does not issue Search queries:

```powershell
.\.venv\Scripts\python.exe -m app.compare --run-dir outputs\generated\reproduction\runs\<run-id>
```

## Effective request contract

Both SDK clients must send equivalent requests as defined in the
[data model](../data-model.md#query-case-and-run). Record declared settings and
capture actual request serialization/API. Normalize equivalent wire forms, such
as array versus comma-separated field selection, without erasing semantic
differences. Include implicit defaults and whether they are documented or observed.

Do not silently inject `search=*` into the vector-only case. Do not send preview
hybrid controls, ordering, filters, semantic options, or additional vectors.
Set measured Search-request retries to zero in both clients. Only `skip` changes
within a case; the repeated boundary requests use the same inputs as originals.

Use one service response per logical page: Python consumes the first `by_page()`
page and obtains count from the same raw response hook; .NET consumes only the
first `AsPages()` page and uses the initial response's `TotalCount`. Count actual
Search sends and retain continuation presence without following it automatically.
If these guarantees fail, record the mismatch and mark the case incomplete.

For every scan, probe, and repeat, if `rowCount < top` and continuation information
is present, retain the actual response and set `incompleteReason=service-continuation`.
Stop the case with status `incomplete`, outcome `blocked/incomplete`, and nonzero
exit before treating that response as an exhausted/empty page or using it to
establish reproduction. Do not fetch continuation automatically. A short response
without continuation can still be a valid partial or empty page. This rule takes
precedence over the optional-vector-count completion exception.

## Scan and boundary algorithm

1. Request offset zero with `top=5` and count enabled; keep this observation as
   the first scan page when advertised count is positive.
2. With an initial count, set `scanBasis=advertised-count` and
   `advertisedPages=ceil(initialCount/5)`. Request every remaining advertised
   offset, even after an empty response without continuation. A partial final
   page without continuation is valid.
3. Preserve a nullable count for each response. Compare available non-null counts;
   differing available counts invalidate the stable run. Null means unavailable,
   not zero or count drift. Do not silently reuse an old count as a new observation.
4. Missing initial count blocks keyword/hybrid completion. For vector-only,
   require every offset in the `ceil(k/5)` candidate-page budget, labeled
   `scanBasis=vector-k` (`scanPageCount=10` for `k=50`). Keep reported count,
   advertised pages, advertised-page coverage, and reported-minus-reachable gap
   null. Do not switch scan basis if a later response supplies a count; preserve
   all actual counts and still detect disagreements among available counts.
5. Compute rows/IDs/duplicate and populated/empty-page metrics from valid primary
   scan observations in the declared scan basis, excluding probes/repeats and
   responses marked incomplete. Candidate-page metrics are not advertised-page
   metrics. A zero-count bootstrap is not an advertised page.
6. Select the last populated page, its immediately following page, final advertised
   page, and first empty advertised page when present. For `vector-k`, use the
   final candidate scan page and first empty candidate page in place of advertised
   boundaries. Deduplicate selected offsets. An immediately following page outside
   the applicable scan range is an explicit probe.
7. Reuse an existing scan observation as the first boundary observation. Obtain
   any new outside-range probe once. Repeat every selected boundary offset once,
   giving exactly two observations per selected offset, not three. For zero
   advertised pages, repeat the bootstrap offset once instead.
8. Record agreement in count, size, ID set, and ordering separately. Tied ordering
   differences are not automatically an SDK defect or a failed reproduction.
9. A stable vector-only `vector-k` scan with every required offset and boundary
   successfully measured completes with `status=complete`, `outcome=not-applicable`,
   and reason `count-unavailable`. It is a completed control, not a count-gap
   classification. Any failure, short response with continuation, count drift, or
   unfinished measurement instead remains blocked/incomplete.

## Outputs

Under the supplied run directory:

```text
python-keyword.json             python-keyword.pages.jsonl
python-vector.json              python-vector.pages.jsonl
python-hybrid.json              python-hybrid.pages.jsonl
dotnet-keyword.json             dotnet-keyword.pages.jsonl
dotnet-vector.json              dotnet-vector.pages.jsonl
dotnet-hybrid.json              dotnet-hybrid.pages.jsonl
comparison.json
comparison.md
```

The six JSON files are the case reports. Each references a UTF-8 JSON Lines file
containing durable page observations. Report shape:

| Member | Required content |
|--------|------------------|
| `schemaVersion`, `runId`, `language`, `case` | Version `1`, unique run-directory identity, `python`/`dotnet`, three-case enum. |
| `fixture`, `index`, `environment` | Corpus/schema hashes, index name, endpoint/resource/subscription identity; no credentials. |
| `client`, `query` | Exact package versions, runtime, configured and observed API, settings/defaults. |
| `startedAt`, `finishedAt` | UTC ISO timestamps; unfinished runs have null finish time. |
| `status`, `outcome`, `reasons` | States/classifications defined in the data model; explicit causes of incompleteness. |
| `observationsFile` | Relative path to this case's evidence; no other client's report as a substitute. |
| `summary` | All specified counts/rows/IDs/duplicates/pages, count drift, coverage, index start/end counts. |
| `boundaries`, `limitations` | Two observations per selected offset, agreement flags, tie/mutation/customer-parity caveats. |

`summary.scanBasis` is `advertised-count` or `vector-k`; `summary.scanPageCount`
is the required number of primary scan offsets for that basis.
`summary.reportedCount`, `summary.advertisedPages`,
`summary.advertisedPageCoverage`, and `summary.reportedMinusReachable` are null
for `vector-k`, never zero or values inferred from `k`. Advertised-only boundaries
are also null; candidate boundaries and actual measured IDs remain available.
`not-applicable` is allowed only for a complete vector-only case whose initial
reported count is unavailable, never for a failed case or keyword/hybrid case.

Initialize a durable incomplete report before requests; finalize it only after
the complete scan and replays. Append and flush each page observation. Failed
requests retain status/error/request identity, with null result values. Persist
the failure and propagate the original SDK error/nonzero exit; never catch broad
exceptions to write empty results or a success-shaped fallback.

`comparison.json` includes all six expected case slots, actual report references,
input/request parity, case metrics/outcomes, pairwise ID-set differences and
overlaps, missing cases, control validity, and an overall completion status.
`comparison.md` renders these facts with separate observations, hypothesis, and
limitations sections and authoritative links. Missing cases remain explicit gaps.
Do not discard disagreements or demand equal tied ordering to finish a comparison.
Disclose missing vector counts and different scan bases, leaving unavailable count
comparisons null rather than asserting agreement. A complete `not-applicable`
vector control alone does not block overall acceptance; all six cases must still
execute successfully, keyword baselines must pass, hybrid outcomes must be
classified, and genuine input/request mismatches or failures remain blockers.

All generated files, environment files, .NET build outputs, and tokens stay out
of source control. The comparison may quote synthetic IDs but never token/header
data. It must not claim a customer SDK defect, production suitability, or GA date.
