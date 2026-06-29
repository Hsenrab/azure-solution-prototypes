# gpt4o01-text-image-audio

## Problem statement

Teams want to evaluate GPT-4o multimodal capability quickly, but often start with complex architectures that slow down learning.

## Hypothesis

A staged notebook-first demo can prove core multimodal capability with minimal setup:
- text-only first
- local image input second
- speech-in to text-out and speech-in to speech-out third

## Scope

- In scope:
	- Foundry-aligned Azure AI Services account deployment
	- Reusable notebook patterns for setup, deployment, configuration, and teardown
	- Clear learning-oriented notebooks with concise why-comments in non-obvious code
	- Local file input for image and audio in Phase A
- Out of scope (Phase B / follow-up):
	- URL-based media inputs (image URL and audio URL)
	- APIM integration
	- Function app API surface
	- Full evaluation pipeline

## Notebook journey

The demo is driven by numbered notebooks in `notebooks/`. Run them in order:

| Notebook | What it does |
|---|---|
| `00_setup.ipynb` | Verify prerequisites, log in to Azure, and install Python packages |
| `01_deploy_infra.ipynb` | Deploy Bicep template and write `env/.env` automatically |
| `02_configure.ipynb` | Validate environment and finalize deployment/config values |
| `03_text_test.ipynb` | Plain text GPT-4o validation (first checkpoint) |
| `04_image_test.ipynb` | Local image input validation in a separate notebook |
| `05_audio_text.ipynb` | Speech-in to text-out flow |
| `06_audio_roundtrip.ipynb` | Speech-in to speech-out roundtrip |
| `X_destroy.ipynb` | Tear down deployed resources |

## Staged rollout

- Phase A (implemented now): local media inputs and staged multimodal validation
- Phase B (later extension): add `07_image_url_test.ipynb` and `08_audio_url_test.ipynb` after Phase A verification

## Folder map

```text
infra/      # infrastructure as code (Bicep)
notebooks/  # numbered step-by-step notebooks (primary interface)
env/        # .env.example documents expected vars; .env is written by notebook
app/        # small helpers when notebook reuse is insufficient
data/       # sample/mock data
docs/       # architecture notes and assumptions
outputs/    # sample outputs
```

## Quick start

1. Open `notebooks/00_setup.ipynb` and complete setup.
2. Run `notebooks/01_deploy_infra.ipynb` to deploy and generate `env/.env`.
3. Run `notebooks/02_configure.ipynb`.
4. Validate in order: `03_text_test.ipynb`, then `04_image_test.ipynb`, then audio notebooks.
5. Run `notebooks/X_destroy.ipynb` when finished.

## Known limitations

- This is a feasibility demo, not production architecture.
- Latency and speech quality vary by region, model deployment, and audio input quality.
- URL-based media inputs are intentionally deferred until local flow is verified.
