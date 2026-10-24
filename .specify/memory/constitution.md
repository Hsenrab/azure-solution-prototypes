<!--
Sync Impact Report (remove before committing the constitution)
Version change: unratified template -> 1.0.0 (initial adoption).
Modified principles: replaced the five template slots with:
  I. Existing Copilot Guidance Remains Active
  II. Lightweight, Hypothesis-Driven Demos
  III. Infrastructure-First, Root-Cause Fixes
  IV. Consistent Notebook Journeys
  V. Evidence-Based Validation and Existing Quality Gates
Added sections: Authoritative Guidance; Spec Kit Workflow and Compliance Gates.
Removed sections: none; template placeholders and examples replaced.
Follow-up TODOs: none.
Dependent templates and commands: unchanged; consume this constitution at runtime.
-->

# Azure Solution Prototypes Constitution

## Core Principles

### I. Existing Copilot Guidance Remains Active

Spec Kit MUST complement, not replace, the repository's Copilot instructions, skills,
and GitHub Actions workflows. Every Spec Kit phase MUST apply the relevant rules in
[Copilot instructions](../../.github/copilot-instructions.md).
For demo creation or extension, including notebook and metadata updates, agents MUST
load [Azure Demo Authoring](../../.github/skills/azure-demo-authoring/SKILL.md) before
domain work and follow its applicable references. Starting a Spec Kit command does
not waive this requirement.

Relevant supporting skills MUST be used according to the routing in the Copilot
instructions. Reusable procedures MUST remain in skill references; specifications,
plans, tasks, and this constitution MUST reference them rather than maintain competing
copies. This keeps one source of truth as the repository evolves.

### II. Lightweight, Hypothesis-Driven Demos

Every new or extended demo MUST identify one customer problem and one testable
hypothesis. Demo implementation MUST remain self-contained under `demos/<demo-name>/`,
with minimal dependencies and infrastructure sufficient to validate that hypothesis.
New demos MUST start from [the demo template](../../demo-template/) and follow the
[authoring workflow](../../.github/skills/azure-demo-authoring/references/workflow.md).

Plans MUST use the existing demo layout rather than introduce generic application
scaffolding. Documentation and metadata MUST stay aligned with scope. Production
hardening, enterprise-scale architecture, and backward compatibility MUST NOT become
default requirements unless the user explicitly requests them.

### III. Infrastructure-First, Root-Cause Fixes

Infrastructure and platform behavior changes MUST be implemented in Bicep first.
Notebook and application code MUST consume deployed behavior rather than work around
infrastructure drift. Fix scope MUST follow this order: Bicep or shared infrastructure,
then a shared helper, then a local notebook change only when the earlier options
cannot resolve the cause.

Changes to deployment, authentication, or tooling MUST respect the demo's existing
identity and network constraints. Significant strategy changes MUST include concise
trade-offs and explicit user confirmation before implementation. Python Azure SDKs
MUST be preferred where they support the operation; CLI use MUST follow the existing
fallback guidance. Fixes MUST remediate the upstream cause, not merely add fallback
branches, diagnostics, or catch-and-explain wrappers.

### IV. Consistent Notebook Journeys

Notebooks MUST remain the primary demo interface, with small, single-purpose cells.
The deployment notebook MUST generate `env/.env` from deployed resource outputs;
users MUST NOT be required to populate it manually. Secrets MUST NOT be committed.

Setup and destroy notebooks MUST follow the source-of-truth notebooks and permitted
substitutions defined in the Copilot instructions:
[speech setup](../../demos/speech01-foundry-speech/notebooks/00_setup.ipynb) and
[speech destroy](../../demos/speech01-foundry-speech/notebooks/X_destroy.ipynb).
Setup MUST retain the ordered environment/kernel, authentication/subscription, and
dependency-installation steps. Template destroy confirmations MUST remain disabled.
Notebook discussions MUST identify cells by heading or purpose, never by cell number.

### V. Evidence-Based Validation and Existing Quality Gates

Specs MUST define observable hypothesis acceptance criteria; plans and tasks MUST
carry those criteria through to validation. Changes MUST be checked with the smallest
relevant existing checks and scenario validation. Reports MUST distinguish checks
actually run from Azure-dependent checks blocked by prerequisites or not run.

The existing
[Notebook Metadata Check](../../.github/workflows/notebook-metadata-check.yml)
GitHub Actions workflow and
[pre-commit configuration](../../.pre-commit-config.yaml) MUST remain active when
using Spec Kit. For applicable changes, agents MUST use the configured notebook
cleanup checks, including `nbstripout` and removal of kernel display-name metadata.
Spec Kit MUST NOT bypass or weaken these checks. CI validates notebook hygiene;
it does not replace scenario or hypothesis validation.

## Authoritative Guidance

The following sources remain applicable throughout Spec Kit work:

- [Copilot instructions](../../.github/copilot-instructions.md): always-on guardrails,
  skill routing, infrastructure-first decisions, notebook standards, and communication.
- [Azure Demo Authoring](../../.github/skills/azure-demo-authoring/SKILL.md) and its
  [workflow reference](../../.github/skills/azure-demo-authoring/references/workflow.md):
  the reusable create/extend procedure, required demo shape, and notebook conventions.
- [Azure AI Foundry standards](../../.github/skills/azure-demo-authoring/references/azure-ai-foundry.md):
  applicable Foundry research, resource, SDK, model, and preview guidance.
- [Contributing guide](../../CONTRIBUTING.md) and
  [repository README](../../README.md): contributor setup, demo layout, and metadata.
- [Notebook Metadata Check](../../.github/workflows/notebook-metadata-check.yml) and
  [pre-commit configuration](../../.pre-commit-config.yaml): executable notebook hygiene gates.
- [Spec Kit skills](../../.github/skills/): specification, clarification, planning,
  task generation, implementation, analysis, and convergence procedures.

Supporting skills are loaded only when relevant: `vscode-microsoft-foundry` for
Foundry agents, `microsoft-foundry` for Foundry resources and operations,
`cosmosdb-best-practices` for Cosmos DB changes, `foundrytk-quick-start` for onboarding,
and `use-winml-cli` for non-generative ONNX/Windows ML scenarios. Their availability
MUST NOT be assumed solely because they are referenced here.

## Spec Kit Workflow and Compliance Gates

1. **Specify and clarify**: consult the Copilot instructions and applicable authoring
   references; capture the problem, hypothesis, acceptance criteria, and hard constraints.
2. **Plan**: use the Constitution Check to record applicable skill/reference use,
   demo placement, Bicep-first decisions, notebook standards, and validation gates.
   Recheck compliance after design. Generic Spec Kit template examples MUST NOT
   override this repository's demo conventions.
3. **Tasks**: include the implementation, directly related documentation/metadata,
   and validation work required by those decisions; keep the scope hypothesis-driven.
4. **Implement**: load applicable skills, follow their procedures, preserve existing
   workflows, and execute relevant checks. The metadata workflow currently runs
   `pre-commit run --all-files --show-diff-on-failure`; retain its configured triggers.
5. **Review, analyze, and converge**: assess compliance with both the feature artifacts
   and the repository guidance. Report validation evidence, root-cause fix location,
   why that scope was chosen, and any temporary workaround with its removal plan.

GitHub Actions workflows are executable automation, not agent skills: they MUST run
through their configured events or supported local checks, not be treated as a
replacement for loading the authoring skill.

## Governance

This constitution governs Spec Kit artifacts and explicitly incorporates the
repository guidance above. Spec Kit templates and generated feature artifacts MUST
NOT override the Copilot guardrails, applicable skill procedures, or existing CI
checks. If authoritative sources conflict, agents MUST surface the conflict and
obtain user direction before implementing a conflicting approach.

Amendments MUST state their rationale, impact on existing work, and required
follow-up, and require explicit user approval. Versioning MUST use MAJOR for
incompatible principle changes or removals, MINOR for new or materially expanded
guidance, and PATCH for non-semantic clarifications. Ratification records initial
adoption; Last Amended records the date of the latest amendment.

Every plan's Constitution Check and implementation review MUST verify applicable
principles and linked procedures. Exceptions MUST be documented with rationale and
approved by the user; an exception MUST NOT silently redefine repository-wide policy.
The temporary Sync Impact Report above MUST be removed before committing this file.

**Version**: 1.0.0 | **Ratified**: 2026-10-23 | **Last Amended**: 2026-10-23
