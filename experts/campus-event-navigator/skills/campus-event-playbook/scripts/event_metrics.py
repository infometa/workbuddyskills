#!/usr/bin/env python3
"""Calculate deterministic metrics for a campus event workbench.

The script does not approve an event or determine that an event is safe. It only
summarizes the JSON values supplied by the caller.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

READINESS_KEYS = (
    "venue_approval",
    "run_of_show",
    "key_roles",
    "budget_materials",
    "promotion_registration",
    "equipment_rehearsal",
    "safety_contingency",
    "data_collection",
)
CRITICAL_READINESS_KEYS = {
    "venue_approval",
    "run_of_show",
    "key_roles",
    "safety_contingency",
}
READINESS_STATUSES = {"ready", "needs_work", "missing"}
COUNT_KEYS = {
    "registration_count",
    "attendance_count",
    "tasks_total",
    "tasks_done",
}


class InputError(ValueError):
    """Raised when the input cannot be interpreted safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate attendance, task, budget, and readiness metrics."
    )
    parser.add_argument(
        "--input",
        default="-",
        help="Input JSON file. Use '-' or omit the option to read stdin.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output.",
    )
    return parser.parse_args()


def load_payload(input_path: str) -> dict[str, Any]:
    try:
        if input_path == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(input_path).read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read input: {exc}") from exc

    if not raw.strip():
        raise InputError("input JSON is empty")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON: {exc.msg} at line {exc.lineno}") from exc

    if not isinstance(payload, dict):
        raise InputError("input JSON must be an object")
    return payload


def optional_number(payload: dict[str, Any], key: str) -> float | None:
    if key not in payload or payload[key] is None or payload[key] == "":
        return None

    value = payload[key]
    if isinstance(value, bool):
        raise InputError(f"{key} must be a non-negative number")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{key} must be a non-negative number") from exc

    if not math.isfinite(number):
        raise InputError(f"{key} must be a finite number")
    if number < 0:
        raise InputError(f"{key} must be non-negative")
    if key in COUNT_KEYS and not number.is_integer():
        raise InputError(f"{key} must be a whole number")
    return number


def percentage(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator * 100, 2)


def budget_variance(value: float | None, planned: float | None) -> float | None:
    if value is None or planned is None or planned == 0:
        return None
    return round((value - planned) / planned * 100, 2)


def summarize_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    if "readiness" not in payload or payload["readiness"] is None:
        return {
            "items": {},
            "counts": {status: 0 for status in sorted(READINESS_STATUSES)},
            "critical_missing": [],
            "unknown_keys_ignored": [],
            "readiness_status": "not_evaluated",
            "disclaimer": (
                "Readiness was not evaluated because no readiness checklist was "
                "supplied. This is not a school approval, safety certification, or "
                "go/no-go decision."
            ),
        }

    readiness = payload["readiness"]
    if not isinstance(readiness, dict):
        raise InputError("readiness must be an object")

    normalized: dict[str, str] = {}
    for key in READINESS_KEYS:
        status = readiness.get(key, "missing")
        if not isinstance(status, str):
            raise InputError(f"readiness.{key} must be a string")
        status = status.strip().lower()
        if status not in READINESS_STATUSES:
            allowed = ", ".join(sorted(READINESS_STATUSES))
            raise InputError(f"readiness.{key} must be one of: {allowed}")
        normalized[key] = status

    unknown_keys = sorted(set(readiness) - set(READINESS_KEYS))
    counts = {
        status: sum(1 for value in normalized.values() if value == status)
        for status in sorted(READINESS_STATUSES)
    }
    critical_missing = sorted(
        key for key in CRITICAL_READINESS_KEYS if normalized[key] == "missing"
    )

    if critical_missing:
        overall = "blocked"
    elif counts["missing"]:
        overall = "not_ready"
    elif counts["needs_work"]:
        overall = "needs_attention"
    else:
        overall = "ready"

    return {
        "items": normalized,
        "counts": counts,
        "critical_missing": critical_missing,
        "unknown_keys_ignored": unknown_keys,
        "readiness_status": overall,
        "disclaimer": (
            "Readiness is calculated only from supplied checklist values and is not "
            "a school approval, safety certification, or go/no-go decision."
        ),
    }


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    registration = optional_number(payload, "registration_count")
    attendance = optional_number(payload, "attendance_count")
    tasks_total = optional_number(payload, "tasks_total")
    tasks_done = optional_number(payload, "tasks_done")
    budget_planned = optional_number(payload, "budget_planned")
    budget_committed = optional_number(payload, "budget_committed")
    budget_actual = optional_number(payload, "budget_actual")
    budget_forecast = optional_number(payload, "budget_forecast")

    warnings: list[str] = []
    if registration is not None and attendance is not None and attendance > registration:
        warnings.append(
            "attendance_count exceeds registration_count; confirm whether walk-in attendees are included"
        )
    if tasks_total is not None and tasks_done is not None and tasks_done > tasks_total:
        warnings.append("tasks_done exceeds tasks_total; verify the task counts")
    if (
        budget_planned is not None
        and budget_committed is not None
        and budget_committed > budget_planned
    ):
        warnings.append("budget_committed exceeds budget_planned")

    provided = {
        key: payload.get(key)
        for key in (
            "registration_count",
            "attendance_count",
            "tasks_total",
            "tasks_done",
            "budget_planned",
            "budget_committed",
            "budget_actual",
            "budget_forecast",
        )
        if key in payload
    }

    return {
        "input_values": provided,
        "attendance_rate_percent": percentage(attendance, registration),
        "task_completion_rate_percent": percentage(tasks_done, tasks_total),
        "actual_budget_variance_percent": budget_variance(
            budget_actual, budget_planned
        ),
        "forecast_budget_variance_percent": budget_variance(
            budget_forecast, budget_planned
        ),
        "remaining_budget_vs_actual": (
            round(budget_planned - budget_actual, 2)
            if budget_planned is not None and budget_actual is not None
            else None
        ),
        "remaining_budget_vs_committed": (
            round(budget_planned - budget_committed, 2)
            if budget_planned is not None and budget_committed is not None
            else None
        ),
        "readiness": summarize_readiness(payload),
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    try:
        result = calculate(load_payload(args.input))
    except InputError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps({"status": "ok", "result": result}, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
