"""HTTP-triggered function that shallow-clones a public repo and runs the
GitHub Copilot CLI (@github/copilot) in BYOK mode against a Foundry model.

Contract (POST /api/review):
    Request body: {} (empty — the target repo and model come from app settings)
    Response 200: {
        "review": str,           # markdown from the CLI
        "repo": str,             # cloned URL
        "prompt": str,           # exact prompt sent to Copilot
        "provider": {            # what the CLI routed to (never the key)
            "type": "azure",
            "base_url": "https://<foundry>.cognitiveservices.azure.com/",
            "model": "<deployment>"
        },
        "timing": {              # per-step seconds
            "clone_s": float,
            "copilot_s": float,
            "total_s": float
        },
        "repo_snapshot": {       # what Copilot actually saw after clone
            "file_count": int,
            "total_bytes": int,
            "top_files": [ {"path": str, "bytes": int}, ... ]  # up to 20
        },
        "stdout_tail": str,      # last ~1.5KB of CLI stdout
        "stderr_tail": str,      # last ~1.5KB of CLI stderr
        "invocation_id": str,    # Functions invocation id (App Insights operation_Id)
        "started_utc": str,      # ISO-8601 start timestamp (for App Insights time filter)
        "ended_utc": str         # ISO-8601 end timestamp
    }
    Response 500: same shape without "review", plus "error".

App settings consumed:
    SAMPLE_REPO_URL           — public Git URL to clone (shallow, depth 1)
    COPILOT_PROVIDER_BASE_URL — Foundry AIServices endpoint
    COPILOT_PROVIDER_TYPE     — "azure"
    COPILOT_PROVIDER_API_KEY  — Foundry AIServices account key
    COPILOT_MODEL             — Foundry model deployment name

Timeouts are set to 200s (below the 230s Azure Load Balancer HTTP ceiling).
"""
import datetime as _dt
import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

CLONE_TIMEOUT_S = 30
COPILOT_TIMEOUT_S = 180
REVIEW_PROMPT = (
    "Perform a concise code review of the repository in the current working directory. "
    "Return a markdown response with: a one-paragraph summary, then the top 5 issues or "
    "improvement opportunities as a numbered list. Keep the response under 400 words."
)


def _tail(text: str, max_chars: int = 1500) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return "..." + text[-max_chars:]


def _iso_utc(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts, tz=_dt.timezone.utc).isoformat(timespec="seconds")


def _snapshot_repo(root: Path, max_top_files: int = 20) -> dict:
    """Walk the cloned repo, skipping .git, and return counts + biggest files."""
    files: list[tuple[str, int]] = []
    total_bytes = 0
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        files.append((rel, size))
        total_bytes += size
    files.sort(key=lambda x: x[1], reverse=True)
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "top_files": [{"path": p, "bytes": b} for p, b in files[:max_top_files]],
    }


def _provider_public() -> dict:
    return {
        "type": os.environ.get("COPILOT_PROVIDER_TYPE", ""),
        "base_url": os.environ.get("COPILOT_PROVIDER_BASE_URL", ""),
        "model": os.environ.get("COPILOT_MODEL", ""),
    }


@app.function_name(name="CopilotReview")
@app.route(route="review", methods=["POST"])
def copilot_review(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    start = time.monotonic()
    start_wall = time.time()
    invocation_id = getattr(context, "invocation_id", "") or ""

    repo_url = os.environ["SAMPLE_REPO_URL"]
    provider_env = {
        "COPILOT_PROVIDER_BASE_URL": os.environ["COPILOT_PROVIDER_BASE_URL"],
        "COPILOT_PROVIDER_TYPE": os.environ["COPILOT_PROVIDER_TYPE"],
        "COPILOT_PROVIDER_API_KEY": os.environ["COPILOT_PROVIDER_API_KEY"],
        "COPILOT_MODEL": os.environ["COPILOT_MODEL"],
    }
    provider_public = _provider_public()
    common_headers = {"Access-Control-Allow-Origin": "*"}

    with tempfile.TemporaryDirectory(prefix="copilot-review-") as work_dir:
        # Step 1: shallow-clone the target repo.
        clone_start = time.monotonic()
        clone_result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, work_dir],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_S,
        )
        clone_s = round(time.monotonic() - clone_start, 2)

        if clone_result.returncode != 0:
            logging.error("git clone failed: %s", clone_result.stderr)
            end_wall = time.time()
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": f"git clone failed (exit {clone_result.returncode})",
                        "repo": repo_url,
                        "prompt": REVIEW_PROMPT,
                        "provider": provider_public,
                        "timing": {
                            "clone_s": clone_s,
                            "copilot_s": 0.0,
                            "total_s": round(time.monotonic() - start, 2),
                        },
                        "stderr_tail": _tail(clone_result.stderr),
                        "invocation_id": invocation_id,
                        "started_utc": _iso_utc(start_wall),
                        "ended_utc": _iso_utc(end_wall),
                    }
                ),
                status_code=500,
                mimetype="application/json",
                headers=common_headers,
            )

        repo_snapshot = _snapshot_repo(Path(work_dir))

        # Step 2: run the Copilot CLI in programmatic BYOK mode. -p makes the CLI
        # single-shot and login-free when COPILOT_PROVIDER_* is set.
        copilot_env = {**os.environ, **provider_env}
        copilot_start = time.monotonic()
        copilot_result = subprocess.run(
            ["copilot", "-p", REVIEW_PROMPT, "--allow-all-tools", "--no-color"],
            cwd=work_dir,
            env=copilot_env,
            capture_output=True,
            text=True,
            timeout=COPILOT_TIMEOUT_S,
        )
        copilot_s = round(time.monotonic() - copilot_start, 2)

    total_s = round(time.monotonic() - start, 2)
    end_wall = time.time()
    timing = {"clone_s": clone_s, "copilot_s": copilot_s, "total_s": total_s}

    if copilot_result.returncode != 0:
        logging.error(
            "copilot exited %s in %ss: %s",
            copilot_result.returncode,
            total_s,
            copilot_result.stderr,
        )
        return func.HttpResponse(
            json.dumps(
                {
                    "error": f"copilot CLI failed (exit {copilot_result.returncode})",
                    "repo": repo_url,
                    "prompt": REVIEW_PROMPT,
                    "provider": provider_public,
                    "timing": timing,
                    "repo_snapshot": repo_snapshot,
                    "stdout_tail": _tail(copilot_result.stdout),
                    "stderr_tail": _tail(copilot_result.stderr),
                    "invocation_id": invocation_id,
                    "started_utc": _iso_utc(start_wall),
                    "ended_utc": _iso_utc(end_wall),
                }
            ),
            status_code=500,
            mimetype="application/json",
            headers=common_headers,
        )

    logging.info(
        "copilot review succeeded in %ss (%s chars, %s files)",
        total_s,
        len(copilot_result.stdout),
        repo_snapshot["file_count"],
    )
    return func.HttpResponse(
        json.dumps(
            {
                "review": copilot_result.stdout,
                "repo": repo_url,
                "prompt": REVIEW_PROMPT,
                "provider": provider_public,
                "timing": timing,
                "repo_snapshot": repo_snapshot,
                "stdout_tail": _tail(copilot_result.stdout),
                "stderr_tail": _tail(copilot_result.stderr),
                "invocation_id": invocation_id,
                "started_utc": _iso_utc(start_wall),
                "ended_utc": _iso_utc(end_wall),
            }
        ),
        status_code=200,
        mimetype="application/json",
        headers=common_headers,
    )
