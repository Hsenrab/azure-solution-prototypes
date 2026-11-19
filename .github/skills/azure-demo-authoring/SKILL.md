---
name: azure-demo-authoring
description: "Create or extend Azure prototype demos in this repository. Use for new demo scaffolding, extending demo scope, notebook updates, metadata updates, Azure AI Foundry alignment, and lightweight hypothesis-driven feasibility work."
argument-hint: "Describe the demo goal, hypothesis, and whether this is new or existing."
user-invocable: true
---

# Azure Demo Authoring

## When to Use
- Create a new demo under `demos/<demo-name>/`.
- Extend an existing demo while preserving lightweight scope.
- Update notebooks, demo metadata, and deployment/configuration flow.
- Align Azure AI demos with current Azure AI Foundry guidance.

## Procedure
1. Decide whether this is create or extend.
2. For every new or extended demo, follow the Spec Kit handoff in the workflow
   reference, including bounded artifact discovery before Specify.
3. Define one customer problem and one testable hypothesis.
4. Apply the minimal change set required to validate that hypothesis.
5. Keep docs and metadata aligned with scope.
6. For Azure AI work, follow the Foundry standards reference.

## References
- [Workflow checklist](./references/workflow.md)
- [Azure AI Foundry standards](./references/azure-ai-foundry.md)
- [Repository-wide rules](../../copilot-instructions.md)
