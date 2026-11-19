---
name: "speckit-tasks"
description: "Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/tasks.md"
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before tasks generation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_tasks` key
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

1. **Setup**: Run `.specify/scripts/powershell/setup-tasks.ps1 -Json` from repo root and parse FEATURE_DIR, TASKS_TEMPLATE_CONTENT, TASKS_TEMPLATE, and AVAILABLE_DOCS list. `FEATURE_DIR` and `TASKS_TEMPLATE` must be absolute paths when provided. `AVAILABLE_DOCS` is a list of document names/relative paths available under `FEATURE_DIR` (for example `research.md` or `contracts/`). For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (interface contracts), research.md (decisions), quickstart.md (test scenarios)
   - **IF EXISTS**: Load `.specify/memory/constitution.md` for project principles and governance constraints
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Extract the minimum work**:
   - Map the spec's requirements and success criteria to the plan's actual changed files.
   - Preserve the plan's reuse decisions: name source files/cell headings, destinations,
     and necessary substitutions rather than generate tasks to rewrite working code.
   - Consume optional design artifacts only where they affect the agreed scope.
     Their absence is not a gap and does not require tasks to create them.
   - Include notebook/scenario verification and relevant existing checks, not just code.
   - Record actual dependencies; notebook steps may depend on setup and deployment.
     Do not invent independent MVPs, layers, or parallel work to fill a template.

4. **Generate tasks.md**: Use TASKS_TEMPLATE_CONTENT (from the JSON output above) as the structure. For compatibility with older setup scripts that omit TASKS_TEMPLATE_CONTENT, read TASKS_TEMPLATE instead. Fill with:
   - Feature name and links to spec.md and plan.md
   - Only implementation, directly related documentation/metadata, and verification tasks
     needed by the hypothesis, with task IDs and exact file paths
   - Source references for copied cells, helpers, or Bicep where applicable
   - Expected outputs, prerequisites, and paid operations for verification tasks
   - A short dependency note; use numbered phases only if useful for real dependencies
   - No mandatory setup/foundational/polish phases, new tooling, refactoring, performance
     optimization, or hardening outside the agreed plan

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_tasks`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_tasks` key.
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

Report the tasks.md path, minimal change scope, task count, actual dependencies,
and how the hypothesis will be verified. Mention blockers or paid operations.
Do not require a separate MVP strategy or parallel execution examples.

Context for task generation: $ARGUMENTS

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

Generate only work required by the agreed spec and plan. One short task list for
one notebook journey is sufficient. Apply the constitution and applicable authoring
guidance; do not introduce generic application scaffolding.

**Verification is REQUIRED; new automated tests are OPTIONAL**: Follow the
[verification guidance](../speckit-plan/SKILL.md#verification-required-automated-test-suites-optional).
Always include the agreed notebook/scenario verification and relevant existing checks.
Generate new automated test tasks only if requested or if the plan identifies
specific nontrivial introduced/fixed logic that warrants focused regression checks.
An acceptance scenario or "Independent Test" is not itself a request for test files.
Do not add coverage targets, a test framework, or TDD by default.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
4. **[Story] label**: Use [US1], [US2], etc. for tasks specific to an existing
   spec story; omit for shared or cross-scenario work. Do not invent stories to add labels.
5. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 [US1] Copy the plan's source gateway cell into demos/<demo-name>/notebooks/03_test.ipynb with the listed substitutions`
- ✅ CORRECT: `- [ ] T002 [US1] Run demos/<demo-name>/notebooks/03_test.ipynb and check the response shape per SC-001`
- ✅ CORRECT: `- [ ] T003 Update run instructions in demos/<demo-name>/README.md`
- ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

### Task Scope and Order

- Follow the plan's actual dependencies. Add setup or infrastructure tasks only
  when the change needs them; implement platform behavior Bicep-first.
- Reference agreed data/interface constraints when optional artifacts exist;
  do not infer models, service layers, or contract tests merely from their presence.
- Keep copied code self-contained in the destination demo. Do not add a shared
  cross-demo abstraction or refactoring task just to avoid duplication.
- Include a runnable verification task for each relevant acceptance outcome;
  one notebook run may cover several requirements or stories.
- Add automated tests only under the verification guidance above, and order them
  before implementation only when TDD was requested.
- Keep existing task IDs and references intact when updating an existing list.

## Done When

- [ ] tasks.md contains only required work, task IDs, file paths, and scenario verification
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported with minimal scope, dependencies, verification, and any blockers
