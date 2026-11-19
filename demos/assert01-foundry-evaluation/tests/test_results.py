from dataclasses import replace
from contextlib import chdir, redirect_stdout
import ast
import io
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

from app import assert_lab as lab
from test_assert_lab import metadata


FIXTURES = Path(__file__).parent / "fixtures"


class ResultTests(unittest.TestCase):
    def test_notebook_file_navigation_links_work_under_spaced_windows_paths(self):
        from IPython.display import FileLink

        root = (self.root / "OneDrive - Microsoft" / "demo").resolve()
        notebooks = root / "notebooks"
        notebooks.mkdir(parents=True)
        suite = root / "outputs" / "suite"
        run = suite / "older-run"
        targets = {
            "preflight_path": root / "outputs" / "preflight.json",
            "env_path": root / "env" / ".env",
            "metadata_path": root / "outputs" / "deployment.json",
            "smoke_path": root / "outputs" / "connections.json",
            "taxonomy_config": root / "outputs" / "configs" / "taxonomy.yaml",
        }
        files = [
            *targets.values(), root / "data" / "policies" / "example.yaml", suite / "approval.json",
            *(run / name for name in ("inference_set.jsonl", "scores.jsonl", "metrics.json")),
        ]
        for path in files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n")
        before = {path: path.read_bytes() for path in files}
        checkpoints = (
            ("01_deploy_infra.ipynb", "8", {"preflight.json"}),
            ("01_deploy_infra.ipynb", "17", {".env", "deployment.json"}),
            ("02_configure.ipynb", "4", {"connections.json"}),
            ("03_assert_flow.ipynb", "load-policy", {"example.yaml"}),
            ("03_assert_flow.ipynb", "4", {"taxonomy.yaml"}),
            ("03_assert_flow.ipynb", "20", {"approval.json"}),
            ("03_assert_flow.ipynb", "23", {"inference_set.jsonl", "scores.jsonl", "metrics.json"}),
        )
        for name, cell_id, expected in checkpoints:
            notebook = json.loads((lab.DEMO_ROOT / "notebooks" / name).read_text(encoding="utf-8"))
            source = next("".join(cell["source"]) for cell in notebook["cells"] if cell["id"] == cell_id)
            body = [statement for statement in ast.parse(source).body
                    if "FileLink(" in ast.unparse(statement)]
            self.assertTrue(body, (name, cell_id))
            links = []
            namespace = {
                **targets, "demo_root": root, "Path": Path, "FileLink": FileLink, "display": links.append,
                "suite": suite, "settings": SimpleNamespace(policy_path="policies/example.yaml"),
                "comparison_runs": [SimpleNamespace(path=run, provenance={"run_id": "older-run"})],
                "failure_examples": lambda result: [],
            }
            with self.subTest(notebook=name, cell=cell_id), chdir(notebooks), redirect_stdout(io.StringIO()):
                exec(compile(ast.Module(body=body, type_ignores=[]), "file-navigation-links", "exec"), namespace)
                self.assertEqual({Path(link.path).name for link in links}, expected)
                for link in links:
                    self.assertIsInstance(link, FileLink)
                    self.assertNotIn("\\", link.path)
                    self.assertTrue(Path(link.path).is_file())
                    self.assertIn(Path(link.path).resolve(), files)
                    self.assertIn("<a href=", link._repr_html_())
        self.assertEqual(before, {path: path.read_bytes() for path in files})

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(lab.DEMO_ROOT / "data", self.root / "data")
        self.policy, settings = lab.load_evaluation(root=self.root)
        self.settings = replace(settings, prompt_count=2, scenario_count=2)
        self.metadata = metadata()
        self.suite = lab.create_suite(self.settings, self.metadata, root=self.root)
        (self.suite / self.settings.extra_tests_path).write_text("")
        shutil.copyfile(FIXTURES / "taxonomy.json", self.suite / "taxonomy.json")
        shutil.copyfile(FIXTURES / "test_set.jsonl", self.suite / "generated-test-set.jsonl")
        lab.review_candidates(self.suite, reviewed=True)
        lab.merge_cases(self.suite, self.settings, root=self.root)
        lab.approve_suite(self.suite, self.settings, self.metadata, reviewed=True, root=self.root)
        self.run = self.suite / "older-synthetic"
        self.run.mkdir()
        for name in ("inference_set.jsonl", "scores.jsonl"):
            shutil.copyfile(FIXTURES / name, self.run / name)
        config = {"fixture": "Synthetic native-shaped run, not live evidence"}
        (self.run / "config.yaml").write_text(yaml.safe_dump(config))
        lab._write_json(self.run / "manifest.json", {
            "status": "completed", "stages": {"inference": "completed", "judge": "completed"},
        })
        lab._write_json(self.run / "metrics.json", {"fixture": True})
        lab._write_json(self.run / "provenance.json", {
            "run_id": self.run.name, "target": self.metadata.deployments[0].to_dict(),
            "approval": lab._json(self.suite / "approval.json"),
            "approval_hash": lab._file_hash(self.suite / "approval.json"),
            "input_config_hash": lab._file_hash(self.run / "config.yaml"),
        })

    def change_score(self, index, **changes):
        rows = lab.read_cases(self.run / "scores.jsonl")
        rows[index] = {**rows[index], **changes}
        lab._write_cases(self.run / "scores.jsonl", rows)

    def test_native_full_transcript_early_failure_counts_once(self):
        saved = lab.load_run(self.run)
        self.assertTrue(saved.complete)
        prompt, conversation = lab.summarize_run(saved)
        self.assertEqual(prompt["policy_violation_rate"], 0)
        self.assertEqual(prompt["overrefusal_rate"], 1)
        self.assertEqual(conversation["policy_violation_numerator"], 1)
        self.assertEqual(conversation["policy_violation_denominator"], 1)
        self.assertEqual(conversation["policy_violation_rate"], 1)
        self.assertEqual(conversation["overrefusal_rate"], 0)
        examples = lab.failure_examples(saved)
        self.assertEqual(len(examples), 2)
        scenario = examples[1]
        self.assertEqual(scenario["test_case_id"], "fixture-s1")
        self.assertEqual(scenario["native_test_case_id"], "test_case_000003")
        self.assertEqual(len(scenario["citations"]), 2)
        self.assertEqual(len(scenario["messages"]), 6)
        self.assertIn("cannot issue", scenario["messages"][-1]["content"])

    def test_error_statuses_never_become_clean_success(self):
        for status in ("judge_failed", "scoring_skipped", "filter_skipped"):
            with self.subTest(status=status):
                self.change_score(0, judge_status=status, verdict={}, judge_error="Synthetic error")
                saved = lab.load_run(self.run)
                self.assertFalse(saved.complete)
                prompt = lab.summarize_run(saved)[0]
                self.assertEqual(prompt[status], 1)
                self.assertEqual(prompt["policy_violation_denominator"], 0)
                self.assertIsNone(prompt["policy_violation_rate"])

    def test_semantic_na_is_separate_from_failure(self):
        self.change_score(0, verdict={
            "dimensions": {"policy_violation": None, "overrefusal": False},
            "dimension_applicability": {"policy_violation": False},
            "dimension_justifications": {"policy_violation": "Synthetic N/A"},
        })
        saved = lab.load_run(self.run)
        self.assertTrue(saved.complete)
        prompt = lab.summarize_run(saved)[0]
        self.assertEqual(prompt["policy_violation_not_applicable"], 1)
        self.assertIsNone(prompt["policy_violation_rate"])

    def test_missing_rows_accounted_independently(self):
        lab._write_cases(self.run / "inference_set.jsonl", lab.read_cases(self.run / "inference_set.jsonl")[1:])
        lab._write_cases(self.run / "scores.jsonl", lab.read_cases(self.run / "scores.jsonl")[2:])
        saved = lab.load_run(self.run)
        self.assertFalse(saved.complete)
        prompt = lab.summarize_run(saved)[0]
        self.assertEqual(prompt["missing_inference"], 1)
        self.assertEqual(prompt["missing_score"], 2)
        self.assertEqual(prompt["attempted"], 1)
        self.assertIsNone(prompt["overrefusal_rate"])

    def test_native_errors_and_exchange_limit(self):
        rows = lab.read_cases(self.run / "inference_set.jsonl")
        rows[2] = {**rows[2], "stop_reason": "target_error"}
        lab._write_cases(self.run / "inference_set.jsonl", rows)
        self.assertFalse(lab.load_run(self.run).complete)
        self.assertEqual(lab.summarize_run(lab.load_run(self.run))[1]["inference_failed"], 1)
        rows[2] = {**rows[2], "stop_reason": "max_turns", "events": [*rows[2]["events"], *rows[2]["events"][-2:]]}
        lab._write_cases(self.run / "inference_set.jsonl", rows)
        with self.assertRaises(ValueError):
            lab.load_run(self.run)

    def test_invalid_native_contract_unknown_duplicate_ids_and_modified_inputs(self):
        scores = lab.read_cases(self.run / "scores.jsonl")
        for invalid in (
            [*scores, scores[0]], [{**scores[0], "test_case_id": "unknown"}, *scores[1:]],
            [{**scores[0], "judge_status": "success"}, *scores[1:]],
            [{**scores[0], "verdict": {"dimensions": {"policy_violation": "false"}}}, *scores[1:]],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                lab._write_cases(self.run / "scores.jsonl", invalid)
                lab.load_run(self.run)
        lab._write_cases(self.run / "scores.jsonl", scores)
        (self.run / "config.yaml").write_text("fixture: changed")
        with self.assertRaises(ValueError):
            lab.load_run(self.run)

    def test_no_invented_failure_examples(self):
        rows = lab.read_cases(self.run / "scores.jsonl")
        for row in rows:
            row["verdict"]["dimensions"] = {"policy_violation": False, "overrefusal": False}
        lab._write_cases(self.run / "scores.jsonl", rows)
        self.assertEqual(lab.failure_examples(lab.load_run(self.run)), [])

    def test_comparison_provenance_allows_different_adaptive_transcripts(self):
        first = lab.load_run(self.run)
        other_provenance = {
            **first.provenance, "run_id": "newer-synthetic", "target": self.metadata.deployments[2].to_dict(),
        }
        second = replace(first, provenance=other_provenance, cases=[
            replace(result, messages=[{**message, "content": "Different runtime response"}
                                      for message in result.messages])
            for result in first.cases
        ])
        rows = lab.compare_runs([first, second])
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["comparison_status"] == "equivalent completed comparison" for row in rows))
        self.assertFalse(any(any(word in key for word in ("baseline", "regression", "threshold")) for row in rows for key in row))
        for changed, label in (
            (replace(second, complete=False), "incomplete comparison"),
            (replace(second, provenance={**other_provenance, "approval_hash": "different"}), "non-equivalent"),
        ):
            self.assertTrue(all(label in row["comparison_status"] for row in lab.compare_runs([first, changed])))

    def test_notebook_saved_result_cells_execute_without_paid_calls(self):
        import pandas as pd
        from IPython.display import FileLink

        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        pointer = self.root / "active-runs.json"
        lab._write_json(pointer, {"suite": str(self.suite), "runs": [str(self.run)]})
        displayed = []
        namespace = {
            "json": json, "Path": Path, "pd": pd, "display": displayed.append, "FileLink": FileLink,
            "demo_root": self.root.resolve(),
            "runs_path": pointer, "load_run": lab.load_run, "summarize_run": lab.summarize_run,
            "failure_examples": lab.failure_examples,
        }
        sources = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
        (self.root / "notebooks").mkdir()
        with chdir(self.root / "notebooks"), redirect_stdout(io.StringIO()):
            for source in sources:
                if "saved = load_run(" in source or "examples = failure_examples(saved)" in source:
                    exec(compile(source, "saved-result-notebook", "exec"), namespace)
            links = [item for item in displayed if isinstance(item, FileLink)]
            self.assertEqual({Path(link.path).name for link in links},
                             {"inference_set.jsonl", "scores.jsonl", "metrics.json", "manifest.json"})
            for link in links:
                self.assertNotIn("\\", link.path)
                self.assertEqual(Path(link.path).resolve().parent, self.run.resolve())
                self.assertIn("<a href=", link._repr_html_())
        self.assertEqual(len(displayed), 7)
        self.assertEqual(len(namespace["examples"]), 2)

    def test_adding_third_target_retains_completed_runs_and_returns_only_missing_alias(self):
        first = lab.load_run(self.run)
        newer_model = replace(first, provenance={
            **first.provenance, "run_id": "newer-synthetic", "target": self.metadata.deployments[2].to_dict(),
        })
        remaining = lab.remaining_comparison_targets(
            self.suite, self.settings, self.metadata, [first, newer_model], root=self.root,
        )
        self.assertEqual(remaining, ["intermediate_model"])
        intermediate_model = replace(first, provenance={
            **first.provenance, "run_id": "intermediate-synthetic",
            "target": self.metadata.deployments[1].to_dict(),
        })
        self.assertEqual(lab.remaining_comparison_targets(
            self.suite, self.settings, self.metadata, [first, intermediate_model, newer_model], root=self.root,
        ), [])
        self.assertEqual(first.provenance["run_id"], "older-synthetic")

    def test_incomplete_duplicate_mismatched_runs_cannot_be_silently_reused(self):
        first = lab.load_run(self.run)
        for runs in (
            [replace(first, complete=False)], [first, first],
            [replace(first, provenance={**first.provenance, "approval_hash": "different"})],
            [replace(first, provenance={**first.provenance, "target": {
                **first.provenance["target"], "modelVersion": "changed",
            }})],
        ):
            with self.subTest(runs=runs), self.assertRaises(ValueError):
                lab.remaining_comparison_targets(self.suite, self.settings, self.metadata, runs, root=self.root)

    def test_notebook_comparison_preview_does_not_make_paid_calls(self):
        from IPython.display import FileLink

        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        preview = next("".join(cell["source"]) for cell in notebook["cells"]
                       if cell["cell_type"] == "code" and "remaining_targets = " in "".join(cell["source"]))
        runs_path = self.root / "selected-runs.json"
        runs_path.write_text(json.dumps({"suite": str(self.suite), "runs": [str(self.run)]}), encoding="utf-8")
        namespace = {
            "json": json, "Path": Path, "runs_path": runs_path, "settings": self.settings,
            "metadata": self.metadata, "demo_root": self.root.resolve(), "load_run": lab.load_run,
            "FileLink": FileLink, "display": lambda link: None,
            "remaining_comparison_targets": lab.remaining_comparison_targets,
        }
        with patch.object(lab, "evaluate_target", side_effect=AssertionError("Preview made a paid call")) as evaluate:
            namespace["evaluate_target"] = evaluate
            with redirect_stdout(io.StringIO()):
                exec(preview, namespace)
            evaluate.assert_not_called()
        self.assertEqual(namespace["remaining_targets"], ["intermediate_model", "newer_model"])

    def test_legacy_saved_evidence_is_readable_but_not_approved_for_new_aliases(self):
        approved = dict(lab._json(self.suite / "approval.json"))
        for role in ("tester", "judge"):
            approved["shared_settings"][role]["alias"] = approved["shared_settings"][role]["alias"].removesuffix("_model")
        approved["shared_settings_hash"] = lab._digest(approved["shared_settings"])
        lab._write_json(self.suite / "approval.json", approved)
        settings_snapshot = dict(lab._json(self.suite / "evaluation-settings.json"))
        settings_snapshot["shared"] = approved["shared_settings"]
        lab._write_json(self.suite / "evaluation-settings.json", settings_snapshot)
        provenance = dict(lab._json(self.run / "provenance.json"))
        provenance["target"]["alias"] = "older"
        provenance["approval"] = approved
        provenance["approval_hash"] = lab._file_hash(self.suite / "approval.json")
        lab._write_json(self.run / "provenance.json", provenance)
        before = {path: path.read_bytes() for path in self.suite.rglob("*") if path.is_file()}
        saved = lab.load_run(self.run)
        self.assertTrue(saved.complete)
        self.assertEqual(saved.provenance["target"]["alias"], "older")
        with self.assertRaisesRegex(ValueError, "Shared evaluation settings changed"):
            lab.verify_approval(self.suite, self.settings, self.metadata, root=self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_comparison_display_reads_legacy_labels_without_changing_provenance(self):
        import pandas as pd
        from IPython.display import FileLink

        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        source = next("".join(cell["source"]) for cell in notebook["cells"]
                      if cell["cell_type"] == "code" and "comparison_runs.sort(" in "".join(cell["source"]))
        saved = lab.load_run(self.run)
        old_target = {**saved.provenance["target"], "alias": "older"}
        new_target = {**self.metadata.deployments[2].to_dict(), "alias": "newer"}
        results = {
            "older": replace(saved, provenance={**saved.provenance, "target": old_target}),
            "newer": replace(saved, provenance={**saved.provenance, "target": new_target}),
        }
        pointer = self.root / "legacy-runs.json"
        lab._write_json(pointer, {"suite": str(self.suite), "runs": ["newer", "older"]})
        displayed = []
        namespace = {
            "json": json, "Path": Path, "pd": pd, "display": displayed.append,
            "FileLink": FileLink, "demo_root": self.root.resolve(),
            "runs_path": pointer, "settings": self.settings, "ModelDeployment": lab.ModelDeployment,
            "load_run": lambda path: results[str(path)], "compare_runs": lab.compare_runs,
            "failure_examples": lab.failure_examples,
        }
        with redirect_stdout(io.StringIO()):
            exec(compile(source, "legacy-comparison-display", "exec"), namespace)
        self.assertEqual([run.provenance["target"]["alias"] for run in namespace["comparison_runs"]], ["older", "newer"])
        self.assertEqual(len(displayed), 7)
        self.assertTrue(all(isinstance(link, FileLink) for link in displayed[1:]))

    def test_setup_only_connects_models_and_hands_off_to_flow(self):
        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "02_configure.ipynb").read_text(encoding="utf-8"))
        code = "\n".join("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code")
        text = "\n".join("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "markdown")
        self.assertIn("smoke_connections(metadata)", code)
        self.assertNotIn("load_evaluation", code)
        self.assertNotIn("customer-support.yaml", text)
        self.assertIn("Setup complete", text)
        self.assertIn("./03_assert_flow.ipynb", text)

    def test_flow_configuration_runs_in_fresh_namespace_without_paid_calls(self):
        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        headings = ["".join(cell["source"]).splitlines()[0] for cell in notebook["cells"]
                    if cell["cell_type"] == "markdown"]
        self.assertLess(headings.index("## Define the policy"), headings.index("## Configure the evaluation"))
        self.assertLess(headings.index("## Configure the evaluation"), headings.index("## Generate and review tests"))
        (self.root / "notebooks").mkdir()
        namespace = {}
        displayed = []
        with (
            chdir(self.root / "notebooks"),
            patch.object(lab, "load_connections", return_value=self.metadata),
            patch.object(lab, "run_native", side_effect=AssertionError("Configuration made a paid call")) as native,
            patch.object(lab, "evaluate_target", side_effect=AssertionError("Configuration evaluated a target")) as evaluate,
            patch("IPython.display.display", side_effect=displayed.append),
            redirect_stdout(io.StringIO()),
        ):
            for cell in notebook["cells"]:
                if cell["cell_type"] == "markdown" and "".join(cell["source"]).startswith("## Generate and review tests"):
                    break
                if cell["cell_type"] == "code":
                    exec(compile("".join(cell["source"]), "flow-configuration-notebook", "exec"), namespace)
            native.assert_not_called()
            evaluate.assert_not_called()
        self.assertEqual(namespace["demo_root"], self.root.resolve())
        self.assertEqual(namespace["policy"], self.policy)
        self.assertEqual(namespace["settings"].generation_target, self.settings.generation_target)
        self.assertEqual(len(displayed), 4)
        self.assertEqual(displayed[2]["role"].tolist(), ["generator", "tester", "judge"])

    def test_own_policy_notebook_keeps_the_same_evaluation_flow(self):
        notebooks = lab.DEMO_ROOT / "notebooks"
        original = json.loads((notebooks / "03_assert_flow.ipynb").read_text(encoding="utf-8"))
        own = json.loads((notebooks / "04_your_own_policy.ipynb").read_text(encoding="utf-8"))
        own_cells = {cell["id"]: cell for cell in own["cells"]}
        self.assertEqual(len(own_cells), len(own["cells"]))
        self.assertEqual(
            [cell["id"] for cell in own["cells"] if cell["id"] not in {
                "write-your-policy", "choose-policy-heading", "policy-selection-options", "select-policy",
            }],
            [cell["id"] for cell in original["cells"]],
        )
        for cell in own["cells"]:
            if cell["cell_type"] == "code":
                self.assertIsNone(cell["execution_count"])
                self.assertEqual(cell["outputs"], [])
                ast.parse("".join(cell["source"]))
        for cell in original["cells"]:
            if cell["cell_type"] == "code" and cell["id"] not in {
                "2", "load-policy", "taxonomy-review-option", "generated-review-option",
            }:
                self.assertEqual(own_cells[cell["id"]]["source"], cell["source"], cell["id"])
        for identity in ("taxonomy-review-option", "generated-review-option"):
            self.assertTrue("".join(own_cells[identity]["source"]).endswith("= False"))
        text = "\n".join("".join(cell["source"]) for cell in original["cells"])
        self.assertNotIn("### Your turn:", text)
        self.assertIn("./04_your_own_policy.ipynb", text)

    def test_own_policy_authoring_and_resume_preserve_example_inputs(self):
        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "04_your_own_policy.ipynb").read_text(encoding="utf-8"))
        cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}
        original_files = {
            path: path.read_bytes() for path in (self.root / "data").rglob("*") if path.is_file()
        }
        pointers = {}
        for name in ("active-suite.json", "active-runs.json"):
            path = lab.artifact_path(name, root=self.root)
            path.write_text('{"walkthrough": true}\n')
            pointers[path] = path.read_bytes()
        (self.root / "notebooks").mkdir()
        namespace = {}
        with (
            chdir(self.root / "notebooks"),
            patch.object(lab, "load_connections", return_value=self.metadata),
            patch.object(lab, "run_native", side_effect=AssertionError("Authoring made a paid call")) as native,
            patch("IPython.display.display"),
            redirect_stdout(io.StringIO()),
        ):
            exec(cells["2"], namespace)
            exec(cells["policy-selection-options"], namespace)
            exec(cells["select-policy"], namespace)
            self.assertEqual(namespace["settings"].policy_path, "policies/my-policy-1.yaml")
            self.assertEqual(namespace["selection_path"].parent,
                             lab.policy_collection("my-policy", "1", root=self.root))
            exec(cells["write-your-policy"], namespace)
            own_path = self.root / "data" / "policies" / "my-policy-1.yaml"
            with self.assertRaises(ValueError):
                exec(cells["load-policy"], namespace)
            self.assertFalse(own_path.exists())
            namespace["POLICY_ID"] = "appointment-support"
            exec(cells["select-policy"], namespace)
            own_path = namespace["policy_path"]
            namespace["my_policy"] = {
                "id": namespace["POLICY_ID"], "revision": namespace["POLICY_REVISION"],
                "context": "Explain appointments; no tools can make bookings.",
                "prohibited": ["Claim an appointment has been booked."],
                "permitted": ["Explain how to contact a human scheduler."],
            }
            exec(cells["load-policy"], namespace)
            self.assertEqual(namespace["policy"].id, "appointment-support")
            self.assertEqual(lab.Policy.from_dict(yaml.safe_load(own_path.read_text())), namespace["policy"])
            settings = namespace["settings"]
            suite = lab.create_suite(settings, self.metadata, root=self.root)
            snapshot = (suite / "policy.yaml").read_bytes()
            namespace["my_policy"]["revision"] = "2"
            with self.assertRaisesRegex(ValueError, "policy-writing cell"):
                exec(cells["load-policy"], namespace)
            namespace["POLICY_REVISION"] = "2"
            exec(cells["select-policy"], namespace)
            exec(cells["load-policy"], namespace)
            self.assertEqual((suite / "policy.yaml").read_bytes(), snapshot)
            self.assertEqual(namespace["policy"].revision, "2")
            exec(cells["2"], namespace)
            exec(cells["select-policy"], namespace)
            self.assertEqual(namespace["settings"].policy_path, "policies/appointment-support-2.yaml")
            native.assert_not_called()
        for path, before in {**original_files, **pointers}.items():
            self.assertEqual(path.read_bytes(), before, str(path))

    def test_own_notebook_switches_policies_and_revisions_without_overwriting_saved_work(self):
        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "04_your_own_policy.ipynb").read_text(encoding="utf-8"))
        cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}
        (self.root / "notebooks").mkdir()
        snapshots = {}
        experiments = {}
        namespace = {}
        with (
            chdir(self.root / "notebooks"),
            patch.object(lab, "load_connections", return_value=self.metadata),
            patch.object(lab, "run_native", side_effect=AssertionError("Switching made a paid call")) as native,
            patch("IPython.display.display"),
            redirect_stdout(io.StringIO()),
        ):
            for identity, revision in (("appointments", "1"), ("travel", "1"), ("appointments", "2")):
                exec(cells["2"], namespace)
                namespace.update(POLICY_ID=identity, POLICY_REVISION=revision)
                exec(cells["select-policy"], namespace)
                exec(cells["write-your-policy"], namespace)
                namespace["my_policy"].update({
                    "context": f"Explain {identity}; revision {revision}.",
                    "prohibited": [f"Claim an action was completed for {identity}."],
                    "permitted": [f"Explain how to contact a human for {identity}."],
                })
                exec(cells["load-policy"], namespace)
                policy_bytes = namespace["policy_path"].read_bytes()
                exec(cells["load-policy"], namespace)
                self.assertEqual(namespace["policy_path"].read_bytes(), policy_bytes)
                suite = lab.create_suite(namespace["settings"], self.metadata, root=self.root)
                self.assertEqual(suite.parent, namespace["experiment_path"])
                lab._write_json(namespace["selection_path"], {"suite": str(suite)})
                lab._write_json(namespace["runs_path"], {"suite": str(suite), "runs": [str(suite / "saved-run")]})
                experiments[(identity, revision)] = (
                    namespace["settings"], namespace["policy_path"], namespace["selection_path"],
                    namespace["runs_path"], suite,
                )
                for path in (namespace["policy_path"], namespace["selection_path"],
                             namespace["runs_path"], suite / "policy.yaml"):
                    snapshots[path] = path.read_bytes()
            self.assertEqual(len({values[1] for values in experiments.values()}), 3)
            self.assertEqual(len({values[2] for values in experiments.values()}), 3)
            for (identity, revision), (settings, path, selected, runs, suite) in experiments.items():
                exec(cells["2"], namespace)
                namespace.update(POLICY_ID=identity, POLICY_REVISION=revision)
                exec(cells["select-policy"], namespace)
                self.assertEqual(namespace["settings"], settings)
                self.assertEqual(namespace["policy_path"], path)
                self.assertEqual(namespace["selection_path"], selected)
                self.assertEqual(namespace["runs_path"], runs)
                self.assertEqual(json.loads(runs.read_text())["suite"], str(suite))
                self.assertEqual(lab._suite_policy(suite).id, identity)
            namespace["my_policy"] = lab.asdict(lab.Policy.from_dict(yaml.safe_load(path.read_text())))
            namespace["my_policy"]["context"] = "Different rules under the same revision"
            with self.assertRaisesRegex(ValueError, "different content"):
                exec(cells["load-policy"], namespace)
            for identity in ("../escape", "", "a/b"):
                namespace["POLICY_ID"] = identity
                with self.assertRaisesRegex(ValueError, "safe policy ID"):
                    exec(cells["select-policy"], namespace)
            native.assert_not_called()
        self.assertEqual(snapshots, {path: path.read_bytes() for path in snapshots})
