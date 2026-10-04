#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from evidence_cache import lookup_evidence, store_evidence  # noqa: E402


class EvidenceCacheLibraryTest(unittest.TestCase):
    def test_library_round_trip_supports_pipeline_batching(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            response = root / "response.json"
            response.write_text("{}", encoding="utf-8")
            with patch.dict(os.environ, {"LINKFOX_WORKSPACE": str(root)}):
                stored = store_evidence(
                    "product-detail", {"asin": "B000000001", "site": "US"},
                    str(response),
                )
                found = lookup_evidence(
                    "product-detail", {"asin": "B000000001", "site": "US"},
                )
            self.assertTrue(stored["stored"])
            self.assertTrue(found["hit"])
            self.assertEqual(found["path"], str(response))

    def test_missing_target_is_a_normal_cache_miss(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"LINKFOX_WORKSPACE": tmp}):
                found = lookup_evidence("keyword-matrix", {"asin": "B000000001"})
            self.assertEqual(found, {
                "hit": False, "path": None, "age_hours": None, "status": None,
            })


if __name__ == "__main__":
    unittest.main()
