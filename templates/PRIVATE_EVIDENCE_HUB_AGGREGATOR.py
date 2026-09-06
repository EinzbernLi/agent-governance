#!/usr/bin/env python3
"""Deterministically aggregate private project-local calibration states.

This tool is intentionally offline. It reads one JSON bundle from a file or
stdin and writes one derived Private Evidence Hub state JSON to stdout.
It performs no network calls and no repository or Issue writes.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict

SCHEMA_VERSION = "1.0"
CONFIG_TITLE = "[PRIVATE-EVIDENCE-HUB] Sources"
CONFIG_MARKER = "[PRIVATE-EVIDENCE-HUB-CONFIG-v1]"
STATE_TITLE = "[PRIVATE-CROSS-PROJECT-CALIBRATION] Derived routing prior"
STATE_MARKER = "[PRIVATE-CROSS-PROJECT-CALIBRATION-STATE-v1]"
PROJECT_STATE_MARKER = "[PROJECT-LOCAL-CALIBRATION-STATE-v1]"
ALLOWED_ROLES = {"bounded_worker", "validator"}
GROUP_KEYS = (
    "role",
    "task_class",
    "risk_level",
    "model_semantic_key",
    "reasoning_semantic_key",
)


class HubInputError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HubInputError(message)


def _number(value, field: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), field)
    number = float(value)
    _require(math.isfinite(number) and number >= 0.0, field)
    return number


def _integer(value, field: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, field)
    return value


def _rate(value, field: str):
    if value is None:
        return None
    number = _number(value, field)
    _require(number <= 1.0, field)
    return number


def _nonempty(value, field: str) -> str:
    _require(isinstance(value, str) and value.strip(), field)
    return value.strip()


def _group_identity(group: dict) -> tuple:
    return tuple(group[key] for key in GROUP_KEYS)


def _evidence_strength(effective_samples: float, source_count: int) -> str:
    if source_count < 2 or effective_samples < 2.0:
        return "insufficient"
    if effective_samples < 5.0:
        return "developing"
    return "established"


def _validate_group(group: dict, source: str) -> dict:
    _require(isinstance(group, dict), f"{source}:group_not_object")
    role = _nonempty(group.get("role"), f"{source}:group.role")
    _require(role in ALLOWED_ROLES, f"{source}:group.role")
    for key in ("task_class", "risk_level", "model_semantic_key", "reasoning_semantic_key"):
        _nonempty(group.get(key), f"{source}:group.{key}")
    if "model_id" in group and group.get("model_id") is not None:
        _nonempty(group.get("model_id"), f"{source}:group.model_id")

    metrics = group.get("metrics")
    _require(isinstance(metrics, dict), f"{source}:group.metrics")
    _integer(metrics.get("sample_count"), f"{source}:metrics.sample_count")
    _number(metrics.get("effective_sample_count"), f"{source}:metrics.effective_sample_count")
    _number(metrics.get("mean_rework_count"), f"{source}:metrics.mean_rework_count")
    if metrics.get("weighted_mean_rework_count") is not None:
        _number(metrics.get("weighted_mean_rework_count"), f"{source}:metrics.weighted_mean_rework_count")

    if role == "bounded_worker":
        for key in (
            "accepted_first_pass_rate",
            "final_accepted_rate",
            "tests_passed_rate",
            "any_violation_rate",
        ):
            _rate(metrics.get(key), f"{source}:metrics.{key}")
    else:
        _rate(metrics.get("review_completed_rate"), f"{source}:metrics.review_completed_rate")
        for name in (
            "material_findings_confirmed",
            "false_positive_confirmed",
            "missed_defect_confirmed",
        ):
            total_key = name + "_total"
            known_key = name + "_known_samples"
            if total_key in metrics:
                _integer(metrics.get(total_key), f"{source}:metrics.{total_key}")
            if known_key in metrics:
                _integer(metrics.get(known_key), f"{source}:metrics.{known_key}")
    return group


def _validate_project_state(source: str, state: dict) -> dict:
    _require(isinstance(state, dict), f"{source}:state_not_object")
    _require(state.get("schema_version") == SCHEMA_VERSION, f"{source}:schema_version")
    _require(state.get("repository_scope") == "same_repository_only", f"{source}:repository_scope")
    _require(state.get("usable_for_routing") is True, f"{source}:usable_for_routing")
    scan = state.get("scan")
    _require(isinstance(scan, dict) and scan.get("complete") is True, f"{source}:scan.complete")
    authority = state.get("authority")
    _require(isinstance(authority, dict), f"{source}:authority")
    _require(authority.get("derived_cache_only") is True, f"{source}:authority.derived_cache_only")
    _require(
        authority.get("task_result_validation_acceptance_remain_authoritative") is True,
        f"{source}:authority.task_result_validation_acceptance_remain_authoritative",
    )
    model_groups = state.get("model_groups")
    _require(isinstance(model_groups, list), f"{source}:model_groups")
    for group in model_groups:
        _validate_group(group, source)
    strategy_groups = state.get("strategy_groups", [])
    _require(isinstance(strategy_groups, list), f"{source}:strategy_groups")
    return state


def _weighted_rate(rows: list[tuple[float, float | None]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for weight, value in rows:
        if value is None or weight <= 0.0:
            continue
        numerator += weight * value
        denominator += weight
    if denominator <= 0.0:
        return None
    return round(numerator / denominator, 4)


def _weighted_mean(rows: list[tuple[float, float | None]]) -> float | None:
    return _weighted_rate(rows)


def _aggregate_model_groups(projects: list[tuple[str, dict]]) -> list[dict]:
    buckets: dict[tuple, dict] = {}
    for source, state in projects:
        seen_in_source = set()
        for group in state.get("model_groups", []):
            identity = _group_identity(group)
            _require(identity not in seen_in_source, f"{source}:duplicate_group:{identity}")
            seen_in_source.add(identity)
            bucket = buckets.setdefault(
                identity,
                {
                    "base": {key: group[key] for key in GROUP_KEYS},
                    "model_id": group.get("model_id"),
                    "sources": set(),
                    "groups": [],
                },
            )
            if bucket["model_id"] is not None and group.get("model_id") is not None:
                _require(bucket["model_id"] == group.get("model_id"), f"inconsistent_model_id:{identity}")
            if bucket["model_id"] is None:
                bucket["model_id"] = group.get("model_id")
            bucket["sources"].add(source)
            bucket["groups"].append(group)

    output = []
    for identity in sorted(buckets):
        bucket = buckets[identity]
        groups = bucket["groups"]
        source_list = sorted(bucket["sources"])
        role = bucket["base"]["role"]
        sample_count = sum(int(g["metrics"]["sample_count"]) for g in groups)
        effective = sum(float(g["metrics"]["effective_sample_count"]) for g in groups)

        metrics = {
            "sample_count": sample_count,
            "effective_sample_count": round(effective, 3),
            "evidence_strength": _evidence_strength(effective, len(source_list)),
            "mean_rework_count": _weighted_mean(
                [(float(g["metrics"]["sample_count"]), float(g["metrics"]["mean_rework_count"])) for g in groups]
            ),
            "weighted_mean_rework_count": _weighted_mean(
                [
                    (
                        float(g["metrics"]["effective_sample_count"]),
                        None
                        if g["metrics"].get("weighted_mean_rework_count") is None
                        else float(g["metrics"]["weighted_mean_rework_count"]),
                    )
                    for g in groups
                ]
            ),
        }

        if role == "bounded_worker":
            for key in (
                "accepted_first_pass_rate",
                "final_accepted_rate",
                "tests_passed_rate",
                "any_violation_rate",
            ):
                metrics[key] = _weighted_rate(
                    [
                        (
                            float(g["metrics"]["effective_sample_count"]),
                            None if g["metrics"].get(key) is None else float(g["metrics"][key]),
                        )
                        for g in groups
                    ]
                )
        else:
            metrics["review_completed_rate"] = _weighted_rate(
                [
                    (
                        float(g["metrics"]["effective_sample_count"]),
                        None
                        if g["metrics"].get("review_completed_rate") is None
                        else float(g["metrics"]["review_completed_rate"]),
                    )
                    for g in groups
                ]
            )
            for name in (
                "material_findings_confirmed",
                "false_positive_confirmed",
                "missed_defect_confirmed",
            ):
                metrics[name + "_total"] = sum(int(g["metrics"].get(name + "_total", 0)) for g in groups)
                metrics[name + "_known_samples"] = sum(
                    int(g["metrics"].get(name + "_known_samples", 0)) for g in groups
                )

        row = {
            **bucket["base"],
            "source_project_count": len(source_list),
            "source_repositories": source_list,
            "cross_project_usable": len(source_list) >= 2,
            "metrics": metrics,
        }
        if bucket["model_id"] is not None:
            row["model_id"] = bucket["model_id"]
        output.append(row)
    return output


def aggregate_bundle(bundle: dict) -> dict:
    _require(isinstance(bundle, dict), "bundle_not_object")
    _require(bundle.get("schema_version") == SCHEMA_VERSION, "schema_version")
    hub = bundle.get("hub")
    _require(isinstance(hub, dict), "hub")
    enabled = hub.get("enabled")
    _require(isinstance(enabled, bool), "hub.enabled")
    configured = hub.get("source_repositories")
    _require(isinstance(configured, list) and configured, "hub.source_repositories")
    configured = [_nonempty(value, "hub.source_repositories[]") for value in configured]
    _require(len(configured) == len(set(configured)), "duplicate_configured_source")

    project_states = bundle.get("project_states")
    _require(isinstance(project_states, list), "project_states")
    by_repo = {}
    for item in project_states:
        _require(isinstance(item, dict), "project_state_item")
        repo = _nonempty(item.get("repository"), "project_state.repository")
        _require(repo not in by_repo, f"duplicate_project_state:{repo}")
        _require(repo in configured, f"unconfigured_project_state:{repo}")
        by_repo[repo] = _validate_project_state(repo, item.get("state"))

    missing = [repo for repo in configured if repo not in by_repo]
    _require(not missing, "missing_configured_sources:" + ",".join(missing))

    projects = [(repo, by_repo[repo]) for repo in configured]
    model_groups = _aggregate_model_groups(projects) if enabled else []
    cross_project_group_count = sum(1 for group in model_groups if group["cross_project_usable"])

    return {
        "schema_version": SCHEMA_VERSION,
        "state_title": STATE_TITLE,
        "state_marker": STATE_MARKER,
        "enabled": enabled,
        "usable_for_routing": bool(enabled and len(configured) >= 2 and cross_project_group_count > 0),
        "repository_scope": "same_private_governance_fork_issue",
        "authority": {
            "derived_cache_only": True,
            "source_projects_remain_task_result_validation_acceptance_authority": True,
            "model_routing_remains_canonical_owner": True,
            "may_auto_qualify_or_dequalify_model": False,
            "may_override_task_safety_permission_capability_or_independence": False,
            "may_rewrite_governance_core_rules": False,
        },
        "privacy": {
            "private_source_identity_allowed_inside_owner_trust_boundary": True,
            "automatic_public_upstream_delivery": False,
            "public_adopter_registry_required": False,
            "raw_source_project_payload_copied_to_hub_state": False,
        },
        "source_repositories": configured,
        "source_project_count": len(configured),
        "cross_project_group_count": cross_project_group_count,
        "aggregation_policy": {
            "input_state_marker": PROJECT_STATE_MARKER,
            "group_dimensions": list(GROUP_KEYS),
            "project_local_outranks_private_cross_project": True,
            "minimum_distinct_sources_per_usable_group": 2,
            "effective_sample_weighting": True,
            "worker_validator_metrics_separate": True,
            "single_global_model_score": False,
            "findings_may_propose_governance_task_but_not_rewrite_core": True,
        },
        "model_groups": model_groups,
    }


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON bundle path; omit to read stdin")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    try:
        if args.input:
            with open(args.input, "r", encoding="utf-8") as handle:
                bundle = json.load(handle)
        else:
            bundle = json.load(sys.stdin)
        state = aggregate_bundle(bundle)
    except (OSError, json.JSONDecodeError, HubInputError) as exc:
        print(f"PEH_ERROR: {exc}", file=sys.stderr)
        return 2
    json.dump(state, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
