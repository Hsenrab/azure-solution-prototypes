# Implementation Plan: [FEATURE]

**Date**: [DATE] | **Spec**: [repository-relative link]

## Summary

[Restate the hypothesis and the minimal approach that can validate it.]

## Existing sources and reuse decisions

| Source path | Existing behavior / constraint | Decision (reuse unchanged, adapt, do not reuse, or new) | Rationale / delta |
|---|---|---|---|
| [Repository-relative path] | [Evidence from discovery] | [Decision] | [Why and what changes] |

Include only relevant sources: demo template, candidate or target demo Bicep,
notebooks, helpers, scripts, docs/metadata, and prior specs/plans. Do not copy
entire inventories into the plan. Explain why any plausible source is not reused.

## Technical decisions and constraints

- **Demo location**: `demos/<demo-name>/`; keep runtime files self-contained.
- **Infrastructure and platform behavior**: [Bicep-first decision, or why none is needed.]
- **Identity, authentication, and network**: [Existing hard constraints and compatibility.]
- **Deployment, subscription, and live resources**: [Deployment boundaries and explicit
  approval needed, if any. Reusing code does not authorize live-resource reuse or change.]
- **Environment handoff and notebooks**: [Generated `env/.env`, canonical setup/destroy,
  and relevant notebook journey.]
- **Dependencies and architecture**: [Existing choices to retain; justify any necessary
  new dependency or shared behavior.]

## Changed files and validation

| Path | Necessary change | Observable hypothesis check / existing gate |
|---|---|---|
| [Repository-relative path] | [Minimal delta] | [Runnable check or applicable existing quality gate] |

Describe one concise runnable hypothesis-validation journey and its expected
observable result. Separate local/offline validation from Azure-dependent steps;
state the required explicit approval before any live Azure operation. Add
automated tests only when requested or justified by changed logic. Preserve
existing notebook hygiene/CI checks and historical results.

## Deferred artifacts

List only additional research, data-model, contract, or quickstart artifacts that
are necessary to resolve an actual design question or support validation. Otherwise
record `None`; do not create generic application or documentation artifacts.
