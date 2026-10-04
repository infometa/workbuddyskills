#!/usr/bin/env python3
"""save_keyword_plan — Stage 2 词表计划落盘（listingKeywordPlan）。

`keywords.json` 是 UI 词表工作台（KeywordPlanPanel）和 `[fieldAdjust:keywords]`
回写链路的唯一数据入口，此前只有文档口头约定、没有生产者，导致模型自由写文件、
schema 漂移、UI 认不出 kind。本脚本是它唯一的落盘出口。

设计铁律：
- 只校验和落盘，不改词、不补词、不打分。缺数据就是缺数据。
- 用户手输词没有检索数据：`source=user`、`search_volume=null`，禁止编造 volume。
- 输出走 `JSON artifact:` 行（伴生产物），不占用一次 Bash 唯一的
  `Saved full response:` 行。

用法：
    python3 save_keyword_plan.py --out /abs/keywords.json --source /abs/plan.json

    # 洞察只需输出四组词；脚本从 matrix 回填来源与真实搜索量
    python3 save_keyword_plan.py --out /abs/keywords.json \
      --source /abs/grouped-plan.json --matrix /abs/keyword-matrix.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

KIND = "listingKeywordPlan"
SCHEMA_VERSION = 1
GROUPS = ("core", "scene", "pain", "attribute")
STRING_LISTS = ("locked", "banned")


def _fail(msg: str) -> None:
    print(f"keyword plan 校验未通过: {msg}", file=sys.stderr)
    raise SystemExit(1)


def normalize(payload: object) -> dict:
    """把宽松输入归一为 UI 既有的 listingKeywordPlan 形状，形状不对就失败。"""
    if not isinstance(payload, dict):
        _fail("顶层必须是 JSON 对象")

    kind = payload.get("kind", KIND)
    if kind != KIND:
        _fail(f"kind 必须是 {KIND}，收到 {kind!r}")

    plan: dict[str, object] = {"kind": KIND, "schema_version": SCHEMA_VERSION}

    for group in GROUPS:
        raw = payload.get(group, [])
        if raw is None:
            raw = []
        if not isinstance(raw, list):
            _fail(f"`{group}` 必须是数组")
        words: list[dict[str, object]] = []
        for idx, item in enumerate(raw):
            if isinstance(item, str):
                item = {"word": item}
            if not isinstance(item, dict):
                _fail(f"`{group}[{idx}]` 必须是字符串或对象")
            word = str(item.get("word") or "").strip()
            if not word:
                _fail(f"`{group}[{idx}]` 缺少 word")
            volume = item.get("search_volume", None)
            if volume is not None and not isinstance(volume, (int, float)):
                _fail(f"`{group}[{idx}].search_volume` 只能是数字或 null")
            source = str(item.get("source") or "").strip() or "unknown"
            if source == "user" and volume is not None:
                _fail(
                    f"`{group}[{idx}]` 是用户手输词（source=user），"
                    "没有检索数据，search_volume 必须为 null"
                )
            words.append({"word": word, "source": source, "search_volume": volume})
        plan[group] = words

    for key in STRING_LISTS:
        raw = payload.get(key, [])
        if raw is None:
            raw = []
        if not isinstance(raw, list):
            _fail(f"`{key}` 必须是数组")
        normalized: list[str] = []
        for idx, item in enumerate(raw):
            # 语义步骤经常沿用四个词组的 {word, source, search_volume} 形状。
            # locked/banned 最终契约仍是字符串数组；这里只做无损形状归一，
            # 不新增、删除或改写任何关键词。
            if isinstance(item, dict):
                item = item.get("word")
            if not isinstance(item, str):
                _fail(f"`{key}[{idx}]` 必须是字符串或带 word 的对象")
            word = item.strip()
            if word:
                normalized.append(word)
        plan[key] = normalized

    known = {w["word"] for group in GROUPS for w in plan[group]}  # type: ignore[index]
    missing = [w for w in plan["locked"] if w not in known]  # type: ignore[union-attr]
    if missing:
        _fail(
            f"locked 里的词必须先出现在四个词组中: {missing}；"
            "品牌名由 spec.brands 传递，不要放入 locked"
        )

    if not any(plan[group] for group in GROUPS):
        _fail("四个词组全空——没有词表就不要落盘，先如实标注 keyword_data_unavailable")

    return plan


def enrich_from_matrix(plan: dict, matrix: object) -> dict:
    """按词精确回填 matrix 证据，不参与语义分组、不改洞察结论。"""
    if not isinstance(matrix, dict):
        _fail("--matrix 顶层必须是 JSON 对象")
    rows = matrix.get("scored_table")
    if not isinstance(rows, list):
        _fail("--matrix 必须包含 scored_table 数组")
    evidence: dict[str, dict[str, object]] = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            _fail(f"--matrix scored_table[{idx}] 必须是对象")
        word = str(row.get("word") or row.get("keyword") or row.get("text") or "").strip()
        if not word:
            continue
        volume = row.get("weekly_search_volume", row.get("search_volume"))
        if volume is not None and not isinstance(volume, (int, float)):
            volume = None
        evidence.setdefault(word.casefold(), {
            "source": str(row.get("source") or "unknown").strip() or "unknown",
            "search_volume": volume,
        })

    for group in GROUPS:
        for item in plan[group]:
            # 显式 user/local 来源优先，防止把推导词误标成 SIF。
            if item["source"] not in {"", "unknown"}:
                continue
            matched = evidence.get(str(item["word"]).casefold())
            if matched:
                item.update(matched)
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="落盘 listingKeywordPlan（keywords.json）")
    parser.add_argument("--out", required=True, help="keywords.json 输出绝对路径")
    parser.add_argument("--source", required=True, help="输入 JSON 文件")
    parser.add_argument(
        "--matrix", default=None,
        help="原始 keyword matrix JSON；仅按词回填 source/weekly_search_volume，不做语义分组",
    )
    args = parser.parse_args()

    try:
        with open(args.source, encoding="utf-8") as f:
            raw = f.read()
    except OSError as exc:
        _fail(f"无法读取 --source: {exc}")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(f"输入不是合法 JSON: {exc}")
        return

    plan = normalize(payload)
    if args.matrix:
        try:
            with open(args.matrix, encoding="utf-8") as f:
                matrix = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            _fail(f"无法读取 --matrix: {exc}")
            return
        plan = enrich_from_matrix(plan, matrix)

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    counts = " ".join(f"{g}={len(plan[g])}" for g in GROUPS)  # type: ignore[arg-type]
    print(f"Keyword plan: {counts} locked={len(plan['locked'])} banned={len(plan['banned'])}")  # type: ignore[arg-type]
    print(f"JSON artifact: {out_path}")


if __name__ == "__main__":
    main()
