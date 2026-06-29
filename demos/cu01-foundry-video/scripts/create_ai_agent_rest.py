import argparse
import json
import os
import sys

import requests
from azure.identity import DefaultAzureCredential


DEFAULT_API_VERSION = "2024-05-01-preview"
TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"


def _build_auth_headers() -> dict:
    """Build API key or AAD auth headers for Azure OpenAI REST calls."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        return {"api-key": api_key}

    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token = credential.get_token(TOKEN_SCOPE)
    return {"Authorization": f"Bearer {token.token}"}


def create_agent(
    endpoint: str,
    deployment_name: str,
    agent_name: str,
    instructions: str,
    api_version: str = DEFAULT_API_VERSION,
) -> dict:
    """Create an assistant-style AI agent via Azure OpenAI REST API."""
    base = endpoint.rstrip("/")
    url = f"{base}/openai/assistants"

    headers = {
        "Content-Type": "application/json",
        **_build_auth_headers(),
    }

    payload = {
        "model": deployment_name,
        "name": agent_name,
        "instructions": instructions,
        "tools": [{"type": "code_interpreter"}],
    }

    response = requests.post(
        url,
        params={"api-version": api_version},
        headers=headers,
        json=payload,
        timeout=60,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            "Failed to create agent. "
            f"HTTP {response.status_code}: {response.text}"
        )

    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an Azure AI agent (assistant) via REST API."
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("AZURE_OPENAI_ENDPOINT"),
        help="Azure OpenAI endpoint (for example https://my-resource.openai.azure.com)",
    )
    parser.add_argument(
        "--deployment",
        default=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        help="Model deployment name (for example gpt-4.1-mini)",
    )
    parser.add_argument(
        "--name",
        default="quick-rest-agent",
        help="Agent name",
    )
    parser.add_argument(
        "--instructions",
        default="You are a helpful AI agent for quick prototyping.",
        help="Agent instructions",
    )
    parser.add_argument(
        "--api-version",
        default=os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION),
        help="Azure OpenAI API version",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional file path to save full JSON response",
    )

    args = parser.parse_args()

    if not args.endpoint:
        print("ERROR: Missing --endpoint or AZURE_OPENAI_ENDPOINT", file=sys.stderr)
        return 1
    if not args.deployment:
        print("ERROR: Missing --deployment or AZURE_OPENAI_DEPLOYMENT", file=sys.stderr)
        return 1

    try:
        created = create_agent(
            endpoint=args.endpoint,
            deployment_name=args.deployment,
            agent_name=args.name,
            instructions=args.instructions,
            api_version=args.api_version,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    agent_id = created.get("id", "<unknown>")
    print(f"Created agent id: {agent_id}")
    print(json.dumps(created, indent=2))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(created, f, indent=2)
        print(f"Saved response to: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
