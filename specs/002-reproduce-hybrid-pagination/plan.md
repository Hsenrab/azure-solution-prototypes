# Implementation Plan: Reproduce Hybrid Search Count/Pagination Discrepancy

**Working branch**: `feat/search-hybrid-pagination-infra`
**Spec Kit feature**: `002-reproduce-hybrid-pagination`
**Date**: 2026-10-28
**Refined**: 2026-10-30 (optional vector counts and short-response continuation)
**Spec**: [Feature 2](./spec.md)
**Status**: Implemented and all six cases measured; overall live acceptance remains
blocked by keyword duplicate/missing IDs. See [actual outcomes](./spec.md).

## Summary

Extend the existing Search demo with one notebook-led experiment. Generate exactly
6,158 synthetic keyword matches and fixed vectors, populate one shared index, and
independently scan keyword-only, vector-only, and hybrid cases using Python and
.NET. Compare reported counts with unique reachable IDs, every advertised page,
and repeated boundary observations.

**Hypothesis**: A hybrid count can describe more matching documents than the
distinct candidates available for paging. Treat this as a hypothesis, not a
confirmed SDK defect or a promise to reproduce the customer's 257-page boundary.

The user approved one additional reproduction notebook, a small independent .NET
console client, stable SDKs pinned to a common API, and no new infrastructure or
test framework. Beta remediation, distance sorting, production approval, and
release-roadmap advice remain outside this feature.

## Technical Context

- **Languages**: Python 3.11+ in the existing demo environment; C# targeting
  `net10.0`, requiring a .NET 10 SDK.
- **Python dependencies**: Reuse the existing pins, including
  `azure-search-documents==12.0.0` and `azure-identity==1.25.3`; standard-library
  generation, hashing, and reporting. No additional Python package is planned.
- **.NET dependencies**: `Azure.Search.Documents` 12.0.0 and `Azure.Identity`
  1.21.0; built-in JSON/file support. Pin direct versions and retain a NuGet
  lock file when implementation restores the project.
- **Service API**: Explicit `2025-09-01` for both data-plane clients. Independently
  verified package choices and paging details are in [research](./research.md).
- **Storage**: One index in Feature 1's Search service; generated local fixture
  and evidence under the demo's already ignored generated-output directory.
- **Authentication**: Existing setup user through `AzureCliCredential`, selecting
  the exported subscription without simultaneously passing a tenant override.
  Preserve disabled shared keys, existing roles, and public endpoint configuration.
- **Platform/interface**: VS Code notebooks on the existing Windows workflow;
  standalone language runners over the same files/index, not a hosted application.
- **Validation**: Scenario measurements plus existing notebook hygiene and targeted
  local checks; no new unit-test framework or synthetic success evidence.
- **Scale/performance**: 6,158 documents, 16-dimensional vectors, `k=50`, five
  results per page. Sequential requests; complete coverage, not a latency target.
  Expect several thousand reads; do not cap or sample advertised pages.
- **Prerequisite limitation**: Planning found `dotnet` but no SDK in
  `dotnet --list-sdks`. Document the SDK prerequisite; do not call the .NET
  experiment validated or install tooling during planning.

## Constitution Check

Pre-research and post-design gates both pass:

| Principle | Design evidence |
|-----------|-----------------|
| Existing guidance stays active | Loaded Azure Demo Authoring and Spec Kit planning; consulted the [workflow](../../.github/skills/azure-demo-authoring/references/workflow.md), [Foundry reference](../../.github/skills/azure-demo-authoring/references/azure-ai-foundry.md), and [constitution](../../.specify/memory/constitution.md). Foundry/model changes are not applicable. |
| Lightweight, hypothesis-driven | Extend only `demos/search02-hybrid-pagination`; one index, one hypothesis, no UI/model service or generic framework. |
| Bicep-first, root-cause scope | No platform behavior changes are required. Leave Feature 1 Bicep/authentication/network settings unchanged. Index and query operations belong to the Search data-plane SDKs. |
| Notebook journey | Retain canonical setup/destroy and existing infrastructure readiness; append the user-approved reproduction notebook. Small cells orchestrate reusable experiment code and the independent .NET client. |
| Evidence and quality gates | Preserve existing CI/pre-commit checks; validate the actual six measurements and comparison. Failures are not empty pages; not-reproduced is a valid result. |

No constitutional exception or temporary infrastructure workaround is required.
This is experimental instrumentation, not a fix for the customer's service
behavior. Narrow request-failure recording is required evidence, not a
catch-and-explain substitute for remediation.

## Project Structure

### Planning artifacts

- [Research](./research.md): version, retrieval, paging, and scope decisions.
- [Data model](./data-model.md): fixture, index, observations, and findings.
- [Local interface contract](./contracts/experiment.md): runner inputs and evidence.
- [Quickstart](./quickstart.md): future end-to-end execution and acceptance.
- [Tasks](./tasks.md): implementation and actual validation checklist.

### Planned implementation inside the existing demo

```text
demos/search02-hybrid-pagination/
  notebooks/
    00_setup.ipynb              # retain canonical flow
    01_deploy_infra.ipynb       # retain infrastructure/output export
    02_configure.ipynb          # explain readiness-before-reproduction handoff
    03_test.ipynb               # retain initial infrastructure-only readiness
    04_reproduce.ipynb          # prepare, run both clients, compare
    X_destroy.ipynb             # retain canonical cleanup
  app/
    notebook_helpers.py        # reuse environment contract/resolver
    fixture.py                 # deterministic fixture and SDK index population
    reproduce.py               # independent Python queries and evidence
    compare.py                 # aggregate/compare, never issue replacement queries
    dotnet/
      HybridPagination.csproj
      Program.cs               # direct .NET Search SDK queries
      packages.lock.json
  outputs/generated/
    reproduction/              # ignored fixture, schema, per-run evidence
  README.md
  docs/architecture-notes.md
  metadata.json
```

App code is justified by independently executable clients and shared reporting;
do not put thousands of requests or large result arrays directly in notebook cells.
This approved tree is implemented. No infrastructure or canonical notebook change
was required.

## Execution Design

1. **Load prerequisites**: Read Feature 1's generated environment, verify the
   selected setup-user context, and check Python/.NET versions before mutations.
   Do not assume a historical deployment still exists or redeploy automatically.
2. **Preserve readiness ordering**: Run existing infrastructure readiness before
   index preparation. Its zero-index/zero-document assertion is an initial
   baseline, not a check to rerun after ingestion. Never delete scenario data
   merely to make that initial assertion pass.
3. **Prepare the fixture/index**: Use the [data model](./data-model.md), batch
   uploads, and validate every indexing result. Verify 6,158 indexed records;
   if indexing is not yet visible, stop explicitly and rerun the readiness
   portion when ready, without an invented empty dataset or hidden fallback.
4. **Freeze inputs**: Both clients consume the same manifest, corpus identity,
   index/schema, and query vector. No writes during scans or boundary repeats.
   Record start/end index counts; acknowledge these are not snapshot isolation.
5. **Run six cases independently**: Keyword, vector, hybrid for each language.
   The [contract](./contracts/experiment.md) defines exact offsets, single-response
   handling, complete scans, repeat requests, and failure evidence.
   Any response with fewer than `top=5` rows plus continuation information stops
   the case as incomplete with reason `service-continuation`; it is not exhaustion
   or reproduction evidence, and no continuation is fetched automatically.
   Keyword/hybrid cases require an initial count. A vector-only control without
   that optional count instead measures all `ceil(k/5)` candidate pages plus
   boundaries, keeps count/advertised fields null, and may complete with outcome
   `not-applicable`. Failures and drift still take precedence over this exception.
6. **Compare**: Recompute metrics from page evidence. A failed keyword baseline,
   input mismatch, missing case, or count drift prevents a complete causal
   comparison. Tied ordering and boundary variation remain visible limitations.
   Disclose vector counts unavailable for comparison and candidate-based versus
   advertised scan coverage; do not fail acceptance solely for an optional missing
   vector count or pretend that `not-applicable` proves no count discrepancy.
7. **Explain and clean up**: Separate observed symptoms from the candidate-window
   hypothesis and customer-parity gaps. Use existing canonical cleanup; do not
   add a second environment or a feature-local destroy workaround.

## Validation and Requirements Coverage

| Coverage | Required evidence |
|----------|-------------------|
| FR-001-003; SC-001 | Deterministic corpus hash; exactly 6,158 unique IDs, all containing the keyword; fixed nonzero vectors; successful upload results. |
| FR-004-008; SC-002 | Six request configurations and durable observations; five-result explicit offsets; 100% advertised-page coverage or the complete count-unavailable vector candidate budget; independent metrics with unavailable counts null. |
| FR-009-010; SC-003-005 | Last populated, following, and final advertised boundaries; two observations per selected offset; explicit classification and failure/count-change handling. |
| FR-011-013; SC-006 | Source-backed hypothesis, overlap accounting, no manufactured 257-page target, and excluded confounders. |
| FR-014 | Reuse deployment outputs and existing setup/readiness/destroy; update demo README, architecture notes, notebook handoffs, and metadata during implementation. |
| FR-015-019; SC-007-008 | Exact versions/API and captured effective requests; independent SDK calls; six actual case reports and one comparison disclosing all mismatches. |

During implementation, build the .NET project and check Python syntax; use the
existing focused validator where applicable, adjusting only obsolete
infrastructure-only scope assumptions. Apply the existing notebook hygiene checks
to changed notebooks. Live acceptance must exercise this exact corpus, page size,
coverage, classification, and report shape; static checks do not prove reproduction.

## Complexity Tracking

No exceptions. No new infrastructure, generic experiment framework, preview
dependency, defensive fallback path, or additional test framework is planned.
