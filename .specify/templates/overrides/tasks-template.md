---
description: "Minimal, dependency-ordered tasks for an Azure prototype demo"
---

# Tasks: [FEATURE]

**Inputs**: [Repository-relative links to spec.md and plan.md]

## Task-generation rules

- Include only implementation deltas and directly related documentation/metadata
  recorded in the approved plan. Do not add generic setup, framework, dependency,
  ignore-file, or project-initialization tasks unless the plan requires them.
- Organize work by the smallest dependency-ready implementation slices. Add setup
  or foundational phases only when an actual prerequisite blocks the change.
- Automated test tasks are optional: include them when requested or justified by
  changed logic. Do not assume TDD, test-first, coverage targets, a new test
  framework, or a broad test matrix.
- Include one concise runnable hypothesis-validation journey and applicable
  existing checks. Preserve notebook metadata/pre-commit gates and identify
  Azure-dependent acceptance separately; live operations require explicit approval.
- Preserve canonical setup/destroy flows and generated `env/.env` handoff when
  those artifacts are in scope. Never treat code reuse as permission to touch
  existing live Azure resources.
- Use exact repository-relative paths, respect identity/network/deployment
  constraints, and carry the plan's reuse/adapt/new decisions into the tasks.

## Tasks

- [ ] T001 [P?] [Action and exact path; state the necessary delta.]

## Validation

- [ ] T00N [P?] [Run the plan's hypothesis-validation journey and relevant existing
  checks; state expected observable result and any Azure approval prerequisite.]
