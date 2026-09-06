#!/usr/bin/env python3
"""Deterministic GitHub-native LiveBench prior refresher (stdlib only)."""

from __future__ import annotations

import argparse, base64, csv, io, json, os, re, sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONFIG = Path("config/EXTERNAL_MODEL_EVIDENCE_SOURCE.yaml")
EVIDENCE = Path("config/EXTERNAL_MODEL_EVIDENCE.yaml")
EXIT_CHANGED = 10
COLUMNS = [
    "model_key", "source_model_label", "benchmark_group", "benchmark",
    "source_native_metric", "benchmark_or_methodology_version",
    "source_ref", "model_identity_match",
]


class EvidenceError(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"{path} must contain an object")
    return value


def dump(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def api(config: dict[str, Any], suffix: str) -> Any:
    repo = config["source"]["repository"]
    if repo != "LiveBench/new-livebench":
        raise EvidenceError("v1 source repository is fixed")
    url = f"https://api.github.com/repos/{repo}/{suffix}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "agent-dev-governance-external-evidence/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            return json.loads(response.read().decode())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"public GitHub fetch failed: {exc}") from exc


def branch_commit(config: dict[str, Any]) -> str:
    branch = config["source"]["branch_for_future_refresh"]
    payload = api(config, f"branches/{branch}")
    sha = payload.get("commit", {}).get("sha") if isinstance(payload, dict) else None
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise EvidenceError("source branch has no exact commit SHA")
    return sha


def latest_pair(config: dict[str, Any], commit: str) -> tuple[str, str, str]:
    directory = config["source"]["public_directory"]
    payload = api(config, f"contents/{directory}?ref={commit}")
    if not isinstance(payload, list):
        raise EvidenceError("source directory response is not a list")
    tables, cats = {}, {}
    tr = re.compile(config["source"]["table_pattern"])
    cr = re.compile(config["source"]["categories_pattern"])
    for item in payload:
        name = item.get("name") if isinstance(item, dict) else None
        if not isinstance(name, str):
            continue
        m = tr.fullmatch(name)
        if m:
            tables[m.group(1)] = item.get("path")
        m = cr.fullmatch(name)
        if m:
            cats[m.group(1)] = item.get("path")
    pairs = sorted(set(tables) & set(cats))
    if not pairs:
        raise EvidenceError("no valid table/categories pair")
    token = pairs[-1]
    return token.replace("_", "-"), tables[token], cats[token]


def content(config: dict[str, Any], path: str, commit: str) -> tuple[str, str]:
    payload = api(config, f"contents/{path}?ref={commit}")
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise EvidenceError(f"invalid content response for {path}")
    sha, encoded = payload.get("sha"), payload.get("content")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise EvidenceError(f"missing blob SHA for {path}")
    if not isinstance(encoded, str):
        raise EvidenceError(f"missing content for {path}")
    try:
        return base64.b64decode(encoded).decode(), sha
    except Exception as exc:
        raise EvidenceError(f"cannot decode {path}") from exc


def fetch(config: dict[str, Any], release: str | None, commit: str | None) -> dict[str, str]:
    commit = commit or branch_commit(config)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise EvidenceError("source commit must be exact")
    if release:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", release):
            raise EvidenceError("release must use YYYY-MM-DD")
        token = release.replace("-", "_")
        table, cats = f"public/table_{token}.csv", f"public/categories_{token}.json"
    else:
        release, table, cats = latest_pair(config, commit)
    table_text, table_sha = content(config, table, commit)
    cats_text, cats_sha = content(config, cats, commit)
    return {
        "source_commit": commit, "source_release": release,
        "table_path": table, "table_blob_sha": table_sha, "table_text": table_text,
        "categories_path": cats, "categories_blob_sha": cats_sha, "categories_text": cats_text,
    }


def metric(raw: str) -> int | float:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise EvidenceError(f"invalid metric {raw!r}") from exc
    if not value.is_finite():
        raise EvidenceError("non-finite metric")
    return int(value) if value == value.to_integral() else float(value)


def normalize(config: dict[str, Any], source: dict[str, str], collected_at: str) -> dict[str, Any]:
    try:
        categories = json.loads(source["categories_text"])
    except json.JSONDecodeError as exc:
        raise EvidenceError("categories JSON invalid") from exc
    if not isinstance(categories, dict):
        raise EvidenceError("categories must be an object")

    membership = {}
    for group, names in categories.items():
        if not isinstance(group, str) or not isinstance(names, list):
            raise EvidenceError("categories schema drift")
        for name in names:
            if not isinstance(name, str) or name in membership:
                raise EvidenceError("categories schema drift")
            membership[name] = group

    reader = csv.DictReader(io.StringIO(source["table_text"]))
    if not reader.fieldnames or reader.fieldnames[0] != "model":
        raise EvidenceError("table schema drift")
    if set(reader.fieldnames[1:]) != set(membership):
        raise EvidenceError("table/categories metric set drift")
    source_rows = {}
    for row in reader:
        label = row.get("model")
        if label:
            if label in source_rows:
                raise EvidenceError(f"duplicate model row {label}")
            source_rows[label] = row

    selected = config.get("representative_benchmarks")
    if not isinstance(selected, dict) or set(selected) != set(categories):
        raise EvidenceError("representative benchmark groups must match source groups")
    for group, bench in selected.items():
        if membership.get(bench) != group:
            raise EvidenceError(f"selected benchmark missing/moved: {group}/{bench}")

    mappings = config.get("model_mappings")
    if not isinstance(mappings, dict) or len(mappings) != 4:
        raise EvidenceError("exact four model mappings required")
    observations = []
    series = f"livebench-release-{source['source_release']}"
    source_ref = (
        f"{config['source']['repository']}@{source['source_commit']}:"
        f"{source['table_path']}"
    )
    for model_key in sorted(mappings):
        mapping = mappings[model_key]
        label = mapping.get("source_model_label") if isinstance(mapping, dict) else None
        identity = mapping.get("model_identity_match") if isinstance(mapping, dict) else None
        if not isinstance(label, str) or not isinstance(identity, str):
            raise EvidenceError(f"invalid mapping {model_key}")
        row = source_rows.get(label)
        if row is None:
            raise EvidenceError(f"required exact mapped source row missing: {label}")
        for group in sorted(selected):
            bench = selected[group]
            raw = row.get(bench)
            if raw is None or raw == "":
                raise EvidenceError(f"missing selected metric {label}/{bench}")
            observations.append([
                model_key, label, group, bench, metric(raw), series, source_ref, identity
            ])

    if len(observations) != 28:
        raise EvidenceError("v1 must emit exactly 28 observations")
    return {
        "schema_version": "0.1",
        "status": "accepted_external_benchmark_prior",
        "provenance": {
            "source_id": config["source"]["source_id"],
            "source_repository": config["source"]["repository"],
            "source_commit": source["source_commit"],
            "source_release": source["source_release"],
            "table_path": source["table_path"],
            "table_blob_sha": source["table_blob_sha"],
            "categories_path": source["categories_path"],
            "categories_blob_sha": source["categories_blob_sha"],
            "collected_at": collected_at,
        },
        "authority": {
            "evidence_only": True,
            "may_auto_change_model_registry_status": False,
            "may_bypass_qualification": False,
            "may_directly_promote_or_demote_production_route": False,
            "higher_precedence_internal_evidence": [
                "project_local_calibration", "governance_calibration_snapshot"
            ],
        },
        "observation_columns": COLUMNS,
        "observation_rows": observations,
    }


def material(value: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(value))
    if isinstance(value.get("provenance"), dict):
        value["provenance"].pop("collected_at", None)
    if isinstance(value.get("observation_rows"), list):
        value["observation_rows"] = sorted(
            value["observation_rows"], key=lambda row: tuple(str(x) for x in row)
        )
    return value


def materially_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return material(left) == material(right)


def validate_initial_anchor(config: dict[str, Any], source: dict[str, str]) -> None:
    anchor = config["initial_anchor"]
    for key in (
        "source_commit", "source_release", "table_path", "table_blob_sha",
        "categories_path", "categories_blob_sha",
    ):
        if source[key] != anchor[key]:
            raise EvidenceError(f"initial anchor mismatch: {key}")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-config", type=Path, default=CONFIG)
    p.add_argument("--output", type=Path, default=EVIDENCE)
    p.add_argument("--release")
    p.add_argument("--source-commit")
    p.add_argument("--collected-at")
    p.add_argument("--mode", choices=["check", "write", "stdout", "metadata"], default="check")
    p.add_argument("--metadata-file", type=Path)
    p.add_argument("--require-initial-anchor", action="store_true")
    args = p.parse_args()
    try:
        config = load(args.source_config)
        source = fetch(config, args.release, args.source_commit)
        if args.require_initial_anchor:
            validate_initial_anchor(config, source)
        candidate = normalize(config, source, args.collected_at or now())
        meta = {k: source[k] for k in (
            "source_commit", "source_release", "table_path", "table_blob_sha",
            "categories_path", "categories_blob_sha",
        )}
        if args.metadata_file:
            atomic_write(args.metadata_file, json.dumps(meta, sort_keys=True) + "\n")
        if args.mode == "metadata":
            print(json.dumps(meta, sort_keys=True))
            return 0
        if args.mode == "stdout":
            sys.stdout.write(dump(candidate))
            return 0
        if args.mode == "write":
            atomic_write(args.output, dump(candidate))
            print(f"WROTE {args.output} {source['source_release']} {source['table_blob_sha']}")
            return 0
        if not args.output.is_file():
            print("MATERIAL_CHANGE: accepted evidence missing")
            return EXIT_CHANGED
        if materially_equal(load(args.output), candidate):
            print(f"NO_MATERIAL_CHANGE {source['source_release']} {source['table_blob_sha']}")
            return 0
        print(f"MATERIAL_CHANGE {source['source_release']} {source['table_blob_sha']}")
        return EXIT_CHANGED
    except EvidenceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
