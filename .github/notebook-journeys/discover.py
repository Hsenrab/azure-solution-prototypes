import json
import os
import subprocess
import sys


def git_paths(*args):
    output = subprocess.check_output(["git", *args])
    return [os.fsdecode(path) for path in output.split(b"\0") if path]


def notebook_demos(ref):
    demos = set()
    for path in git_paths("ls-tree", "-r", "--name-only", "-z", ref):
        parts = path.split("/")
        if (
            len(parts) >= 4
            and parts[0] == "demos"
            and parts[2] == "notebooks"
            and path.endswith(".ipynb")
        ):
            demos.add(parts[1])
    return demos


def is_documentation(path):
    if path.endswith(".ipynb"):
        return False
    parts = path.split("/")
    name = parts[-1].lower()
    return (
        "docs" in parts
        or name == "metadata.json"
        or name == ".gitkeep"
        or name.startswith("readme")
        or name.endswith((".md", ".markdown", ".rst", ".adoc"))
    )


def main():
    event = os.environ["GITHUB_EVENT_NAME"]
    demos = notebook_demos("HEAD")
    removed = set()

    if event == "workflow_dispatch":
        raw_names = os.environ["INPUT_DEMOS"].strip()
        all_demos = os.environ["INPUT_ALL_DEMOS"] == "true"
        if bool(raw_names) == all_demos:
            raise ValueError("Specify either demos or all_demos, but not both.")
        if all_demos:
            selected = demos
        else:
            names = [name.strip() for name in raw_names.split(",")]
            if any(not name for name in names):
                raise ValueError("The demo list must not contain empty names.")
            selected = set(names)
            invalid = selected - demos
            if invalid:
                raise ValueError(f"Unknown notebook demos: {json.dumps(sorted(invalid))}")
    elif event == "push":
        before = os.environ["PUSH_BEFORE"]
        after = os.environ["PUSH_AFTER"]
        if before == "0" * 40:
            paths = git_paths("ls-tree", "-r", "--name-only", "-z", after)
        else:
            if subprocess.run(
                ["git", "cat-file", "-e", f"{before}^{{commit}}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode:
                subprocess.check_call(["git", "fetch", "--no-tags", "origin", before])
            paths = git_paths("diff", "--no-renames", "--name-only", "-z", before, after, "--")
        selected = set()
        for path in paths:
            if is_documentation(path):
                continue
            if path == ".github/workflows/notebook-journeys.yml" or path.startswith(
                ".github/notebook-journeys/"
            ):
                selected = demos.copy()
                break
            parts = path.split("/")
            if len(parts) >= 3 and parts[0] == "demos":
                if parts[1] in demos:
                    selected.add(parts[1])
                else:
                    removed.add(parts[1])
    else:
        raise ValueError(f"Unsupported event: {event}")

    selected = sorted(selected)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        print(f"demos={json.dumps(selected, ensure_ascii=True)}", file=output)
        print(f"has_demos={str(bool(selected)).lower()}", file=output)

    summary = [
        "## Notebook journey selection",
        "",
        f"Selected demos: {json.dumps(selected, ensure_ascii=True)}",
        "",
        "Selection only: notebooks were not executed and Azure resources were not provisioned.",
    ]
    if removed:
        summary.extend(
            ["", f"Changed demo paths without remaining notebooks: {json.dumps(sorted(removed), ensure_ascii=True)}"]
        )
    if not selected:
        summary.extend(["", "No notebook demos selected; no matrix jobs will run."])
    text = "\n".join(summary) + "\n"
    print(text)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
        output.write(text)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"Discovery failed: {error}", file=sys.stderr)
        sys.exit(1)
