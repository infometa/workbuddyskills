#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "run_preflight.py"


class AuditPreflightTest(unittest.TestCase):
    def test_packages_normalize_compliance_and_field_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "product-detail.json"
            source.write_text(json.dumps({"products": [{
                "asin": "B012345678",
                "title": "Example Digital Food Scale",
                "aboutItemFivePoint": ["Accurate readings", "Compact design"],
                "productDescription": "A compact scale.",
            }]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT),
                "--source", str(source), "--out-dir", str(workdir / "audit"),
                "--source-kind", "amazon_product_detail",
                "--asin", "B012345678", "--marketplace", "US",
                "--skip-compliance", "restricted", "--skip-compliance", "claims",
                "--skip-compliance", "claims_zh", "--skip-compliance", "brand",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((workdir / "audit" / "audit-preflight.json").read_text("utf-8"))
            self.assertEqual(summary["kind"], "listingAuditPreflight")
            self.assertEqual(summary["field_metrics"]["bullets_count"], 2)
            self.assertEqual(
                summary["field_provenance"]["bullets"]["source_field"],
                "products[0].aboutItemFivePoint",
            )
            self.assertIn("normalize_ms", summary["timings"])
            report = json.loads((workdir / "audit" / "check-report-before.json").read_text("utf-8"))
            self.assertEqual(report["fields"]["search_terms"]["status"], "fail")

    def test_invalid_asin_fails_without_partial_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "product-detail.json"
            source.write_text(json.dumps({"products": [{
                "asin": "B012345678", "title": "Example",
            }]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "audit"), "--asin", "B099999999",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((workdir / "audit" / "audit-preflight.json").exists())


if __name__ == "__main__":
    unittest.main()
