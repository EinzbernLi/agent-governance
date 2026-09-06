#!/usr/bin/env python3
"""Offline, read-only governance conformance reference evaluator.

The loader intentionally implements only the repository's configuration YAML
subset. Unsupported YAML fails closed instead of being guessed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path


RESULT_SCHEMA = "0.2"
EVALUATOR_VERSION = "0.3.17"
OVERALL = {"CONFORMANT", "RECONCILIATION_REQUIRED", "BLOCKED"}
DRIFT = {"CONFORMANT", "DRIFT_RECONCILABLE", "DRIFT_BLOCKING"}

SEMANTIC_OWNER_KEYS = {
    "lead_core_responsibilities",
    "lead_continuity_and_takeover",
    "task_objective_scope_permissions_evidence_tests_result_contract",
    "dispatch_execution_economy_capability_route_and_delegated_observation",
    "runtime_profile_deltas",
    "worker_validator_role_coordination_and_parallel_role_boundaries",
    "model_qualification_and_routing",
    "lead_acceptance_and_independent_validation_disposition",
    "governance_currency_and_adoption",
    "conformance_and_local_action_evaluation_meaning",
    "local_action_authority",
    "lprl_independent_module_lifecycle",
    "formal_launcher_presentation",
    "release_identity_and_compatibility_metadata",
}
SURFACE_ROLES = {
    "README.md": "navigation_onboarding_non_authoritative",
    "config/CONFORMANCE_POLICY.yaml": "derived_verification_pointer_map_only",
    "docs/protocol/DISPATCH_ROUTING_PROTOCOL.md": "non_authoritative_reference_guide",
    "docs/protocol/SUBAGENT_RELIABILITY_PROTOCOL.md": "non_authoritative_principles_appendix",
}
KERNEL_INVARIANTS = {
    "github_repository_durable_authority",
    "one_active_lead_per_project",
    "task_scope_permission_boundaries",
    "owner_control_gates",
    "safety_and_fail_closed_behavior",
    "result_independent_validation_and_final_acceptance_boundaries",
    "takeover_activation_reconciliation_and_AWAIT_OWNER_CONTINUE",
    "accepted_governance_and_module_currency",
    "no_second_authority_store",
}
KERNEL_FORBIDDEN = {
    "runtime_execution_preferences",
    "client_presentation_details",
    "optional_lprl_rule_body",
    "local_action_specific_procedure",
    "release_only_procedure",
}
RUNTIME_PROFILE_FIELDS = {
    "execution_economy_profile",
    "direct_vs_delegate_preference_among_already_compliant_choices",
    "delegable_preparation_preference",
    "wait_or_transport_preference",
    "launcher_presentation_hint",
}
FORBIDDEN_RUNTIME_OVERRIDES = {
    "task_authority_or_scope",
    "owner_authorization_or_continue_requirements",
    "permissions",
    "safety_or_fail_closed_behavior",
    "lead_identity_or_uniqueness",
    "result_validator_or_acceptance_authority",
    "independent_validation_requirement",
    "takeover_AWAIT_OWNER_CONTINUE",
    "governance_or_module_pin_authority",
    "conformance_result_meaning",
}
COLD_PATHS = {
    "takeover_recovery": ("takeover_or_recovery", "docs/context-continuity/TAKEOVER_RECONCILIATION_GATE.md"),
    "conformance": ("accepted_bounded_conformance_gate", "docs/conformance/GOVERNANCE_CONFORMANCE_PROTOCOL.md"),
    "local_action": ("explicit_local_action_request", "docs/conformance/GOVERNANCE_CONFORMANCE_PROTOCOL.md"),
    "lprl": ("accepted_lprl_pin_and_task_requires_lprl_semantics", "modules/local-resource-lifecycle"),
    "independent_validator": ("task_requires_independent_validation", "docs/acceptance/LEAD_CONTROLLER_ACCEPTANCE_PROTOCOL.md"),
    "release_acceptance": ("governance_release_or_currency_relevant_acceptance", "docs/acceptance/LEAD_CONTROLLER_ACCEPTANCE_PROTOCOL.md"),
}
PRECEDENCE_ORDER = [
    "accepted_main_and_release_baseline",
    "canonical_lead_sink_continuity",
    "exact_frozen_task_revision",
    "protected_or_forbidden_older_work_excluded",
]
LOCAL_MATERIALIZATION_TRIGGERS = {
    "local_checkout_required",
    "local_file_read_or_write_required",
    "local_workspace_or_worktree_required",
    "local_software_or_runtime_required",
    "local_test_execution_required",
    "local_artifact_generation_or_validation_required",
}
REMOTE_ONLY_WORK = {
    "github_durable_fact_read",
    "remote_authority_reconciliation",
    "governance_judgment",
    "issue_or_pr_review_without_local_checkout",
    "remote_documentation_or_evidence_review",
}
PLACEMENT_HIGHER_PRECEDENCE = {
    "explicit_task_executor_or_role_requirement",
    "independent_validation_or_evidence_isolation",
    "safety_permission_and_forbidden_boundaries",
    "proven_runtime_capability",
    "task_specific_software_or_artifact_requirement",
}
CODEX_DELEGATION_BENEFITS = {
    "sol_or_terra_quota_preservation",
    "context_isolation",
    "elapsed_time_reduction",
    "specialization",
}
RUNNING_TASK_BINDING_RULES = {
    "activation_binds_exact_task_revision": True,
    "same_issue_later_revision_is_in_place_contract_update": False,
    "task_publication_is_activation_or_reanchor": False,
    "later_durable_facts_may_be_read_without_authority_adoption": True,
    "material_later_authority_without_reanchor_action": "NEEDS_ATTENTION_OR_REANCHOR_REQUIRED",
    "material_execution_under_later_revision_without_reanchor_allowed": False,
    "authorized_reanchor_requires": "explicit_route_appropriate_activation_or_reanchor_evidence",
    "internal_child_binding": "parent_exact_activated_task_revision",
    "lead_publication_implies_running_external_worker_adoption": False,
    "lead_result_interpretation_basis": "executed_exact_task_revision",
}
RUNNING_TASK_RESULT_FIELDS = {
    "executed_exact_task_ref",
    "reanchor_used",
    "reanchor_from_ref",
    "reanchor_to_ref",
    "reanchor_evidence_ref",
}
RUNNING_TASK_FIXTURE_NAMES = {
    "web_no_reanchor",
    "codex_no_reanchor",
    "material_conflict_without_reanchor",
    "authorized_reanchor",
    "child_cannot_expand_parent",
}
RUNNING_TASK_FIXTURE_KEYS = {
    "runtime",
    "activated_task_ref",
    "observed_later_task_ref",
    "later_revision_material_to_running_contract",
    "reanchor_authorized",
    "reanchor_from_ref",
    "reanchor_to_ref",
    "reanchor_evidence_ref",
    "expected_selected_task_ref",
    "expected_action",
}
LEAD_CORE_RESPONSIBILITY_KEYS = {
    "architecture",
    "task_decomposition_freeze",
    "scope_permission_high_risk",
    "worker_validator_coordination",
    "sibling_integration",
    "exception_reanchor_replan",
    "final_acceptance",
}
LEAD_CORE_DELEGATION_KEYS = {
    "bounded",
    "authority_transfer",
    "preference_only",
}
LEAD_CORE_ROLE_BOUNDARY_KEYS = {"forbidden_worker_child_authority"}


class ConformanceError(RuntimeError):
    pass


def _strip_comment(text):
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "#" and quote is None:
            return text[:index].rstrip()
    if quote is not None:
        raise ConformanceError("unterminated quoted scalar")
    return text.rstrip()


def _split_key(text):
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == ":" and quote is None:
            return text[:index].strip(), text[index + 1 :].strip()
    raise ConformanceError(f"mapping entry lacks colon: {text!r}")


def _split_inline_list(text):
    values = []
    quote = None
    escaped = False
    start = 0
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "," and quote is None:
            values.append(text[start:index].strip())
            start = index + 1
    values.append(text[start:].strip())
    return [] if values == [""] else values


def _scalar(text):
    if text in {"|", ">"}:
        raise ConformanceError("block scalars are outside the supported YAML subset")
    if text.startswith(("&", "*", "!")):
        raise ConformanceError("anchors, aliases and tags are outside the supported YAML subset")
    if text.startswith('"'):
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConformanceError(f"invalid quoted scalar: {exc}") from exc
        if not isinstance(value, str):
            raise ConformanceError("double-quoted YAML scalar must decode to string")
        return value
    if text.startswith("'"):
        if len(text) < 2 or not text.endswith("'"):
            raise ConformanceError("invalid single-quoted scalar")
        return text[1:-1].replace("''", "'")
    if text.startswith("["):
        if not text.endswith("]"):
            raise ConformanceError("unterminated inline list")
        return [_scalar(item) for item in _split_inline_list(text[1:-1])]
    lowered = text.lower()
    if lowered in {"null", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"-?(0|[1-9][0-9]*)", text):
        return int(text)
    if re.fullmatch(r"-?(0|[1-9][0-9]*)\.[0-9]+", text):
        return float(text)
    if any(token in text for token in ("{", "}")):
        raise ConformanceError("inline mappings are outside the supported YAML subset")
    return text


def load_yaml_subset(path):
    try:
        raw = Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ConformanceError(f"cannot read {path}: {exc}") from exc
    lines = []
    for number, raw_line in enumerate(raw.splitlines(), 1):
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise ConformanceError(f"{path}:{number}: tab indentation is forbidden")
        text = _strip_comment(raw_line)
        if not text.strip():
            continue
        indent = len(text) - len(text.lstrip(" "))
        if indent % 2:
            raise ConformanceError(f"{path}:{number}: indentation must use two-space levels")
        lines.append((indent, text.strip(), number))
    if not lines:
        raise ConformanceError(f"{path}: empty YAML document")

    def parse_block(index, indent):
        if index >= len(lines) or lines[index][0] != indent:
            raise ConformanceError(f"{path}: malformed indentation")
        is_list = lines[index][1].startswith("- ") or lines[index][1] == "-"
        value = [] if is_list else {}
        while index < len(lines):
            current_indent, text, number = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise ConformanceError(f"{path}:{number}: unexpected indentation")
            if is_list:
                if not (text.startswith("- ") or text == "-"):
                    raise ConformanceError(f"{path}:{number}: mixed list and mapping block")
                item = text[1:].strip()
                if not item:
                    if index + 1 >= len(lines) or lines[index + 1][0] <= indent:
                        raise ConformanceError(f"{path}:{number}: empty list item")
                    child, index = parse_block(index + 1, lines[index + 1][0])
                    value.append(child)
                else:
                    if ":" in item and not item.startswith(('"', "'")):
                        raise ConformanceError(
                            f"{path}:{number}: list mappings are outside the supported YAML subset"
                        )
                    value.append(_scalar(item))
                    index += 1
            else:
                if text.startswith("-"):
                    raise ConformanceError(f"{path}:{number}: mixed mapping and list block")
                key, rest = _split_key(text)
                if not key:
                    raise ConformanceError(f"{path}:{number}: empty mapping key")
                if key in value:
                    raise ConformanceError(f"{path}:{number}: duplicate key {key!r}")
                if rest:
                    value[key] = _scalar(rest)
                    index += 1
                elif index + 1 < len(lines) and lines[index + 1][0] > indent:
                    child_indent = lines[index + 1][0]
                    if child_indent != indent + 2:
                        raise ConformanceError(f"{path}:{number}: indentation jumped more than one level")
                    value[key], index = parse_block(index + 1, child_indent)
                else:
                    value[key] = None
                    index += 1
        return value, index

    document, consumed = parse_block(0, lines[0][0])
    if consumed != len(lines):
        raise ConformanceError(f"{path}: trailing unparsed YAML")
    if not isinstance(document, dict):
        raise ConformanceError(f"{path}: top-level mapping required")
    return document


def sha256_path(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested(mapping, *keys, default=None):
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def is_nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def running_task_revision_decision(facts):
    """Select a running contract from exact refs without consulting Issue order."""
    activated = facts.get("activated_task_ref")
    observed_later = facts.get("observed_later_task_ref")
    from_ref = facts.get("reanchor_from_ref")
    to_ref = facts.get("reanchor_to_ref")
    evidence_ref = facts.get("reanchor_evidence_ref")
    authorized = facts.get("reanchor_authorized") is True
    reanchor_fields_present = any(is_nonempty(value) for value in (from_ref, to_ref, evidence_ref))
    valid_reanchor = (
        authorized
        and is_nonempty(activated)
        and is_nonempty(observed_later)
        and from_ref == activated
        and to_ref == observed_later
        and is_nonempty(evidence_ref)
    )
    if valid_reanchor:
        return {
            "selected_task_ref": to_ref,
            "action": "CONTINUE_REANCHORED_EXACT_REVISION",
        }
    if authorized or reanchor_fields_present or facts.get("later_revision_material_to_running_contract") is True:
        return {
            "selected_task_ref": activated,
            "action": "NEEDS_ATTENTION_OR_REANCHOR_REQUIRED",
        }
    return {
        "selected_task_ref": activated,
        "action": "CONTINUE_PINNED_EXACT_REVISION",
    }


class Evaluation:
    def __init__(self, mode):
        self.mode = mode
        self.findings = []
        self.advisories = []
        self.authorities = {}
        self.update_available = False
        self.metrics = {}
        self.local_action = {"requested": False, "decision": "NOT_REQUESTED", "reasons": []}

    def add_authority(self, ref, identity):
        self.authorities[str(ref)] = str(identity)

    def finding(self, code, severity, authority_ref, explanation):
        self.findings.append(
            {
                "code": code,
                "severity": severity,
                "authority_ref": str(authority_ref),
                "explanation": explanation,
            }
        )

    def block(self, code, authority_ref, explanation):
        self.finding(code, "required_block", authority_ref, explanation)

    def reconcile(self, code, authority_ref, explanation):
        self.finding(code, "reconciliation", authority_ref, explanation)

    def result(self):
        severities = {item["severity"] for item in self.findings}
        if "required_block" in severities:
            overall, drift = "BLOCKED", "DRIFT_BLOCKING"
        elif "reconciliation" in severities:
            overall, drift = "RECONCILIATION_REQUIRED", "DRIFT_RECONCILABLE"
        else:
            overall, drift = "CONFORMANT", "CONFORMANT"
        findings = sorted(self.findings, key=lambda item: (item["code"], item["authority_ref"]))
        authorities = [
            {"ref": ref, "digest_or_exact_identity": identity}
            for ref, identity in sorted(self.authorities.items())
        ]
        return {
            "schema_version": RESULT_SCHEMA,
            "evaluator_version": EVALUATOR_VERSION,
            "mode": self.mode,
            "evaluated_authorities": authorities,
            "overall_status": overall,
            "internal_drift": drift,
            "update_available": bool(self.update_available),
            "findings": findings,
            "advisories": sorted(set(self.advisories)),
            "metrics": dict(sorted(self.metrics.items())),
            "local_action": self.local_action,
        }


def confined_path(root, relative, evaluation, ref):
    if not is_nonempty(relative):
        evaluation.block("PATH_REQUIRED", ref, "An explicit relative path is required.")
        return None
    candidate = Path(relative)
    if candidate.is_absolute():
        evaluation.block("RELATIVE_PATH_REQUIRED", ref, "Authority paths must be relative to the explicit root.")
        return None
    resolved = (root / candidate).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        evaluation.block("PATH_OUTSIDE_ROOT", ref, "Authority path resolves outside the explicit root.")
        return None
    return resolved


def git_identity(root, evaluation):
    values = []
    for revision in ("HEAD", "HEAD^{tree}"):
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "rev-parse", revision],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            evaluation.block("GIT_IDENTITY_UNAVAILABLE", str(root), f"Cannot resolve local {revision}: {exc}")
            return None, None
        values.append(completed.stdout.strip())
    evaluation.add_authority("git:HEAD", values[0])
    evaluation.add_authority("git:HEAD^{tree}", values[1])
    try:
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        evaluation.block("GIT_STATUS_UNAVAILABLE", str(root), f"Cannot verify candidate worktree: {exc}")
    else:
        if status:
            evaluation.block("CANDIDATE_WORKTREE_DIRTY", "git:worktree", "Exact candidate evaluation requires a clean worktree.")
    return values


def canonical_git_blob_size(root, commit, relative, evaluation):
    """Return the committed blob size for an exact path, or fail closed."""
    if not is_nonempty(commit):
        evaluation.block(
            "HOT_PATH_CANONICAL_BLOB_UNAVAILABLE",
            relative,
            "Exact candidate commit is required for canonical hot-path measurement.",
        )
        return None
    git_relative = Path(relative).as_posix()
    try:
        object_id = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", f"{commit}:{git_relative}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        object_type = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-t", object_id],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        object_size = int(
            subprocess.run(
                ["git", "-C", str(root), "cat-file", "-s", object_id],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
        )
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        evaluation.block(
            "HOT_PATH_CANONICAL_BLOB_UNAVAILABLE",
            relative,
            f"Cannot resolve canonical blob bytes at exact commit {commit}: {exc}",
        )
        return None
    if object_type != "blob" or object_size < 0:
        evaluation.block(
            "HOT_PATH_CANONICAL_BLOB_INVALID",
            relative,
            "Declared hot-path surface must resolve to a committed Git blob with a valid size.",
        )
        return None
    evaluation.add_authority(f"git-blob:{relative}", f"{object_id}:{object_size}")
    return object_size


def exact_mapping(mapping, expected_keys, evaluation, ref):
    if not isinstance(mapping, dict):
        evaluation.block("POLICY_MAPPING_REQUIRED", ref, "An exact mapping is required.")
        return {}
    observed = set(mapping)
    missing = sorted(set(expected_keys) - observed)
    unknown = sorted(observed - set(expected_keys))
    if missing:
        evaluation.block("POLICY_REQUIRED_KEY_MISSING", ref, f"Missing keys: {', '.join(missing)}")
    if unknown:
        evaluation.block("POLICY_UNKNOWN_KEY", ref, f"Unknown keys: {', '.join(unknown)}")
    return mapping


def exact_set(value, expected, evaluation, ref):
    if not isinstance(value, list):
        evaluation.block("POLICY_LIST_REQUIRED", ref, "An exact list is required.")
        return set()
    observed = set(value)
    if len(value) != len(observed) or observed != set(expected):
        evaluation.block("POLICY_EXACT_SET_MISMATCH", ref, "List contains missing, unknown or duplicate values.")
    return observed


def validate_lead_core_contract(dispatch, evaluation):
    contract = exact_mapping(
        dispatch.get("lead_core_responsibilities"),
        {
            "owner",
            "one_active_lead",
            "runtime_independent",
            "lead_retains_terminal_accountability",
            "responsibilities",
            "delegation",
            "forbidden_worker_child_authority",
            "labels_not_capability_proof",
        },
        evaluation,
        "lead_core_responsibilities",
    )
    if contract.get("owner") != "config/DISPATCH_POLICY.yaml":
        evaluation.block("LEAD_CORE_OWNER_INVALID", "lead_core_responsibilities.owner", "Lead core must have one canonical Dispatch Policy owner.")
    for field in ("one_active_lead", "runtime_independent"):
        if contract.get(field) is not True:
            evaluation.block("LEAD_CORE_INVARIANT_INVALID", f"lead_core_responsibilities.{field}", "Lead core authority and one-Lead invariants must be true.")
    if contract.get("lead_retains_terminal_accountability") is not True:
        evaluation.block("LEAD_CORE_ACCOUNTABILITY_INVALID", "lead_core_responsibilities.lead_retains_terminal_accountability", "Delegation must never transfer the active Project Lead's terminal accountability.")
    exact_set(contract.get("responsibilities"), LEAD_CORE_RESPONSIBILITY_KEYS, evaluation, "lead_core_responsibilities.responsibilities")
    delegation = exact_mapping(
        contract.get("delegation"),
        LEAD_CORE_DELEGATION_KEYS,
        evaluation,
        "lead_core_responsibilities.delegation",
    )
    if delegation.get("bounded") is not True or delegation.get("preference_only") is not True:
        evaluation.block("LEAD_CORE_DELEGATION_BOUNDARY_INVALID", "lead_core_responsibilities.delegation", "Delegation must remain bounded and profile changes must remain preference-only.")
    if delegation.get("authority_transfer") is not False:
        evaluation.block("LEAD_CORE_DELEGATION_BOUNDARY_INVALID", "lead_core_responsibilities.delegation", "Delegation must not transfer Lead authority or terminal accountability.")
    exact_set(contract.get("forbidden_worker_child_authority"), {"claim_project_lead", "integrate_siblings", "final_acceptance"}, evaluation, "lead_core_responsibilities.forbidden_worker_child_authority")
    if contract.get("labels_not_capability_proof") is not True:
        evaluation.block("LEAD_CORE_CAPABILITY_BOUNDARY_INVALID", "lead_core_responsibilities.capability_boundary", "Runtime labels must not prove capability.")


def validate_startup_card_shape(rendered, task_ref, role, display_fields, semantic_line_count):
    """Validate the complete formal card shape independently of the renderer."""

    if role not in {"worker", "independent_validator"}:
        raise ValueError("unsupported startup-card role")
    if not isinstance(rendered, str):
        raise ValueError("startup card must be text")
    if not isinstance(task_ref, str) or not task_ref:
        raise ValueError("startup card task reference must be non-empty")
    if tuple(display_fields) != ("模型", "思考等级", "对话"):
        raise ValueError("startup card display fields are not canonical")
    if semantic_line_count != 3:
        raise ValueError("startup launcher must contain three semantic lines")
    role_phrase = (
        "作为该 Task 的执行者执行，不接管项目 Lead。"
        if role == "worker"
        else "作为该 Task 的独立 Validator 执行，不接管项目 Lead。"
    )
    if rendered != rendered.strip() or "\r" in rendered:
        raise ValueError("startup card has surrounding or carriage-return content")
    lines = rendered.split("\n")
    if len(lines) != 9:
        raise ValueError("startup card must contain exactly nine lines")
    formal = []
    for line in lines[:3]:
        match = re.fullmatch(r"([^:]+): (.+)", line)
        if not match:
            raise ValueError("startup card formal fields are malformed")
        formal.append((match.group(1), match.group(2)))
    if [field for field, _ in formal] != list(display_fields):
        raise ValueError("startup card formal fields are missing or reordered")
    if dict(formal) != {"模型": "model", "思考等级": "high", "对话": "session"}:
        raise ValueError("startup card formal values are invalid")
    if lines[3] != "" or lines[4] != "```text" or lines[8] != "```":
        raise ValueError("startup card fence structure is invalid")
    if rendered.count("```") != 2 or rendered.count("```text") != 1:
        raise ValueError("startup card must contain exactly one text fence")
    if lines[5] != f"执行 {task_ref}；":
        raise ValueError("startup card task reference differs from the expected exact ref")
    if lines[6] != "先读取该 Task，并按 Task 内引用读取关联事实；" or lines[7] != role_phrase:
        raise ValueError("startup card launcher semantics are invalid")


def validate_startup_renderer_contract(root, presentation, evaluation):
    renderer_path = confined_path(root, presentation.get("renderer_path"), evaluation, "presentation.renderer_path")
    if not renderer_path or not renderer_path.is_file():
        evaluation.block("STARTUP_RENDERER_MISSING", "presentation.renderer_path", "The canonical Startup Card Renderer is required.")
        return
    try:
        spec = importlib.util.spec_from_file_location("startup_card_renderer", renderer_path)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        if tuple(renderer.DISPLAY_FIELDS) != tuple(presentation.get("startup_card_display_fields")):
            evaluation.block("STARTUP_RENDERER_CONSTANTS_INVALID", "presentation.startup_card_display_fields", "Renderer display fields differ from the canonical presentation contract.")
        if renderer.STANDARD_LAUNCHER_SEMANTIC_LINES != presentation.get("standard_launcher_semantic_lines"):
            evaluation.block("STARTUP_RENDERER_CONSTANTS_INVALID", "presentation.standard_launcher_semantic_lines", "Renderer launcher line count differs from the canonical presentation contract.")
        if not callable(getattr(renderer, presentation.get("reverse_validator_api"))):
            evaluation.block("STARTUP_RENDERER_GATE_MISSING", "presentation.reverse_validator_api", "The public renderer must expose the structural reverse validator.")
        exact_task_ref = "github:owner/repo#1@2"
        for role in ("worker", "independent_validator"):
            rendered = renderer.render_startup_card(
                task_ref=exact_task_ref,
                model="model",
                reasoning="high",
                conversation="session",
                role=role,
            )
            renderer.validate_rendered_startup_card(
                rendered,
                task_ref=exact_task_ref,
                model="model",
                reasoning="high",
                conversation="session",
                role=role,
            )
            try:
                validate_startup_card_shape(
                    rendered,
                    exact_task_ref,
                    role,
                    presentation.get("startup_card_display_fields"),
                    presentation.get("standard_launcher_semantic_lines"),
                )
            except ValueError as exc:
                evaluation.block("STARTUP_RENDERER_OUTPUT_INVALID", f"presentation.{role}", str(exc))
    except (AttributeError, ImportError, OSError, TypeError, ValueError) as exc:
        evaluation.block("STARTUP_RENDERER_INVALID", "presentation.renderer_path", f"Renderer contract could not be evaluated: {exc}")


def validate_policy_contract(root, policy, evaluation):
    semantic = exact_mapping(
        policy.get("semantic_authority"),
        {"owners", "surface_roles"},
        evaluation,
        "semantic_authority",
    )
    owners = exact_mapping(semantic.get("owners"), SEMANTIC_OWNER_KEYS, evaluation, "semantic_authority.owners")
    for semantic_name, owner in owners.items():
        if not is_nonempty(owner):
            evaluation.block("SEMANTIC_OWNER_INVALID", f"semantic_authority.owners.{semantic_name}", "One canonical owner is required.")
    roles = exact_mapping(semantic.get("surface_roles"), SURFACE_ROLES, evaluation, "semantic_authority.surface_roles")
    for path, role in SURFACE_ROLES.items():
        if roles.get(path) != role:
            evaluation.block("SURFACE_ROLE_MISMATCH", f"semantic_authority.surface_roles.{path}", "Surface role differs from the canonical consolidation contract.")

    kernel = exact_mapping(policy.get("shared_kernel"), {"implementation", "invariants", "forbidden_contents"}, evaluation, "shared_kernel")
    if kernel.get("implementation") != "references_to_canonical_owners_only":
        evaluation.block("KERNEL_IMPLEMENTATION_INVALID", "shared_kernel.implementation", "Kernel must remain a reference manifest, not a new authority file.")
    exact_set(kernel.get("invariants"), KERNEL_INVARIANTS, evaluation, "shared_kernel.invariants")
    exact_set(kernel.get("forbidden_contents"), KERNEL_FORBIDDEN, evaluation, "shared_kernel.forbidden_contents")

    boundary = exact_mapping(
        policy.get("runtime_override_boundary"),
        {"allowlist", "forbidden", "unknown_or_forbidden_override_action"},
        evaluation,
        "runtime_override_boundary",
    )
    exact_set(boundary.get("allowlist"), RUNTIME_PROFILE_FIELDS, evaluation, "runtime_override_boundary.allowlist")
    exact_set(boundary.get("forbidden"), FORBIDDEN_RUNTIME_OVERRIDES, evaluation, "runtime_override_boundary.forbidden")
    if boundary.get("unknown_or_forbidden_override_action") != "fail_closed":
        evaluation.block("RUNTIME_OVERRIDE_NOT_FAIL_CLOSED", "runtime_override_boundary", "Unknown or forbidden overrides must fail closed.")

    dispatch_path = confined_path(root, "config/DISPATCH_POLICY.yaml", evaluation, "runtime_profiles")
    try:
        dispatch = load_yaml_subset(dispatch_path) if dispatch_path and dispatch_path.is_file() else {}
    except ConformanceError as exc:
        evaluation.block("DISPATCH_POLICY_INVALID", "config/DISPATCH_POLICY.yaml", str(exc))
        dispatch = {}
    validate_lead_core_contract(dispatch, evaluation)
    runtime = exact_mapping(
        dispatch.get("runtime_profiles"),
        {"mode", "capability_probe_outranks_profile_or_client_label", "full_core_copies_allowed", "profiles"},
        evaluation,
        "runtime_profiles",
    )
    if runtime.get("mode") != "delta_only" or runtime.get("full_core_copies_allowed") is not False:
        evaluation.block("RUNTIME_PROFILES_NOT_DELTA_ONLY", "runtime_profiles", "Runtime profiles must be delta-only and may not copy the core.")
    if runtime.get("capability_probe_outranks_profile_or_client_label") is not True:
        evaluation.block("CAPABILITY_PROFILE_PRECEDENCE_INVALID", "runtime_profiles", "Capability probe must outrank every runtime label/profile.")
    profiles = exact_mapping(runtime.get("profiles"), {"web_interactive", "codex_native_subagents", "generic"}, evaluation, "runtime_profiles.profiles")
    full_core_copies = 0
    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            evaluation.block("RUNTIME_PROFILE_INVALID", f"runtime_profiles.profiles.{name}", "Profile must be a delta mapping.")
            continue
        unknown = sorted(set(profile) - RUNTIME_PROFILE_FIELDS)
        if unknown:
            full_core_copies += 1
            evaluation.block("RUNTIME_PROFILE_OVERRIDE_FORBIDDEN", f"runtime_profiles.profiles.{name}", f"Unknown/forbidden override fields: {', '.join(unknown)}")
        if profile.get("execution_economy_profile") not in {"lead_direct_preferred", "native_delegate_preferred", "balanced"}:
            evaluation.block("RUNTIME_PROFILE_ECONOMY_INVALID", f"runtime_profiles.profiles.{name}", "Known execution-economy profile required.")

    economy = dispatch.get("execution_economy") if isinstance(dispatch.get("execution_economy"), dict) else {}
    economy_profiles = economy.get("profiles") if isinstance(economy.get("profiles"), dict) else {}
    native_profile = economy_profiles.get("native_delegate_preferred") if isinstance(economy_profiles.get("native_delegate_preferred"), dict) else {}
    if native_profile.get("lead_core_responsibilities_ref") != "lead_core_responsibilities":
        evaluation.block("LEAD_CORE_REFERENCE_INVALID", "execution_economy.profiles.native_delegate_preferred", "Native delegation must reference the canonical Lead core contract.")
    if "preserve_lead_for" in native_profile:
        evaluation.block("LEAD_CORE_DUPLICATED", "execution_economy.profiles.native_delegate_preferred.preserve_lead_for", "Runtime economy profiles must not duplicate Lead responsibilities.")

    placement = exact_mapping(
        dispatch.get("runtime_placement_policy"),
        {"purpose", "local_materialization_required", "no_local_materialization_required", "higher_precedence_constraints", "placement_is_execution_preference_not_authority", "placement_may_change_task_scope_or_permissions"},
        evaluation,
        "runtime_placement_policy",
    )
    if placement.get("purpose") != "choose_required_execution_surface_before_execution_economy_tiebreaks":
        evaluation.block("RUNTIME_PLACEMENT_PURPOSE_INVALID", "runtime_placement_policy.purpose", "Placement must resolve required surface before economy tiebreaks.")
    local_placement = exact_mapping(
        placement.get("local_materialization_required"),
        {"triggers", "preferred_surface", "policy", "web_exception_requires_bounded_reason"},
        evaluation,
        "runtime_placement_policy.local_materialization_required",
    )
    exact_set(local_placement.get("triggers"), LOCAL_MATERIALIZATION_TRIGGERS, evaluation, "runtime_placement_policy.local_materialization_required.triggers")
    if local_placement.get("preferred_surface") != "codex" or local_placement.get("policy") != "codex_required_by_default" or local_placement.get("web_exception_requires_bounded_reason") is not True:
        evaluation.block("LOCAL_PLACEMENT_INVALID", "runtime_placement_policy.local_materialization_required", "Local materialization must default to Codex; Web exception needs a bounded reason.")
    remote_placement = exact_mapping(
        placement.get("no_local_materialization_required"),
        {"preferred_surface", "policy", "representative_work"},
        evaluation,
        "runtime_placement_policy.no_local_materialization_required",
    )
    exact_set(remote_placement.get("representative_work"), REMOTE_ONLY_WORK, evaluation, "runtime_placement_policy.no_local_materialization_required.representative_work")
    if remote_placement.get("preferred_surface") != "web" or remote_placement.get("policy") != "web_preferred":
        evaluation.block("REMOTE_PLACEMENT_INVALID", "runtime_placement_policy.no_local_materialization_required", "Remote-only work must prefer Web.")
    exact_set(placement.get("higher_precedence_constraints"), PLACEMENT_HIGHER_PRECEDENCE, evaluation, "runtime_placement_policy.higher_precedence_constraints")
    if placement.get("placement_is_execution_preference_not_authority") is not True or placement.get("placement_may_change_task_scope_or_permissions") is not False:
        evaluation.block("RUNTIME_PLACEMENT_AUTHORITY_INVALID", "runtime_placement_policy", "Placement is preference only and cannot change scope/permissions.")

    delegation_expected_keys = {
        "applies_when",
        "default_allowed",
        "child_use_optional",
        "valid_material_benefits",
        "cheaper_child_must_be_qualified_for_actual_subproblem_and_risk",
        "parent_worker_retains_scope_permission_integration_and_terminal_result_accountability",
        "child_may_expand_scope_permissions_forbidden_boundary_or_result_sink",
        "child_review_counts_as_independent_validation",
        "child_write_ownership_required",
        "parallel_child_writes_require_pairwise_disjoint_scope",
        "overlapping_child_writes_action",
        "child_recursive_delegation_default",
        "uncontrolled_recursive_agent_tree_allowed",
        "ordinary_success_requires_full_child_transcript_or_hidden_identity_chain",
    }
    delegation = exact_mapping(dispatch.get("codex_worker_native_delegation"), delegation_expected_keys, evaluation, "codex_worker_native_delegation")
    exact_set(delegation.get("applies_when"), {"assigned_execution_surface_is_codex", "native_child_capability_is_proven"}, evaluation, "codex_worker_native_delegation.applies_when")
    exact_set(delegation.get("valid_material_benefits"), CODEX_DELEGATION_BENEFITS, evaluation, "codex_worker_native_delegation.valid_material_benefits")
    required_true = {
        "default_allowed",
        "child_use_optional",
        "cheaper_child_must_be_qualified_for_actual_subproblem_and_risk",
        "parent_worker_retains_scope_permission_integration_and_terminal_result_accountability",
        "child_write_ownership_required",
        "parallel_child_writes_require_pairwise_disjoint_scope",
    }
    required_false = {
        "child_may_expand_scope_permissions_forbidden_boundary_or_result_sink",
        "child_review_counts_as_independent_validation",
        "child_recursive_delegation_default",
        "uncontrolled_recursive_agent_tree_allowed",
        "ordinary_success_requires_full_child_transcript_or_hidden_identity_chain",
    }
    for field in required_true:
        if delegation.get(field) is not True:
            evaluation.block("CODEX_DELEGATION_BOUNDARY_INVALID", f"codex_worker_native_delegation.{field}", "Required Codex delegation/accountability fact must be true.")
    for field in required_false:
        if delegation.get(field) is not False:
            evaluation.block("CODEX_DELEGATION_BOUNDARY_INVALID", f"codex_worker_native_delegation.{field}", "Forbidden Codex delegation behavior must remain false.")
    if delegation.get("overlapping_child_writes_action") != "serialize_or_fail":
        evaluation.block("CODEX_CHILD_WRITE_CONFLICT_INVALID", "codex_worker_native_delegation.overlapping_child_writes_action", "Overlapping child writes must serialize or fail.")

    cold = exact_mapping(
        policy.get("cold_path_manifest"),
        {"mode", "triggers_from_durable_facts_only", "categories", "dynamic_loader_registry_or_daemon_allowed"},
        evaluation,
        "cold_path_manifest",
    )
    if cold.get("mode") != "deterministic_references_not_dynamic_loader" or cold.get("triggers_from_durable_facts_only") is not True or cold.get("dynamic_loader_registry_or_daemon_allowed") is not False:
        evaluation.block("COLD_PATH_BOUNDARY_INVALID", "cold_path_manifest", "Cold paths must be deterministic durable-fact references without a loader/registry/daemon.")
    categories = exact_mapping(cold.get("categories"), COLD_PATHS, evaluation, "cold_path_manifest.categories")
    for name, (trigger, owner) in COLD_PATHS.items():
        spec = exact_mapping(categories.get(name), {"trigger", "owner"}, evaluation, f"cold_path_manifest.categories.{name}")
        if spec.get("trigger") != trigger or spec.get("owner") != owner:
            evaluation.block("COLD_PATH_ROUTE_INVALID", f"cold_path_manifest.categories.{name}", "Trigger or owner differs from the canonical route.")

    precedence = exact_mapping(
        policy.get("durable_authority_precedence"),
        {"required_order", "semantic_role_plus_exact_revision_not_latest_comment_wins", "later_exact_frozen_task_beats_stale_proposal_body", "protected_open_work_is_not_resume_target_by_openness", "takeover_terminal_state_after_recommendation", "replay_fixture"},
        evaluation,
        "durable_authority_precedence",
    )
    if precedence.get("required_order") != PRECEDENCE_ORDER:
        evaluation.block("AUTHORITY_PRECEDENCE_ORDER_INVALID", "durable_authority_precedence.required_order", "Generic authority precedence order differs.")
    for field in ("semantic_role_plus_exact_revision_not_latest_comment_wins", "later_exact_frozen_task_beats_stale_proposal_body", "protected_open_work_is_not_resume_target_by_openness"):
        if precedence.get(field) is not True:
            evaluation.block("AUTHORITY_PRECEDENCE_FACT_INVALID", f"durable_authority_precedence.{field}", "Required precedence fact must be true.")
    if precedence.get("takeover_terminal_state_after_recommendation") != "AWAIT_OWNER_CONTINUE":
        evaluation.block("TAKEOVER_BARRIER_CHANGED", "durable_authority_precedence", "Takeover recommendation must terminate at AWAIT_OWNER_CONTINUE.")
    fixture_expected = {
        "accepted_main_present": True,
        "canonical_lead_sink_present": True,
        "stale_proposal_body_present": True,
        "later_exact_frozen_task_present": True,
        "protected_older_open_work_present": True,
        "selected_authority_role": "exact_frozen_task_revision",
        "protected_older_open_work_selected": False,
    }
    fixture = exact_mapping(precedence.get("replay_fixture"), fixture_expected, evaluation, "durable_authority_precedence.replay_fixture")
    for field, required in fixture_expected.items():
        if fixture.get(field) != required:
            evaluation.block("AUTHORITY_PRECEDENCE_REPLAY_FAILED", f"durable_authority_precedence.replay_fixture.{field}", "Generic frozen-task precedence replay failed.")

    binding = exact_mapping(
        policy.get("running_task_revision_binding"),
        {"canonical_owner", "rules", "result_evidence_fields", "replay_fixtures"},
        evaluation,
        "running_task_revision_binding",
    )
    if binding.get("canonical_owner") != "docs/task-package/TASK_PACKAGE_SPEC.md":
        evaluation.block("RUNNING_TASK_BINDING_OWNER_INVALID", "running_task_revision_binding.canonical_owner", "The Task Package specification must remain the single canonical owner.")
    rules = exact_mapping(binding.get("rules"), RUNNING_TASK_BINDING_RULES, evaluation, "running_task_revision_binding.rules")
    for field, required in RUNNING_TASK_BINDING_RULES.items():
        if rules.get(field) != required:
            evaluation.block("RUNNING_TASK_BINDING_RULE_INVALID", f"running_task_revision_binding.rules.{field}", "Running Task exact-revision rule differs from the canonical contract.")
    exact_set(binding.get("result_evidence_fields"), RUNNING_TASK_RESULT_FIELDS, evaluation, "running_task_revision_binding.result_evidence_fields")
    fixtures = exact_mapping(binding.get("replay_fixtures"), RUNNING_TASK_FIXTURE_NAMES, evaluation, "running_task_revision_binding.replay_fixtures")
    replay_results = {}
    for name, facts in fixtures.items():
        fixture_facts = exact_mapping(facts, RUNNING_TASK_FIXTURE_KEYS, evaluation, f"running_task_revision_binding.replay_fixtures.{name}")
        if fixture_facts.get("runtime") not in {"web_interactive", "codex_native_subagents", "generic"}:
            evaluation.block("RUNNING_TASK_REPLAY_RUNTIME_INVALID", f"running_task_revision_binding.replay_fixtures.{name}.runtime", "Known runtime profile required.")
        if not is_nonempty(fixture_facts.get("activated_task_ref")) or not is_nonempty(fixture_facts.get("observed_later_task_ref")):
            evaluation.block("RUNNING_TASK_REPLAY_REF_INVALID", f"running_task_revision_binding.replay_fixtures.{name}", "Exact activated and observed Task refs are required.")
        for field in ("later_revision_material_to_running_contract", "reanchor_authorized"):
            if not isinstance(fixture_facts.get(field), bool):
                evaluation.block("RUNNING_TASK_REPLAY_FACT_INVALID", f"running_task_revision_binding.replay_fixtures.{name}.{field}", "Boolean replay fact required.")
        decision = running_task_revision_decision(fixture_facts)
        replay_results[name] = decision
        if decision.get("selected_task_ref") != fixture_facts.get("expected_selected_task_ref") or decision.get("action") != fixture_facts.get("expected_action"):
            evaluation.block("RUNNING_TASK_REVISION_REPLAY_FAILED", f"running_task_revision_binding.replay_fixtures.{name}", "Derived exact-revision binding differs from the expected replay result.")
    if replay_results.get("web_no_reanchor") != replay_results.get("codex_no_reanchor"):
        evaluation.block("RUNNING_TASK_RUNTIME_OUTCOME_DRIFT", "running_task_revision_binding.replay_fixtures", "Web and Codex must produce the same authority outcome.")

    presentation_expected = {
        "canonical_owner": "docs/task-package/TASK_PACKAGE_SPEC.md",
        "renderer_path": "templates/STARTUP_CARD_RENDER.py",
        "renderer_api": "render_startup_card",
        "reverse_validator_api": "validate_rendered_startup_card",
        "renderer_cli": True,
        "exact_task_ref_form": "github:owner/repo#issue@comment",
        "startup_card_display_fields": ["模型", "思考等级", "对话"],
        "additional_formal_card_fields_allowed": False,
        "internal_reasoning_profile_in_native_thinking_field_allowed": False,
        "fenced_text_blocks": 1,
        "activation_pointer_only": True,
        "durable_task_details_in_launcher_allowed": False,
        "standard_launcher_semantic_lines": 3,
        "line_breaks_change_semantics": False,
        "malformed_replay_expected": "REVISE_REQUIRED",
        "conformant_replay_expected": "PASS",
        "durable_task_remains_authority": True,
        "startup_card_gate_required": True,
        "manual_handwritten_standard_card_emission_allowed": False,
        "emit_only_after_gate_pass": True,
        "gate_failure_action": "BLOCK",
    }
    presentation = exact_mapping(policy.get("presentation"), presentation_expected, evaluation, "presentation")
    for field, required in presentation_expected.items():
        if presentation.get(field) != required:
            evaluation.block("PRESENTATION_CONTRACT_INVALID", f"presentation.{field}", "Formal launcher presentation contract differs.")
    validate_startup_renderer_contract(root, presentation, evaluation)

    simplicity = exact_mapping(
        policy.get("simplicity"),
        {"baseline_hot_path_required_surfaces", "baseline_hot_path_required_bytes", "candidate_hot_path_surfaces", "candidate_hot_path_byte_measurement", "candidate_hot_path_required_surfaces_max", "candidate_hot_path_required_bytes_max", "material_normative_semantics_with_multiple_owners_max", "runtime_profiles_containing_full_core_copies_max", "collapsed_surfaces", "current_tree_retired_or_collapsed_surfaces_min", "net_authority_surface"},
        evaluation,
        "simplicity",
    )
    if simplicity.get("candidate_hot_path_byte_measurement") != "committed_repository_blob_bytes_for_declared_hot_path_surfaces":
        evaluation.block(
            "HOT_PATH_METRIC_DEFINITION_INVALID",
            "simplicity.candidate_hot_path_byte_measurement",
            "Hot-path bytes must be measured from exact committed repository blobs.",
        )
    hot_paths = simplicity.get("candidate_hot_path_surfaces") if isinstance(simplicity.get("candidate_hot_path_surfaces"), list) else []
    hot_bytes = 0
    exact_commit = evaluation.authorities.get("git:HEAD")
    for relative in hot_paths:
        path = confined_path(root, relative, evaluation, f"simplicity.{relative}")
        if not path or not path.is_file():
            evaluation.block("HOT_PATH_SURFACE_MISSING", relative, "Declared hot-path surface is missing.")
        else:
            canonical_size = canonical_git_blob_size(root, exact_commit, relative, evaluation)
            if canonical_size is not None:
                hot_bytes += canonical_size
    collapsed = simplicity.get("collapsed_surfaces") if isinstance(simplicity.get("collapsed_surfaces"), list) else []
    evaluation.metrics.update({
        "baseline_hot_path_required_surfaces": simplicity.get("baseline_hot_path_required_surfaces"),
        "baseline_hot_path_required_bytes": simplicity.get("baseline_hot_path_required_bytes"),
        "hot_path_required_surfaces": len(hot_paths),
        "hot_path_required_bytes": hot_bytes,
        "material_normative_semantics_with_multiple_owners": 0,
        "runtime_profiles_containing_full_core_copies": full_core_copies,
        "current_tree_retired_or_collapsed_surfaces": len(set(collapsed)),
        "net_authority_surface": simplicity.get("net_authority_surface"),
        "runtime_placement_local_to_codex_remote_to_web": True,
        "codex_worker_native_delegation_default_allowed": delegation.get("default_allowed") is True,
        "quota_economy_without_qualification_bypass": delegation.get("cheaper_child_must_be_qualified_for_actual_subproblem_and_risk") is True,
        "child_scope_write_and_recursion_boundaries": all(delegation.get(field) is False for field in required_false),
        "running_task_revision_binding_owner_count": 1 if binding.get("canonical_owner") == "docs/task-package/TASK_PACKAGE_SPEC.md" else 0,
        "running_task_revision_replay_count": len(replay_results),
    })
    if len(hot_paths) > 3 or hot_bytes > 30000 or len(set(collapsed)) < 3 or simplicity.get("net_authority_surface") != "decrease":
        evaluation.reconcile("SIMPLICITY_TARGET_MISSED", "simplicity", "Candidate does not meet the frozen hot-path/collapse/net-authority targets.")
    if simplicity.get("material_normative_semantics_with_multiple_owners_max") != 0 or simplicity.get("runtime_profiles_containing_full_core_copies_max") != 0:
        evaluation.block("SIMPLICITY_BOUNDARY_WEAKENED", "simplicity", "Duplicate owners and full runtime core copies must remain zero.")


def evaluate_central(root, policy, inputs, evaluation):
    central = policy.get("central_governance") or {}
    profile = inputs.get("central_profile", "current_candidate")
    replay = profile in {"accepted_0_3_14_replay", "accepted_0_3_15_replay", "accepted_0_3_16_replay"}
    if profile not in {"current_candidate", "accepted_0_3_14_replay", "accepted_0_3_15_replay", "accepted_0_3_16_replay"}:
        evaluation.block("CENTRAL_PROFILE_UNSUPPORTED", "central_profile", "Unknown central evaluation profile.")
        replay = False
    contract = dict(central)
    if replay:
        replay_contract = central.get(profile) or {}
        for key in ("ordinary_version", "release_schema", "change_class", "required_paths", "required_markers"):
            contract[key] = replay_contract.get(key)
    commit, tree = git_identity(root, evaluation)
    expected = inputs.get("expected_identity") or {}
    for name, actual in (("commit", commit), ("tree", tree)):
        wanted = expected.get(name)
        if not is_nonempty(wanted):
            evaluation.block("EXPECTED_IDENTITY_REQUIRED", f"expected_identity.{name}", "Exact identity is required.")
        elif actual and wanted != actual:
            evaluation.block("IDENTITY_MISMATCH", f"expected_identity.{name}", f"Expected {wanted}, observed {actual}.")

    required_paths = contract.get("required_paths") or []
    if not isinstance(required_paths, list):
        evaluation.block("POLICY_REQUIRED_PATHS_INVALID", "central_governance.required_paths", "List required.")
        required_paths = []
    for relative in required_paths:
        path = confined_path(root, relative, evaluation, relative)
        if path is None:
            continue
        if not path.is_file():
            evaluation.block("REQUIRED_PATH_MISSING", relative, "Required conformance authority surface is missing.")
        else:
            evaluation.add_authority(relative, sha256_path(path))

    version_path = confined_path(root, central.get("version_path"), evaluation, "central.version_path")
    release_path = confined_path(root, central.get("release_path"), evaluation, "central.release_path")
    if version_path and version_path.is_file():
        version = version_path.read_text(encoding="utf-8-sig").strip()
        evaluation.add_authority(central.get("version_path"), sha256_path(version_path))
        if version != str(contract.get("ordinary_version")):
            evaluation.reconcile("VERSION_POLICY_MISMATCH", central.get("version_path"), "VERSION differs from conformance policy.")
    else:
        version = None

    if release_path and release_path.is_file():
        try:
            release = load_yaml_subset(release_path)
        except ConformanceError as exc:
            evaluation.block("RELEASE_YAML_INVALID", central.get("release_path"), str(exc))
            release = {}
        evaluation.add_authority(central.get("release_path"), sha256_path(release_path))
    else:
        release = {}

    release_version = nested(release, "ordinary_governance", "version")
    if version and release_version != version:
        evaluation.reconcile("VERSION_RELEASE_MISMATCH", central.get("release_path"), "Release ordinary version differs from VERSION.")
    if str(release.get("schema_version")) != str(contract.get("release_schema")):
        evaluation.reconcile("RELEASE_SCHEMA_MISMATCH", central.get("release_path"), "Release schema differs from policy.")
    if nested(release, "ordinary_governance", "change_class") != contract.get("change_class"):
        evaluation.reconcile("CHANGE_CLASS_MISMATCH", central.get("release_path"), "Release change class differs from policy.")

    release_conformance = release.get("conformance") or {}
    required_release_conformance = {
        "policy_path": "config/CONFORMANCE_POLICY.yaml",
        "protocol_path": "docs/conformance/GOVERNANCE_CONFORMANCE_PROTOCOL.md",
        "input_template_path": "templates/GOVERNANCE_CONFORMANCE_INPUT.yaml",
        "result_template_path": "templates/GOVERNANCE_CONFORMANCE_RESULT.yaml",
        "checker_path": "templates/GOVERNANCE_CONFORMANCE_CHECK.py",
        "derived_read_only_evidence": True,
        "becomes_authority_store": False,
        "network_required": False,
        "automatic_pin_advance_allowed": False,
        "local_action_execution_allowed": False,
        "bounded_drift_triggers_only": True,
        "console_consumption_optional_read_only": True,
        "policy_schema": "0.2",
        "evaluator_version": "0.3.17",
        "semantic_authority_map_is_derived_verification_metadata": True,
        "shared_kernel_is_canonical_owner_references_only": True,
        "runtime_profiles_delta_only": True,
        "unknown_owner_override_trigger_or_precedence_fails_closed": True,
        "durable_authority_precedence_is_semantic_role_plus_exact_revision": True,
        "formal_presentation_owner": "docs/task-package/TASK_PACKAGE_SPEC.md",
        "simplicity_metrics_required": True,
        "runtime_placement_contract_checked": True,
        "codex_worker_delegation_contract_checked": True,
        "running_task_revision_binding_checked": True,
    }
    if not replay:
        for field, required in required_release_conformance.items():
            if release_conformance.get(field) != required:
                evaluation.reconcile("RELEASE_CONFORMANCE_CONTRACT_MISMATCH", f"{central.get('release_path')}:conformance.{field}", "Release conformance contract differs from accepted policy.")
        if release_conformance.get("evaluation_modes") != ["central_governance", "downstream_project"]:
            evaluation.reconcile("RELEASE_CONFORMANCE_MODES_MISMATCH", f"{central.get('release_path')}:conformance.evaluation_modes", "Evaluation modes differ from accepted policy.")
        if set(release_conformance.get("overall_statuses") or []) != OVERALL:
            evaluation.reconcile("RELEASE_CONFORMANCE_STATUS_MISMATCH", f"{central.get('release_path')}:conformance.overall_statuses", "Overall status set differs from accepted policy.")
        if set(release_conformance.get("local_action_decisions") or []) != {"ALLOW", "BLOCK"}:
            evaluation.reconcile("RELEASE_LOCAL_ACTION_STATUS_MISMATCH", f"{central.get('release_path')}:conformance.local_action_decisions", "Local-action decision set differs from accepted policy.")

    modules_policy = policy.get("independent_modules") or {}
    release_modules = release.get("modules") or {}
    for module_name, module_policy in sorted(modules_policy.items()):
        declared = release_modules.get(module_policy.get("release_key", module_name))
        ref = f"{central.get('release_path')}:modules.{module_name}"
        if not isinstance(declared, dict):
            evaluation.block("MODULE_DECLARATION_MISSING", ref, "Independent module declaration is required.")
            continue
        if declared.get("independent_pin") is not True:
            evaluation.block("MODULE_NOT_INDEPENDENT", ref, "Independent pin invariant is missing.")
        if declared.get("ordinary_governance_upgrade_does_not_silently_repin_module") is not True:
            evaluation.block("MODULE_SILENT_REPIN_GUARD_MISSING", ref, "Silent-repin guard is required.")
        for key in ("root_path", "version_path"):
            if declared.get(key) != module_policy.get(key):
                evaluation.block("MODULE_PATH_MISMATCH", ref, f"{key} differs from policy.")
        module_version_path = confined_path(root, declared.get("version_path"), evaluation, ref)
        if module_version_path and module_version_path.is_file():
            actual_module_version = module_version_path.read_text(encoding="utf-8-sig").strip()
            evaluation.add_authority(declared.get("version_path"), sha256_path(module_version_path))
            if declared.get("version") != actual_module_version:
                evaluation.block("MODULE_VERSION_MISMATCH", ref, "Release pin differs from module VERSION.")
            notes = release.get("notes") or []
            pattern = re.compile(rf"{re.escape(module_name)} semantic version remains ([^\s.]+(?:\.[^\s.]+)*)", re.IGNORECASE)
            for note in notes if isinstance(notes, list) else []:
                match = pattern.search(str(note))
                if match and match.group(1).rstrip(".\"") != str(declared.get("version")):
                    evaluation.reconcile("MODULE_NOTE_PIN_CONTRADICTION", central.get("release_path"), "Release note contradicts accepted module pin.")

    markers = contract.get("required_markers") or {}
    if not isinstance(markers, dict):
        evaluation.block("POLICY_MARKERS_INVALID", "central_governance.required_markers", "Mapping required.")
    else:
        for relative, required in markers.items():
            path = confined_path(root, relative, evaluation, relative)
            if not path or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8-sig")
            for marker in required if isinstance(required, list) else []:
                if str(marker) not in text:
                    evaluation.block("REQUIRED_INVARIANT_MARKER_MISSING", relative, f"Missing marker: {marker}")
    if not replay:
        validate_policy_contract(root, policy, evaluation)


def evaluate_downstream(root, policy, inputs, evaluation):
    project = inputs.get("project") or {}
    facts = inputs.get("durable_facts") or {}
    supplied_root = project.get("root")
    if not is_nonempty(supplied_root):
        evaluation.block("PROJECT_ROOT_REQUIRED", "project.root", "Exact Owner-supplied/confirmed root is required.")
    else:
        try:
            supplied_resolved = Path(supplied_root).resolve(strict=True)
        except OSError as exc:
            evaluation.block("PROJECT_ROOT_UNVERIFIED", "project.root", f"Cannot verify project root: {exc}")
        else:
            if supplied_resolved != root:
                evaluation.block("PROJECT_ROOT_MISMATCH", "project.root", "Input root differs from explicit CLI root.")
    source = project.get("root_source")
    accepted_sources = nested(policy, "local_action", "accepted_root_sources", default=[])
    if source not in accepted_sources:
        evaluation.block("PROJECT_ROOT_SOURCE_INVALID", "project.root_source", "Root was not Owner-supplied or Owner-confirmed.")

    paths = {
        "governance_lock": project.get("governance_lock_path"),
        "local_policy": project.get("local_policy_path"),
        "project_state": project.get("project_state_path"),
    }
    loaded = {}
    for name, relative in paths.items():
        path = confined_path(root, relative, evaluation, f"project.{name}_path")
        if not path or not path.is_file():
            evaluation.block("DOWNSTREAM_AUTHORITY_MISSING", relative or name, "Required downstream authority file is missing.")
            continue
        evaluation.add_authority(relative, sha256_path(path))
        if name != "project_state":
            try:
                loaded[name] = load_yaml_subset(path)
            except ConformanceError as exc:
                evaluation.block("DOWNSTREAM_YAML_INVALID", relative, str(exc))
        elif facts.get("project_state_digest") != sha256_path(path):
            evaluation.block("PROJECT_STATE_DIGEST_MISMATCH", relative, "Supplied project-state digest does not match exact file.")

    downstream_policy = policy.get("downstream_project") or {}
    for field in downstream_policy.get("required_durable_refs") or []:
        if not is_nonempty(facts.get(field)):
            evaluation.block("DURABLE_FACT_REQUIRED", f"durable_facts.{field}", "Exact durable ref/digest is required.")
        else:
            evaluation.add_authority(f"durable:{field}", facts.get(field))
    if facts.get("lead_current") is not True:
        evaluation.block("LEAD_REF_STALE", "durable_facts.lead_current", "Current Lead continuity is required.")
    if facts.get("task_current") is not True:
        evaluation.block("TASK_REF_STALE", "durable_facts.task_current", "Current durable Task authority is required.")
    if facts.get("copied_governance_semantics_weakened") is not False:
        evaluation.block("COPIED_GOVERNANCE_WEAKENED", "durable_facts.copied_governance_semantics_weakened", "Copied central semantics may not weaken accepted governance.")
    evaluation.update_available = facts.get("update_available") is True
    if evaluation.update_available:
        evaluation.advisories.append("A governance or module update is available; the accepted pin remains authority until explicit adoption.")

    lock = loaded.get("governance_lock") or {}
    allowed_lock_schemas = [str(item) for item in downstream_policy.get("lock_schema_versions") or []]
    if str(lock.get("schema_version")) not in allowed_lock_schemas:
        evaluation.block("LOCK_SCHEMA_UNSUPPORTED", paths.get("governance_lock"), "Governance lock schema is unsupported.")
    governance = lock.get("governance") or {}
    for field in ("repository", "protocol_version", "pinned_ref"):
        if not is_nonempty(governance.get(field)):
            evaluation.block("GOVERNANCE_PIN_INCOMPLETE", paths.get("governance_lock"), f"governance.{field} is required.")
    if facts.get("accepted_governance_pin") != governance.get("pinned_ref"):
        evaluation.block("GOVERNANCE_PIN_CONFLICT", paths.get("governance_lock"), "Durable accepted governance pin conflicts with lock.")
    if facts.get("governance_pin_valid") is not True:
        evaluation.block("GOVERNANCE_PIN_INVALID", paths.get("governance_lock"), "Accepted governance pin must be verified valid.")
    layering = lock.get("project_policy") or {}
    if layering.get("may_weaken_central_invariants") is not False:
        evaluation.block("LOCAL_POLICY_LAYERING_WEAKENED", paths.get("governance_lock"), "Local policy may not weaken central invariants.")
    update = lock.get("update_policy") or {}
    for field in ("auto_follow_main", "automatic_adoption_allowed", "automatic_pin_advance_allowed"):
        if update.get(field) is not False:
            evaluation.block("AUTOMATIC_PIN_CHANGE_FORBIDDEN", paths.get("governance_lock"), f"update_policy.{field} must be false.")
    module = nested(lock, "modules", "lprl", default={}) or {}
    if module.get("enabled") is True:
        for field in ("version", "pinned_ref", "root_path", "version_path"):
            if not is_nonempty(module.get(field)):
                evaluation.block("MODULE_PIN_INCOMPLETE", paths.get("governance_lock"), f"modules.lprl.{field} is required.")
        if facts.get("accepted_module_pin") != module.get("pinned_ref"):
            evaluation.block("MODULE_PIN_CONFLICT", paths.get("governance_lock"), "Durable accepted module pin conflicts with lock.")
        if facts.get("module_compatible") is not True:
            evaluation.block("MODULE_INCOMPATIBLE", paths.get("governance_lock"), "Independent module/core compatibility must be verified.")

    local = loaded.get("local_policy") or {}
    allowed_local_schemas = [str(item) for item in downstream_policy.get("local_policy_schema_versions") or []]
    if str(local.get("schema_version")) not in allowed_local_schemas:
        evaluation.block("LOCAL_POLICY_SCHEMA_UNSUPPORTED", paths.get("local_policy"), "Local policy schema is unsupported.")
    resource_policy = local.get("local_resource_policy") or {}
    if nested(resource_policy, "project_root", "source") not in accepted_sources:
        evaluation.block("LOCAL_POLICY_ROOT_SOURCE_INVALID", paths.get("local_policy"), "Local policy root source is not Owner-controlled.")
    required_false = (
        "allow_agent_to_choose_or_relocate_project_root",
        "allow_write_outside_owner_supplied_project_root",
        "tracking_authorizes_migration_or_cleanup",
    )
    for field in required_false:
        if resource_policy.get(field) is not False:
            evaluation.block("LOCAL_POLICY_ACTION_GUARD_INVALID", paths.get("local_policy"), f"local_resource_policy.{field} must be false.")

    topology_applicable = resource_policy.get("mode") == "tracking" or isinstance(inputs.get("local_action"), dict)
    if topology_applicable:
        if not is_nonempty(facts.get("topology_digest")):
            evaluation.block("TOPOLOGY_DIGEST_REQUIRED", "durable_facts.topology_digest", "Exact topology digest is required when local topology is applicable.")
        else:
            evaluation.add_authority("durable:topology_digest", facts.get("topology_digest"))
        if facts.get("topology_facts_current") is not True:
            evaluation.block("TOPOLOGY_FACTS_STALE", "durable_facts.topology_facts_current", "Current topology facts are required when local topology is applicable.")

    if isinstance(inputs.get("local_action"), dict):
        evaluate_local_action(root, policy, inputs, evaluation)


def evaluate_local_action(root, policy, inputs, evaluation):
    action = inputs.get("local_action") or {}
    evaluation.local_action = {"requested": True, "decision": "BLOCK", "reasons": []}
    reasons = evaluation.local_action["reasons"]

    def require(condition, code, ref, explanation):
        if not condition:
            reasons.append(code)
            evaluation.block(code, ref, explanation)

    if "decision" in action:
        require(False, "CALLER_DECISION_FORBIDDEN", "local_action.decision", "Decision is evaluator output, not caller input.")
    local_policy = policy.get("local_action") or {}
    resource_type = action.get("resource_type")
    resource_known = nested(action, "topology", "resource_class_known") is True
    require(resource_type in (local_policy.get("resource_types") or []) and resource_known, "UNKNOWN_RESOURCE", "local_action.resource_type", "Unknown resources require inventory/classification/reconciliation; no action is performed.")
    if "UNKNOWN_RESOURCE" in reasons:
        evaluation.advisories.append("Inventory and classify the unknown resource; quarantine remains a separately authorized non-automatic action.")
    require(action.get("action") in (local_policy.get("actions") or []), "ACTION_UNSUPPORTED", "local_action.action", "Unsupported local action.")
    require(action.get("project") == nested(inputs, "project", "name"), "ACTION_PROJECT_MISMATCH", "local_action.project", "Action project differs from evaluated project.")
    require(action.get("task_ref") == nested(inputs, "durable_facts", "task_ref"), "ACTION_TASK_MISMATCH", "local_action.task_ref", "Action Task differs from durable Task.")
    for field in ("governance_pin_valid", "local_policy_valid", "task_authorized"):
        require(nested(action, "authority", field) is True, "ACTION_AUTHORITY_MISSING", f"local_action.authority.{field}", "All authority gates must be true.")
    root_source = nested(action, "root", "source")
    require(root_source in (local_policy.get("accepted_root_sources") or []), "ACTION_ROOT_GUESSED", "local_action.root.source", "Guessed/inferred roots are forbidden.")
    require(nested(action, "root", "owner_supplied_or_confirmed") is True, "ACTION_ROOT_NOT_OWNER_CONTROLLED", "local_action.root", "Owner root authority is required.")
    require(nested(action, "root", "verified") is True, "ACTION_ROOT_UNVERIFIED", "local_action.root", "Root verification is required.")
    require(nested(action, "root", "within_boundary") is True, "ACTION_ROOT_OUTSIDE_BOUNDARY", "local_action.root", "Root must be within the controlled boundary.")
    try:
        action_root = Path(nested(action, "root", "path", default="")).resolve(strict=True)
    except (OSError, TypeError):
        action_root = None
    require(action_root == root, "ACTION_ROOT_MISMATCH", "local_action.root.path", "Action root must equal the exact evaluated root.")
    require(nested(action, "topology", "facts_current") is True, "ACTION_TOPOLOGY_STALE", "local_action.topology", "Current topology facts are required.")
    protected = nested(action, "topology", "protected_runtime") is True
    shared = nested(action, "topology", "shared_resource") is True
    if protected or shared:
        separate = nested(action, "authority", "action_specific_authorization") is True
        owner_set = nested(action, "topology", "owner_set_complete") is True
        require(separate and owner_set, "PROTECTED_OR_SHARED_ACTION_BLOCKED", "local_action.topology", "Protected/shared action requires separate authority and complete owner set.")
    if not reasons:
        evaluation.local_action["decision"] = "ALLOW"


def blocked_result(mode, code, explanation, authority_ref="evaluator"):
    evaluation = Evaluation(mode)
    evaluation.block(code, authority_ref, explanation)
    return evaluation.result()


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Explicit absolute repository/project root")
    parser.add_argument("--policy", required=True, help="Explicit conformance policy path")
    parser.add_argument("--input", required=True, help="Explicit conformance input path")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    raw_root = Path(args.root)
    if not raw_root.is_absolute():
        result = blocked_result("unknown", "CLI_ROOT_NOT_ABSOLUTE", "--root must be explicit and absolute.", "--root")
    else:
        try:
            root = raw_root.resolve(strict=True)
            policy = load_yaml_subset(args.policy)
            inputs = load_yaml_subset(args.input)
            mode = inputs.get("mode")
            if str(policy.get("schema_version")) != "0.2" or str(inputs.get("schema_version")) != "0.2":
                raise ConformanceError("unsupported policy or input schema")
            if mode not in {"central_governance", "downstream_project"}:
                raise ConformanceError(f"unsupported evaluation mode: {mode!r}")
            evaluation = Evaluation(mode)
            evaluation.add_authority("conformance-policy", sha256_path(args.policy))
            evaluation.add_authority("conformance-input", sha256_path(args.input))
            if mode == "central_governance":
                evaluate_central(root, policy, inputs, evaluation)
            else:
                evaluate_downstream(root, policy, inputs, evaluation)
            result = evaluation.result()
        except (ConformanceError, OSError, ValueError) as exc:
            result = blocked_result("unknown", "EVALUATOR_INPUT_ERROR", str(exc))

    if result["overall_status"] not in OVERALL or result["internal_drift"] not in DRIFT:
        result = blocked_result("unknown", "EVALUATOR_INTERNAL_ERROR", "Invalid evaluator status.")
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return {"CONFORMANT": 0, "RECONCILIATION_REQUIRED": 2, "BLOCKED": 3}[result["overall_status"]]


if __name__ == "__main__":
    sys.exit(run())
