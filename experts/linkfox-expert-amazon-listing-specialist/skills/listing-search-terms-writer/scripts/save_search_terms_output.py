#!/usr/bin/env python3
"""listing-search-terms-writer 落盘器。"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
from listing_spec import extract_spec_arg, resolve_limit, tag  # type: ignore

SLUG = "linkfox-listing-search-terms-writer"
# 250 bytes 是平台真实上限（Layer A，超限整个字段不被索引）；spec 只能收紧不能放宽
BYTES_MAX = 250

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def _read_input(argv: list[str]) -> str:
    if not argv or argv[0] == "-":
        return sys.stdin.read() if not sys.stdin.isatty() else ""
    return open(argv[0], encoding="utf-8").read() if os.path.isfile(argv[0]) else argv[0]


def _tokenize(text: str) -> list[str]:
    """Unicode 归一化后按完整词元切分，不对多语言文本强套英文词干规则。"""
    normalized = unicodedata.normalize("NFKC", text or "").casefold()
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


def _extract_front_text(value: str) -> str:
    """把 --dedup-from-listing 的入参解析成前台纯文本。

    入参可以是：① 文件路径（JSON 含 title/item_highlights/bullets/description，
    或纯文本文件）；② 内联 JSON 字符串；③ 直接的纯文本（title+bullets 拼接）。
    """
    raw = value
    if os.path.isfile(value):
        try:
            raw = open(value, encoding="utf-8").read()
        except OSError:
            return value
    try:
        doc = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
    if isinstance(doc, str):
        return doc
    if isinstance(doc, list):
        return " ".join(str(x) for x in doc)
    if isinstance(doc, dict):
        parts: list[str] = []
        for key in ("title", "item_highlights", "itemHighlights", "description"):
            v = doc.get(key)
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                parts.append(" ".join(str(x) for x in v))
        bullets = doc.get("bullets") or doc.get("aboutItemFivePoint")
        if isinstance(bullets, list):
            parts.append(" ".join(str(x) for x in bullets))
        elif isinstance(bullets, str):
            parts.append(bullets)
        return " ".join(parts)
    return raw


def dedup_against_front(terms: str, front_texts: list[str]) -> tuple[str, list[str]]:
    """从 search_terms 中剔除前台字段已出现的词。

    返回 (去重后的搜索词, 被移除的词列表)。按 Unicode 归一化后的完整词元比较，
    不使用可能误伤其他站点语言的英文词干规则。
    """
    front_tokens = {token for text in front_texts for token in _tokenize(text)}
    if not front_tokens:
        return terms, []

    kept: list[str] = []
    removed: list[str] = []
    for token in _tokenize(terms):
        if token in front_tokens:
            removed.append(token)
        else:
            kept.append(token)
    return " ".join(kept), removed


def _validate(payload: dict, spec: dict | None = None) -> list[str]:
    errors: list[str] = []
    terms = str(payload.get("search_terms") or "")
    if not terms.strip():
        errors.append("缺少 search_terms")
        return errors

    byte_count = len(terms.encode("utf-8"))
    max_bytes, layer = resolve_limit(spec, "search_terms", "bytes_max", BYTES_MAX)
    max_bytes = min(max_bytes or BYTES_MAX, BYTES_MAX)  # 平台上限不可放宽
    if byte_count > max_bytes:
        which = "platform" if byte_count > BYTES_MAX else layer
        errors.append(f"{tag(which)} search_terms 超长：{byte_count} bytes > {max_bytes}；未修改原文")
    payload["byte_count"] = byte_count
    return errors


def main() -> None:
    argv, spec = extract_spec_arg(sys.argv[1:])
    # --strict is retained as a no-op compatibility flag; validation is always strict.
    argv = [a for a in argv if a != "--strict"]

    # Compatibility: --dedup-from-listing now validates overlap without mutating content.
    # Prefer the accurately named --check-against-listing in new callers.
    dedup_inputs: list[str] = []
    cleaned: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--dedup-from-listing", "--check-against-listing"):
            if i + 1 < len(argv):
                dedup_inputs.append(argv[i + 1])
                i += 2
                continue
            i += 1
            continue
        if a.startswith("--dedup-from-listing="):
            dedup_inputs.append(a.split("=", 1)[1])
            i += 1
            continue
        if a.startswith("--check-against-listing="):
            dedup_inputs.append(a.split("=", 1)[1])
            i += 1
            continue
        cleaned.append(a)
        i += 1
    argv = cleaned

    try:
        payload = json.loads(_read_input(argv))
    except json.JSONDecodeError as e:
        print(f"输入不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(1)

    errors: list[str] = []
    # Validate front-end overlap, but never delete or rewrite generated terms.
    if dedup_inputs:
        front_texts = [_extract_front_text(v) for v in dedup_inputs]
        original_terms = str(payload.get("search_terms") or "")
        _deduped, removed = dedup_against_front(original_terms, front_texts)
        if removed:
            errors.append(
                "search_terms 与前台文案重复："
                + ", ".join(removed[:20])
                + ("…" if len(removed) > 20 else "")
                + "；未修改原文"
            )

    errors.extend(_validate(payload, spec))
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from linkfox_save import save_json_payload  # type: ignore

    # 载荷自描述：UI 的 skill-data-router 按 `kind` 精确路由，没有 kind 的裸 JSON
    # 只能落到 FormattedJsonView 兜底。已有 kind 时不覆盖调用方的值。
    payload.setdefault("kind", "listingSearchTerms")
    payload.setdefault("schema_version", 1)

    save_json_payload(
        SLUG,
        payload,
        summary_lines=[f"已落盘后台搜索词 {payload.get('byte_count')} bytes"],
    )


if __name__ == "__main__":
    main()
