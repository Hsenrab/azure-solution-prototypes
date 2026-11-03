# Interface Contract: Mixed-Fixture Experiment

## Existing interfaces retained

Original notebook and CLI defaults select version 1. Existing dependencies, keyless authentication, generated nine-value environment export, stable SDK/API pins, preview isolation, and original evidence paths remain unchanged.

Preparation uses the Python Search SDK. The .NET client remains an independent reader/measurement implementation, not a caller of the Python runner.

## Local fixture generation and approved preparation

From the demo root, the planned fixture command extends the existing parser:

```powershell
.\.venv\Scripts\python.exe -m app.fixture --fixture-version 2 --directory outputs\generated\reproduction\fixtures\mixed-v2
```

- `--fixture-version`: choices `1` and `2`, default `1`.
- Existing `--directory`, `--prepare`, and `--env-file` semantics remain.
- Generation is local only. The mixed directory must not be the original fixture directory.
- Different existing fixture bytes cause nonzero failure; no overwrite.
- With separately approved `--prepare --env-file env\.env`, only the validated version-2 index can be created/populated.
- A populated target causes nonzero failure before upload or schema update. Missing service, wrong identity, unexpected schema/data, or failed upload never triggers recreation, deletion, credential fallback, or a success response.
- Successful output identifies the fixture, index, actual count 6,183, and durable completed preparation receipt. An indexing delay blocks readiness; it does not justify measurement or reuploading into a populated index.

The new shared Python notebook callable `verify_prepared_fixture(manifest_path, env_file)` performs read-only Azure readiness/reuse checks and returns the fixture/index/count/inventory finding. It validates the matching preparation receipt and may finalize only its local `uploaded` state to `ready` after all checks pass; `uploading` or `incomplete` is rejected. It never uploads, patches schema, clears data, or provisions resources. Hidden-vector equivalence is not asserted.

The .NET client independently validates the same ready receipt and schema/count/ID-content inventory before measuring. It does not call the Python readiness implementation. SDK request iteration for this ordered inventory is separate from first-page-only measured requests.

## Stable cases

Both existing CLIs retain their four required selectors:

```powershell
.\.venv\Scripts\python.exe -m app.reproduce --case <keyword|vector|hybrid> --manifest <mixed-manifest> --env-file env\.env --run-dir <mixed-run-dir>
dotnet run --project app\dotnet\HybridPagination.csproj --no-build -- --case <keyword|vector|hybrid> --manifest <mixed-manifest> --env-file env\.env --run-dir <mixed-run-dir>
```

Outputs remain `python-<case>.json/.pages.jsonl/.schema.json` and `dotnet-<case>.json/.pages.jsonl/.schema.json`. A manifest selects its approved index and expected sets; a separate index override is not introduced.

All six cases use stable API `2025-09-01`. Only offset changes within a measured case. Case/schema/observation files cannot be overwritten. Underlying errors remain visible; nonzero incomplete classification is not an empty-page success.

## Configured preview cases [PREVIEW]

Reuse the isolated Python preview interpreter and existing selectors:

```powershell
.\.venv-preview\Scripts\python.exe -m app.preview run --scenario <retrievable|expanded> --baseline <mixed-run-dir>\python-hybrid.json --manifest <mixed-manifest> --env-file env\.env --run-dir <mixed-run-dir>
```

- `retrievable`: recall 1,000 and `countRetrievableResults`.
- `expanded`: recall derived from expected keyword membership, **6,158**, not total indexed count 6,183; same count mode.
- SDK `12.1.0b2`, actual document API `2026-08-01-preview`.
- Names remain `preview-retrievable-1000` and `preview-retrievable-6158`, each with the three existing evidence files.
- The stable baseline must be completed, request-verified, and bound to the same version-2 fixture/index/environment.
- An original version-1 baseline is rejected, not silently substituted.
- A failed keyword control does not fabricate a successful preview baseline or prevent deliberate collection of independently valid hybrid evidence. Overall contribution acceptance still requires valid controls.

## Local contribution renderer

Add one local CLI:

```powershell
.\.venv\Scripts\python.exe -m app.contributions --manifest <mixed-manifest> --run-dir <mixed-run-dir>
```

It reads the verified version-2 fixture and these eight slots:

| Slots | Package/API profile |
|---|---|
| Python keyword, vector, hybrid | Original stable Python |
| .NET keyword, vector, hybrid | Original stable .NET |
| Preview recall 1,000 / 6,158 | Existing configured Python preview |

It issues no Search requests or replacement measurements. It writes `contribution-comparison.json` and `contribution-comparison.md` in the mixed run directory, using common evidence inspection and rendering existing stable/preview summaries where appropriate.

### Finding shape

- `schemaVersion`, `runId`, fixture/schema identity, evidence references and hashes.
- `cases`: all eight slots; a missing case is null with an explicit missing-case reason.
- `identityMismatches`: fixture, environment, index, run, or unauthorized effective-query differences.
- `expectedMembership`: exact fixture groups.
- `observedMembership`: actual sets plus control-completeness/validity flags.
- `hybridContributions`: per-case observed declared-vector-only IDs, verified IDs or null when not established, shared full-query candidates, missing expected IDs, and text examples.
- `keywordWindowMembership`: status `not-observed`, IDs null; no separate reference query is treated as internal attribution.
- `countFindings`: actual reported count, rows, unique IDs, duplicate excess, advertised/populated/empty pages, scan basis, boundaries, and positive out-of-range probes.
- `measurementsComplete`, `contributionAcceptance`, and per-case `countAlignmentVerified`.
- `limitations`: synthetic-vector meaning, historical/concurrent-index assumptions, internal-window observability, preview scope, and outstanding control failures.

Text examples must reference actual measured hybrid IDs and the verified corpus. Do not claim the original ID-only search response returned document text.

### Completion and exit status

Exit 0 requires all eight required measurements complete and compatible, both keyword/vector controls valid, all 25 verified vector-only additions present in each required hybrid case, and expanded-preview coverage/count alignment meeting the specification.

Otherwise persist a blocked/incomplete finding and exit nonzero. Individual observed facts may still be shown; missing negative evidence, unknown membership, or count-only equality cannot become accepted contribution evidence.

## Notebook interface and boundaries

One planned additional notebook, `06_vector_contributions.ipynb`, uses the original kernel and the existing preview subprocess environment. Purpose headings cover:

1. Prerequisites and explicit mixed-fixture paths.
2. Local mixed-fixture generation and group preview.
3. Separately approved one-time index preparation.
4. Read-only readiness/reuse and fresh run identity.
5. Six independent stable measurements.
6. Two configured preview measurements.
7. Local contribution review and actual evidence links.

Each measurement cell surfaces subprocess output and failure rather than swallowing it. After a failed case, collection of other independent cases or partial review is deliberate, not an automatic success path. Reruns use a fresh run directory and skip populated-index preparation.

No new environment keys, infrastructure deployments, diagnostic queries, ordering/weight changes to measured cases, new kernels, package upgrades, or separate cleanup commands are added.
