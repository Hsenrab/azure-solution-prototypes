"""Synthetic native-contract tests; fixtures are not live evaluation evidence."""

from dataclasses import replace
import asyncio
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import yaml

from app import assert_lab as lab
from test_assert_lab import metadata


FIXTURES = Path(__file__).parent / "fixtures"


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(lab.DEMO_ROOT / "data", self.root / "data")
        (self.root / "data" / "extra-tests.jsonl").write_text("")
        self.policy, self.settings = lab.load_evaluation(root=self.root)
        self.metadata = metadata()
        self.suite = lab.create_suite(self.settings, self.metadata, root=self.root)
        shutil.copyfile(FIXTURES / "taxonomy.json", self.suite / "taxonomy.json")
        cases = lab.read_cases(FIXTURES / "test_set.jsonl")
        self.generated = [
            {**case, "test_case_id": f"generated-{index}-{copy}"}
            for index, case in enumerate(cases)
            for copy in range(4 if case["type"] == "prompt" else 2)
        ]
        lab._write_cases(self.suite / "generated-test-set.jsonl", self.generated)
        lab.review_candidates(self.suite, reviewed=True)

    def approve(self):
        lab.merge_cases(self.suite, self.settings, root=self.root)
        return lab.approve_suite(self.suite, self.settings, self.metadata, reviewed=True, root=self.root)

    def test_strict_policy_and_settings(self):
        for extra in ("api_key", "system_prompt"):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                lab.Policy.from_dict({**lab.asdict(self.policy), extra: "not-a-key"})
        for key in ("prompt_count", "scenario_count", "max_turns"):
            for value in (0, -1, True, 1.5, "8"):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    lab.LabSettings.from_dict({**lab.asdict(self.settings), key: value})
        with self.assertRaises(ValueError):
            lab._data_path("..\\outside.yaml", self.root)
        with self.assertRaises(ValueError):
            lab.Policy.from_dict({**lab.asdict(self.policy), "id": "../escape"})
        with self.assertRaises(ValueError):
            lab.create_suite(replace(self.settings, judge_target="absent"), self.metadata, root=self.root)

    def test_native_configs_disable_paid_target_calls_during_generation(self):
        for taxonomy_only in (True, False):
            path = lab.generation_config(
                self.suite, self.settings, self.metadata, taxonomy_only=taxonomy_only, root=self.root
            )
            config = yaml.safe_load(path.read_text())
            pipeline = config["pipeline"]
            self.assertFalse(pipeline["inference"]["enabled"])
            self.assertFalse(pipeline["judge"]["enabled"])
            self.assertEqual(pipeline["systematize"]["enabled"], taxonomy_only)
            self.assertEqual(pipeline["test_set"].get("enabled", True), not taxonomy_only)
            self.assertNotIn("${", path.read_text())
            self.assertIn("azure/gpt5_series/assert-newer", path.read_text())

    def test_taxonomy_and_cases_reject_ambiguous_classification(self):
        taxonomy = json.loads((FIXTURES / "taxonomy.json").read_text())
        taxonomy["behavior_categories"][0]["permissible"] = "false"
        with self.assertRaises(ValueError):
            lab.validate_taxonomy(taxonomy)
        labels = lab.validate_taxonomy(lab._json(self.suite / "taxonomy.json"))
        with self.assertRaises(ValueError):
            lab.validate_cases([*self.generated, self.generated[0]], labels)
        for change in (
            {"dimensions": {"behavior": "invented"}}, {"permissible": True},
            {"seed": {"title": "test", "description": "test", "system_prompt": "override"}},
            {"seed": {"title": "test", "description": ""}},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                lab.validate_cases([{**self.generated[0], **change}], labels, coverage=False)
        with self.assertRaises(ValueError):
            lab.validate_cases(self.generated[:1], labels)

    def test_generated_config_is_consumed_by_native_stage_not_only_top_level_parser(self):
        from assert_ai.config import load_config, load_runtime_context
        from assert_ai.stages import STAGES, test_set

        path = lab.generation_config(self.suite, self.settings, self.metadata, taxonomy_only=False, root=self.root)
        raw = load_config(path)
        context = load_runtime_context(raw, path, stage_modules=STAGES)
        with patch.object(test_set, "run_test_set", new_callable=AsyncMock) as native:
            native.return_value = {"count": 12, "test_set_path": str(self.suite / "test_set.jsonl")}
            asyncio.run(test_set.run(context, raw["pipeline"]["test_set"]))
        native.assert_awaited_once()

    def test_generated_scenario_prompt_is_removed_only_at_explicit_review(self):
        generated = [{**row, "seed": {**row["seed"], "system_prompt": "Generated store-specific prompt"}}
                     if row["type"] == "scenario" else row for row in self.generated]
        lab._write_cases(self.suite / "generated-test-set.jsonl", generated)
        with self.assertRaises(ValueError):
            lab.review_candidates(self.suite)
        reviewed = lab.review_candidates(self.suite, reviewed=True)
        self.assertTrue(all("system_prompt" not in row["seed"] for row in reviewed))
        self.assertEqual(lab.read_cases(self.suite / "generated-test-set.jsonl"), generated)

    def test_generated_and_two_handwritten_cases_preserve_ids_and_counts(self):
        additions = [
            {**self.generated[0], "test_case_id": "manual-prohibited"},
            {**self.generated[4], "test_case_id": "manual-permitted"},
        ]
        lab._write_cases(self.root / "data" / "extra-tests.jsonl", additions)
        rows = lab.merge_cases(self.suite, self.settings, root=self.root)
        self.assertEqual(len(rows), 14)
        self.assertEqual(rows[:12], self.generated)
        self.assertEqual(lab.read_cases(self.suite / "generated-test-set.jsonl"), self.generated)
        identity_map = lab.native_id_map(rows)
        self.assertEqual(identity_map["manual-prohibited"], "test_case_000013")
        self.assertEqual(identity_map["manual-permitted"], "test_case_000014")
        self.assertEqual(rows[-1]["test_case_id"], "manual-permitted")

    def test_wrong_generated_budget_and_handwritten_prefix_are_rejected(self):
        lab._write_cases(self.suite / "reviewed-test-set.jsonl", self.generated[:-1])
        with self.assertRaises(ValueError):
            lab.merge_cases(self.suite, self.settings, root=self.root)
        lab._write_cases(self.suite / "reviewed-test-set.jsonl", self.generated)
        lab._write_cases(self.root / "data" / "extra-tests.jsonl", [{**self.generated[0], "test_case_id": "wrong-prefix"}])
        with self.assertRaises(ValueError):
            lab.merge_cases(self.suite, self.settings, root=self.root)

    def test_explicit_approval_and_immutable_inputs(self):
        lab.merge_cases(self.suite, self.settings, root=self.root)
        with self.assertRaises(ValueError):
            lab.approve_suite(self.suite, self.settings, self.metadata, root=self.root)
        self.approve()
        self.assertTrue(lab.verify_approval(self.suite, self.settings, self.metadata, root=self.root)["reviewed"])
        for operation in (
            lambda: lab.merge_cases(self.suite, self.settings, root=self.root),
            lambda: lab.approve_suite(self.suite, self.settings, self.metadata, reviewed=True, root=self.root),
            lambda: lab.generation_config(self.suite, self.settings, self.metadata, taxonomy_only=True, root=self.root),
        ):
            with self.assertRaises(ValueError):
                operation()
        with (self.suite / "test_set.jsonl").open("a") as stream:
            stream.write("\n")
        with self.assertRaises(ValueError):
            lab.verify_approval(self.suite, self.settings, self.metadata, root=self.root)

    def test_role_turn_policy_changes_invalidate_approval_but_generation_changes_do_not(self):
        self.approve()
        for changed in (
            replace(self.settings, tester_target="older"), replace(self.settings, judge_target="older"),
            replace(self.settings, max_turns=2),
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                lab.verify_approval(self.suite, changed, self.metadata, root=self.root)
        lab.verify_approval(
            self.suite, replace(self.settings, generation_target="older", prompt_count=10),
            self.metadata, root=self.root,
        )
        policy_path = self.root / "data" / self.settings.policy_path
        policy_path.write_text(policy_path.read_text() + "\n# content change without revision change\n")
        with self.assertRaises(ValueError):
            lab.verify_approval(self.suite, self.settings, self.metadata, root=self.root)
        new_suite = lab.create_suite(self.settings, self.metadata, root=self.root)
        self.assertNotEqual(new_suite, self.suite)
        self.assertTrue((self.suite / "approval.json").exists())

    def test_unapproved_or_changed_inputs_never_reach_target_calls(self):
        lab.write_connections(self.metadata, root=self.root)
        with patch.object(lab, "verify_live_deployments") as live, patch.object(lab, "run_native") as native:
            with self.assertRaises(FileNotFoundError):
                lab.evaluate_target(self.suite, "older", self.settings, root=self.root)
            live.assert_not_called()
            native.assert_not_called()

    def test_cli_uses_current_interpreter_and_visible_nonzero_failure(self):
        lab.write_connections(self.metadata, root=self.root)
        config = self.suite / "unused.yaml"
        with patch.object(lab.subprocess, "run") as process:
            lab.run_native(config, root=self.root)
        args, kwargs = process.call_args
        self.assertEqual(args[0][:4], [lab.sys.executable, "-m", "assert_ai.cli", "run"])
        self.assertEqual(args[0][-2:], ["--concurrency", "1"])
        self.assertTrue(kwargs["check"])
        self.assertEqual(kwargs["cwd"], self.root)
        self.assertEqual(kwargs["env"]["ASSERT_AZURE_USE_AAD"], "1")

    def test_target_only_replacement_reuses_approval_and_emits_only_native_inference_judge(self):
        self.approve()
        replacement = replace(
            self.metadata.deployments[0], model_name="gpt-5.1", model_version="synthetic-next-version",
            deployment_name="explicit-replacement",
        )
        changed_metadata = replace(self.metadata, deployments=(replacement, *self.metadata.deployments[1:]))
        lab.write_connections(changed_metadata, root=self.root)
        with patch.object(lab, "verify_live_deployments") as live, patch.object(lab, "run_native") as native:
            run = lab.evaluate_target(self.suite, "older", self.settings, root=self.root)
        live.assert_called_once()
        cfg = yaml.safe_load(native.call_args.args[0].read_text())
        self.assertFalse(cfg["pipeline"]["systematize"]["enabled"])
        self.assertFalse(cfg["pipeline"]["test_set"]["enabled"])
        self.assertEqual(cfg["pipeline"]["inference"]["target"]["model"]["name"], "azure/gpt5_series/explicit-replacement")
        self.assertEqual(cfg["pipeline"]["inference"]["target"]["system_prompt"], self.policy.render())
        self.assertEqual(cfg["pipeline"]["inference"]["max_turns"], 3)
        self.assertEqual(cfg["pipeline"]["judge"]["model"]["name"], "azure/gpt5_series/assert-newer")
        self.assertEqual(cfg["pipeline"]["inference"]["test_set_path"], str((self.suite / "test_set.jsonl").resolve()))
        self.assertEqual(lab._json(run / "provenance.json")["target"]["modelVersion"], "synthetic-next-version")

    def test_second_policy_configuration_creates_distinct_suite_and_retains_first(self):
        self.approve()
        original_approval = (self.suite / "approval.json").read_bytes()
        second = {**lab.asdict(self.policy), "id": "appointment-support", "revision": "1",
                  "context": "Synthetic appointment explanations; no tools can book an appointment.",
                  "prohibited": ["Claim that an appointment has been booked."],
                  "permitted": ["Explain how to contact a human scheduler."]}
        (self.root / "data" / "policies" / "second.yaml").write_text(yaml.safe_dump(second))
        changed = replace(self.settings, policy_path="policies/second.yaml")
        new_suite = lab.create_suite(changed, self.metadata, root=self.root)
        self.assertNotEqual(new_suite, self.suite)
        self.assertEqual(lab._suite_policy(new_suite).id, "appointment-support")
        self.assertEqual((self.suite / "approval.json").read_bytes(), original_approval)
        self.assertFalse((new_suite / "approval.json").exists())

    def test_compact_ids_keep_native_viewer_tempfile_below_windows_max_path(self):
        from assert_ai.viewer_read_model import build_run_viewer_artifacts

        generated = lab.artifact_path("suites")
        generated.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="path-check-", dir=generated) as directory:
            run = Path(directory) / "intermediate-123456789abc"
            run.mkdir()
            lab.validate_native_paths(run)
            shutil.copyfile(FIXTURES / "inference_set.jsonl", run / "inference_set.jsonl")
            build_run_viewer_artifacts(run)
            native_index = run / ".viewer" / "viewer_transcript_index.json"
            self.assertTrue(native_index.exists())
            with tempfile.NamedTemporaryFile(
                prefix=".viewer_transcript_index.json.", suffix=".tmp", dir=run / ".viewer"
            ) as stream:
                self.assertLess(len(stream.name), 260)
        if lab.os.name == "nt":
            with self.assertRaises(ValueError):
                lab.validate_native_paths(lab.artifact_path("suites", "x" * 100, "long-run"))
