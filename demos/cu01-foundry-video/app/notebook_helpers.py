"""Shared helpers for Content Understanding video analysis."""

import os
import json
import time
import requests
from azure.core.credentials import TokenCredential


def analyze_video_rest(
    endpoint: str,
    deployment_name: str,
    video_path: str,
    credential: TokenCredential,
    api_version: str = "2025-11-01",
    max_polls: int = 120,
    poll_interval: int = 5,
) -> dict:
    """
    Analyze video using Azure Content Understanding REST API.
    
    Args:
        endpoint: Content Understanding endpoint URL
        deployment_name: Model deployment name (unused in prebuilt analyzer but kept for consistency)
        video_path: Path to local video file
        credential: Azure credential for authentication
        api_version: Content Understanding API version
        max_polls: Maximum number of poll attempts
        poll_interval: Seconds between polls
    
    Returns:
        Analysis result as dict
    """
    # Get auth token
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/octet-stream",
    }
    
    # Read video file
    with open(video_path, "rb") as f:
        video_data = f.read()
    
    # POST video for analysis
    analyze_url = f"{endpoint.rstrip('/')}/contentunderstanding/analyzers/prebuilt-videoSearch:analyzeBinary"
    params = {"api-version": api_version}
    
    print(f"Submitting video ({len(video_data) / 1024 / 1024:.1f} MB) for analysis...")
    response = requests.post(
        analyze_url,
        params=params,
        headers=headers,
        data=video_data,
        timeout=600,
    )
    response.raise_for_status()
    
    # Get operation location from response header
    operation_location = response.headers.get("Operation-Location")
    if not operation_location:
        raise ValueError("No Operation-Location header in response")
    
    print(f"Analysis submitted. Polling for results...")
    
    # Poll for completion
    for poll_count in range(max_polls):
        time.sleep(poll_interval)
        
        poll_response = requests.get(
            operation_location,
            params={"api-version": api_version},
            headers={"Authorization": f"Bearer {token.token}"},
            timeout=30,
        )
        poll_response.raise_for_status()
        
        result = poll_response.json()
        status = result.get("status", "").lower()
        
        print(f"  Poll {poll_count + 1}: status={status}")
        
        if status == "succeeded":
            print("Analysis complete!")
            return result
        elif status == "failed":
            raise RuntimeError(f"Analysis failed: {result.get('error', 'Unknown error')}")
    
    raise TimeoutError(f"Analysis did not complete after {max_polls} polls")


def analyze_video_sdk(
    endpoint: str,
    deployment_name: str,
    video_path: str,
    credential: TokenCredential,
    api_version: str = "2025-11-01",
    max_polls: int = 120,
    poll_interval: int = 5,
) -> dict:
    """
    Analyze video using Azure Content Understanding SDK.
    
    Args:
        endpoint: Content Understanding endpoint URL
        deployment_name: Model deployment name (unused in prebuilt analyzer but kept for consistency)
        video_path: Path to local video file
        credential: Azure credential for authentication
        api_version: Content Understanding API version
        max_polls: Maximum number of poll attempts
        poll_interval: Seconds between polls
    
    Returns:
        Analysis result as dict
    
    Note:
        Falls back to REST if SDK is not available.
    """
    try:
        from azure.ai.contentunderstanding import ContentUnderstandingClient
    except ImportError:
        print("SDK not available, falling back to REST API...")
        return analyze_video_rest(
            endpoint, deployment_name, video_path, credential, api_version, max_polls, poll_interval
        )
    
    # Initialize SDK client
    client = ContentUnderstandingClient(endpoint=endpoint, credential=credential)
    
    # Read video file
    with open(video_path, "rb") as f:
        video_data = f.read()
    
    print(f"Submitting video ({len(video_data) / 1024 / 1024:.1f} MB) for analysis via SDK...")
    
    # Submit analysis
    operation = client.begin_analyze_document_from_url(
        analyzer_id="prebuilt-videoSearch",
        bytes_content=video_data,
        content_type="video/mp4",  # Adjust based on actual video format
    )
    
    print("Analysis submitted. Polling for results...")
    
    # Poll for completion
    result = operation.result()
    print("Analysis complete!")
    
    # Convert to dict if needed
    if hasattr(result, "as_dict"):
        return result.as_dict()
    return result


def extract_descriptions_and_transcript(result: dict) -> dict:
    """
    Extract scene descriptions and transcript from Content Understanding result.
    
    Args:
        result: Analysis result dict from REST or SDK
    
    Returns:
        Dict with 'descriptions', 'transcript', and 'keyframes'
    """
    descriptions = []
    keyframes = []
    transcript_lines = []
    
    # Parse markdown output if present
    if "contents" in result:
        for content in result.get("contents", []):
            markdown = content.get("markdown", "")
            if markdown:
                # Simple extraction: split by "# Video:" to find segments
                segments = markdown.split("# Video:")
                for segment in segments[1:]:  # Skip first empty split
                    lines = segment.strip().split("\n")
                    if lines:
                        # First line is typically timestamp and description
                        descriptions.append(lines[0])
                        
                        # Extract transcript lines (between "Transcript" and "Key Frames")
                        in_transcript = False
                        for line in lines:
                            if line.startswith("Transcript"):
                                in_transcript = True
                            elif line.startswith("Key Frames"):
                                in_transcript = False
                            elif in_transcript and line.strip().startswith("WEBVTT") is False and line.strip():
                                transcript_lines.append(line.strip())
                            
                            # Extract keyframe references
                            if "keyFrame." in line:
                                keyframes.append(line.strip())
    
    # Also parse JSON fields if present
    if "contents" in result:
        for content in result.get("contents", []):
            if "fields" in content:
                fields = content["fields"]
                if "description" in fields:
                    descriptions.append(fields["description"]["value"])
    
    return {
        "descriptions": descriptions,
        "transcript": "\n".join(transcript_lines),
        "keyframes": keyframes,
    }


def resolve_az_cli():
    """Return the Azure CLI executable path visible to the notebook kernel."""
    import shutil
    from pathlib import Path

    az_in_path = shutil.which("az")
    if az_in_path:
        return az_in_path

    windows_fallbacks = [
        Path(r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"),
        Path(r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"),
    ]
    for candidate in windows_fallbacks:
        if candidate.exists():
            return str(candidate)

    return None
