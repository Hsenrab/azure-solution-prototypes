# Azure AI Foundry Standards

## Use New Foundry Pattern
Use new Azure AI Foundry patterns, not classic Azure OpenAI/hub-era guidance.

## Required Research Before Changes
1. Confirm current stable Bicep API versions for every resource type used.
2. Confirm latest non-deprecated model and version for the target region.
3. Mark preview-only features as `[PREVIEW]` in notebook markdown.

## Resource and SDK Direction
- Prefer `kind: 'AIServices'` for new AI service resources.
- Use `GlobalStandard` where required by API version/SKU rules.
- Use endpoint patterns based on new Foundry AI services.
- Prefer `azure-ai-inference` patterns over legacy `openai.AzureOpenAI` unless there is a specific compatibility requirement.

## Model Hygiene
- Do not hardcode a model version in templates unless requested.
- Validate at implementation time from current catalog for the deployment region.
