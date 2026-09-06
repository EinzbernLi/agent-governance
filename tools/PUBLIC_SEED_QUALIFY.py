#!/usr/bin/env python3
"""Deterministic, read-only qualifier for a derived clean public seed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Any


DEFAULT_POLICY_PATH = "config/PUBLIC_SEED_POLICY.json"

SECRET_PATTERNS = (
    ("pem_private_key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("sk_style_secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
)

_MAC_HOME_RE = re.compile(re.escape("/" + "Users" + "/") + r"[^/\s\"'<>]+/")
_LINUX_HOME_RE = re.compile(re.escape("/" + "home" + "/") + r"[^/\s\"'<>]+/")
_WINDOWS_HOME_RE = re.compile(
    r"\b[A-Za-z]:" + re.escape("\\" + "Users" + "\\") + r"[^\\\s\"'<>]+\\"
)
HOME_PATH_PATTERNS = (
    ("macos_user_home", _MAC_HOME_RE),
    ("linux_user_home", _LINUX_HOME_RE),
    ("windows_user_home", _WINDOWS_HOME_RE),
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse policy {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("public seed policy must be a JSON object")
    return data


def _require_list_of_strings(mapping: dict[str, Any], key: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"policy field {key!r} must be a non-empty-string list")
    return list(value)


def _validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != "1.0":
        raise ValueError("unsupported public seed policy schema")
    if policy.get("source_authority") != "accepted_private_main":
        raise ValueError("source_authority must be accepted_private_main")

    history = policy.get("history")
    if not isinstance(history, dict):
        raise ValueError("history policy is required")
    if history.get("inherit_private_git_history") is not False:
        raise ValueError("private Git history inheritance must be false")
    if history.get("future_public_history") != "fresh_root_required":
        raise ValueError("future public history must require a fresh root")

    excluded = policy.get("exclude")
    if not isinstance(excluded, dict):
        raise ValueError("exclude policy is required")
    prefixes = _require_list_of_strings(excluded, "prefixes")
    exact = _require_list_of_strings(excluded, "exact")
    for required in (".agent/", ".publicization/"):
        if required not in prefixes:
            raise ValueError(f"required excluded prefix missing: {required}")
    if "CHANGELOG.md" not in exact:
        raise ValueError("current private CHANGELOG.md must be excluded")

    regeneration = _require_list_of_strings(policy, "regenerate_after_public_identity")
    for required in (
        ".agent/BOOTSTRAP.md",
        ".agent/PROJECT_STATE.md",
        "CHANGELOG.md",
    ):
        if required not in regeneration:
            raise ValueError(f"required regeneration surface missing: {required}")

    _require_list_of_strings(policy, "required_retained_paths")

    qualification = policy.get("qualification")
    if not isinstance(qualification, dict):
        raise ValueError("qualification policy is required")
    denylist_path = qualification.get("private_denylist_path")
    if not isinstance(denylist_path, str) or not denylist_path:
        raise ValueError("private_denylist_path is required")
    for flag in (
        "scan_private_literals",
        "scan_strong_secrets",
        "scan_user_home_absolute_paths",
    ):
        if qualification.get(flag) is not True:
            raise ValueError(f"{flag} must be true")

    authority = policy.get("publication_authority")
    if not isinstance(authority, dict):
        raise ValueError("publication_authority policy is required")
    if authority.get("qualifies_content_only") is not True:
        raise ValueError("qualification must be content-only")
    for flag in (
        "authorizes_publication",
        "decides_namespace",
        "decides_license",
        "decides_first_public_version",
        "decides_console_first_tag_inclusion",
    ):
        if authority.get(flag) is not False:
            raise ValueError(f"{flag} must be false")


def _load_denylist(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read private denylist {path}: {exc}") from exc
    values = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
    if not values:
        raise ValueError("private denylist must contain at least one literal")
    return values


def _tracked_files(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"git ls-files failed for {root}: {exc}") from exc
    return sorted(
        part.decode("utf-8")
        for part in completed.stdout.split(b"\0")
        if part
    )


def _is_excluded(path: str, *, prefixes: list[str], exact: list[str]) -> bool:
    return path in exact or any(path.startswith(prefix) for prefix in prefixes)


def _read_text_if_safe(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read tracked file {path}: {exc}") from exc
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def qualify(
    root: str | Path,
    *,
    policy_path: str = DEFAULT_POLICY_PATH,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    policy = _load_json(root_path / policy_path)
    _validate_policy(policy)

    excluded_policy = policy["exclude"]
    prefixes = list(excluded_policy["prefixes"])
    exact = list(excluded_policy["exact"])
    denylist_relative = policy["qualification"]["private_denylist_path"]
    denylist = _load_denylist(root_path / denylist_relative)

    tracked = _tracked_files(root_path)
    included = [
        path
        for path in tracked
        if not _is_excluded(path, prefixes=prefixes, exact=exact)
    ]
    excluded = sorted(set(tracked) - set(included))
    violations: list[dict[str, Any]] = []

    for forbidden_path in tracked:
        if (
            forbidden_path.startswith(".agent/")
            or forbidden_path.startswith(".publicization/")
            or forbidden_path == "CHANGELOG.md"
        ) and forbidden_path in included:
            violations.append(
                {"kind": "excluded_surface_included", "path": forbidden_path}
            )

    required = list(policy["required_retained_paths"])
    for path in required:
        if path not in included:
            violations.append({"kind": "required_retained_missing", "path": path})

    if denylist_relative in included:
        violations.append(
            {"kind": "private_denylist_included", "path": denylist_relative}
        )

    for relative in included:
        text = _read_text_if_safe(root_path / relative)
        if text is None:
            continue

        for index, literal in enumerate(denylist):
            start = text.find(literal)
            if start >= 0:
                violations.append(
                    {
                        "kind": "private_literal",
                        "path": relative,
                        "line": _line_number(text, start),
                        "literal_index": index,
                    }
                )

        for name, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                violations.append(
                    {
                        "kind": "strong_secret",
                        "pattern": name,
                        "path": relative,
                        "line": _line_number(text, match.start()),
                    }
                )

        for name, pattern in HOME_PATH_PATTERNS:
            match = pattern.search(text)
            if match:
                violations.append(
                    {
                        "kind": "user_home_absolute_path",
                        "pattern": name,
                        "path": relative,
                        "line": _line_number(text, match.start()),
                    }
                )

    violations.sort(
        key=lambda item: (
            str(item.get("path", "")),
            str(item.get("kind", "")),
            str(item.get("pattern", "")),
            int(item.get("line", 0)),
        )
    )

    history = policy["history"]
    return {
        "overall": "PASS" if not violations else "FAIL",
        "policy_schema_version": policy["schema_version"],
        "source_authority": policy["source_authority"],
        "history_policy": {
            "inherit_private_git_history": history["inherit_private_git_history"],
            "future_public_history": history["future_public_history"],
        },
        "regeneration_required": list(policy["regenerate_after_public_identity"]),
        "included_count": len(included),
        "included_paths": included,
        "excluded_count": len(excluded),
        "excluded_paths": excluded,
        "violations": violations,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="repository root containing the tracked private accepted checkout",
    )
    parser.add_argument(
        "--policy",
        default=DEFAULT_POLICY_PATH,
        help="policy path relative to --root",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the full machine-readable qualification result",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = qualify(args.root, policy_path=args.policy)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"overall": "FAIL", "error": str(exc)}, sort_keys=True))
        else:
            print(f"PUBLIC_SEED_QUALIFICATION: FAIL ({exc})")
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            "PUBLIC_SEED_QUALIFICATION: "
            f"{result['overall']} "
            f"included={result['included_count']} "
            f"excluded={result['excluded_count']} "
            f"violations={len(result['violations'])}"
        )
        print(
            "history="
            f"{result['history_policy']['future_public_history']} "
            "inherit_private_git_history="
            f"{str(result['history_policy']['inherit_private_git_history']).lower()}"
        )
        for violation in result["violations"]:
            fields = " ".join(
                f"{key}={value}"
                for key, value in violation.items()
                if key != "literal_index"
            )
            print(f"violation {fields}")

    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
