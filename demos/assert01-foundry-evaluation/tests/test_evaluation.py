"""Synthetic native-contract tests; fixtures are not live evaluation evidence."""

from contextlib import chdir, redirect_stdout
from dataclasses import replace
import asyncio
import io
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
        self.policy, self.settings = lab.load_evaluation(root=self.root)
        self.metadata = metadata()
        self.suite = lab.create_suite(self.settings, self.metadata, root=self.root)
        (self.suite / self.settings.extra_tests_path).write_text("")
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
        for taxonomy_only, starters_only in ((True, False), (False, False), (False, True)):
            path = lab.generation_config(
                self.suite, self.settings, self.metadata, taxonomy_only=taxonomy_only,
                starters_only=starters_only, root=self.root,
            )
            config = yaml.safe_load(path.read_text())
            pipeline = config["pipeline"]
            self.assertFalse(pipeline["inference"]["enabled"])
            self.assertFalse(pipeline["judge"]["enabled"])
            self.assertEqual(pipeline["systematize"]["enabled"], taxonomy_only)
            self.assertEqual(pipeline["test_set"].get("enabled", True), not taxonomy_only)
            self.assertNotIn("${", path.read_text())
            self.assertIn("azure/gpt5_series/assert-newer", path.read_text())
            if starters_only:
                self.assertEqual(pipeline["test_set"]["prompt"]["sample_size"], 2)
                self.assertNotIn("scenario", pipeline["test_set"])
                self.assertEqual(Path(pipeline["test_set"]["save_path"]).name, "generated-extra-tests.jsonl")

    def test_review_checkpoints_link_complete_generated_files(self):
        import pandas as pd
        from IPython.display import FileLink

        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        self.assertNotIn("generated-test-links", {cell["id"] for cell in notebook["cells"]})
        additions = [
            {**self.generated[0], "test_case_id": "starter-prohibited"},
            {**self.generated[4], "test_case_id": "starter-permitted"},
        ]
        lab._write_cases(self.suite / self.settings.extra_tests_path, additions)
        displayed = []
        namespace = {
            "suite": self.suite, "settings": self.settings, "metadata": self.metadata,
            "demo_root": self.root.resolve(), "Path": Path, "json": json, "pd": pd,
            "FileLink": FileLink, "display": displayed.append,
            "TAXONOMY_REVIEWED": True, "GENERATED_CASES_REVIEWED": True,
            "read_cases": lab.read_cases, "case_category": lab.case_category,
            "review_candidates": lab.review_candidates, "merge_cases": lab.merge_cases,
            "approve_suite": lab.approve_suite,
            "labels": lab.validate_taxonomy(lab._json(self.suite / "taxonomy.json")),
        }
        (self.root / "notebooks").mkdir()
        with (
            chdir(self.root / "notebooks"), redirect_stdout(io.StringIO()),
            patch.object(lab, "generate_candidates") as generate,
            patch.object(lab, "generate_starter_tests") as starters,
            patch.object(lab, "run_native", side_effect=AssertionError("Review made a paid call")) as native,
        ):
            namespace["generate_candidates"] = generate
            namespace["generate_starter_tests"] = starters
            stages = (
                (("generate_candidates(suite,", "generate_starter_tests(suite,"), None),
                (("reviewed_cases = review_candidates(",), "reviewed-test-links"),
            )
            for markers, link_cell_id in stages:
                for marker in markers:
                    source = next("".join(cell["source"]) for cell in notebook["cells"]
                                  if cell["cell_type"] == "code" and marker in "".join(cell["source"]))
                    start = len(displayed)
                    exec(compile(source, "review-file-links", "exec"), namespace)
                    if marker in ("generate_candidates(suite,", "generate_starter_tests(suite,"):
                        preview, link = displayed[start:]
                        self.assertIsInstance(preview, pd.DataFrame)
                        self.assertIsInstance(link, FileLink)
                        expected = self.generated if marker == "generate_candidates(suite," else additions
                        self.assertEqual(preview["id"].tolist(), [row["test_case_id"] for row in expected])
                        filename = "generated-test-set.jsonl" if marker == "generate_candidates(suite," else self.settings.extra_tests_path
                        self.assertEqual(Path(link.path).name, filename)
                if link_cell_id is not None:
                    links_source = next("".join(cell["source"]) for cell in notebook["cells"]
                                        if cell["id"] == link_cell_id)
                    exec(compile(links_source, "read-only-file-links", "exec"), namespace)
            links = [item for item in displayed if isinstance(item, FileLink)]
            self.assertEqual(len(links), 4)
            self.assertEqual({Path(link.path).name for link in links}, {
                "generated-test-set.jsonl", "reviewed-test-set.jsonl", "test_set.jsonl",
                self.settings.extra_tests_path,
            })
            for link in links:
                self.assertNotIn("\\", link.path)
                self.assertEqual(Path(link.path).resolve().parent, self.suite.resolve())
                self.assertTrue(Path(link.path).is_file())
                self.assertIn("<a href=", link._repr_html_())
            before = {path: path.read_bytes() for path in self.suite.rglob("*") if path.is_file()}
            for _, link_cell_id in stages:
                if link_cell_id is None:
                    continue
                links_source = next("".join(cell["source"]) for cell in notebook["cells"]
                                    if cell["id"] == link_cell_id)
                exec(compile(links_source, "reopen-approved-file-links", "exec"), namespace)
            self.assertEqual(before, {path: path.read_bytes() for path in before})
            generate.assert_called_once()
            starters.assert_called_once()
            native.assert_not_called()
            self.assertTrue((self.suite / "review.json").is_file())
            self.assertFalse((self.suite / "approval.json").exists())
            self.assertFalse(any("APPROVE_REVIEWED_SUITE" in "".join(cell["source"])
                                 for cell in notebook["cells"]))

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

        for starters_only in (False, True):
            with self.subTest(starters_only=starters_only):
                path = lab.generation_config(
                    self.suite, self.settings, self.metadata, taxonomy_only=False,
                    starters_only=starters_only, root=self.root,
                )
                raw = load_config(path)
                context = load_runtime_context(raw, path, stage_modules=STAGES)
                with patch.object(test_set, "run_test_set", new_callable=AsyncMock) as native:
                    native.return_value = {"test_set_path": str(self.suite / "test_set.jsonl")}
                    asyncio.run(test_set.run(context, raw["pipeline"]["test_set"]))
                native.assert_awaited_once()
                self.assertEqual(native.call_args.kwargs["context"], self.policy.context)
                self.assertEqual(native.call_args.kwargs["prompt"]["sample_size"], 2 if starters_only else 8)
                if starters_only:
                    self.assertIsNone(native.call_args.kwargs["scenario"])

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
        lab._write_cases(self.suite / self.settings.extra_tests_path, additions)
        rows = lab.merge_cases(self.suite, self.settings, root=self.root)
        self.assertEqual(len(rows), 14)
        self.assertEqual(rows[:12], self.generated)
        self.assertEqual(lab.read_cases(self.suite / "generated-test-set.jsonl"), self.generated)
        identity_map = lab.native_id_map(rows)
        self.assertEqual(identity_map["manual-prohibited"], "test_case_000013")
        self.assertEqual(identity_map["manual-permitted"], "test_case_000014")
        self.assertEqual(rows[-1]["test_case_id"], "manual-permitted")

    def test_native_starters_follow_each_suites_policy_and_taxonomy_and_preserve_edits(self):
        self.approve()
        original = {path: path.read_bytes() for path in self.suite.rglob("*") if path.is_file()}
        legacy = self.root / "data" / "extra-tests.jsonl"
        legacy_before = legacy.read_bytes()
        for policy_id in ("customer-support", "appointment-support"):
            with self.subTest(policy=policy_id):
                settings = self.settings
                if policy_id == "appointment-support":
                    policy = {
                        "id": policy_id, "revision": "1",
                        "context": "Explain appointments; no tools can make bookings.",
                        "prohibited": ["Claim an appointment has been booked."],
                        "permitted": ["Explain how to contact a human scheduler."],
                    }
                    (self.root / "data" / "policies" / "appointment.yaml").write_text(yaml.safe_dump(policy))
                    settings = replace(settings, policy_path="policies/appointment.yaml")
                suite = lab.create_suite(settings, self.metadata, root=self.root)
                taxonomy = lab._json(FIXTURES / "taxonomy.json")
                taxonomy["behavior"]["name"] = policy_id
                for category in taxonomy["behavior_categories"]:
                    category["name"] = f"{policy_id}: {'help' if category['permissible'] else 'unsupported action'}"
                lab._write_json(suite / "taxonomy.json", taxonomy)
                names = {category["permissible"]: category["name"] for category in taxonomy["behavior_categories"]}
                fixture_labels = lab.validate_taxonomy(lab._json(FIXTURES / "taxonomy.json"))
                native_outputs = []

                def generate(config, *, root):
                    raw = yaml.safe_load(config.read_text())
                    self.assertIn(lab._suite_policy(suite).render(), raw["behavior"]["description"])
                    self.assertEqual(raw["context"], lab._suite_policy(suite).context)
                    starter_pass = "scenario" not in raw["pipeline"]["test_set"]
                    source = lab.read_cases(FIXTURES / "test_set.jsonl")[:2] if starter_pass else self.generated
                    rows = [{
                        **row, "behavior": policy_id,
                        "dimensions": {"behavior": names[fixture_labels[lab.case_category(row)]]},
                        "seed": {
                            "title": f"{policy_id} {'editable starter' if starter_pass else 'main'} {index}",
                            "description": f"Synthetic native output for {policy_id}, pass {starter_pass}, case {index}",
                        },
                    } for index, row in enumerate(source)]
                    native = suite / "artifacts" / "test_set" / f"v{len(native_outputs) + 1:04d}" / "test_set.jsonl"
                    native.parent.mkdir(parents=True)
                    lab._write_cases(native, rows)
                    lab._write_json(suite / "latest.json", {
                        "artifacts": {"test_set": {"path": str(native.relative_to(suite))}},
                    })
                    native_outputs.append(rows)

                with patch.object(lab, "run_native", side_effect=generate) as native:
                    lab.generate_candidates(suite, settings, self.metadata, root=self.root)
                    lab.generate_starter_tests(suite, settings, self.metadata, root=self.root)
                    extra_path = suite / settings.extra_tests_path
                    starters = lab.read_cases(extra_path)
                    self.assertEqual({row["test_case_id"] for row in starters},
                                     {"starter-permitted", "starter-prohibited"})
                    self.assertEqual({lab.case_category(row) for row in starters}, set(names.values()))
                    self.assertTrue(all(row["behavior"] == policy_id for row in starters))
                    self.assertEqual(lab.read_cases(suite / "generated-extra-tests.jsonl"), native_outputs[1])
                    self.assertEqual([row["seed"] for row in starters],
                                     [row["seed"] for row in native_outputs[1]])
                    self.assertTrue(all(row["seed"] not in [main["seed"] for main in native_outputs[0]]
                                        for row in starters))
                    starters[0]["seed"]["description"] = "Learner's edited request; do not overwrite."
                    lab._write_cases(extra_path, starters)
                    edited = extra_path.read_bytes()
                    lab.review_candidates(suite, reviewed=True)
                    for _ in range(2):
                        merged = lab.merge_cases(suite, settings, root=self.root)
                        self.assertEqual(len(merged), 14)
                        self.assertEqual(merged[-2:], starters)
                        self.assertEqual(extra_path.read_bytes(), edited)
                    with redirect_stdout(io.StringIO()) as output:
                        lab.generate_starter_tests(suite, settings, self.metadata, root=self.root)
                    self.assertIn("Using existing editable tests; no generation or paid model calls", output.getvalue())
                    self.assertEqual(extra_path.read_bytes(), edited)
                    self.assertEqual(native.call_count, 2)
                    lab.approve_suite(suite, settings, self.metadata, reviewed=True, root=self.root)
                    with self.assertRaisesRegex(ValueError, "frozen"):
                        lab.generate_starter_tests(suite, settings, self.metadata, root=self.root)
                    self.assertEqual(native.call_count, 2)
        self.assertEqual(legacy.read_bytes(), legacy_before)
        self.assertEqual(original, {path: path.read_bytes() for path in original})

    def test_incomplete_or_misclassified_starters_are_not_made_editable(self):
        destination = self.suite / self.settings.extra_tests_path
        destination.unlink()
        valid = lab.read_cases(FIXTURES / "test_set.jsonl")[:2]
        native_path = self.suite / "native-starters.jsonl"
        lab._write_json(self.suite / "latest.json", {
            "artifacts": {"test_set": {"path": native_path.name}},
        })
        invalid = (
            valid[:1],
            [valid[0], {**valid[0], "test_case_id": "different-id"}],
            [{**valid[0], "dimensions": {"behavior": "old taxonomy category"}}, valid[1]],
            [{**valid[0], "type": "scenario"}, valid[1]],
        )
        for rows in invalid:
            with self.subTest(rows=rows), patch.object(lab, "run_native") as native:
                lab._write_cases(native_path, rows)
                with self.assertRaises(ValueError):
                    lab.generate_starter_tests(self.suite, self.settings, self.metadata, root=self.root)
                native.assert_called_once()
                self.assertFalse(destination.exists())

    def test_existing_editable_tests_rerun_notebook_preview_without_paid_calls(self):
        import pandas as pd
        from IPython.display import FileLink

        additions = [
            {**self.generated[0], "test_case_id": "starter-prohibited"},
            {**self.generated[4], "test_case_id": "manual-added", "seed": {
                "title": "Learner addition", "description": "Explain the refund review process.",
            }},
        ]
        lab._write_cases(self.suite / self.settings.extra_tests_path, additions)
        before = {path: path.read_bytes() for path in self.suite.rglob("*") if path.is_file()}
        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        source = next("".join(cell["source"]) for cell in notebook["cells"]
                      if cell["id"] == "generate-editable-starters")
        displayed = []
        namespace = {
            "suite": self.suite, "settings": self.settings, "metadata": self.metadata,
            "demo_root": self.root.resolve(), "Path": Path, "pd": pd,
            "FileLink": FileLink, "display": displayed.append,
            "TAXONOMY_REVIEWED": True, "generate_starter_tests": lab.generate_starter_tests,
            "read_cases": lab.read_cases, "case_category": lab.case_category,
            "labels": lab.validate_taxonomy(lab._json(self.suite / "taxonomy.json")),
        }
        (self.root / "notebooks").mkdir()
        with (
            chdir(self.root / "notebooks"), redirect_stdout(io.StringIO()) as output,
            patch.object(lab, "run_native", side_effect=AssertionError("Rerun made a paid call")) as native,
        ):
            for _ in range(2):
                exec(compile(source, "rerun-editable-preview", "exec"), namespace)
            self.assertEqual(len(displayed), 4)
            for preview, link in (displayed[:2], displayed[2:]):
                self.assertEqual(preview["id"].tolist(), [row["test_case_id"] for row in additions])
                self.assertIsInstance(link, FileLink)
                self.assertIn("<a href=", link._repr_html_())
            self.assertEqual(output.getvalue().count("Using existing editable tests"), 2)
            native.assert_not_called()
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        additions[0]["dimensions"] = {"behavior": "outdated category"}
        lab._write_cases(self.suite / self.settings.extra_tests_path, additions)
        invalid = (self.suite / self.settings.extra_tests_path).read_bytes()
        with patch.object(lab, "run_native") as native:
            with self.assertRaisesRegex(ValueError, "Unknown taxonomy category"):
                lab.generate_starter_tests(self.suite, self.settings, self.metadata, root=self.root)
            native.assert_not_called()
        self.assertEqual((self.suite / self.settings.extra_tests_path).read_bytes(), invalid)

    def test_editable_filename_cannot_escape_or_replace_suite_artifacts(self):
        for filename in ("..\\outside.jsonl", "test_set.jsonl", "generated-test-set.jsonl", "approval.json"):
            with self.subTest(filename=filename), patch.object(lab, "run_native") as native:
                with self.assertRaisesRegex(ValueError, "separate JSONL file"):
                    lab.generate_starter_tests(
                        self.suite, replace(self.settings, extra_tests_path=filename),
                        self.metadata, root=self.root,
                    )
                native.assert_not_called()

    def test_wrong_generated_budget_and_handwritten_prefix_are_rejected(self):
        lab._write_cases(self.suite / "reviewed-test-set.jsonl", self.generated[:-1])
        with self.assertRaises(ValueError):
            lab.merge_cases(self.suite, self.settings, root=self.root)
        lab._write_cases(self.suite / "reviewed-test-set.jsonl", self.generated)
        lab._write_cases(self.suite / self.settings.extra_tests_path,
                         [{**self.generated[0], "test_case_id": "wrong-prefix"}])
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
            replace(self.settings, tester_target="older_model"), replace(self.settings, judge_target="older_model"),
            replace(self.settings, max_turns=2),
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                lab.verify_approval(self.suite, changed, self.metadata, root=self.root)
        lab.verify_approval(
            self.suite, replace(self.settings, generation_target="older_model", prompt_count=10),
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
                lab.evaluate_target(self.suite, "older_model", self.settings, root=self.root)
            live.assert_not_called()
            native.assert_not_called()

    def test_evaluation_cell_freezes_reviewed_inputs_once_and_reuses_them(self):
        from IPython.display import FileLink

        lab.write_connections(self.metadata, root=self.root)
        lab.merge_cases(self.suite, self.settings, root=self.root)
        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        source = next("".join(cell["source"]) for cell in notebook["cells"] if cell["id"] == "14")
        selection = lab.artifact_path("active-suite.json", root=self.root)
        lab._write_json(selection, {"suite": str(self.suite)})
        links = []
        namespace = {
            "Path": Path, "json": json, "selection_path": selection, "settings": self.settings,
            "demo_root": self.root.resolve(), "evaluate_target": lab.evaluate_target,
            "FileLink": FileLink, "display": links.append,
            "runs_path": lab.artifact_path("active-runs.json", root=self.root),
        }

        def verify_frozen_before_native(config, *, root):
            self.assertTrue(lab.verify_approval(self.suite, self.settings, self.metadata, root=root)["reviewed"])
            run = Path(yaml.safe_load(config.read_text())["pipeline"]["inference"]["save_dir"])
            for name in ("inference_set.jsonl", "scores.jsonl", "metrics.json"):
                (run / name).write_text("{}\n")

        (self.root / "notebooks").mkdir()
        with (
            chdir(self.root / "notebooks"),
            patch.object(lab, "verify_live_deployments"),
            patch.object(lab, "run_native", side_effect=verify_frozen_before_native) as native,
            redirect_stdout(io.StringIO()),
        ):
            exec(compile(source, "start-evaluation", "exec"), namespace)
            self.assertEqual({Path(link.path).name for link in links},
                             {"inference_set.jsonl", "scores.jsonl", "metrics.json"})
            self.assertEqual(len(links), 3)
            for link in links:
                self.assertIsInstance(link, FileLink)
                self.assertNotIn("\\", link.path)
                self.assertTrue(Path(link.path).is_file())
                self.assertEqual(Path(link.path).resolve().parent, namespace["first_run"].resolve())
                self.assertIn("<a href=", link._repr_html_())
            frozen = (self.suite / "approval.json").read_bytes()
            lab.evaluate_target(self.suite, "newer_model", self.settings, root=self.root)
            self.assertEqual((self.suite / "approval.json").read_bytes(), frozen)
            self.assertEqual(native.call_count, 2)
            with (self.suite / "test_set.jsonl").open("a") as stream:
                stream.write("\n")
            with self.assertRaisesRegex(ValueError, "no longer matches"):
                lab.evaluate_target(self.suite, "older_model", self.settings, root=self.root)
            self.assertEqual(native.call_count, 2)
            self.assertEqual((self.suite / "approval.json").read_bytes(), frozen)

    def test_changed_review_inputs_block_automatic_freezing_before_calls(self):
        lab.write_connections(self.metadata, root=self.root)
        lab.merge_cases(self.suite, self.settings, root=self.root)
        files = lab._review_hashes(self.suite, self.settings)
        for name in files:
            path = self.suite / name
            before = path.read_bytes()
            with self.subTest(name=name), patch.object(lab, "run_native") as native, patch.object(
                lab, "verify_live_deployments"
            ) as live:
                path.write_bytes(before + b"\n")
                with self.assertRaisesRegex(ValueError, "Inputs changed since review"):
                    lab.evaluate_target(self.suite, "older_model", self.settings, root=self.root)
                self.assertFalse((self.suite / "approval.json").exists())
                native.assert_not_called()
                live.assert_not_called()
                path.write_bytes(before)

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
            run = lab.evaluate_target(self.suite, "older_model", self.settings, root=self.root)
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
        self.assertEqual(lab._json(run / "provenance.json")["target"]["alias"], "older_model")
        self.assertTrue(run.name.startswith("older-"))

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

    def test_collections_group_suites_by_policy_revision_and_keep_native_layout(self):
        collection = lab.policy_collection(self.policy.id, self.policy.revision, root=self.root)
        self.assertEqual(self.suite.parent, collection)
        self.assertEqual(lab._json(collection / "collection.json"), {
            "policy_id": self.policy.id, "revision": self.policy.revision,
        })
        before = {path: path.read_bytes() for path in self.suite.rglob("*") if path.is_file()}
        second = lab.create_suite(self.settings, self.metadata, root=self.root)
        self.assertEqual(second.parent, collection)
        self.assertNotEqual(second, self.suite)
        self.assertNotEqual(collection, lab.policy_collection(self.policy.id, "2", root=self.root))
        self.assertNotEqual(collection, lab.policy_collection("another-policy", "1", root=self.root))
        config = lab.generation_config(self.suite, self.settings, self.metadata, taxonomy_only=False, root=self.root)
        self.assertEqual(Path(yaml.safe_load(config.read_text())["results_dir"]), collection)
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        from assert_ai.viewer_read_model import build_run_viewer_artifacts

        generated = lab.artifact_path("collections", root=lab.DEMO_ROOT)
        generated.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="c-", dir=generated) as directory:
            run = Path(directory) / self.suite.name / "intermediate-123456789abc"
            run.mkdir(parents=True)
            lab.validate_native_paths(run)
            shutil.copyfile(FIXTURES / "inference_set.jsonl", run / "inference_set.jsonl")
            build_run_viewer_artifacts(run)
            self.assertTrue((run / ".viewer" / "viewer_transcript_index.json").exists())
