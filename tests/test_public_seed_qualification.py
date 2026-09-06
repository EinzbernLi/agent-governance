from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO / "tests" / "fixtures" / "public-history"
LEGACY_PATH = FIXTURE_ROOT / "public_seed_qualification_legacy.py"
REPLAY_ENV = "GOVERNANCE_PUBLIC_SEED_FRESH_ROOT_REPLAY"

legacy = types.ModuleType("_public_seed_qualification_legacy")
legacy.__file__ = str(REPO / "tests" / "test_public_seed_qualification.py")
legacy.__name__ = "_public_seed_qualification_legacy"
exec(
    compile(LEGACY_PATH.read_text(encoding="utf-8"), legacy.__file__, "exec"),
    legacy.__dict__,
)

for _name, _value in vars(legacy).items():
    if (
        isinstance(_value, type)
        and issubclass(_value, unittest.TestCase)
        and _value is not unittest.TestCase
    ):
        globals()[_name] = _value


class FreshRootRetainedSuiteTests(unittest.TestCase):
    def test_qualified_seed_retained_suite_passes_in_fresh_git_root(self) -> None:
        if os.environ.get(REPLAY_ENV) == "1":
            return
        if not (REPO / legacy.DENYLIST_PATH).exists():
            return

        qualification = legacy.qualify(REPO)
        self.assertEqual(
            qualification["overall"],
            "PASS",
            msg=f"public seed qualification failed: {qualification['violations']}",
        )

        with tempfile.TemporaryDirectory() as temp:
            fresh = Path(temp) / "fresh-public-root"
            fresh.mkdir()
            for relative in qualification["included_paths"]:
                source = REPO / relative
                target = fresh / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

            subprocess.run(["git", "init", "-q", str(fresh)], check=True)
            subprocess.run(
                ["git", "-C", str(fresh), "config", "user.name", "Fresh Root Fixture"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(fresh),
                    "config",
                    "user.email",
                    "fixture@example.invalid",
                ],
                check=True,
            )
            subprocess.run(["git", "-C", str(fresh), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(fresh), "commit", "-q", "-m", "fresh public seed"],
                check=True,
            )

            historical_commits = (
                "db193e1ae6f5c92f512034444354549581c0b843",
                "971458bfe2bde2963edac2bc33862ecc3b83999c",
                "78f2936dec3185b76fe5b46a6e4e59d0f3751f41",
                "e49eb7c878bf2a91674b12781a2185264411848b",
                "7f0b0158092aa39c53540e6ff87dbabb1c9fc6af",
                "172314103fe8d2eb5bc61802e1c4f71db81599a2",
            )
            for historical in historical_commits:
                probe = subprocess.run(
                    ["git", "-C", str(fresh), "cat-file", "-e", f"{historical}^{{commit}}"],
                    capture_output=True,
                )
                self.assertNotEqual(
                    probe.returncode,
                    0,
                    msg=f"fresh root unexpectedly inherited historical commit {historical}",
                )

            env = os.environ.copy()
            env[REPLAY_ENV] = "1"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test*.py",
                ],
                cwd=fresh,
                env=env,
                capture_output=True,
                text=True,
            )
            combined = completed.stdout + completed.stderr
            self.assertEqual(completed.returncode, 0, msg=combined)
            self.assertIn("OK", combined)
            for historical in historical_commits:
                self.assertNotIn(historical, combined)
            self.assertNotIn("fatal: bad object", combined.lower())
            self.assertNotIn("not a valid object name", combined.lower())
            self.assertNotIn("unknown revision", combined.lower())


if __name__ == "__main__":
    unittest.main()
