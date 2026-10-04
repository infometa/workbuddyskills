from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preflight.py"
SPEC = importlib.util.spec_from_file_location("listing_core_preflight", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_complete_runtime(source: Path) -> None:
    source.parent.mkdir(parents=True, exist_ok=True)
    source.touch()
    for relative in MODULE.REQUIRED_FILES:
        target = source.parent / relative
        flags = MODULE.REQUIRED_CLI_FLAGS.get(relative, set())
        target.write_text(
            "\n".join(f"parser.add_argument({flag!r})" for flag in sorted(flags)),
            encoding="utf-8",
        )


class PreflightTest(unittest.TestCase):
    def test_accepts_complete_skill_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "workspaces" / ".ce" / "skills"
            source = skills / "listing-core" / "scripts" / "preflight.py"
            make_complete_runtime(source)

            result = MODULE.inspect_runtime(source)

            self.assertTrue(result["ok"])
            self.assertEqual(result["scripts_root"], str(source.parent.resolve()))
            self.assertEqual(result["incompatible"], {})

    def test_reports_missing_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "workspaces" / ".ce" / "skills" / "listing-core" / "scripts" / "preflight.py"
            source.parent.mkdir(parents=True)
            source.touch()

            result = MODULE.inspect_runtime(source)

            self.assertFalse(result["ok"])
            self.assertIn("run_manifest.py", result["missing"])

    def test_reports_incompatible_hot_path_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "skills" / "listing-core" / "scripts" / "preflight.py"
            make_complete_runtime(source)
            run_full = source.parent / "run_full.py"
            run_full.write_text("parser.add_argument('--run-dir')", encoding="utf-8")

            result = MODULE.inspect_runtime(source)

            self.assertFalse(result["ok"])
            self.assertIn("--deductions", result["incompatible"]["run_full.py"])


if __name__ == "__main__":
    unittest.main()
