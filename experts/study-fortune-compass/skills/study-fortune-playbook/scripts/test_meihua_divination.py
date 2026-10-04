#!/usr/bin/env python3

import importlib.util
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("meihua_divination.py")
SPEC = importlib.util.spec_from_file_location("meihua_divination", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MeiHuaDivinationTests(unittest.TestCase):
    def test_known_number_seven_you_hour(self):
        moment = datetime(2026, 7, 18, 18, 56, tzinfo=timezone(timedelta(hours=8)))
        result = MODULE.calculate(7, moment)
        self.assertEqual(result["input"]["earthly_branch_hour"], "酉")
        self.assertEqual(result["input"]["utc_offset"], "+08:00")
        self.assertEqual(result["schema_version"], "1.1")
        self.assertEqual(result["primary_hexagram"]["number"], 41)
        self.assertEqual(result["primary_hexagram"]["name"], "损")
        self.assertEqual(result["moving_line"]["position"], 5)
        self.assertEqual(result["mutual_hexagram"]["name"], "复")
        self.assertEqual(result["changed_hexagram"]["name"], "中孚")

    def test_zero_remainders(self):
        moment = datetime(2026, 7, 18, 13, 0, tzinfo=timezone(timedelta(hours=8)))
        result = MODULE.calculate(8, moment)
        self.assertIn("坤", result["calculation"]["upper_trigram"])
        self.assertIn("坤", result["calculation"]["lower_trigram"])
        self.assertEqual(result["moving_line"]["position"], 4)

    def test_midnight_is_zi_hour(self):
        moment = datetime(2026, 7, 18, 23, 30, tzinfo=timezone(timedelta(hours=8)))
        result = MODULE.calculate(8, moment)
        self.assertEqual(result["input"]["earthly_branch_hour"], "子")
        self.assertEqual(result["input"]["hour_number"], 1)

    def test_same_input_same_hour_is_deterministic(self):
        first = MODULE.calculate(7, datetime(2026, 7, 18, 17, 1, tzinfo=timezone.utc))
        second = MODULE.calculate(7, datetime(2026, 7, 18, 18, 59, tzinfo=timezone.utc))
        self.assertEqual(first["primary_hexagram"], second["primary_hexagram"])
        self.assertEqual(first["moving_line"], second["moving_line"])
        self.assertEqual(first["changed_hexagram"], second["changed_hexagram"])

    def test_all_numbers_and_branches_resolve(self):
        for number in range(1, 65):
            for hour in range(24):
                result = MODULE.calculate(number, datetime(2026, 7, 18, hour, 0, tzinfo=timezone.utc))
                self.assertIn(result["primary_hexagram"]["number"], range(1, 65))
                self.assertIn(result["mutual_hexagram"]["number"], range(1, 65))
                self.assertIn(result["changed_hexagram"]["number"], range(1, 65))
                self.assertIn(result["moving_line"]["position"], range(1, 7))

    def test_non_positive_number_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.calculate(0, datetime.now(timezone.utc))

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.calculate(7, datetime(2026, 7, 18, 18, 56))


if __name__ == "__main__":
    unittest.main()
