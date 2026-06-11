from pathlib import Path
import shutil


def resolve_az_cli() -> str | None:
    """Return the Azure CLI executable path visible to the notebook kernel."""
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