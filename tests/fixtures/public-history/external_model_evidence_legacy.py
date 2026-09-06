import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "templates" / "EXTERNAL_MODEL_EVIDENCE_UPDATE.py"
SOURCE_CONFIG = REPO / "config" / "EXTERNAL_MODEL_EVIDENCE_SOURCE.yaml"
EVIDENCE = REPO / "config" / "EXTERNAL_MODEL_EVIDENCE.yaml"
MODEL_ROUTING = REPO / "config" / "MODEL_ROUTING.yaml"
WORKFLOW = REPO / ".github" / "workflows" / "external-model-evidence.yml"
PROTOCOL = REPO / "docs" / "model-governance" / "EXTERNAL_MODEL_EVIDENCE.md"
BASELINE = "e49eb7c878bf2a91674b12781a2185264411848b"
ACCEPTED_0_3_18 = "7f0b0158092aa39c53540e6ff87dbabb1c9fc6af"

SPEC = importlib.util.spec_from_file_location("external_model_evidence_update", SCRIPT)
UPDATER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATER)

HEADER = (
    "model,AMPS_Hard,code_completion,code_generation,connections,consecutive_events,"
    "integrals_with_game,javascript,logic_with_navigation,math_comp,olympiad,paraphrase,"
    "plot_unscrambling,python,simplify,spatial,story_generation,summarize,tablejoin,"
    "tablereformat,theory_of_mind,typescript,typos,zebra_puzzle"
)
ROWS = [
    "gpt-5.6-sol-max,98.0,84.783,83.099,100.0,90.214,100.0,63.636,82.0,95.098,91.693,71.517,79.051,55.0,70.517,100.0,75.917,69.433,49.308,100.0,84.615,50.0,84.0,100.0",
    "gpt-5.6-terra-max,98.0,80.435,76.056,93.0,87.67,95.0,68.182,76.0,95.098,91.535,57.033,69.678,50.0,61.433,100.0,66.833,73.167,50.25,100.0,86.538,46.667,86.0,100.0",
    "gpt-5.6-luna-max,98.0,86.957,78.873,96.5,86.504,70.0,63.636,80.0,92.157,88.646,47.817,51.201,45.0,58.667,96.0,69.067,64.933,47.596,100.0,73.077,36.667,70.0,93.5",
    "gemini-3.7-flash-high,98.0,76.087,81.69,100.0,60.373,88.0,68.182,74.0,96.078,91.794,78.067,66.365,60.0,74.617,100.0,82.25,84.767,45.481,98.039,82.692,46.667,90.0,94.5",
]
CATEGORIES = {
    "Reasoning": ["theory_of_mind", "zebra_puzzle", "spatial", "logic_with_navigation"],
    "Coding": ["code_generation", "code_completion"],
    "Agentic Coding": ["javascript", "typescript", "python"],
    "Mathematics": ["AMPS_Hard", "integrals_with_game", "math_comp", "olympiad"],
    "Data Analysis": ["consecutive_events", "tablejoin", "tablereformat"],
    "Language": ["connections", "plot_unscrambling", "typos"],
    "IF": ["paraphrase", "simplify", "story_generation", "summarize"],
}


def git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def baseline_bytes(path):
    return subprocess.run(
        ["git", "-C", str(REPO), "show", f"{BASELINE}:{path}"],
        check=True,
        capture_output=True,
    ).stdout


def accepted_release_bytes(path):
    return subprocess.run(
        ["git", "-C", str(REPO), "show", f"{ACCEPTED_0_3_18}:{path}"],
        check=True,
        capture_output=True,
    ).stdout


class ExternalEvidenceQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = UPDATER.load(SOURCE_CONFIG)

    def source_fixture(self):
        anchor = self.config["initial_anchor"]
        return {
            "source_commit": anchor["source_commit"],
            "source_release": anchor["source_release"],
            "table_path": anchor["table_path"],
            "table_blob_sha": anchor["table_blob_sha"],
            "table_text": HEADER + "\n" + "\n".join(ROWS) + "\n",
            "categories_path": anchor["categories_path"],
            "categories_blob_sha": anchor["categories_blob_sha"],
            "categories_text": json.dumps(CATEGORIES),
        }

    def normalize(self, source=None, config=None, collected="2026-09-01T05:57:00Z"):
        return UPDATER.normalize(config or self.config, source or self.source_fixture(), collected)

    def test_q1_initial_exact_anchor_generates_current_gpt_and_gemini_library(self):
        source = self.source_fixture()
        UPDATER.validate_initial_anchor(self.config, source)
        evidence = self.normalize(source)
        self.assertEqual(len(evidence["observation_rows"]), 28)
        self.assertEqual(
            {row[0] for row in evidence["observation_rows"]},
            {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gemini-3.7-flash"},
        )
        self.assertTrue(UPDATER.materially_equal(evidence, UPDATER.load(EVIDENCE)))

    def test_q2_only_four_frozen_model_keys_can_be_emitted(self):
        evidence = self.normalize()
        keys = sorted({row[0] for row in evidence["observation_rows"]})
        self.assertEqual(keys, sorted(self.config["model_mappings"]))
        self.assertEqual(len(keys), 4)

    def test_q3_source_native_representative_metrics_are_preserved_without_composite(self):
        evidence = self.normalize()
        self.assertEqual(evidence["observation_columns"], UPDATER.COLUMNS)
        rows = evidence["observation_rows"]
        self.assertEqual({row[2] for row in rows}, set(self.config["representative_benchmarks"]))
        row = next(row for row in rows if row[0] == "gpt-5.6-sol" and row[3] == "code_generation")
        self.assertEqual(row[4], 83.099)
        serialized = json.dumps(evidence)
        self.assertNotIn("overall_score", serialized)
        self.assertNotIn("category_average", serialized)

    def test_q4_unknown_external_models_are_ignored(self):
        source = self.source_fixture()
        source["table_text"] += "unknown-model," + ",".join(["1"] * 23) + "\n"
        evidence = self.normalize(source)
        self.assertNotIn("unknown-model", {row[1] for row in evidence["observation_rows"]})

    def test_q5_missing_required_mapping_fails_before_candidate(self):
        source = self.source_fixture()
        source["table_text"] = HEADER + "\n" + "\n".join(
            row for row in ROWS if not row.startswith("gpt-5.6-terra-max,")
        ) + "\n"
        with self.assertRaises(UPDATER.EvidenceError):
            self.normalize(source)

    def test_q6_source_schema_or_selected_benchmark_drift_fails_closed(self):
        source = self.source_fixture()
        broken = copy.deepcopy(CATEGORIES)
        broken["Agentic Coding"] = ["javascript", "typescript"]
        source["categories_text"] = json.dumps(broken)
        with self.assertRaises(UPDATER.EvidenceError):
            self.normalize(source)

        config = copy.deepcopy(self.config)
        config["representative_benchmarks"]["Coding"] = "python"
        with self.assertRaises(UPDATER.EvidenceError):
            self.normalize(config=config)

    def test_q7_similar_name_cannot_replace_exact_mapping(self):
        source = self.source_fixture()
        source["table_text"] = source["table_text"].replace("gpt-5.6-sol-max,", "gpt-5.6-sol-max-v2,", 1)
        with self.assertRaisesRegex(UPDATER.EvidenceError, "exact mapped source row"):
            self.normalize(source)

    def test_q8_release_change_creates_new_series(self):
        old = self.normalize()
        source = self.source_fixture()
        source["source_release"] = "2026-07-01"
        source["table_path"] = "public/table_2026_07_01.csv"
        source["table_blob_sha"] = "1" * 40
        source["categories_path"] = "public/categories_2026_07_01.json"
        source["categories_blob_sha"] = "2" * 40
        new = self.normalize(source)
        self.assertFalse(UPDATER.materially_equal(old, new))
        self.assertEqual({row[5] for row in new["observation_rows"]}, {"livebench-release-2026-07-01"})

    def test_q9_timestamp_order_and_json_format_noise_is_non_material(self):
        first = self.normalize(collected="2026-09-01T05:57:00Z")
        second = self.normalize(collected="2026-09-02T05:57:00Z")
        second["observation_rows"].reverse()
        reparsed = json.loads(json.dumps(second, indent=7))
        self.assertTrue(UPDATER.materially_equal(first, reparsed))

    def test_q10_registry_and_qualification_boundary_is_untouched(self):
        accepted_registry = accepted_release_bytes("config/MODEL_REGISTRY.yaml")
        self.assertEqual(accepted_registry, baseline_bytes("config/MODEL_REGISTRY.yaml"))
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("MODEL_REGISTRY.yaml", script)
        accepted = UPDATER.load(EVIDENCE)
        self.assertFalse(accepted["authority"]["may_auto_change_model_registry_status"])
        self.assertFalse(accepted["authority"]["may_bypass_qualification"])

    def test_q11_internal_calibration_remains_higher_precedence(self):
        text = MODEL_ROUTING.read_text(encoding="utf-8")
        order = [
            "- task_override",
            "- project_local_calibration",
            "- governance_calibration_snapshot",
            "- accepted_external_benchmark_evidence",
            "- bootstrap_seed",
        ]
        start = text.index("selection_precedence:")
        positions = [text.index(item, start) for item in order]
        self.assertEqual(positions, sorted(positions))

    def test_q12_0_3_18_conformance_checker_and_tests_match_0_3_17_baseline(self):
        for path in ("templates/GOVERNANCE_CONFORMANCE_CHECK.py", "tests/test_governance_conformance.py"):
            self.assertEqual(accepted_release_bytes(path), baseline_bytes(path))

    def test_q13_later_evidence_revision_is_non_retroactive(self):
        text = PROTOCOL.read_text(encoding="utf-8")
        self.assertIn("never retroactively changes an already activated Task", text)
        routing = MODEL_ROUTING.read_text(encoding="utf-8")
        self.assertIn("exact accepted external evidence ref", routing)
        self.assertIn("later evidence revision does not retroactively change", routing)

    def test_q14_pull_request_validation_is_read_only(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        validate = text.split("  validate:", 1)[1].split("  refresh:", 1)[0]
        self.assertIn("contents: read", validate)
        self.assertNotIn("git push", validate)
        self.assertNotIn("gh pr create", validate)
        self.assertNotIn("contents: write", validate)

    def test_q15_refresh_never_auto_merges_or_auto_qualifies(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        refresh = text.split("  refresh:", 1)[1]
        self.assertIn("gh pr create", refresh)
        self.assertNotIn("gh pr merge", refresh)
        self.assertNotIn("MODEL_REGISTRY", refresh)
        self.assertNotIn("MODEL_ROUTING.yaml", refresh)

    def test_q16_existing_open_update_pr_guard_precedes_candidate_generation(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("[MODEL-EXTERNAL-EVIDENCE-UPDATE-v1]", text)
        guard = text.index("Refuse to mutate an existing update candidate")
        check = text.index("Check latest public evidence")
        write = text.index("Generate deterministic candidate")
        self.assertLess(guard, check)
        self.assertLess(check, write)

    def test_q17_0_3_18_running_task_pinning_surfaces_match_0_3_17_baseline(self):
        for path in (
            "config/DISPATCH_POLICY.yaml",
            "docs/task-package/TASK_PACKAGE_SPEC.md",
            "templates/RESULT.md",
            "docs/context-continuity/TAKEOVER_RECONCILIATION_GATE.md",
            "docs/acceptance/LEAD_CONTROLLER_ACCEPTANCE_PROTOCOL.md",
        ):
            self.assertEqual(accepted_release_bytes(path), baseline_bytes(path))

    def test_q18_scope_protection_and_hot_path_bounds(self):
        accepted_candidate = "172314103fe8d2eb5bc61802e1c4f71db81599a2"
        allowed = {
            ".github/workflows/external-model-evidence.yml",
            "CHANGELOG.md",
            "GOVERNANCE_RELEASE.yaml",
            "VERSION",
            "config/CONFORMANCE_POLICY.yaml",
            "config/EXTERNAL_MODEL_EVIDENCE.yaml",
            "config/EXTERNAL_MODEL_EVIDENCE_SOURCE.yaml",
            "config/MODEL_ROUTING.yaml",
            "docs/model-governance/EXTERNAL_MODEL_EVIDENCE.md",
            "templates/EXTERNAL_MODEL_EVIDENCE_UPDATE.py",
            "tests/test_external_model_evidence.py",
        }
        required = {
            ".github/workflows/external-model-evidence.yml",
            "GOVERNANCE_RELEASE.yaml",
            "VERSION",
            "config/CONFORMANCE_POLICY.yaml",
            "config/EXTERNAL_MODEL_EVIDENCE.yaml",
            "config/EXTERNAL_MODEL_EVIDENCE_SOURCE.yaml",
            "config/MODEL_ROUTING.yaml",
            "docs/model-governance/EXTERNAL_MODEL_EVIDENCE.md",
            "templates/EXTERNAL_MODEL_EVIDENCE_UPDATE.py",
            "tests/test_external_model_evidence.py",
        }
        changed = {}
        for line in git("diff", "--name-status", f"{BASELINE}...{accepted_candidate}").splitlines():
            if not line:
                continue
            status, path = line.split("\t", 1)
            changed[path] = status
        self.assertTrue(set(changed) <= allowed)
        self.assertTrue(required <= set(changed))
        self.assertFalse(any(status.startswith("D") for status in changed.values()))
        hot_paths = (
            "config/DISPATCH_POLICY.yaml",
            "templates/RESULT.md",
            "docs/acceptance/LEAD_CONTROLLER_ACCEPTANCE_PROTOCOL.md",
        )
        sizes = [int(git("cat-file", "-s", f"{accepted_candidate}:{path}")) for path in hot_paths]
        self.assertEqual(len(hot_paths), 3)
        self.assertLessEqual(sum(sizes), 30000)


if __name__ == "__main__":
    unittest.main()
