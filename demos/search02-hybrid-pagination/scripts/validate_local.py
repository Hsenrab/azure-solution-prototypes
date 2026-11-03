"""Validate Feature 1 locally with compiled Bicep and synthetic SDK responses."""

import ast
from collections.abc import Iterator
import copy
import json
import math
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from types import SimpleNamespace, TracebackType
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from azure.core.credentials import AccessToken
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError, ServiceRequestError
from azure.core.pipeline.transport import HttpRequest, HttpResponse, HttpTransport
from azure.mgmt.resource.deployments import DeploymentsMgmtClient
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.identity import AzureCliCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from dotenv import dotenv_values

DEMO = Path(__file__).resolve().parents[1]
REPOSITORY = DEMO.parents[1]
GENERATED = DEMO / "outputs" / "generated"
sys.path.insert(0, str(DEMO))

from app.notebook_helpers import ENV_OUTPUTS, environment_from_outputs, validate_environment
from app import fixture
from app.reproduce import (
    Case, Observation, SearchProfile, boundary_agreement, boundary_offsets, classification,
    query_settings, summarize,
)
from app.reproduce import measure

CONTEXT = {
    "subscription_id": "11111111-1111-1111-1111-111111111111",
    "tenant_id": "22222222-2222-2222-2222-222222222222",
    "resource_group": "rg-search02-hybrid-pagination-ne",
    "operator_object_id": "33333333-3333-3333-3333-333333333333",
}
GROUP_ID = f"/subscriptions/{CONTEXT['subscription_id']}/resourceGroups/{CONTEXT['resource_group']}"
VALUES = {
    "AZURE_SUBSCRIPTION_ID": CONTEXT["subscription_id"],
    "AZURE_TENANT_ID": CONTEXT["tenant_id"],
    "AZURE_RESOURCE_GROUP": CONTEXT["resource_group"],
    "AZURE_RESOURCE_GROUP_ID": GROUP_ID,
    "AZURE_LOCATION": "northeurope",
    "AZURE_SEARCH_SERVICE_NAME": "srch-hybrid-local",
    "AZURE_SEARCH_RESOURCE_ID": f"{GROUP_ID}/providers/Microsoft.Search/searchServices/srch-hybrid-local",
    "AZURE_SEARCH_ENDPOINT": "https://srch-hybrid-local.search.windows.net",
    "AZURE_OPERATOR_OBJECT_ID": CONTEXT["operator_object_id"],
}
OUTPUTS = {name: {"type": "String", "value": VALUES[key]} for key, name in ENV_OUTPUTS.items()}


def notebook(name: str) -> dict[str, Any]:
    return json.loads((DEMO / "notebooks" / name).read_text(encoding="utf-8"))


def source(name: str, heading: str) -> str:
    current_heading = ""
    for cell in notebook(name)["cells"]:
        if cell["cell_type"] == "markdown":
            current_heading = cell["source"][0].strip()
        elif current_heading == heading:
            return "".join(cell["source"])
    raise ValueError(f"No executable step for heading {heading} in {name}")


class SyntheticCredential:
    def __init__(self) -> None:
        self.scopes: tuple[str, ...] = ()

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        self.scopes = scopes
        return AccessToken("synthetic-local-test-only", int(time.time()) + 3600)


class SyntheticResponse(HttpResponse):
    def __init__(self, request: HttpRequest, payload: dict[str, Any], status: int) -> None:
        super().__init__(request, None)
        self.status_code = status
        self.headers = {"content-type": "application/json"}
        self.reason = "Synthetic local response"
        self._body = json.dumps(payload).encode()

    def body(self) -> bytes:
        return self._body

    def text(self, encoding: str | None = None) -> str:
        return self._body.decode(encoding or "utf-8")

    def json(self) -> dict[str, Any]:
        return json.loads(self._body)

    def iter_bytes(self, **kwargs: Any) -> Iterator[bytes]:
        yield self._body

    def iter_raw(self, **kwargs: Any) -> Iterator[bytes]:
        yield self._body

    def read(self) -> bytes:
        return self._body


class SyntheticTransport(HttpTransport):
    def __init__(self, payload: dict[str, Any] | Callable[[HttpRequest], dict[str, Any]], status: int = 200) -> None:
        self.payload = payload
        self.status = status
        self.requests: list[tuple[str, str]] = []

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def __enter__(self) -> "SyntheticTransport":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def send(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        self.requests.append((request.method, request.url))
        payload = self.payload(request) if callable(self.payload) else self.payload
        return SyntheticResponse(request, payload, self.status)


class InfrastructureChecks(unittest.TestCase):
    def test_compiled_resource_properties_and_outputs(self) -> None:
        template = json.loads((GENERATED / "main.json").read_text(encoding="utf-8"))
        self.assertEqual(set(template["outputs"]), set(ENV_OUTPUTS.values()))
        resources = template["resources"]
        self.assertEqual(len(resources), 2)
        group = next(item for item in resources if item["type"] == "Microsoft.Resources/resourceGroups")
        self.assertEqual(group["tags"]["demo"], "[parameters('demoId')]")
        module = next(item for item in resources if item["type"] == "Microsoft.Resources/deployments")
        nested = module["properties"]["template"]
        self.assertEqual(len(nested["resources"]), 3)
        search = next(item for item in nested["resources"] if item["type"] == "Microsoft.Search/searchServices")
        self.assertEqual(search["apiVersion"], "2025-05-01")
        self.assertEqual(search["sku"]["name"], "basic")
        self.assertNotIn("identity", search)
        properties = search["properties"]
        self.assertEqual(properties["replicaCount"], 1)
        self.assertEqual(properties["partitionCount"], 1)
        self.assertIs(properties["disableLocalAuth"], True)
        self.assertEqual(properties["publicNetworkAccess"], "enabled")
        self.assertEqual(properties["networkRuleSet"]["ipRules"], [])
        self.assertNotIn("authOptions", properties)
        roles = [item for item in nested["resources"] if item["type"] == "Microsoft.Authorization/roleAssignments"]
        self.assertEqual(len(roles), 2)
        self.assertEqual(len({item["name"] for item in roles}), 2)
        for role in roles:
            self.assertEqual(role["apiVersion"], "2022-04-01")
            self.assertEqual(role["properties"]["principalType"], "User")
            self.assertEqual(role["properties"]["principalId"], "[parameters('operatorObjectId')]")
            self.assertIn("Microsoft.Search/searchServices", role["scope"])
            self.assertIn("guid(", role["name"])
        self.assertIn("7ca78c08-252a-4471-8644-bb5ff32d4ba0", nested["variables"]["serviceContributorRoleId"])
        self.assertIn("8ebe5a00-799e-43f5-93ac-243d3dce84a7", nested["variables"]["dataContributorRoleId"])
        self.assertIn("uniqueString(", nested["variables"]["serviceName"])
        self.assertEqual(template["parameters"]["location"]["allowedValues"], ["northeurope"])

    def test_notebook_syntax_and_no_reproduction_operations(self) -> None:
        for path in (DEMO / "notebooks").glob("*.ipynb"):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["nbformat"], 4)
            self.assertNotIn("display_name", data["metadata"]["kernelspec"])
            for cell in data["cells"]:
                if cell["cell_type"] != "code":
                    continue
                self.assertIsNone(cell["execution_count"])
                self.assertEqual(cell["outputs"], [])
                tree = ast.parse("".join(cell["source"]))
                if path.name not in ("01_deploy_infra.ipynb", "03_test.ipynb"):
                    continue
                self.assertFalse(any(isinstance(node, ast.Try) for node in ast.walk(tree)))
                forbidden = {"create_index", "create_or_update_index", "upload_documents", "search", "list_keys"}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                        self.assertNotIn(node.func.attr, forbidden)

    def test_metadata_schema(self) -> None:
        template = json.loads((REPOSITORY / "demo-template" / "metadata.json").read_text())
        actual = json.loads((DEMO / "metadata.json").read_text())
        self.assertEqual(set(template), set(actual))
        self.assertIsInstance(actual["status"], str)
        self.assertTrue(actual["status"].strip())


class HandoffChecks(unittest.TestCase):
    def test_readiness_region_names_and_wrong_settings(self) -> None:
        tree = ast.parse(source("03_test.ipynb", "## Step 2 - Match the actual successful deployment and owned resources"))
        guard = next(node for node in tree.body if isinstance(node, ast.If) and "service.location" in ast.unparse(node.test))
        code = compile(ast.Module(body=[guard], type_ignores=[]), "live-region-check", "exec")
        for location, sku, accepted in (
            ("northeurope", "basic", True),
            ("North Europe", "basic", True),
            ("westeurope", "basic", False),
            ("West Europe", "basic", False),
            ("northeurope", "standard", False),
        ):
            with self.subTest(location=location, sku=sku):
                state = {"service": SimpleNamespace(location=location, sku=SimpleNamespace(name=sku))}
                if accepted:
                    exec(code, state)
                else:
                    with self.assertRaisesRegex(ValueError, "Live tier/location"):
                        exec(code, state)

    def test_cli_token_request_does_not_combine_tenant_and_subscription(self) -> None:
        for name, heading in (
            ("01_deploy_infra.ipynb", "## Step 1 - Resolve the selected subscription and setup user"),
            ("03_test.ipynb", "## Step 1 - Validate the handoff against the current CLI user"),
        ):
            tree = ast.parse(source(name, heading))
            call = next(node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "AzureCliCredential")
            credential = eval(compile(ast.Expression(call), name, "eval"), {"AzureCliCredential": AzureCliCredential, "subscription_id": CONTEXT["subscription_id"]})
            response = json.dumps({"accessToken": "synthetic-local-test-only", "expires_on": int(time.time()) + 3600})
            with patch("subprocess.check_output", return_value=response) as cli:
                credential.get_token("https://management.azure.com/.default")
            arguments = cli.call_args.args[0]
            self.assertIn("--subscription", arguments)
            self.assertIn(CONTEXT["subscription_id"], arguments)
            self.assertNotIn("--tenant", arguments)

    def test_control_plane_sdk_preview_deployment_and_readiness(self) -> None:
        role_ids = ("7ca78c08-252a-4471-8644-bb5ff32d4ba0", "8ebe5a00-799e-43f5-93ac-243d3dce84a7")
        service_id = VALUES["AZURE_SEARCH_RESOURCE_ID"]
        assignment_ids = [f"{service_id}/providers/Microsoft.Authorization/roleAssignments/local-{index}" for index in range(2)]

        def payload(request: HttpRequest) -> dict[str, Any]:
            path = urlparse(request.url).path
            if path.endswith("/validate"):
                return {"properties": {"provisioningState": "Succeeded"}}
            if path.endswith("/whatIf"):
                return {"status": "Succeeded", "properties": {"changes": []}}
            if path.endswith("/deployments/search02-hybrid-pagination-search"):
                return {"name": "search02-hybrid-pagination-search", "properties": {"provisioningState": "Succeeded", "outputResources": [{"id": value} for value in [service_id, *assignment_ids]]}}
            if path.endswith("/deployments/search02-hybrid-pagination"):
                return {"name": "search02-hybrid-pagination", "properties": {"provisioningState": "Succeeded", "outputs": OUTPUTS}}
            if path.casefold() == GROUP_ID.casefold():
                return {"id": GROUP_ID, "name": CONTEXT["resource_group"], "location": "northeurope", "tags": {"demo": "search02-hybrid-pagination"}}
            if path.casefold() == service_id.casefold():
                return {"id": service_id, "name": VALUES["AZURE_SEARCH_SERVICE_NAME"], "location": "North Europe", "sku": {"name": "basic"}, "properties": {"replicaCount": 1, "partitionCount": 1, "disableLocalAuth": True, "publicNetworkAccess": "enabled", "networkRuleSet": {"ipRules": []}}}
            for index, assignment_id in enumerate(assignment_ids):
                if path.casefold() == assignment_id.casefold():
                    return {"id": assignment_id, "properties": {"principalId": CONTEXT["operator_object_id"], "principalType": "User", "roleDefinitionId": f"/subscriptions/{CONTEXT['subscription_id']}/providers/Microsoft.Authorization/roleDefinitions/{role_ids[index]}"}}
            raise AssertionError(f"Unexpected local management request: {request.method} {path}")

        transport = SyntheticTransport(payload)
        credential = SyntheticCredential()
        with tempfile.TemporaryDirectory() as directory:
            state = {
                **CONTEXT,
                "RESOURCE_GROUP": CONTEXT["resource_group"],
                "DEMO_ID": "search02-hybrid-pagination",
                "DEPLOYMENT_NAME": "search02-hybrid-pagination",
                "environment": VALUES,
                "environment_from_outputs": environment_from_outputs,
                "generated": Path(directory),
                "json": json,
                "deployments_client": DeploymentsMgmtClient(credential, CONTEXT["subscription_id"], transport=transport),
                "resource_client": ResourceManagementClient(credential, CONTEXT["subscription_id"], transport=transport),
                "deployment_parameters": {"location": "northeurope", "properties": {"mode": "Incremental", "template": json.loads((GENERATED / "main.json").read_text(encoding="utf-8")), "parameters": {"operatorObjectId": {"value": CONTEXT["operator_object_id"]}}}},
            }
            exec(source("01_deploy_infra.ipynb", "## Step 4 - Validate and review what-if"), state)
            exec(source("01_deploy_infra.ipynb", "## Step 5 - Explicitly deploy the paid environment"), state)
            exec(source("03_test.ipynb", "## Step 2 - Match the actual successful deployment and owned resources"), state)
            exec(source("03_test.ipynb", "## Step 3 - Inspect the two Bicep-owned role assignments"), state)
            self.assertEqual(len(state["role_evidence"]), 2)
            self.assertEqual(state["current_environment"], VALUES)
            self.assertTrue(any(method == "PUT" for method, _ in transport.requests))
            state["environment"] = {
                **VALUES,
                "AZURE_SEARCH_SERVICE_NAME": "srch-stale-local",
                "AZURE_SEARCH_RESOURCE_ID": f"{GROUP_ID}/providers/Microsoft.Search/searchServices/srch-stale-local",
                "AZURE_SEARCH_ENDPOINT": "https://srch-stale-local.search.windows.net",
            }
            with self.assertRaisesRegex(ValueError, "Export is stale"):
                exec(source("03_test.ipynb", "## Step 2 - Match the actual successful deployment and owned resources"), state)

    def test_exact_nine_non_secret_outputs(self) -> None:
        self.assertEqual(environment_from_outputs(OUTPUTS, **CONTEXT), VALUES)
        self.assertEqual(len(VALUES), 9)
        self.assertEqual(set(dotenv_values(DEMO / "env" / ".env.example")), set(ENV_OUTPUTS))

    def test_each_required_output_is_mandatory(self) -> None:
        for name in ENV_OUTPUTS.values():
            with self.subTest(name=name):
                missing = copy.deepcopy(OUTPUTS)
                del missing[name]
                with self.assertRaises(KeyError):
                    environment_from_outputs(missing, **CONTEXT)

    def test_empty_and_non_string_values_fail(self) -> None:
        for key in ENV_OUTPUTS:
            for invalid in ("", " ", None, 0, "injected\nSECRET=value"):
                with self.subTest(key=key, invalid=invalid):
                    values = dict(VALUES, **{key: invalid})
                    with self.assertRaises(ValueError):
                        validate_environment(values, **CONTEXT)

    def test_wrong_identity_and_scope_fail(self) -> None:
        for key in ("AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "AZURE_OPERATOR_OBJECT_ID"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    validate_environment(dict(VALUES, **{key: "44444444-4444-4444-4444-444444444444"}), **CONTEXT)
        for key in ("AZURE_RESOURCE_GROUP", "AZURE_RESOURCE_GROUP_ID", "AZURE_SEARCH_RESOURCE_ID", "AZURE_LOCATION", "AZURE_SEARCH_ENDPOINT"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    validate_environment(dict(VALUES, **{key: "wrong-scope"}), **CONTEXT)

    def test_export_replaces_stale_file_with_complete_utf8_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            (root / "env").mkdir()
            (root / "outputs").mkdir()
            env_path = root / "env" / ".env"
            env_path.write_text("STALE=old-run\n", encoding="utf-8")
            state = {
                **CONTEXT,
                "RESOURCE_GROUP": CONTEXT["resource_group"],
                "DEPLOYMENT_NAME": "local-synthetic",
                "demo_root": root,
                "generated": root / "outputs",
                "deployment": SimpleNamespace(properties=SimpleNamespace(provisioning_state="Succeeded", outputs=OUTPUTS)),
                "environment_from_outputs": environment_from_outputs,
                "json": json, "os": os, "datetime": datetime, "timezone": timezone,
            }
            exec(source("01_deploy_infra.ipynb", "## Step 6 - Export the non-secret handoff"), state)
            self.assertEqual(dict(dotenv_values(env_path)), VALUES)
            self.assertEqual(len(env_path.read_text(encoding="utf-8").splitlines()), 9)
            state["deployment"].properties.provisioning_state = "Failed"
            original = env_path.read_bytes()
            with self.assertRaisesRegex(RuntimeError, "successful"):
                exec(source("01_deploy_infra.ipynb", "## Step 6 - Export the non-secret handoff"), state)
            self.assertEqual(env_path.read_bytes(), original)

    def test_real_sdk_statistics_model_and_search_token_scope(self) -> None:
        transport, credential, state = self.run_statistics({"counters": {"indexesCount": {"usage": 0, "quota": 15}, "documentCount": {"usage": 0, "quota": 10000}}, "limits": {}})
        self.assertEqual(state["index_count"], 0)
        self.assertEqual(state["document_count"], 0)
        self.assertEqual(credential.scopes, ("https://search.azure.com/.default",))
        self.assertEqual(len(transport.requests), 1)
        method, url = transport.requests[0]
        self.assertEqual(method, "GET")
        self.assertEqual(urlparse(url).path, "/servicestats")
        self.assertEqual(parse_qs(urlparse(url).query), {"api-version": ["2025-09-01"]})

    def test_missing_or_nonzero_sdk_counters_fail(self) -> None:
        for counters in (
            {"indexesCount": {"usage": 1}, "documentCount": {"usage": 0}},
            {"indexesCount": {"usage": 0}, "documentCount": {"usage": 1}},
            {"indexesCount": {"usage": 0}},
            {"indexesCount": {}, "documentCount": {"usage": 0}},
        ):
            with self.subTest(counters=counters):
                with self.assertRaises((ValueError, AttributeError)):
                    self.run_statistics({"counters": counters, "limits": {}})

    def test_sdk_http_failure_is_not_converted_to_success(self) -> None:
        with self.assertRaises(HttpResponseError):
            self.run_statistics({"error": {"code": "Forbidden", "message": "Synthetic access failure"}}, status=403)

    def run_statistics(self, payload: dict[str, Any], status: int = 200) -> tuple[SyntheticTransport, SyntheticCredential, dict[str, Any]]:
        transport = SyntheticTransport(payload, status)
        credential = SyntheticCredential()

        def client(endpoint: str, token_credential: SyntheticCredential, **kwargs: Any) -> SearchIndexClient:
            return SearchIndexClient(endpoint, token_credential, transport=transport, **kwargs)

        state = {
            "SearchIndexClient": client, "environment": VALUES,
            "credential": credential, "SEARCH_API_VERSION": "2025-09-01",
        }
        exec(source("03_test.ipynb", "## Step 4 - Read service statistics through the stable Python SDK"), state)
        return transport, credential, state


class MixedFixtureChecks(unittest.TestCase):
    def test_exact_membership_and_repeatable_generation(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            first = fixture.generate(Path(root) / "first", version=2)
            second = fixture.generate(Path(root) / "second", version=2)
            manifest, documents = fixture.load_manifest(first)
            self.assertEqual(manifest, fixture.load_manifest(second)[0])
            for name in ("manifest.json", "corpus.jsonl", "declared-schema.json"):
                self.assertEqual((first.parent / name).read_bytes(), (second.parent / name).read_bytes())
            groups = manifest["membership"]
            self.assertEqual([len(groups[key]) for key in ("keywordOnly", "shared", "vectorOnly")], [6133, 25, 25])
            self.assertEqual(len(set().union(*map(set, groups.values()))), 6183)
            self.assertEqual(len(documents), 6183)
            self.assertEqual({d["id"] for d in documents if "maths" in d["content"].split()},
                             fixture.expected_ids(manifest, "keyword"))
            scored = sorted(
                ((d["vector"][0] / math.sqrt(sum(x * x for x in d["vector"])), d["id"]) for d in documents),
                reverse=True,
            )
            self.assertEqual({identifier for _, identifier in scored[:50]}, fixture.expected_ids(manifest, "vector"))
            self.assertGreater(scored[49][0] - scored[50][0], 0.3)
            self.assertEqual(len({score for score, _ in scored[:50]}), 50)

    def test_manifest_and_corpus_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            path = fixture.generate(Path(root), version=2)
            original = path.read_bytes()
            manifest = json.loads(original)
            changes = {
                "fixtureVersion": 3, "recordCount": 6158, "keywordMatchCount": 6183,
                "indexName": fixture.INDEX, "generatorRules": "changed",
                "corpusSha256": "0" * 64, "declaredSchemaSha256": "0" * 64,
                "membership": {**manifest["membership"], "shared": []},
                "corpusPath": "..\\corpus.jsonl",
            }
            for key, value in changes.items():
                with self.subTest(key=key):
                    fixture.write_json(path, {**manifest, key: value})
                    with self.assertRaises((ValueError, KeyError)):
                        fixture.load_manifest(path)
            path.write_bytes(original)
            for field, value in (("content", "maths"), ("vector", [1.0] * 16)):
                corpus = path.parent / "corpus.jsonl"
                raw = corpus.read_bytes()
                documents = [json.loads(line) for line in raw.splitlines()]
                documents[-1][field] = value
                altered = fixture.corpus_bytes(documents)
                corpus.write_bytes(altered)
                fixture.write_json(path, {**manifest, "corpusSha256": fixture.sha256(altered)})
                with self.assertRaises(ValueError):
                    fixture.load_manifest(path)
                corpus.write_bytes(raw)
                path.write_bytes(original)

    def test_original_identity_and_overwrite_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            original = fixture.generate(Path(root) / "original")
            saved = original.read_bytes()
            with self.assertRaises((ValueError, FileExistsError)):
                fixture.generate(original.parent, version=2)
            self.assertEqual(original.read_bytes(), saved)
            manifest, documents = fixture.load_manifest(original)
            self.assertEqual(manifest["recordCount"], 6158)
            self.assertNotIn("membership", manifest)
            self.assertEqual(fixture.corpus_bytes(documents), fixture.corpus_bytes(fixture.records()))
            with self.assertRaises(ValueError):
                fixture.generate(Path(root) / "unsupported", version=3)

    def test_dotnet_independently_validates_both_recipes(self) -> None:
        assembly = DEMO / "app" / "dotnet" / "bin" / "Debug" / "net10.0" / "HybridPagination.dll"
        self.assertTrue(assembly.exists(), "Build the existing .NET project before this runtime check.")
        with tempfile.TemporaryDirectory() as root:
            for version in (1, 2):
                path = fixture.generate(Path(root) / str(version), version=version)

                def invoke() -> str:
                    result = subprocess.run(
                        ["dotnet", str(assembly), "--case", "vector", "--manifest", str(path),
                         "--env-file", str(Path(root) / "deliberately-absent.env"), "--run-dir", str(Path(root) / "unused-run")],
                        capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    return result.stderr

                self.assertIn("FileNotFoundException", invoke())
                original = path.read_bytes()
                manifest = json.loads(original)
                for key, value in (("fixtureVersion", 3), ("indexName", "arbitrary"), ("corpusPath", "..\\unexpected")):
                    fixture.write_json(path, {**manifest, key: value})
                    self.assertIn("InvalidDataException", invoke())
                path.write_bytes(original)
                if version == 2:
                    for field, value in (("content", "maths"), ("vector", [1.0] * 16)):
                        corpus = path.parent / "corpus.jsonl"
                        raw = corpus.read_bytes()
                        documents = [json.loads(line) for line in raw.splitlines()]
                        documents[-1][field] = value
                        altered = fixture.corpus_bytes(documents)
                        corpus.write_bytes(altered)
                        fixture.write_json(path, {**manifest, "corpusSha256": fixture.sha256(altered)})
                        self.assertIn("InvalidDataException", invoke())
                        corpus.write_bytes(raw)
                        path.write_bytes(original)


class MixedMeasurementChecks(unittest.TestCase):
    def test_real_sdk_first_response_and_continuation_policy(self) -> None:
        manifest = fixture.manifest_definition(2)
        for case in ("keyword", "vector", "hybrid"):
            for continuation in (False, True):
                with self.subTest(case=case, continuation=continuation):
                    payload = {"@odata.count": 50, "value": [{"id": "doc-006159", "@search.score": 1.0}]}
                    if continuation:
                        payload["@odata.nextLink"] = "https://synthetic.search.windows.net/next"
                        payload["@search.nextPageParameters"] = {"skip": 5}
                    transport = SyntheticTransport(payload)
                    client = SearchClient(
                        "https://synthetic.search.windows.net", fixture.MIXED_INDEX,
                        SyntheticCredential(), api_version=fixture.API, transport=transport,
                        retry_total=0,
                    )
                    result = measure(client, case, manifest, "synthetic", 0, "scan", False)
                    self.assertEqual(len(transport.requests), 1)
                    self.assertEqual(result["sendCount"], 1)
                    self.assertEqual(result["apiVersion"], fixture.API)
                    self.assertEqual(result["incompleteReason"], "service-continuation" if continuation else None)
                    actual = dict(result["normalizedRequest"])
                    actual.pop("skip")
                    self.assertEqual(actual, query_settings(case, manifest))

    def test_failures_preserve_error_and_propagate(self) -> None:
        transport = SyntheticTransport({"error": {"code": "Synthetic", "message": "offline failure"}}, status=400)
        client = SearchClient(
            "https://synthetic.search.windows.net", fixture.MIXED_INDEX,
            SyntheticCredential(), api_version=fixture.API, transport=transport, retry_total=0,
        )
        failed: list[Observation] = []
        with self.assertRaises(HttpResponseError):
            measure(client, "hybrid", fixture.manifest_definition(2), "synthetic", 0, "scan", False, failed.append)
        self.assertEqual(len(failed), 1)
        self.assertIsNone(failed[0]["ids"])
        self.assertIsNone(failed[0]["rowCount"])
        self.assertTrue(failed[0]["error"])


class MixedPreparationChecks(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = fixture.generate(Path(temporary.name), version=2)
        self.manifest, self.documents = fixture.load_manifest(self.path)
        self.environment = {
            "AZURE_SEARCH_ENDPOINT": "https://synthetic.search.windows.net",
            "AZURE_SUBSCRIPTION_ID": "11111111-1111-1111-1111-111111111111",
            "AZURE_SEARCH_RESOURCE_ID": "/synthetic/search-service",
        }
        self.indexes = MagicMock()
        self.client = MagicMock()
        self.client.get_document_count.side_effect = [0, 6183]
        self.client.upload_documents.side_effect = lambda batch: [
            SimpleNamespace(key=d["id"], succeeded=True, status_code=201, error_message=None) for d in batch
        ]
        self.client.search.return_value = [{"id": d["id"], "content": d["content"]} for d in self.documents]
        for target, value in (
            ("load_environment", self.environment),
            ("verify_index", fixture.declared_index(2).as_dict()),
        ):
            mock = patch(f"app.fixture.{target}", return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        self.factories: dict[str, Any] = {}
        for target, instance in (
            ("AzureCliCredential", MagicMock()), ("SearchIndexClient", self.indexes), ("SearchClient", self.client),
        ):
            mock = patch(f"app.fixture.{target}")
            factory = mock.start()
            self.factories[target] = factory
            factory.return_value.__enter__.return_value = instance
            self.addCleanup(mock.stop)

    def test_preparation_and_read_only_reuse(self) -> None:
        finding = fixture.prepare(self.path, Path("synthetic.env"))
        self.assertEqual(finding["indexedCount"], 6183)
        receipt = json.loads((self.path.parent / "preparation.json").read_text())
        self.assertEqual(receipt["status"], "ready")
        self.assertEqual(receipt["checkedSuccessCount"], 6183)
        self.client.get_document_count.side_effect = None
        self.client.get_document_count.return_value = 6183
        self.client.reset_mock()
        fixture.verify_prepared_fixture(self.path, Path("synthetic.env"))
        self.client.upload_documents.assert_not_called()
        self.indexes.create_or_update_index.assert_not_called()
        self.indexes.delete_index.assert_not_called()
        with self.assertRaises(ValueError):
            fixture.prepare(self.path, Path("synthetic.env"))
        self.client.upload_documents.assert_not_called()

    def test_populated_target_is_rejected_before_writes(self) -> None:
        self.client.get_document_count.side_effect = None
        self.client.get_document_count.return_value = 1
        with self.assertRaises(ValueError):
            fixture.prepare(self.path, Path("synthetic.env"))
        self.client.upload_documents.assert_not_called()
        self.indexes.create_index.assert_not_called()
        self.indexes.create_or_update_index.assert_not_called()
        self.assertFalse((self.path.parent / "preparation.json").exists())

    def test_absent_target_uses_only_the_approved_name(self) -> None:
        schema = fixture.declared_index(2).as_dict()
        with patch("app.fixture.verify_index", side_effect=[ResourceNotFoundError("synthetic missing"), schema, schema]):
            fixture.prepare(self.path, Path("synthetic.env"))
        self.assertEqual(self.indexes.create_index.call_args.args[0].name, fixture.MIXED_INDEX)
        self.assertTrue(all(call.args[1] == fixture.MIXED_INDEX for call in self.factories["SearchClient"].call_args_list))
        self.indexes.create_or_update_index.assert_not_called()
        self.indexes.delete_index.assert_not_called()

    def test_missing_service_and_bad_schema_do_not_trigger_repairs(self) -> None:
        for error in (ServiceRequestError("synthetic missing service"), ValueError("synthetic wrong schema")):
            with self.subTest(error=type(error).__name__):
                with patch("app.fixture.verify_index", side_effect=error):
                    with self.assertRaises(type(error)):
                        fixture.prepare(self.path, Path("synthetic.env"))
                self.indexes.create_index.assert_not_called()
                self.client.upload_documents.assert_not_called()

    def test_partial_upload_cannot_be_promoted(self) -> None:
        self.client.upload_documents.side_effect = lambda batch: [
            SimpleNamespace(key=d["id"], succeeded=i != 0, status_code=400, error_message="synthetic failure")
            for i, d in enumerate(batch)
        ]
        with self.assertRaises(RuntimeError):
            fixture.prepare(self.path, Path("synthetic.env"))
        self.assertEqual(json.loads((self.path.parent / "preparation.json").read_text())["status"], "incomplete")
        self.client.get_document_count.side_effect = None
        self.client.get_document_count.return_value = 6183
        with self.assertRaises(ValueError):
            fixture.verify_prepared_fixture(self.path, Path("synthetic.env"))

    def test_indexing_delay_uses_read_only_finalization(self) -> None:
        self.client.get_document_count.side_effect = [0, 6000]
        with self.assertRaises(ValueError):
            fixture.prepare(self.path, Path("synthetic.env"))
        self.assertEqual(json.loads((self.path.parent / "preparation.json").read_text())["status"], "uploaded")
        self.client.get_document_count.side_effect = None
        self.client.get_document_count.return_value = 6183
        self.client.reset_mock()
        fixture.verify_prepared_fixture(self.path, Path("synthetic.env"))
        self.client.upload_documents.assert_not_called()
        self.assertEqual(json.loads((self.path.parent / "preparation.json").read_text())["status"], "ready")

    def test_receipt_identity_and_inventory_are_required(self) -> None:
        with self.assertRaises(FileNotFoundError):
            fixture.verify_prepared_fixture(self.path, Path("synthetic.env"))
        fixture.prepare(self.path, Path("synthetic.env"))
        receipt_path = self.path.parent / "preparation.json"
        receipt = json.loads(receipt_path.read_text())
        self.client.get_document_count.side_effect = None
        self.client.get_document_count.return_value = 6183
        for status in ("uploading", "incomplete"):
            fixture.write_json(receipt_path, {**receipt, "status": status})
            with self.assertRaises(ValueError):
                fixture.verify_prepared_fixture(self.path, Path("synthetic.env"))
        fixture.write_json(receipt_path, {**receipt, "identity": {**receipt["identity"], "indexName": fixture.INDEX}})
        with self.assertRaises(ValueError):
            fixture.verify_prepared_fixture(self.path, Path("synthetic.env"))
        fixture.write_json(receipt_path, receipt)
        self.client.search.return_value = [{"id": "unexpected", "content": "maths"}]
        with self.assertRaises(ValueError):
            fixture.verify_prepared_fixture(self.path, Path("synthetic.env"))

    def test_dotnet_ready_gate_with_an_offline_sdk_transport(self) -> None:
        fixture.prepare(self.path, Path("synthetic.env"))
        binary = DEMO / "app" / "dotnet" / "bin" / "Debug" / "net10.0"
        sdk_version = subprocess.check_output(["dotnet", "--version"], text=True).strip()
        sdk_line = next(line for line in subprocess.check_output(["dotnet", "--list-sdks"], text=True).splitlines()
                        if line.startswith(sdk_version + " "))
        sdk_root = Path(sdk_line.split("[", 1)[1].rstrip("]"))
        reference_root = sdk_root.parent / "packs" / "Microsoft.NETCore.App.Ref"
        reference_pack = max(reference_root.glob("10.*"), key=lambda p: tuple(map(int, p.name.split("."))))
        references = list((reference_pack / "ref" / "net10.0").glob("*.dll"))
        names = {path.name for path in references}
        references += [path for path in binary.glob("*.dll") if path.name not in names]
        source_path = self.path.parent / "ReadinessChecks.cs"
        output = binary / (self.path.parent.name + "-ReadinessChecks.dll")
        self.addCleanup(output.unlink, missing_ok=True)
        source_path.write_text(r'''
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Azure;
using Azure.Core;
using Azure.Core.Pipeline;
using Azure.Search.Documents;

var directory = args[1];
var manifest = JsonNode.Parse(File.ReadAllText(Path.Combine(directory, "manifest.json"))).AsObject();
var environment = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(Path.Combine(directory, "environment.json")));
var rows = new JsonArray(File.ReadLines(Path.Combine(directory, "corpus.jsonl")).Select(line => {
    var row = JsonNode.Parse(line);
    return (JsonNode)new JsonObject { ["id"] = row["id"].GetValue<string>(), ["content"] = row["content"].GetValue<string>() };
}).ToArray());
if (args[2] == "bad-inventory") rows[0]["content"] = "altered";
var transport = new LocalTransport(new JsonObject { ["value"] = rows }.ToJsonString(), args[2] == "bad-count" ? "6000" : "6183");
var options = new SearchClientOptions(SearchClientOptions.ServiceVersion.V2025_09_01) { Transport = transport };
options.Retry.MaxRetries = 0;
var search = new SearchClient(new Uri(environment["AZURE_SEARCH_ENDPOINT"]), "hybrid-pagination-mixed-v2",
    new AzureKeyCredential("synthetic-offline-transport-only"), options);
var assembly = Assembly.LoadFrom(args[0]);
var method = assembly.GetType("Experiment").GetMethod("VerifyPreparedFixture", BindingFlags.Static | BindingFlags.NonPublic);
await (Task)method.Invoke(null, new object[] { Path.Combine(directory, "manifest.json"), manifest, environment, search });
Console.WriteLine("READY_GATES_PASSED");

sealed class LocalTransport : HttpPipelineTransport
{
    readonly string inventory;
    readonly string count;
    public LocalTransport(string inventory, string count) { this.inventory = inventory; this.count = count; }
    public override Request CreateRequest() => HttpClientTransport.Shared.CreateRequest();
    public override void Process(HttpMessage message)
    {
        var method = message.Request.Method;
        if (method != RequestMethod.Get && method != RequestMethod.Post) throw new Exception("Unexpected SDK mutation.");
        message.Response = new LocalResponse(method == RequestMethod.Get ? count : inventory);
    }
    public override ValueTask ProcessAsync(HttpMessage message) { Process(message); return default; }
}
sealed class LocalResponse : Response
{
    public LocalResponse(string body) { ContentStream = new MemoryStream(Encoding.UTF8.GetBytes(body)); }
    public override int Status => 200;
    public override string ReasonPhrase => "Synthetic offline";
    public override Stream ContentStream { get; set; }
    public override string ClientRequestId { get; set; } = "synthetic";
    public override void Dispose() => ContentStream.Dispose();
    protected override bool ContainsHeader(string name) => name.Equals("Content-Type", StringComparison.OrdinalIgnoreCase);
    protected override IEnumerable<HttpHeader> EnumerateHeaders() => new[] { new HttpHeader("Content-Type", "application/json") };
    protected override bool TryGetHeader(string name, out string value) { value = "application/json"; return ContainsHeader(name); }
    protected override bool TryGetHeaderValues(string name, out IEnumerable<string> values) { values = new[] { "application/json" }; return ContainsHeader(name); }
}
''', encoding="utf-8")
        compiled = subprocess.run(
            ["dotnet", str(sdk_root / sdk_version / "Roslyn" / "bincore" / "csc.dll"),
             "-nologo", "-target:exe", f"-out:{output}", *[f"-r:{path}" for path in references], str(source_path)],
            capture_output=True, text=True,
        )
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        fixture.write_json(self.path.parent / "environment.json", self.environment)
        command = [
            "dotnet", "exec", "--runtimeconfig", str(binary / "HybridPagination.runtimeconfig.json"),
            "--depsfile", str(binary / "HybridPagination.deps.json"), str(output),
            str(binary / "HybridPagination.dll"), str(self.path.parent),
        ]
        receipt_path = self.path.parent / "preparation.json"
        receipt = json.loads(receipt_path.read_text())
        valid = subprocess.run([*command, "valid"], capture_output=True, text=True)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        self.assertIn("READY_GATES_PASSED", valid.stdout)
        for state in ("uploading", "uploaded", "incomplete"):
            fixture.write_json(receipt_path, {**receipt, "status": state})
            rejected = subprocess.run([*command, "valid"], capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("InvalidDataException", rejected.stderr)
        fixture.write_json(receipt_path, receipt)
        for mode in ("bad-count", "bad-inventory"):
            rejected = subprocess.run([*command, mode], capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("InvalidDataException", rejected.stderr)


def write_synthetic_case(
    directory: Path, manifest: dict[str, Any], language: str, case: Case, ids: list[str],
    count: int | None, profile: SearchProfile | None = None,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    name = profile.name if profile else f"{language}-{case}"
    page_count = math.ceil((50 if count is None else count) / 5)
    pages: list[Observation] = []

    def page(offset: int, phase: Any) -> Observation:
        rows = ids[offset:offset + 5]
        return {
            "runId": directory.name, "language": language, "case": case, "phase": phase,
            "pageNumber": offset // 5 + 1, "skip": offset, "top": 5,
            "advertised": count is not None and offset < page_count * 5,
            "ids": rows, "scores": [1.0] * len(rows), "rowCount": len(rows),
            "reportedCount": count, "timestamp": "2026-11-02T00:00:00Z",
            "apiVersion": profile.api_version if profile else fixture.API, "method": "POST",
            "path": f"/indexes('{manifest['indexName']}')/docs/search.post.search",
            "normalizedRequest": {**query_settings(case, manifest, profile), "skip": offset},
            "sendCount": 1, "statusCode": 200, "requestId": "synthetic",
            "continuation": False, "incompleteReason": None, "error": None,
        }

    pages.extend(page(offset, "scan") for offset in range(0, max(1, page_count) * 5, 5))
    summary = summarize(pages, case, manifest, 6183, 6183)
    offsets = boundary_offsets(summary, 5)
    for offset in offsets:
        if not any(row["skip"] == offset for row in pages):
            pages.append(page(offset, "boundary-probe"))
        pages.append(page(offset, "boundary-repeat"))
    summary = summarize(pages, case, manifest, 6183, 6183)
    boundaries = boundary_agreement(pages, offsets)
    status, outcome, reasons = classification(summary, boundaries, pages, case, manifest)
    report = {
        "schemaVersion": 1, "runId": directory.name, "language": language, "case": case,
        "fixture": manifest, "index": {"name": manifest["indexName"], "actualSchemaFile": f"{name}.schema.json"},
        "environment": {"AZURE_SEARCH_ENDPOINT": "https://synthetic.search.windows.net"},
        "client": {
            "configuredApi": profile.api_version if profile else fixture.API,
            "packages": (
                {"azure-search-documents": profile.sdk_version if profile else "12.0.0", "azure-identity": "1.25.3"}
                if language == "python" else {"Azure.Search.Documents": "12.0.0", "Azure.Identity": "1.21.0"}
            ),
        },
        "query": query_settings(case, manifest, profile), "startedAt": "2026-11-02T00:00:00Z",
        "finishedAt": "2026-11-02T00:00:01Z", "status": status, "outcome": outcome, "reasons": reasons,
        "observationsFile": f"{name}.pages.jsonl", "summary": summary, "boundaries": boundaries,
        "limitations": ["Synthetic local test evidence; no live acceptance."],
    }
    if profile:
        report["profile"] = profile.name
    fixture.write_json(directory / f"{name}.json", report)
    fixture.write_json(directory / f"{name}.schema.json", fixture.declared_index(2).as_dict())
    (directory / f"{name}.pages.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in pages), encoding="utf-8",
    )
    return directory / f"{name}.json"


class MixedContributionChecks(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = fixture.generate(Path(temporary.name) / "fixture", version=2)
        self.manifest, _ = fixture.load_manifest(self.path)
        self.run = Path(temporary.name) / "synthetic-run"
        keyword = sorted(fixture.expected_ids(self.manifest, "keyword"))
        vector = sorted(fixture.expected_ids(self.manifest, "vector"))
        small = sorted(set(keyword[:1000]) | set(vector))
        for language in ("python", "dotnet"):
            for case, ids, count in (("keyword", keyword, 6158), ("vector", vector, 50), ("hybrid", small, 6158)):
                write_synthetic_case(self.run, self.manifest, language, case, ids, count)
        from app.preview import profile
        for scenario, ids in (("retrievable", small), ("expanded", sorted(fixture.expected_ids(self.manifest)))):
            write_synthetic_case(self.run, self.manifest, "python", "hybrid", ids, len(ids), profile(scenario))

    def test_complete_contributions_and_text_provenance(self) -> None:
        from app.contributions import comparison, render
        with patch("socket.create_connection", side_effect=AssertionError("Network forbidden")):
            result = comparison(self.path, self.run)
        self.assertTrue(result["measurementsComplete"])
        self.assertTrue(result["contributionAcceptance"])
        self.assertEqual(result["keywordWindowMembership"], {"status": "not-observed", "ids": None})
        self.assertEqual(len(result["cases"]), 8)
        for finding in result["hybridContributions"].values():
            self.assertEqual(len(finding["verifiedVectorOnlyIds"]), 25)
            self.assertGreaterEqual(len(finding["textExamples"]), 3)
            self.assertTrue(all(row["textSource"] == "verified-fixture" for row in finding["textExamples"]))
        self.assertTrue(result["countFindings"]["preview-retrievable-6158"]["countAlignmentVerified"])
        self.assertIn("6,183", render(result))
        self.assertTrue((self.run / "contribution-comparison.json").exists())

    def test_incomplete_control_never_establishes_additions(self) -> None:
        from app.contributions import comparison
        ids = sorted(fixture.expected_ids(self.manifest, "keyword"))
        ids[-1] = ids[0]
        write_synthetic_case(self.run, self.manifest, "python", "keyword", ids, 6158)
        result = comparison(self.path, self.run)
        self.assertFalse(result["contributionAcceptance"])
        self.assertTrue(all(row["verifiedVectorOnlyIds"] is None for row in result["hybridContributions"].values()))

    def test_missing_and_altered_evidence_remain_blocked(self) -> None:
        from app.contributions import comparison
        (self.run / "dotnet-vector.json").unlink()
        report_path = self.run / "preview-retrievable-6158.json"
        report = json.loads(report_path.read_text())
        report["summary"]["uniqueReachableIds"] = 1
        fixture.write_json(report_path, report)
        result = comparison(self.path, self.run)
        self.assertFalse(result["measurementsComplete"])
        self.assertFalse(result["contributionAcceptance"])
        self.assertIsNone(result["cases"]["dotnet-vector"])
        self.assertIn("dotnet-vector", result["missingCases"])
        self.assertTrue(result["cases"]["preview-retrievable-6158"]["reasons"])

    def test_following_results_invalidate_count_alignment(self) -> None:
        from app.contributions import comparison
        from app.preview import profile
        ids = sorted(fixture.expected_ids(self.manifest))
        write_synthetic_case(self.run, self.manifest, "python", "hybrid", ids, 6180, profile("expanded"))
        result = comparison(self.path, self.run)
        self.assertTrue(result["countFindings"]["preview-retrievable-6158"]["resultsBeyondAdvertisedRange"])
        self.assertFalse(result["countFindings"]["preview-retrievable-6158"]["countAlignmentVerified"])
        self.assertFalse(result["contributionAcceptance"])

    def test_wrong_vector_membership_and_missing_vector_count(self) -> None:
        from app.compare import inspect_case
        ids = sorted(fixture.expected_ids(self.manifest, "vector"))
        path = write_synthetic_case(self.run, self.manifest, "python", "vector", ids, None)
        self.assertEqual(inspect_case(path)["status"], "complete")
        self.assertIsNone(inspect_case(path)["summary"]["reportedCount"])
        ids[0] = "doc-000001"
        path = write_synthetic_case(self.run, self.manifest, "python", "vector", ids, 50)
        self.assertEqual(inspect_case(path)["status"], "incomplete")

    def test_identity_request_drift_boundaries_and_overwrite_refusal(self) -> None:
        from app.compare import inspect_case
        from app.contributions import comparison
        from app.preview import profile, validate_baseline
        from app.reproduce import run
        self.assertEqual(profile("expanded", manifest=self.manifest).hybrid_search["maxTextRecallSize"], 6158)
        with self.assertRaises(FileExistsError):
            run("hybrid", self.path, Path("deliberately-absent.env"), self.run)
        original = fixture.generate(self.path.parent.parent / "original")
        with self.assertRaises(ValueError):
            validate_baseline(self.run / "python-hybrid.json", original, Path("deliberately-absent.env"))
        path = self.run / "python-hybrid.pages.jsonl"
        raw = path.read_bytes()
        pages = [json.loads(line) for line in raw.splitlines()]
        pages[1]["reportedCount"] += 1
        path.write_text("".join(json.dumps(row) + "\n" for row in pages), encoding="utf-8")
        case = inspect_case(self.run / "python-hybrid.json")
        self.assertTrue(case["summary"]["countChanged"])
        self.assertEqual(case["status"], "incomplete")
        path.write_bytes(raw)
        pages = [json.loads(line) for line in raw.splitlines()]
        repeated = next(row for row in pages if row["phase"] == "boundary-repeat" and row["ids"])
        repeated["ids"][0] = "doc-000999"
        path.write_text("".join(json.dumps(row) + "\n" for row in pages), encoding="utf-8")
        self.assertEqual(inspect_case(self.run / "python-hybrid.json")["status"], "incomplete")
        path.write_bytes(raw)
        report_path = self.run / "dotnet-vector.json"
        report = json.loads(report_path.read_text())
        report["environment"] = {"AZURE_SEARCH_ENDPOINT": "https://different.search.windows.net"}
        fixture.write_json(report_path, report)
        result = comparison(self.path, self.run)
        self.assertTrue(result["identityMismatches"])
        self.assertFalse(result["contributionAcceptance"])

    def test_cli_exit_status_and_durable_partial_report(self) -> None:
        command = [
            sys.executable, "-m", "app.contributions", "--manifest", str(self.path), "--run-dir", str(self.run),
        ]
        result = subprocess.run(command, cwd=DEMO, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.run / "dotnet-vector.json").unlink()
        result = subprocess.run(command, cwd=DEMO, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        saved = json.loads((self.run / "contribution-comparison.json").read_text())
        self.assertEqual(saved["status"], "blocked/incomplete")
        self.assertIn("dotnet-vector", saved["missingCases"])


class MixedNotebookChecks(unittest.TestCase):
    def test_syntax_hygiene_and_offline_command_wiring(self) -> None:
        data = notebook("06_vector_contributions.ipynb")
        self.assertNotIn("display_name", data["metadata"]["kernelspec"])
        self.assertEqual(data["metadata"]["kernelspec"]["name"], "search02-hybrid-pagination")
        headings = {
            "mixed-prerequisites": "Prerequisites and explicit paths",
            "mixed-generation": "Local generation and declared groups",
            "mixed-build": "Build the independent .NET reader",
            "mixed-preparation": "Separately approved one-time preparation",
            "mixed-reuse": "Read-only reuse and fresh run",
            "mixed-python-keyword": "Python keyword control",
            "mixed-dotnet-keyword": "Independent .NET keyword control",
            "mixed-python-vector": "Python vector control",
            "mixed-dotnet-vector": "Independent .NET vector control",
            "mixed-python-hybrid": "Python stable hybrid",
            "mixed-dotnet-hybrid": "Independent .NET stable hybrid",
            "mixed-preview-small": "Smaller retrievable-count hybrid [PREVIEW]",
            "mixed-preview-expanded": "Expanded retrievable-count hybrid [PREVIEW]",
            "mixed-review": "Local contribution review",
        }
        cells = {key: source("06_vector_contributions.ipynb", "## " + heading) for key, heading in headings.items()}
        for cell in data["cells"]:
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), cell["id"], "exec")
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])
        with tempfile.TemporaryDirectory() as root:
            demo = Path(root)
            for relative in (
                "app\\fixture.py", ".venv\\Scripts\\python.exe", ".venv-preview\\Scripts\\python.exe",
                "env\\.env", "app\\dotnet\\HybridPagination.csproj",
            ):
                path = demo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            namespace: dict[str, Any] = {}
            old_path = sys.path.copy()
            self.addCleanup(lambda: sys.path.__setitem__(slice(None), old_path))
            with patch("pathlib.Path.cwd", return_value=demo), patch("builtins.print"):
                exec(cells["mixed-prerequisites"], namespace)
                exec(cells["mixed-generation"], namespace)
                self.assertEqual(namespace["manifest"]["recordCount"], 6183)
                with patch("app.fixture.prepare") as prepare:
                    with self.assertRaises(ValueError):
                        exec(cells["mixed-preparation"], namespace)
                    prepare.assert_not_called()
                with patch("app.fixture.verify_prepared_fixture", return_value={"status": "ready"}):
                    exec(cells["mixed-reuse"], namespace)
                    first_run = namespace["run_dir"]
                    exec(cells["mixed-reuse"], namespace)
                    self.assertNotEqual(first_run, namespace["run_dir"])
                with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "offline stdout", "")) as run:
                    exec(cells["mixed-build"], namespace)
                    for name in (
                        "mixed-python-keyword", "mixed-dotnet-keyword", "mixed-python-vector", "mixed-dotnet-vector",
                        "mixed-python-hybrid", "mixed-dotnet-hybrid", "mixed-preview-small", "mixed-preview-expanded",
                    ):
                        exec(cells[name], namespace)
                        command = run.call_args.args[0]
                        self.assertEqual(command[command.index("--manifest") + 1], str(namespace["manifest_path"]))
                        self.assertEqual(command[command.index("--run-dir") + 1], str(namespace["run_dir"]))
                        if "preview" in name:
                            self.assertEqual(command[0], str(namespace["preview_python"]))
                            self.assertEqual(command[command.index("--baseline") + 1],
                                             str(namespace["run_dir"] / "python-hybrid.json"))
                with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 7, "failed stdout", "failed stderr")):
                    with self.assertRaises(subprocess.CalledProcessError):
                        exec(cells["mixed-python-keyword"], namespace)
                    (namespace["run_dir"] / "contribution-comparison.md").write_text("blocked/incomplete", encoding="utf-8")
                    namespace["display"] = MagicMock()
                    with self.assertRaises(subprocess.CalledProcessError):
                        exec(cells["mixed-review"], namespace)
                    namespace["display"].assert_called_once()


class CanonicalChecks(unittest.TestCase):
    def test_destroy_is_verbatim(self) -> None:
        original = REPOSITORY / "demos" / "speech01-foundry-speech" / "notebooks" / "X_destroy.ipynb"
        self.assertEqual(original.read_bytes(), (DEMO / "notebooks" / "X_destroy.ipynb").read_bytes())

    def test_setup_has_only_permitted_substitutions(self) -> None:
        original = REPOSITORY / "demos" / "speech01-foundry-speech" / "notebooks" / "00_setup.ipynb"
        expected = original.read_text(encoding="utf-8").replace("Python (speech01-foundry-speech)", "Python (search02-hybrid-pagination)").replace("| Python | `>= 3.10` |", "| Python | `>= 3.11` |")
        self.assertEqual(expected, (DEMO / "notebooks" / "00_setup.ipynb").read_text(encoding="utf-8"))

    def test_cli_resolver_is_canonical(self) -> None:
        original = REPOSITORY / "demos" / "speech01-foundry-speech" / "app" / "notebook_helpers.py"
        expected = next(node for node in ast.parse(original.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == "resolve_az_cli")
        actual = next(node for node in ast.parse((DEMO / "app" / "notebook_helpers.py").read_text()).body if isinstance(node, ast.FunctionDef) and node.name == "resolve_az_cli")
        self.assertEqual(ast.dump(expected), ast.dump(actual))

    def test_configuration_is_explanatory_only(self) -> None:
        self.assertTrue(all(cell["cell_type"] == "markdown" for cell in notebook("02_configure.ipynb")["cells"]))


def main() -> int:
    GENERATED.mkdir(parents=True, exist_ok=True)
    groups = (
        (InfrastructureChecks, "us1-static-validation.json"),
        (HandoffChecks, "us2-local-validation.json"),
        (CanonicalChecks, "us3-static-validation.json"),
        (MixedFixtureChecks, "mixed-fixture-local-validation.json"),
        (MixedMeasurementChecks, "mixed-measurement-local-validation.json"),
        (MixedPreparationChecks, "mixed-preparation-local-validation.json"),
        (MixedContributionChecks, "mixed-contribution-local-validation.json"),
        (MixedNotebookChecks, "mixed-notebook-local-validation.json"),
    )
    succeeded = True
    for case, filename in groups:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        evidence = {
            "observedAt": datetime.now(timezone.utc).isoformat(),
            "mode": "local-synthetic-no-azure",
            "status": "passed" if result.wasSuccessful() else "failed",
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "liveAcceptance": "not-run",
        }
        (GENERATED / filename).write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        succeeded = succeeded and result.wasSuccessful()
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
