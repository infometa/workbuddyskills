#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_scored_report.py"
SPEC = importlib.util.spec_from_file_location("render_scored_report", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def scored_panel(overall: int = 86) -> dict:
    return {
        "overall": overall,
        "grade": "B+",
        "insufficientData": False,
        "items": [{"name": "平台合规与风险", "score": 90, "state": "ok"}],
    }


class RenderScoredReportTest(unittest.TestCase):
    def test_rejects_core_placeholder_panel(self) -> None:
        with self.assertRaisesRegex(ValueError, "canonical 数字评分"):
            MODULE.validate_scored_report({
                "scorePanel": {
                    "overall": None,
                    "grade": "—",
                    "insufficientData": True,
                    "items": [{"name": "标题", "score": None, "state": "na"}],
                }
            })

    def test_requires_every_variant_to_have_an_effective_score(self) -> None:
        with self.assertRaisesRegex(ValueError, r"products\[0\]\.variants\[1\]"):
            MODULE.validate_scored_report({
                "products": [{
                    "variants": [
                        {"scorePanel": scored_panel()},
                        {"listing": {"title": "missing score"}},
                    ]
                }]
            })

    def test_cli_does_not_invoke_renderer_when_score_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "report.json"
            source.write_text(json.dumps({"scorePanel": {"overall": None}}), encoding="utf-8")
            marker = workdir / "renderer-called"
            renderer = workdir / "renderer.mjs"
            renderer.write_text(
                f"require('fs').writeFileSync({json.dumps(str(marker))}, 'called')",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input", str(source),
                    "--renderer", str(renderer),
                    "--output", str(workdir / "report.html"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("overall=null", result.stderr)
            self.assertFalse(marker.exists())

    def test_accepts_scored_single_and_inherited_batch_panels(self) -> None:
        MODULE.validate_scored_report({"scorePanel": scored_panel()})
        MODULE.validate_scored_report({
            "scorePanel": scored_panel(),
            "products": [{"variants": [{"listing": {"title": "A"}}]}],
        })
        MODULE.validate_scored_report({
            "listings": [
                {"scorePanel": scored_panel(90)},
                {"scorePanel": scored_panel(78)},
            ]
        })

    def test_cli_invokes_renderer_after_score_gate_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "report.json"
            source.write_text(json.dumps({"scorePanel": scored_panel()}), encoding="utf-8")
            renderer = workdir / "renderer.mjs"
            renderer.write_text(
                "import fs from 'node:fs'; fs.writeFileSync(process.argv[3], 'rendered');",
                encoding="utf-8",
            )
            output = workdir / "report.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input", str(source),
                    "--renderer", str(renderer),
                    "--output", str(output),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "rendered")


if __name__ == "__main__":
    unittest.main()
