#!/usr/bin/env python3
"""Deterministic Mei Hua Yi Shu one-number divination.

Method used:
- Reported number -> upper trigram.
- Current earthly-branch hour number -> lower trigram.
- Reported number + hour number -> moving line.
- Remainder 0 is treated as 8 for trigrams and 6 for moving lines.

The script performs calculation and canonical text lookup only. It does not
claim predictive accuracy and does not generate interpretations.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TRIGRAMS = {
    1: {"name": "乾", "symbol": "☰", "image": "天", "element": "金", "lines": [1, 1, 1]},
    2: {"name": "兑", "symbol": "☱", "image": "泽", "element": "金", "lines": [1, 1, 0]},
    3: {"name": "离", "symbol": "☲", "image": "火", "element": "火", "lines": [1, 0, 1]},
    4: {"name": "震", "symbol": "☳", "image": "雷", "element": "木", "lines": [1, 0, 0]},
    5: {"name": "巽", "symbol": "☴", "image": "风", "element": "木", "lines": [0, 1, 1]},
    6: {"name": "坎", "symbol": "☵", "image": "水", "element": "水", "lines": [0, 1, 0]},
    7: {"name": "艮", "symbol": "☶", "image": "山", "element": "土", "lines": [0, 0, 1]},
    8: {"name": "坤", "symbol": "☷", "image": "地", "element": "土", "lines": [0, 0, 0]},
}

BRANCHES = [
    ("子", 1, "23:00-00:59"),
    ("丑", 2, "01:00-02:59"),
    ("寅", 3, "03:00-04:59"),
    ("卯", 4, "05:00-06:59"),
    ("辰", 5, "07:00-08:59"),
    ("巳", 6, "09:00-10:59"),
    ("午", 7, "11:00-12:59"),
    ("未", 8, "13:00-14:59"),
    ("申", 9, "15:00-16:59"),
    ("酉", 10, "17:00-18:59"),
    ("戌", 11, "19:00-20:59"),
    ("亥", 12, "21:00-22:59"),
]

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def normalize(value: int, modulus: int) -> int:
    remainder = value % modulus
    return modulus if remainder == 0 else remainder


def parse_utc_offset(value: str) -> timezone:
    if len(value) != 6 or value[0] not in "+-" or value[3] != ":":
        raise ValueError("utc offset must use +HH:MM or -HH:MM")
    hours = int(value[1:3])
    minutes = int(value[4:6])
    if hours > 14 or minutes > 59:
        raise ValueError("utc offset is out of range")
    delta = timedelta(hours=hours, minutes=minutes)
    if value[0] == "-":
        delta = -delta
    return timezone(delta)


def parse_datetime(value: str | None, utc_offset: str) -> datetime:
    tz = parse_utc_offset(utc_offset)
    if value is None:
        return datetime.now(tz)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def branch_for_hour(hour: int) -> tuple[str, int, str]:
    if hour in (23, 0):
        return BRANCHES[0]
    return BRANCHES[(hour + 1) // 2]


def load_library() -> tuple[dict[tuple[int, ...], dict], dict[int, dict]]:
    library_path = Path(__file__).resolve().parent.parent / "references" / "hexagram-library.json"
    data = json.loads(library_path.read_text(encoding="utf-8"))
    by_lines = {tuple(item["array"]): item for item in data["hexagrams"]}
    by_id = {item["id"]: item for item in data["hexagrams"]}
    if len(by_lines) != 64 or len(by_id) != 64:
        raise RuntimeError("hexagram library must contain 64 unique records")
    return by_lines, by_id


def compound_name(hexagram: dict) -> str:
    lower_name, upper_name = hexagram["combination"]
    lower = next(item for item in TRIGRAMS.values() if item["name"] == lower_name)
    upper = next(item for item in TRIGRAMS.values() if item["name"] == upper_name)
    if lower_name == upper_name:
        return f"{upper_name}为{upper['image']}"
    return f"{upper['image']}{lower['image']}{hexagram['name']}"


def line_drawing(lines: list[int]) -> list[str]:
    return ["━━━━━━" if value else "━━  ━━" for value in reversed(lines)]


def element_relation(body: str, use: str) -> dict[str, str]:
    if body == use:
        return {"code": "比和", "traditional_text": "体用同类，称为比和。"}
    if GENERATES[use] == body:
        return {"code": "用生体", "traditional_text": "用卦五行生体卦五行。"}
    if GENERATES[body] == use:
        return {"code": "体生用", "traditional_text": "体卦五行生用卦五行。"}
    if CONTROLS[body] == use:
        return {"code": "体克用", "traditional_text": "体卦五行克用卦五行。"}
    return {"code": "用克体", "traditional_text": "用卦五行克体卦五行。"}


def hexagram_summary(item: dict) -> dict:
    return {
        "number": item["id"],
        "name": item["name"],
        "full_name": compound_name(item),
        "symbol": item["symbol"],
        "lower_trigram": item["combination"][0],
        "upper_trigram": item["combination"][1],
        "lines_bottom_to_top": item["array"],
        "drawing_top_to_bottom": line_drawing(item["array"]),
        "gua_ci": item["scripture"],
        "source": f"https://zh.wikisource.org/wiki/周易/{item['name']}",
    }


def calculate(number: int, moment: datetime) -> dict:
    if number <= 0:
        raise ValueError("number must be a positive integer")
    if moment.utcoffset() is None:
        raise ValueError("moment must include timezone information")

    compact_offset = moment.strftime("%z")
    utc_offset = f"{compact_offset[:3]}:{compact_offset[3:]}"

    by_lines, _ = load_library()
    branch_name, branch_number, branch_range = branch_for_hour(moment.hour)

    upper_number = normalize(number, 8)
    lower_number = normalize(branch_number, 8)
    moving_line = normalize(number + branch_number, 6)

    upper = TRIGRAMS[upper_number]
    lower = TRIGRAMS[lower_number]
    primary_lines = lower["lines"] + upper["lines"]
    primary = by_lines[tuple(primary_lines)]

    changed_lines = primary_lines.copy()
    changed_lines[moving_line - 1] = 1 - changed_lines[moving_line - 1]
    changed = by_lines[tuple(changed_lines)]

    mutual_lower_lines = primary_lines[1:4]
    mutual_upper_lines = primary_lines[2:5]
    mutual_lines = mutual_lower_lines + mutual_upper_lines
    mutual = by_lines[tuple(mutual_lines)]

    moving_trigram = "下卦" if moving_line <= 3 else "上卦"
    if moving_line <= 3:
        body = upper
        use = lower
    else:
        body = lower
        use = upper
    relation = element_relation(body["element"], use["element"])

    line_record = next(line for line in primary["lines"] if line["id"] == moving_line)

    return {
        "schema_version": "1.1",
        "method": {
            "name": "梅花易数·一数成卦",
            "rule": "报数为上卦，时辰地支序数为下卦，报数与时数之和除六取动爻。",
            "trigram_sequence": "乾一、兑二、离三、震四、巽五、坎六、艮七、坤八",
            "zero_remainder_rule": "卦数余0按8计，动爻余0按6计。",
            "stability": "同一报数、同一时辰得到相同结果；跨时辰结果会按传统规则变化。",
        },
        "input": {
            "reported_number": number,
            "datetime": moment.isoformat(),
            "utc_offset": utc_offset,
            "earthly_branch_hour": branch_name,
            "hour_number": branch_number,
            "hour_range": branch_range,
        },
        "calculation": {
            "upper_trigram": f"{number} ÷ 8，取余为 {upper_number} → {upper['name']}{upper['symbol']}",
            "lower_trigram": f"{branch_name}时序数 {branch_number} ÷ 8，取余为 {lower_number} → {lower['name']}{lower['symbol']}",
            "moving_line": f"({number} + {branch_number}) ÷ 6，取余为 {moving_line} → 第{moving_line}爻动",
            "mutual_hexagram": "取本卦二三四爻为互卦下卦，三四五爻为互卦上卦。",
            "changed_hexagram": f"本卦第{moving_line}爻阴阳翻转。",
        },
        "primary_hexagram": hexagram_summary(primary),
        "moving_line": {
            "position": moving_line,
            "name": line_record["name"],
            "scripture": line_record["scripture"],
            "moving_trigram": moving_trigram,
        },
        "mutual_hexagram": hexagram_summary(mutual),
        "changed_hexagram": hexagram_summary(changed),
        "body_use": {
            "body_trigram": body["name"],
            "body_element": body["element"],
            "use_trigram": use["name"],
            "use_element": use["element"],
            "relation": relation["code"],
            "traditional_text": relation["traditional_text"],
            "rule": "动者为用，静者为体。",
        },
        "scope_note": "以上只展示传统起卦计算与古籍原文查表，不等于对考试结果的科学预测。",
    }


def render_text(result: dict) -> str:
    primary = result["primary_hexagram"]
    mutual = result["mutual_hexagram"]
    changed = result["changed_hexagram"]
    moving = result["moving_line"]
    body_use = result["body_use"]
    lines = [
        "【起卦方法】",
        result["method"]["name"],
        result["method"]["rule"],
        "",
        "【输入】",
        f"报数：{result['input']['reported_number']}",
        f"起卦时间：{result['input']['datetime']}",
        f"时区：UTC{result['input']['utc_offset']}",
        f"时辰：{result['input']['earthly_branch_hour']}时（序数 {result['input']['hour_number']}）",
        "",
        "【计算过程】",
        f"上卦：{result['calculation']['upper_trigram']}",
        f"下卦：{result['calculation']['lower_trigram']}",
        f"动爻：{result['calculation']['moving_line']}",
        "",
        f"【本卦】{primary['symbol']} {primary['full_name']}（第{primary['number']}卦）",
        *primary["drawing_top_to_bottom"],
        f"卦辞：{primary['gua_ci']}",
        f"动爻：{moving['name']}：{moving['scripture']}",
        "",
        f"【互卦】{mutual['symbol']} {mutual['full_name']}（第{mutual['number']}卦）",
        f"【变卦】{changed['symbol']} {changed['full_name']}（第{changed['number']}卦）",
        "",
        "【体用】",
        f"体：{body_use['body_trigram']}（{body_use['body_element']}）",
        f"用：{body_use['use_trigram']}（{body_use['use_element']}）",
        f"关系：{body_use['relation']}——{body_use['traditional_text']}",
        "",
        result["scope_note"],
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="梅花易数一数成卦确定性计算器")
    parser.add_argument("--number", type=int, required=True, help="用户报出的正整数")
    parser.add_argument("--datetime", help="ISO 8601 时间；省略则使用当前时间")
    parser.add_argument("--utc-offset", default="+08:00", help="起卦地 UTC 偏移，默认 +08:00")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    try:
        moment = parse_datetime(args.datetime, args.utc_offset)
        result = calculate(args.number, moment)
    except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
