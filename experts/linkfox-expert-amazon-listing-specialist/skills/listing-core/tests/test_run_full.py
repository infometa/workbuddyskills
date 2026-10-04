from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_full.py"


class RunFullPortableTest(unittest.TestCase):
    def test_start_builds_local_run_without_platform_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "start", "--run-dir", str(run_dir),
                "--mode", "create", "--evidence-mode", "facts_only",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            spec = json.loads((run_dir / "03-write" / "spec.json").read_text())
            self.assertTrue(spec["performance_contract"]["provided_evidence_only"])
            self.assertEqual(spec["performance_contract"]["portable_outputs"], ["json", "markdown"])


if __name__ == "__main__":
    unittest.main()
