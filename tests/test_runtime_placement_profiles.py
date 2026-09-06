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
        cls.conformance = CHECKER.load_yaml_subset(REPO / "config" / "CONFORMANCE_POLICY.yaml")
        cls.executor_compliance = CHECKER.load_yaml_subset(REPO / "config" / "EXECUTOR_COMPLIANCE.yaml")
        cls.local_policy = CHECKER.load_yaml_subset(REPO / "templates" / "LOCAL_POLICY.yaml")
        cls.routing_text = (REPO / "config" / "MODEL_ROUTING.yaml").read_text(
            encoding="utf-8-sig"
        )
        cls.registry_text = (REPO / "config" / "MODEL_REGISTRY.yaml").read_text(
            encoding="utf-8-sig"
        )
        cls.adoption_text = (REPO / "docs" / "project-adoption" / "PROJECT_ADOPTION.md").read_text(
            encoding="utf-8-sig"
        )
        cls.dispatch_guide_text = (REPO / "docs" / "protocol" / "DISPATCH_ROUTING_PROTOCOL.md").read_text(
            encoding="utf-8-sig"
        )

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

    def test_web_github_capability_is_prerequisite_not_agent_trigger(self):
        principles = self.dispatch["principles"]
        self.assertTrue(principles["web_mode_requires_confirmed_github_repository_read_write"])
        self.assertTrue(principles["github_native_operations_are_not_agent_placement_triggers"])
        self.assertTrue(principles["remote_repository_ci_is_not_local_test_execution"])
        self.assertTrue(principles["external_owner_launch_is_provider_and_client_neutral"])
        self.assertIn("GitHub-native 操作本身不构成 Agent placement", self.adoption_text)
        self.assertIn("github_native_operation_alone != agent_placement_trigger", self.dispatch_guide_text)
        self.assertIn("remote_repository_ci != local_test_execution", self.dispatch_guide_text)

    def test_web_direct_and_native_delegate_route_orders_are_locked(self):
        profiles = self.dispatch["execution_economy"]["profiles"]
        self.assertEqual(
            profiles["lead_direct_preferred"]["preferred_route_order"],
            ["current_session", "native_dispatch", "external_owner_launch", "blocked"],
        )
        self.assertEqual(
            profiles["native_delegate_preferred"]["preferred_route_order"],
            ["native_dispatch", "current_session", "external_owner_launch", "blocked"],
        )
        self.assertIn(
            "current_tools_and_permissions_are_sufficient",
            profiles["lead_direct_preferred"]["prefer_current_session_when"],
        )
        self.assertTrue(profiles["native_delegate_preferred"]["native_dispatch_must_be_proven_available"])
        self.assertTrue(profiles["native_delegate_preferred"]["native_reachable_executor_must_be_qualified"])

    def test_external_owner_launch_is_neutral_not_agent_by_definition(self):
        condition = self.dispatch["routing"]["external_owner_launch"]["condition"]
        self.assertIn("external", condition)
        self.assertIn("execution session", condition)
        self.assertNotIn("Agent", condition)
        self.assertIn("external_owner_launch != agent_by_definition", self.dispatch_guide_text)

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
        triggers = self.dispatch["runtime_placement_policy"]["local_materialization_required"]["triggers"]
        self.assertIn("local_test_execution_required", triggers)
        self.assertNotIn("remote_repository_ci", triggers)

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

    def test_executor_compliance_is_special_mode_reference_not_shadow_owner(self):
        compliance = self.executor_compliance
        self.assertEqual(compliance["scope"], "special_exact_model_reasoning_compliance_only")
        boundary = compliance["ordinary_task_boundary"]
        self.assertTrue(boundary["ordinary_task_semantics_are_owned_elsewhere"])
        self.assertFalse(boundary["duplicated_ordinary_task_gate_allowed"])
        self.assertFalse(boundary["duplicated_nested_delegation_policy_allowed"])
        self.assertFalse(boundary["duplicated_dispatch_decision_policy_allowed"])
        self.assertFalse(boundary["duplicated_validator_independence_policy_allowed"])
        for forbidden_top_level in (
            "ordinary_task_gate",
            "nested_delegation",
            "dispatch_decision",
            "delegated_execution",
            "validator_independence",
        ):
            self.assertNotIn(forbidden_top_level, compliance)
        self.assertEqual(
            compliance["canonical_ordinary_owners"]["dispatch_capability_route_delegation_lifecycle"],
            "config/DISPATCH_POLICY.yaml",
        )

    def test_surface_model_pools_are_selection_inputs_not_placement_owners(self):
        required = (
            "model_selection_happens_after_execution_surface_resolution: true",
            "model_price_tier_provider_may_change_execution_surface: false",
            "placement_authority: config/DISPATCH_POLICY.yaml",
            "surface_pool_is_selection_input_not_placement_authority: true",
            "default_model_is_preference_not_pin: true",
            "role_preferences_are_preferences_not_pins: true",
            "exact_task_or_owner_override_may_pin_exact_model: true",
            "one_model_pool_requires_no_special_routing_mode: true",
            "conversation_display_is_not_surface_or_model_authority: true",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.routing_text)
        self.assertIn("supported_surfaces:\n      - web\n      - agent", self.routing_text)
        self.assertIn("required_execution_surface_before_model_selection", self.dispatch_guide_text)
        self.assertIn("model_selection_inside_resolved_surface", self.dispatch_guide_text)
        pre_surface_constraints = self.dispatch["runtime_placement_policy"]["higher_precedence_constraints"]
        self.assertNotIn("model_qualification_and_material_suitability", pre_surface_constraints)
        self.assertFalse(any("model" in constraint for constraint in pre_surface_constraints))

    def test_local_policy_has_independent_web_and_agent_pool_contract(self):
        bindings = self.local_policy["model_bindings"]
        self.assertEqual(set(bindings), {
            "web",
            "agent",
            "ai_recommendation_allowed",
            "initial_or_material_change_requires_owner_confirmation",
        })
        for surface in ("web", "agent"):
            self.assertEqual(bindings[surface]["allowed_models"], [])
            self.assertIsNone(bindings[surface]["default_model"])
            self.assertEqual(bindings[surface]["role_preferences"], {
                "lead": None,
                "worker": None,
                "validator": None,
            })
        self.assertTrue(bindings["ai_recommendation_allowed"])
        self.assertTrue(bindings["initial_or_material_change_requires_owner_confirmation"])

    def test_registry_is_recommended_catalog_not_exhaustive_adopter_allowlist(self):
        required = (
            "purpose: recommended_and_validated_default_catalog",
            "exhaustive_adopter_allowlist: false",
            "local_custom_model_gains_central_status: false",
            "local_custom_model_gains_cross_project_evidence: false",
            "local_custom_model_auto_promotes_globally: false",
            "dispatch_or_execution_surface_authority: false",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.registry_text)

    def test_current_conformance_retains_runtime_hardening_tests_and_special_compliance_surface(self):
        paths = set(self.conformance["central_governance"]["required_paths"])
        self.assertIn("tests/test_runtime_placement_profiles.py", paths)
        self.assertIn("config/EXECUTOR_COMPLIANCE.yaml", paths)

    def test_release_identity_and_lprl_independence(self):
        self.assertEqual(self.release["ordinary_governance"]["version"], "0.3.27")
        self.assertEqual(
            self.release["ordinary_governance"]["change_class"],
            "governance_consistency_hardening",
        )
        binding_release = self.release["adopter_local_model_bindings"]
        self.assertEqual(binding_release["placement_owner"], "config/DISPATCH_POLICY.yaml")
        self.assertFalse(binding_release["surface_pool_is_placement_authority"])
        self.assertFalse(binding_release["central_registry_is_exhaustive_adopter_allowlist"])
        self.assertTrue(binding_release["initial_or_material_persisted_change_requires_owner_confirmation"])
        self.assertTrue(binding_release["formal_launch_requires_explicit_surface_and_local_policy"])
        lprl = self.release["modules"]["lprl"]
        self.assertEqual(lprl["version"], "0.2.5-pilot")
        self.assertFalse(lprl["semantic_change"])
        economy = self.release["execution_economy"]
        self.assertTrue(economy["runtime_mode_is_capability_defined_not_client_brand_defined"])
        self.assertTrue(economy["web_mode_requires_confirmed_github_repository_read_write"])
        self.assertTrue(economy["github_native_operations_are_not_agent_placement_triggers"])
        self.assertTrue(economy["remote_repository_ci_is_not_local_test_execution"])
        self.assertTrue(economy["external_owner_launch_is_provider_and_client_neutral"])
        self.assertTrue(economy["required_execution_surface_precedes_model_selection"])
        self.assertFalse(economy["external_transport_reclassifies_originating_runtime_profile"])
        self.assertFalse(
            economy["native_agent_cross_software_external_route_uses_web_external_placement"]
        )


if __name__ == "__main__":
    unittest.main()
