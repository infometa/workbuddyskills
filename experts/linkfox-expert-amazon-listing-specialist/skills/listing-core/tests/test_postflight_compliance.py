#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from postflight_compliance import run_postflight  # noqa: E402


class PostflightComplianceTest(unittest.TestCase):
    def _run(self, search_terms: str, title: str = "Soft Musical Baby Toy") -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            listing = root / "listing.json"
            output = root / "compliance.json"
            listing.write_text(json.dumps({
                "title": title,
                "item_highlights": ["Soft plush toy for floor play"],
                "bullets": ["Encourages interactive play"],
                "description": "A plush toy with music and movement.",
                "search_terms": search_terms,
                "subject_matter": [search_terms],
            }), encoding="utf-8")
            return run_postflight(listing, output, {
                "marketplace": "US",
                "brands": {"owned": ["JoySpark"], "competitor": []},
            })

    def test_known_brand_in_backend_blocks(self) -> None:
        report = self._run("weebles wobble sensory toy")
        gate = report["postflight_gate"]
        self.assertEqual(gate["status"], "blocked")
        self.assertTrue(any(hit["term"].casefold() == "weebles" for hit in gate["blocking_hits"]))

    def test_plain_generic_backend_terms_do_not_block(self) -> None:
        report = self._run("sensory crawling plush floor play")
        self.assertNotEqual(report["postflight_gate"]["status"], "blocked")

    def test_reproduced_generic_lexicon_hits_do_not_block(self) -> None:
        report = self._run("tummy time stimulation discovery")
        gate = report["postflight_gate"]
        self.assertNotEqual(gate["status"], "blocked")
        generic_hits = {
            hit["term"].casefold(): hit["severity"]
            for hit in report.get("hits") or []
            if hit.get("library") == "brand-lexicon"
        }
        self.assertEqual(generic_hits.get("tummy time"), "review")
        self.assertEqual(generic_hits.get("stimulation"), "review")
        self.assertEqual(generic_hits.get("discovery"), "review")

    def test_frontend_global_brand_false_positive_is_review_not_block(self) -> None:
        report = self._run("sensory crawling plush floor play", title="Your Baby Musical Toy")
        brand_front_blockers = [
            hit for hit in report["postflight_gate"]["blocking_hits"]
            if hit.get("library") == "brand-lexicon" and hit.get("field") == "title"
        ]
        self.assertEqual(brand_front_blockers, [])


if __name__ == "__main__":
    unittest.main()
