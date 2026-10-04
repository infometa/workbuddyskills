from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE / "scripts"))

from build_spec import assemble_spec  # noqa: E402
from finalize_listing import finalize  # noqa: E402
from run_manifest import init_manifest  # noqa: E402
from validate_fields import check_fields  # noqa: E402


class FinalizePortableTest(unittest.TestCase):
    def test_writes_only_portable_listing_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = Path(init_manifest(str(root / "run"), "create", {}))
            spec = assemble_spec("create", ["PawGo"], [], {"core": ["dog bottle"]}, [])
            draft = {
                "title": "PawGo Dog Water Bottle for Travel",
                "item_highlights": ["Portable hydration for daily walks"],
                "bullets": [f"BENEFIT {i}: useful product detail" for i in range(1, 6)],
                "description": "A compact bottle for walks and travel.",
                "search_terms": "portable pet hydration outdoor",
            }
            report = check_fields(draft, spec, facts_text="")
            paths = {}
            for name, value in (("draft.json", draft), ("spec.json", spec), ("check.json", report)):
                path = root / name
                path.write_text(json.dumps(value), encoding="utf-8")
                paths[name] = path

            result = finalize(
                str(manifest), str(paths["draft.json"]), str(paths["spec.json"]),
                str(paths["check.json"]), seller_sku="SKU-1",
            )

            self.assertEqual(
                set(result),
                {"listing_json", "listing_md", "check_report", "ai_readiness", "detail_preview", "manifest"},
            )
            self.assertNotIn("xlsx", result)
            self.assertNotIn("html", result)
            bundle = json.loads(Path(result["listing_json"]).read_text(encoding="utf-8"))
            self.assertEqual(bundle["kind"], "listingFinalBundle")
            self.assertNotIn("productLibraryContext", bundle)
            self.assertNotIn("productId", bundle)
            self.assertEqual(bundle["listing"]["sellerSku"], "SKU-1")

    def test_rejects_failed_quality_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = Path(init_manifest(str(root / "run"), "create", {}))
            spec = assemble_spec("create", [], [], {"core": ["bottle"]}, [])
            draft = {
                "title": "x" * 90, "item_highlights": ["Compact"],
                "bullets": [f"Benefit {i}" for i in range(5)],
                "description": "Description", "search_terms": "portable bottle",
            }
            report = check_fields(draft, spec)
            files = []
            for name, value in (("draft.json", draft), ("spec.json", spec), ("check.json", report)):
                path = root / name
                path.write_text(json.dumps(value), encoding="utf-8")
                files.append(str(path))
            with self.assertRaisesRegex(ValueError, "quality gate failed"):
                finalize(str(manifest), *files)


if __name__ == "__main__":
    unittest.main()
