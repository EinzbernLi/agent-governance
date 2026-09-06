from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.PUBLIC_SEED_QUALIFY import qualify


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "PUBLIC_SEED_POLICY.json"
DENYLIST_PATH = ".publicization/PRIVATE_SEED_DENYLIST.txt"


def _fixture_policy() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "source_authority": "accepted_private_main",
        "history": {
            "inherit_private_git_history": False,
            "future_public_history": "fresh_root_required",
        },
        "exclude": {
            "prefixes": [".agent/", ".publicization/"],
            "exact": ["CHANGELOG.md"],
        },
        "regenerate_after_public_identity": [
            ".agent/BOOTSTRAP.md",
            ".agent/PROJECT_STATE.md",
            "CHANGELOG.md",
        ],
        "required_retained_paths": ["README.md"],
        "qualification": {
            "private_denylist_path": DENYLIST_PATH,
            "scan_private_literals": True,
            "scan_strong_secrets": True,
            "scan_user_home_absolute_paths": True,
        },
        "publication_authority": {
            "qualifies_content_only": True,
            "authorizes_publication": False,
            "decides_namespace": False,
            "decides_license": False,
            "decides_first_public_version": False,
            "decides_console_first_tag_inclusion": False,
        },
    }


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_fixture(root: Path) -> None:
    _write(
        root,
        "config/PUBLIC_SEED_POLICY.json",
        json.dumps(_fixture_policy(), indent=2) + "\n",
    )
    _write(root, DENYLIST_PATH, "private-owner/private-repo\nprivate-pilot\n")
    _write(root, "README.md", "generic seed fixture\n")
    _write(root, ".agent/BOOTSTRAP.md", "private continuity\n")
    _write(root, "CHANGELOG.md", "private development history\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)


def _snapshot_tracked(root: Path) -> dict[str, str]:
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    result: dict[str, str] = {}
    for raw in listed.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8")
        result[relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    return result


class PublicSeedQualificationTests(unittest.TestCase):
    def test_policy_freezes_clean_seed_boundaries(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

        self.assertFalse(policy["history"]["inherit_private_git_history"])
        self.assertEqual(
            policy["history"]["future_public_history"],
            "fresh_root_required",
        )
        self.assertEqual(
            set(policy["exclude"]["prefixes"]),
            {".agent/", ".publicization/"},
        )
        self.assertEqual(policy["exclude"]["exact"], ["CHANGELOG.md"])
        self.assertEqual(
            set(policy["regenerate_after_public_identity"]),
            {
                ".agent/BOOTSTRAP.md",
                ".agent/PROJECT_STATE.md",
                "CHANGELOG.md",
            },
        )
        self.assertFalse(
            policy["publication_authority"]["authorizes_publication"]
        )
        self.assertFalse(policy["publication_authority"]["decides_license"])

    def test_current_private_tree_qualifies_as_derived_seed_view(self) -> None:
        if not (ROOT / DENYLIST_PATH).exists():
            self.skipTest(
                "current-tree clean-seed qualification applies to private source checkouts"
            )
        result = qualify(ROOT)

        self.assertEqual(result["overall"], "PASS")
        self.assertEqual(result["violations"], [])
        self.assertFalse(result["history_policy"]["inherit_private_git_history"])
        self.assertEqual(
            result["history_policy"]["future_public_history"],
            "fresh_root_required",
        )

        included = set(result["included_paths"])
        excluded = set(result["excluded_paths"])
        self.assertNotIn("CHANGELOG.md", included)
        self.assertIn("CHANGELOG.md", excluded)
        self.assertFalse(any(path.startswith(".agent/") for path in included))
        self.assertTrue(any(path.startswith(".agent/") for path in excluded))
        self.assertNotIn(DENYLIST_PATH, included)
        self.assertIn(DENYLIST_PATH, excluded)

        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        for required in policy["required_retained_paths"]:
            self.assertIn(required, included)

    def test_private_literal_in_retained_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _init_fixture(root)
            _write(
                root,
                "leak.txt",
                "do not publish private-owner/private-repo here\n",
            )
            subprocess.run(["git", "-C", str(root), "add", "leak.txt"], check=True)

            result = qualify(root)

        self.assertEqual(result["overall"], "FAIL")
        self.assertTrue(
            any(item["kind"] == "private_literal" for item in result["violations"])
        )

    def test_strong_secret_in_retained_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _init_fixture(root)
            synthetic_secret = "gh" + "p_" + ("A" * 32)
            _write(root, "secret.txt", synthetic_secret + "\n")
            subprocess.run(["git", "-C", str(root), "add", "secret.txt"], check=True)

            result = qualify(root)

        self.assertEqual(result["overall"], "FAIL")
        self.assertTrue(
            any(item["kind"] == "strong_secret" for item in result["violations"])
        )

    def test_user_home_absolute_path_in_retained_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _init_fixture(root)
            synthetic_home = "/" + "home" + "/alice/project/file.txt"
            _write(root, "path.txt", synthetic_home + "\n")
            subprocess.run(["git", "-C", str(root), "add", "path.txt"], check=True)

            result = qualify(root)

        self.assertEqual(result["overall"], "FAIL")
        self.assertTrue(
            any(
                item["kind"] == "user_home_absolute_path"
                for item in result["violations"]
            )
        )

    def test_qualifier_is_read_only_for_tracked_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _init_fixture(root)
            before = _snapshot_tracked(root)

            result = qualify(root)

            after = _snapshot_tracked(root)

        self.assertEqual(result["overall"], "PASS")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
