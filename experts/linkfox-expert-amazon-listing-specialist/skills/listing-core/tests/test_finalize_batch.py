from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE / "scripts"))
from finalize_batch import finalize_batch  # noqa: E402


class FinalizeBatchPortableTest(unittest.TestCase):
    def test_merges_completed_rows_to_json_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "row"
            out = run / "03-write"
            out.mkdir(parents=True)
            listing = out / "listing-final.json"
            listing.write_text(json.dumps({"kind": "listingFinalBundle", "listing": {"title": "Title"}}))
            manifest = run / "run-manifest.json"
            manifest.write_text(json.dumps({
                "kind": "listingRunManifest",
                "stages": [{"id": key, "status": "complete"} for key in ("facts", "insight", "write")],
                "final": {"listing_json": str(listing)},
            }))
            items = root / "items.json"
            items.write_text(json.dumps({"items": [
                {"row_id": "1", "status": "complete", "manifest": str(manifest)},
                {"row_id": "2", "status": "failed", "reason": "missing facts"},
            ]}))

            result = finalize_batch(str(items), str(root / "final"))
            self.assertEqual(set(result), {"batch_json"})
            payload = json.loads(Path(result["batch_json"]).read_text())
            self.assertEqual(payload["batch_stats"], {"total": 2, "complete": 1, "failed": 1, "needs_review": 0})
            self.assertEqual(len(payload["products"]), 1)


if __name__ == "__main__":
    unittest.main()
