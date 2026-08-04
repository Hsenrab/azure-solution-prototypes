from __future__ import annotations

import shutil


def resolve_az_cli() -> str:
    """Resolve Azure CLI on Windows and non-Windows hosts."""
    return shutil.which("az") or shutil.which("az.cmd") or ""