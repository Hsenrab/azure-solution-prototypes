# Custom Function App image: Python 3.12 base + git + Node 20 + GitHub Copilot CLI.
# Built in ACR by notebook 02 via `az acr build` (no local Docker required).

FROM mcr.microsoft.com/azure-functions/python:4-python3.12

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    PYTHONUNBUFFERED=1

# Install git (for cloning the sample repo) and Node.js 20 (runtime for @github/copilot).
# Pin Node major version via NodeSource setup script; keep the layer slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @github/copilot \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify the CLI is on PATH at build time — fail fast if the install regressed.
RUN copilot --version && git --version && node --version

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

COPY . /home/site/wwwroot
