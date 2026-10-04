from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from save_title_output import (  # noqa: E402
    WORKBENCH_SCHEMA,
    _validate,
    build_workbench_payload,
)


class TitleWorkbenchPayloadTest(unittest.TestCase):
    def _validated(self, payload: dict) -> tuple[dict, list[str], list[str]]:
        item = copy.deepcopy(payload)
        errors, warnings = _validate(item)
        return item, errors, warnings

    def test_generate_uses_fixed_workbench_schema_without_source_title(self) -> None:
        item = self._validated(
            {
                "task_mode": "generate",
                "row_index": 1,
                "product": {
                    "sku": "SKU-1",
                    "product_name": "Test Bottle",
                    "marketplace": "US",
                },
                "title": "ExampleBrand Insulated Water Bottle 24 oz",
                "item_highlights": "Stainless steel bottle for gym and travel.",
                "meta": {"amazon_title_policy": "compact_75"},
            }
        )

        result = build_workbench_payload([item])

        self.assertEqual(result["schema"], WORKBENCH_SCHEMA)
        self.assertEqual(result["type"], "tableListWorkbenches")
        self.assertEqual(result["view"]["single"], "card")
        self.assertEqual(result["summary"], {"total": 1, "ok": 1, "review": 0, "failed": 0})
        self.assertIsNone(result["rows"][0]["source"]["title"])
        self.assertEqual(result["rows"][0]["result"]["title"], result["title"])
        self.assertEqual(result["rows"][0]["sku"], "SKU-1")
        self.assertEqual(result["policy"]["title_max"], 75)
        self.assertEqual(result["rows"][0]["policy"], result["policy"])

    def test_legacy_split_mode_maps_to_migrate(self) -> None:
        item = self._validated(
            {
                "source_mode": "split_legacy",
                "row_index": 2,
                "legacy_title": "ExampleBrand Insulated Water Bottle for Gym and Travel",
                "title": "ExampleBrand Insulated Water Bottle",
                "item_highlights": "Designed for gym and travel.",
                "migration_map": [
                    {
                        "segment": "gym and travel",
                        "from": "legacy_title",
                        "to": "highlights",
                        "reason": "scene",
                    }
                ],
            }
        )

        result = build_workbench_payload([item])
        row = result["rows"][0]

        self.assertEqual(result["task_mode"], "migrate")
        self.assertEqual(row["task_mode"], "migrate")
        self.assertEqual(row["source"]["title"], row["legacy_title"])
        self.assertEqual(row["strategy"]["migration_map"], row["migration_map"])

    def test_mixed_batch_has_one_envelope_and_multiple_rows(self) -> None:
        generate = self._validated(
            {
                "task_mode": "generate",
                "row_index": 2,
                "title": "ExampleBrand Travel Bottle",
                "item_highlights": "Compact bottle for daily use.",
            }
        )
        rewrite = self._validated(
            {
                "task_mode": "rewrite",
                "row_index": 3,
                "legacy_title": "Old ExampleBrand Travel Bottle Title",
                "title": "ExampleBrand Travel Bottle",
                "item_highlights": "Compact bottle for daily use.",
            }
        )

        result = build_workbench_payload([generate, rewrite], source_file="/tmp/input.json")

        self.assertEqual(result["task_mode"], "mixed")
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(len(result["rows"]), 2)
        self.assertIsNone(result["title"])
        self.assertEqual(result["view"]["batch"], "table")
        self.assertEqual(result["source_file"], "/tmp/input.json")

    def test_rewrite_requires_source_title(self) -> None:
        payload = {
            "task_mode": "rewrite",
            "title": "ExampleBrand Travel Bottle",
            "item_highlights": "Compact bottle for daily use.",
        }

        errors, _ = _validate(payload)

        self.assertIn("rewrite 模式缺少 legacy_title", errors)

    def test_warning_is_rendered_as_review_status(self) -> None:
        item = self._validated(
            {
                "task_mode": "generate",
                "title": "ExampleBrand Travel Bottle",
                "item_highlights": "",
            }
        )

        result = build_workbench_payload([item])

        self.assertEqual(result["summary"]["review"], 1)
        self.assertEqual(result["rows"][0]["status"], "review")
        self.assertTrue(result["rows"][0]["validation_notes"])

    def test_classic_mode_generates_one_title_with_legacy_default_limit(self) -> None:
        item = self._validated(
            {
                "task_mode": "classic",
                "platform": "temu",
                "title": "A" * 100,
                "item_highlights": "",
            }
        )

        result = build_workbench_payload([item])
        row = result["rows"][0]

        self.assertEqual(item[1], [])
        self.assertEqual(result["task_mode"], "classic")
        self.assertEqual(result["workbench_title"], "多平台 Title 工作台")
        self.assertEqual(result["policy"]["policy_id"], "classic_title_only")
        self.assertEqual(result["policy"]["title_max"], 200)
        self.assertEqual(result["policy"]["item_highlights_max"], 0)
        self.assertEqual(result["policy"]["marketplace"], "temu")
        self.assertEqual(row["item_highlights"], "")
        self.assertEqual(row["source_mode"], "generate")

    def test_classic_mode_respects_configured_title_limit(self) -> None:
        payload = {
            "task_mode": "classic",
            "policy": {"title_max": 10},
            "title": "12345678901",
            "item_highlights": "",
        }

        errors, _ = _validate(payload)

        self.assertIn("title 超长：11 > 10", errors)

    def test_classic_mode_rejects_item_highlights(self) -> None:
        payload = {
            "task_mode": "classic",
            "title": "ExampleBrand Travel Bottle",
            "item_highlights": "Should not be generated",
        }

        errors, _ = _validate(payload)

        self.assertIn("classic 模式 item_highlights 必须为空", errors)

    def test_temu_platform_auto_routes_to_classic_without_task_mode(self) -> None:
        item = self._validated(
            {
                "platform": "temu",
                "legacy_title": "Old Lenovo Tablet Title",
                "title": "A" * 100,
                "item_highlights": "",
            }
        )

        result = build_workbench_payload([item])

        self.assertEqual(item[1], [])
        self.assertEqual(result["task_mode"], "classic")
        self.assertEqual(result["policy"]["title_max"], 200)

    def test_title_only_signal_auto_routes_to_classic(self) -> None:
        item = self._validated(
            {
                "title_only": True,
                "title": "A" * 100,
                "item_highlights": "",
            }
        )

        result = build_workbench_payload([item])

        self.assertEqual(item[1], [])
        self.assertEqual(result["task_mode"], "classic")

    def test_explicit_split_legacy_still_has_priority(self) -> None:
        item = self._validated(
            {
                "source_mode": "split_legacy",
                "platform": "temu",
                "legacy_title": "Old Tablet Title for Students",
                "title": "Tablet Title",
                "item_highlights": "For students.",
                "migration_map": [{"segment": "for students", "to": "highlights"}],
            }
        )

        result = build_workbench_payload([item])

        self.assertEqual(result["task_mode"], "migrate")

if __name__ == "__main__":
    unittest.main()
