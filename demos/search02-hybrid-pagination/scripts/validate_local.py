"""Validate Feature 1 locally with compiled Bicep and synthetic SDK responses."""

import ast
from collections.abc import Iterator
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from types import SimpleNamespace, TracebackType
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from azure.core.credentials import AccessToken
from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.transport import HttpRequest, HttpResponse, HttpTransport
from azure.mgmt.resource.deployments import DeploymentsMgmtClient
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.identity import AzureCliCredential
from azure.search.documents.indexes import SearchIndexClient
from dotenv import dotenv_values

DEMO = Path(__file__).resolve().parents[1]
REPOSITORY = DEMO.parents[1]
GENERATED = DEMO / "outputs" / "generated"
sys.path.insert(0, str(DEMO))

from app.notebook_helpers import ENV_OUTPUTS, environment_from_outputs, validate_environment

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
        self.assertEqual(actual["status"], "validated")


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
