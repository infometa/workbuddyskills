#!/usr/bin/env python3
"""Build a bounded non-uniform temperature list for one PROPDB call."""

from __future__ import annotations

import argparse
import json
import math


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    parser.add_argument("--intervals", type=int, required=True)
    parser.add_argument("--critical-temperature", type=float)
    parser.add_argument("--anchor", type=float, action="append", default=[])
    return parser.parse_args()


def build_grid(
    start: float,
    end: float,
    intervals: int,
    critical_temperature: float | None,
    anchors: list[float],
) -> dict[str, object]:
    if not all(math.isfinite(value) for value in (start, end)) or start >= end:
        raise ValueError("require finite start < end")
    if not 2 <= intervals <= 199:
        raise ValueError("intervals must be between 2 and 199 (maximum 200 points)")
    if critical_temperature is not None and not math.isfinite(critical_temperature):
        raise ValueError("critical-temperature must be finite")
    if not all(math.isfinite(value) for value in anchors):
        raise ValueError("anchors must be finite")

    target_count = intervals + 1
    span = end - start
    epsilon = max(abs(start), abs(end), span, 1.0) * 1e-12
    prioritized: list[float] = []

    def add(value: float | None) -> None:
        if value is None or value < start - epsilon or value > end + epsilon:
            return
        bounded = min(max(value, start), end)
        if not any(abs(bounded - existing) <= epsilon for existing in prioritized):
            prioritized.append(bounded)

    add(start)
    add(end)
    add(critical_temperature)
    for value in anchors:
        add(value)

    if critical_temperature is not None and start < critical_temperature < end:
        for fraction in (0.01, 0.025, 0.05, 0.1):
            add(critical_temperature - fraction * span)
            add(critical_temperature + fraction * span)

    selected = prioritized[:target_count]
    baseline = [start + span * index / intervals for index in range(intervals + 1)]
    candidates = [
        value
        for value in baseline
        if not any(abs(value - existing) <= epsilon for existing in selected)
    ]

    while len(selected) < target_count and candidates:
        next_value = max(
            candidates,
            key=lambda value: (
                min(abs(value - existing) for existing in selected),
                -value,
            ),
        )
        selected.append(next_value)
        candidates.remove(next_value)

    values = sorted(round(value, 12) for value in selected)
    used_anchors = [
        round(value, 12)
        for value in prioritized
        if any(abs(value - selected_value) <= epsilon for selected_value in selected)
    ]
    warnings: list[str] = []
    if critical_temperature is not None and not start <= critical_temperature <= end:
        warnings.append("critical temperature is outside the requested range")
    if len(prioritized) > target_count:
        warnings.append("point budget was too small to retain every optional anchor")

    return {
        "tempVary": 3,
        "valueList": values,
        "pointCount": len(values),
        "anchorsUsed": sorted(used_anchors),
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    try:
        result = build_grid(
            args.start,
            args.end,
            args.intervals,
            args.critical_temperature,
            args.anchor,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
