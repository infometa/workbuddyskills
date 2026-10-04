#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "project_product_detail.py"


def product(asin: str, *, bullets_key: str = "aboutItemFivePoint", bullets=None):
    return {
        "asin": asin, "title": f"Product {asin}", "brand": "Brand",
        bullets_key: bullets if bullets is not None else ["First fact", "Second fact"],
        "itemSpecifications": {"Weight": "10 oz"},
        "authorsReviews": [{"title": "Good", "text": "Works", "rating": 5, "author": "private"}],
        "pageFileUrl": "large-raw-page-that-must-not-be-projected",
    }


class ProjectProductDetailTest(unittest.TestCase):
    def test_projects_known_bullet_fields_and_separates_competitors(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "raw.json"
            source.write_text(json.dumps({"products": [
                product("B000000001", bullets_key="aboutItemFivePoint"),
                product("B000000002", bullets_key="bulletPoints"),
                product("B000000003", bullets_key="aboutItem"),
            ]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "facts"), "--target-asin", "B000000001",
                "--competitor-asin", "B000000002", "--competitor-asin", "B000000003",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            bundle = json.loads((workdir / "facts" / "product-detail.json").read_text("utf-8"))
            self.assertEqual(bundle["target"]["aboutItemFivePoint"], ["First fact", "Second fact"])
            self.assertEqual(bundle["competitors"][0]["field_provenance"]["bullets"], "bulletPoints")
            self.assertNotIn("pageFileUrl", bundle["target"])
            self.assertNotIn("author", bundle["target"]["authorsReviews"][0])
            facts = (workdir / "facts" / "product-facts.md").read_text("utf-8")
            self.assertIn("竞品字段仅供结构", facts)

    def test_missing_target_fails_without_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "raw.json"
            source.write_text(json.dumps({"products": [product("B000000001")]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "facts"), "--target-asin", "B000000099",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((workdir / "facts" / "product-detail.json").exists())

    def test_create_projects_own_facts_and_reference_without_claim_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "raw.json"
            source.write_text(json.dumps({"products": [
                product("B000000002", bullets=["Competitor padded seat", "Competitor warranty"]),
            ]}), encoding="utf-8")
            own_facts = workdir / "own-facts.json"
            own_facts.write_text(json.dumps({
                "confirmed": {"brand": "Velmoriq", "shape": "round"},
                "observed": ["taupe upholstery"],
                "unknown": ["seat filling", "weight capacity", "care instructions"],
            }), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "facts"), "--own-facts", str(own_facts),
                "--reference-asin", "B000000002",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            bundle = json.loads((workdir / "facts" / "product-detail.json").read_text("utf-8"))
            self.assertEqual(bundle["target"]["factSource"], "provided_product_facts")
            self.assertEqual(bundle["target"]["confirmedFacts"]["confirmed"]["brand"], "Velmoriq")
            self.assertEqual(bundle["competitors"][0]["asin"], "B000000002")
            facts = (workdir / "facts" / "product-facts.md").read_text("utf-8")
            self.assertIn("不可据此推断内部填充", facts)
            self.assertIn("竞品字段仅供结构", facts)

    def test_create_requires_structured_own_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "raw.json"
            source.write_text(json.dumps({"products": [product("B000000002")]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "facts"), "--reference-asin", "B000000002",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires --own-facts", result.stderr)

    def test_invalid_competitor_is_projected_as_weak_without_fallback_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "raw.json"
            source.write_text(json.dumps({"products": [
                product("B000000001"), product("B000000002", bullets=[]),
            ]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "facts"), "--target-asin", "B000000001",
                "--competitor-asin", "B000000002",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            bundle = json.loads((workdir / "facts" / "product-detail.json").read_text("utf-8"))
            self.assertEqual(bundle["validation"]["valid_competitors"], 0)
            self.assertEqual(bundle["competitors"][0]["evidence_strength"]["bullets"], "unavailable")

    def test_missing_competitor_is_retained_as_weak_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "raw.json"
            source.write_text(
                json.dumps({"products": [product("B000000001")]}), encoding="utf-8"
            )
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "facts"), "--target-asin", "B000000001",
                "--competitor-asin", "B000000099",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            bundle = json.loads((workdir / "facts" / "product-detail.json").read_text("utf-8"))
            self.assertEqual(bundle["validation"]["valid_competitors"], 0)
            self.assertTrue(bundle["competitors"][0]["missing_from_response"])
            self.assertEqual(bundle["competitors"][0]["asin"], "B000000099")

    def test_comma_joined_competitors_are_split_for_legacy_callers(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            source = workdir / "raw.json"
            source.write_text(json.dumps({"products": [
                product("B000000001"), product("B000000002"), product("B000000003"),
            ]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--source", str(source),
                "--out-dir", str(workdir / "facts"), "--target-asin", "B000000001",
                "--competitor-asin", "B000000002,B000000003",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            bundle = json.loads((workdir / "facts" / "product-detail.json").read_text("utf-8"))
            self.assertEqual(
                [item["asin"] for item in bundle["competitors"]],
                ["B000000002", "B000000003"],
            )


if __name__ == "__main__":
    unittest.main()
