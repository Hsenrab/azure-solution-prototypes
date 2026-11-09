from dataclasses import replace
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import yaml

from app import assert_lab as lab
from test_assert_lab import metadata


FIXTURES = Path(__file__).parent / "fixtures"


class ResultTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(lab.DEMO_ROOT / "data", self.root / "data")
        (self.root / "data" / "extra-tests.jsonl").write_text("")
        self.policy, settings = lab.load_evaluation(root=self.root)
        self.settings = replace(settings, prompt_count=2, scenario_count=2)
        self.metadata = metadata()
        self.suite = lab.create_suite(self.settings, self.metadata, root=self.root)
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

        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_test.ipynb").read_text(encoding="utf-8"))
        pointer = self.root / "active-runs.json"
        lab._write_json(pointer, {"suite": str(self.suite), "runs": [str(self.run)]})
        displayed = []
        namespace = {
            "json": json, "Path": Path, "pd": pd, "display": displayed.append,
            "runs_path": pointer, "load_run": lab.load_run, "summarize_run": lab.summarize_run,
            "failure_examples": lab.failure_examples,
        }
        sources = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
        with redirect_stdout(io.StringIO()):
            for source in sources:
                if "saved = load_run(" in source or "examples = failure_examples(saved)" in source:
                    exec(compile(source, "saved-result-notebook", "exec"), namespace)
        self.assertEqual(len(displayed), 3)
        self.assertEqual(len(namespace["examples"]), 2)

    def test_adding_third_target_retains_completed_runs_and_returns_only_missing_alias(self):
        first = lab.load_run(self.run)
        newer = replace(first, provenance={
            **first.provenance, "run_id": "newer-synthetic", "target": self.metadata.deployments[2].to_dict(),
        })
        remaining = lab.remaining_comparison_targets(
            self.suite, self.settings, self.metadata, [first, newer], root=self.root,
        )
        self.assertEqual(remaining, ["intermediate"])
        intermediate = replace(first, provenance={
            **first.provenance, "run_id": "intermediate-synthetic",
            "target": self.metadata.deployments[1].to_dict(),
        })
        self.assertEqual(lab.remaining_comparison_targets(
            self.suite, self.settings, self.metadata, [first, intermediate, newer], root=self.root,
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
        notebook = json.loads((lab.DEMO_ROOT / "notebooks" / "03_test.ipynb").read_text(encoding="utf-8"))
        preview = next("".join(cell["source"]) for cell in notebook["cells"]
                       if cell["cell_type"] == "code" and "remaining_targets = " in "".join(cell["source"]))
        runs_path = self.root / "selected-runs.json"
        runs_path.write_text(json.dumps({"suite": str(self.suite), "runs": [str(self.run)]}), encoding="utf-8")
        namespace = {
            "json": json, "Path": Path, "runs_path": runs_path, "settings": self.settings,
            "metadata": self.metadata, "demo_root": self.root, "load_run": lab.load_run,
            "remaining_comparison_targets": lab.remaining_comparison_targets,
        }
        with patch.object(lab, "evaluate_target", side_effect=AssertionError("Preview made a paid call")) as evaluate:
            namespace["evaluate_target"] = evaluate
            with redirect_stdout(io.StringIO()):
                exec(preview, namespace)
            evaluate.assert_not_called()
        self.assertEqual(namespace["remaining_targets"], ["intermediate", "newer"])
