from __future__ import annotations

import hashlib
import json
import shutil
import types
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO / "tests" / "fixtures" / "public-history"
LEGACY_PATH = FIXTURE_ROOT / "governance_conformance_legacy.py"
MANIFEST_PATH = FIXTURE_ROOT / "conformance_manifest.json"

legacy = types.ModuleType("_governance_conformance_legacy")
legacy.__file__ = str(REPO / "tests" / "test_governance_conformance.py")
legacy.__name__ = "_governance_conformance_legacy"
exec(
    compile(LEGACY_PATH.read_text(encoding="utf-8"), legacy.__file__, "exec"),
    legacy.__dict__,
)

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
_EXPECTED_PROVENANCE = {
    "0.3.14": (legacy.ACCEPTED_0_3_14_COMMIT, legacy.FROZEN_BASELINE_TREE),
    "0.3.15": (legacy.ACCEPTED_0_3_15_COMMIT, legacy.ACCEPTED_0_3_15_TREE),
    "0.3.16": (legacy.ACCEPTED_0_3_16_COMMIT, legacy.ACCEPTED_0_3_16_TREE),
}


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _release(version: str) -> dict[str, object]:
    release = MANIFEST["releases"][version]
    expected_commit, expected_tree = _EXPECTED_PROVENANCE[version]
    if release["source_commit"] != expected_commit:
        raise AssertionError(f"{version} fixture source commit provenance mismatch")
    if release["source_tree"] != expected_tree:
        raise AssertionError(f"{version} fixture source tree provenance mismatch")
    return release


def _storage_relative(relative: str) -> str:
    if relative.startswith("tests/") and relative.endswith(".py"):
        return relative + ".fixture"
    return relative


def _verified_fixture_path(version: str, relative: str) -> Path:
    release = _release(version)
    expected = release["blobs"][relative]
    path = FIXTURE_ROOT / "conformance" / version / _storage_relative(relative)
    data = path.read_bytes()
    actual = _git_blob_sha(data)
    if actual != expected:
        raise AssertionError(
            f"{version}:{relative} retained fixture blob mismatch: {actual} != {expected}"
        )
    return path


def _materialize(
    self: unittest.TestCase,
    version: str,
    root_name: str,
    commit_message: str,
) -> Path:
    root = self.base / root_name
    root.mkdir(parents=True)
    release = _release(version)
    for relative in sorted(release["blobs"]):
        source = _verified_fixture_path(version, relative)
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    legacy.git(root, "init", "-q")
    legacy.git(root, "config", "user.name", "Conformance Fixture")
    legacy.git(root, "config", "user.email", "fixture@example.invalid")
    legacy.git(root, "add", ".")
    legacy.git(root, "commit", "-q", "-m", commit_message)
    return root


def _accepted_baseline_fixture(self):
    return _materialize(
        self,
        "0.3.14",
        "accepted-baseline",
        "accepted 0.3.14 retained-content baseline",
    )


def _accepted_0_3_15_fixture(self):
    return _materialize(
        self,
        "0.3.15",
        "accepted-0.3.15",
        "accepted 0.3.15 retained-content baseline",
    )


def _accepted_0_3_16_fixture(self):
    return _materialize(
        self,
        "0.3.16",
        "accepted-0.3.16",
        "accepted 0.3.16 retained-content baseline",
    )


legacy.ConformanceFixture.accepted_baseline_fixture = _accepted_baseline_fixture
legacy.ConformanceFixture.accepted_0_3_15_fixture = _accepted_0_3_15_fixture
legacy.ConformanceFixture.accepted_0_3_16_fixture = _accepted_0_3_16_fixture

_original_canonical_git_blob_size = legacy.CHECKER.canonical_git_blob_size


def _canonical_git_blob_size(root, ref, relative, evaluation):
    if (
        Path(root).resolve() == REPO.resolve()
        and ref == legacy.ACCEPTED_0_3_15_COMMIT
        and relative in _release("0.3.15")["blobs"]
    ):
        return len(_verified_fixture_path("0.3.15", relative).read_bytes())
    return _original_canonical_git_blob_size(root, ref, relative, evaluation)


legacy.CHECKER.canonical_git_blob_size = _canonical_git_blob_size

for _name, _value in vars(legacy).items():
    if (
        isinstance(_value, type)
        and issubclass(_value, unittest.TestCase)
        and _value is not unittest.TestCase
    ):
        globals()[_name] = _value


if __name__ == "__main__":
    unittest.main()
