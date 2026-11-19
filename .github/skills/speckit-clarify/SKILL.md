---
name: "speckit-clarify"
description: "Resolve only prototype decisions that affect the hypothesis, implementation, cost, or hard constraints; zero questions is a valid outcome."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/clarify.md"
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Repository Scope

Apply [the constitution](../../../.specify/memory/constitution.md) and
[the Copilot guidance](../../copilot-instructions.md). For demo creation or extension,
load `azure-demo-authoring` and follow its applicable references. Preserve the
agreed scope and existing identity, network, deployment, and notebook patterns.

## Pre-Execution Checks

**Check for extension hooks (before clarification)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_clarify` key
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

Goal: Resolve unanswered decisions that matter to the prototype and update the
spec directly, without expanding its scope.

Clarification is optional, not a prerequisite for `/speckit-plan`. Zero questions
is a normal successful outcome; do not warn merely because this command was skipped.

Execution steps:

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Optionally capture `IMPL_PLAN`, `TASKS` for future chained flows.)
   - If JSON parsing fails, abort and instruct user to re-run `/speckit-specify` or verify feature branch environment.
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **IF EXISTS**: Load `.specify/memory/constitution.md` for project principles and governance constraints.

3. Load the spec and relevant existing demo context. Check only:
   - Is the problem and hypothesis clear?
   - Are the scope boundaries and observable pass/fail evidence clear?
   - Are required services, identity/network constraints, prerequisites, and paid
     operations understood well enough to choose an implementation?
   - Does any unresolved choice materially change that implementation or validation?

   Do not treat absent production concerns (scale, uptime, localization, retention,
   compatibility, observability) as gaps unless the hypothesis or user requires them.
   Reuse established repository/demo patterns and state low-impact assumptions.

4. Ask only necessary questions through `ask_user`, prioritizing blockers and
   significant strategy decisions. Use plain language, explain why the answer matters,
   and give a recommendation with concise trade-offs. Accept freeform answers;
   do not impose word limits or require a coverage quota.
   - Ask up to five questions, stopping as soon as the relevant decisions are clear.
   - Respect user instructions to stop or proceed.
   - If there are no meaningful questions, report "No blocking ambiguities found"
     and continue to the post-execution hooks without modifying the spec.
   - If the user stops or the question limit is reached with blockers remaining,
     report those blockers and pause; do not silently assume approval.

5. After each accepted answer, update the relevant scope, constraint, requirement,
   scenario, or success criterion directly in `FEATURE_SPEC`.
   - Replace contradictory statements rather than append competing requirements.
   - Preserve existing identifiers and unrelated content.
   - Keep the change minimal; no separate clarification log or coverage report is required.
   - Check that the resulting spec still tests one hypothesis and does not add
     unrequested hardening, fallback paths, or implementation work.

6. If an existing `checklists/requirements.md` is affected, update only applicable
   items whose status changed. Do not create a checklist or add scope to satisfy a
   generic checklist item. Surface conflicts with repository guidance explicitly.

If the spec is missing, report that prerequisite and direct the user to
`/speckit-specify`; do not create a replacement spec here.

Context for prioritization: $ARGUMENTS

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_clarify`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_clarify` key.
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

Report decisions made, the spec path and sections changed (if any), and any remaining
blocking choices. If none remain, say the spec is ready for `/speckit-plan`.
Zero questions needs only a brief no-blockers report; do not invent full coverage.

## Done When

- [ ] Relevant blocking choices resolved and accepted answers integrated, or remaining blockers reported
- [ ] No speculative requirements or unnecessary artifacts added
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported with decisions, changes, and readiness or remaining blockers
