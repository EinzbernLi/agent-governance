#!/usr/bin/env python3
"""Offline, read-only governance conformance reference evaluator.

The loader intentionally implements only the repository's configuration YAML
subset. Unsupported YAML fails closed instead of being guessed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


RESULT_SCHEMA = "0.1"
EVALUATOR_VERSION = "0.3.15"
OVERALL = {"CONFORMANT", "RECONCILIATION_REQUIRED", "BLOCKED"}
DRIFT = {"CONFORMANT", "DRIFT_RECONCILABLE", "DRIFT_BLOCKING"}


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


class Evaluation:
    def __init__(self, mode):
        self.mode = mode
        self.findings = []
        self.advisories = []
        self.authorities = {}
        self.update_available = False
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


def evaluate_central(root, policy, inputs, evaluation):
    central = policy.get("central_governance") or {}
    profile = inputs.get("central_profile", "current_candidate")
    replay = profile == "accepted_0_3_14_replay"
    if profile not in {"current_candidate", "accepted_0_3_14_replay"}:
        evaluation.block("CENTRAL_PROFILE_UNSUPPORTED", "central_profile", "Unknown central evaluation profile.")
        replay = False
    contract = dict(central)
    if replay:
        replay_contract = central.get("accepted_0_3_14_replay") or {}
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
            if str(policy.get("schema_version")) != "0.1" or str(inputs.get("schema_version")) != "0.1":
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
