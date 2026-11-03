"""Explain saved mixed-fixture measurements without issuing Search requests."""

import argparse
import json
from pathlib import Path
from typing import Any

from app.compare import inspect_case
from app.fixture import expected_ids, fixture_version, load_manifest, sha256, write_json
from app.preview import profile


def comparison(manifest_path: Path, run_dir: Path) -> dict[str, Any]:
    manifest, documents = load_manifest(manifest_path)
    if fixture_version(manifest) != 2:
        raise ValueError("Contribution review requires the verified version-2 mixed fixture.")
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Mixed run directory does not exist: {run_dir}")
    profiles = {profile(scenario, manifest=manifest).name: profile(scenario, manifest=manifest)
                for scenario in ("retrievable", "expanded")}
    names = [f"{language}-{case}" for language in ("python", "dotnet")
             for case in ("keyword", "vector", "hybrid")] + list(profiles)
    cases: dict[str, Any] = {}
    missing: list[str] = []
    invalid: dict[str, str] = {}
    mismatches: list[str] = []
    references: dict[str, Any] = {}
    environment = None
    for name in names:
        path = run_dir / f"{name}.json"
        cases[name] = None
        if not path.exists():
            missing.append(name)
            continue
        try:
            case = inspect_case(path, profile=profiles.get(name))
            references[name] = {
                "report": path.name, "reportSha256": sha256(path.read_bytes()),
                "observationsFile": case["observationsFile"],
                "observationsSha256": sha256((run_dir / case["observationsFile"]).read_bytes()),
                "schemaFile": case["index"]["actualSchemaFile"],
                "schemaSha256": sha256((run_dir / case["index"]["actualSchemaFile"]).read_bytes()),
            }
        except (OSError, ValueError, KeyError, TypeError) as error:
            invalid[name] = f"{type(error).__name__}: {error}"
            continue
        cases[name] = case
        expected_language, expected_case = ("python", "hybrid") if name in profiles else name.split("-")
        if (
            case["fixture"] != manifest or case["index"]["name"] != manifest["indexName"]
            or case["runId"] != run_dir.name or case["language"] != expected_language
            or case["case"] != expected_case
        ):
            mismatches.append(f"{name}: fixture/index/run/client/case mismatch")
        if environment is None:
            environment = case["environment"]
        if case["environment"] != environment:
            mismatches.append(f"{name}: environment mismatch")

    def valid(name: str) -> bool:
        case = cases[name]
        return bool(case and case["status"] == "complete" and case["requestParity"])

    controls = {
        language: bool(
            valid(f"{language}-keyword") and valid(f"{language}-vector")
            and cases[f"{language}-keyword"]["summary"]["baselineValid"]
            and cases[f"{language}-vector"]["summary"]["vectorMembershipValid"]
        ) for language in ("python", "dotnet")
    }
    controls_valid = all(controls.values()) and not mismatches
    observed: dict[str, Any] = {}
    counts: dict[str, Any] = {}
    additions: dict[str, Any] = {}
    text = {row["id"]: row["content"] for row in documents}
    groups = {name: set(ids) for name, ids in manifest["membership"].items()}
    for name, case in cases.items():
        if case is None:
            observed[name] = None
            counts[name] = None
            continue
        summary = case["summary"]
        ids = set(summary["reachableIds"])
        observed[name] = {
            "ids": sorted(ids), "complete": valid(name),
            "groups": {group: sorted(ids & members) for group, members in groups.items()},
            "provenance": "saved-primary-page-observations",
        }
        outside = [
            result for boundary in case["boundaries"]
            if summary["advertisedPages"] is not None
            and boundary["skip"] >= summary["advertisedPages"] * manifest["pageSize"]
            for result in boundary["results"]
        ]
        beyond = any(row["rowCount"] is not None and row["rowCount"] > 0 for row in outside)
        aligned = bool(
            valid(name) and summary["reportedCount"] is not None and summary["scanCoverage"] == 1
            and summary["reportedMinusReachable"] == 0 and not summary["duplicateIds"]
            and summary["emptyPages"] == 0 and outside and not beyond
        )
        counts[name] = {
            **summary, "boundaries": case["boundaries"],
            "duplicateExcessRows": summary["totalRows"] - summary["uniqueReachableIds"],
            "resultsBeyondAdvertisedRange": beyond, "countAlignmentVerified": aligned,
        }
        if case["case"] == "hybrid":
            declared_only = sorted(ids & groups["vectorOnly"])
            established = controls_valid and valid(name)
            additions[name] = {
                "observedDeclaredVectorOnlyIds": declared_only,
                "verifiedVectorOnlyIds": declared_only if established else None,
                "fullKeywordVectorSharedCandidates": sorted(ids & groups["shared"]) if established else None,
                "missingExpectedVectorOnlyIds": sorted(groups["vectorOnly"] - ids),
                "textExamples": [
                    {"id": identifier, "content": text[identifier], "textSource": "verified-fixture"}
                    for identifier in declared_only[:3]
                ],
            }
    complete = not missing and not invalid and not mismatches and all(valid(name) for name in names)
    expanded = cases.get("preview-retrievable-6158")
    expanded_valid = bool(
        expanded and counts["preview-retrievable-6158"]["countAlignmentVerified"]
        and set(expanded["summary"]["reachableIds"]) == expected_ids(manifest)
        and expanded["summary"]["reportedCount"] == 6183
        and expanded["summary"]["populatedPages"] == 1237
        and any(
            boundary["skip"] == 6180 and all(row["rowCount"] == 3 for row in boundary["results"])
            for boundary in expanded["boundaries"]
        )
    )
    accepted = bool(
        complete and controls_valid and expanded_valid and len(additions) == 4
        and all(
            row["verifiedVectorOnlyIds"] == sorted(groups["vectorOnly"])
            and not cases[name]["summary"]["duplicateIds"] for name, row in additions.items()
        )
    )
    overlaps = {
        language: sorted(
            set(cases[f"{language}-keyword"]["summary"]["reachableIds"])
            & set(cases[f"{language}-vector"]["summary"]["reachableIds"])
        ) if controls_valid else None for language in ("python", "dotnet")
    }
    result = {
        "schemaVersion": 1, "runId": run_dir.name, "fixture": manifest, "index": manifest["indexName"],
        "indexedDocumentCount": manifest["recordCount"], "keywordMatchCount": manifest["keywordMatchCount"],
        "vectorCandidateCount": manifest["candidateCount"],
        "cases": cases, "missingCases": missing, "invalidCases": invalid, "identityMismatches": mismatches,
        "evidenceReferences": references, "expectedMembership": manifest["membership"],
        "observedMembership": observed, "controlValidity": controls, "fullKeywordVectorIntersection": overlaps,
        "hybridContributions": additions, "keywordWindowMembership": {"status": "not-observed", "ids": None},
        "countFindings": counts, "measurementsComplete": bool(complete), "contributionAcceptance": accepted,
        "status": "complete" if accepted else "blocked/incomplete",
        "limitations": [
            "Group labels apply only to this fixed query and k=50, not to documents under arbitrary queries.",
            "Engineered vector proximity is not evidence of embedding quality or semantic understanding.",
            "Text examples come from the verified local fixture, not the ID-only measured Search response.",
            "Internal keyword-window membership is not observed; shared full-keyword matches may be outside that window.",
            "Incomplete keyword/vector controls cannot establish accepted vector-only contributions.",
            "SDK, API and hybrid settings change together in preview cases; this is not an isolated SDK fix or production approval.",
            "Ready receipts and ID/content inventories do not prove hidden-vector immutability or snapshot isolation.",
            "This follow-on does not resolve or waive the original failed keyword-control acceptance.",
        ],
    }
    write_json(run_dir / "contribution-comparison.json", result)
    (run_dir / "contribution-comparison.md").write_text(render(result), encoding="utf-8")
    return result


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Mixed-fixture vector contributions", "",
        f"Run: `{result['runId']}`; status: **{result['status']}**.",
        f"Indexed: {result['indexedDocumentCount']:,}; keyword matches: {result['keywordMatchCount']:,}; "
        f"vector candidates: {result['vectorCandidateCount']}.",
        "Declared fixed-query groups: keyword-only 6,133; shared 25; vector-only 25.",
        "Internal keyword-window membership: **not observed** (IDs null).", "",
        "| Case | Reported | Unique | Keyword-only / shared / vector-only observed | Populated / empty | Count aligned |",
        "|---|---:|---:|---|---|---|",
    ]
    for name, case in result["cases"].items():
        if case is None:
            lines.append(f"| {name} | unavailable | unavailable | unavailable | unavailable | no |")
            continue
        finding = result["countFindings"][name]
        groups = result["observedMembership"][name]["groups"]
        lines.append(
            f"| {name} | {finding['reportedCount']} | {finding['uniqueReachableIds']} | "
            f"{len(groups['keywordOnly'])} / {len(groups['shared'])} / {len(groups['vectorOnly'])} | "
            f"{finding['populatedPages']} / {finding['emptyPages']} | {finding['countAlignmentVerified']} |"
        )
    lines += ["", "## Actual hybrid IDs with verified fixture text", ""]
    for name, finding in result["hybridContributions"].items():
        verified = finding["verifiedVectorOnlyIds"]
        lines.append(f"### {name}")
        lines.append(f"Verified non-keyword additions: {len(verified) if verified is not None else 'not established'}.")
        for example in finding["textExamples"]:
            lines.append(f"- `{example['id']}`: {example['content']} (`textSource: verified-fixture`)")
    lines += [
        "", "## Evidence and acceptance", "",
        f"- Measurements complete: {result['measurementsComplete']}",
        f"- Contribution acceptance: {result['contributionAcceptance']}",
        f"- Controls: {json.dumps(result['controlValidity'])}",
        f"- Missing cases: {', '.join(result['missingCases']) or 'none'}",
        f"- Invalid cases: {json.dumps(result['invalidCases'])}",
        f"- Identity mismatches: {json.dumps(result['identityMismatches'])}",
        "- Inspect [full JSON](./contribution-comparison.json) for exact expected/observed IDs, duplicates, "
        "boundaries, missing evidence, case reasons, request identity, and source-file hashes.",
        "", "## Limitations", "",
        *[f"- {limitation}" for limitation in result["limitations"]],
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    arguments = parser.parse_args()
    result = comparison(arguments.manifest, arguments.run_dir)
    print(json.dumps({
        "status": result["status"], "measurementsComplete": result["measurementsComplete"],
        "contributionAcceptance": result["contributionAcceptance"],
        "missingCases": result["missingCases"], "invalidCases": result["invalidCases"],
        "identityMismatches": result["identityMismatches"],
        "report": str(arguments.run_dir / "contribution-comparison.md"),
    }, indent=2))
    raise SystemExit(0 if result["contributionAcceptance"] else 1)


if __name__ == "__main__":
    main()
