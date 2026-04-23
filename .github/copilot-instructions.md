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
- `infra/`, `env/`, `docs/`
- `notebooks/` with the standard 4-notebook journey (see below)
- `app/` only when code is needed beyond what the notebooks cover

## Notebook standard

Every demo uses numbered notebooks as the primary interface. The standard structure is:

| Notebook | Purpose |
|---|---|
| `00_setup.ipynb` | Prerequisites, `az login`, `pip install` |
| `01_deploy_infra.ipynb` | Deploy Bicep via Azure CLI; retrieve outputs; write `env/.env` automatically |
| `02_configure.ipynb` | Python SDK post-deploy setup (create indexes, upload data, etc.) — skip steps not applicable |
| `03_test.ipynb` | Load `env/.env`, exercise scenario, validate hypothesis |

`env/.env` is **never filled in manually**. It is always written by `01_deploy_infra.ipynb` from the deployed resource outputs.

## Metadata

Always populate the fields from `demo-template/metadata.json` exactly.

## Recommendations style

If uncertain, provide a sensible recommendation and clearly label it as a recommendation.
