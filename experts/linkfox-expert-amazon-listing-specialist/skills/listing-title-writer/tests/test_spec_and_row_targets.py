"""用户规格（--spec）与批量写回行号的回归测试。

这两块能力原先只存在于 agents/linkfox-listing-agent 下的分叉副本，
统一为一份实现后必须继续成立，否则 listing-core 的 `--spec` 契约会断。
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from listing_spec import extract_spec_arg, load_spec  # noqa: E402
from save_title_batch_output import find_target_collisions, resolve_target_rows  # noqa: E402
from save_title_output import (  # noqa: E402
    _validate,
    apply_spec_to_policy,
    build_workbench_payload,
)

BASE = {
    "task_mode": "generate",
    "row_index": 1,
    "product": {"sku": "SKU-1", "marketplace": "US"},
    "title": "ExampleBrand Insulated Water Bottle 24 oz Stainless Steel for Gym and Office Use",
    "item_highlights": "Keeps drinks cold 24 hours. Ideal for gym, office and outdoor trips.",
}


def _spec_file(spec: dict) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(spec, handle)
    handle.close()
    return handle.name


class UserSpecTest(unittest.TestCase):
    def test_default_limits_still_reject_over_75(self) -> None:
        errors, _ = _validate(copy.deepcopy(BASE))
        self.assertTrue(any("title 超长" in e for e in errors))
        self.assertTrue(any("[默认规格]" in e or "默认" in e for e in errors))

    def test_user_spec_can_widen_title_within_platform_limit(self) -> None:
        spec = load_spec(_spec_file({"title": {"max": 190}}))
        errors, _ = _validate(copy.deepcopy(BASE), spec)
        self.assertEqual(errors, [])

    def test_platform_hard_limit_cannot_be_widened(self) -> None:
        spec = load_spec(_spec_file({"title": {"max": 190}}))
        payload = copy.deepcopy(BASE)
        payload["title"] = "A" * 201
        errors, _ = _validate(payload, spec)
        self.assertTrue(any("平台硬限制" in e for e in errors))

    def test_disabled_item_highlights_must_be_empty(self) -> None:
        spec = load_spec(_spec_file({"title": {"max": 190}, "item_highlights": {"enabled": False}}))
        errors, _ = _validate(copy.deepcopy(BASE), spec)
        self.assertTrue(any("禁用 item_highlights" in e for e in errors))

    def test_spec_limits_reach_policy_so_char_meters_match(self) -> None:
        spec = load_spec(_spec_file({"title": {"max": 190}, "item_highlights": {"max": 200}}))
        payload = copy.deepcopy(BASE)
        apply_spec_to_policy(payload, spec)
        errors, warnings = _validate(payload, spec)
        result = build_workbench_payload([(payload, errors, warnings)])

        self.assertEqual(result["policy"]["title_max"], 190)
        self.assertEqual(result["policy"]["item_highlights_max"], 200)
        self.assertEqual(result["policy"]["policy_id"], "user_spec")

    def test_user_spec_overrides_an_existing_default_policy(self) -> None:
        spec = load_spec(_spec_file({"title": {"max": 190}, "item_highlights": {"max": 200}}))
        payload = copy.deepcopy(BASE)
        payload["title"] = "A" * 100
        payload["policy"] = {"policy_id": "compact_75", "title_max": 75, "item_highlights_max": 125}

        apply_spec_to_policy(payload, spec)
        errors, _ = _validate(payload, spec)

        self.assertEqual(errors, [])
        self.assertEqual(payload["policy"]["title_max"], 190)
        self.assertEqual(payload["policy"]["item_highlights_max"], 200)
        self.assertEqual(payload["policy"]["policy_id"], "user_spec")

    def test_extract_spec_arg_strips_flag_and_keeps_others(self) -> None:
        path = _spec_file({"title": {"max": 120}})
        argv, spec = extract_spec_arg(["payload.json", "--spec", path, "--xlsx"])
        self.assertEqual(argv, ["payload.json", "--xlsx"])
        self.assertIsNotNone(spec)


class RowTargetTest(unittest.TestCase):
    def test_one_based_batch_maps_to_data_rows(self) -> None:
        rows = [{"row_index": 1}, {"row_index": 2}, {"row_index": 3}]
        self.assertEqual(resolve_target_rows(rows), [2, 3, 4])

    def test_worksheet_convention_is_preserved(self) -> None:
        rows = [{"row_index": 2}, {"row_index": 3}, {"row_index": 7}]
        self.assertEqual(resolve_target_rows(rows), [2, 3, 7])

    def test_missing_indices_fall_back_to_position(self) -> None:
        rows = [{}, {}, {}]
        self.assertEqual(resolve_target_rows(rows), [2, 3, 4])

    def test_explicit_source_row_wins(self) -> None:
        rows = [{"row_index": 1, "source_row": 9}, {"row_index": 2}]
        self.assertEqual(resolve_target_rows(rows), [9, 3])

    def test_collision_is_detectable(self) -> None:
        rows = [{"row_index": 2}, {"source_row": 2}]
        targets = resolve_target_rows(rows)
        self.assertEqual(targets, [2, 2])
        self.assertEqual(find_target_collisions(targets), {2: [1, 2]})


if __name__ == "__main__":
    unittest.main()
