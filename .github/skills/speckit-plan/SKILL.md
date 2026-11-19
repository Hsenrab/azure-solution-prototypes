---
name: "speckit-plan"
description: "Plan the smallest prototype change and its validation; create separate design artifacts only when needed."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/plan.md"
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Repository Scope

Apply [the constitution](../../../.specify/memory/constitution.md) and
[the Copilot guidance](../../copilot-instructions.md). For demo creation or extension,
load `azure-demo-authoring` and follow its applicable references before planning.
Use the existing demo layout and preserve its hard constraints. Do not copy
reusable authoring procedures into feature artifacts.

## Pre-Execution Checks

**Check for extension hooks (before planning)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_plan` key
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. **Setup**: Run `.specify/scripts/powershell/setup-plan.ps1 -Json` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, FEATURE_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `.specify/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Check readiness**: A separate `/speckit-clarify` run is not required.
   Ask through `ask_user` only when an unresolved choice changes the hypothesis,
   implementation, cost, or hard constraints. Pause on blocking decisions.

4. **Plan the minimum change**:
   - Fill Summary and Technical Context from the existing demo and agreed spec.
   - Fill Constitution Check with applicable rules and skill/reference links.
     Pause on violations unless the user explicitly approves a documented exception.
   - Resolve only unknowns that block feasibility or implementation (see below).
   - List the files to change and the smallest end-to-end implementation steps.
   - Map the spec's acceptance criteria to the smallest relevant existing checks and
     notebook scenario; distinguish planned checks from evidence already collected.
   - Link existing run instructions rather than duplicate the demo README.
   - Recheck constitution compliance after design. Significant strategy changes
     require concise trade-offs and explicit user approval before implementation.

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_plan`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_plan` key.
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue to the Completion Report.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Mandatory hook** (`optional: false`) — **You MUST emit `EXECUTE_COMMAND:` for each mandatory hook**:
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## Completion Report

Report branch, IMPL_PLAN path, minimal change scope, validation approach, and any
blocking decisions. List supporting artifacts only if they were needed and created.
Do not claim planned checks have run.

## Reuse Working Demo Code First

- Search other demos for suitable notebook cells, helpers, and Bicep before planning
  new code. Prefer copying working code as-is, with only necessary demo-specific
  substitutions, over rewriting it.
- Check that the source code fits the target demo's identity, network, deployment,
  runtime, and dependency constraints. Do not copy incompatible behavior or change
  those constraints merely to enable reuse.
- In the plan, identify the source file/cell heading, destination, and necessary
  substitutions. If suitable existing code is not reused, briefly explain why.
- Keep demos self-contained. Do not refactor or introduce shared cross-demo
  abstractions merely to avoid duplication. Preserve the mandated setup/destroy
  notebook sources and their permitted substitutions.
- Verify the reused code in the target demo's scenario; a working source demo is
  not evidence that the copied code works in its new environment.

## Research Only What Is Unresolved

1. Reuse existing code, demo patterns, and applicable authoring references first.
2. Research only unanswered capability, API/SDK compatibility, identity/network,
   quota, or cost questions that affect feasibility or the chosen implementation.
   Do not research every dependency or integration by default.
3. Record concise decisions and supporting sources in `plan.md`. Use a separate
   `research.md` only when substantial findings warrant it.
4. Handle focused lookups directly. Do not automatically dispatch research agents;
   delegate only when substantial separate context is necessary.

## Verification Required; Automated Test Suites Optional

- Default to running the notebook scenario and checking its expected outputs against
  the hypothesis. This can be sufficient verification without adding test files.
- Add automated tests only when explicitly requested or when specific nontrivial
  introduced/fixed logic benefits from focused regression checks; explain that need
  in the plan. Do not create a test suite just to satisfy a template or general practice.
- Do not introduce coverage targets, test frameworks, or TDD as default requirements.
- Run the smallest relevant existing checks and preserve existing CI/notebook hygiene
  gates. Making new test files optional does not waive these checks or scenario validation.
- Report checks actually run and their results. If Azure access or another prerequisite
  blocks verification, report that limitation rather than claim the scenario passed.

## Supporting Artifacts Are Optional

`plan.md` is the only required planning output. Do not generate empty or ceremonial files.
Create a supporting artifact only when it is needed to implement or validate the hypothesis:

- `data-model.md`: nontrivial new data shapes, relationships, or state rules that
  cannot be expressed clearly in a short plan section.
- `contracts/`: a new or changed interface whose exact request/response format
  needs an explicit agreement; do not restate an unchanged Azure API.
- `quickstart.md`: a distinct validation guide not already covered by the demo
  README or notebook journey.
- `research.md`: substantial feasibility findings as described above.

When extending a demo, update directly related docs and metadata instead of
creating parallel sources of truth. Preserve existing supporting artifacts and
update them only where the agreed change affects their content.

## Key rules

- Use absolute paths for filesystem operations; use project-relative paths for references in documentation
- Pause on unapproved constitution violations or unresolved blocking decisions.
- Keep infrastructure/platform changes Bicep-first, notebooks small, and scenario
  validation tied to the hypothesis. Do not weaken existing CI or notebook cleanup.

## Done When

- [ ] Minimal implementation plan written with applicable constitution checks and validation
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported with branch, plan path, and any blockers or necessary supporting artifacts
