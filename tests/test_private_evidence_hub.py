import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AGGREGATOR = ROOT / "templates" / "PRIVATE_EVIDENCE_HUB_AGGREGATOR.py"
ROUTING = ROOT / "config" / "MODEL_ROUTING.yaml"


def load_aggregator():
    spec = importlib.util.spec_from_file_location("private_evidence_hub_aggregator", AGGREGATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def worker_group(first_pass, final_accept, rework, effective=2.0, samples=2):
    return {
        "role": "bounded_worker",
        "task_class": "bounded_code_edit",
        "risk_level": "medium",
        "model_id": "model-a",
        "model_semantic_key": "model-a@r1",
        "reasoning_semantic_key": "model-a:high@r1",
        "metrics": {
            "sample_count": samples,
            "effective_sample_count": effective,
            "evidence_strength": "developing",
            "mean_rework_count": rework,
            "weighted_mean_rework_count": rework,
            "accepted_first_pass_rate": first_pass,
            "final_accepted_rate": final_accept,
            "tests_passed_rate": 1.0,
            "any_violation_rate": 0.0,
        },
        "covariates": {},
    }


def validator_group(review=1.0, findings=1):
    return {
        "role": "validator",
        "task_class": "bounded_code_edit",
        "risk_level": "medium",
        "model_id": "model-v",
        "model_semantic_key": "model-v@r1",
        "reasoning_semantic_key": "model-v:high@r1",
        "metrics": {
            "sample_count": 2,
            "effective_sample_count": 2.0,
            "evidence_strength": "developing",
            "mean_rework_count": 0.0,
            "weighted_mean_rework_count": 0.0,
            "review_completed_rate": review,
            "material_findings_confirmed_total": findings,
            "material_findings_confirmed_known_samples": 2,
            "false_positive_confirmed_total": 0,
            "false_positive_confirmed_known_samples": 2,
            "missed_defect_confirmed_total": 0,
            "missed_defect_confirmed_known_samples": 2,
        },
        "covariates": {},
    }


def state(groups):
    return {
        "schema_version": "1.0",
        "repository_scope": "same_repository_only",
        "enabled": True,
        "usable_for_routing": True,
        "authority": {
            "derived_cache_only": True,
            "task_result_validation_acceptance_remain_authoritative": True,
            "deleting_state_does_not_delete_evidence": True,
            "rebuildable_from_durable_comments": True,
        },
        "scan": {"complete": True},
        "model_groups": groups,
        "strategy_groups": [],
    }


def bundle(states):
    repos = [repo for repo, _ in states]
    return {
        "schema_version": "1.0",
        "hub": {"enabled": True, "source_repositories": repos},
        "project_states": [{"repository": repo, "state": value} for repo, value in states],
    }


class PrivateEvidenceHubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_aggregator()

    def test_two_project_deterministic_merge(self):
        data = bundle([
            ("owner/a", state([worker_group(0.5, 1.0, 1.0)])),
            ("owner/b", state([worker_group(1.0, 1.0, 0.0)])),
        ])
        one = self.mod.aggregate_bundle(copy.deepcopy(data))
        two = self.mod.aggregate_bundle(copy.deepcopy(data))
        self.assertEqual(one, two)
        self.assertTrue(one["usable_for_routing"])
        group = one["model_groups"][0]
        self.assertEqual(group["source_project_count"], 2)
        self.assertTrue(group["cross_project_usable"])
        self.assertEqual(group["metrics"]["accepted_first_pass_rate"], 0.75)
        self.assertEqual(group["metrics"]["final_accepted_rate"], 1.0)
        self.assertEqual(group["metrics"]["weighted_mean_rework_count"], 0.5)

    def test_single_project_group_is_not_cross_project_usable(self):
        data = bundle([
            ("owner/a", state([worker_group(1.0, 1.0, 0.0)])),
            ("owner/b", state([])),
        ])
        result = self.mod.aggregate_bundle(data)
        self.assertFalse(result["usable_for_routing"])
        self.assertEqual(result["source_project_count"], 2)
        self.assertFalse(result["model_groups"][0]["cross_project_usable"])
        self.assertEqual(result["model_groups"][0]["metrics"]["evidence_strength"], "insufficient")

    def test_duplicate_missing_and_unusable_sources_fail_closed(self):
        good = state([worker_group(1.0, 1.0, 0.0)])
        duplicate = {
            "schema_version": "1.0",
            "hub": {"enabled": True, "source_repositories": ["owner/a", "owner/a"]},
            "project_states": [{"repository": "owner/a", "state": good}],
        }
        with self.assertRaises(self.mod.HubInputError):
            self.mod.aggregate_bundle(duplicate)

        missing = {
            "schema_version": "1.0",
            "hub": {"enabled": True, "source_repositories": ["owner/a", "owner/b"]},
            "project_states": [{"repository": "owner/a", "state": good}],
        }
        with self.assertRaises(self.mod.HubInputError):
            self.mod.aggregate_bundle(missing)

        bad_state = copy.deepcopy(good)
        bad_state["usable_for_routing"] = False
        with self.assertRaises(self.mod.HubInputError):
            self.mod.aggregate_bundle(bundle([("owner/a", good), ("owner/b", bad_state)]))

    def test_worker_and_validator_remain_separate(self):
        data = bundle([
            ("owner/a", state([worker_group(1.0, 1.0, 0.0), validator_group(findings=1)])),
            ("owner/b", state([worker_group(0.5, 1.0, 1.0), validator_group(findings=2)])),
        ])
        result = self.mod.aggregate_bundle(data)
        self.assertEqual(len(result["model_groups"]), 2)
        roles = {group["role"] for group in result["model_groups"]}
        self.assertEqual(roles, {"bounded_worker", "validator"})
        validator = next(group for group in result["model_groups"] if group["role"] == "validator")
        self.assertEqual(validator["metrics"]["material_findings_confirmed_total"], 3)

    def test_output_is_prior_not_authority_or_auto_qualification(self):
        result = self.mod.aggregate_bundle(bundle([
            ("owner/a", state([worker_group(1.0, 1.0, 0.0)])),
            ("owner/b", state([worker_group(1.0, 1.0, 0.0)])),
        ]))
        authority = result["authority"]
        self.assertTrue(authority["derived_cache_only"])
        self.assertTrue(authority["model_routing_remains_canonical_owner"])
        self.assertFalse(authority["may_auto_qualify_or_dequalify_model"])
        self.assertFalse(authority["may_override_task_safety_permission_capability_or_independence"])
        self.assertFalse(authority["may_rewrite_governance_core_rules"])
        self.assertFalse(result["privacy"]["automatic_public_upstream_delivery"])

    def test_routing_precedence_places_project_local_above_peh_and_peh_above_global(self):
        text = ROUTING.read_text(encoding="utf-8")
        local = text.index("    - project_local_calibration")
        private = text.index("    - private_cross_project_calibration")
        governance = text.index("    - governance_calibration_snapshot")
        external = text.index("    - accepted_external_benchmark_evidence")
        self.assertLess(local, private)
        self.assertLess(private, governance)
        self.assertLess(governance, external)
        self.assertIn("private_cross_project_prior_may_change_model_qualification_automatically: false", text)
        self.assertIn("private_cross_project_prior_may_rewrite_core_rules: false", text)

    def test_aggregator_has_no_network_imports_and_cli_fails_closed(self):
        source = AGGREGATOR.read_text(encoding="utf-8")
        for forbidden in ("urllib", "requests", "http.client", "socket", "github.com", "api.github.com"):
            self.assertNotIn(forbidden, source)

        invalid = {"schema_version": "1.0", "hub": {"enabled": True, "source_repositories": []}, "project_states": []}
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "invalid.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(AGGREGATOR), "--input", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("PEH_ERROR:", proc.stderr)


if __name__ == "__main__":
    unittest.main()
