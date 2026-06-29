# cu01-foundry-video Demo

Analyze video content at scale using Azure AI Content Understanding. Extract transcripts, scene descriptions, and keyframes for RAG ingestion or media asset management.

## Quick Start

1. **Setup:** Run `notebooks/00_setup.ipynb`
   - Creates Python venv, authenticates with Azure, installs dependencies

2. **Deploy:** Run `notebooks/01_deploy_infra.ipynb`
   - Deploys Foundry AIServices resource with model deployment to UK South
   - Writes config to `env/.env`

3. **Configure:** Run `notebooks/02_configure.ipynb`
   - Verifies endpoint connectivity and authentication

4. **Analyze (REST):** Run `notebooks/03_test_rest.ipynb`
   - Submit a local video for analysis via REST API
   - Displays transcriptions, scene descriptions, keyframes

5. **Analyze (SDK):** Run `notebooks/04_test_sdk.ipynb` (optional)
   - Same analysis using `azure-ai-contentunderstanding` SDK
   - Falls back to REST if SDK unavailable

6. **Cleanup:** Run `notebooks/X_destroy.ipynb`
   - Removes all resources; keeps resource group for purge operation

## Architecture

- **Service:** Azure AI Content Understanding (GA `2025-11-01`)
- **Model:** Configurable Bicep parameter (default: `gpt-4.1-mini`, swappable to `gpt-4.1`, `gpt-4.1-nano`, `gpt-5.2`)
- **Auth:** Managed Identity (disableLocalAuth: true, no keys)
- **Region:** UK South (`uksouth`)
- **Analyzer:** `prebuilt-videoSearch` (transcription + scene segmentation + keyframe extraction)

## File Structure

```
cu01-foundry-video/
├── notebooks/
│   ├── 00_setup.ipynb             # Create venv, auth, install
│   ├── 01_deploy_infra.ipynb      # Deploy Bicep/ARM template
│   ├── 02_configure.ipynb         # Verify deployment
│   ├── 03_test_rest.ipynb         # Analyze video (REST API)
│   ├── 04_test_sdk.ipynb          # Analyze video (SDK)
│   └── X_destroy.ipynb            # Cleanup (from speech01 pattern)
├── infra/
│   ├── main.bicep                 # Infrastructure as code (source of truth)
│   └── main.json                  # Compiled ARM template
├── app/
│   └── notebook_helpers.py        # Shared analysis functions
├── env/
│   └── .env                       # Configuration (git-ignored, auto-generated)
├── outputs/
│   ├── video_analysis_result_rest.json  # REST API results
│   └── video_analysis_result_sdk.json   # SDK results
├── data/
│   └── (user places video files here)
├── metadata.json                  # Demo metadata
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Model Swappability

To use a different model, edit `infra/main.bicep`:

```bicep
param deploymentName string = 'gpt-4.1'        # <- Change here
param modelName string = 'gpt-4.1'             # <- Change here
param modelVersion string = '2024-12-01'       # <- Change here
```

Then regenerate the ARM template:
```bash
bicep build infra/main.bicep --outfile infra/main.json
```

Supported models:
- `gpt-5.2` (recommended)
- `gpt-4.1`
- `gpt-4.1-mini` (default, lowest cost)
- `gpt-4.1-nano`

## Requirements

- Azure CLI installed and authenticated
- Python 3.9+
- Video file < 200 MB, < 2 hours duration
- Supported formats: MP4, M4V, AVI, MKV, MOV, FLV, WMV

## Key Features

✅ REST API approach (no SDK dependency)  
✅ SDK approach (when available)  
✅ Built-in transcription (Speech-to-text)  
✅ Scene segmentation and descriptions  
✅ Keyframe extraction for indexing  
✅ Managed Identity authentication  
✅ Bicep + ARM template options  

## Costs

- AIServices S0 SKU: ~$1–5/month (all regions)
- Model deployment: Token-based billing (gpt-4.1-mini is cheapest)
- Storage: None (no blob dependency)

Estimate: $5–20/month for light usage.

## Limitations

- Frame sampling: ~1 FPS (rapid motions may be missed)
- Frame resolution: 512×512 px (small text lost)
- Max 4 hours video / minute throughput per resource
- Segmentation: 1 content category per video (max 2 hierarchy levels)

## Next Steps

- Replace `deploymentName`, `modelName`, `modelVersion` in Bicep to test different models
- Integrate analysis output into a RAG pipeline
- Extend to process multiple videos in batch
- Add custom field extraction via Content Understanding analyzers

## References

- [Azure Content Understanding](https://learn.microsoft.com/azure/ai-services/content-understanding/)
- [Region and Language Support](https://learn.microsoft.com/azure/ai-services/content-understanding/language-region-support)
- [REST API Reference](https://learn.microsoft.com/azure/ai-services/content-understanding/quickstart/use-rest-api)
