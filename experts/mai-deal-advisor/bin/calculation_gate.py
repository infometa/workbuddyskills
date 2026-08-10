#!/usr/bin/env python3
"""Validate explicit arithmetic equations in MAI Markdown or text workpapers.

Usage: calculation_gate.py <file.md|file.txt|file.csv> [more files...]
Exit codes: 0=checked/pass, 1=checked/mismatch, 2=not verified.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sys


NUMBER = r"[-+]?\d[\d,]*(?:\.\d+)?"
UNIT = r"(?:万亿元|亿美元|亿港元|亿元|万美元|万港元|万元|亿股|万股|美元|港元|元|股|%|倍)?"
EQUATION = re.compile(
    rf"(?P<left>{NUMBER})\s*(?P<left_unit>{UNIT})\s*"
    rf"(?P<operator>[+\-*/×÷])\s*"
    rf"(?P<right>{NUMBER})\s*(?P<right_unit>{UNIT})\s*=\s*"
    rf"(?P<actual>{NUMBER})\s*(?P<actual_unit>{UNIT})"
    r"(?=$|[,，。；;、）)\]}])"
)
EQUATION_CANDIDATE = re.compile(r"\d.*[+\-*/×÷].*=")
SUPPORTED = {".md", ".txt", ".csv"}

UNIT_INFO = {
    "": ("scalar", Decimal("1")),
    "倍": ("scalar", Decimal("1")),
    "%": ("percent", Decimal("0.01")),
    "元": ("CNY", Decimal("1")),
    "万元": ("CNY", Decimal("10000")),
    "亿元": ("CNY", Decimal("100000000")),
    "万亿元": ("CNY", Decimal("1000000000000")),
    "港元": ("HKD", Decimal("1")),
    "万港元": ("HKD", Decimal("10000")),
    "亿港元": ("HKD", Decimal("100000000")),
    "美元": ("USD", Decimal("1")),
    "万美元": ("USD", Decimal("10000")),
    "亿美元": ("USD", Decimal("100000000")),
    "股": ("shares", Decimal("1")),
    "万股": ("shares", Decimal("10000")),
    "亿股": ("shares", Decimal("100000000")),
}


class UnsupportedEquation(ValueError):
    pass


def decimal(raw: str) -> Decimal:
    return Decimal(raw.replace(",", ""))


def quantity(number: str, unit: str) -> tuple[Decimal, str]:
    dimension, scale = UNIT_INFO[unit]
    return decimal(number) * scale, dimension


def expected_value(
    left: Decimal,
    left_dimension: str,
    operator: str,
    right: Decimal,
    right_dimension: str,
) -> tuple[Decimal, str]:
    if operator in {"+", "-"}:
        if left_dimension != right_dimension:
            raise UnsupportedEquation("加减两侧的币种或单位不一致")
        value = left + right if operator == "+" else left - right
        return value, left_dimension

    if operator in {"*", "×"}:
        if left_dimension == "percent":
            return left * right, right_dimension
        if right_dimension == "percent":
            return left * right, left_dimension
        if left_dimension == "scalar":
            return left * right, right_dimension
        if right_dimension == "scalar":
            return left * right, left_dimension
        raise UnsupportedEquation("两个带量纲数值相乘，当前闸门无法确认结果单位")

    if right == 0:
        raise ZeroDivisionError
    if left_dimension == right_dimension:
        return left / right, "scalar"
    if right_dimension in {"scalar", "percent"}:
        return left / right, left_dimension
    raise UnsupportedEquation("除法两侧的币种或单位不兼容")


def is_close(expected: Decimal, actual: Decimal, dimension: str) -> bool:
    absolute_tolerance = {
        "scalar": Decimal("0.0001"),
        "percent": Decimal("0.0001"),
        "CNY": Decimal("0.01"),
        "HKD": Decimal("0.01"),
        "USD": Decimal("0.01"),
        "shares": Decimal("0.01"),
    }[dimension]
    tolerance = max(absolute_tolerance, abs(expected) * Decimal("0.001"))
    return abs(expected - actual) <= tolerance


def check(path: Path) -> tuple[int, list[str]]:
    if path.suffix.lower() not in SUPPORTED:
        return 2, [f"[UNVERIFIED] 不支持的文件类型: {path.suffix or '[无扩展名]'}"]
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return 2, [f"[UNVERIFIED] 无法读取文件: {exc}"]

    matches = []
    unrecognized_lines = []
    for line_number, line in enumerate(text.splitlines(), 1):
        line_matches = list(EQUATION.finditer(line))
        matches.extend((line_number, match) for match in line_matches)

        residual = list(line)
        for match in line_matches:
            residual[match.start() : match.end()] = " " * (match.end() - match.start())
        if EQUATION_CANDIDATE.search("".join(residual)):
            unrecognized_lines.append(
                f"L{line_number} [UNVERIFIED] 疑似公式未被完整识别: {line.strip()}"
            )

    if not matches:
        if unrecognized_lines:
            return 2, unrecognized_lines
        return 2, ["[UNVERIFIED] 未识别到可复算的显式公式"]

    lines: list[str] = list(unrecognized_lines)
    mismatch = False
    unverified = bool(unrecognized_lines)
    for line_number, match in matches:
        expression = match.group(0)
        try:
            left, left_dimension = quantity(
                match.group("left"), match.group("left_unit")
            )
            right, right_dimension = quantity(
                match.group("right"), match.group("right_unit")
            )
            actual, actual_dimension = quantity(
                match.group("actual"), match.group("actual_unit")
            )
            expected, expected_dimension = expected_value(
                left,
                left_dimension,
                match.group("operator"),
                right,
                right_dimension,
            )
            if expected_dimension != actual_dimension:
                raise UnsupportedEquation(
                    f"结果单位应为 {expected_dimension}，实际为 {actual_dimension}"
                )
        except UnsupportedEquation as exc:
            unverified = True
            lines.append(f"L{line_number} [UNVERIFIED] {expression}；{exc}")
            continue
        except (InvalidOperation, ZeroDivisionError):
            mismatch = True
            lines.append(f"L{line_number} [MISMATCH] 无法复算: {expression}")
            continue
        if is_close(expected, actual, expected_dimension):
            lines.append(f"L{line_number} [PASS] {expression}")
        else:
            mismatch = True
            lines.append(
                f"L{line_number} [MISMATCH] {expression}；复算后的基础单位数值应约为 {expected:.4f}"
            )
    if unverified:
        return 2, lines
    return (1 if mismatch else 0), lines


def main(argv: list[str] | None = None) -> int:
    paths = [Path(item) for item in (argv if argv is not None else sys.argv[1:])]
    if not paths:
        print(__doc__)
        return 2

    statuses = []
    for path in paths:
        status, lines = check(path)
        statuses.append(status)
        print(f"\n### {path.name}")
        for line in lines:
            print(line)
    if 2 in statuses:
        return 2
    if 1 in statuses:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
