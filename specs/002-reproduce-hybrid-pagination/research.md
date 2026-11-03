# Research: Hybrid Search Count/Pagination Reproduction

**Date**: 2026-10-28
**Scope**: Planning decisions; no document query or reproduction executed.

## 1. Independently pin the clients and common API

**Decision**: Python `azure-search-documents==12.0.0` and .NET
`Azure.Search.Documents` 12.0.0, explicitly using service API `2025-09-01`.
Retain Python identity 1.25.3; pin .NET `Azure.Identity` 1.21.0. Target .NET 10 LTS
(`net10.0`) without installing it as part of planning.

**Evidence**: Independently checked [PyPI](https://pypi.org/project/azure-search-documents/12.0.0/)
and [NuGet Search](https://www.nuget.org/packages/Azure.Search.Documents/12.0.0),
plus [NuGet Identity](https://www.nuget.org/packages/Azure.Identity/1.21.0).
The installed Python package exposes explicit `api_version` client configuration
and the required count, offset, top, and vector query arguments. The exact
[.NET 12.0.0 source](https://github.com/Azure/azure-sdk-for-net/blob/Azure.Search.Documents_12.0.0/sdk/search/Azure.Search.Documents/src/SearchClientOptions.cs)
includes `V2025_09_01`; its default is instead `V2026_04_01`.

**Rationale**: Same package number is not evidence of parity. An explicit common
stable API removes an otherwise hidden default difference. These are a verified
standalone baseline, not proof of the customer's exact dependency/API combination.

**Alternatives considered**: Reject floating defaults and prerelease packages for
the initial baseline. Reject assuming the customer's stated package pins describe
the actual deployed request. Do not select an unverified local .NET SDK: no SDK
was listed locally during planning, so installation remains an execution prerequisite.

## 2. Treat count scope as the hypothesis, not the conclusion

**Decision**: Request counts in every case; measure all advertised five-result
pages. Do not set preview `maxTextRecallSize` or `countAndFacetMode`.

**Evidence**: The [hybrid guide](https://learn.microsoft.com/en-us/azure/search/hybrid-search-how-to-query#set-maxtextrecallsize-and-countandfacetmode-preview)
describes `countAllResults` as the default and distinguishes full text-side matches
from the documents retrieved for RRF. It documents default text recall of 1,000,
maximum 10,000 for the preview control, and vector contribution bounded by `k`.
The [pagination guide](https://learn.microsoft.com/en-us/azure/search/search-pagination-page-layout)
distinguishes count from response size, documents `top`/`skip`, and states that
counts are accurate on a stable index but approximate during active indexing.

**Rationale**: This supports a candidate-window explanation worth testing, not a
guaranteed boundary for this service/API. Documented defaults are labeled as such;
actual responses and captured requests are the evidence for the pinned baseline.
Candidate overlap means text/vector sizes cannot simply be added. Offset queries
are independent requests, not a frozen result snapshot.

**Alternatives considered**: Reject guessing a limit of 1,285 documents, tuning data
to get 257 populated pages, stopping at the first empty page, or treating a count
gap alone as sufficient reproduction. Preview remediation and production/release
advice belong to a later investigation.

## 3. Use small fixed vectors, not model-generated embeddings

**Decision**: Exactly 6,158 records; 16-dimensional deterministic vectors;
exhaustive KNN with cosine similarity; a fixed query vector and `k=50`.

**Rationale**: Exhaustive search removes approximate-neighbor retrieval as a
confounder at this small scale. Integer-valued components are exactly representable
as float32 in both clients. The shared fixture carries the vector values; .NET
does not independently regenerate them. All vector candidates are among known
keyword matches because every document matches "maths".

**Alternatives considered**: Reject an embedding/model deployment, semantic-quality
claims, approximate HNSW retrieval for the first baseline, multiple vectors,
filters, custom sorting, or semantic reranking. Customer use of any of these is a
parity gap, not an explanation already established by this experiment.

## 4. Measure one logical offset request without accidental auto-paging

**Decision**: Every logical page creates a new SDK search with `top=5` and
`skip=5*(pageNumber-1)`. Consume only the first service response page.

**Python evidence**: Inspected the installed 12.0.0
`azure.search.documents._operations._patch.SearchItemPaged`. Iterating all items
can auto-continue. `get_count()` caches a first page iterator, while a separate
`by_page()` creates a new iterator; combining them naively can issue another
search. Implementation must consume one `by_page()` page and capture the count
from that same response via a public response hook, not depend on private APIs.

**.NET evidence**: The exact
[12.0.0 SearchResults source](https://github.com/Azure/azure-sdk-for-net/blob/Azure.Search.Documents_12.0.0/sdk/search/Azure.Search.Documents/src/Models/SearchResults.cs)
exposes `TotalCount` and pageable results. Use the initial `SearchAsync` result's
count and only the first page from `GetResultsAsync().AsPages()`, disposing the
enumerator without traversing continuation pages.

**Rationale**: Capture the actual service API, normalized request body, status,
request ID, and number of Search HTTP sends per logical page. Explicitly disable
automatic retries for measured Search requests in both clients; request failures
remain failures, not extra unreported attempts. Do not log authorization headers
or tokens. Public SDK hooks/policies are experiment instrumentation, not a new
HTTP client or a replacement for direct SDK search.

**Alternatives considered**: Reject `list(all_results)`, unbounded async iteration,
using a page-size hint without explicit `top`, reporting SDK continuation as a
user page, or comparing only intended settings. If a single-response assumption
fails, report non-equivalence/incompleteness rather than silently changing the
query. Compilation and live request capture must validate this design later.

**Approved refinement (2026-10-30)**: A scan, probe, or repeat returning fewer
than `top=5` rows with continuation information is incomplete with reason
`service-continuation`. Preserve the response, stop the case, and never count it
as exhausted/empty-page reproduction evidence or fetch continuation implicitly.
A short response without continuation remains valid. This closes an ambiguity
in the measurement design; it is not a claim that the service was observed doing
this during planning.

## 5. Keep the existing infrastructure journey intact

**Decision**: Append one reproduction notebook after initial infrastructure
readiness. Use one Python runner and one direct .NET console implementation.
Reuse Feature 1's environment exports and setup-user identity.

**Rationale**: Explicitly approved by the user after presenting the .NET prerequisite
and several-thousand-read trade-off. Preserves canonical setup/destroy and avoids
changing an infrastructure-only zero-index baseline into a misleading post-ingest
check. Both language runners can execute without wrapping the other.

**Alternatives considered**: Reject separate services per client, rewriting the
canonical notebooks, moving deployment/authentication into app code, or adding a
test framework. Separate notebooks add navigation without improving independence.

The [.NET CLI credential options](https://learn.microsoft.com/en-us/dotnet/api/azure.identity.azureclicredentialoptions?view=azure-dotnet)
support `Subscription`. Use it without a simultaneous tenant override, matching
the existing Python fix. Load the generated environment; never choose the first
enabled subscription or infer a live endpoint from old evidence.

## 6. Preserve failures and incomplete runs

**Decision**: Append page observations durably, then write a case summary. Missing
initial keyword/hybrid counts, HTTP errors, incomplete indexing, count drift,
unsupported settings, or missing cases cannot become a completed reproduction or
a synthetic empty page.

**Approved refinement (2026-10-30)**: A vector-only control's initial count is
optional. Without it, measure the full `ceil(k/5)` candidate-page budget and
boundaries, label the scan `vector-k`, and leave count/advertised fields null.
Successful measurement completes that control with outcome `not-applicable`,
not a count/pagination classification. Preserve actual counts when returned;
compare available counts for drift without treating null as zero or changing the
scan basis mid-run. This optional-count exception does not override failures or
`service-continuation`, and missing counts alone do not fail overall acceptance.

**Rationale**: The experiment specifically requires failure evidence. Narrow SDK
exception handling may persist the failed observation and propagate the original
failure/nonzero exit; no broad catch, backup query, or catch-and-explain-only fix.
Count-only index checks cannot detect every mutation, so a no-writes assumption
must remain explicit.

**Alternatives considered**: Reject success-shaped default reports, swallowed
throttling, hidden retries, and classifying duplicate-induced gaps as proof of
hybrid recall. Boundary repeats record differences without requiring tied result
ordering to match across languages.

## Resolution

No design clarification remains. Execution dependencies remain real prerequisites:
a usable .NET SDK, a current authorized deployment, indexed fixture availability,
and successful live request capture. None has been substituted with invented
reproduction evidence or a claim that the customer cause is confirmed.
