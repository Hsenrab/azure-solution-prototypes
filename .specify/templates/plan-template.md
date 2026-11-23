# Implementation Plan: [FEATURE]

**Branch**: `[branch-name]` | **Date**: [DATE] | **Spec**: [link]

## Summary

[Smallest technical approach that tests the spec's hypothesis]

## Technical Context

- **Demo**: `demos/<demo-name>/` [existing demo, or new demo from demo-template/]
- **Language/runtime and dependencies**: [Reuse existing; list only relevant additions]
- **Services and hard constraints**: [Relevant Azure services, identity/network
  constraints, API/SDK compatibility, and cost implications]

## Constitution Check

Check before research/design and again after design. Record only applicable
decisions and links, not copies of reusable procedures.

- [ ] Copilot guidance and applicable authoring skill/references followed
- [ ] One problem/hypothesis; minimal scope and dependencies; demo self-contained
- [ ] Bicep-first platform changes; existing identity/network constraints preserved
- [ ] Significant strategy changes or exceptions explicitly approved by the user
- [ ] Notebook journey and setup/destroy standards preserved where applicable
- [ ] Hypothesis validation and existing CI/notebook hygiene gates preserved

## Files and Implementation Steps

<!--
Use the existing demo layout. List only changed files and required steps for an
extension. New demos start from demo-template/ and the standard notebook sources.
Do not introduce root-level src/, frontend/, or backend/ scaffolding by default.
Search other demos first. Prefer copying compatible working cells, helpers, and
Bicep as-is with minimal substitutions; do not introduce cross-demo abstractions
just to avoid duplication. Follow the plan skill's reuse guidance.
-->

1. `[demo-relative file path]`: [Smallest required change; identify any reused source
   file/cell heading and necessary substitutions, or why suitable code is not reused]
2. `[directly related docs/metadata path]`: [Update needed, if scope changes]

## Validation

Verification is required; a new automated test suite is not. Default to running the
notebook scenario and checking expected outputs. Follow the
[verification guidance](../../.github/skills/speckit-plan/SKILL.md#verification-required-automated-test-suites-optional).

- **Acceptance evidence**: [Map spec success criteria to observable notebook outputs]
- **Checks**: [Smallest relevant existing checks and notebook scenario; retain CI/hygiene gates]
- **New automated tests (optional)**: [Only if requested or specific nontrivial
  introduced/fixed logic warrants them; explain why, otherwise omit this item.
  Do not invent coverage targets or require a new test framework.]
- **Prerequisites and paid operations**: [Azure access/resources and calls needed]
- **Run instructions**: [Link to the demo README/notebook; do not duplicate setup]
- **Evidence status**: [What actually ran, what is planned, and what is blocked]

## Decisions and Open Questions

[Only unresolved blockers or significant choices: decision, rationale, and sources.
Include concise trade-offs and approval status for significant strategy changes.
Remove this section if there are none.]

<!--
plan.md is the only required planning output. Add research.md, data-model.md,
contracts/, or quickstart.md only if substantial findings, nontrivial data rules,
new/changed interface agreements, or a distinct run guide warrant them.
Do not create empty artifacts or duplicate existing demo documentation.
-->
