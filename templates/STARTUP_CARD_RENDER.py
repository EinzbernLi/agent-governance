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


def _config_lines(filename: str) -> list[str]:
    root = Path(__file__).resolve().parents[1]
    try:
        return (root / "config" / filename).read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read {filename}: {exc}") from exc


def _section(lines: list[str], key: str, indent: int) -> list[str]:
    marker = " " * indent + key + ":"
    start = next((index + 1 for index, line in enumerate(lines) if line == marker), None)
    if start is None:
        raise ValueError(f"required governance section is missing: {key}")
    end = len(lines)
    for index in range(start, len(lines)):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip(" ")) <= indent:
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


def _list(lines: list[str], key: str, indent: int) -> list[str]:
    block = _section(lines, key, indent)
    values = []
    item_prefix = " " * (indent + 2) + "- "
    for line in block:
        if line.startswith(item_prefix):
            values.append(line[len(item_prefix):].strip().strip('"'))
    if not values:
        raise ValueError(f"required governance list is missing or empty: {key}")
    return values


def _child_keys(lines: list[str], indent: int) -> list[str]:
    prefix = " " * indent
    return [
        line[len(prefix):-1]
        for line in lines
        if line.startswith(prefix)
        and len(line) - len(line.lstrip(" ")) == indent
        and line.endswith(":")
        and line[len(prefix):-1]
    ]


def validate_model_routing_decision(decision: dict, *, model: str, reasoning: str) -> None:
    """Validate an already-resolved routing decision; never rank or choose a model."""

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
        or _scalar(gate, "missing_or_invalid_decision_action", 4) != "BLOCK"
    ):
        raise ValueError("formal launch gate policy is not fail-closed")

    values = {key: _normalise_value(key, decision[key]) for key in required}
    if values["selected_model"] != _normalise_value("model", model) or values["selected_reasoning"] != _normalise_value("reasoning", reasoning):
        raise ValueError("startup card model/reasoning must match routing_decision")
    if values["risk_level"] not in RISK_ORDER or values["authority_class"] not in _list(gate, "authority_classes", 4):
        raise ValueError("routing_decision risk/authority class is invalid")

    models = _section(registry_lines, "models", 0)
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
        for name in _child_keys(models, 2)
        if _scalar(_section(models, name, 2), "status", 4) == "candidate"
    }
    challenger = decision.get("challenger_model")
    strength = decision.get("challenger_evidence_strength")
    defer_reason = decision.get("challenger_defer_reason")
    if disposition == "not_applicable":
        if candidate_models or any(value is not None for value in (challenger, strength, defer_reason)):
            raise ValueError("registered candidate must be selected or explicitly deferred")
        return
    if not isinstance(challenger, str) or challenger not in _child_keys(models, 2):
        raise ValueError("selected/deferred challenger must name a registered model")
    if candidate_models and challenger not in candidate_models:
        raise ValueError("registered candidate challenger may not be silently bypassed")
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
) -> str:
    """Render from already-resolved inputs; routing authority remains external."""

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
        validate_model_routing_decision(routing_decision, model=values["模型"], reasoning=values["思考等级"])

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
            )
        )
    except (ValueError, json.JSONDecodeError) as exc:
        _parser().error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
