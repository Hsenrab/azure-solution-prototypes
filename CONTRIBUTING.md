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

## 6) Running Azure CLI Commands in Notebooks

Use `subprocess` with `shell=True` to run `az` CLI commands. This pattern ensures the shell handles PATH lookup correctly.

**Pattern:**

```python
import subprocess

# ✓ CORRECT: Use shell=True (string command, not list)
result = subprocess.run('az login', shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print('OK: Login successful')
else:
    print(f'ERROR: {result.stderr}')
```

**Key points:**
- Always use `shell=True` so the shell (PowerShell on Windows) resolves `az` on PATH
- Pass the command as a **string**, not a list: `'az login'` not `['az', 'login']`
- Use `capture_output=True, text=True` to capture stdout/stderr as strings
- Check `result.returncode == 0` for success; `result.stderr` for error messages

**For Azure CLI queries that need JSON parsing:**

```python
import subprocess
import json

result = subprocess.run(
    'az account show --query "{Id:id, Name:name}" -o json',
    shell=True,
    capture_output=True,
    text=True
)
if result.returncode == 0:
    data = json.loads(result.stdout)
    print(f"Subscription: {data['Name']} ({data['Id']})")
```

Avoid calling `subprocess.run()` with a list (e.g., `['az', 'login']`) — this bypasses the shell and causes PATH lookup failures.

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
