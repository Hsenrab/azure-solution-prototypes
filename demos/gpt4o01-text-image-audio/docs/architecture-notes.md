# Architecture notes

## Goal

Provide a notebook-first, learning-oriented multimodal GPT-4o prototype with a staged test flow:
1. text-only
2. local image input
3. speech-in to text-out
4. speech-in to speech-out

## Reuse-first strategy

- Reuse setup/deploy/env generation flow from demo-template notebooks.
- Reuse response parsing and request-shape patterns from eval notebooks where applicable.
- Reuse speech interaction patterns from speech01 app helpers where they reduce notebook duplication.
- Keep helper extraction minimal and only when a pattern repeats across notebooks.

## Phase boundaries

- Phase A (current): local file media inputs only.
- Phase B (future): add URL-based media input notebooks after Phase A is validated.

## Assumptions

- Target region supports the selected GPT-4o deployment and Speech capability.
- Demo remains feasibility-focused, not production-hardened.
