#!/usr/bin/env python3
"""Normalize and save Stage 2 buyer questions for build_spec and the Writer."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

KIND = "listingBuyerQuestions"
SCHEMA_VERSION = 1


def _fail(message: str) -> None:
    print(f"buyer questions 校验未通过: {message}", file=sys.stderr)
    raise SystemExit(1)


def normalize(payload: Any) -> dict[str, Any]:
    raw_questions = payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(raw_questions, list):
        _fail("输入必须是问题数组或包含 questions 数组的对象")
    questions: list[dict[str, Any]] = []
    for index, item in enumerate(raw_questions):
        if isinstance(item, str):
            item = {"question": item}
        if not isinstance(item, dict):
            _fail(f"questions[{index}] 必须是字符串或对象")
        question = str(item.get("question") or item.get("text") or "").strip()
        if not question:
            _fail(f"questions[{index}] 缺少 question")
        target_fields = item.get("target_fields", item.get("targetFields", ["bullets"]))
        if isinstance(target_fields, str):
            target_fields = [target_fields]
        if not isinstance(target_fields, list) or not all(
            isinstance(field, str) and field.strip() for field in target_fields
        ):
            _fail(f"questions[{index}].target_fields 必须是非空字符串数组")
        questions.append({
            "question": question,
            "source": str(item.get("source") or "insight").strip() or "insight",
            "strength": str(item.get("strength") or "unknown").strip() or "unknown",
            "target_fields": [field.strip() for field in target_fields],
        })
    if not questions:
        _fail("questions 不能为空")
    return {"kind": KIND, "schema_version": SCHEMA_VERSION, "questions": questions}


def question_items(payload: Any) -> list[Any]:
    """Build-spec 兼容入口：接受 canonical 信封和历史裸数组。"""
    if isinstance(payload, dict):
        if payload.get("kind") not in (None, KIND):
            raise ValueError(f"buyer questions kind must be {KIND}")
        payload = payload.get("questions")
    if not isinstance(payload, list):
        raise ValueError("buyer questions must be an array or a questions envelope")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="落盘 listingBuyerQuestions")
    parser.add_argument("--out", required=True)
    parser.add_argument("--source", default=None, help="输入 JSON；缺省从 stdin 读")
    args = parser.parse_args()
    try:
        if args.source:
            with open(args.source, encoding="utf-8") as handle:
                raw = handle.read()
        else:
            raw = sys.stdin.read()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"无法读取输入: {exc}")
        return
    result = normalize(payload)
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(f"Buyer questions: {len(result['questions'])}")
    print(f"JSON artifact: {out_path}")


if __name__ == "__main__":
    main()
