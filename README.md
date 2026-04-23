# Azure Solution Prototypes

A lightweight internal starter repository for Azure-focused prototypes, feasibility demos, and proof-of-concept experiments.

## Repository purpose

- Capture small, practical demos for real customer scenarios
- Keep each demo self-contained and easy to run
- Support fast experimentation over production hardening
- Combine infrastructure, app code, notebooks, and setup notes where useful

## Top-level structure

```text
.github/
  copilot-instructions.md
  prompts/
demos/
  foundry-model-notebook-sweden-central/
demo-template/
CONTRIBUTING.md
```

## Standard demo folder structure

Each demo should follow this layout:

```text
<demo-folder>/
  README.md                # what problem this demo explores + how to run
  metadata.json            # lightweight indexable metadata
  infra/                   # IaC (Bicep/Terraform/ARM)
  app/                     # application code, scripts, APIs, UIs
  notebooks/               # optional investigation notebooks
  data/                    # sample/mock data only (no secrets)
  env/                     # environment templates (e.g., .env.example)
  docs/                    # architecture notes and assumptions
  outputs/                 # screenshots, sample output artifacts
  scripts/                 # setup/run helpers
```

### Placement guidance

- **Infrastructure as code**: `infra/`
- **Application code**: `app/`
- **Notebooks**: `notebooks/`
- **Sample data**: `data/`
- **Environment configuration**: `env/`
- **Architecture notes**: `docs/`
- **Screenshots or outputs**: `outputs/`

## Naming conventions (recommended)

- **Demo folders**: `kebab-case` with intent + scope (example: `foundry-model-notebook-sweden-central`)
- **Branches**: `feat/<short-topic>`, `fix/<short-topic>`, `docs/<short-topic>`
- **Environment variables**: `UPPER_SNAKE_CASE` and demo-specific prefix when useful (example: `FOUNDRY_ENDPOINT`)
- **Infrastructure resources**: lowercase + hyphen + short region/env suffix (example: `aoai-foundry-feasibility-swec`)

## Demo metadata schema (lightweight)

Every demo includes `metadata.json` with these fields:

- `demo_name`
- `problem_statement`
- `hypothesis`
- `customer_scenario`
- `status`
- `owner`
- `technologies`
- `azure_services`
- `data_requirements`
- `security_notes`
- `setup_time_estimate`
- `last_updated`

Use `demo-template/metadata.json` as the baseline.

## Example demo (included)

| Folder | One-line purpose | Likely components | Notebook useful? | Infra needed? |
|---|---|---|---|---|
| `demos/foundry-model-notebook-sweden-central` | Deploy Azure AI Foundry model in Sweden Central and validate with a notebook prompt | Bicep, env template, notebook, quick-start scripts, architecture notes | Yes | Yes |

## Copilot support

- Repo-wide instructions: `.github/copilot-instructions.md`
- Reusable prompts:
  - `.github/prompts/create-new-demo.prompt.md`
  - `.github/prompts/extend-existing-demo.prompt.md`

## Recommendation notes

- Recommendation: keep demos intentionally small and disposable.
- Recommendation: start with mocked/sample data first, then attach real integrations.
- Recommendation: capture assumptions and known limits in each demo `README.md`.
