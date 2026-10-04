#!/usr/bin/env python3
"""质量评分落盘器必须独立运行，不依赖调用方配置 PYTHONPATH。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "save_quality_score_output.py"


class SaveQualityScoreOutputTest(unittest.TestCase):
    def test_resolves_listing_core_path_helper(self) -> None:
        payload = {
            "scorePanel": {
                "overall": 88,
                "grade": "B+",
                "items": [{"name": "标题", "score": 88, "state": "pass"}],
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "SESSION_ID": "score-output-contract"}
            result = subprocess.run(
                [sys.executable, str(SCRIPT), json.dumps(payload, ensure_ascii=False)],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Saved full response:", result.stdout)
        self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
