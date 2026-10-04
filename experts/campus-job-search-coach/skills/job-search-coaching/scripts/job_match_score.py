#!/usr/bin/env python3
"""Calculate evidence coverage between job requirements and user materials.

Input JSON example:
{
  "requirements": [
    {"id": "M1", "text": "熟悉 Python", "kind": "must", "weight": 3, "evidence": 1},
    {"id": "N1", "text": "有开源项目", "kind": "nice", "weight": 1, "evidence": null},
    {"id": "G1", "text": "毕业时间符合要求", "kind": "gate", "weight": 5, "evidence": 0}
  ]
}

Evidence must be 1 (direct), 0.5 (adjacent), 0 (not shown), or null (unknown).
The score measures evidence coverage only. It is not an interview, hiring, or ATS probability.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """Raised when the input violates the scoring contract."""


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


def validate(data: dict[str, Any]) -> list[dict[str, Any]]:
    requirements = data.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise InputError("requirements 必须是非空数组。")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(requirements, start=1):
        if not isinstance(item, dict):
            raise InputError(f"第 {index} 条要求必须是对象。")
        req_id = item.get("id")
        text = item.get("text")
        kind = item.get("kind")
        weight = item.get("weight", 1)
        evidence = item.get("evidence")

        if not isinstance(req_id, str) or not req_id.strip():
            raise InputError(f"第 {index} 条要求缺少有效 id。")
        if req_id in seen_ids:
            raise InputError(f"要求 id 重复：{req_id}")
        seen_ids.add(req_id)
        if not isinstance(text, str) or not text.strip():
            raise InputError(f"要求 {req_id} 缺少有效 text。")
        if kind not in {"must", "nice", "gate"}:
            raise InputError(f"要求 {req_id} 的 kind 必须是 must、nice 或 gate。")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise InputError(f"要求 {req_id} 的 weight 必须是有限正数。")
        normalized_weight = float(weight)
        if not math.isfinite(normalized_weight) or normalized_weight <= 0:
            raise InputError(f"要求 {req_id} 的 weight 必须是有限正数。")
        if evidence is not None:
            if isinstance(evidence, bool) or not isinstance(evidence, (int, float)):
                raise InputError(f"要求 {req_id} 的 evidence 必须是 1、0.5、0 或 null。")
            evidence = float(evidence)
            if evidence not in {0.0, 0.5, 1.0}:
                raise InputError(f"要求 {req_id} 的 evidence 必须是 1、0.5、0 或 null。")

        normalized.append(
            {
                "id": req_id.strip(),
                "text": text.strip(),
                "kind": kind,
                "weight": normalized_weight,
                "evidence": evidence,
            }
        )
    return normalized


def score_group(items: list[dict[str, Any]]) -> dict[str, Any]:
    total_weight = sum(item["weight"] for item in items)
    known = [item for item in items if item["evidence"] is not None]
    known_weight = sum(item["weight"] for item in known)
    assessable_coverage = known_weight / total_weight if total_weight else 0.0
    score = None
    if known_weight > 0 and assessable_coverage >= 0.60:
        score = round(
            100 * sum(item["weight"] * item["evidence"] for item in known) / known_weight,
            2,
        )
    return {
        "score": score,
        "assessable_coverage": round(assessable_coverage, 4),
        "assessable_coverage_percent": round(assessable_coverage * 100, 2),
        "total_weight": round(total_weight, 4),
        "known_weight": round(known_weight, 4),
    }


def calculate(requirements: list[dict[str, Any]]) -> dict[str, Any]:
    groups = {
        kind: score_group([item for item in requirements if item["kind"] == kind])
        for kind in ("must", "nice", "gate")
        if any(item["kind"] == kind for item in requirements)
    }
    overall = score_group(requirements)
    buckets = {
        "direct": [item for item in requirements if item["evidence"] == 1.0],
        "adjacent": [item for item in requirements if item["evidence"] == 0.5],
        "not_shown": [item for item in requirements if item["evidence"] == 0.0],
        "unknown": [item for item in requirements if item["evidence"] is None],
    }
    missed_gates = [
        item for item in requirements if item["kind"] == "gate" and item["evidence"] == 0.0
    ]
    if overall["score"] is None:
        confidence = "信息不足"
    elif overall["assessable_coverage"] < 0.80:
        confidence = "低"
    elif overall["assessable_coverage"] < 0.95:
        confidence = "中"
    else:
        confidence = "高"

    return {
        "metric_name": "岗位证据覆盖率",
        "warning": "该分数仅表示当前材料对岗位要求的证据覆盖，不是录用概率、拿面概率或 ATS 通过率。",
        "overall": overall,
        "groups": groups,
        "confidence": confidence,
        "missed_gates": missed_gates,
        "buckets": buckets,
    }


def render_markdown(result: dict[str, Any]) -> str:
    overall = result["overall"]
    score_text = "不计算" if overall["score"] is None else f"{overall['score']:.2f}%"
    lines = [
        "## 岗位证据覆盖结果",
        "",
        f"- 可判断要求权重覆盖：{overall['assessable_coverage_percent']:.2f}%",
        f"- 岗位证据覆盖率：{score_text}",
        f"- 结论置信度：{result['confidence']}",
        f"- 解释：{result['warning']}",
        "",
    ]
    if result["missed_gates"]:
        lines.append("### 未命中硬门槛")
        for item in result["missed_gates"]:
            lines.append(f"- {item['id']}：{item['text']}")
        lines.append("")

    labels = {
        "direct": "直接证据",
        "adjacent": "相邻证据",
        "not_shown": "当前材料未体现",
        "unknown": "无法判断",
    }
    for key, label in labels.items():
        items = result["buckets"][key]
        lines.append(f"### {label}")
        if items:
            for item in items:
                lines.append(f"- {item['id']} [{item['kind']}]：{item['text']}")
        else:
            lines.append("- 无")
        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="计算岗位要求的证据覆盖率。")
    parser.add_argument("input", type=Path, help="评分输入 JSON 文件")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    try:
        data = load_input(args.input)
        requirements = validate(data)
        result = calculate(requirements)
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
