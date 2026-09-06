import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "templates" / "STARTUP_CARD_RENDER.py"
DEFAULT_LOCAL_POLICY = REPO / "templates" / "LOCAL_POLICY.yaml"
SPEC = importlib.util.spec_from_file_location("startup_card_render", SCRIPT)
RENDERER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDERER)


class StartupCardRendererTests(unittest.TestCase):
    TASK_REF = "github:owner/repo#102@5518486414"

    def decision(self, **overrides):
        value = {
            "role": "bounded_worker",
            "task_class": "bounded_code_edit",
            "risk_level": "medium",
            "authority_class": "production",
            "selected_model": "gpt-5.6-luna",
            "selected_reasoning": "high",
            "challenger_disposition": "deferred",
            "challenger_model": "gemini-3.8-flash",
            "challenger_evidence_strength": "insufficient",
            "challenger_defer_reason": "material_task_unsuitability",
        }
        value.update(overrides)
        return value

    def render(self, **overrides):
        values = {
            "task_ref": self.TASK_REF,
            "model": "gpt-5.6-luna",
            "reasoning": "high",
            "conversation": "current-session",
            "routing_decision": self.decision(),
            "execution_surface": "web",
            "local_policy_path": DEFAULT_LOCAL_POLICY,
        }
        values.update(overrides)
        return RENDERER.render_startup_card(**values)

    def local_policy(
        self,
        *,
        web_models=(),
        agent_models=(),
        web_default=None,
        agent_default=None,
        web_roles=None,
        agent_roles=None,
        ai_recommendation_allowed=True,
        owner_confirmation=True,
    ):
        web_roles = web_roles or {}
        agent_roles = agent_roles or {}

        def encoded_list(values):
            return "[" + ", ".join(json.dumps(value) for value in values) + "]"

        def scalar(value):
            return "null" if value is None else json.dumps(value)

        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        path = Path(tempdir.name) / "LOCAL_POLICY.yaml"
        path.write_text(
            "\n".join(
                [
                    'schema_version: "0.4"',
                    'project_name: "test"',
                    "model_bindings:",
                    "  web:",
                    f"    allowed_models: {encoded_list(web_models)}",
                    f"    default_model: {scalar(web_default)}",
                    "    role_preferences:",
                    f"      lead: {scalar(web_roles.get('lead'))}",
                    f"      worker: {scalar(web_roles.get('worker'))}",
                    f"      validator: {scalar(web_roles.get('validator'))}",
                    "  agent:",
                    f"    allowed_models: {encoded_list(agent_models)}",
                    f"    default_model: {scalar(agent_default)}",
                    "    role_preferences:",
                    f"      lead: {scalar(agent_roles.get('lead'))}",
                    f"      worker: {scalar(agent_roles.get('worker'))}",
                    f"      validator: {scalar(agent_roles.get('validator'))}",
                    f"  ai_recommendation_allowed: {str(ai_recommendation_allowed).lower()}",
                    "  initial_or_material_change_requires_owner_confirmation: "
                    f"{str(owner_confirmation).lower()}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def no_challenger(decision):
        return {
            **decision,
            "challenger_disposition": "not_applicable",
            "challenger_model": None,
            "challenger_evidence_strength": None,
            "challenger_defer_reason": None,
        }

    def test_valid_task_ref_and_display_order_are_deterministic(self):
        first = self.render(route="current_session", profile="balanced")
        second = self.render(route="native_dispatch", profile="native_delegate_preferred")
        self.assertEqual(first, second)
        self.assertEqual(first.splitlines()[:3], [
            "模型: gpt-5.6-luna",
            "思考等级: high",
            "对话: current-session",
        ])
        self.assertEqual(first.count("模型:"), 1)
        self.assertEqual(first.count("思考等级:"), 1)
        self.assertEqual(first.count("对话:"), 1)

    def test_whitespace_variation_is_normalised_without_semantic_change(self):
        self.assertEqual(
            self.render(model="  gpt-5.6-luna\n", conversation="  current-session  "),
            self.render(),
        )

    def test_launcher_is_one_thin_three_line_block(self):
        rendered = self.render()
        self.assertEqual(rendered.count("```text"), 1)
        self.assertEqual(rendered.count("```") , 2)
        launcher = rendered.split("```text\n", 1)[1].rsplit("\n```", 1)[0]
        self.assertEqual(launcher.splitlines(), [
            f"执行 {self.TASK_REF}；",
            "先读取该 Task，并按 Task 内引用读取关联事实；",
            "作为该 Task 的执行者执行，不接管项目 Lead。",
        ])
        self.assertNotIn("challenger", rendered)
        self.assertNotIn("task_class", rendered)

    def test_invalid_or_mutable_task_refs_fail_closed(self):
        invalid = [
            "github:owner/repo#102",
            "github:owner/repo#102@",
            "https://github.com/owner/repo/issues/102",
            "github:owner/repo#102@5518486414 extra",
            "github:owner/repo#0@5518486414",
        ]
        for task_ref in invalid:
            with self.subTest(task_ref=task_ref):
                with self.assertRaises(ValueError):
                    self.render(task_ref=task_ref)

    def test_display_inputs_do_not_change_launcher_authority(self):
        baseline = self.render()
        sol_decision = self.decision(
            role="core_implementation",
            task_class="core_implementation",
            risk_level="high",
            selected_model="gpt-5.6-sol",
            selected_reasoning="low",
        )
        changed = self.render(
            model="gpt-5.6-sol",
            reasoning="low",
            conversation="new-session",
            routing_decision=sol_decision,
        )
        self.assertEqual(baseline.split("\n\n", 1)[1], changed.split("\n\n", 1)[1])
        self.assertIn("模型: gpt-5.6-sol", changed)
        self.assertIn("思考等级: low", changed)

    def test_validator_role_changes_only_explicit_role_phrase(self):
        validator_decision = self.decision(
            role="validator",
            task_class="regression_validation",
        )
        worker = self.render()
        validator = self.render(role="independent_validator", routing_decision=validator_decision)
        self.assertEqual(worker.split("\n\n", 1)[0], validator.split("\n\n", 1)[0])
        self.assertIn("作为该 Task 的独立 Validator 执行，不接管项目 Lead。", validator)

    def test_reverse_validation_binds_all_resolved_inputs_and_rejects_tampering(self):
        rendered = self.render()
        cases = {
            "task-ref": {"task_ref": "github:owner/repo#103@5518486414"},
            "model": {"model": "other-model"},
            "reasoning": {"reasoning": "low"},
            "conversation": {"conversation": "other-session"},
            "role": {"role": "independent_validator"},
        }
        for name, overrides in cases.items():
            with self.subTest(name=name):
                values = {
                    "task_ref": self.TASK_REF,
                    "model": "gpt-5.6-luna",
                    "reasoning": "high",
                    "conversation": "current-session",
                    "role": "worker",
                }
                values.update(overrides)
                with self.assertRaises(ValueError):
                    RENDERER.validate_rendered_startup_card(rendered, **values)

        malformed = {
            "extra-formal-field": rendered.replace("对话: current-session\n\n", "对话: current-session\n角色: worker\n\n"),
            "reordered-formal-field": rendered.replace("模型: gpt-5.6-luna\n思考等级: high", "思考等级: high\n模型: gpt-5.6-luna"),
            "missing-formal-field": rendered.replace("对话: current-session\n", ""),
            "wrong-role-phrase": rendered.replace("执行者", "独立 Validator"),
            "missing-launcher-line": rendered.replace("先读取该 Task，并按 Task 内引用读取关联事实；\n", ""),
            "extra-launcher-line": rendered.replace("先读取该 Task，并按 Task 内引用读取关联事实；\n", "额外语义行\n先读取该 Task，并按 Task 内引用读取关联事实；\n"),
            "extra-fence": rendered + "\n```text\nextra\n```",
            "outer-wrapper": "```text\n" + rendered + "\n```",
            "leading-content": "前置内容\n" + rendered,
            "trailing-content": rendered + "\n尾部内容",
        }
        for candidate in malformed.values():
            with self.assertRaises(ValueError):
                RENDERER.validate_rendered_startup_card(
                    candidate,
                    task_ref=self.TASK_REF,
                    model="gpt-5.6-luna",
                    reasoning="high",
                    conversation="current-session",
                    role="worker",
                )

    def test_public_renderer_blocks_tampered_private_render_result(self):
        with mock.patch.object(
            RENDERER,
            "_render_startup_card",
            return_value="模型: tampered-model\n思考等级: high\n对话: current-session\n\n```text\n执行 github:owner/repo#102@5518486414；\n先读取该 Task，并按 Task 内引用读取关联事实；\n作为该 Task 的执行者执行，不接管项目 Lead。\n```",
        ):
            with self.assertRaises(ValueError):
                self.render()

    def test_formal_launch_requires_routing_decision_but_structural_probe_remains(self):
        with self.assertRaises(ValueError):
            RENDERER.render_startup_card(
                task_ref=self.TASK_REF,
                model="gpt-5.6-luna",
                reasoning="high",
                conversation="session",
            )
        probe = RENDERER.render_startup_card(
            task_ref="github:owner/repo#1@2",
            model="model",
            reasoning="high",
            conversation="session",
        )
        self.assertIn("模型: model", probe)

    def test_formal_launch_requires_explicit_surface_and_project_local_policy(self):
        with self.assertRaisesRegex(ValueError, "explicit already-resolved execution_surface"):
            self.render(execution_surface=None)
        with self.assertRaisesRegex(ValueError, "explicit project LOCAL_POLICY"):
            self.render(local_policy_path=None)

        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        missing_bindings = Path(tempdir.name) / "LOCAL_POLICY.yaml"
        missing_bindings.write_text('schema_version: "0.4"\nproject_name: "test"\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "model_bindings section is required"):
            self.render(local_policy_path=missing_bindings)

    def test_routing_decision_binds_model_reasoning_and_registry_ceiling(self):
        with self.assertRaises(ValueError):
            self.render(reasoning="medium")
        with self.assertRaises(ValueError):
            self.render(routing_decision=self.decision(risk_level="high"))
        with self.assertRaises(ValueError):
            self.render(routing_decision=self.decision(task_class="adversarial_verification"))

    def test_candidate_requires_explicit_challenger_accounting_and_no_production(self):
        candidate = self.decision(
            role="independent_evidence_validator",
            task_class="evidence_only_review",
            authority_class="qualification",
            selected_model="gemini-3.8-flash",
            challenger_disposition="selected",
            challenger_model="gemini-3.8-flash",
            challenger_defer_reason=None,
        )
        rendered = self.render(model="gemini-3.8-flash", routing_decision=candidate)
        self.assertIn("模型: gemini-3.8-flash", rendered)
        with self.assertRaises(ValueError):
            self.render(
                model="gemini-3.8-flash",
                routing_decision={**candidate, "authority_class": "production"},
            )
        with self.assertRaises(ValueError):
            self.render(routing_decision=self.decision(
                challenger_disposition="not_applicable",
                challenger_model=None,
                challenger_evidence_strength=None,
                challenger_defer_reason=None,
            ))

    def test_challenger_deferral_reuses_model_routing_reasons(self):
        self.render(routing_decision=self.decision(challenger_defer_reason="independence_conflict"))
        with self.assertRaises(ValueError):
            self.render(routing_decision=self.decision(challenger_defer_reason="prefer_incumbent"))

    def test_central_registered_model_launch_remains_conformant_with_empty_project_pool(self):
        rendered = self.render(conversation="新开 Web 对话")
        self.assertIn("模型: gpt-5.6-luna", rendered)
        self.assertIn("对话: 新开 Web 对话", rendered)

    def test_declared_local_custom_model_passes_without_central_registry_entry(self):
        custom_model = "owner-custom-worker-v1"
        self.assertNotIn(custom_model + ":", (REPO / "config" / "MODEL_REGISTRY.yaml").read_text(encoding="utf-8"))
        policy = self.local_policy(agent_models=[custom_model])
        decision = self.no_challenger(self.decision(selected_model=custom_model))
        rendered = self.render(
            model=custom_model,
            routing_decision=decision,
            execution_surface="agent",
            local_policy_path=policy,
            conversation="新开本地 Agent/Codex 对话",
        )
        self.assertIn(f"模型: {custom_model}", rendered)
        self.assertNotIn("preferred", rendered)
        self.assertNotIn("provisional", rendered)
        self.assertNotIn("candidate", rendered)

    def test_undeclared_noncentral_model_fails_closed(self):
        custom_model = "undeclared-custom-v1"
        decision = self.no_challenger(self.decision(selected_model=custom_model))
        with self.assertRaisesRegex(ValueError, "undeclared non-central"):
            self.render(model=custom_model, routing_decision=decision)

    def test_configured_surface_pool_blocks_out_of_pool_central_model(self):
        policy = self.local_policy(web_models=["gpt-5.6-luna"])
        sol_decision = self.no_challenger(self.decision(
            role="core_implementation",
            task_class="core_implementation",
            risk_level="high",
            selected_model="gpt-5.6-sol",
        ))
        with self.assertRaisesRegex(ValueError, "outside the configured execution-surface pool"):
            self.render(
                model="gpt-5.6-sol",
                routing_decision=sol_decision,
                execution_surface="web",
                local_policy_path=policy,
            )

    def test_surface_is_explicit_and_never_inferred_from_conversation_display(self):
        custom_model = "owner-agent-only-v1"
        policy = self.local_policy(web_models=["gpt-5.6-luna"], agent_models=[custom_model])
        decision = self.no_challenger(self.decision(selected_model=custom_model))
        rendered = self.render(
            model=custom_model,
            routing_decision=decision,
            execution_surface="agent",
            local_policy_path=policy,
            conversation="新开 Web 对话",
        )
        self.assertIn("对话: 新开 Web 对话", rendered)
        with self.assertRaisesRegex(ValueError, "outside the configured execution-surface pool"):
            self.render(
                model=custom_model,
                routing_decision=decision,
                execution_surface="web",
                local_policy_path=policy,
                conversation="新开本地 Agent/Codex 对话",
            )
        with self.assertRaisesRegex(ValueError, "explicit already-resolved execution_surface"):
            self.render(
                model=custom_model,
                routing_decision=decision,
                execution_surface=None,
                local_policy_path=policy,
                conversation="新开本地 Agent/Codex 对话",
            )

    def test_one_model_web_pool_needs_no_special_routing_mode(self):
        policy = self.local_policy(web_models=["gpt-5.6-luna"])
        decision = self.no_challenger(self.decision())
        first = self.render(
            routing_decision=decision,
            execution_surface="web",
            local_policy_path=policy,
            route="external_owner_launch",
        )
        second = self.render(
            routing_decision=decision,
            execution_surface="web",
            local_policy_path=policy,
            route="current_session",
        )
        self.assertEqual(first, second)
        self.assertIn("模型: gpt-5.6-luna", first)

    def test_multi_model_agent_pool_preferences_are_not_hard_pins(self):
        custom_model = "owner-custom-agent-v2"
        policy = self.local_policy(
            agent_models=["gpt-5.6-luna", custom_model],
            agent_default=custom_model,
            agent_roles={"worker": custom_model},
        )
        central_decision = self.no_challenger(self.decision())
        central = self.render(
            routing_decision=central_decision,
            execution_surface="agent",
            local_policy_path=policy,
        )
        custom_decision = self.no_challenger(self.decision(selected_model=custom_model))
        custom = self.render(
            model=custom_model,
            routing_decision=custom_decision,
            execution_surface="agent",
            local_policy_path=policy,
        )
        self.assertIn("模型: gpt-5.6-luna", central)
        self.assertIn(f"模型: {custom_model}", custom)

    def test_local_policy_rejects_preference_outside_nonempty_pool_and_owner_confirmation_false(self):
        outside = self.local_policy(
            web_models=["gpt-5.6-luna"],
            web_default="gpt-5.6-sol",
        )
        decision = self.no_challenger(self.decision())
        with self.assertRaisesRegex(ValueError, "preference is outside allowed_models"):
            self.render(
                routing_decision=decision,
                execution_surface="web",
                local_policy_path=outside,
            )

        unconfirmed = self.local_policy(
            web_models=["gpt-5.6-luna"],
            owner_confirmation=False,
        )
        with self.assertRaisesRegex(ValueError, "must require Owner confirmation"):
            self.render(
                routing_decision=decision,
                execution_surface="web",
                local_policy_path=unconfirmed,
            )

    def test_pre_freeze_regression_reuses_existing_routing_gate_for_182_v1(self):
        valid = {
            "role": "independent_evidence_validator",
            "task_class": "evidence_only_review",
            "risk_level": "medium",
            "authority_class": "production",
            "selected_model": "gemini-3.7-flash",
            "selected_reasoning": "high",
            "challenger_disposition": "deferred",
            "challenger_model": "gemini-3.8-flash",
            "challenger_evidence_strength": "insufficient",
            "challenger_defer_reason": "material_task_unsuitability",
        }
        RENDERER.validate_model_routing_decision(
            valid,
            model="gemini-3.7-flash",
            reasoning="high",
            execution_surface="web",
            local_policy_path=DEFAULT_LOCAL_POLICY,
        )

        malformed_v1 = {
            "basis": "accepted_core_0.3.25_model_routing_and_bootstrap_seed",
            "selected_model": "gemini-3.7-flash",
            "selected_reasoning": "high",
            "challenger_disposition": "not_applicable",
            "rationale": "different_model_family_when_practical_for_independent_validation",
        }
        with self.assertRaisesRegex(ValueError, "fields do not match"):
            RENDERER.validate_model_routing_decision(
                malformed_v1,
                model="gemini-3.7-flash",
                reasoning="high",
                execution_surface="web",
                local_policy_path=DEFAULT_LOCAL_POLICY,
            )

    def test_non_owner_launch_surfaces_delegate_to_canonical_renderer(self):
        paths = [
            REPO / "README.md",
            REPO / "templates" / "BOOTSTRAP.md",
        ]
        private_bootstrap = REPO / ".agent" / "BOOTSTRAP.md"
        if private_bootstrap.exists():
            paths.append(private_bootstrap)

        forbidden = (
            "执行 <exact Task ref>；",
            "只给 Owner 看的执行建议",
            "只有启动指令本身进入",
            "标准 Worker 骨架：",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(REPO))):
                self.assertIn("docs/task-package/TASK_PACKAGE_SPEC.md", text)
                self.assertIn("templates/STARTUP_CARD_RENDER.py", text)
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)

        if private_bootstrap.exists():
            self.assertNotIn(
                "accepted ordinary governance is `0.3.18`",
                private_bootstrap.read_text(encoding="utf-8"),
            )

    def test_cli_is_offline_standard_library_and_fail_closed(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("import socket", "import urllib", "import requests", "urlopen("):
            self.assertNotIn(forbidden, source)
        decision = json.dumps(self.decision(), separators=(",", ":"))
        common = [
            "--execution-surface",
            "web",
            "--local-policy",
            str(DEFAULT_LOCAL_POLICY),
        ]
        success = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--task-ref",
                self.TASK_REF,
                "--model",
                "gpt-5.6-luna",
                "--reasoning",
                "high",
                "--conversation",
                "session",
                "--routing-decision-json",
                decision,
                *common,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(success.returncode, 0)
        self.assertIn("模型: gpt-5.6-luna", success.stdout)
        failure = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--task-ref",
                "https://github.com/owner/repo/issues/102",
                "--model",
                "gpt-5.6-luna",
                "--reasoning",
                "high",
                "--conversation",
                "session",
                "--routing-decision-json",
                decision,
                *common,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(failure.returncode, 0)
        self.assertEqual(failure.stdout, "")


if __name__ == "__main__":
    unittest.main()
