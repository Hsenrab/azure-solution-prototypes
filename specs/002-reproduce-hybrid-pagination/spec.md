# Feature Specification: Reproduce Hybrid Search Count/Pagination Discrepancy

**Feature Branch**: `feat/search-hybrid-pagination-infra` (shared working branch;
Spec Kit feature identity: `002-reproduce-hybrid-pagination`).

**Created**: 2026-10-23

**Status**: Implemented; live symptom reproduced in both clients. Full acceptance
remains blocked by failed keyword complete-ID baselines (T029), not missing clients.

**Validation record (2026-10-30)**: All six cases measured in ignored local run
`demos/search02-hybrid-pagination/outputs/generated/reproduction/runs/20261030-live-v2/`.
Both hybrid cases: count 6,158, 1,039 unique IDs, 208 populated and 1,024 empty
advertised pages. Both vector cases: count/unique 50. Both keyword cases: 6,158
rows, 6,111 unique IDs, 100% advertised-offset coverage; duplicate/missing IDs
invalidate the required baseline. Actual requests/API and cross-client ID sets
agreed. This establishes the symptom, not the customer cause or exact boundary.
No data/sort change was made to force acceptance. See the demo's
[validation record](../../demos/search02-hybrid-pagination/README.md#feature-2-live-observations---2026-10-30).

**Depends On**: [Feature 1 - Provision Search Debug Environment](../001-provision-search-debug/spec.md).

**Input**: Design a standalone Azure AI Search debugging demo using dummy data to
investigate a customer report: searching for "maths" reports 6,158 results and
advertises 1,232 pages at five results per page, but only the first 257 pages
contain results. The user confirmed reproduction and explanation only, examples in
both Python and .NET against the shared environment provisioned by Feature 1, and
deferral of distance sorting.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Measure the Discrepancy Without Customer Data (Priority: P1)

As an engineer investigating the report, I want to compare the reported count with
the documents actually reachable through hybrid-search pages, using a known synthetic
corpus, so that I can establish whether the symptom exists independently of the
customer's UI and private data.

**Why this priority**: Remedy recommendations are premature until the symptom has
been measured directly and distinguished from UI behavior.

**Independent Test**: Run one fixed hybrid search over the complete synthetic corpus,
request every advertised page, and compare its count with the unique returned IDs.
This test delivers a reproduced, not-reproduced, or blocked finding without a UI.

**Acceptance Scenarios**:

1. **Given** a complete, unchanged corpus with 6,158 known keyword matches,
   **When** the engineer searches for "maths" with a page size of five,
   **Then** the evidence records the reported count, calculated page count,
   returned document IDs and size of every requested page, and unique reachable count.
2. **Given** the advertised pages have been inspected,
   **When** the reported count exceeds the unique reachable count and at least one
   advertised page is empty, **Then** the run is classified as reproducing the symptom.
3. **Given** all advertised results are reachable without unexpected empty pages,
   **When** the run is summarized, **Then** it is classified as not reproduced,
   without manufacturing an artificial result limit.
4. **Given** a request fails or indexing has not completed,
   **When** the engineer reviews the result, **Then** the experiment is classified
   as blocked or incomplete, not as a successful reproduction or an empty page.

---

### User Story 2 - Isolate Hybrid Behavior From Other Causes (Priority: P1)

As an engineer, I want keyword-only and vector-only controls against the same
unchanged corpus, so that I can determine whether hybrid candidate retrieval is a
plausible explanation rather than indexing gaps or application pagination logic.

**Why this priority**: A count mismatch alone does not establish its cause.

**Independent Test**: Run and inspect each control independently against the known
corpus and record the count, unique IDs, and page boundaries it actually returns.

**Acceptance Scenarios**:

1. **Given** the complete corpus and keyword-only control,
   **When** all advertised pages are retrieved, **Then** all 6,158 matching IDs
   are reachable across 1,232 pages, with three results on the final page,
   or the investigation reports a failed baseline before attributing a hybrid cause.
2. **Given** a fixed vector query and candidate limit,
   **When** the vector-only control runs, **Then** the evidence records its actual
   returned IDs, reported count when available, and overlap with keyword results.
   If the initial count is unavailable, successful measurement of the configured
   candidate-page budget and boundaries completes the control with outcome
   `not-applicable`; it does not invent an advertised count or block the whole
   demonstration solely because that optional count is absent.
3. **Given** keyword-only, vector-only, and hybrid observations,
   **When** the findings are compared, **Then** the report distinguishes observations
   from hypotheses and states whether the evidence supports the proposed cause.

---

### User Story 3 - Produce a Reusable Customer-Safe Explanation (Priority: P2)

As an engineer discussing the issue with the customer, I want a reproducible evidence
summary with its limitations, so that I can explain what was demonstrated without
claiming an exact reproduction of an unavailable customer configuration.

**Why this priority**: Findings must be useful for escalation and avoid unsupported
claims about SDK defects, preview suitability, or release timelines.

**Independent Test**: A second reviewer can use the recorded corpus identity,
query settings, versions, and page evidence to understand the classification and
repeat the same experiment.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** its summary is reviewed,
   **Then** it includes reported versus reachable counts, advertised versus populated
   pages, boundary evidence, exact settings and versions, and explicit limitations.
2. **Given** the customer package and query are unavailable,
   **When** a generic reproduction succeeds, **Then** the report calls it a reproduction
   of the symptom, not proof of the customer's exact cause or a defect in a named SDK.

---

### User Story 4 - Compare Python and .NET Observations (Priority: P1)

As an engineer, I want both language clients to run equivalent experiments against
one shared index, so that language-specific behavior can be separated from the
service-level count/pagination symptom.

**Why this priority**: The user explicitly requires both clients; assuming equivalent
SDK behavior without comparing effective requests would undermine the explanation.

**Independent Test**: Each client can execute all three query cases independently
against the prepared index and produce the same evidence fields. A reviewer can
compare the two reports without rerunning infrastructure deployment.

**Acceptance Scenarios**:

1. **Given** the same immutable index, query vectors, and equivalent query settings,
   **When** both clients run keyword-only, vector-only, and hybrid cases,
   **Then** six client/query-case reports and one side-by-side comparison are produced.
2. **Given** the clients can target the same service API version,
   **When** their results are compared, **Then** reported counts, unique IDs,
   page boundaries, duplicates, and outcome classifications are compared explicitly.
   Exact ordering of tied scores is not assumed to be identical.
3. **Given** a client cannot express a required setting or target the same API version,
   **When** parity is assessed, **Then** the limitation is reported as an unsupported
   or non-equivalent comparison, not silently replaced with a different query.
4. **Given** results differ, **When** findings are summarized, **Then** the report
   identifies differences in effective requests and versions before alleging an SDK defect.

### Edge Cases

- Zero matches: zero advertised pages, with no division or page-indexing ambiguity.
- Result counts not divisible by five: a partial final page is valid, not an error.
- Duplicate IDs across pages: report total rows and unique IDs separately; duplicates
  must not inflate the reachable-document count.
- An empty intermediate page followed by nonempty pages: record it and continue
  scanning; the first empty page alone does not prove all subsequent pages are empty.
- Equal ranking scores and unstable ordering: flag duplicates, gaps, or repeated-run
  differences as limitations rather than attributing them automatically to recall.
- Index mutation or incomplete ingestion: invalidate the comparison until the fixed
  corpus prerequisite is satisfied.
- Service errors, throttling, or unsupported settings: record a blocked/incomplete
  result; never turn them into empty search results.
- Different client defaults, lazy iteration, or automatic continuation: distinguish
  requested logical pages from additional SDK requests; do not silently compare
  differently shaped requests or count automatic traversal as a five-result page.
- A response with fewer than the requested five rows and continuation information:
  preserve the actual response, stop the case as incomplete with reason
  `service-continuation`, and do not treat it as an exhausted/empty page or
  reproduction evidence. This applies to scans, probes, and repeats in both clients.
- Missing initial count: blocks keyword/hybrid classification. Vector-only controls
  may complete a clearly labeled candidate-limit scan with count/advertised-page
  fields null and outcome `not-applicable`; failures still make them incomplete.
- Multiple vector queries, filters, semantic reranking, and explicit sorting:
  excluded from the initial baseline, and documented as possible customer differences.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The investigation MUST use synthetic records only and require no customer
  documents, customer embeddings, customer credentials, or customer application.
- **FR-002**: The primary fixture MUST contain exactly 6,158 uniquely identified
  records matching "maths", with varied deterministic text and fixed reproducible
  vector values. All fixture records MUST be indexed before comparisons begin.
- **FR-003**: The fixture MUST document its generation inputs, corpus identity,
  matching IDs, and intended keyword/vector overlap. It MUST NOT require an external
  embedding model to investigate pagination rather than semantic relevance.
- **FR-004**: The initial experiment MUST compare keyword-only, vector-only, and
  hybrid queries in both Python and .NET over the same immutable corpus.
  The hybrid query MUST combine the
  keyword query with one fixed vector query. Relevant settings MUST remain unchanged
  across page requests except for the page offset.
- **FR-005**: The hybrid baseline MUST request counts and use five results per page.
  Advertised pages MUST be calculated as the ceiling of reported count divided by
  five, with user-facing page numbers starting at one.
- **FR-006**: The evidence MUST include the full non-secret query configuration,
  client language, exact client package/version, actual service REST API version, index definition,
  vector candidate limit, ordering, and any explicitly set or implicit defaults.
- **FR-007**: Every advertised page MUST be requested for a completed measurement.
  Evidence MUST record its page number, offset, returned size, IDs, reported count
  when present, and any request failure. Scanning MUST NOT stop at the first empty page.
  A short/empty response with continuation information MUST instead stop the case
  as incomplete with reason `service-continuation`, never establish exhaustion,
  and never trigger hidden continuation requests.
- **FR-008**: The summary MUST distinguish reported count, total returned rows,
  unique reachable IDs, duplicate IDs, advertised pages, populated pages, first empty
  advertised page, and last populated page. Count changes during a run MUST be flagged.
- **FR-009**: Boundary evidence MUST show the last populated page, the immediately
  following page, and final advertised page where applicable. The same boundary
  requests MUST be repeated once with unchanged inputs to check repeatability.
  For a vector control without an initial count, use the configured candidate-page
  budget and its final scan page instead of inventing a final advertised page.
- **FR-010**: The report MUST classify the outcome as reproduced, not reproduced,
  or blocked/incomplete, using the acceptance conditions in User Story 1.
  Keyword and hybrid cases require an initial reported count. The sole exception
  is a successfully measured vector-only control without that count: its status
  is `complete`, outcome is `not-applicable`, and reported count and advertised-page
  fields remain null. This exception MUST NOT override any failed/incomplete
  request, count drift, or unfinished required scan/boundary measurement.
- **FR-011**: The explanation MUST assess the hypothesis that counting all keyword
  matches can exceed the distinct hybrid candidate set available for paging.
  It MUST account for text/vector overlap and MUST NOT assume their sizes simply add.
- **FR-012**: The experiment MUST NOT hardcode 257 populated pages as an expected
  outcome or alter data/settings solely to manufacture that exact boundary.
  The original numbers MUST remain customer-reported context, not verified results.
- **FR-013**: The initial baseline MUST exclude UI code, filters, explicit sorting,
  semantic reranking, multiple vector queries, and concurrent writes, so that the
  count/pagination question can be investigated with fewer confounding variables.
- **FR-014**: The eventual reproduction MUST consume Feature 1's deployment outputs
  and use its existing setup, deployment, and cleanup journey, without deploying
  separate infrastructure for each client. This feature MUST own index creation,
  synthetic data generation/population, both clients' query experiments, and their
  related configuration/test documentation and metadata.
- **FR-015**: Findings MUST cite current authoritative guidance, distinguish documented
  behavior from inferred causes, and identify gaps preventing exact customer parity.
  API-version-specific behaviors MUST NOT be generalized to all service versions.
- **FR-016**: Both clients MUST support independent execution of all three query cases
  against the same index and emit equivalent evidence fields. One client MUST NOT
  merely display or wrap the other client's results.
- **FR-017**: The comparison MUST align corpus, index, query text/vector, candidate
  limits, page size/offsets, count request, ordering, and effective service API version
  where supported. Any unmatched settings or defaults MUST be disclosed.
- **FR-018**: The summary MUST present each client/query-case outcome side by side,
  including agreement or disagreement in counts, reachable IDs, and boundaries.
  Cross-client equality MUST NOT be assumed or required to declare the experiment complete.
- **FR-019**: Python and .NET SDK versions MUST be selected and verified independently
  during planning. The same major number MUST NOT be assumed to imply API parity,
  feature availability, or equivalent support status.

### Key Entities

- **Synthetic record**: A stable unique ID, searchable text containing "maths", and
  fixed vector values; no personal or customer data.
- **Corpus fixture**: The immutable collection, expected keyword matches, generation
  inputs, and identity needed to repeat the investigation.
- **Query case**: Client language, keyword-only, vector-only, or hybrid inputs, version information,
  candidate settings, count request, and paging settings.
- **Page observation**: The requested page/offset, returned IDs and size, count,
  and success or explicit failure.
- **Investigation finding**: Aggregated counts, page boundaries, comparison evidence,
  classification, hypothesis assessment, and customer-parity limitations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The baseline accounts for all 6,158 expected keyword IDs, with no
  missing or duplicate IDs; failure is explicitly reported before cause attribution.
- **SC-002**: For each completed query case with an initial reported count, 100%
  of advertised pages have recorded observations, and reported count, unique
  reachable count, and empty-page count can be independently calculated from
  that evidence. A vector-only control without an initial count instead records
  100% of its configured candidate-page budget; count-based fields/coverage stay
  null, while actual rows, unique IDs, and candidate-page metrics remain measurable.
- **SC-003**: A completed hybrid case produces an unambiguous reproduced or
  not-reproduced classification; every failed/incomplete case is distinguished from
  those outcomes.
- **SC-004**: For a reproduced case, the evidence demonstrates both a positive
  reported-minus-reachable count gap and at least one empty advertised page.
- **SC-005**: Boundary observations are repeated twice in total; agreement or
  disagreement is stated explicitly rather than assumed.
- **SC-006**: A reviewer can identify the hypothesis, observed outcome, control
  results, and outstanding customer-parity limitations from one summary without
  accessing customer data or a customer UI.
- **SC-007**: There are six client/query-case reports covering two clients and three
  cases, each with a completed outcome or an explicit blocked/unsupported status.
  Completion of the two-client demonstration requires all six cases to execute;
  unsupported cases remain gaps rather than successful demonstrations.
  A successfully completed vector control with unavailable initial count uses
  `not-applicable` as specified in FR-010 and is not an unsupported or missing case.
- **SC-008**: One comparison accounts for every matched or unmatched query setting
  and states agreement or disagreement for reported counts, unique reachable counts,
  returned ID sets, and page boundaries.

## Assumptions

- The initial specification-only phase created requirements without demo source,
  datasets, or Azure resources. The subsequently approved [implementation plan](./plan.md)
  records the design; planning does not authorize executing or deploying the experiment.
- The user selected reproduction and explanation only. Preview count-scope changes,
  expanded recall comparisons, remediation implementation, production approval,
  GA alternatives, and GA-release timelines are out of scope for this first feature.
- Distance-based sorting is deferred to a separate investigation; whether "distance"
  means geographic distance or vector similarity is not assumed.
- Feature 1 provisions the shared environment using Bicep. This feature adds Python
  and .NET examples, index/data preparation, and experiments; it does not duplicate
  the infrastructure or change its authentication/network policy.
- Python's `azure-search-documents` package has published 12.x releases. The .NET
  package is `Azure.Search.Documents`; its exact version must be verified separately.
  Neither SDK's version number is the service's date-based REST API version.
  Customer-specific package versions and effective service API version remain unknown.
- A service-level symptom reproduction does not require an exact customer SDK match.
  Exact customer parity remains unconfirmed until sanitized query and dependency
  details are available; their absence does not block this standalone experiment.
- Fixed synthetic vectors isolate retrieval/paging mechanics, not embedding quality.
  A real embedding deployment is not necessary for this first hypothesis.
- Later execution depends on an authorized Azure subscription and suitable Search
  service availability. No deployment, paid resource creation, or production usage
  is authorized by this specification-writing step.

### Working Hypothesis and Evidence Limits

The reported total can describe a broader matching population than the finite
keyword/vector candidate set used for hybrid ranking and paging. This could explain
advertised pages with no results, but must be tested rather than declared the cause.
Candidate overlap, query settings, and service/API versions can change the boundary.
The customer report does not establish that exactly 1,285 documents were returned:
257 populated pages at five per page could include a partial final populated page.

### Applicable Repository Guidance

- [Constitution](../../.specify/memory/constitution.md)
- [Copilot instructions](../../.github/copilot-instructions.md)
- [Azure Demo Authoring](../../.github/skills/azure-demo-authoring/SKILL.md)
- [Authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md)
- [Notebook Metadata Check](../../.github/workflows/notebook-metadata-check.yml)

### Initial External References

These references inform the hypothesis, not evidence that this demo has reproduced it.
Support status and exact version behavior must be rechecked during later planning.

- [Hybrid query count scope and text recall](https://learn.microsoft.com/en-us/azure/search/hybrid-search-how-to-query#set-maxtextrecallsize-and-countandfacetmode-preview)
- [Search result counts and pagination](https://learn.microsoft.com/en-us/azure/search/search-pagination-page-layout)
- [Python SDK package](https://pypi.org/project/azure-search-documents/):
  verify Python versions and availability independently of other language packages.
- [.NET SDK package](https://www.nuget.org/packages/Azure.Search.Documents):
  verify .NET versions and capability parity separately.
