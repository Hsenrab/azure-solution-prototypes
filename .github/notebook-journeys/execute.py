import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = ROOT / "demos" / "speech01-foundry-speech"
NOTEBOOKS = DEMO_ROOT / "notebooks"
DEMO_KERNEL = "speech01-foundry-speech"
SYSTEM_KERNEL = "python3"
CELL_TIMEOUT = 1800
JOURNEY = [
    "00_setup.ipynb",
    "01_deploy_infra.ipynb",
    "02_configure.ipynb",
    "03_test.ipynb",
    "04_function.ipynb",
]


def run_resource_group() -> str:
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "").strip()
    if not run_id or not attempt:
        raise RuntimeError("GitHub run identity is required for isolated resource naming.")
    return f"rg-speech01-{run_id}-{attempt}"


def execute_notebook(name: str, kernel_name: str) -> None:
    notebook = nbformat.read(NOTEBOOKS / name, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=CELL_TIMEOUT,
        kernel_name=kernel_name,
        resources={"metadata": {"path": str(NOTEBOOKS)}},
    )
    client.execute()


def cleanup_kernel() -> str:
    kernelspec = Path.home() / ".local" / "share" / "jupyter" / "kernels" / DEMO_KERNEL
    virtualenv = DEMO_ROOT / ".venv" / "bin" / "python"
    if kernelspec.is_dir() and virtualenv.exists():
        return DEMO_KERNEL
    return SYSTEM_KERNEL


def run_az(args: list[str], stage: str, check: bool = True) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            ["az", *args],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(stage) from error
    if check and result.returncode:
        raise RuntimeError(stage)
    return result


def belongs_to_run(item: dict, resource_group: str) -> bool:
    parts = str(item.get("id", "")).lower().split("/")
    try:
        group_index = parts.index("resourcegroups")
    except ValueError:
        return False
    return group_index + 1 < len(parts) and parts[group_index + 1] == resource_group.lower()


def list_run_deleted_accounts(resource_group: str) -> list[dict]:
    result = run_az(
        ["cognitiveservices", "account", "list-deleted", "--output", "json"],
        "list deleted run resources",
    )
    return [
        item
        for item in json.loads(result.stdout or "[]")
        if belongs_to_run(item, resource_group)
    ]


def resource_group_exists(resource_group: str) -> bool:
    result = run_az(["group", "exists", "--name", resource_group], "check run resource group")
    value = result.stdout.strip().lower()
    if value not in {"true", "false"}:
        raise RuntimeError("Azure CLI returned an invalid resource-group status.")
    return value == "true"


def run_ownership_marker(resource_group: str) -> Path | None:
    runner_temp = os.environ.get("RUNNER_TEMP", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "").strip()
    if not runner_temp or not run_id or not attempt:
        return None
    marker = Path(runner_temp) / f"speech01-{run_id}-{attempt}.owned"
    if marker.is_file() and marker.read_text(encoding="utf-8").strip() == resource_group:
        return marker
    return None


def verify_resource_group_ownership(resource_group: str) -> None:
    result = run_az(
        ["group", "show", "--name", resource_group, "--query", "tags", "--output", "json"],
        "read run resource-group ownership tags",
    )
    tags = json.loads(result.stdout or "{}") or {}
    if not isinstance(tags, dict):
        tags = {}
    if (
        tags.get("speech01-run-id") != os.environ.get("GITHUB_RUN_ID")
        or tags.get("speech01-run-attempt") != os.environ.get("GITHUB_RUN_ATTEMPT")
    ):
        raise RuntimeError("Resource group is not tagged as owned by this workflow run.")


def fallback_cleanup(resource_group: str) -> list[str]:
    errors = []
    try:
        exists = resource_group_exists(resource_group)
        if exists:
            try:
                verify_resource_group_ownership(resource_group)
            except (RuntimeError, ValueError, json.JSONDecodeError):
                return ["refuse cleanup of resource group not owned by this run"]
        elif run_ownership_marker(resource_group) is None:
            return []

        accounts_to_delete = []
        if exists:
            resources_result = run_az(
                [
                    "resource",
                    "list",
                    "--resource-group",
                    resource_group,
                    "--resource-type",
                    "Microsoft.CognitiveServices/accounts",
                    "--output",
                    "json",
                ],
                "list run Cognitive Services accounts",
            )
            accounts_to_delete = json.loads(resources_result.stdout or "[]")
            for account in accounts_to_delete:
                name = account.get("name")
                if name:
                    deleted = run_az(
                        [
                            "cognitiveservices",
                            "account",
                            "delete",
                            "--name",
                            name,
                            "--resource-group",
                            resource_group,
                            "--yes",
                        ],
                        "delete run Cognitive Services account",
                        check=False,
                    )
                    if deleted.returncode:
                        errors.append("delete run Cognitive Services account")

        accounts = list_run_deleted_accounts(resource_group)
        if exists and accounts_to_delete:
            for _ in range(12):
                if accounts or not resource_group_exists(resource_group):
                    break
                time.sleep(10)
                accounts = list_run_deleted_accounts(resource_group)

        for account in accounts:
            name = account.get("name")
            location = account.get("location")
            if not name or not location:
                errors.append("identify run soft-deleted account")
                continue
            purged = run_az(
                [
                    "cognitiveservices",
                    "account",
                    "purge",
                    "--name",
                    name,
                    "--location",
                    location,
                    "--resource-group",
                    resource_group,
                ],
                "purge run soft-deleted account",
                check=False,
            )
            if purged.returncode:
                errors.append("purge run soft-deleted account")
    except (RuntimeError, ValueError, json.JSONDecodeError):
        errors.append("enumerate run resources for cleanup")

    try:
        if resource_group_exists(resource_group):
            deleted = run_az(
                ["group", "delete", "--name", resource_group, "--yes"],
                "delete run resource group",
                check=False,
            )
            if deleted.returncode:
                errors.append("delete run resource group")
    except RuntimeError:
        errors.append("delete run resource group")

    try:
        if resource_group_exists(resource_group):
            errors.append("verify run resource group deletion")
        if list_run_deleted_accounts(resource_group):
            errors.append("verify run soft-deleted account purge")
    except (RuntimeError, ValueError, json.JSONDecodeError):
        errors.append("verify run cleanup")
    return errors


def write_summary(
    results: list[tuple[str, str]],
    cleanup_status: str,
    cleanup_errors: list[str],
    cleanup_notes: list[str],
) -> None:
    lines = ["## speech01 notebook journey", ""]
    lines.extend(f"- `{name}`: {status}" for name, status in results)
    lines.extend(["", f"- Cleanup: {cleanup_status}"])
    if cleanup_errors:
        lines.extend(["", "Cleanup issues:"])
        lines.extend(f"- {error}" for error in sorted(set(cleanup_errors)))
    if cleanup_notes:
        lines.extend(["", "Cleanup notes:"])
        lines.extend(f"- {note}" for note in cleanup_notes)
    summary = "\n".join(lines) + "\n"
    print(summary)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as output:
            output.write(summary)


def verify_cleanup(resource_group: str) -> list[str]:
    errors = []
    try:
        if resource_group_exists(resource_group):
            errors.append("run resource group still exists")
        if list_run_deleted_accounts(resource_group):
            errors.append("run soft-deleted Cognitive Services accounts remain")
    except (RuntimeError, ValueError, json.JSONDecodeError):
        errors.append("run cleanup verification failed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup-only", action="store_true")
    args = parser.parse_args()

    resource_group = run_resource_group()
    os.environ["AZURE_RESOURCE_GROUP"] = resource_group

    if args.cleanup_only:
        errors = fallback_cleanup(resource_group)
        write_summary([], "verified" if not errors else "failed", errors, [])
        return 1 if errors else 0

    results = []
    failure = None
    for name in JOURNEY:
        try:
            execute_notebook(
                name,
                SYSTEM_KERNEL if name == "00_setup.ipynb" else DEMO_KERNEL,
            )
            results.append((name, "passed"))
        except Exception as error:
            failure = (name, type(error).__name__)
            results.append((name, f"failed ({type(error).__name__})"))
            break

    cleanup_errors = []
    cleanup_notes = []
    cleanup_notebook_status = "failed"
    first_cleanup_error = None
    cleanup_required = False
    fallback_used = False
    try:
        if resource_group_exists(resource_group):
            cleanup_required = True
            verify_resource_group_ownership(resource_group)
            preferred_kernel = cleanup_kernel()
            try:
                execute_notebook("X_destroy.ipynb", preferred_kernel)
                cleanup_notebook_status = "passed"
            except Exception as error:
                first_cleanup_error = type(error).__name__
                if preferred_kernel != SYSTEM_KERNEL:
                    try:
                        execute_notebook("X_destroy.ipynb", SYSTEM_KERNEL)
                        cleanup_notebook_status = f"passed using fallback kernel ({first_cleanup_error})"
                        cleanup_notes.append(
                            f"X_destroy notebook succeeded with the system kernel after {first_cleanup_error}."
                        )
                    except Exception:
                        cleanup_errors.append(f"X_destroy notebook failed ({first_cleanup_error})")
                else:
                    cleanup_errors.append(f"X_destroy notebook failed ({first_cleanup_error})")
        elif run_ownership_marker(resource_group):
            cleanup_required = True
            cleanup_notebook_status = "not needed (run resource group already deleted)"
        else:
            cleanup_notebook_status = "not needed (run resource group was not created)"
    except (RuntimeError, ValueError, json.JSONDecodeError):
        cleanup_errors.append("verify run resource-group ownership")

    if cleanup_required:
        initial_verification_errors = []
        if cleanup_notebook_status == "passed" or run_ownership_marker(resource_group):
            initial_verification_errors = verify_cleanup(resource_group)
        if not cleanup_notebook_status.startswith("passed") or initial_verification_errors:
            fallback_used = True
            fallback_errors = fallback_cleanup(resource_group)
            final_verification_errors = verify_cleanup(resource_group)
            cleanup_errors.extend(fallback_errors)
            cleanup_errors.extend(final_verification_errors)
            if initial_verification_errors and not fallback_errors and not final_verification_errors:
                cleanup_notes.append(
                    "Initial cleanup verification found run resources; scoped fallback removed them."
                )

    cleanup_status = cleanup_notebook_status
    if cleanup_errors:
        cleanup_status = "failed"
    elif fallback_used:
        cleanup_status = "verified with run-scoped fallback"
    elif cleanup_notebook_status.startswith("passed"):
        cleanup_status = "verified"

    if failure:
        results.append(("Journey", f"failed at {failure[0]} ({failure[1]})"))
    write_summary(results, cleanup_status, cleanup_errors, cleanup_notes)
    return 1 if failure or cleanup_errors or cleanup_notebook_status == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
