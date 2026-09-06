from __future__ import annotations

import hashlib
import json
import types
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO / "tests" / "fixtures" / "public-history"
LEGACY_PATH = FIXTURE_ROOT / "external_model_evidence_legacy.py"
MANIFEST_PATH = FIXTURE_ROOT / "external_model_evidence_manifest.json"

legacy = types.ModuleType("_external_model_evidence_legacy")
legacy.__file__ = str(REPO / "tests" / "test_external_model_evidence.py")
legacy.__name__ = "_external_model_evidence_legacy"
exec(
    compile(LEGACY_PATH.read_text(encoding="utf-8"), legacy.__file__, "exec"),
    legacy.__dict__,
)

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _storage_relative(relative: str) -> str:
    if relative.startswith("tests/") and relative.endswith(".py"):
        return relative + ".fixture"
    return relative


def _verified_shared_bytes(section: str, relative: str) -> bytes:
    source = MANIFEST[section]
    expected_commit = (
        legacy.BASELINE if section == "baseline" else legacy.ACCEPTED_0_3_18
    )
    if source["source_commit"] != expected_commit:
        raise AssertionError(f"{section} fixture source commit provenance mismatch")
    expected_blob = source["blobs"][relative]
    path = (
        FIXTURE_ROOT
        / "external-model-evidence"
        / "shared"
        / _storage_relative(relative)
    )
    data = path.read_bytes()
    actual_blob = _git_blob_sha(data)
    if actual_blob != expected_blob:
        raise AssertionError(
            f"{section}:{relative} retained fixture blob mismatch: "
            f"{actual_blob} != {expected_blob}"
        )
    return data


def _baseline_bytes(relative: str) -> bytes:
    return _verified_shared_bytes("baseline", relative)


def _accepted_release_bytes(relative: str) -> bytes:
    return _verified_shared_bytes("accepted_release", relative)


legacy.baseline_bytes = _baseline_bytes
legacy.accepted_release_bytes = _accepted_release_bytes

_original_git = legacy.git


def _git(*args):
    candidate = MANIFEST["accepted_candidate"]
    candidate_commit = candidate["source_commit"]
    if args == (
        "diff",
        "--name-status",
        f"{legacy.BASELINE}...{candidate_commit}",
    ):
        return candidate["diff_name_status"]
    if len(args) == 3 and args[0] == "cat-file" and args[1] == "-s":
        prefix = f"{candidate_commit}:"
        if args[2].startswith(prefix):
            relative = args[2][len(prefix):]
            if relative in candidate["blob_sizes"]:
                return str(candidate["blob_sizes"][relative])
    return _original_git(*args)


legacy.git = _git

for _name, _value in vars(legacy).items():
    if (
        isinstance(_value, type)
        and issubclass(_value, unittest.TestCase)
        and _value is not unittest.TestCase
    ):
        globals()[_name] = _value


if __name__ == "__main__":
    unittest.main()
