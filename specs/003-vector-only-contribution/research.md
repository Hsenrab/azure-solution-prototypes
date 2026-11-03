# Research: Mixed Vector-Only Contributions

All design unknowns are resolved. Public-doc research was read-only; offline calculations wrote no corpus or index. No live Azure operation was performed.

## 1. Explicit version-2 fixture and separate index

**Decision**: Preserve version 1 exactly; add one fixed version-2 recipe and `hybrid-pagination-mixed-v2` on the existing service.

**Rationale**: Current helpers and both clients hard-code the original all-keyword fixture. Changing `COUNT` alone would break readiness, expected IDs, keyword control validity, schema inspection, and existing preview comparison. A separate identity keeps historical evidence interpretable.

**Alternatives considered**:

- In-place dataset/index replacement is simpler but invalidates the unchanged original baseline: rejected by the specification.
- Copying the entire runner/notebook implementation would preserve old code but duplicate behavior and future fixes: rejected in favor of common version-aware helpers.
- A generic fixture/plugin framework is unnecessary for two fixed recipes: rejected.

**Repository evidence**: [fixture generator and loader](../../demos/search02-hybrid-pagination/app/fixture.py), [Python summary/classification](../../demos/search02-hybrid-pagination/app/reproduce.py), [inspector](../../demos/search02-hybrid-pagination/app/compare.py), [preview profiles](../../demos/search02-hybrid-pagination/app/preview.py), and [independent .NET validator](../../demos/search02-hybrid-pagination/app/dotnet/Program.cs).

## 2. Separated synthetic vector membership

**Decision**: Retain SHA-256 vectors for the 6,133 keyword-only records. Use `[100, r, 0, ..., 0]` for 25 shared records with `r=26..50` and 25 vector-only records with `r=1..25`. Preserve integer-valued float32 components and existing dimensions/query/cosine setup.

**Rationale**: The controlled top 50 makes genuine non-keyword additions predictable without an embedding dependency or changing retrieval settings. Keyword content remains the original deterministic recipe; new non-keyword text excludes `maths`.

**Offline facts collected during Plan**:

| Quantity | Calculated value |
|---|---:|
| Selected top-50 shared/vector-only IDs | 25 / 25 |
| Weakest selected cosine | 0.8944271909999159 |
| Strongest keyword-only cosine | 0.5758656815513996 |
| Cutoff gap | 0.31856150944851624 |
| Distinct simulated float32 similarity scores among selected IDs | 50 |

The calculation covered all 6,183 proposed vector recipes with a float32 accumulation/score simulation. It is design evidence, not a proof of Azure numerical behavior or an executed corpus generator. Both actual vector controls remain required.

**Alternatives considered**: Randomly adding non-keyword documents would not ensure selection; identical nearest vectors would introduce avoidable boundary ties; a real embedding model adds unrelated service/dependency work. All are rejected for this mechanics demo.

## 3. Count semantics and expanded recall [PREVIEW]

**Decision**: Keep the existing stable/default and two configured Python preview profiles. Expanded text recall remains 6,158, derived from expected keyword matches. Test 6,183 as the expanded union/count acceptance target, not as a Microsoft-guaranteed numeric output.

**Rationale**: `maxTextRecallSize` limits BM25-ranked inputs to hybrid ranking, not the vector contribution. `countAndFacetMode` changes count/facet scope, not the candidate ranking configuration itself. `countRetrievableResults` scopes reporting to retrieved text/vector candidates; default scope can include text matches outside the text window.

With 6,158 full keyword matches and 50 vector candidates sharing 25 IDs, the intended full union is `6158 + 50 - 25 = 6183`. This is our fixture arithmetic. Public sources do not contain a worked numeric guarantee for this exact fixture; actual counts and paging must be measured.

The smaller-window union is not necessarily 1,025. Full-keyword/vector membership does not show which shared documents entered the smaller BM25 window. Stable default counts must likewise be observed, not fixed by assumption about vector-only count contribution.

**Alternatives considered**: Expanding recall to total record count 6,183 conflates index size with text matches; adding SDK/API/default isolation cases exceeds the approved shorter experiment. Rejected.

**Primary sources**:

- [Hybrid recall/count guidance](https://learn.microsoft.com/en-us/azure/search/hybrid-search-how-to-query#set-maxtextrecallsize-and-countandfacetmode-preview)
- [Preview Search request contract](https://learn.microsoft.com/en-us/rest/api/searchservice/documents/search-post?view=rest-searchservice-2026-08-01-preview)
- [Count mode documentation](https://learn.microsoft.com/en-us/dotnet/api/azure.search.documents.models.hybridcountandfacetmode?view=azure-dotnet-preview)
- [Recall-size documentation](https://learn.microsoft.com/en-us/dotnet/api/azure.search.documents.models.hybridsearch.maxtextrecallsize?view=azure-dotnet-preview)

Existing Python preview serialization and actual API use were already measured in the original comparison. No new stable-API capability, production-support decision, or GA date is inferred from the public documentation.

## 4. Internal keyword-window attribution

**Decision**: Verify full keyword/vector groups and actual hybrid additions; record exact smaller-window membership as `not-observed` when current responses do not expose it. The user explicitly approved this clarification during Plan; User Stories 1/3, FR-011, and SC-003 were updated.

**Rationale**: The 25 shared documents match the full keyword query but are not guaranteed positions inside the top 1,000 BM25 candidates. Current measured requests return IDs/scores without internal branch-membership evidence. A separate keyword query, especially across score ties or independent requests, is not proof of the original hybrid query's internal list.

**Alternatives considered**: Assume all 25 shared IDs overlap the smaller window, infer exact IDs from aggregate count, or add a reference query and label its results as authoritative internal attribution. Rejected. Diagnostic/debug-query expansion is outside the agreed scope.

**Sources**: [BM25 window guidance](https://learn.microsoft.com/en-us/azure/search/hybrid-search-how-to-query), [RRF mechanics](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking), and the [existing ID-only request/response hooks](../../demos/search02-hybrid-pagination/app/reproduce.py).

## 5. Safe preparation and bounded reuse checks

**Decision**: Populate only an absent/empty approved version-2 target. Refuse a populated target before writes. Record successful upload/readiness evidence; repeated measurements use read-only reuse checks, not an upsert into that target.

**Rationale**: Indexed count equality alone cannot exclude unexpected IDs/content or prove ownership. A completed fixture-bound receipt plus ordered ID/content inventory makes reuse explicit without modifying the original index or schema.

The recorded original schema has retrievable/sortable IDs and retrievable content, but vectors are non-retrievable. The new schema changes only its name. Consequently, remote checks cannot establish a full vector-byte hash. Do not change retrievability or claim count/schema checks prove immutability; preserve the no-write-target invariant and disclosed no-concurrent-writes assumption.

If all uploads succeeded but indexing is pending, read-only readiness may finalize the evidence once count/schema/inventory pass. Failed uploads remain incomplete; there is no automatic reupload, clear-and-retry, service recreation, or repair path.

**Alternatives considered**: Blind create-or-update/upsert hides target drift; full remote vector verification requires an unrequested schema change; a receipt alone misses changed IDs/content. Rejected.

**Evidence**: The original saved [schema observation](../../demos/search02-hybrid-pagination/outputs/generated/reproduction/runs/20261030-live-v2/python-hybrid.schema.json) was inspected locally. It reports ID sortable/retrievable, content retrievable, and vector non-retrievable. [Existing preparation](../../demos/search02-hybrid-pagination/app/fixture.py) already checks individual upload success.

## 6. Independent clients and explicit incomplete evidence

**Decision**: Keep independent stable Python/.NET measurements, two existing preview cases, and common local inspection. Separate total-index, expected-keyword, expected-vector, observed-contribution, and acceptance states.

**Rationale**: A partial keyword scan cannot prove an unseen ID does not match. Show declared groups and observed IDs with provenance, but require complete controls for verified membership and full contribution acceptance. Keep missing-count vector handling, single-response measured requests, repeated boundaries, and refusal to overwrite evidence.

**Alternatives considered**: Treating every indexed ID as a keyword expectation would fail the new legitimate split. Accepting contributions merely because counts match, hiding duplicates, or relaxing the original T029 would invalidate the experiment. Rejected.

## 7. Pagination, ordering, and scope limitations

**Decision**: Preserve current measured query ordering/settings and disclose count fluctuations, score ties, independent-request membership, and preview limitations.

**Rationale**: Counts can fluctuate during indexing/mutation; equal start/end counts are not snapshot isolation. RRF merges ranked lists and can produce tied fused scores even though this fixture separates vector similarities. The existing keyword duplicate/missing-ID issue is not proven to be a score-tie effect and is not fixed by this work.

Five-result paging and complete advertised scans remain acceptance mechanisms; no auto-pagination, ordering/weight change, or hidden fallback is introduced in measured cases. Sorted ID inventory is a separate readiness operation, not a keyword-control fix.

**Sources**: [Paging/count guidance](https://learn.microsoft.com/en-us/azure/search/search-pagination-page-layout), [RRF scoring](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking), and [preview request contract](https://learn.microsoft.com/en-us/rest/api/searchservice/documents/search-post?view=rest-searchservice-2026-08-01-preview).
