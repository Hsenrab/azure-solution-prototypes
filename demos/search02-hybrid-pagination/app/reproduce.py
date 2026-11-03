"""Independent Python Search measurements; one service response per offset."""

import argparse
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
from typing import Any, Literal, NotRequired, TypedDict
from urllib.parse import parse_qs, urlparse

from azure.core.exceptions import AzureError
from azure.identity import AzureCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery

from app.fixture import (
    API, COUNT, expected_ids, fixture_version, load_environment, load_manifest,
    verify_index, verify_prepared_fixture, write_json,
)

Case = Literal["keyword", "vector", "hybrid"]
Phase = Literal["scan", "boundary-probe", "boundary-repeat"]


@dataclass(frozen=True)
class SearchProfile:
    name: str
    sdk_version: str
    api_version: str
    hybrid_search: dict[str, Any]
    sdk_hybrid_search: object | None = None


class QuerySettings(TypedDict, total=False):
    count: bool
    select: list[str]
    top: int
    queryType: str
    searchMode: str
    vectorFilterMode: str
    search: str
    searchFields: list[str]
    vectorQueries: list[dict[str, Any]]
    hybridSearch: dict[str, Any]


class Observation(TypedDict):
    runId: str
    language: str
    case: str
    phase: Phase
    pageNumber: int
    skip: int
    top: int
    advertised: bool
    ids: list[str] | None
    scores: list[float | None] | None
    rowCount: int | None
    reportedCount: int | None
    timestamp: str
    apiVersion: str | None
    method: str | None
    path: str | None
    normalizedRequest: dict[str, Any] | None
    sendCount: int
    statusCode: int | None
    requestId: str | None
    continuation: bool
    incompleteReason: str | None
    error: dict[str, Any] | None


class CaseReport(TypedDict):
    profile: NotRequired[str]
    schemaVersion: int
    runId: str
    language: str
    case: str
    fixture: dict[str, Any]
    index: dict[str, Any]
    environment: dict[str, str]
    client: dict[str, Any]
    query: QuerySettings
    startedAt: str
    finishedAt: str | None
    status: str
    outcome: str
    reasons: list[str]
    observationsFile: str
    summary: dict[str, Any]
    boundaries: list[dict[str, Any]]
    limitations: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalized_request(body: dict[str, Any]) -> dict[str, Any]:
    result = dict(body)
    for key in ("select", "searchFields"):
        if isinstance(result.get(key), str):
            result[key] = result[key].split(",")
    # These are service defaults, not observations of server-internal execution.
    result.setdefault("queryType", "simple")
    result.setdefault("searchMode", "any")
    result.setdefault("vectorFilterMode", "preFilter")
    return result


def query_settings(
    case: Case, manifest: dict[str, Any], profile: SearchProfile | None = None,
) -> QuerySettings:
    settings: QuerySettings = {
        "count": True, "select": ["id"], "top": manifest["pageSize"],
        "queryType": "simple", "searchMode": "any", "vectorFilterMode": "preFilter",
    }
    if case != "vector":
        settings.update(search=manifest["keyword"], searchFields=["content"])
    if case != "keyword":
        settings["vectorQueries"] = [{
            "kind": "vector", "vector": manifest["queryVector"], "fields": "vector",
            "k": manifest["candidateCount"], "exhaustive": True,
        }]
    if profile is not None:
        settings["hybridSearch"] = profile.hybrid_search
    return settings


def measure(
    client: SearchClient, case: Case, manifest: dict[str, Any], run_id: str,
    skip: int, phase: Phase, advertised: bool,
    on_failure: Callable[[Observation], None] | None = None,
    *,
    profile: SearchProfile | None = None,
) -> Observation:
    observation: Observation = {
        "runId": run_id, "language": "python", "case": case, "phase": phase,
        "pageNumber": skip // manifest["pageSize"] + 1, "skip": skip,
        "top": manifest["pageSize"], "advertised": advertised, "ids": None,
        "scores": None, "rowCount": None, "reportedCount": None,
        "timestamp": utc_now(), "apiVersion": None, "method": None, "path": None,
        "normalizedRequest": None, "sendCount": 0, "statusCode": None,
        "requestId": None, "continuation": False, "incompleteReason": None, "error": None,
    }

    def request_hook(pipeline_request: Any) -> None:
        request = pipeline_request.http_request
        url = urlparse(request.url)
        observation["sendCount"] += 1
        observation["apiVersion"] = parse_qs(url.query)["api-version"][0]
        observation["method"] = request.method
        observation["path"] = url.path
        observation["normalizedRequest"] = normalized_request(json.loads(request.body))

    def response_hook(pipeline_response: Any) -> None:
        response = pipeline_response.http_response
        observation["statusCode"] = response.status_code
        observation["requestId"] = response.headers.get("request-id") or response.headers.get("x-ms-request-id")
        if response.status_code == 200:
            body = json.loads(response.text())
            observation["reportedCount"] = body.get("@odata.count")
            observation["continuation"] = bool(
                body.get("@odata.nextLink") or body.get("@search.nextPageParameters")
            )

    options: dict[str, Any] = {
        "include_total_count": True, "select": ["id"], "top": manifest["pageSize"], "skip": skip,
        "raw_request_hook": request_hook, "raw_response_hook": response_hook,
    }
    if case != "vector":
        options.update(
            search_text=manifest["keyword"], query_type="simple",
            search_fields=["content"], search_mode="any",
        )
    if case != "keyword":
        options["vector_queries"] = [VectorizedQuery(
            vector=manifest["queryVector"], fields="vector",
            k_nearest_neighbors=manifest["candidateCount"], exhaustive=True,
        )]
    if profile is not None:
        if profile.sdk_hybrid_search is None:
            raise ValueError("The preview request profile requires its public SDK HybridSearch model.")
        options["hybrid_search"] = profile.sdk_hybrid_search
    try:
        pages = client.search(**options).by_page()
        page = next(pages, None)
        rows = list(page) if page is not None else []
        observation["ids"] = [row["id"] for row in rows]
        observation["scores"] = [row.get("@search.score") for row in rows]
        observation["rowCount"] = len(rows)
        observation["continuation"] = observation["continuation"] or bool(pages.continuation_token)
    except (AzureError, OSError) as error:
        observation["error"] = {"type": type(error).__name__, "message": str(error)}
        if on_failure is not None:
            on_failure(observation)
        raise
    if skip == 0 and phase == "scan":
        observation["advertised"] = observation["reportedCount"] is not None and observation["reportedCount"] > 0
    if len(rows) < manifest["pageSize"] and observation["continuation"]:
        observation["incompleteReason"] = "service-continuation"
    elif observation["sendCount"] != 1:
        observation["incompleteReason"] = "multiple-service-sends"
    elif observation["apiVersion"] != (profile.api_version if profile else API):
        observation["incompleteReason"] = "api-version-mismatch"
    else:
        expected = query_settings(case, manifest, profile)
        actual = dict(observation["normalizedRequest"] or {})
        actual.pop("skip", None)
        if actual != expected:
            observation["incompleteReason"] = "effective-request-mismatch"
    return observation


def summarize(
    observations: list[Observation], case: str, manifest: dict[str, Any],
    index_start: int | None, index_end: int | None,
) -> dict[str, Any]:
    initial = observations[0]["reportedCount"] if observations else None
    candidate_basis = case == "vector" and initial is None
    pages = math.ceil((manifest["candidateCount"] if candidate_basis else (initial or 0)) / manifest["pageSize"])
    primary = [
        page for page in observations
        if page["phase"] == "scan" and page["skip"] < pages * manifest["pageSize"]
        and page["rowCount"] is not None and not page["incompleteReason"] and not page["error"]
    ]
    occurrences = Counter(identifier for page in primary for identifier in (page["ids"] or []))
    empty = [page["pageNumber"] for page in primary if page["rowCount"] == 0]
    populated = [page["pageNumber"] for page in primary if page["rowCount"]]
    counts = sorted({page["reportedCount"] for page in observations if page["reportedCount"] is not None})
    keyword_ids = expected_ids(manifest, "keyword")
    baseline = (
        case == "keyword" and initial == COUNT and pages == 1232
        and len(primary) == pages and len(populated) == pages and not empty
        and set(occurrences) == keyword_ids and all(count == 1 for count in occurrences.values())
        and primary[-1]["rowCount"] == 3
    )
    coverage = len({page["skip"] for page in primary}) / pages if pages else (1.0 if observations else 0.0)
    result = {
        "scanBasis": "vector-k" if candidate_basis else "advertised-count",
        "scanPageCount": pages, "reportedCount": None if candidate_basis else initial,
        "advertisedPages": None if candidate_basis else (pages if initial is not None else None),
        "advertisedPageCoverage": None if candidate_basis else (coverage if initial is not None else None),
        "reportedMinusReachable": None if initial is None or candidate_basis else initial - len(occurrences),
        "scanCoverage": coverage, "observedCounts": counts, "countChanged": len(counts) > 1,
        "totalRows": sum(occurrences.values()), "uniqueReachableIds": len(occurrences),
        "reachableIds": sorted(occurrences),
        "duplicateIds": {key: count for key, count in sorted(occurrences.items()) if count > 1},
        "missingExpectedKeywordIds": sorted(keyword_ids - set(occurrences)) if case == "keyword" else None,
        "populatedPages": len(populated), "emptyPages": len(empty),
        "firstEmptyPage": min(empty) if empty else None,
        "lastPopulatedPage": max(populated) if populated else None,
        "indexCountStart": index_start, "indexCountEnd": index_end,
        "baselineValid": baseline if case == "keyword" else None,
    }
    if fixture_version(manifest) == 2:
        result["vectorMembershipValid"] = (
            set(occurrences) == expected_ids(manifest, "vector")
            and all(count == 1 for count in occurrences.values())
        ) if case == "vector" else None
    return result


def boundary_offsets(summary: dict[str, Any], top: int) -> list[int]:
    if summary["scanPageCount"] == 0:
        return [0]
    pages = {summary["scanPageCount"]}
    if summary["lastPopulatedPage"] is not None:
        pages.update((summary["lastPopulatedPage"], summary["lastPopulatedPage"] + 1))
    if summary["firstEmptyPage"] is not None:
        pages.add(summary["firstEmptyPage"])
    return sorted((page - 1) * top for page in pages)


def boundary_agreement(observations: list[Observation], offsets: list[int]) -> list[dict[str, Any]]:
    result = []
    for offset in offsets:
        indexes = [index for index, page in enumerate(observations) if page["skip"] == offset]
        if len(indexes) != 2:
            result.append({"skip": offset, "observationIndexes": indexes, "complete": False})
            continue
        first, second = (observations[index] for index in indexes)
        counts = (first["reportedCount"], second["reportedCount"])
        result.append({
            "skip": offset, "observationIndexes": indexes, "complete": all(
                page["rowCount"] is not None and not page["error"] and not page["incompleteReason"]
                for page in (first, second)
            ),
            "countAgreement": counts[0] == counts[1] if None not in counts else None,
            "sizeAgreement": (
                first["rowCount"] == second["rowCount"]
                if first["rowCount"] is not None and second["rowCount"] is not None else None
            ),
            "idSetAgreement": (
                set(first["ids"]) == set(second["ids"])
                if first["ids"] is not None and second["ids"] is not None else None
            ),
            "orderAgreement": (
                first["ids"] == second["ids"]
                if first["ids"] is not None and second["ids"] is not None else None
            ),
        })
    return result


def classification(
    summary: dict[str, Any], boundaries: list[dict[str, Any]],
    observations: list[Observation], case: str, manifest: dict[str, Any] | None = None,
) -> tuple[str, str, list[str]]:
    reasons = []
    for page in observations:
        if page["error"]:
            reasons.append("request-failed")
        if page["incompleteReason"]:
            reasons.append(page["incompleteReason"])
    if not observations:
        reasons.append("no-observations")
    if case != "vector" and summary["reportedCount"] is None:
        reasons.append("initial-count-unavailable")
    if summary["countChanged"]:
        reasons.append("count-drift")
    if summary["scanCoverage"] != 1:
        reasons.append("incomplete-scan")
    indexed_count = manifest["recordCount"] if manifest is not None else COUNT
    if summary["indexCountStart"] != indexed_count or summary["indexCountEnd"] != indexed_count:
        reasons.append("index-count-mismatch")
    if manifest is not None and fixture_version(manifest) == 2:
        if not set(summary["reachableIds"]).issubset(expected_ids(manifest)):
            reasons.append("unexpected-corpus-ids")
        if case == "vector" and not summary["vectorMembershipValid"]:
            reasons.append("vector-membership-failed")
    expected_offsets = boundary_offsets(summary, 5)
    if {boundary["skip"] for boundary in boundaries} != set(expected_offsets):
        reasons.append("missing-boundaries")
    if any(
        not boundary.get("complete") or boundary.get("sizeAgreement") is False
        or boundary.get("idSetAgreement") is False or boundary.get("countAgreement") is False
        for boundary in boundaries
    ):
        reasons.append("unstable-or-incomplete-boundary")
    if case == "keyword" and not summary["baselineValid"]:
        reasons.append("keyword-baseline-failed")
    if reasons:
        return "incomplete", "blocked/incomplete", sorted(set(reasons))
    if summary["scanBasis"] == "vector-k":
        return "complete", "not-applicable", ["count-unavailable"]
    if summary["reportedMinusReachable"] > 0 and summary["emptyPages"] > 0:
        return "complete", "reproduced", []
    if summary["reportedMinusReachable"] == 0 and summary["emptyPages"] == 0 and not summary["duplicateIds"]:
        return "complete", "not-reproduced", []
    return "incomplete", "blocked/incomplete", ["inconsistent-reachability-evidence"]


def run(
    case: Case, manifest_path: Path, env_file: Path, run_dir: Path,
    *, profile: SearchProfile | None = None,
) -> int:
    if profile is not None and case != "hybrid":
        raise ValueError("Preview comparison profiles apply only to the hybrid case.")
    manifest, _ = load_manifest(manifest_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    name = profile.name if profile else f"python-{case}"
    api_version = profile.api_version if profile else API
    sdk_version = profile.sdk_version if profile else "12.0.0"
    report_path = run_dir / f"{name}.json"
    observations_path = run_dir / f"{name}.pages.jsonl"
    if report_path.exists() or observations_path.exists() or (run_dir / f"{name}.schema.json").exists():
        raise FileExistsError(f"Existing {name} evidence; use a new run directory.")
    observations: list[Observation] = []
    report: CaseReport = {
        "schemaVersion": 1, "runId": run_dir.name, "language": "python", "case": case,
        "fixture": manifest, "index": {"name": manifest["indexName"], "actualSchemaFile": f"{name}.schema.json"},
        "environment": {}, "client": {
            "packages": {"azure-search-documents": version("azure-search-documents"), "azure-identity": version("azure-identity")},
            "runtime": platform.python_version(), "configuredApi": api_version, "observedApi": [],
        },
        "query": query_settings(case, manifest, profile), "startedAt": utc_now(), "finishedAt": None,
        "status": "incomplete", "outcome": "blocked/incomplete", "reasons": ["unfinished"],
        "observationsFile": observations_path.name,
        "summary": summarize([], case, manifest, None, None), "boundaries": [],
        "limitations": [
            "Independent offset requests are not snapshot isolation; equal index counts do not prove immutability.",
            "Score ties can change order; set/size/count agreement is recorded separately.",
            "No orderBy is sent; documented service ordering is descending search score with unspecified ties.",
            "Synthetic fixed vectors and standalone SDK versions do not establish customer-request parity.",
            "queryType=simple, searchMode=any and vectorFilterMode=preFilter are documented defaults when omitted.",
        ],
    }
    if profile is not None:
        report["profile"] = profile.name
        report["limitations"].append(
            "This comparison changes SDK, service API, and hybrid settings together; it is not an SDK-only test."
        )
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    with observations_path.open("x", encoding="utf-8") as stream:
        if version("azure-search-documents") != sdk_version or version("azure-identity") != "1.25.3":
            report["reasons"] = ["package-version-mismatch"]
            write_json(report_path, report)
            raise ValueError(f"Install the pinned Search {sdk_version} and Identity 1.25.3 requirements before measurements.")
        environment = load_environment(env_file)
        report["environment"] = environment
        write_json(report_path, report)
        if fixture_version(manifest) == 2:
            verify_prepared_fixture(manifest_path, env_file)
        with AzureCliCredential(subscription=environment["AZURE_SUBSCRIPTION_ID"]) as credential:
            with SearchIndexClient(environment["AZURE_SEARCH_ENDPOINT"], credential, api_version=API) as indexes:
                actual = verify_index(indexes, fixture_version(manifest))
                write_json(run_dir / f"{name}.schema.json", actual)
            with SearchClient(
                environment["AZURE_SEARCH_ENDPOINT"], manifest["indexName"], credential, api_version=api_version,
                retry_total=0, retry_connect=0, retry_read=0, retry_status=0,
            ) as client:
                start_count = client.get_document_count()
                report["summary"]["indexCountStart"] = start_count
                write_json(report_path, report)
                if start_count != manifest["recordCount"]:
                    raise ValueError(
                        f"Index has {start_count} records, expected {manifest['recordCount']}; finish preparation first."
                    )

                def persist_failure(page: Observation) -> None:
                    observations.append(page)
                    stream.write(json.dumps(page, allow_nan=False) + "\n")
                    stream.flush()
                    report.update(
                        reasons=["request-failed"], finishedAt=utc_now(),
                        summary=summarize(observations, case, manifest, start_count, None),
                    )
                    write_json(report_path, report)

                def append(skip: int, phase: Phase, advertised: bool) -> Observation:
                    page = measure(
                        client, case, manifest, run_dir.name, skip, phase, advertised, persist_failure,
                        profile=profile,
                    )
                    observations.append(page)
                    stream.write(json.dumps(page, allow_nan=False) + "\n")
                    stream.flush()
                    return page

                first = append(0, "scan", False)
                initial = first["reportedCount"]
                required = math.ceil(
                    (initial if initial is not None else manifest["candidateCount"] if case == "vector" else 0) / 5
                )
                stopped = first["incompleteReason"] is not None or (initial is None and case != "vector")
                if not stopped:
                    for page_number in range(1, required):
                        page = append(page_number * 5, "scan", initial is not None)
                        if page["incompleteReason"]:
                            stopped = True
                            break
                preliminary = summarize(observations, case, manifest, start_count, None)
                offsets = boundary_offsets(preliminary, 5)
                if not stopped:
                    for offset in offsets:
                        if not any(page["skip"] == offset for page in observations):
                            page = append(offset, "boundary-probe", initial is not None and offset < required * 5)
                            if page["incompleteReason"]:
                                stopped = True
                                break
                        page = append(offset, "boundary-repeat", initial is not None and offset < required * 5)
                        if page["incompleteReason"]:
                            stopped = True
                            break
                end_count = client.get_document_count()
        summary = summarize(observations, case, manifest, start_count, end_count)
        boundaries = boundary_agreement(observations, offsets)
        status, outcome, reasons = classification(summary, boundaries, observations, case, manifest)
        report.update(
            summary=summary, boundaries=boundaries, status=status, outcome=outcome,
            reasons=reasons, finishedAt=utc_now(),
        )
        report["client"]["observedApi"] = sorted({page["apiVersion"] for page in observations if page["apiVersion"]})
        write_json(report_path, report)
    print(json.dumps({"report": str(report_path), "status": status, "outcome": outcome, "summary": {
        key: summary[key] for key in ("reportedCount", "uniqueReachableIds", "populatedPages", "emptyPages", "scanBasis")
    }, "reasons": reasons}, indent=2))
    return 0 if status == "complete" else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("keyword", "vector", "hybrid"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.case, arguments.manifest, arguments.env_file, arguments.run_dir))


if __name__ == "__main__":
    main()
