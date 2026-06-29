# Architecture Notes

## Overview

**cu01-foundry-video** demonstrates Azure AI Content Understanding for large-scale video analysis.

The service extracts:
- **Transcription** (Speech-to-text with timestamps)
- **Scene descriptions** (Segment each video into logical scenes with AI-generated summaries)
- **Keyframes** (Index thumbnails for quick preview)

All results are returned as a single operation with three structured outputs.

## Service Architecture

### Azure Content Understanding Analyzer

| Attribute | Value |
|-----------|-------|
| **Service** | Azure Cognitive Services → AI Services |
| **API** | `POST {endpoint}/contentunderstanding/analyzers/prebuilt-videoSearch:analyzeBinary` |
| **Auth** | Bearer token (DefaultAzureCredential) |
| **Streaming** | Video binary in request body (multipart/octet-stream) |
| **Response** | 202 Accepted + Operation-Location header |
| **Polling** | GET Operation-Location until status=="succeeded" |

### Supported Models (Content Understanding GA)

| Model | Capability | Supported | Cost |
|-------|-----------|-----------|------|
| gpt-4o | Vision (images) | ❌ Not supported by Content Understanding | N/A |
| gpt-4.1 | Video analysis | ✅ Full | ~$0.05/min video |
| gpt-4.1-mini | Video analysis | ✅ Full | ~$0.015/min video |
| gpt-4.1-nano | Video analysis | ✅ Full | ~$0.005/min video |
| gpt-5.2 | Video analysis | ✅ Full | ~$0.10/min video |

**Default:** gpt-4.1-mini (cost-optimized for prototyping).

**Key Constraint:** Content Understanding requires the gpt-4.1 family. GPT-4o (image-only) is not supported.

### Infrastructure as Code

#### Bicep Template (`infra/main.bicep`)

Parameters:
- `location`: Azure region (default: `uksouth`)
- `demoId`: Resource naming prefix (default: `cu01`)
- `deploymentName`: Model deployment name (default: `gpt-4.1-mini`, swappable)
- `modelName`: Model name (default: `gpt-4.1-mini`, swappable)
- `modelVersion`: Model version (default: `2024-12-01`)
- `deployerPrincipalId`: User principal ID for RBAC (optional)

Resources Created:
1. **AIServices Account** (Cognitive Services)
   - SKU: GlobalStandard (required for Content Understanding)
   - Auth: disableLocalAuth = true (no keys)
   - Managed Identity: system-assigned

2. **Model Deployment**
   - Deployment name: `${deploymentName}`
   - Capacity: 1 (default; adjustable)
   - SKU: Standard

3. **RBAC Role Assignment** (optional)
   - Role: Cognitive Services User
   - Scope: AIServices account
   - Principal: Deployer principal ID

#### ARM Template Compilation

The Bicep template is compiled to ARM JSON for CLI deployment:

```bash
bicep build infra/main.bicep --outfile infra/main.json
```

This is pre-generated in `infra/main.json` (no CLI required to deploy).

### Authentication Flow

```
User (Device Code)
     ↓
Azure CLI (az account show)
     ↓
AZURE_SUBSCRIPTION_ID / AZURE_AUTH_MODE = aad
     ↓
Notebook loads env/.env
     ↓
DefaultAzureCredential()
     ↓
Token (https://cognitiveservices.azure.com/.default)
     ↓
Authorization: Bearer {token}
```

**Key:** No keys stored locally. All auth via managed identity (system-assigned) and DefaultAzureCredential.

### Video Submission Flow

#### REST API Path (Primary)

```
1. User selects video file
   ↓
2. Read video bytes (< 200 MB)
   ↓
3. POST /contentunderstanding/analyzers/prebuilt-videoSearch:analyzeBinary
   - Header: Authorization: Bearer {token}
   - Content-Type: application/octet-stream
   - Body: video binary
   ↓
4. Response: 202 Accepted + Operation-Location header
   ↓
5. Poll GET Operation-Location (every 5s, max 30 retries = 2.5 min timeout)
   ↓
6. When status == "succeeded", return result dict
   ↓
7. Extract descriptions, transcript, keyframes from result
```

#### SDK Path (Secondary, with Fallback)

```
1. Try import azure.ai.contentunderstanding
   ↓
   If success:
     - Use ContentUnderstandingClient(endpoint, credential)
     - Client.analyze_video_binary(video_bytes, deployment_name)
   
   If ImportError:
     - Fall back to REST API (same flow as above)
```

### Response Structure

Content Understanding returns a dict like:

```json
{
  "status": "succeeded",
  "result": {
    "videoDescription": {
      "description": "A person explains...",
      "keyframes": [
        {"timestamp": 0.5, "imageDescription": "Scene showing..."},
        ...
      ]
    },
    "transcription": {
      "vtt": "WEBVTT\n00:00:00 --> 00:00:05\nHello world\n...",
      "json": [{"startTime": 0, "endTime": 5, "text": "Hello world"}]
    }
  }
}
```

Extracted by `notebook_helpers.extract_descriptions_and_transcript()`:

```python
{
  "descriptions": ["Scene 1 description", "Scene 2 description", ...],
  "transcript": "Extracted text from WebVTT",
  "keyframes": [
    {"timestamp": 0.5, "description": "..."},
    ...
  ]
}
```

## Demo Notebook Flow

| Notebook | Purpose | Output |
|----------|---------|--------|
| 00_setup.ipynb | Venv, auth, install | Interactive kernel registration |
| 01_deploy_infra.ipynb | Deploy template, capture outputs | env/.env |
| 02_configure.ipynb | Verify connectivity, token flow | Console OK messages |
| 03_test_rest.ipynb | Analyze video via REST | outputs/video_analysis_result_rest.json |
| 04_test_sdk.ipynb | Analyze video via SDK (or fallback) | outputs/video_analysis_result_sdk.json |
| X_destroy.ipynb | Resource cleanup (soft-delete + purge) | (no output file) |

## Configuration Management

### Environment Variables

Written to `env/.env` by `01_deploy_infra.ipynb`:

```env
AZURE_RESOURCE_GROUP=rg-cu01-video
AZURE_AI_ENDPOINT=https://ai-cu01-xxxxx.openai.azure.com/
AZURE_AI_ACCOUNT_NAME=ai-cu01-xxxxx
CU_MODEL_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_AUTH_MODE=aad
```

Loaded in each notebook via:
```python
from dotenv import load_dotenv
load_dotenv(dotenv_path="../env/.env")
```

### Model Swapping Procedure

To use a different model:

1. Edit `infra/main.bicep` (parameters at top):
   ```bicep
   param deploymentName string = 'gpt-5.2'
   param modelName string = 'gpt-5.2'
   param modelVersion string = '2024-12-01'
   ```

2. Regenerate ARM template (optional, but recommended):
   ```bash
   cd infra
   bicep build main.bicep --outfile main.json
   ```

3. Redeploy by running `01_deploy_infra.ipynb` again
   - New deployment will use new model
   - Capacity can be adjusted in Bicep as well

## Cost Optimization

### Recommended for Prototyping

- **Model:** gpt-4.1-mini (~$0.015/min)
- **Capacity:** 1 TPM (tokens per minute; adjustable)
- **Region:** uksouth (pricing consistent)
- **Storage:** None (analyzed inline)

### Scaling to Production

- **Capacity:** Increase in Bicep param `capacity`
- **Model:** Switch to gpt-4.1 (if higher quality needed) or gpt-5.2 (for best accuracy)
- **Batching:** Process multiple videos asynchronously
- **Caching:** Store results in Azure Blob + Azure Search for re-use

## Error Handling

### REST API Errors

| Status | Meaning | Handling |
|--------|---------|----------|
| 400 | Bad request (video format, size) | Check video file format and size |
| 401 | Unauthorized | Re-run 00_setup.ipynb to re-auth |
| 402 | Quota exceeded | Check model capacity in Bicep |
| 408 | Timeout (poll exceeded 2.5 min) | Re-submit video or increase timeout |
| 500 | Server error | Retry (usually transient) |

### SDK Fallback

If `azure-ai-contentunderstanding` import fails, helper automatically uses REST API:

```python
try:
    from azure.ai.contentunderstanding import ContentUnderstandingClient
    # Use SDK
except ImportError:
    # Fall back to REST API
```

## Bicep to ARM Compilation Notes

The Bicep template includes:

- **Symbolic links:** None (uses built-in types)
- **Custom types:** None (uses primitives)
- **Conditional RBAC:** Only assigned if `deployerPrincipalId != ''`
- **Output values:**
  - aiServicesEndpoint
  - aiServicesAccountName
  - aiDeploymentName
  - resourceGroupName

To compile locally (requires Bicep CLI):

```bash
bicep build demos/cu01-foundry-video/infra/main.bicep --outfile demos/cu01-foundry-video/infra/main.json
```

Pre-compiled `main.json` is included; no need to compile to deploy.

## Testing the Demo

### Quick Validation

1. Run 00_setup (once)
2. Run 01_deploy_infra
3. Run 02_configure → should see "✓ Endpoint reachable" and "✓ Authentication successful"
4. Download a short public video (< 1 min, < 50 MB MP4)
5. Place in `data/` folder
6. Run 03_test_rest → should see descriptions and transcript

### Expected Output (REST)

```
==============================================================
SCENE DESCRIPTIONS
==============================================================

[Scene 1] A person sits at a desk and speaks directly to camera...

==============================================================
TRANSCRIPT
==============================================================

Hello, my name is [name]. Today I want to talk about...

==============================================================
KEYFRAMES
==============================================================

{'timestamp': 0.5, 'description': 'Person at desk, looking at camera...'}
...
```

## References

- [Content Understanding GA Release Notes](https://learn.microsoft.com/azure/ai-services/content-understanding/release-notes)
- [prebuilt-videoSearch Analyzer](https://learn.microsoft.com/azure/ai-services/content-understanding/concepts/analyzers#video-search)
- [API Versioning](https://learn.microsoft.com/azure/ai-services/content-understanding/api-versioning)
- [Bicep Language Reference](https://learn.microsoft.com/azure/azure-resource-manager/bicep/file)
