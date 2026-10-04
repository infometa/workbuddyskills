#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_audit_report import normalize_report  # noqa: E402


class NormalizeAuditReportTest(unittest.TestCase):
    def _fixture(self, root: Path) -> dict:
        for name in ("listing.json", "compliance.json", "score.json"):
            (root / name).write_text("{}", encoding="utf-8")
        return {
            "kind": "listingAuditReport",
            "schema_version": 2,
            "target": {"asin": "B0FNMB69KL", "marketplace": "US"},
            "scorePanel": {},
            "auditHandoff": {
                "mode": "rewrite",
                "target_asin": "B0FNMB69KL",
                "marketplace": "US",
                "evidence_paths": {
                    "normalized_listing": "listing.json",
                    "compliance_report": "compliance.json",
                    "score_result": "score.json",
                },
                "field_actions": [{
                    "field": "search_terms",
                    "priority": "high",
                    "reason": "后台字段不可见",
                    "constraints": ["<=250 bytes"],
                }],
            },
        }

    def test_legacy_semantic_handoff_becomes_canonical_and_safe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = normalize_report(self._fixture(root), root)
            handoff = result["auditHandoff"]
            self.assertTrue(result["rewrite_ready"])
            self.assertEqual(handoff["kind"], "listingAuditHandoff")
            self.assertEqual(handoff["schema_version"], 1)
            self.assertEqual(handoff["target"]["asin"], "B0FNMB69KL")
            self.assertTrue(Path(handoff["source_listing_path"]).is_absolute())
            self.assertEqual(handoff["evidence_paths"]["compliance"], str((root / "compliance.json").resolve()))
            action = handoff["field_actions"][0]
            self.assertEqual(action["problem"], "后台字段不可见")
            self.assertTrue(any("品牌名" in value for value in action["constraints"]))
            self.assertTrue(any("重新扫描" in value for value in action["constraints"]))

    def test_missing_evidence_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self._fixture(root)
            (root / "listing.json").unlink()
            with self.assertRaisesRegex(ValueError, "does not exist"):
                normalize_report(payload, root)

    def test_target_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self._fixture(root)
            payload["auditHandoff"]["target_asin"] = "B000000000"
            with self.assertRaisesRegex(ValueError, "does not match"):
                normalize_report(payload, root)


if __name__ == "__main__":
    unittest.main()
