# Implementation Plan: Vector-Only Hybrid Contributions

**Branch**: `feat/search-hybrid-pagination-infra` (unchanged) | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Feature directory**: `specs\003-vector-only-contribution`

**Input**: Approved mixed-fixture specification, including the planning clarification that unavailable internal keyword-window membership is explicitly "not observed".

## Summary

Extend the existing Search pagination demo with a deterministic version-2 fixture: 6,133 keyword-only documents, 25 full-keyword/vector shared documents, and 25 vector-only documents. Preserve the original fixture, index, evidence, and notebook journeys.

The root change is in shared fixture/measurement consumers, not Bicep: indexed cardinality, keyword membership, and vector expectations must no longer be conflated. Both independent stable clients consume the same validated manifest; the existing Python preview scenarios use the new run's stable baseline. Add one notebook and one local contribution renderer to explain actual non-keyword additions.

This plan defines implementation work; it does not implement or run it. Preparation of the additional index remains separately approved. Original keyword duplicate/missing-ID failures remain unresolved.

## Technical Context

**Language/Version**: Existing Python 3.11+ code, currently exercised on 3.12.10; existing C#/.NET 10 console runner.

**Primary Dependencies**: Stable Python Search 12.0.0, Identity 1.25.3, and existing notebook/management dependencies; .NET Search 12.0.0 and Identity 1.21.0 with the existing lockfile. Isolated Python preview Search 12.1.0b2 remains unchanged. No new dependency.

**Storage**: One additional data-plane index `hybrid-pagination-mixed-v2` on the existing keyless service; versioned local JSONL corpus, manifest, preparation evidence, append-only observations, and local reports under existing generated-output exclusions.

**Testing**: Existing local validator/unittest approach, focused Python/runtime and offline transport checks, locked .NET restore/build, original-evidence regressions, notebook syntax and configured pre-commit hygiene. Actual mixed membership/count acceptance requires separately approved live execution.

**Target Platform**: Windows/PowerShell, existing demo notebook kernel and subscription-aligned generated environment; existing Basic Search service without redeployment, new roles, or key authentication.

**Project Type**: Notebook-led Azure debugging demo with two independent stable CLI clients and an isolated Python preview comparison.

**Performance Goals**: Deterministic local generation at this small scale; preparation retains 500-document upload batches. Measurement remains sequential with retries disabled and actual advertised-offset coverage. Under expected counts, all eight cases require roughly 6,400 primary requests plus inventory/boundaries and can take tens of minutes; no unmeasured latency guarantee.

**Constraints**: Preserve version-1 bytes/defaults, original index write isolation, ID-only measured responses, fixed query/vector dimensions, `k=50`, five-result pages, no semantic ranking/filter/explicit measured ordering or weights. No diagnostic attribution queries, package changes, hidden-vector readback claim, automatic service recreation, or deletion.

**Scale/Scope**: 6,183 mixed records, eight required case slots, three membership groups, at least three vector-only text examples, one additional notebook. No generalized fixture framework, UI, new model, or cleanup workflow.

## Constitution Check

*GATE: Must pass before Phase 0 research. Rechecked after Phase 1 design.*

| Gate | Pre-design assessment | Post-design assessment |
|---|---|---|
| Existing guidance/skills | Plan and Azure Demo Authoring apply; repository constitution and authoring references loaded | Existing guidance, notebook metadata workflow, and pre-commit remain authoritative; relevant references linked below |
| Lightweight hypothesis | Test genuine vector-only contribution, not production search architecture | One fixed mixed fixture, existing clients/environments, one renderer/notebook; no new framework or dependency |
| Infrastructure-first | No platform/authentication/network/capacity change requested | Bicep unchanged; index-name/data changes are SDK data-plane operations consuming deployed behavior |
| Global/root-cause scope | Multiple clients conflate all-record and keyword expectations | Shared Python fixture/inspection logic and independent .NET validation change together; no single-cell workaround |
| Hard constraints/approval | Existing keyless identity/environment flow and original index must remain intact | Only the new target may be prepared, with separate live approval; no missing-service fallback |
| Notebook standards | Existing canonical setup/destroy and original reproduction journeys retained | Small purpose-headed new notebook; original kernel invokes existing preview subprocess environment |
| Evidence/quality gates | Original baseline failure cannot be waived | Exact membership, incomplete-control policy, unknown window membership, and count-alignment conditions carried into contracts/checks |
| Preview/model guidance | Existing explicit preview configuration, no new Foundry resource/model | Preview marked `[PREVIEW]`; no production/GA claim or unnecessary model/API upgrade research |

**Gate result**: PASS before research and after design. No constitutional exception is requested. The user explicitly approved the observability clarification; no unresolved design clarification remains.

Applicable sources: [constitution](../../.specify/memory/constitution.md), [Copilot instructions](../../.github/copilot-instructions.md), [authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md), [Foundry standards](../../.github/skills/azure-demo-authoring/references/azure-ai-foundry.md), [notebook workflow](../../.github/workflows/notebook-metadata-check.yml), and [pre-commit](../../.pre-commit-config.yaml). No Foundry model/resource changes are in scope.

## Project Structure

### Documentation (this feature)

```text
specs\003-vector-only-contribution\
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts\experiment.md
  checklists\requirements.md
  tasks.md                         # next phase; not created by Plan
```

### Source Code (repository root; planned changes)

```text
demos\search02-hybrid-pagination\
  app\
    fixture.py                     # explicit versions 1/2; preparation/readiness
    reproduce.py                   # manifest-derived counts/expected sets
    compare.py                     # common version-aware evidence inspection
    preview.py                     # same-fixture baseline and keyword-sized recall
    contributions.py               # new local eight-case contribution renderer
    dotnet\Program.cs              # independent v1/v2 validation and summaries
  notebooks\06_vector_contributions.ipynb
  scripts\validate_local.py         # directly related focused checks; gates retained
  README.md
  metadata.json
  docs\architecture-notes.md
  outputs\generated\reproduction\
    fixtures\mixed-v2\              # new fixture/preparation evidence
    mixed-runs\<run-id>\            # new cases/reports
```

**Structure Decision**: Extend the existing self-contained demo. Preserve the current `fixture`, `runs`, and `preview-runs` paths, original notebooks, package manifests/lockfile, and infrastructure. No source files are created or edited during Plan.

## Phase 0: Research Decisions

[research.md](./research.md) resolves the fixture geometry, versioned expectations, index preparation/reuse boundary, hidden-vector limitation, count semantics, and internal-window observability.

Offline arithmetic validated the proposed top-50 membership and a cosine cutoff margin of approximately 0.318562. Public-doc research confirms that recall controls candidate eligibility, count mode controls reporting scope, and full keyword membership does not reveal smaller-window membership. Actual service outcomes remain acceptance measurements, not research results.

## Phase 1: Design and Integration

### 1. Versioned fixture without baseline migration

Extend `generate`/the existing CLI with `fixture-version` defaulting to 1. Version 1 retains exact original rules and bytes. Version 2 uses the [data model](./data-model.md), the new approved index name, and explicit group membership.

Keep existing public version-1 defaults/imports needed by notebooks. Shared consumers resolve a validated version before obtaining schema, target name, total IDs/count, keyword IDs/count, and optional expected vector IDs. Reject unknown or inconsistent manifests before any Azure write.

### 2. Preparation and read-only reuse

Only an absent or empty correctly defined version-2 target can be populated. Use SDK operations scoped to that target, with all upload results checked. Persist preparation evidence; a completed matching receipt and schema/count/ID-content checks gate reuse.

ID/content inventory uses the existing sortable ID and normal text retrieval; it is explicitly outside measured-case contracts. Vectors remain non-retrievable. A populated target is not upserted or silently repaired by preparation; measuring an already prepared target skips that operation.

A completed upload with indexing still pending must be distinguishable from failed/incomplete uploads. The read-only readiness operation may finalize the receipt only after every upload succeeded and schema/count/inventory now pass; it never reuploads or converts a failed upload to success.

### 3. Both clients and existing inspectors

Python summaries/classification/readiness must use manifest total count and expected keyword IDs instead of global `COUNT` assumptions. The .NET runner independently validates both deterministic recipes and derives the same distinct expectations rather than its fixed `Records` set.

Inspectors validate each report's version-specific schema, allowed corpus IDs, package/API/request profile, summaries, and completeness. Version-2 vector membership failures are explicit; version-1 vector behavior remains measured, not newly predeclared.

### 4. Preview remains a same-fixture comparison

Keep two configured preview scenarios and current package/API pins. Derive expanded recall from the expected keyword ID count, 6,158, not the total index count, 6,183. Bind baseline and preview evidence to the same mixed fixture/index/environment; never reuse an original version-1 baseline for this comparison.

### 5. Contribution presentation

The new local renderer consumes the eight slots in [the interface contract](./contracts/experiment.md), using common inspection rather than duplicating page logic. Derive actual full-query overlap only from complete valid controls; show expected groups separately when controls are incomplete.

Current responses do not expose exact internal text-window membership: report `not-observed` with null IDs. Example text comes from the verified local fixture for IDs actually returned by hybrid, preserving ID-only measured queries. No reference/debug requests, relevance changes, or synthetic examples are added to measured evidence.

### 6. Validation and acceptance

[quickstart.md](./quickstart.md) carries SC-001 through SC-007 into local and live validation. Preserve old evidence hashes, reject cross-fixture/target/overwrite mistakes, prove both version-2 controls, collect all eight cases, and verify 25 additional vector-only IDs plus the expanded 6,183-ID result.

A case/control failure remains visible and blocks full acceptance. The original T029 is not completed by this feature. Existing original-notebook kernel metadata can independently fail the full validator; report it without rewriting that notebook or weakening its hygiene gate.

## Complexity Tracking

No constitution violations. The only retained compatibility is the explicitly required original fixture/journey preservation. Two fixed versions inside existing helpers are sufficient; a fixture registry, pluggable providers, new service, embedding model, test framework, and diagnostic-query pipeline are rejected as unnecessary.
