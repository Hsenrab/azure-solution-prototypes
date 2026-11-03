"""Recompute and compare saved experiment evidence without Search requests."""

import argparse
from itertools import product
import json
from pathlib import Path
from typing import Any

from app.fixture import (
    API, canonical, declared_index, expected_ids, fixture_version,
    require_declared, sha256, validate_manifest_identity, write_json,
)
from app.reproduce import (
    Observation, SearchProfile, boundary_agreement, boundary_offsets, classification,
    normalized_request, query_settings, summarize,
)

REFERENCES = [
    "https://learn.microsoft.com/en-us/azure/search/hybrid-search-how-to-query#set-maxtextrecallsize-and-countandfacetmode-preview",
    "https://learn.microsoft.com/en-us/azure/search/search-pagination-page-layout",
    "https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking",
]


def inspect_case(path: Path, *, profile: SearchProfile | None = None) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    if (
        report["observationsFile"] != f"{path.stem}.pages.jsonl"
        or report["index"].get("actualSchemaFile") != f"{path.stem}.schema.json"
    ):
        raise ValueError("Case evidence filenames must belong to the selected report.")
    evidence_path = path.parent / report["observationsFile"]
    pages: list[Observation] = [
        json.loads(line) for line in evidence_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()
    ]
    manifest = report["fixture"]
    validate_manifest_identity(manifest)
    declared = declared_index(fixture_version(manifest)).as_dict()
    summary = summarize(
        pages, report["case"], manifest,
        report["summary"].get("indexCountStart"), report["summary"].get("indexCountEnd"),
    )
    offsets = boundary_offsets(summary, manifest["pageSize"])
    boundaries = boundary_agreement(pages, offsets)
    status, outcome, reasons = classification(summary, boundaries, pages, report["case"], manifest)
    errors = []
    if manifest["declaredSchemaSha256"] != sha256(canonical(declared)):
        errors.append("Declared schema identity differs from the fixture contract.")
    schema_file = report["index"].get("actualSchemaFile")
    if not schema_file or not (path.parent / schema_file).exists():
        errors.append("Actual index-schema evidence is missing.")
    else:
        actual_schema = json.loads((path.parent / schema_file).read_text(encoding="utf-8-sig"))
        try:
            require_declared(actual_schema, declared)
        except ValueError as error:
            errors.append(str(error))
        if any(actual_schema.get(key) for key in ("semantic", "scoringProfiles", "suggesters")):
            errors.append("Actual schema has excluded ranking settings.")
        if actual_schema.get("vectorSearch", {}).get("vectorizers"):
            errors.append("Actual schema has an excluded vectorizer.")
    expected_api = profile.api_version if profile else API
    expected_query = query_settings(report["case"], manifest, profile)
    for page in pages:
        actual = normalized_request(page["normalizedRequest"]) if page["normalizedRequest"] is not None else None
        if actual is not None:
            actual.pop("skip", None)
        if (
            actual != expected_query or page["apiVersion"] != expected_api or page["sendCount"] != 1
            or page["top"] != 5 or page["method"] != "POST"
            or page["pageNumber"] != page["skip"] // 5 + 1
            or (page["rowCount"] is not None and page["rowCount"] != len(page["ids"] or []))
            or page["runId"] != report["runId"] or page["language"] != report["language"]
            or page["case"] != report["case"]
            or manifest["indexName"] not in (page["path"] or "")
            or page["advertised"] != (
                summary["advertisedPages"] is not None and page["skip"] < summary["advertisedPages"] * 5
            )
        ):
            errors.append(f"Invalid observation contract: {page['phase']} offset {page['skip']}")
        if page["rowCount"] is not None and page["rowCount"] < 5 and page["continuation"]:
            if page["incompleteReason"] != "service-continuation":
                errors.append(f"Unmarked partial response with continuation: offset {page['skip']}")
    expected_scan = list(range(0, summary["scanPageCount"] * 5, 5))
    actual_scan = [page["skip"] for page in pages if page["phase"] == "scan"]
    if actual_scan != (expected_scan or [0]):
        errors.append("Primary scan offsets are missing, duplicated, or out of order.")
    for key, value in summary.items():
        if report["summary"].get(key) != value:
            errors.append(f"Saved summary differs from page evidence: {key}")
    if report["status"] != status or report["outcome"] != outcome:
        errors.append("Saved classification differs from page evidence.")
    if report["query"] != expected_query:
        errors.append("Declared query differs from the shared contract.")
    if report["client"]["configuredApi"] != expected_api:
        errors.append("Configured API mismatch.")
    expected_packages = (
        {"azure-search-documents": profile.sdk_version if profile else "12.0.0", "azure-identity": "1.25.3"}
        if report["language"] == "python" else
        {"Azure.Search.Documents": "12.0.0", "Azure.Identity": "1.21.0"}
    )
    if report["client"]["packages"] != expected_packages:
        errors.append("Runtime package metadata does not match the independently pinned clients.")
    if profile is not None and (report.get("profile") != profile.name or report["case"] != "hybrid"):
        errors.append("Preview profile identity mismatch.")
    if report["finishedAt"] is None:
        errors.append("Run was not finalized.")
    if report["index"]["name"] != manifest["indexName"]:
        errors.append("Index name differs from the verified fixture.")
    if not set(summary["reachableIds"]).issubset(expected_ids(manifest)):
        errors.append("Returned IDs outside the shared corpus.")
    if errors:
        status, outcome = "incomplete", "blocked/incomplete"
    for boundary in boundaries:
        boundary["results"] = [
            {key: pages[index][key] for key in ("reportedCount", "rowCount", "ids")}
            for index in boundary["observationIndexes"]
        ]
    return {
        "report": path.name, "observationsFile": evidence_path.name,
        "language": report["language"], "case": report["case"], "runId": report["runId"],
        "fixture": manifest, "index": report["index"], "environment": report["environment"],
        "client": report["client"], "query": report["query"], "summary": summary,
        "boundaries": boundaries, "status": status, "outcome": outcome,
        "reasons": sorted(set(reasons + errors)), "requestParity": not errors,
    }


def compare(run_dir: Path) -> dict[str, Any]:
    slots: dict[str, Any] = {}
    missing = []
    for language, case in product(("python", "dotnet"), ("keyword", "vector", "hybrid")):
        name = f"{language}-{case}"
        path = run_dir / f"{name}.json"
        slots[name] = inspect_case(path) if path.exists() else None
        if not path.exists():
            missing.append(name)
    present = [case for case in slots.values() if case is not None]
    identity_errors = []
    if present:
        first = present[0]
        for case in present:
            for key in ("fixture", "environment"):
                if case[key] != first[key]:
                    identity_errors.append(f"{case['report']}: {key} mismatch")
            if case["index"]["name"] != first["index"]["name"] or case["runId"] != run_dir.name:
                identity_errors.append(f"{case['report']}: index/run identity mismatch")
    pairwise = {}
    for case_name in ("keyword", "vector", "hybrid"):
        python, dotnet = (slots[f"{language}-{case_name}"] for language in ("python", "dotnet"))
        if python is None or dotnet is None:
            pairwise[case_name] = None
            continue
        left, right = (set(case["summary"]["reachableIds"]) for case in (python, dotnet))
        counts = [case["summary"]["reportedCount"] for case in (python, dotnet)]
        parity = python["query"] == dotnet["query"] and python["requestParity"] and dotnet["requestParity"]
        left_boundaries, right_boundaries = (
            {boundary["skip"]: boundary for boundary in case["boundaries"]} for case in (python, dotnet)
        )
        boundary_comparisons = []
        for offset in sorted(left_boundaries.keys() | right_boundaries.keys()):
            left_boundary, right_boundary = left_boundaries.get(offset), right_boundaries.get(offset)
            if (
                left_boundary is None or right_boundary is None
                or not left_boundary["results"] or not right_boundary["results"]
            ):
                boundary_comparisons.append({
                    "skip": offset, "presentIn": [
                        language for language, boundary in (("python", left_boundary), ("dotnet", right_boundary))
                        if boundary is not None and boundary["results"]
                    ],
                    "countAgreement": None, "sizeAgreement": None,
                    "idSetAgreement": None, "orderAgreement": None,
                })
                continue
            left_result, right_result = left_boundary["results"][0], right_boundary["results"][0]
            boundary_counts = (left_result["reportedCount"], right_result["reportedCount"])
            boundary_comparisons.append({
                "skip": offset, "presentIn": ["python", "dotnet"],
                "countAgreement": boundary_counts[0] == boundary_counts[1] if None not in boundary_counts else None,
                "sizeAgreement": (
                    left_result["rowCount"] == right_result["rowCount"]
                    if left_result["rowCount"] is not None and right_result["rowCount"] is not None else None
                ),
                "idSetAgreement": (
                    set(left_result["ids"]) == set(right_result["ids"])
                    if left_result["ids"] is not None and right_result["ids"] is not None else None
                ),
                "orderAgreement": (
                    left_result["ids"] == right_result["ids"]
                    if left_result["ids"] is not None and right_result["ids"] is not None else None
                ),
            })
        pairwise[case_name] = {
            "requestParity": parity,
            "countAgreement": counts[0] == counts[1] if None not in counts else None,
            "uniqueCountAgreement": len(left) == len(right),
            "scanBasisAgreement": python["summary"]["scanBasis"] == dotnet["summary"]["scanBasis"],
            "intersectionCount": len(left & right), "pythonOnlyIds": sorted(left - right),
            "dotnetOnlyIds": sorted(right - left),
            "duplicateAgreement": python["summary"]["duplicateIds"] == dotnet["summary"]["duplicateIds"],
            "boundaryOffsetsAgreement": [b["skip"] for b in python["boundaries"]] == [b["skip"] for b in dotnet["boundaries"]],
            "boundaries": boundary_comparisons,
            "outcomeAgreement": python["outcome"] == dotnet["outcome"],
        }
    overlaps = {}
    for language in ("python", "dotnet"):
        cases = {name: slots[f"{language}-{name}"] for name in ("keyword", "vector", "hybrid")}
        if all(cases.values()):
            ids = {name: set(case["summary"]["reachableIds"]) for name, case in cases.items()}
            overlaps[language] = {
                "keywordVector": len(ids["keyword"] & ids["vector"]),
                "vectorHybrid": len(ids["vector"] & ids["hybrid"]),
                "keywordHybrid": len(ids["keyword"] & ids["hybrid"]),
            }
        else:
            overlaps[language] = None
    controls = {
        language: bool(
            slots[f"{language}-keyword"] is not None
            and slots[f"{language}-keyword"]["summary"]["baselineValid"]
            and slots[f"{language}-keyword"]["status"] == "complete"
            and slots[f"{language}-vector"] is not None
            and slots[f"{language}-vector"]["status"] == "complete"
        ) for language in ("python", "dotnet")
    }
    complete = (
        not missing and not identity_errors and all(controls.values())
        and all(case["status"] == "complete" and case["requestParity"] for case in present)
        and all(pair is not None and pair["requestParity"] for pair in pairwise.values())
    )
    reproduced = [case["report"] for case in present if case["case"] == "hybrid" and case["outcome"] == "reproduced"]
    result = {
        "schemaVersion": 1, "runId": run_dir.name,
        "status": "complete" if complete else "blocked/incomplete",
        "cases": slots, "missingCases": missing, "identityMismatches": identity_errors,
        "pairwise": pairwise, "overlaps": overlaps, "controlValidity": controls,
        "hypothesis": (
            "Observed hybrid count gaps and empty advertised pages are consistent with a bounded candidate window; "
            "this is not proof of the customer's cause."
            if complete and reproduced else
            "No causal conclusion: measurements are incomplete or the specified symptom was not reproduced."
        ),
        "limitations": [
            "Service defaults (documented, not measured internally): text recall 1,000; countAllResults; vector candidates bounded by k.",
            "No orderBy is sent: documented default is descending search score; tied ordering is unspecified.",
            "Text/vector overlap is measured; their candidate sizes cannot simply be added.",
            "Equal start/end counts do not prove snapshot isolation or exclude intervening writes.",
            "Tied ordering alone is not an SDK defect; fixed synthetic vectors do not establish semantic quality.",
            "Different scan bases and absent vector counts limit count comparisons; unavailable agreement stays null.",
            "Customer package/API, index, ranking/filter/semantic settings and concurrent writes remain unverified.",
            "No production/beta suitability or GA date is asserted. A complete not-reproduced run is valid evidence.",
        ],
        "references": REFERENCES,
    }
    write_json(run_dir / "comparison.json", result)
    (run_dir / "comparison.md").write_text(render(result), encoding="utf-8")
    return result


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Hybrid pagination experiment", "", f"Run: `{result['runId']}`; status: **{result['status']}**", "",
        "## Observations", "",
        "| Case | Status/outcome | Reported | Unique IDs | Scan basis / pages | Populated / empty | Duplicates |",
        "|---|---|---:|---:|---|---|---:|",
    ]
    for name, case in result["cases"].items():
        if case is None:
            lines.append(f"| {name} | missing | — | — | — | — | — |")
            continue
        summary = case["summary"]
        lines.append(
            f"| [{name}]({case['report']}) | {case['status']} / {case['outcome']} | "
            f"{summary['reportedCount']} | {summary['uniqueReachableIds']} | "
            f"{summary['scanBasis']} / {summary['scanPageCount']} | "
            f"{summary['populatedPages']} / {summary['emptyPages']} | {len(summary['duplicateIds'])} |"
        )
    for name, case in result["cases"].items():
        if case is None:
            continue
        lines.extend([
            "", f"### {name}",
            f"- Evidence: [{case['observationsFile']}]({case['observationsFile']})",
            f"- Corpus: `{case['fixture']['corpusSha256']}`; schema: `{case['fixture']['declaredSchemaSha256']}`",
            f"- Index: `{case['index']['name']}`; endpoint: `{case['environment'].get('AZURE_SEARCH_ENDPOINT')}`",
            f"- Client/API: `{json.dumps(case['client'], sort_keys=True)}`",
            f"- Query: `{json.dumps(case['query'], sort_keys=True)}`",
            f"- Baseline: `{case['summary']['baselineValid']}`; reasons: `{case['reasons']}`",
            f"- Repeated boundaries: `{json.dumps(case['boundaries'], sort_keys=True)}`",
        ])
    lines.extend([
        "", "### Cross-client parity and overlaps",
        f"Controls: `{result['controlValidity']}`",
        f"Input mismatches: `{result['identityMismatches']}`",
        f"Overlaps: `{result['overlaps']}`",
    ])
    for name, pair in result["pairwise"].items():
        display_pair = None if pair is None else {
            key: len(value) if key.endswith("OnlyIds") else value for key, value in pair.items()
        }
        lines.append(f"- {name} (ID differences shown as counts; full IDs in JSON): `{json.dumps(display_pair, sort_keys=True)}`")
    lines.extend(["", "## Hypothesis", "", result["hypothesis"], "", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in result["limitations"])
    lines.extend(["", "## Authoritative references", ""])
    lines.extend(f"- {url}" for url in result["references"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    arguments = parser.parse_args()
    result = compare(arguments.run_dir)
    print(json.dumps({
        "status": result["status"], "missingCases": result["missingCases"],
        "controlValidity": result["controlValidity"], "report": str(arguments.run_dir / "comparison.md"),
    }, indent=2))
    raise SystemExit(0 if result["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
