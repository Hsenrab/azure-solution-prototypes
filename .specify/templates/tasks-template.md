---
description: "Minimal implementation and verification tasks for a prototype"
---

# Tasks: [FEATURE NAME]

**Required input**: [spec.md](./spec.md), [plan.md](./plan.md)

**Optional context**: Read research.md, data-model.md, contracts/, or quickstart.md
only if present and relevant. Do not create these just to generate tasks.

## Scope and Format

- Include only work needed to prove or disprove the agreed hypothesis.
- Use `- [ ] T001 [P?] [US1?] Description with exact file path`.
- Assign sequential task IDs; keep existing IDs when updating a task list.
- Use `[P]` only for independent tasks on different files; story labels refer to
  existing spec stories and are not needed for shared work.
- Use `demos/<demo-name>/` and the existing notebook/infra layout. No default
  root-level application scaffolding, foundational layers, or polish phase.
- Preserve the plan's copy/reuse choices. Name source files/cell headings and
  necessary substitutions instead of rewriting working code.
- Numbered phases are optional; add them only to clarify actual dependencies.

## Implementation

<!--
Replace these placeholders with the actual minimal work. Remove inapplicable
tasks; do not add setup, models, services, hardening, or tooling to fill sections.
-->

- [ ] T001 [US1] [Smallest change or copy from the plan's source to demos/<demo-name>/<destination>; list necessary substitutions]
- [ ] T002 [Update directly related demos/<demo-name>/README.md and metadata.json only where affected]

## Verification

Verification is required; new automated test files are optional. Follow the
[verification guidance](../../.github/skills/speckit-plan/SKILL.md#verification-required-automated-test-suites-optional).

- [ ] T003 [US1] [Run demos/<demo-name>/notebooks/<scenario>.ipynb and check specific expected outputs per SC-001; state prerequisites and paid operations]
- [ ] T004 [Run the smallest relevant existing checks, retaining CI/notebook hygiene gates]

<!--
One notebook run may cover several acceptance criteria. Add focused automated
test tasks only if requested or justified in the plan for nontrivial logic.
Do not introduce a test framework, coverage target, or TDD by default.
When reporting results, distinguish passed, failed, blocked, and not-run checks.
Do not mark blocked verification complete.
-->

## Dependencies

[List only actual dependencies. Implementation normally precedes scenario
verification; notebook steps may depend on earlier setup and deployment.
Do not invent parallel execution examples or independent MVPs.]
