#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <resource-group> <account-name> <deployment-name> [model-name] [model-version]"
  exit 1
fi

RESOURCE_GROUP="$1"
ACCOUNT_NAME="$2"
DEPLOYMENT_NAME="$3"
MODEL_NAME="${4:-gpt-4o-mini}"
MODEL_VERSION="${5:-2024-07-18}"

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "infra/main.bicep" \
  --parameters \
    location=swedencentral \
    accountName="$ACCOUNT_NAME" \
    deploymentName="$DEPLOYMENT_NAME" \
    modelName="$MODEL_NAME" \
    modelVersion="$MODEL_VERSION"
