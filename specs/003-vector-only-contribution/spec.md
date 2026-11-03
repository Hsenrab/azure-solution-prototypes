# Feature Specification: Demonstrate Vector-Only Contributions to Hybrid Search

**Feature Branch**: `feat/search-hybrid-pagination-infra` (existing branch, unchanged)

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "can you improve our data set so we have some result from vector that contribute but arent in the keyword search". The user requested Specify after a proposal to retain 6,158 keyword matches, add 25 vector-only documents, and use a separate version-2 fixture/index on the existing service.

**Problem**: Every document in the original fixture matches "maths". Consequently, vector retrieval can change ranking or candidate selection, but cannot demonstrate documents that genuinely do not match the keyword query.

**Hypothesis**: A controlled mixed fixture will show that hybrid search includes documents selected through vector similarity even when those documents do not match the keyword query. It will also make the distinction between keyword matches, retrieved candidates, overlap, and advertised counts observable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Observe Additional Vector Results (Priority: P1)

As an engineer explaining hybrid search to a customer, I want a reproducible dataset with known keyword-only, shared, and vector-only membership so that I can demonstrate that vector retrieval adds documents rather than merely reorders keyword matches.

**Why this priority**: This directly addresses the missing demonstration in the current all-keyword fixture.

**Independent Test**: Against the prepared mixed fixture, collect keyword-only, vector-only, and hybrid results using either existing client. Compare actual returned IDs with the fixture's declared membership. This demonstrates the contribution without requiring the presentation work in User Story 3.

**Acceptance Scenarios**:

1. **Given** the mixed fixture, **When** its contents and intended retrieval membership are validated, **Then** it contains 6,183 unique documents: 6,133 keyword-only, 25 shared, and 25 vector-only.
2. **Given** the unchanged "maths" keyword query, **When** a complete keyword measurement is collected, **Then** it reaches exactly the expected 6,158 keyword IDs and none of the 25 vector-only IDs, with no duplicates.
3. **Given** the fixed vector query and a 50-candidate budget, **When** a complete vector measurement is collected, **Then** the actual result set contains exactly the 25 shared IDs and 25 vector-only IDs, with no duplicates.
4. **Given** the same fixture and query inputs, **When** a complete hybrid scan is collected with the smaller keyword window, **Then** all 25 vector-only IDs are reachable and identified as additional contributions, while exact keyword-window membership is reported only when observed and otherwise explicitly marked "not observed".
5. **Given** a keyword candidate window large enough to include all 6,158 keyword matches, **When** a complete hybrid measurement with retrievable-result counting is collected, **Then** all 6,183 expected IDs are reachable, including the 25 vector-only IDs.

---

### User Story 2 - Preserve the Original Reproduction (Priority: P1)

As an engineer investigating the original pagination discrepancy, I want the new experiment isolated from the original fixture and evidence so that I can still reproduce and review the original findings.

**Why this priority**: Changing the original index in place would invalidate its use as an unchanged historical baseline and obscure which dataset produced a result.

**Independent Test**: Validate both fixture identities, verify the original stored evidence remains byte-unchanged, and check that the original notebook journey still resolves the original fixture and index. These preservation checks do not require completing new live measurements.

**Acceptance Scenarios**:

1. **Given** original fixture files, evidence, and an existing original index, **When** the mixed fixture is generated or prepared, **Then** none of those original artifacts or index contents are modified or deleted.
2. **Given** the original and mixed experiments, **When** either is selected through its notebook journey, **Then** its fixture and target index are explicit and the original journey remains usable without migration to the mixed fixture.
3. **Given** saved results from different fixture versions or indexes, **When** a matched-input comparison is requested, **Then** the mismatch is reported and the results are not presented as equivalent-input measurements.
4. **Given** an absent service or unavailable prerequisites, **When** mixed-fixture preparation is attempted, **Then** it stops without automatic provisioning, deletion, credential changes, or changes to the original index.

---

### User Story 3 - Explain Membership and Count Scope (Priority: P2)

As an engineer reviewing the experiment with a customer, I want a concise notebook comparison showing actual group membership, example documents, and count scope so that I can explain why hybrid results can include non-keyword documents.

**Why this priority**: The evidence needs to distinguish genuine vector-only additions from keyword documents that merely fall outside a smaller keyword ranking window.

**Independent Test**: Render the explanation from complete saved mixed-fixture measurements and inspect the resulting groups, examples, and counts without issuing replacement searches.

**Acceptance Scenarios**:

1. **Given** saved mixed-fixture results, **When** their comparison is rendered, **Then** it shows keyword-only, shared, and vector-only IDs and totals, and at least three examples of vector-only document text returned by hybrid search.
2. **Given** a document that matches "maths" and is returned through vector retrieval, **When** its membership in the smaller keyword candidate window is not exposed by the measured response, **Then** it is described as a full-keyword/vector shared candidate with window membership "not observed", not as a vector-only document or a proven outside-window contribution.
3. **Given** the smaller-window and expanded-window hybrid scenarios, **When** the comparison is rendered, **Then** it shows actual advertised count, total rows, unique reachable IDs, duplicates, populated and empty advertised pages, and results beyond the advertised range, keeping match scope separate from candidate scope.
4. **Given** a missing, failed, or incomplete control or scan, **When** the report is rendered, **Then** it identifies the gap, retains the available evidence, and does not assert complete coverage, accurate counts, or successful causal acceptance.

### Edge Cases

- A nominally vector-only document matches the actual keyword query because its text unexpectedly contains a matching token: fixture membership validation fails.
- Similarity ties at the vector selection boundary admit a keyword-only document or omit an intended member: actual membership fails acceptance; observed results must not be relabeled to fit the target groups.
- A shared document matches the keyword query but its smaller-window membership is not exposed: its full-query group remains shared, and window membership stays "not observed".
- Keyword paging returns duplicates or misses expected IDs: the keyword control remains incomplete, even if its reported count is 6,158.
- Hybrid paging omits an expected vector-only ID, returns duplicate IDs, or changes counts across requests: the report identifies the inconsistency instead of claiming the hypothesis passed.
- A short or empty response includes continuation information: retain the response and mark the scan incomplete, rather than interpreting it as exhaustion.
- A vector-only response omits its initial count: retain the existing bounded-candidate measurement policy; do not invent a count or treat missing count alone as failed retrieval.
- Following-page probes return results beyond the advertised range: do not claim that advertised counts align with reachable results.
- The new target index already contains unexpected documents, or the fixture identity differs from the requested experiment: stop without silently clearing, replacing, or mixing data.
- Concurrent writes or an interrupted run undermine completeness: retain incomplete evidence. Equal starting and ending indexed counts are not proof of snapshot isolation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST extend the existing Search pagination demo to test vector-only contributions, with no customer data or new embedding dependency.
- **FR-002**: The mixed fixture MUST contain exactly 6,183 unique, reproducibly generated documents with declared ID sets for 6,133 keyword-only, 25 shared, and 25 vector-only members.
- **FR-003**: Exactly 6,158 documents MUST match the unchanged "maths" keyword query. The 25 vector-only documents MUST not match that query; their text MUST be available for the explanation.
- **FR-004**: For the fixed vector query, the intended top-50 membership MUST be exactly the 25 shared and 25 vector-only documents, with a clearly separated selection boundary. Actual retrieved membership MUST be verified rather than inferred from the declaration.
- **FR-005**: Group labels MUST be defined for this fixed query and candidate budget, not presented as permanent properties of documents under every possible query. Synthetic vector proximity MUST NOT be described as proof of semantic understanding.
- **FR-006**: The mixed fixture MUST have a distinct version, identity, and target index on the existing service. Original fixture files, original index data, saved measurements, and their existing notebook journeys MUST be preserved.
- **FR-007**: Preparation MUST validate fixture membership and target identity, require successful preparation and the exact indexed total before measurement, and stop on missing prerequisites or unexpected target data. It MUST NOT automatically provision a service, overwrite the original index, or delete unexpected data.
- **FR-008**: The two existing independent measurement clients MUST consume the same declared mixed fixture and verify keyword membership against its expected keyword ID set, rather than assuming that every indexed document is a keyword match.
- **FR-009**: Existing retrieval settings, authentication, network behavior, service capacity, setup, and cleanup journeys MUST remain unchanged. The experiment MUST retain five-result pages and the fixed 50-candidate vector query.
- **FR-010**: The existing stable/default and configured preview hybrid scenarios MUST be usable with the mixed fixture. The smaller scenario MUST retain a 1,000-document keyword window; the expanded scenario MUST include all 6,158 keyword matches. These experiments MUST remain labeled as different count/recall configurations, not an isolated client-package comparison.
- **FR-011**: The feature MUST measure actual full keyword/vector intersection, hybrid membership, and the 25 vector-only contributions. Exact keyword-window membership MUST be reported only when directly observed and otherwise explicitly marked "not observed"; it MUST NOT be inferred solely from declared full keyword membership, equal result counts, or a separate reference query.
- **FR-012**: The feature MUST preserve complete advertised scans, applicable bounded vector scans, selected repeated boundaries, actual request evidence, count drift detection, duplicate/missing-ID detection, and failure/continuation policies from the existing experiment.
- **FR-013**: The comparison MUST distinguish indexed document count, full keyword membership, vector candidate membership, hybrid unique reachability, and advertised count. It MUST separately report membership differences and count-alignment findings.
- **FR-014**: A count-alignment claim MUST require complete valid evidence, no duplicate IDs or empty advertised pages, agreement between the advertised count and unique reachability, and no results in the applicable beyond-advertised boundary probes.
- **FR-015**: The notebook explanation MUST show at least three identified vector-only hybrid results with their document text, the group totals, and the actual differences between smaller and expanded recall.
- **FR-016**: Each run MUST bind results to its fixture, index, query settings, client identity, and measurement completeness. Incompatible fixtures MUST NOT be silently combined as matched-input cases; existing case evidence MUST NOT be overwritten.
- **FR-017**: The notebook journey, related demo documentation, and metadata MUST explain the mixed fixture, expected versus observed membership, isolation from the original experiment, and known limitations without duplicating repository-wide procedures.
- **FR-018**: The feature MUST NOT close or weaken the original failed keyword-control acceptance requirement. A failed new control likewise MUST remain explicit; successful vector-only demonstrations do not erase incomplete controls.
- **FR-019**: Creating this specification MUST NOT initiate live preparation, measurement, provisioning, or deletion. Any later live preparation of the additional index requires explicit execution approval.

### Key Entities *(include if feature involves data)*

- **Mixed fixture**: A versioned synthetic dataset with 6,183 documents, reproducible identity, expected membership sets, a fixed query, and a separate target index.
- **Synthetic document**: A stable ID, displayable text, and synthetic vector; its expected membership is defined relative to the fixed keyword/vector queries.
- **Membership group**: One of keyword-only, shared, or vector-only, with declared IDs and separately verified observed membership.
- **Measurement case**: A fixture-bound keyword, vector, or hybrid retrieval case containing actual requests, page observations, counts, returned IDs, and completeness.
- **Contribution comparison**: A local explanation derived from saved evidence that distinguishes genuine non-keyword additions, ranking-window contributions, overlap, coverage, and count scope.
- **Original baseline**: The preserved version-1 fixture, target index, notebook journey, and historical evidence whose acceptance status is not changed by this follow-on.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two independent local generations produce identical mixed-fixture contents and identity, with exactly 6,183 unique documents and the declared 6,133/25/25 group split.
- **SC-002**: Both existing independent clients complete keyword controls with exactly the expected 6,158 IDs and vector controls with exactly the expected 50 IDs, including 25 vector-only IDs, with zero duplicate or unexpected IDs.
- **SC-003**: Every completed required hybrid scenario reaches all 25 vector-only IDs and reports them as non-keyword additions. Full-keyword/vector shared candidates are identified separately; their smaller-window membership is explicitly "not observed" when the measured response does not expose it.
- **SC-004**: The expanded-recall, retrievable-count scenario reaches all 6,183 expected IDs with 6,183 advertised results, 1,237 populated five-result pages, zero empty advertised pages, zero duplicates, and no positive following-page probe. Its final advertised page contains three results.
- **SC-005**: For every comparison case, a reviewer can inspect declared versus observed membership, actual advertised count, unique reachability, duplicates, page coverage, and missing or incomplete evidence; all three membership groups and at least three vector-only text examples are visible in the notebook explanation.
- **SC-006**: Original stored fixture and measurement files remain byte-unchanged after new-fixture preparation and measurement, original index contents remain unchanged, and the original notebook journey remains usable against version 1.
- **SC-007**: Missing/inconsistent fixture identity, unexpected indexed data, failed controls, interrupted scans, and continuation-bearing partial pages are explicitly identified and never reported as a completed successful experiment.

## Assumptions

- The user selected the proposed 6,183-document mixed fixture and separate target index; updating the original index in place is not the chosen approach.
- The intended users are engineers running a lightweight notebook-led demonstration, not end users of a production search application.
- Existing service access and keyless identity constraints remain authoritative. An absent service is a blocker, not implicit approval to recreate paid resources.
- The original query, vector dimensions, similarity setup, retrieval modes, and page-observation contract remain available from the existing demo. Exact client/package choices remain those of the existing experiments and are not redesigned by this specification.
- The 25 shared documents are members of the full keyword match set and vector top 50; this does not guarantee that they are inside the smaller keyword ranking window.
- During planning, the user explicitly approved marking exact smaller-window membership "not observed" rather than adding diagnostic queries or pretending a separate keyword request proves the hybrid query's internal candidates.
- The feature demonstrates controlled synthetic retrieval, not embedding quality, natural-language semantic relevance, a production-support decision, or a general guarantee that all keyword matches are pageable in any hybrid query.
- Original duplicate/missing-ID observations remain a known limitation. Correcting their underlying cause, adding explicit sorting or ranking weights, and changing original acceptance outcomes are separate work.
- Index writes occur only during separately approved preparation, and the selected fixture remains unchanged throughout measurement. Historical comparisons do not provide snapshot isolation.
- Detailed generation design and notebook wiring belong to the planning phase. The repository's [constitution](../../.specify/memory/constitution.md), [Copilot guidance](../../.github/copilot-instructions.md), and [authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md) remain applicable.
- This feature depends on [the original reproduction feature](../002-reproduce-hybrid-pagination/spec.md) and its existing [demo](../../demos/search02-hybrid-pagination/README.md); it is a separate follow-on and does not amend that feature's acceptance criteria.
