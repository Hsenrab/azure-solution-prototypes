# Tasks: Connected Model Prompt Agent

## Implementation

- [X] T001 Create `06_prompt_agent.ipynb` by adapting the existing connected-model
  agent flow with generated settings, no tools, pirate system instructions, and
  the Azure AI Foundry user query.
- [X] T002 Add targeted cleanup for only the new notebook's test conversation and
  agent version; retain the connected model and gateway.
- [X] T003 Update the BYOM README and metadata with the new notebook journey.

## Validation

- [X] T004 Run notebook parsing/source checks and the existing notebook hygiene
  check on the new notebook.
- [X] T005 Report live inference as unrun unless explicitly authorized; do not
  claim pirate-style output without a live run.
