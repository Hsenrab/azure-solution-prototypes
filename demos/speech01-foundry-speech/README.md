# speech01: Azure AI Foundry + Speech Roundtrip

## Problem statement

Teams want to validate speech features quickly in a Foundry-aligned setup without building a full app stack.

## Hypothesis

If we deploy one `AIServices` account with Foundry project support enabled, we can use the same account outputs to run Speech SDK text-to-speech and speech-to-text roundtrips in a notebook-first workflow.

## Scope

- In scope:
	- Deploy one Azure AI Services account (`kind: AIServices`) with project management enabled.
	- Deploy one Foundry project under that account.
	- Write deployment outputs to `env/.env` automatically.
	- Run Speech SDK synthesis and recognition against the deployed account.
- Out of scope:
	- Real-time streaming agents and conversation orchestration.
	- Production networking, private endpoints, and managed identity hardening.
	- Human-recorded audio capture from microphone.

## Notebook journey

Run notebooks in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, Azure login, and install Python packages |
| `01_deploy_infra.ipynb` | Deploy Bicep for AIServices + Foundry project and write bootstrap values to `env/.env` |
| `02_configure.ipynb` | Publish the Function App code, capture the function key, and preview available voices |
| `03_test.ipynb` | Synthesize text to WAV, run speech recognition on the WAV, and save output |
| `04_function.ipynb` | Invoke Azure Function with function-key auth and inspect recent logs |

## Folder map

```text
infra/      # Bicep for AIServices account + Foundry project
notebooks/  # numbered notebook flow
env/        # .env.example contract; .env auto-written by notebook 01
app/        # helper script for speech roundtrip reuse
data/       # optional inputs
docs/       # architecture notes
outputs/    # generated WAV and JSON test output
```

## Quick start

1. Open `notebooks/00_setup.ipynb` and run all cells.
2. Run `notebooks/01_deploy_infra.ipynb` to create resources and generate the bootstrap `env/.env` file.
3. Run `notebooks/02_configure.ipynb` to publish the function code, write the function key, and choose a voice.
4. Run `notebooks/03_test.ipynb` to execute the end-to-end speech roundtrip.

## Known limitations

- Speech synthesis and recognition are single-shot in this prototype.
- The test uses generated audio, not human microphone input.
- This demo uses function-key auth for the Function endpoint and AAD/managed identity for Speech SDK calls.
