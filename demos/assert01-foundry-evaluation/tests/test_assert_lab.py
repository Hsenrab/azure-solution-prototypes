import ast
import asyncio
from contextlib import chdir, redirect_stdout
from dataclasses import replace
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from azure.mgmt.cognitiveservices.models import Account, Deployment, Model, Usage
from dotenv import dotenv_values

from app.assert_lab import (
    DeploymentMetadata,
    ModelDeployment,
    artifact_path,
    load_connections,
    provider_model,
    smoke_connections,
    validate_catalog,
    validate_deployments,
    write_connections,
)


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
SPEECH = REPOSITORY / "demos" / "speech01-foundry-speech"


def deployments():
    return (
        ModelDeployment("older", "assert-older", "gpt-5", "2025-08-07", "GlobalStandard", 10),
        ModelDeployment("intermediate", "assert-intermediate", "gpt-5.4", "2026-03-05", "GlobalStandard", 10),
        ModelDeployment("newer", "assert-newer", "gpt-5.6-sol", "2026-07-09", "GlobalStandard", 10),
    )


def metadata():
    return DeploymentMetadata(
        subscription_id="synthetic-subscription",
        resource_group="rg-synthetic-assert",
        location="eastus2",
        account_name="aisyntheticassert",
        account_id="/subscriptions/synthetic-subscription/resourceGroups/rg-synthetic-assert/providers/Microsoft.CognitiveServices/accounts/aisyntheticassert",
        ai_endpoint="https://aisyntheticassert.cognitiveservices.azure.com/",
        project_name="proj-assert01",
        project_endpoint="https://aisyntheticassert.services.ai.azure.com/api/projects/proj-assert01",
        api_base="https://aisyntheticassert.openai.azure.com/",
        api_version="2024-10-21",
        deployments=deployments(),
    )


def catalog():
    return [
        Model.deserialize({
            "kind": "AIServices", "skuName": "S0",
            "model": {
                "format": "OpenAI", "name": selected.model_name, "version": selected.model_version,
                "lifecycleStatus": "GenerallyAvailable",
                "skus": [{
                    "name": "GlobalStandard", "usageName": f"OpenAI.GlobalStandard.{selected.model_name}",
                    "capacity": {"default": 10, "maximum": 1000000},
                }],
            },
        })
        for selected in deployments()
    ]


def quotas():
    return [
        Usage.deserialize({
            "name": {"value": f"OpenAI.GlobalStandard.{selected.model_name}"},
            "unit": "Count", "currentValue": 0, "limit": 250,
        })
        for selected in deployments()
    ]


class DeploymentContractTests(unittest.TestCase):
    def test_exactly_three_aliases_and_distinct_models(self):
        self.assertEqual(validate_deployments(deployments()), deployments())
        for invalid in (
            deployments()[:2],
            (*deployments()[:2], replace(deployments()[2], alias="older")),
            (*deployments()[:2], replace(deployments()[2], deployment_name="ASSERT-OLDER")),
            (*deployments()[:2], replace(deployments()[2], model_name="gpt-5")),
            (*deployments()[:2], replace(deployments()[2], model_version="2025-08-07")),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_deployments(invalid)

    def test_invalid_values_do_not_become_defaults(self):
        for field, value in (
            ("capacity", 0), ("capacity", True), ("model_version", ""),
            ("alias", "unknown"), ("sku", "Standard"),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(deployments()[0], **{field: value})

    def test_native_provider_uses_deployment_name_not_alias_or_model(self):
        self.assertEqual(provider_model(deployments()[0]), "azure/gpt5_series/assert-older")

    def test_artifacts_resolve_under_generated_directory(self):
        path = artifact_path("configs", "smoke.json")
        self.assertTrue(path.is_absolute())
        self.assertTrue(path.is_relative_to(ROOT / "outputs" / "generated"))
        with self.assertRaises(ValueError):
            artifact_path("..", "..", "escaped.json")

    def test_connection_files_round_trip_without_secret_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            env_path, metadata_path = write_connections(metadata(), root=root)
            self.assertEqual(env_path, root / "env" / ".env")
            self.assertEqual(metadata_path, root / "outputs" / "generated" / "deployment.json")
            self.assertNotIn("synthetic-test-key", metadata_path.read_text())
            self.assertNotIn("AZURE_API_KEY", metadata_path.read_text())
            env = dotenv_values(env_path)
            self.assertNotIn("AZURE_API_KEY", env)
            self.assertEqual(env["ASSERT_AZURE_USE_AAD"], "1")
            self.assertEqual(env["ASSERT_TARGET_NEWER"], "assert-newer")
            with patch.dict(os.environ, {}, clear=True):
                restored = load_connections(root=root)
                self.assertEqual(restored, metadata())
                self.assertNotIn("AZURE_API_KEY", os.environ)

    def test_missing_environment_fails(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(FileNotFoundError):
            load_connections(root=Path(directory))

    def test_missing_auth_setting_and_stale_metadata_fail_before_client_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env_path, _ = write_connections(metadata(), root=root)
            content = env_path.read_text()
            env_path.write_text(content.replace('ASSERT_AZURE_USE_AAD="1"\n', ""))
            with patch.dict(os.environ, {"AZURE_API_KEY": "ambient-key"}), self.assertRaises(ValueError):
                load_connections(root=root)
            env_path.write_text(content.replace("assert-newer", "different-deployment"))
            with self.assertRaises(ValueError):
                load_connections(root=root)

    def test_writer_does_not_accept_account_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(TypeError):
                write_connections(metadata(), "", root=root)
            self.assertFalse((root / "env" / ".env").exists())

    def test_entra_loader_clears_ambient_keys_and_rejects_stored_tokens(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env_path, _ = write_connections(metadata(), root=root)
            with patch.dict(os.environ, {"AZURE_API_KEY": "ambient-key", "AZURE_AD_TOKEN": "ambient-token"}):
                load_connections(root=root)
                self.assertNotIn("AZURE_API_KEY", os.environ)
                self.assertNotIn("AZURE_AD_TOKEN", os.environ)
            with env_path.open("a", encoding="utf-8") as file:
                file.write('AZURE_AD_TOKEN="synthetic-token"\n')
            with self.assertRaisesRegex(ValueError, "keys/tokens"):
                load_connections(root=root)

    def test_metadata_rejects_secret_fields(self):
        payload = metadata().to_dict()
        payload["api_key"] = "synthetic-test-key"
        with self.assertRaises(ValueError):
            DeploymentMetadata.from_dict(payload)

    def test_partial_metadata_requires_an_explicit_skip_and_clears_ambient_alias(self):
        partial = replace(
            metadata(), deployments=(deployments()[0], deployments()[2]),
            skipped_deployment=deployments()[1], skip_reason="Explicit quota-blocked verification",
        )
        self.assertEqual(len(partial.deployments), 2)
        with self.assertRaises(ValueError):
            replace(partial, skip_reason=None)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_connections(partial, root=root)
            with patch.dict(os.environ, {"ASSERT_TARGET_INTERMEDIATE": "stale-deployment"}):
                self.assertEqual(load_connections(root=root), partial)
                self.assertNotIn("ASSERT_TARGET_INTERMEDIATE", os.environ)


class CatalogTests(unittest.TestCase):
    def test_selects_the_deployed_account_kind_not_duplicate_openai_rows(self):
        openai_rows = catalog()
        for row in openai_rows:
            row.kind = "OpenAI"
        rows = validate_catalog(deployments(), openai_rows + catalog(), quotas())
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["capacity"] == 10 for row in rows))
        self.assertTrue(all(row["quota_limit"] == 250 for row in rows))

    def test_exact_identity_lifecycle_and_sku_are_required(self):
        for attribute, value in (("version", "unavailable"), ("lifecycle_status", "Deprecated")):
            records = catalog()
            setattr(records[0].model, attribute, value)
            with self.subTest(attribute=attribute), self.assertRaises(ValueError):
                validate_catalog(deployments(), records, quotas())
        records = catalog()
        records[0].model.skus[0].name = "Standard"
        with self.assertRaises(ValueError):
            validate_catalog(deployments(), records, quotas())
        with self.assertRaises(ValueError):
            validate_catalog(deployments(), catalog()[1:], quotas())

    def test_missing_increments_only_permit_the_advertised_default(self):
        selected = (replace(deployments()[0], capacity=11), *deployments()[1:])
        with self.assertRaisesRegex(ValueError, "advertised default capacity 10"):
            validate_catalog(selected, catalog(), quotas())

    def test_known_increments_allowed_values_and_maximum_are_enforced(self):
        records = catalog()
        capacity = records[0].model.skus[0].capacity
        capacity.minimum, capacity.step = 2, 4
        self.assertEqual(len(validate_catalog(deployments(), records, quotas())), 3)
        selected = (replace(deployments()[0], capacity=11), *deployments()[1:])
        with self.assertRaisesRegex(ValueError, "minimum/increment"):
            validate_catalog(selected, records, quotas())
        capacity.allowed_values = [10, 20]
        selected = (replace(deployments()[0], capacity=20), *deployments()[1:])
        self.assertEqual(validate_catalog(selected, records, quotas())[0]["capacity"], 20)
        capacity.maximum = 15
        with self.assertRaisesRegex(ValueError, "maximum"):
            validate_catalog(selected, records, quotas())

    def test_real_quota_blocker_and_missing_quota_fail(self):
        usage = quotas()
        usage[1].current_value = 400
        with self.assertRaisesRegex(ValueError, r"gpt-5.4.*used 400.*limit 250.*requested 10"):
            validate_catalog(deployments(), catalog(), usage)
        with self.assertRaisesRegex(ValueError, "Missing quota"):
            validate_catalog(deployments(), catalog(), quotas()[1:])


class NativeSmokeTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {
            "ASSERT_AZURE_USE_AAD": "1", "AZURE_TOKEN_CREDENTIALS": "AzureCliCredential",
        })
        environment.start()
        self.addCleanup(environment.stop)

    def test_released_client_parses_structured_output_and_provider_maps_tokens(self):
        from litellm.utils import get_optional_params

        def response(text):
            return {"choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop"}]}

        transport = MagicMock()
        transport.acompletion = AsyncMock(side_effect=[response("READY"), response('{"ready":true}')] * 3)
        with patch("assert_ai.core.model_client._get_litellm_module", return_value=transport):
            results = asyncio.run(smoke_connections(metadata()))
        self.assertEqual(len(results), 3)
        self.assertEqual(transport.acompletion.await_count, 6)
        structured_request = transport.acompletion.await_args_list[1].kwargs
        self.assertEqual(structured_request["response_format"]["type"], "json_schema")
        self.assertTrue(callable(structured_request["azure_ad_token_provider"]))
        self.assertNotIn("api_key", structured_request)
        parameters = get_optional_params(
            model="gpt5_series/assert-older", custom_llm_provider="azure", max_tokens=1024,
        )
        self.assertEqual(parameters["max_completion_tokens"], 1024)
        self.assertNotIn("max_tokens", parameters)

    def test_native_calls_for_all_targets_have_only_nonsecret_results(self):
        from assert_ai.core.model_client import ModelResponse

        text = ModelResponse(text="READY", finish_reason="stop", api_mode="chat_completion")
        structured = ModelResponse(parsed={"ready": True}, finish_reason="stop", api_mode="chat_completion")
        with (
            patch("assert_ai.core.model_client.generate", new=AsyncMock(return_value=text)) as generate,
            patch("assert_ai.core.model_client.generate_structured", new=AsyncMock(return_value=structured)) as generate_structured,
        ):
            results = asyncio.run(smoke_connections(metadata()))
        expected = [provider_model(model) for model in deployments()]
        self.assertEqual([call.args[0] for call in generate.await_args_list], expected)
        self.assertEqual([call.args[0] for call in generate_structured.await_args_list], expected)
        self.assertTrue(all(result["structured_ready"] is True for result in results))
        self.assertTrue(all(result["api_mode"] == "chat_completion" for result in results))
        self.assertNotIn("api_key", json.dumps(results))
        self.assertNotIn("request_payload", json.dumps(results))
        self.assertFalse(generate.await_args_list[0].args[2].web_search)
        self.assertEqual(generate.await_args_list[0].args[2].max_tokens, 4096)

    def test_failed_checks_do_not_produce_success_or_try_another_provider(self):
        from assert_ai.core.model_client import ModelResponse

        for parsed in (None, {"ready": False}, {"ready": 1}, {"ready": True, "extra": True}):
            with (
                self.subTest(parsed=parsed),
                patch("assert_ai.core.model_client.generate", new=AsyncMock(return_value=ModelResponse(
                    text="READY", api_mode="chat_completion", finish_reason="stop",
                ))) as generate,
                patch("assert_ai.core.model_client.generate_structured", new=AsyncMock(return_value=ModelResponse(
                    parsed=parsed, api_mode="chat_completion", finish_reason="stop",
                ))) as generate_structured,
                self.assertRaisesRegex(ValueError, "structured-output"),
            ):
                asyncio.run(smoke_connections(metadata()))
            self.assertEqual(generate.await_count, 1)
            self.assertEqual(generate_structured.await_count, 1)


class NotebookContractTests(unittest.TestCase):
    def test_export_uses_actual_sdk_properties_and_writes_only_nonsecret_settings(self):
        context = metadata()
        cognitive = MagicMock()
        cognitive.accounts.get.return_value = Account.deserialize({
            "id": context.account_id, "name": context.account_name, "location": context.location,
            "properties": {"endpoint": context.ai_endpoint, "disableLocalAuth": True, "publicNetworkAccess": "Enabled"},
        })
        cognitive.deployments.get.side_effect = [
            Deployment.deserialize({
                "name": model.deployment_name, "sku": {"name": model.sku, "capacity": model.capacity},
                "properties": {
                    "model": {"format": "OpenAI", "name": model.model_name, "version": model.model_version},
                    "versionUpgradeOption": "NoAutoUpgrade",
                },
            }) for model in context.deployments
        ]
        document = json.loads((ROOT / "notebooks" / "01_deploy_infra.ipynb").read_text())
        cell = next(
            cell for cell in document["cells"]
            if cell["cell_type"] == "code" and "account = cognitive.accounts.get(" in "".join(cell["source"])
        )
        with tempfile.TemporaryDirectory() as directory:
            namespace = {
                "cognitive": cognitive, "RESOURCE_GROUP": context.resource_group,
                "SUBSCRIPTION_ID": context.subscription_id, "MODEL_SELECTIONS": context.deployments,
                "SKIPPED_MODEL": None, "SKIP_REASON": None, "demo_root": Path(directory),
                "PROVIDER_API_VERSION": context.api_version, "DeploymentMetadata": DeploymentMetadata,
                "ModelDeployment": ModelDeployment, "write_connections": write_connections,
                "deployment_outputs": {
                    "aiServicesAccountName": {"value": context.account_name},
                    "foundryProjectName": {"value": context.project_name},
                    "foundryProjectEndpoint": {"value": context.project_endpoint},
                    "azureOpenAIEndpoint": {"value": context.api_base},
                },
            }
            with redirect_stdout(io.StringIO()):
                exec(compile("".join(cell["source"]), "export", "exec"), namespace)
            self.assertEqual(namespace["metadata"], context)
            env = dotenv_values(Path(directory) / "env" / ".env")
            self.assertEqual(env["ASSERT_AZURE_USE_AAD"], "1")
            self.assertNotIn("AZURE_API_KEY", env)
            cognitive.accounts.list_keys.assert_not_called()

    def test_quota_block_stops_notebook_before_resource_creation(self):
        cognitive, resources = MagicMock(), MagicMock()
        cognitive.models.list.return_value = catalog()
        usage = quotas()
        usage[2].current_value = 400
        cognitive.usages.list.return_value = usage
        notebook = json.loads((ROOT / "notebooks" / "01_deploy_infra.ipynb").read_text())
        with tempfile.TemporaryDirectory() as directory:
            notebook_directory = Path(directory) / "notebooks"
            notebook_directory.mkdir()
            with (
                chdir(notebook_directory), redirect_stdout(io.StringIO()),
                patch.dict(os.environ, {"AZURE_SUBSCRIPTION_ID": "synthetic-subscription"}),
                patch("app.notebook_helpers.resolve_az_cli", return_value="az"),
                patch("azure.mgmt.cognitiveservices.CognitiveServicesManagementClient", return_value=cognitive),
                patch("azure.mgmt.resource.resources.ResourceManagementClient", return_value=resources),
                self.assertRaisesRegex(ValueError, "Insufficient quota"),
            ):
                namespace = {}
                for cell in notebook["cells"]:
                    if cell["cell_type"] == "code":
                        exec(compile("".join(cell["source"]), cell["id"], "exec"), namespace)
            resources.resource_groups.create_or_update.assert_not_called()
            cognitive.accounts.list_keys.assert_not_called()
            self.assertFalse((Path(directory) / "env" / ".env").exists())

    def test_destroy_is_verbatim_source(self):
        self.assertEqual(
            (ROOT / "notebooks" / "X_destroy.ipynb").read_bytes(),
            (SPEECH / "notebooks" / "X_destroy.ipynb").read_bytes(),
        )

    def test_setup_only_has_authorized_substitutions(self):
        source = (SPEECH / "notebooks" / "00_setup.ipynb").read_text(encoding="utf-8")
        expected = source.replace("speech01-foundry-speech", ROOT.name).replace(">= 3.10", ">= 3.11")
        self.assertEqual((ROOT / "notebooks" / "00_setup.ipynb").read_text(encoding="utf-8"), expected)

    def test_notebooks_are_valid_and_have_no_saved_outputs(self):
        for path in (ROOT / "notebooks").glob("*.ipynb"):
            notebook = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(path=path.name):
                self.assertEqual(notebook["nbformat"], 4)
                self.assertNotIn("display_name", notebook["metadata"].get("kernelspec", {}))
                for cell in notebook["cells"]:
                    if cell["cell_type"] == "code":
                        self.assertEqual(cell["outputs"], [])
                        self.assertIsNone(cell["execution_count"])
                        ast.parse("".join(cell["source"]))

    def test_metadata_uses_exact_template_fields(self):
        template = json.loads((REPOSITORY / "demo-template" / "metadata.json").read_text())
        actual = json.loads((ROOT / "metadata.json").read_text())
        self.assertEqual(set(actual), set(template))
        self.assertEqual(actual["demo_name"], ROOT.name)

    def test_bicep_defines_platform_behavior_and_no_keys(self):
        bicep = (ROOT / "infra" / "main.bicep").read_text()
        for required in ("disableLocalAuth: true", "publicNetworkAccess: 'Enabled'",
                         "versionUpgradeOption: 'NoAutoUpgrade'", "@minLength(2)", "@maxLength(3)", "@batchSize(1)"):
            self.assertIn(required, bicep)
        self.assertEqual(bicep.count("@2026-09-01"), 3)
        self.assertNotIn("listKeys", bicep)
        self.assertNotIn("assert distinct", bicep)
        self.assertNotIn("param modelVersion string =", bicep)


if __name__ == "__main__":
    unittest.main()
