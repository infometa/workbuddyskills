#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE_ROOT / "scripts"))

from update_detail_preview import normalize_assets, update_preview  # noqa: E402


def _preview(images=None, images_source=None):
    product = {
        "id": "SKU-1",
        "title": "PawGo Dog Water Bottle",
        "bullets": ["b1", "b2", "b3", "b4", "b5"],
        "images": images or [],
    }
    if images_source:
        product["imagesSource"] = images_source
    return {
        "kind": "amazonDetailPreview",
        "schema_version": 1,
        "marketplace": "US",
        "status": "Draft",
        "products": [product],
    }


class TestNormalizeAssets(unittest.TestCase):
    def test_accepts_manifest_shapes_like_merge_listing_assets(self):
        payload = [
            {"assets": [{"src": "https://cdn/a.png", "label": "主图", "type": "MAIN"}]},
            {"id": "t2", "type": "APLUS_BANNER", "images": ["https://cdn/b.png"]},
            "https://cdn/c.png",
        ]
        assets = normalize_assets(payload)
        self.assertEqual(
            [(a["src"], a["slot"]) for a in assets],
            [("https://cdn/a.png", "main"), ("https://cdn/b.png", "aplus"), ("https://cdn/c.png", "main")],
        )
        self.assertEqual(assets[0]["alt"], "主图")

    def test_accepts_assets_object_payload(self):
        assets = normalize_assets({"assets": [{"url": "https://cdn/d.png", "slot": "aplus"}]})
        self.assertEqual(assets, [{"src": "https://cdn/d.png", "alt": "素材图 1", "slot": "aplus"}])


class TestUpdatePreview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def test_generated_images_replace_reference_images(self):
        preview_path = self._write(
            "amazon-detail-preview.json",
            _preview(
                images=[{"src": "https://cdn/competitor.jpg", "alt": "参考图（竞品）"}],
                images_source="reference",
            ),
        )
        manifest_path = self._write(
            "collection-asset-manifest.json",
            {"assets": [
                {"src": "https://cdn/gen-main.png", "label": "主图"},
                {"src": "https://cdn/gen-aplus.png", "label": "A+ 横幅", "type": "APLUS"},
            ]},
        )
        result = update_preview(preview_path, manifest_path)
        self.assertEqual(result["main"], 1)
        self.assertEqual(result["aplus"], 1)
        doc = json.loads(Path(preview_path).read_text(encoding="utf-8"))
        product = doc["products"][0]
        self.assertEqual(product["images"], [{"src": "https://cdn/gen-main.png", "alt": "主图"}])
        self.assertEqual(product["imagesSource"], "generated")
        self.assertEqual(
            product["aplusImages"], [{"src": "https://cdn/gen-aplus.png", "alt": "A+ 横幅"}]
        )
        # 文案字段逐字保持不变
        self.assertEqual(product["title"], "PawGo Dog Water Bottle")
        self.assertIn("generatedAt", doc)

    def test_append_keeps_own_images_but_drops_reference(self):
        own_path = self._write(
            "own-preview.json",
            _preview(images=[{"src": "https://cdn/own.jpg"}], images_source="own"),
        )
        manifest = self._write(
            "manifest-a.json", {"assets": [{"src": "https://cdn/gen.png", "label": "新图"}]}
        )
        update_preview(own_path, manifest, append=True)
        own_doc = json.loads(Path(own_path).read_text(encoding="utf-8"))
        self.assertEqual(
            [img["src"] for img in own_doc["products"][0]["images"]],
            ["https://cdn/own.jpg", "https://cdn/gen.png"],
        )

        ref_path = self._write(
            "ref-preview.json",
            _preview(images=[{"src": "https://cdn/competitor.jpg"}], images_source="reference"),
        )
        manifest_b = self._write(
            "manifest-b.json", {"assets": [{"src": "https://cdn/gen2.png", "label": "新图"}]}
        )
        update_preview(ref_path, manifest_b, append=True)
        ref_doc = json.loads(Path(ref_path).read_text(encoding="utf-8"))
        self.assertEqual(
            [img["src"] for img in ref_doc["products"][0]["images"]], ["https://cdn/gen2.png"]
        )

    def test_refuses_non_public_asset_urls(self):
        preview_path = self._write("preview.json", _preview())
        manifest_path = self._write(
            "manifest.json", {"assets": [{"src": "/root/.linkfox/media/local.png"}]}
        )
        with self.assertRaisesRegex(ValueError, "non-public"):
            update_preview(preview_path, manifest_path)

    def test_refuses_empty_manifest_and_bad_index(self):
        preview_path = self._write("preview2.json", _preview())
        empty_manifest = self._write("empty.json", {"assets": []})
        with self.assertRaisesRegex(ValueError, "no usable assets"):
            update_preview(preview_path, empty_manifest)
        manifest_path = self._write(
            "manifest2.json", {"assets": [{"src": "https://cdn/x.png"}]}
        )
        with self.assertRaisesRegex(ValueError, "out of range"):
            update_preview(preview_path, manifest_path, product_index=3)


if __name__ == "__main__":
    unittest.main()
