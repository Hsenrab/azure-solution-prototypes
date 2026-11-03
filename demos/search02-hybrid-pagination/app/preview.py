"""Compare saved stable evidence with two configured Python preview experiments."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
from typing import Any, Literal

from app.compare import REFERENCES, inspect_case
from app.fixture import COUNT, expected_ids, load_environment, load_manifest, sha256, write_json
from app.reproduce import SearchProfile, run

PREVIEW_API = "2026-08-01-preview"
PREVIEW_SDK = "12.1.0b2"
Scenario = Literal["retrievable", "expanded"]


def profile(
    scenario: Scenario, *, sdk_model: bool = False, manifest: dict[str, Any] | None = None,
) -> SearchProfile:
    keyword_count = len(expected_ids(manifest, "keyword")) if manifest is not None else COUNT
    recall = {"retrievable": 1000, "expanded": keyword_count}[scenario]
    settings = {"maxTextRecallSize": recall, "countAndFacetMode": "countRetrievableResults"}
    model = None
    if sdk_model:
        from azure.search.documents.models import HybridSearch

        model = HybridSearch(max_text_recall_size=recall, count_and_facet_mode="countRetrievableResults")
    return SearchProfile(
        name=f"preview-retrievable-{recall}", sdk_version=PREVIEW_SDK,
        api_version=PREVIEW_API, hybrid_search=settings, sdk_hybrid_search=model,
    )


def validate_baseline(baseline: Path, manifest_path: Path, env_file: Path) -> dict[str, Any]:
    manifest, _ = load_manifest(manifest_path)
    evidence = inspect_case(baseline)
    if (
        evidence["language"] != "python" or evidence["case"] != "hybrid"
        or evidence["status"] != "complete" or not evidence["requestParity"]
    ):
        raise ValueError(f"Use a completed, verified stable Python hybrid baseline: {evidence['reasons']}")
    if evidence["fixture"] != manifest or evidence["environment"] != load_environment(env_file):
        raise ValueError("The baseline does not belong to this fixture/environment. Do not compare different indexes.")
    return evidence


def run_scenario(
    scenario: Scenario, baseline: Path, manifest_path: Path, env_file: Path, run_dir: Path,
) -> int:
    if version("azure-search-documents") != PREVIEW_SDK:
        raise ValueError(f"Use the isolated preview environment with azure-search-documents=={PREVIEW_SDK}.")
    evidence = validate_baseline(baseline, manifest_path, env_file)
    if evidence["fixture"]["fixtureVersion"] == 2 and evidence["runId"] != run_dir.name:
        raise ValueError("Mixed preview cases require the stable baseline from the same run.")
    return run(
        "hybrid", manifest_path, env_file, run_dir,
        profile=profile(scenario, sdk_model=True, manifest=evidence["fixture"]),
    )


def comparison(baseline: Path, run_dir: Path) -> dict[str, Any]:
    stable = inspect_case(baseline)
    if stable["case"] != "hybrid" or stable["language"] != "python":
        raise ValueError("The baseline must be a stable Python hybrid report.")
    cases: dict[str, Any] = {"stable-baseline": stable}
    missing = []
    mismatches = []
    for scenario in ("retrievable", "expanded"):
        expected = profile(scenario, manifest=stable["fixture"])
        path = run_dir / f"{expected.name}.json"
        case = inspect_case(path, profile=expected) if path.exists() else None
        cases[expected.name] = case
        if case is None:
            missing.append(expected.name)
            continue
        for key in ("fixture", "environment"):
            if case[key] != stable[key]:
                mismatches.append(f"{expected.name}: {key} mismatch")
        query = dict(case["query"])
        query.pop("hybridSearch", None)
        if (
            query != stable["query"] or case["index"]["name"] != stable["index"]["name"]
            or case["runId"] != run_dir.name
        ):
            mismatches.append(f"{expected.name}: unexpected index/query/run difference")
    keyword_path = baseline.parent / "python-keyword.json"
    keyword = inspect_case(keyword_path) if keyword_path.exists() else None
    keyword_valid = bool(
        keyword and keyword["status"] == "complete" and keyword["summary"]["baselineValid"]
        and keyword["fixture"] == stable["fixture"] and keyword["environment"] == stable["environment"]
    )
    observations = {}
    stable_ids = set(stable["summary"]["reachableIds"])
    for name, case in cases.items():
        if case is None:
            observations[name] = None
            continue
        summary = case["summary"]
        outside = [
            result for boundary in case["boundaries"]
            if summary["advertisedPages"] is not None
            and boundary["skip"] >= summary["advertisedPages"] * 5
            for result in boundary["results"]
        ]
        beyond = any(result["rowCount"] is not None and result["rowCount"] > 0 for result in outside)
        ids = set(summary["reachableIds"])
        observations[name] = {
            "countAlignmentVerified": (
                case["status"] == "complete" and summary["reportedMinusReachable"] == 0
                and summary["emptyPages"] == 0 and not summary["duplicateIds"] and not beyond
            ),
            "resultsBeyondAdvertisedRange": beyond,
            "newUniqueIdsVersusStable": len(ids - stable_ids),
            "sharedIdsWithStable": len(ids & stable_ids),
            "duplicateExcessRows": summary["totalRows"] - summary["uniqueReachableIds"],
        }
    complete = bool(
        not missing and not mismatches
        and all(case["status"] == "complete" and case["requestParity"] for case in cases.values())
    )
    result = {
        "schemaVersion": 1, "runId": run_dir.name,
        "status": "complete-with-limitations" if complete else "blocked/incomplete",
        "measurementsComplete": complete, "cases": cases, "observations": observations,
        "missingCases": missing, "identityMismatches": mismatches,
        "baselineReference": {
            "report": str(baseline.resolve()), "reportSha256": sha256(baseline.read_bytes()),
            "observationsSha256": sha256((baseline.parent / stable["observationsFile"]).read_bytes()),
            "keywordBaselineValid": keyword_valid,
        },
        "causalAcceptance": "not-established" if keyword_valid else "blocked/incomplete",
        "limitations": [
            "The selected short comparison changes Python SDK, REST API and hybrid settings together; it does not isolate an SDK-only fix.",
            "This is Python azure-search-documents 12.1.0b2, not execution of .NET Azure.Search.Documents 12.1.0-beta.2.",
            "The stable evidence is historical and reused unchanged. Same hashes/counts do not establish snapshot isolation across runs.",
            "Causal interpretation requires a valid original keyword complete-ID control; inspect keywordBaselineValid above. Duplicate/missing IDs, when present, are a confounder, not a proven score-tie cause.",
            "Full advertised scans and boundary probes are retained. Results beyond the advertised range invalidate a count-alignment claim.",
            "Larger recall can increase resource usage/latency; complete unique-ID coverage is measured rather than assumed.",
            "Preview availability is not production approval, a GA commitment, or proof of the customer's exact request.",
        ],
        "references": [
            *REFERENCES,
            "https://pypi.org/project/azure-search-documents/12.1.0b2/",
            "https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.models.hybridsearch?view=azure-python-preview",
        ],
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "preview-comparison.json", result)
    (run_dir / "preview-comparison.md").write_text(render(result), encoding="utf-8")
    return result


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Stable versus configured preview hybrid search", "",
        f"Run: `{result['runId']}`; measurements: **{result['status']}**; "
        f"causal acceptance: **{result['causalAcceptance']}**", "",
        "| Scenario | SDK / API | Text recall / count mode | Reported | Unique | Populated / empty | Count aligned? | Outcome |",
        "|---|---|---|---:|---:|---|---|---|",
    ]
    for name, case in result["cases"].items():
        if case is None:
            lines.append(f"| {name} | missing | — | — | — | — | — | missing |")
            continue
        summary = case["summary"]
        settings = case["query"].get("hybridSearch")
        label = f"{settings['maxTextRecallSize']} / {settings['countAndFacetMode']}" if settings else "defaults (not explicitly set)"
        lines.append(
            f"| {name} | {case['client']['packages']['azure-search-documents']} / {case['client']['configuredApi']} | "
            f"{label} | {summary['reportedCount']} | {summary['uniqueReachableIds']} | "
            f"{summary['populatedPages']} / {summary['emptyPages']} | "
            f"{result['observations'][name]['countAlignmentVerified']} | {case['outcome']} |"
        )
    lines.extend(["", "## Observations", ""])
    for name, case in result["cases"].items():
        if case is None:
            continue
        lines.extend([
            f"### {name}",
            f"- Evidence: `{case['report']}`, `{case['observationsFile']}`.",
            f"- Scan coverage: {case['summary']['scanCoverage']}; reasons: `{case['reasons']}`.",
            f"- Facts: `{json.dumps(result['observations'][name], sort_keys=True)}`.",
            f"- Two-observation boundaries: `{json.dumps(case['boundaries'], sort_keys=True)}`.", "",
        ])
    lines.extend([
        "## Interpretation", "",
        "The retrievable-count scenario tests whether advertised pages align with the configured candidate window. "
        "The larger-window scenario tests whether additional keyword candidates become reachable. "
        "Read the actual count-alignment and unique-ID results above: neither improvement is assumed.",
        "",
        f"Missing cases: `{result['missingCases']}`; input mismatches: `{result['identityMismatches']}`.",
        f"Original keyword control valid: `{result['baselineReference']['keywordBaselineValid']}`.", "",
        "## Limits and production scope", "",
    ])
    lines.extend(f"- {text}" for text in result["limitations"])
    lines.extend(["", "## Sources", ""])
    lines.extend(f"- {url}" for url in result["references"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    measure = commands.add_parser("run")
    measure.add_argument("--scenario", choices=("retrievable", "expanded"), required=True)
    measure.add_argument("--manifest", type=Path, required=True)
    measure.add_argument("--env-file", type=Path, required=True)
    for subcommand in (measure, commands.add_parser("compare")):
        subcommand.add_argument("--baseline", type=Path, required=True)
        subcommand.add_argument("--run-dir", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.command == "run":
        raise SystemExit(run_scenario(
            arguments.scenario, arguments.baseline, arguments.manifest, arguments.env_file, arguments.run_dir,
        ))
    result = comparison(arguments.baseline, arguments.run_dir)
    print(json.dumps({
        "status": result["status"], "causalAcceptance": result["causalAcceptance"],
        "observations": result["observations"], "report": str(arguments.run_dir / "preview-comparison.md"),
    }, indent=2))
    raise SystemExit(0 if result["measurementsComplete"] else 1)


if __name__ == "__main__":
    main()
