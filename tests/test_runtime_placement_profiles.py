from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO / "templates" / "GOVERNANCE_CONFORMANCE_CHECK.py"
SPEC = importlib.util.spec_from_file_location("governance_conformance", CHECKER_PATH)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class RuntimePlacementProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dispatch = CHECKER.load_yaml_subset(REPO / "config" / "DISPATCH_POLICY.yaml")
        cls.release = CHECKER.load_yaml_subset(REPO / "GOVERNANCE_RELEASE.yaml")

    def test_runtime_mode_is_capability_defined_not_client_brand_defined(self):
        principles = self.dispatch["principles"]
        self.assertTrue(principles["runtime_mode_is_capability_defined_not_client_brand_defined"])
        self.assertTrue(principles["profile_names_are_compatibility_identifiers_not_brand_requirements"])
        self.assertTrue(principles["never_infer_native_dispatch_from_channel_name"])
        self.assertTrue(principles["web_interactive_means_non_native_delegating_runtime"])
        self.assertTrue(principles["codex_native_subagents_means_native_subagent_capable_runtime"])
        self.assertTrue(self.dispatch["runtime_profiles"]["capability_probe_outranks_profile_or_client_label"])
        self.assertFalse(self.dispatch["execution_economy"]["runtime_profile_is_capability_proof"])
        self.assertTrue(
            self.dispatch["execution_economy"]["profiles"]["native_delegate_preferred"]
            ["native_dispatch_must_be_proven_available"]
        )

    def test_web_external_placement_is_profile_local_and_environment_sensitive(self):
        placement = self.dispatch["web_external_assignment_placement"]
        self.assertEqual(placement["applies_only_to_profile"], "web_interactive")
        self.assertTrue(placement["after_external_dispatch_is_required"])
        self.assertEqual(
            placement["local_environment_required_preferred_surface"],
            "external_local_agent",
        )
        self.assertEqual(
            placement["no_local_environment_required_preferred_surface"],
            "external_web_conversation",
        )
        self.assertTrue(placement["placement_is_preference_not_route_authority"])
        self.assertTrue(placement["session_freshness_remains_owned_by_session_continuity"])

    def test_native_agent_cross_software_external_route_does_not_inherit_web_placement(self):
        placement = self.dispatch["web_external_assignment_placement"]
        self.assertTrue(
            placement["external_transport_does_not_reclassify_originating_runtime_profile"]
        )
        self.assertFalse(
            placement["native_agent_cross_software_external_route_uses_web_external_placement"]
        )
        native = self.dispatch["runtime_profiles"]["profiles"]["codex_native_subagents"]
        self.assertEqual(native["execution_economy_profile"], "native_delegate_preferred")
        self.assertEqual(
            self.dispatch["execution_economy"]["profiles"]["native_delegate_preferred"]
            ["preferred_route_order"],
            ["native_dispatch", "current_session", "external_owner_launch", "blocked"],
        )

    def test_ordinary_dispatch_does_not_inherit_hidden_model_identity_attestation(self):
        special = self.dispatch["special_model_identity_mode"]
        self.assertEqual(
            set(special["enabled_only_for"]),
            {"model_qualification", "model_benchmark", "exact_runtime_identity_experiment"},
        )
        self.assertTrue(special["ordinary_dispatch_policy_must_not_inherit"])
        task_spec = (REPO / "docs" / "task-package" / "TASK_PACKAGE_SPEC.md").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn(
            "普通 Preflight 不验证隐藏的内部 child model/reasoning identity。",
            task_spec,
        )

    def test_release_identity_and_lprl_independence(self):
        self.assertEqual(self.release["ordinary_governance"]["version"], "0.3.25")
        self.assertEqual(
            self.release["ordinary_governance"]["change_class"],
            "fail_closed_model_routing_decision_before_formal_launch",
        )
        lprl = self.release["modules"]["lprl"]
        self.assertEqual(lprl["version"], "0.2.5-pilot")
        self.assertFalse(lprl["semantic_change"])
        economy = self.release["execution_economy"]
        self.assertTrue(economy["runtime_mode_is_capability_defined_not_client_brand_defined"])
        self.assertFalse(economy["external_transport_reclassifies_originating_runtime_profile"])
        self.assertFalse(
            economy["native_agent_cross_software_external_route_uses_web_external_placement"]
        )


if __name__ == "__main__":
    unittest.main()
