# Contributing: adding a new prototype demo

This repository is optimized for **feasibility and learning**, not production hardening.

## 1) Create a new demo folder

Copy `demo-template/` into `demos/<your-demo-folder-name>/`.

Recommended folder naming:

- lowercase `kebab-case`
- include problem/use-case context
- optionally include region/scope suffix

Example:

```text
demos/foundry-rag-private-data-swec
```

## 2) Fill in required files first

- `README.md` (problem, notebook journey table, known limitations)
- `metadata.json` (all required metadata fields)
- `env/.env.example` (document expected variable names — no real values)

## 3) Notebook-first structure

**Notebooks are the primary interface.** Each demo should use numbered notebooks that build up the journey step by step:

| Notebook | Purpose |
|---|---|
| `00_setup.ipynb` | Prerequisites, Azure login, Python dependency install |
| `01_deploy_infra.ipynb` | Deploy Bicep IaC via Azure CLI; retrieve outputs; **write `env/.env` automatically** |
| `02_configure.ipynb` | Python SDK post-deployment setup (e.g. create search index, upload data, register model endpoint) — skip if not needed |
| `03_test.ipynb` | Load `env/.env`, exercise the scenario, validate hypothesis |

Add further numbered notebooks (e.g. `03_`, `04_`) for additional scenario steps.

The `env/.env` file is **never filled in manually**. `01_deploy_infra.ipynb` queries the deployed Azure resources (using Azure CLI or Python SDK) and writes the file automatically.

## 4) Place non-notebook content consistently

- IaC -> `infra/`
- Application code (if needed beyond notebooks) -> `app/`
- Notebooks -> `notebooks/`
- Sample/mock data -> `data/`
- Environment template (no secrets) -> `env/.env.example`
- Architecture notes -> `docs/`
- Screenshots/output artifacts -> `outputs/`

## 5) Keep demos lightweight

- Prefer minimal viable infra and code
- Mark optional production controls clearly as optional
- Record assumptions and known gaps in `docs/architecture-notes.md`

## 6) Metadata expectations

Use the same schema keys as `demo-template/metadata.json` so demos can be indexed consistently.

## 7) Copilot usage

Use these reusable prompts when creating/extending demos:

- `.github/prompts/create-new-demo.prompt.md`
- `.github/prompts/extend-existing-demo.prompt.md`
