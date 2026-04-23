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

- `README.md` (problem, setup, run steps, limitations)
- `metadata.json` (all required metadata fields)
- `env/.env.example` (no secrets)

## 3) Place content consistently

- IaC -> `infra/`
- App code -> `app/`
- Notebooks -> `notebooks/`
- Sample/mock data -> `data/`
- Environment templates -> `env/`
- Architecture notes -> `docs/`
- Screenshots/output artifacts -> `outputs/`

## 4) Keep demos lightweight

- Prefer minimal viable infra and code
- Mark optional production controls clearly as optional
- Record assumptions and known gaps

## 5) Metadata expectations

Use the same schema keys as `demo-template/metadata.json` so demos can be indexed consistently.

## 6) Copilot usage

Use these reusable prompts when creating/extending demos:

- `.github/prompts/create-new-demo.prompt.md`
- `.github/prompts/extend-existing-demo.prompt.md`
