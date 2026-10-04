#!/usr/bin/env python3
"""Calculate evidence-aware Offer comparison scores deterministically.

Input JSON example:
{
  "offers": ["Offer A", "Offer B"],
  "dimensions": [
    {"name": "薪酬", "weight": 30, "scores": {"Offer A": 4, "Offer B": 3}},
    {"name": "成长", "weight": 25, "scores": {"Offer A": null, "Offer B": 4}}
  ]
}

Only dimensions with valid scores for every offer participate in ranking.
Scores must be integers from 1 to 5 or null. Weights must be non-negative.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """Raised when the score input violates the comparison contract."""


def load_input(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError(f"输入文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"JSON 格式错误：{exc}") from exc

    if not isinstance(data, dict):
        raise InputError("顶层数据必须是 JSON 对象。")
    return data


def validate(data: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    offers = data.get("offers")
    dimensions = data.get("dimensions")

    if not isinstance(offers, list) or len(offers) < 2:
        raise InputError("offers 必须是至少包含两个名称的数组。")
    if any(not isinstance(name, str) or not name.strip() for name in offers):
        raise InputError("每个 Offer 名称必须是非空字符串。")
    if len(set(offers)) != len(offers):
        raise InputError("Offer 名称不能重复。")
    if not isinstance(dimensions, list) or not dimensions:
        raise InputError("dimensions 必须是非空数组。")

    seen_names: set[str] = set()
    normalized: list[dict[str, Any]] = []

    for index, item in enumerate(dimensions, start=1):
        if not isinstance(item, dict):
            raise InputError(f"第 {index} 个维度必须是对象。")

        name = item.get("name")
        weight = item.get("weight")
        scores = item.get("scores")

        if not isinstance(name, str) or not name.strip():
            raise InputError(f"第 {index} 个维度缺少有效 name。")
        if name in seen_names:
            raise InputError(f"维度名称重复：{name}")
        seen_names.add(name)

        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise InputError(f"维度“{name}”的 weight 必须是有限的非负数。")
        try:
            normalized_weight = float(weight)
        except OverflowError as exc:
            raise InputError(f"维度“{name}”的 weight 超出可计算范围。") from exc
        if not math.isfinite(normalized_weight) or normalized_weight < 0:
            raise InputError(f"维度“{name}”的 weight 必须是有限的非负数。")
        if not isinstance(scores, dict):
            raise InputError(f"维度“{name}”的 scores 必须是对象。")

        normalized_scores: dict[str, int | None] = {}
        for offer in offers:
            score = scores.get(offer)
            if score is None:
                normalized_scores[offer] = None
                continue
            if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
                raise InputError(f"维度“{name}”中“{offer}”的分值必须是 1—5 的整数或 null。")
            normalized_scores[offer] = score

        normalized.append({"name": name, "weight": normalized_weight, "scores": normalized_scores})

    total_weight = sum(item["weight"] for item in normalized)
    if not math.isfinite(total_weight) or total_weight <= 0:
        raise InputError("全部维度的权重之和必须是有限且大于 0 的数值。")

    return offers, normalized


def confidence_label(coverage: float) -> str:
    if coverage < 0.60:
        return "不足以排序"
    if coverage < 0.80:
        return "低"
    if coverage < 0.95:
        return "中"
    return "高"


def difference_label(difference: float | None, coverage: float) -> str:
    if coverage < 0.60 or difference is None:
        return "共同证据覆盖不足，不输出排序。"
    if coverage < 0.80:
        return "共同证据覆盖有限，当前顺序只代表低置信度倾向。"
    if difference < 5:
        return "结果接近，不构成明显优胜。"
    if difference <= 10:
        return "在当前权重下略占优。"
    return "在当前权重和已知证据下优势较明显。"


def calculate(offers: list[str], dimensions: list[dict[str, Any]]) -> dict[str, Any]:
    total_weight = sum(item["weight"] for item in dimensions)
    common = [
        item
        for item in dimensions
        if item["weight"] > 0 and all(item["scores"][offer] is not None for offer in offers)
    ]
    missing = [
        {
            "dimension": item["name"],
            "missing_offers": [offer for offer in offers if item["scores"][offer] is None],
        }
        for item in dimensions
        if any(item["scores"][offer] is None for offer in offers)
    ]

    common_weight = sum(item["weight"] for item in common)
    coverage = common_weight / total_weight if total_weight else 0.0

    raw_scores: dict[str, float | None] = {}
    for offer in offers:
        if common_weight <= 0:
            raw_scores[offer] = None
            continue
        weighted_mean = sum(item["scores"][offer] * item["weight"] for item in common) / common_weight
        raw_scores[offer] = round(weighted_mean / 5 * 100, 2)

    # Evidence coverage below 60% is insufficient even for displaying total scores.
    scores = raw_scores if coverage >= 0.60 else {offer: None for offer in offers}

    ranking: list[dict[str, Any]] = []
    ranking_groups: list[dict[str, Any]] = []
    ranking_text: str | None = None
    top_difference: float | None = None
    if all(score is not None for score in scores.values()):
        ranking = [
            {"offer": offer, "score": scores[offer]}
            for offer in sorted(offers, key=lambda name: (-float(scores[name]), offers.index(name)))
        ]
        for item in ranking:
            if ranking_groups and ranking_groups[-1]["score"] == item["score"]:
                ranking_groups[-1]["offers"].append(item["offer"])
            else:
                ranking_groups.append({"score": item["score"], "offers": [item["offer"]]})
        ranking_text = " > ".join(" = ".join(group["offers"]) for group in ranking_groups)
        if len(ranking) >= 2:
            top_difference = round(float(ranking[0]["score"]) - float(ranking[1]["score"]), 2)

    return {
        "offers": offers,
        "common_dimensions": [item["name"] for item in common],
        "missing_dimensions": missing,
        "total_weight": round(total_weight, 4),
        "common_weight": round(common_weight, 4),
        "coverage": round(coverage, 4),
        "coverage_percent": round(coverage * 100, 2),
        "confidence": confidence_label(coverage),
        "scores": scores,
        "ranking": ranking,
        "ranking_groups": ranking_groups,
        "ranking_text": ranking_text,
        "top_difference": top_difference,
        "difference_interpretation": difference_label(top_difference, coverage),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "## Offer 确定性计算结果",
        "",
        f"- 共同维度：{('、'.join(result['common_dimensions']) or '无')}",
        f"- 共同维度覆盖率：{result['coverage_percent']:.2f}%",
        f"- 结论置信度：{result['confidence']}",
        "",
        "| Offer | 归一化得分（0—100） |",
        "|---|---:|",
    ]

    for offer in result["offers"]:
        score = result["scores"][offer]
        lines.append(f"| {offer} | {'不计算' if score is None else f'{score:.2f}'} |")

    lines.extend(["", f"- 分差解释：{result['difference_interpretation']}"])

    if result["ranking_text"]:
        lines.append(f"- 当前排序：{result['ranking_text']}")
    else:
        lines.append("- 当前排序：不输出")

    if result["missing_dimensions"]:
        lines.extend(["", "### 待确认维度"])
        for item in result["missing_dimensions"]:
            lines.append(f"- {item['dimension']}：缺少 {', '.join(item['missing_offers'])} 的有效分值")

    lines.extend([
        "",
        "> 该结果只反映用户确认的分值、权重与共同证据维度，不替代用户决策。",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="计算 Offer 共同维度覆盖率与加权得分。")
    parser.add_argument("input", type=Path, help="评分输入 JSON 文件")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    try:
        data = load_input(args.input)
        offers, dimensions = validate(data)
        result = calculate(offers, dimensions)
    except InputError as exc:
        print(f"输入错误：{exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
