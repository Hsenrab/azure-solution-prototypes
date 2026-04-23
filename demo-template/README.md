# <demo-name>

## Problem statement

Describe the customer problem this demo explores.

## Hypothesis

State what you believe this prototype will validate.

## Scope

- In scope:
- Out of scope:

## Notebook journey

The demo is driven by numbered notebooks in `notebooks/`. Run them in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, log in to Azure, install Python packages |
| `01_deploy_infra.ipynb` | Deploy Bicep template via Azure CLI; retrieve outputs and write `env/.env` automatically |
| `02_use_case.ipynb` | Load `env/.env`, connect to deployed resources, exercise the demo scenario |

## Folder map

```text
infra/      # infrastructure as code (Bicep)
notebooks/  # numbered step-by-step notebooks (primary interface)
env/        # .env.example documents expected vars; .env is written by notebook
app/        # app or script code (if needed beyond notebooks)
data/       # sample/mock data
docs/       # architecture notes and assumptions
outputs/    # screenshots and sample outputs
```

## Quick start

1. Open `notebooks/00_setup.ipynb` and follow each step.
2. Continue to `notebooks/01_deploy_infra.ipynb` — this deploys infra and writes `env/.env`.
3. Finish with `notebooks/02_use_case.ipynb`.

## Known limitations

- Keep this section explicit for feasibility demos.
