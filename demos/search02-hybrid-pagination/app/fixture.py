"""Deterministic synthetic fixture and Search data-plane preparation."""

import argparse
from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

from azure.identity import AzureCliCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    SearchField,
    SearchIndex,
    VectorSearch,
    VectorSearchProfile,
)
from dotenv import dotenv_values

from app.notebook_helpers import resolve_az_cli, validate_environment

COUNT = 6158
INDEX = "hybrid-pagination-debug"
MIXED_COUNT = 6183
MIXED_INDEX = "hybrid-pagination-mixed-v2"
API = "2025-09-01"
RULES = (
    "SHA256(UTF8(id)); vector=float(byte[0:16]-128); "
    "content=topic(byte[18]%4), id, maths*(1+byte[16]%7), lesson*(1+byte[17]%23); "
    "ascending IDs; UTF8 compact JSON separators comma/colon; key order id/content/vector; LF"
)
MIXED_RULES = (
    RULES + "; v2: keywordOnly=1..6133; shared=6134..6158 vector=[100,ordinal-6108,0*14]; "
    "vectorOnly=6159..6183 vector=[100,ordinal-6158,0*14]; "
    "nonkeyword topic=(ordinal-6159)%4, id, lesson*(1+byte[17]%23)"
)


def fixture_version(manifest: dict[str, Any]) -> int:
    value = manifest["fixtureVersion"]
    if type(value) is not int or value not in (1, 2):
        raise ValueError(f"Unsupported fixture version: {value!r}")
    return value


def membership() -> dict[str, list[str]]:
    return {
        group: [f"doc-{number:06d}" for number in range(start, end + 1)]
        for group, start, end in (
            ("keywordOnly", 1, 6133), ("shared", 6134, 6158), ("vectorOnly", 6159, MIXED_COUNT),
        )
    }


def expected_ids(manifest: dict[str, Any], case: str = "index") -> set[str]:
    mixed = fixture_version(manifest) == 2
    if case == "vector":
        if not mixed:
            raise ValueError("Version 1 has no declared vector membership.")
        return set(membership()["shared"] + membership()["vectorOnly"])
    count = COUNT if case == "keyword" or not mixed else MIXED_COUNT
    return {f"doc-{number:06d}" for number in range(1, count + 1)}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def declared_index(version: int = 1) -> SearchIndex:
    fixture_version({"fixtureVersion": version})
    return SearchIndex(
        name=MIXED_INDEX if version == 2 else INDEX,
        fields=[
            SearchField(name="id", type="Edm.String", key=True, searchable=False, hidden=False),
            SearchField(
                name="content", type="Edm.String", searchable=True,
                hidden=False, analyzer_name="standard.lucene",
            ),
            SearchField(
                name="vector", type="Collection(Edm.Single)", searchable=True,
                vector_search_dimensions=16, vector_search_profile_name="exact-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[ExhaustiveKnnAlgorithmConfiguration(
                name="exact", parameters=ExhaustiveKnnParameters(metric="cosine"),
            )],
            profiles=[VectorSearchProfile(name="exact-profile", algorithm_configuration_name="exact")],
        ),
    )


def records(version: int = 1) -> list[dict[str, Any]]:
    fixture_version({"fixtureVersion": version})
    result = []
    topics = ("algebra", "geometry", "fractions", "statistics")
    nonkeyword_topics = (
        "arithmetic exercises and number practice", "number patterns and calculation practice",
        "fractions exercises and quantity practice", "geometry exercises and shape practice",
    )
    for number in range(1, (MIXED_COUNT if version == 2 else COUNT) + 1):
        identifier = f"doc-{number:06d}"
        digest = hashlib.sha256(identifier.encode("utf-8")).digest()
        vector = [float(component - 128) for component in digest[:16]]
        content = " ".join([
            topics[digest[18] % 4], identifier,
            *(["maths"] * (1 + digest[16] % 7)),
            *(["lesson"] * (1 + digest[17] % 23)),
        ])
        if version == 2 and number > 6133:
            rank = number - (6108 if number <= COUNT else COUNT)
            vector = [100.0, float(rank)] + [0.0] * 14
        if version == 2 and number > COUNT:
            content = " ".join([
                nonkeyword_topics[(number - 6159) % 4], identifier,
                *(["lesson"] * (1 + digest[17] % 23)),
            ])
        result.append({"id": identifier, "content": content, "vector": vector})
    return result


def corpus_bytes(documents: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(document, separators=(",", ":"), allow_nan=False) + "\n"
        for document in documents
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def manifest_definition(version: int = 1) -> dict[str, Any]:
    corpus = corpus_bytes(records(version))
    schema = declared_index(version).as_dict()
    manifest = {
        "fixtureVersion": version, "generatorRules": MIXED_RULES if version == 2 else RULES,
        "corpusSha256": sha256(corpus), "recordCount": MIXED_COUNT if version == 2 else COUNT,
        "corpusPath": "corpus.jsonl", "indexName": schema["name"],
        "declaredSchemaSha256": sha256(canonical(schema)),
        "keyword": "maths", "queryVector": [1.0] + [0.0] * 15,
        "vectorDimensions": 16, "similarityMetric": "cosine",
        "candidateCount": 50, "serviceApi": API, "pageSize": 5,
    }
    if version == 2:
        manifest.update(keywordMatchCount=COUNT, membership=membership())
    return manifest


def validate_manifest_identity(manifest: dict[str, Any]) -> None:
    expected = manifest_definition(fixture_version(manifest))
    if manifest != expected:
        raise ValueError("Manifest differs from the deterministic fixture definition.")


def generate(directory: Path, version: int = 1) -> Path:
    manifest = manifest_definition(version)
    if version == 2 and directory.resolve() == (
        Path(__file__).resolve().parents[1] / "outputs" / "generated" / "reproduction" / "fixture"
    ).resolve():
        raise ValueError("The original fixture destination is protected.")
    corpus = corpus_bytes(records(version))
    schema = declared_index(version).as_dict()
    files = (
        ("corpus.jsonl", corpus),
        ("declared-schema.json", json.dumps(schema, indent=2).encode("utf-8") + b"\n"),
        ("manifest.json", json.dumps(manifest, indent=2).encode("utf-8") + b"\n"),
    )
    for name, data in files:
        path = directory / name
        if path.exists() and path.read_bytes() != data:
            raise FileExistsError(f"Different fixture already exists: {path}. Use a new fixture directory.")
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in files:
        path = directory / name
        path.write_bytes(data)
    load_manifest(directory / "manifest.json")
    return directory / "manifest.json"


def load_manifest(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest_identity(manifest)
    version = fixture_version(manifest)
    raw = (path.parent / manifest["corpusPath"]).read_bytes()
    if sha256(raw) != manifest["corpusSha256"] or raw != corpus_bytes(records(version)):
        raise ValueError("Corpus hash or deterministic generation does not match.")
    schema = json.loads((path.parent / "declared-schema.json").read_text(encoding="utf-8"))
    if sha256(canonical(schema)) != manifest["declaredSchemaSha256"] or schema != declared_index(version).as_dict():
        raise ValueError("Declared schema hash or definition does not match.")
    documents = [json.loads(line) for line in raw.splitlines()]
    for document in documents:
        vector = document["vector"]
        if len(vector) != 16 or not all(math.isfinite(x) and x == int(x) for x in vector) or not any(vector):
            raise ValueError(f"Invalid vector: {document['id']}")
    return manifest, documents


def load_environment(path: Path) -> dict[str, str]:
    values = dotenv_values(path)
    az = resolve_az_cli()
    if az is None:
        raise RuntimeError("Azure CLI not found. Complete setup first.")
    result = subprocess.run([az, "account", "show", "--output", "json"], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"az account show failed ({result.returncode})\n{result.stderr}\n{result.stdout}")
    account = json.loads(result.stdout)
    if account["id"].casefold() != str(values["AZURE_SUBSCRIPTION_ID"]).casefold():
        result = subprocess.run(
            [az, "account", "set", "--subscription", str(values["AZURE_SUBSCRIPTION_ID"])],
            capture_output=True, text=True,
        )
        if result.returncode:
            raise RuntimeError(f"az account set failed ({result.returncode})\n{result.stderr}\n{result.stdout}")
        result = subprocess.run([az, "account", "show", "--output", "json"], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"az account show failed ({result.returncode})\n{result.stderr}\n{result.stdout}")
        account = json.loads(result.stdout)
    if account["user"]["type"].casefold() != "user":
        raise ValueError("Sign in as the setup user.")
    result = subprocess.run(
        [az, "ad", "signed-in-user", "show", "--query", "id", "--output", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError(f"az ad signed-in-user show failed ({result.returncode})\n{result.stderr}\n{result.stdout}")
    group = values["AZURE_RESOURCE_GROUP"]
    if not isinstance(group, str):
        raise ValueError("Missing AZURE_RESOURCE_GROUP")
    return validate_environment(
        values, subscription_id=account["id"], tenant_id=account["tenantId"],
        resource_group=group, operator_object_id=result.stdout.strip(),
    )


def require_declared(actual: Any, declared: Any, path: str = "index") -> None:
    """Compare declared properties without treating service-added defaults as inputs."""
    if isinstance(declared, Mapping):
        if not isinstance(actual, Mapping):
            raise ValueError(f"Schema mismatch at {path}")
        for key, value in declared.items():
            require_declared(actual.get(key), value, f"{path}.{key}")
    elif isinstance(declared, list):
        if not isinstance(actual, list) or len(actual) != len(declared):
            raise ValueError(f"Schema mismatch at {path}")
        if declared and isinstance(declared[0], Mapping) and "name" in declared[0]:
            actual = sorted(actual, key=lambda item: item["name"])
            declared = sorted(declared, key=lambda item: item["name"])
        for index, value in enumerate(declared):
            require_declared(actual[index], value, f"{path}[{index}]")
    elif actual != declared:
        raise ValueError(f"Schema mismatch at {path}: {actual!r} != {declared!r}")


def verify_index(client: SearchIndexClient, version: int = 1) -> dict[str, Any]:
    actual: dict[str, Any] = {}

    def capture(response: Any) -> None:
        if response.http_response.status_code == 200:
            actual.update(json.loads(response.http_response.text()))

    client.get_index(declared_index(version).name, raw_response_hook=capture)
    if not actual:
        raise RuntimeError("Index response was not captured.")
    require_declared(actual, declared_index(version).as_dict())
    for key in ("semantic", "scoringProfiles", "suggesters"):
        if actual.get(key):
            raise ValueError(f"Unexpected index setting: {key}")
    if actual.get("vectorSearch", {}).get("vectorizers"):
        raise ValueError("Unexpected vectorizer.")
    return actual


def prepare(manifest_path: Path, env_file: Path) -> dict[str, Any]:
    manifest, documents = load_manifest(manifest_path)
    environment = load_environment(env_file)
    if fixture_version(manifest) == 2:
        return prepare_mixed(manifest_path, manifest, documents, environment, env_file)
    with AzureCliCredential(subscription=environment["AZURE_SUBSCRIPTION_ID"]) as credential:
        with SearchIndexClient(environment["AZURE_SEARCH_ENDPOINT"], credential, api_version=API) as indexes:
            indexes.create_or_update_index(declared_index())
            actual = verify_index(indexes)
            write_json(manifest_path.parent / "actual-schema.json", actual)
        with SearchClient(environment["AZURE_SEARCH_ENDPOINT"], INDEX, credential, api_version=API) as client:
            for start in range(0, COUNT, 500):
                batch = documents[start:start + 500]
                results = client.upload_documents(batch)
                if len(results) != len(batch):
                    raise RuntimeError(f"Incomplete indexing response at batch {start}")
                for document, result in zip(batch, results):
                    if not result.succeeded or result.key != document["id"]:
                        raise RuntimeError(f"Indexing failed: {result.key}: {result.error_message}")
            count = client.get_document_count()
            if count != manifest["recordCount"]:
                raise RuntimeError(
                    f"Indexed count is {count}, expected {COUNT}. Wait for indexing then run the indexed-count cell; "
                    "do not measure until it is exact."
                )
    return {"index": INDEX, "indexedCount": count, "corpusSha256": manifest["corpusSha256"]}


def preparation_identity(manifest: dict[str, Any], environment: dict[str, str]) -> dict[str, Any]:
    return {
        "fixtureVersion": fixture_version(manifest), "corpusSha256": manifest["corpusSha256"],
        "declaredSchemaSha256": manifest["declaredSchemaSha256"], "indexName": manifest["indexName"],
        "serviceResourceId": environment["AZURE_SEARCH_RESOURCE_ID"],
        "endpoint": environment["AZURE_SEARCH_ENDPOINT"],
    }


def load_preparation_receipt(
    manifest_path: Path, manifest: dict[str, Any], environment: dict[str, str],
) -> dict[str, Any]:
    receipt = json.loads((manifest_path.parent / "preparation.json").read_text(encoding="utf-8"))
    if (
        receipt["identity"] != preparation_identity(manifest, environment)
        or receipt["status"] not in ("uploaded", "ready")
        or receipt["uploadedRecordCount"] != MIXED_COUNT
        or receipt["checkedSuccessCount"] != MIXED_COUNT
        or receipt["schemaEvidenceFile"] != "actual-schema.json"
    ):
        raise ValueError("Mixed preparation receipt is incomplete or belongs to another fixture/service.")
    results = receipt["uploadResults"]
    if (
        len(results) != MIXED_COUNT or [row["key"] for row in results] != sorted(expected_ids(manifest))
        or not all(row["succeeded"] is True for row in results)
    ):
        raise ValueError("Preparation requires all 6,183 successful individual upload results.")
    raw_schema = (manifest_path.parent / receipt["schemaEvidenceFile"]).read_bytes()
    if sha256(raw_schema) != receipt["schemaEvidenceSha256"]:
        raise ValueError("Preparation schema evidence hash differs.")
    require_declared(json.loads(raw_schema), declared_index(2).as_dict())
    return receipt


def verify_prepared_fixture(manifest_path: Path, env_file: Path) -> dict[str, Any]:
    manifest, documents = load_manifest(manifest_path)
    if fixture_version(manifest) != 2:
        raise ValueError("Mixed readiness requires the version-2 fixture.")
    environment = load_environment(env_file)
    receipt = load_preparation_receipt(manifest_path, manifest, environment)
    with AzureCliCredential(subscription=environment["AZURE_SUBSCRIPTION_ID"]) as credential:
        with SearchIndexClient(environment["AZURE_SEARCH_ENDPOINT"], credential, api_version=API) as indexes:
            verify_index(indexes, 2)
        with SearchClient(
            environment["AZURE_SEARCH_ENDPOINT"], MIXED_INDEX, credential, api_version=API,
        ) as client:
            count = client.get_document_count()
            if count != MIXED_COUNT:
                raise ValueError(f"Mixed indexed count is {count}, expected {MIXED_COUNT}; readiness is pending.")
            actual = [
                {"id": row["id"], "content": row["content"]}
                for row in client.search(search_text="*", select=["id", "content"], order_by=["id asc"])
            ]
    expected = [{"id": row["id"], "content": row["content"]} for row in documents]
    if actual != expected:
        raise ValueError("Mixed ID/content inventory differs from the verified fixture.")
    if receipt["status"] == "uploaded":
        receipt.update(status="ready", indexedCount=count, readyAt=datetime.now(timezone.utc).isoformat())
        write_json(manifest_path.parent / "preparation.json", receipt)
    return {
        "index": MIXED_INDEX, "indexedCount": count, "corpusSha256": manifest["corpusSha256"],
        "status": "ready", "inventoryVerified": True, "hiddenVectorsVerified": False,
    }


def prepare_mixed(
    manifest_path: Path, manifest: dict[str, Any], documents: list[dict[str, Any]],
    environment: dict[str, str], env_file: Path,
) -> dict[str, Any]:
    if manifest["indexName"] != MIXED_INDEX or fixture_version(manifest) != 2:
        raise ValueError("Only the approved mixed target may be prepared here.")
    with AzureCliCredential(subscription=environment["AZURE_SUBSCRIPTION_ID"]) as credential:
        with SearchIndexClient(environment["AZURE_SEARCH_ENDPOINT"], credential, api_version=API) as indexes:
            try:
                actual_schema = verify_index(indexes, 2)
            except ResourceNotFoundError:
                indexes.create_index(declared_index(2))
                actual_schema = verify_index(indexes, 2)
        with SearchClient(
            environment["AZURE_SEARCH_ENDPOINT"], MIXED_INDEX, credential, api_version=API,
        ) as client:
            if client.get_document_count() != 0:
                raise ValueError("Mixed target is populated. Skip preparation and use read-only readiness.")
            receipt_path = manifest_path.parent / "preparation.json"
            schema_path = manifest_path.parent / "actual-schema.json"
            write_json(schema_path, actual_schema)
            receipt: dict[str, Any] = {
                "identity": preparation_identity(manifest, environment),
                "startedAt": datetime.now(timezone.utc).isoformat(), "finishedAt": None,
                "status": "uploading", "uploadedRecordCount": 0, "checkedSuccessCount": 0,
                "uploadResults": [], "indexedCount": None, "schemaEvidenceFile": schema_path.name,
                "schemaEvidenceSha256": sha256(schema_path.read_bytes()),
            }
            write_json(receipt_path, receipt)
            try:
                for start in range(0, MIXED_COUNT, 500):
                    batch = documents[start:start + 500]
                    results = client.upload_documents(batch)
                    receipt["uploadResults"].extend({
                        "key": result.key, "succeeded": result.succeeded,
                        "statusCode": result.status_code, "errorMessage": result.error_message,
                    } for result in results)
                    receipt["checkedSuccessCount"] = sum(row["succeeded"] is True for row in receipt["uploadResults"])
                    receipt["uploadedRecordCount"] = receipt["checkedSuccessCount"]
                    write_json(receipt_path, receipt)
                    if len(results) != len(batch):
                        raise RuntimeError(f"Incomplete mixed upload response at batch {start}.")
                    for document, result in zip(batch, results):
                        if not result.succeeded or result.key != document["id"]:
                            raise RuntimeError(f"Mixed indexing failed: {result.key}: {result.error_message}")
                receipt["status"] = "uploaded"
            finally:
                if receipt["status"] == "uploading":
                    receipt["status"] = "incomplete"
                receipt["finishedAt"] = datetime.now(timezone.utc).isoformat()
                write_json(receipt_path, receipt)
    return verify_prepared_fixture(manifest_path, env_file)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--fixture-version", type=int, choices=(1, 2), default=1)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--env-file", type=Path)
    arguments = parser.parse_args()
    manifest = generate(arguments.directory, arguments.fixture_version)
    if arguments.prepare:
        if arguments.env_file is None:
            parser.error("--env-file is required with --prepare")
        print(json.dumps(prepare(manifest, arguments.env_file), indent=2))
    else:
        print(manifest)


if __name__ == "__main__":
    main()
