# Copilot instructions for this repository

## Intent

Help engineers create and extend lightweight Azure prototype demos quickly.

## Guardrails

- Optimize for feasibility and learning, not production hardening.
- Keep each demo self-contained under `demos/<demo-name>/`.
- Do not introduce enterprise-scale architecture unless explicitly requested.
- Prefer plain language, minimal dependencies, and readable setup steps.

## Required demo shape

When creating a new demo, always include:

- `README.md`
- `metadata.json`
- `infra/`, `app/`, `env/`, `docs/`
- Add `notebooks/` only when exploratory workflows help

## Metadata

Always populate the fields from `demo-template/metadata.json` exactly.

## Recommendations style

If uncertain, provide a sensible recommendation and clearly label it as a recommendation.
