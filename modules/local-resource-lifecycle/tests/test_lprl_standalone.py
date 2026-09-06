"""Structural standalone checks for the module-owned LPRL contract."""

from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import unittest


MODULE_ROOT = Path(__file__).resolve().parents[1]
MODULE_REF_PREFIX = PurePosixPath("modules/local-resource-lifecycle")
CORE_ONLY_SENTINELS = (
    Path("config/CONFORMANCE_POLICY.yaml"),
    Path("GOVERNANCE_RELEASE.yaml"),
    Path("templates/GOVERNANCE_LOCK.yaml"),
    Path("templates/GOVERNANCE_CONFORMANCE_CHECK.py"),
    Path(".agent/GOVERNANCE_LOCK"),
)


@contextmanager
def isolated_module():
    """Yield a temporary copy containing only the accepted LPRL module."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        isolated_root = Path(temporary_directory) / MODULE_REF_PREFIX
        shutil.copytree(MODULE_ROOT, isolated_root)
        yield isolated_root


def _scalar_from_match(match):
    """Decode the simple scalar forms used by the asserted module fields."""
    double_quoted, single_quoted, plain = match.groups()
    return double_quoted or single_quoted or plain


def _extract_scalar(path, field_path):
    """Extract only the known top-level or ``governance`` scalar fields."""
    text = path.read_text(encoding="utf-8")
    if len(field_path) == 1:
        key = re.escape(field_path[0])
        pattern = re.compile(
            rf"^{key}:\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s#]+))\s*(?:#.*)?$",
            re.MULTILINE,
        )
        matches = list(pattern.finditer(text))
    elif field_path[0] == "governance" and len(field_path) == 2:
        key = re.escape(field_path[1])
        pattern = re.compile(
            rf"^  {key}:\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s#]+))\s*(?:#.*)?$",
            re.MULTILINE,
        )
        governance = re.search(r"^governance:\s*$", text, re.MULTILINE)
        if governance is None:
            raise AssertionError(f"missing governance section in {path}")
        next_section = re.search(r"^\S", text[governance.end() :], re.MULTILINE)
        section_end = governance.end() + next_section.start() if next_section else len(text)
        matches = list(pattern.finditer(text[governance.end() : section_end]))
    else:
        raise AssertionError(f"unsupported field path: {field_path!r}")

    if len(matches) != 1:
        raise AssertionError(f"expected one {field_path!r} in {path}, found {len(matches)}")
    return _scalar_from_match(matches[0])


def _resolve_module_ref(isolated_root, reference):
    """Rebase an exact module-prefixed POSIX reference into the fixture."""
    reference_path = PurePosixPath(reference)
    if reference_path.is_absolute() or ".." in reference_path.parts:
        raise AssertionError(f"unsafe module reference: {reference!r}")
    try:
        relative_path = reference_path.relative_to(MODULE_REF_PREFIX)
    except ValueError as exc:
        raise AssertionError(f"non-module reference: {reference!r}") from exc
    return isolated_root.joinpath(*relative_path.parts)


class LprlStandaloneHarnessTests(unittest.TestCase):
    def test_isolated_fixture_has_no_core_only_dependency(self):
        with isolated_module() as isolated_root:
            self.assertTrue((isolated_root / "VERSION").is_file())
            for sentinel in CORE_ONLY_SENTINELS:
                self.assertFalse(
                    (isolated_root / sentinel).exists(),
                    f"Core-only sentinel unexpectedly required: {sentinel}",
                )

    def test_canonical_refs_close_inside_isolated_module(self):
        with isolated_module() as isolated_root:
            rules_path = isolated_root / "templates/LPRL_VALIDATION_RULES.yaml"
            result_path = isolated_root / "templates/LPRL_VALIDATION_RESULT.yaml"
            snapshot_path = isolated_root / "templates/LPRL_CONTROL_SNAPSHOT.yaml"

            refs = (
                (rules_path, ("validation_result_schema_ref",), result_path),
                (result_path, ("ruleset_ref",), rules_path),
                (
                    snapshot_path,
                    ("governance", "validation_rules_ref"),
                    rules_path,
                ),
                (
                    snapshot_path,
                    ("governance", "validation_result_schema_ref"),
                    result_path,
                ),
            )
            for source_path, field_path, expected_path in refs:
                reference = _extract_scalar(source_path, field_path)
                resolved_path = _resolve_module_ref(isolated_root, reference)
                self.assertEqual(resolved_path, expected_path)
                self.assertTrue(resolved_path.is_file())
                resolved_path.relative_to(isolated_root)

    def test_module_version_and_validation_schema_versions_are_coherent(self):
        with isolated_module() as isolated_root:
            module_version = (isolated_root / "VERSION").read_text(encoding="utf-8").strip()
            rules_version = _extract_scalar(
                isolated_root / "templates/LPRL_VALIDATION_RULES.yaml",
                ("schema_version",),
            )
            result_version = _extract_scalar(
                isolated_root / "templates/LPRL_VALIDATION_RESULT.yaml",
                ("schema_version",),
            )

            self.assertTrue(module_version)
            self.assertEqual(rules_version, module_version)
            self.assertEqual(result_version, module_version)

    def test_validation_result_contract_has_one_canonical_file(self):
        with isolated_module() as isolated_root:
            result_files = sorted(
                path.relative_to(isolated_root)
                for path in isolated_root.rglob("LPRL_VALIDATION_RESULT.yaml")
            )
            self.assertEqual(
                result_files,
                [Path("templates/LPRL_VALIDATION_RESULT.yaml")],
            )

            rules_reference = _extract_scalar(
                isolated_root / "templates/LPRL_VALIDATION_RULES.yaml",
                ("validation_result_schema_ref",),
            )
            self.assertEqual(
                _resolve_module_ref(isolated_root, rules_reference),
                isolated_root / "templates/LPRL_VALIDATION_RESULT.yaml",
            )


if __name__ == "__main__":
    unittest.main()
