# Data Model: Mixed Keyword and Vector Fixture

## Versioned fixture identity

Version 1 remains byte-identical to the [original data model](../002-reproduce-hybrid-pagination/data-model.md). Its defaults remain 6,158 documents, index `hybrid-pagination-debug`, and all IDs matching "maths".

Version 2 targets `hybrid-pagination-mixed-v2` on the same service:

| Group | Inclusive ID range | Count | Full keyword match | Expected vector top 50 |
|---|---|---:|---|---|
| `keywordOnly` | `doc-000001` to `doc-006133` | 6,133 | Yes | No |
| `shared` | `doc-006134` to `doc-006158` | 25 | Yes | Yes |
| `vectorOnly` | `doc-006159` to `doc-006183` | 25 | No | Yes |

The groups are disjoint and cover the entire corpus. Keyword membership is the first two groups; vector membership is the last two. These labels describe the fixed queries, not intrinsic document types.

## Deterministic records

Keep the existing three indexed fields: `id`, `content`, and `vector`. Group metadata lives in the manifest, not a new Search field.

- IDs remain ascending, unique, and zero-padded.
- For the first 6,158 records, content is generated exactly by the version-1 SHA-256 topic/repetition rule.
- Keyword-only vectors retain the version-1 SHA-256 components.
- Shared vectors are `[100, r, 0, ..., 0]`, with 16 components and `r = ordinal - 6108`, giving ranks 26 through 50.
- Vector-only vectors have the same shape with `r = ordinal - 6158`, giving ranks 1 through 25.
- Vector-only content is a topic, the ID, and the existing deterministic `lesson` repetition count. Select the topic by `(ordinal - 6159) % 4` from:
  - `arithmetic exercises and number practice`
  - `number patterns and calculation practice`
  - `fractions exercises and quantity practice`
  - `geometry exercises and shape practice`
- Serialize components as integer-valued floats, including `100.0` and `0.0`. Retain compact UTF-8 JSONL, terminal LF, and key order `id`, `content`, `vector`.
- No timestamps, random seeds, embeddings, or new dependencies enter fixture identity.

For the unchanged query vector `[1, 0, ..., 0]`, selected cosine similarities are `100 / sqrt(10000 + r*r)`. The weakest selected vector has cosine approximately `0.894427`; the strongest keyword-only vector has approximately `0.575866`. Offline design calculation found a cutoff gap of approximately `0.318562` and 50 distinct simulated float32 scores. This verifies the proposed arithmetic, not Azure's actual ranking; both live vector controls must still pass.

Vector-only text contains no `maths` token. Local token checks and live keyword membership validation are separate gates. Synthetic proximity does not demonstrate an embedding model's semantic quality.

## Manifest

Retain existing fields and their meanings:

| Field | Version-2 constraint |
|---|---|
| `fixtureVersion` | `2`; only versions 1 and 2 are supported |
| `generatorRules` | Exact documented version-2 rules, validated independently by both clients |
| `recordCount` | `6183` |
| `corpusPath` / `corpusSha256` | `corpus.jsonl` and hash of its exact bytes |
| `indexName` | `hybrid-pagination-mixed-v2`; never arbitrary input |
| `declaredSchemaSha256` | Canonical declared-schema hash, including the new name |
| `keyword` / `queryVector` | `maths` and the existing fixed vector |
| `vectorDimensions` / `similarityMetric` | `16` / `cosine` |
| `candidateCount` / `pageSize` | `50` / `5` |
| `serviceApi` | `2025-09-01`, identifying stable fixture/schema operations |
| `keywordMatchCount` | `6158`; must equal the expected keyword ID-set cardinality |
| `membership` | Exact ascending ID arrays for `keywordOnly`, `shared`, and `vectorOnly` |

Version 1 does not acquire these new fields or a new hash. Its full keyword membership derives from its validated original ID range; its vector top 50 remains measured rather than predeclared.

Consumers derive corpus, keyword, and vector expectations from the validated fixture version. A supplied group list is not trusted unless it equals the deterministic version-2 definition. Unknown versions, misplaced IDs, inconsistent counts, altered content, vectors, hashes, or schema fail before mutation.

## Index and preparation evidence

The version-2 declared schema changes only its index name. Exhaustive cosine, dimensions, fields, analyzer, and ranking exclusions remain unchanged.

The original recorded schema has a sortable/retrievable ID and retrievable content, but **non-retrievable vectors**. Do not promise a full remote vector hash or change retrievability to obtain one.

Preparation targets only an absent or empty version-2 index with the expected schema. A populated index is not overwritten by preparation, even if its document count happens to match. Reuse is read-only.

Store `preparation.json` beside the version-2 manifest with:

- Fixture version, corpus and declared-schema hashes, service resource identity, and target index.
- Start/end timestamps, uploaded record count, checked per-document success total, and readiness status.
- Actual schema evidence reference and indexed count.
- Completed/incomplete status; success requires all 6,183 upload results and readiness checks.

Receipt states are `uploading`, `uploaded`, `ready`, and `incomplete`. `uploaded` means every document upload succeeded but readiness may still be pending; it is not a ready fixture. A read-only readiness operation may transition `uploaded` to `ready` once schema, count, and inventory agree. Failed/partial uploads remain `incomplete` and cannot be promoted by a count-only check.

Read-only reuse requires a matching `ready` receipt, actual schema/count validation, and a complete ID/content inventory matching the fixture. Inventory uses `search="*"`, ID ordering, and retrievable fields only; it is not a measured keyword/vector/hybrid case. Normal inventory paging may traverse continuations.

Receipt and ID/content checks do not prove that hidden vectors were untouched by external writers. Immutable-index assumptions and actual top-50 checks remain explicit; equal counts are not snapshot isolation.

## Measurement and contribution finding

Reuse the [existing observation contract](../002-reproduce-hybrid-pagination/contracts/experiment.md): no fabricated failures, counts, empty pages, or continuation exhaustion.

Keyword validation expects 6,158 IDs while index readiness expects 6,183. Vector validation expects the exact 50 version-2 IDs. Stable hybrid count scope and both preview recall scenarios are measured independently.

The local contribution finding records:

- Eight required cases, their evidence references, identity checks, status, and missing-case reasons.
- Expected membership and observed sets, each with completeness provenance.
- Per hybrid case: declared vector-only IDs observed, verified vector-only additions, shared candidates, missing expected additions, duplicates, and original count/page/boundary metrics.
- `keywordWindowMembership`: `{ "status": "not-observed", "ids": null }` for current responses. Null is not an empty candidate set.
- At least three examples from actual hybrid-returned vector-only IDs, with text from the hash-verified local corpus and explicit `textSource: "verified-fixture"`.
- `measurementsComplete`, `contributionAcceptance`, and `countAlignmentVerified` as distinct findings.

Actual absence from an incomplete keyword scan does not prove a document fails that query. In that situation, show expected group labels and observed IDs, but verified full-query membership and accepted vector-only contribution remain unavailable.

The smaller-window union is not hard-coded to 1,025: the 25 full-query shared documents need not all belong to its internal text window. No exact internal membership is inferred from a count or separate keyword request.

## State transitions and preservation

Local generation -> fixture validation -> separately approved preparation -> completed preparation receipt/readiness -> immutable measurement -> local comparison.

Any failure retains an incomplete state. A failed populated preparation target is not silently cleared or resumed; independent saved-case review remains possible without claiming acceptance.

Preserve original local fixture/evidence byte hashes and audit all mutation targets. Original service/index metadata checks supplement that audit; they are not a claim of full remote vector readback. Explicitly approved future whole-service cleanup remains outside this experiment.
