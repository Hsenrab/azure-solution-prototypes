# Data Model: Shared Fixture and Measurement Evidence

## Synthetic record and fixture

One immutable fixture contains exactly 6,158 records:

| Field | Rule |
|-------|------|
| `id` | `doc-000001` through `doc-006158`; unique and stable. |
| `content` | Deterministic synthetic text containing the token `maths`; no customer content. |
| `vector` | 16 finite, integer-valued float32 components; nonzero norm. |

Generation version `1` uses the ID's SHA-256 digest: the first 16 bytes minus 128
form vector components. The same digest selects a topic from `algebra`, `geometry`,
`fractions`, `statistics` using byte 18 modulo 4, the `maths` repetition count
(1 plus byte 16 modulo 7), and filler repetition count (1 plus byte 17 modulo 23).
Construct content in a documented fixed order from those terms, the ID, and the
filler token `lesson`. There is no random seed, timestamp, Python hash, or external
embedding dependency.

Serialize records in ascending ID order as UTF-8 JSON Lines with LF line endings,
fixed key order `id`, `content`, `vector`, and documented compact separators.
Hash the exact corpus bytes with SHA-256. Validate cardinality, IDs, keyword
membership, dimensions, and nonzero norms before any upload.

The manifest records `fixtureVersion`, generator rules, `corpusSha256`,
`recordCount`, corpus path, index name, declared index-schema hash, keyword,
query vector, vector dimensions, similarity metric, candidate count, service API,
and page size. Deterministic fixture identity excludes run timestamps and endpoint
identity. The query vector is `[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`.

Both clients read this one manifest and the same query vector. The expected
keyword ID set is the complete corpus; every vector result should be a subset.
The actual top-50 vector IDs and their overlap with hybrid results are measured,
not manufactured in advance.

## Index definition

One demo-owned index named `hybrid-pagination-debug`:

- `id`: `Edm.String`, key, retrievable, not searchable.
- `content`: `Edm.String`, searchable and retrievable; `standard.lucene` analyzer.
- `vector`: `Collection(Edm.Single)`, searchable, 16 dimensions, vector profile
  using exhaustive KNN with cosine similarity.
- No semantic configuration, custom scoring profile, vectorizer, filter, or sort.

Store the declared and actual index definitions as evidence. Canonicalize declared
schema JSON with sorted object keys for its hash; preserve raw service schema
separately instead of pretending service-added defaults were declared inputs.
Preparation may create/update this index and upload the deterministic IDs. It
does not clear another index, delete unexpected documents silently, or create
another service. Each upload result must succeed; indexed count must equal 6,158.

## Query case and run

A run binds a unique `runId` to one environment identity, index, fixture/schema
hashes, exact client package versions, start/end timestamps and index counts.
Each run has six query cases keyed by `(language, case)`.

| Case | Keyword contribution | Vector contribution |
|------|----------------------|---------------------|
| `keyword` | `maths`, simple query, `content`, search mode `any` | Absent |
| `vector` | Absent, not `*` | Shared vector, field `vector`, `k=50`, exhaustive |
| `hybrid` | Same as keyword control | Same as vector control |

All cases request count, select `id`, use `top=5`, omit explicit ordering, and use
API `2025-09-01`. Offset is the only changing query input within a case.

## Page observation

Each observation records:

- Case/run identity; phase `scan`, `boundary-probe`, or `boundary-repeat`.
- One-based `pageNumber`, zero-based `skip`, `top`, and whether the page is advertised.
- Returned ID sequence, optional scores, row count, nullable actual reported count.
- Actual API version, method/path, normalized nonsecret request, send count,
  timestamp, HTTP status, service request ID, and continuation presence.
- Explicit error details if failed; failed row count and IDs are null, not zero
  and an empty array.
- `incompleteReason`: null normally; `service-continuation` when fewer than `top`
  rows arrive with continuation information, including an empty response. Retain
  actual response values, stop the case as incomplete, and do not interpret this
  observation as exhaustion or include it in completed primary metrics.

Repeated observations do not inflate primary row/unique/duplicate totals.
Only valid primary scan observations contribute, using the explicit scan basis:
advertised offsets when an initial count exists, or candidate offsets for a
vector-only control without that count. A zero-count bootstrap request is
recorded but is not an advertised page.

## Finding and comparison

Each case report references its append-only observation file and includes:

- Initial reported count and `ceil(count/5)` advertised pages when available.
- `summary.scanBasis`: `advertised-count` or `vector-k`; `summary.scanPageCount`:
  required primary offsets for that basis. A `vector-k` control measures all
  `ceil(k/5)` offsets (10 with this fixture), even after valid empty responses.
- `summary.reportedCount`, `summary.advertisedPages`,
  `summary.advertisedPageCoverage`, and `summary.reportedMinusReachable`: null
  for `vector-k`; never inferred from `k`. Keep actual rows/IDs/page metrics and
  candidate boundaries, clearly labeled rather than advertised.
- Observed counts/count-change flag; scan coverage and all failures.
- Total rows, unique reachable IDs, duplicate IDs with occurrences, missing
  expected keyword IDs, populated/empty pages, first empty and last populated.
- Boundary offsets, initial/repeated observations, and explicit agreement flags.
- `status`: `complete`, `blocked`, `incomplete`, or `unsupported`.
- `outcome`: `reproduced`, `not-reproduced`, `blocked/incomplete`, or `not-applicable`.
- Baseline validity, limitations, and reasons for any blocked attribution.

For a complete stable case, reproduction requires both a positive
reported-minus-unique gap and at least one empty advertised page. Not-reproduced
requires all advertised results to be accounted for without unexpected empty
pages. Other inconsistent evidence remains blocked/incomplete.

The sole `not-applicable` outcome is a successful vector-only control without an
initial count: `status=complete`, `scanBasis=vector-k`, reason `count-unavailable`.
All candidate offsets and required boundary repeats must succeed. Use the final
candidate scan page and first empty candidate page instead of unavailable
advertised boundaries. Later counts do not change the scan basis. Compare
non-null counts for drift; null is unavailable, not zero or drift. Keyword/hybrid
cases require an initial count and cannot use this exception. HTTP failures,
`service-continuation`, count drift, or unfinished scans/repeats take precedence
and keep the case incomplete.

The comparison binds six actual reports, checks input/effective-request parity,
and compares counts, ID sets, duplicates, boundaries, and outcomes pairwise.
It identifies missing cases instead of inventing their results. It separates
observations, candidate-window hypothesis assessment, and unknown customer
settings. Different client results are valid evidence, not a reason to fabricate
agreement.
Missing optional vector counts make count comparisons unavailable, not falsely
equal. Disclose different scan bases and their coverage limits; this absence
alone does not block acceptance when both vector controls completed and all
remaining case/baseline/parity requirements pass.

## State and invariants

Fixture generation -> successful population -> indexed-count check -> immutable
measurement -> summary/comparison. Each case is incomplete until all required
pages and boundary repeats have succeeded. Persist the initial incomplete status
before the first request so interrupted runs cannot look complete.

A keyword baseline passes only with exactly the expected 6,158 IDs, no duplicates,
1,232 advertised/populated pages, and three results on the last advertised page.
Known writes, changed hashes/settings, failed ingestion, or count drift invalidate
the stable comparison. Start/end counts alone do not prove absence of mutation.
