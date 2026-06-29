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
- Python dependencies -> `requirements.txt`

## 5) Python Virtual Environment & Dependencies

Each demo creates its own isolated Python virtual environment to avoid dependency conflicts:

1. **Create `requirements.txt`** in the demo folder root with all Python packages needed
   - Base packages: `azure-ai-inference`, `python-dotenv`, `requests`
   - Add demo-specific packages (e.g., `azure-ai-evaluation`, `azure-search-documents`)
   - See `demo-template/requirements.txt` for examples

2. **Virtual environment setup** is automatic in `00_setup.ipynb`
   - Creates `.venv` folder in demo root
   - Installs all packages from `requirements.txt` into the venv
   - Notebook prompts user to select the venv kernel in VS Code

3. **After running `00_setup.ipynb`:**
   - Users select the `.venv` interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
   - All subsequent notebooks run in this isolated environment

## 6) Python SDK First; Azure CLI as Fallback

Prefer Python Azure SDKs in notebooks and demo app code when they support the operation. This keeps logic in Python, improves type safety, and avoids shell-level command parsing issues.

For Functions-focused demos, prefer SDK-based flows first:
- `azure-identity` for authentication
- `azure-storage-blob` for package upload / data plane operations
- `azure-mgmt-web` for Function App management-plane operations

Use Azure CLI via `subprocess` only when SDK coverage is missing or significantly more complex for the demo scope.

**Fallback CLI pattern (when needed):**

```python
import subprocess

result = subprocess.run([az_cmd, "account", "show", "--output", "json"], capture_output=True, text=True)
if result.returncode != 0:
    raise RuntimeError(
        f"az account show failed (exit {result.returncode})\n"
        f"stderr: {result.stderr.strip()}\n"
        f"stdout: {result.stdout.strip()}"
    )
```

**Key points for CLI fallback:**
- Prefer argument lists over `shell=True`.
- Always capture and surface both stderr and stdout on failure.
- Avoid `check=True` alone for `az` calls; raise explicit errors with captured output.

## 7) Keep demos lightweight

- Prefer minimal viable infra and code
- Mark optional production controls clearly as optional
- Record assumptions and known gaps in `docs/architecture-notes.md`

## 7) Metadata expectations

Use the same schema keys as `demo-template/metadata.json` so demos can be indexed consistently.

## 8) Copilot usage

Use these reusable prompts when creating/extending demos:

- `.github/prompts/create-new-demo.prompt.md`
- `.github/prompts/extend-existing-demo.prompt.md`
