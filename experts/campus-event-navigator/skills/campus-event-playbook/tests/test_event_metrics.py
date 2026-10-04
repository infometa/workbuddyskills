from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "event_metrics.py"
SPEC = importlib.util.spec_from_file_location("event_metrics", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load event_metrics.py")
event_metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(event_metrics)


class EventMetricsTests(unittest.TestCase):
    def test_metrics_without_readiness_are_not_evaluated(self) -> None:
        result = event_metrics.calculate(
            {"registration_count": 120, "attendance_count": 96}
        )
        self.assertEqual(result["attendance_rate_percent"], 80.0)
        self.assertEqual(result["readiness"]["readiness_status"], "not_evaluated")
        self.assertEqual(result["readiness"]["items"], {})
        self.assertEqual(result["readiness"]["critical_missing"], [])

    def test_null_readiness_is_not_evaluated(self) -> None:
        result = event_metrics.calculate({"readiness": None})
        self.assertEqual(result["readiness"]["readiness_status"], "not_evaluated")

    def test_empty_explicit_readiness_is_blocked(self) -> None:
        result = event_metrics.calculate({"readiness": {}})
        self.assertEqual(result["readiness"]["readiness_status"], "blocked")
        self.assertEqual(len(result["readiness"]["critical_missing"]), 4)

    def test_complete_readiness_can_be_ready(self) -> None:
        readiness = {key: "ready" for key in event_metrics.READINESS_KEYS}
        result = event_metrics.calculate({"readiness": readiness})
        self.assertEqual(result["readiness"]["readiness_status"], "ready")

    def test_needs_work_requires_attention(self) -> None:
        readiness = {key: "ready" for key in event_metrics.READINESS_KEYS}
        readiness["equipment_rehearsal"] = "needs_work"
        result = event_metrics.calculate({"readiness": readiness})
        self.assertEqual(result["readiness"]["readiness_status"], "needs_attention")

    def test_noncritical_missing_is_not_ready(self) -> None:
        readiness = {key: "ready" for key in event_metrics.READINESS_KEYS}
        readiness["data_collection"] = "missing"
        result = event_metrics.calculate({"readiness": readiness})
        self.assertEqual(result["readiness"]["readiness_status"], "not_ready")

    def test_zero_denominators_return_none(self) -> None:
        result = event_metrics.calculate(
            {
                "registration_count": 0,
                "attendance_count": 0,
                "tasks_total": 0,
                "tasks_done": 0,
                "budget_planned": 0,
                "budget_actual": 0,
            }
        )
        self.assertIsNone(result["attendance_rate_percent"])
        self.assertIsNone(result["task_completion_rate_percent"])
        self.assertIsNone(result["actual_budget_variance_percent"])

    def test_inconsistent_counts_and_budget_create_warnings(self) -> None:
        result = event_metrics.calculate(
            {
                "registration_count": 1,
                "attendance_count": 2,
                "tasks_total": 1,
                "tasks_done": 2,
                "budget_planned": 100,
                "budget_committed": 120,
            }
        )
        self.assertEqual(len(result["warnings"]), 3)

    def test_unknown_readiness_keys_are_reported(self) -> None:
        readiness = {key: "ready" for key in event_metrics.READINESS_KEYS}
        readiness["extra"] = "ready"
        result = event_metrics.calculate({"readiness": readiness})
        self.assertEqual(result["readiness"]["unknown_keys_ignored"], ["extra"])

    def test_invalid_readiness_status_is_rejected(self) -> None:
        with self.assertRaises(event_metrics.InputError):
            event_metrics.calculate({"readiness": {"venue_approval": "unknown"}})

    def test_boolean_count_is_rejected(self) -> None:
        with self.assertRaises(event_metrics.InputError):
            event_metrics.calculate({"registration_count": True})


if __name__ == "__main__":
    unittest.main()
