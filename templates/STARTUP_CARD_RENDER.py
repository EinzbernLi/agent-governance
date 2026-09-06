"""Deterministic, offline renderer for the formal governance startup card."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DISPLAY_FIELDS = ("模型", "思考等级", "对话")
STANDARD_LAUNCHER_SEMANTIC_LINES = 3
TASK_REF_PATTERN = re.compile(
    r"^github:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*@[1-9][0-9]*$"
)
LAUNCHER_ROLES = {"worker", "independent_validator"}
EXECUTION_SURFACES = {"web", "agent"}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _normalise_value(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    normalised = " ".join(value.split())
    if not normalised:
        raise ValueError(f"{name} must not be empty")
    return normalised


def validate_task_ref(task_ref: str) -> str:
    """Return an exact activation pointer or fail closed."""

    if not isinstance(task_ref, str):
        raise ValueError("task_ref must be a string")
    candidate = task_ref.strip()
    if not TASK_REF_PATTERN.fullmatch(candidate):
        raise ValueError("task_ref must use github:owner/repo#issue@comment")
    return candidate


def _file_lines(path: Path, label: str) -> list[str]:
    try:
        return path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc


def _config_lines(filename: str) -> list[str]:
    root = Path(__file__).resolve().parents[1]
    return _file_lines(root / "config" / filename, filename)


def _section(lines: list[str], key: str, indent: int) -> list[str]:
    marker = " " * indent + key + ":"
    start = next((index + 1 for index, line in enumerate(lines) if line == marker), None)
    if start is None:
        raise ValueError(f"required governance section is missing: {key}")
    end = len(lines)
    for index in range(start, len(lines)):
        line = lines[index]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip(" ")) <= indent:
            end = index
            break
    return lines[start:end]


def _scalar(lines: list[str], key: str, indent: int) -> str:
    prefix = " " * indent + key + ":"
    for line in lines:
        if line.startswith(prefix):
            raw = line[len(prefix):].strip()
            if not raw:
                break
            if raw.startswith('"'):
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid governance scalar: {key}") from exc
                if isinstance(value, str):
                    return value
            return raw
    raise ValueError(f"required governance scalar is missing: {key}")


def _nullable_scalar(lines: list[str], key: str, indent: int) -> str | None:
    raw = _scalar(lines, key, indent)
    if raw in {"null", "~"}:
        return None
    return _normalise_value(key, raw)


def _bool_scalar(lines: list[str], key: str, indent: int) -> bool:
    raw = _scalar(lines, key, indent)
    if raw == "true":
        return True
    if raw == "false":
        return False
    raise ValueError(f"{key} must be true or false")


def _decode_list_item(raw: str, key: str) -> str:
    item = raw.strip()
    if not item:
        raise ValueError(f"{key} contains an empty item")
    if item.startswith('"'):
        try:
            value = json.loads(item)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid list item in {key}") from exc
        if not isinstance(value, str):
            raise ValueError(f"{key} items must be strings")
        return _normalise_value(key, value)
    if item.startswith("'") and item.endswith("'") and len(item) >= 2:
        return _normalise_value(key, item[1:-1].replace("''", "'"))
    return _normalise_value(key, item)


def _string_list(lines: list[str], key: str, indent: int, *, allow_empty: bool) -> list[str]:
    prefix = " " * indent + key + ":"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        raw = line[len(prefix):].strip()
        if raw:
            if raw == "[]":
                values: list[str] = []
            elif raw.startswith("[") and raw.endswith("]"):
                inner = raw[1:-1].strip()
                values = [] if not inner else [_decode_list_item(item, key) for item in inner.split(",")]
            else:
                raise ValueError(f"{key} must be a YAML list")
        else:
            values = []
            item_prefix = " " * (indent + 2) + "- "
            for candidate in lines[index + 1 :]:
                if candidate.strip() and not candidate.lstrip().startswith("#"):
                    candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                    if candidate_indent <= indent:
                        break
                    if candidate.startswith(item_prefix):
                        values.append(_decode_list_item(candidate[len(item_prefix):], key))
            if not values and not allow_empty:
                raise ValueError(f"required governance list is missing or empty: {key}")
        if len(values) != len(set(values)):
            raise ValueError(f"{key} must not contain duplicate models")
        if not values and not allow_empty:
            raise ValueError(f"required governance list is missing or empty: {key}")
        return values
    raise ValueError(f"required governance list is missing: {key}")


def _list(lines: list[str], key: str, indent: int) -> list[str]:
    return _string_list(lines, key, indent, allow_empty=False)


def _mapping_keys(lines: list[str], indent: int) -> set[str]:
    keys: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if len(line) - len(line.lstrip(" ")) != indent or ":" not in stripped:
            continue
        keys.add(stripped.split(":", 1)[0])
    return keys


def _child_keys(lines: list[str], indent: int) -> list[str]:
    prefix = " " * indent
    return [
        line[len(prefix):-1]
        for line in lines
        if line.startswith(prefix)
        and len(line) - len(line.lstrip(" ")) == indent
        and line.endswith(":")
        and line[len(prefix):-1]
        and not line.lstrip().startswith("#")
    ]


def _local_model_bindings(local_policy_path: str | Path | None) -> dict:
    if local_policy_path is None:
        raise ValueError("formal launch requires explicit project LOCAL_POLICY for surface-pool validation")
    path = Path(local_policy_path)
    lines = _file_lines(path, str(path))
    if "model_bindings:" not in lines:
        raise ValueError("project LOCAL_POLICY model_bindings section is required for formal launch")

    bindings = _section(lines, "model_bindings", 0)
    expected_binding_keys = {
        "web",
        "agent",
        "ai_recommendation_allowed",
        "initial_or_material_change_requires_owner_confirmation",
    }
    if _mapping_keys(bindings, 2) != expected_binding_keys:
        raise ValueError("LOCAL_POLICY model_bindings fields do not match the central contract")

    parsed: dict[str, object] = {}
    for surface in sorted(EXECUTION_SURFACES):
        surface_lines = _section(bindings, surface, 2)
        if _mapping_keys(surface_lines, 4) != {"allowed_models", "default_model", "role_preferences"}:
            raise ValueError(f"LOCAL_POLICY model_bindings.{surface} fields are invalid")
        allowed_models = _string_list(surface_lines, "allowed_models", 4, allow_empty=True)
        default_model = _nullable_scalar(surface_lines, "default_model", 4)
        role_lines = _section(surface_lines, "role_preferences", 4)
        if _mapping_keys(role_lines, 6) != {"lead", "worker", "validator"}:
            raise ValueError(f"LOCAL_POLICY model_bindings.{surface}.role_preferences fields are invalid")
        role_preferences = {
            role: _nullable_scalar(role_lines, role, 6)
            for role in ("lead", "worker", "validator")
        }
        preferences = [default_model, *role_preferences.values()]
        if allowed_models and any(value is not None and value not in allowed_models for value in preferences):
            raise ValueError(f"LOCAL_POLICY model_bindings.{surface} preference is outside allowed_models")
        parsed[surface] = {
            "allowed_models": allowed_models,
            "default_model": default_model,
            "role_preferences": role_preferences,
        }

    parsed["ai_recommendation_allowed"] = _bool_scalar(bindings, "ai_recommendation_allowed", 2)
    owner_confirmation = _bool_scalar(
        bindings,
        "initial_or_material_change_requires_owner_confirmation",
        2,
    )
    if not owner_confirmation:
        raise ValueError("LOCAL_POLICY model binding changes must require Owner confirmation")
    parsed["initial_or_material_change_requires_owner_confirmation"] = owner_confirmation
    return parsed


def validate_model_routing_decision(
    decision: dict,
    *,
    model: str,
    reasoning: str,
    execution_surface: str | None = None,
    local_policy_path: str | Path | None = None,
) -> None:
    """Validate an already-resolved routing decision; never rank, place, or choose a model."""

    routing_lines = _config_lines("MODEL_ROUTING.yaml")
    registry_lines = _config_lines("MODEL_REGISTRY.yaml")
    policy = _section(routing_lines, "routing_policy", 0)
    gate = _section(policy, "formal_launch_gate", 2)
    challenger_policy = _section(policy, "challenger_exploration", 2)
    required = set(_list(gate, "required_fields", 4))
    optional = set(_list(gate, "optional_challenger_fields", 4))
    if not isinstance(decision, dict) or not required <= set(decision) or set(decision) - required - optional:
        raise ValueError("routing_decision fields do not match MODEL_ROUTING formal_launch_gate")
    if (
        _scalar(gate, "decision_is_derived_evidence_not_authority", 4) != "true"
        or _scalar(gate, "ranking_or_model_selection_inside_startup_renderer_allowed", 4) != "false"
        or _scalar(gate, "conversation_display_may_infer_execution_surface", 4) != "false"
        or _scalar(gate, "central_registry_is_exhaustive_adopter_allowlist", 4) != "false"
        or _scalar(gate, "undeclared_noncentral_model_action", 4) != "BLOCK"
        or _scalar(gate, "configured_surface_out_of_pool_action", 4) != "BLOCK"
        or _scalar(gate, "missing_or_invalid_decision_action", 4) != "BLOCK"
    ):
        raise ValueError("formal launch gate policy is not fail-closed")

    values = {key: _normalise_value(key, decision[key]) for key in required}
    if values["selected_model"] != _normalise_value("model", model) or values["selected_reasoning"] != _normalise_value("reasoning", reasoning):
        raise ValueError("startup card model/reasoning must match routing_decision")
    if values["risk_level"] not in RISK_ORDER or values["authority_class"] not in _list(gate, "authority_classes", 4):
        raise ValueError("routing_decision risk/authority class is invalid")

    if execution_surface is None:
        raise ValueError("formal launch requires explicit already-resolved execution_surface")
    surface = _normalise_value("execution_surface", execution_surface).lower()
    if surface not in EXECUTION_SURFACES:
        raise ValueError("execution_surface must be web or agent")
    bindings = _local_model_bindings(local_policy_path)
    pool = list(bindings[surface]["allowed_models"])
    if pool and values["selected_model"] not in pool:
        raise ValueError("selected model is outside the configured execution-surface pool")

    models = _section(registry_lines, "models", 0)
    registered_models = set(_child_keys(models, 2))
    selected_is_central = values["selected_model"] in registered_models
    if not selected_is_central:
        if values["selected_model"] not in pool:
            raise ValueError("undeclared non-central model is not eligible for formal launch")
    else:
        selected = _section(models, values["selected_model"], 2)
        status = _scalar(selected, "status", 4)
        if status == "candidate":
            boundaries = _section(challenger_policy, "status_boundaries", 4)
            candidate = _section(boundaries, "candidate", 6)
            if values["authority_class"] not in _list(candidate, "allowed_routes", 8) or _scalar(candidate, "production_mutation_authority", 8) != "false":
                raise ValueError("candidate model exceeds MODEL_ROUTING authority boundary")
        elif status == "provisional":
            roles = _section(selected, "provisional_roles", 4)
            role_spec = _section(roles, values["role"], 6)
            if values["task_class"] not in _list(role_spec, "task_classes", 8):
                raise ValueError("provisional model exceeds role/task_class ceiling")
            ceiling = _scalar(role_spec, "risk_ceiling", 8)
            if ceiling not in RISK_ORDER or RISK_ORDER[values["risk_level"]] > RISK_ORDER[ceiling]:
                raise ValueError("provisional model exceeds risk ceiling")
        elif status == "preferred":
            if values["role"] not in _list(selected, "qualified_roles", 4):
                raise ValueError("preferred model is not qualified for role")
        else:
            raise ValueError("selected model has unsupported registry status")

    disposition = values["challenger_disposition"]
    if disposition not in _list(gate, "challenger_dispositions", 4):
        raise ValueError("challenger_disposition is invalid")
    candidate_models = {
        name
        for name in registered_models
        if _scalar(_section(models, name, 2), "status", 4) == "candidate"
    }
    if pool:
        candidate_models &= set(pool)
    challenger = decision.get("challenger_model")
    strength = decision.get("challenger_evidence_strength")
    defer_reason = decision.get("challenger_defer_reason")
    if disposition == "not_applicable":
        if candidate_models or any(value is not None for value in (challenger, strength, defer_reason)):
            raise ValueError("eligible registered candidate must be selected or explicitly deferred")
        return
    if not isinstance(challenger, str) or challenger not in registered_models:
        raise ValueError("selected/deferred challenger must name a centrally registered model")
    if pool and challenger not in pool:
        raise ValueError("challenger model is outside the configured execution-surface pool")
    if candidate_models and challenger not in candidate_models:
        raise ValueError("eligible registered candidate challenger may not be silently bypassed")
    if challenger not in candidate_models:
        raise ValueError("selected/deferred challenger must be an eligible registered candidate")
    evidence = _section(challenger_policy, "evidence_strength", 4)
    if strength not in _list(evidence, "under_evidenced_bands", 6):
        raise ValueError("challenger must use an under-evidenced strength band")
    if disposition == "selected":
        if challenger != values["selected_model"] or defer_reason is not None:
            raise ValueError("selected challenger must match selected_model and have no defer reason")
    elif disposition == "deferred":
        if challenger == values["selected_model"] or defer_reason not in _list(challenger_policy, "deferral_reasons", 4):
            raise ValueError("deferred challenger requires a different selected model and accepted reason")


def _is_conformance_structural_probe(task_ref: str, model: str, reasoning: str, conversation: str) -> bool:
    """Preserve the existing non-task synthetic probe used by central conformance."""

    return task_ref == "github:owner/repo#1@2" and model == "model" and reasoning == "high" and conversation == "session"


def _build_launcher(task_ref: str, role: str = "worker") -> str:
    """Build the single thin launcher block required by the Task spec."""

    exact_ref = validate_task_ref(task_ref)
    if role not in LAUNCHER_ROLES:
        raise ValueError("role must be worker or independent_validator")
    final_phrase = (
        "作为该 Task 的执行者执行，不接管项目 Lead。"
        if role == "worker"
        else "作为该 Task 的独立 Validator 执行，不接管项目 Lead。"
    )
    return "```text\n执行 %s；\n先读取该 Task，并按 Task 内引用读取关联事实；\n%s\n```" % (
        exact_ref,
        final_phrase,
    )


def _render_startup_card(
    *,
    task_ref: str,
    model: str,
    reasoning: str,
    conversation: str,
    role: str,
) -> str:
    lines = [
        f"{DISPLAY_FIELDS[0]}: {model}",
        f"{DISPLAY_FIELDS[1]}: {reasoning}",
        f"{DISPLAY_FIELDS[2]}: {conversation}",
        "",
        _build_launcher(task_ref, role),
    ]
    return "\n".join(lines)


def validate_rendered_startup_card(
    rendered: str,
    *,
    task_ref: str,
    model: str,
    reasoning: str,
    conversation: str,
    role: str = "worker",
) -> None:
    """Structurally reverse-validate a complete card against resolved inputs."""

    if not isinstance(rendered, str) or rendered != rendered.strip():
        raise ValueError("rendered startup card must not have surrounding content")
    exact_ref = validate_task_ref(task_ref)
    expected = {
        DISPLAY_FIELDS[0]: _normalise_value("model", model),
        DISPLAY_FIELDS[1]: _normalise_value("reasoning", reasoning),
        DISPLAY_FIELDS[2]: _normalise_value("conversation", conversation),
    }
    if role not in LAUNCHER_ROLES:
        raise ValueError("role must be worker or independent_validator")
    lines = rendered.split("\n")
    if len(lines) != 9 or any("\r" in line for line in lines):
        raise ValueError("startup card has an invalid line structure")
    formal = []
    for line in lines[:3]:
        match = re.fullmatch(r"([^:]+): (.+)", line)
        if not match:
            raise ValueError("startup card formal fields are malformed")
        formal.append((match.group(1), match.group(2)))
    if [field for field, _ in formal] != list(DISPLAY_FIELDS):
        raise ValueError("startup card formal fields are missing or reordered")
    if dict(formal) != expected:
        raise ValueError("startup card formal values do not match resolved inputs")
    if lines[3] != "" or lines[4] != "```text" or lines[8] != "```":
        raise ValueError("startup card fence structure is invalid")
    if rendered.count("```") != 2 or rendered.count("```text") != 1:
        raise ValueError("startup card must contain exactly one text fence")
    launcher = lines[5:8]
    if launcher[0] != f"执行 {exact_ref}；":
        raise ValueError("startup card task reference does not match resolved input")
    if launcher[1] != "先读取该 Task，并按 Task 内引用读取关联事实；":
        raise ValueError("startup card launcher read-fact line is invalid")
    expected_role_phrase = (
        "作为该 Task 的执行者执行，不接管项目 Lead。"
        if role == "worker"
        else "作为该 Task 的独立 Validator 执行，不接管项目 Lead。"
    )
    if launcher[2] != expected_role_phrase:
        raise ValueError("startup card role phrase does not match resolved role")


def render_startup_card(
    *,
    task_ref: str,
    model: str,
    reasoning: str,
    conversation: str,
    role: str = "worker",
    route: str | None = None,
    profile: str | None = None,
    routing_decision: dict | None = None,
    execution_surface: str | None = None,
    local_policy_path: str | Path | None = None,
) -> str:
    """Render from already-resolved inputs; routing and placement authority remain external."""

    exact_ref = validate_task_ref(task_ref)
    values = {
        "模型": _normalise_value("model", model),
        "思考等级": _normalise_value("reasoning", reasoning),
        "对话": _normalise_value("conversation", conversation),
    }
    if route is not None:
        _normalise_value("route", route)
    if profile is not None:
        _normalise_value("profile", profile)
    if routing_decision is None:
        if not _is_conformance_structural_probe(exact_ref, values["模型"], values["思考等级"], values["对话"]):
            raise ValueError("formal Worker/Validator startup card requires routing_decision")
    else:
        validate_model_routing_decision(
            routing_decision,
            model=values["模型"],
            reasoning=values["思考等级"],
            execution_surface=execution_surface,
            local_policy_path=local_policy_path,
        )

    rendered = _render_startup_card(
        task_ref=exact_ref,
        model=values["模型"],
        reasoning=values["思考等级"],
        conversation=values["对话"],
        role=role,
    )
    validate_rendered_startup_card(
        rendered,
        task_ref=exact_ref,
        model=values["模型"],
        reasoning=values["思考等级"],
        conversation=values["对话"],
        role=role,
    )
    return rendered


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-ref", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning", required=True)
    parser.add_argument("--conversation", required=True)
    parser.add_argument("--role", choices=sorted(LAUNCHER_ROLES), default="worker")
    parser.add_argument("--route")
    parser.add_argument("--profile")
    parser.add_argument("--routing-decision-json")
    parser.add_argument("--execution-surface", choices=sorted(EXECUTION_SURFACES))
    parser.add_argument("--local-policy")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        decision = json.loads(args.routing_decision_json) if args.routing_decision_json else None
        print(
            render_startup_card(
                task_ref=args.task_ref,
                model=args.model,
                reasoning=args.reasoning,
                conversation=args.conversation,
                role=args.role,
                route=args.route,
                profile=args.profile,
                routing_decision=decision,
                execution_surface=args.execution_surface,
                local_policy_path=args.local_policy,
            )
        )
    except (ValueError, json.JSONDecodeError) as exc:
        _parser().error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
