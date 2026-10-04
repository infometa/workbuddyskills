#!/usr/bin/env python3
"""validate_fields — 字段级安检（无级联），Task 4。

对 draft.json 中的每个字段（title/bullets/description/search_terms/
item_highlights）独立做安检：平台字符限值、受限内容库扫描、竞品品牌词、
特殊符号、核心关键词完整性（拆词检测）、前后台重复词、事实忠实度启发式。

设计铁律：
- 每字段一个纯函数（_check_title/_check_bullets/...），逐字段 try/except，
  单字段异常只影响该字段（status: "fail"），不阻断其它字段（无级联）。
- 本脚本永远不修改任何文案，只产出报告。
- CLI 退出码恒为 0（报告驱动，是否阻断由编排层根据报告决策）。

用法（库）：
    from validate_fields import check_fields
    report = check_fields(draft, spec, facts_text="...")

用法（CLI）：
    python3 validate_fields.py --draft /abs/listing-draft.json --spec /abs/spec.json \\
        [--facts /abs/product-facts.md] --out /abs/check-report.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import restricted_content_scan  # noqa: E402

_SPECIAL_SYMBOL_RE = re.compile(
    r"[™®©€†‡¢£¥±"
    r"\U0001F300-\U0001FAFF☀-➿]"
)

# 数字+真实单位 token，例如 28-45cm / 20 hours / 99 kg。
# 单位必须来自明确白名单；旧版 ``[A-Za-z]+`` 会把 ``Bluetooth 5.4 with``
# 误识别为事实声明 ``5.4 with``。
_UNIT_TOKEN_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?(?:\s*-\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:millimeters?|centimeters?|kilometers?|meters?|inches?|feet|foot|"
    r"milligrams?|kilograms?|grams?|ounces?|pounds?|gallons?|"
    r"milliseconds?|seconds?|minutes?|hours?|days?|years?|"
    r"fl\s*oz|mm|cm|km|m|mg|kg|oz|lbs?|ml|cl|l|"
    r"mah|ah|khz|mhz|ghz|hz|kw|w|v|gb|tb|°c|°f)\b",
    flags=re.IGNORECASE,
)

_ISSUE_SEVERITY = {
    "over_limit": "fail",
    "recommended_length": "warn",
    "missing_field": "fail",
    "empty_field": "fail",
    "type_error": "fail",
    "bullet_count": "fail",
    "empty_item": "fail",
    "competitor_brand": "fail",
    "special_symbol": "fail",
    "fact_conflict": "fail",
    "core_kw_split": "warn",
    "front_dup": "warn",
    # 单个重复词是可容忍的噪声；成规模重复意味着后台位被白白浪费，必须触发一次局部重写
    "front_dup_excess": "fail",
    # banned_term 的严重度按具体命中的 severity（block/review）单独判定
}

# 后台词与前台重复超过该数量即判 fail，交给 writer 做一次局部重写
_FRONT_DUP_FAIL_THRESHOLD = 3

_library_cache: dict[str, Any] = {}


def _load_library(library_path: str) -> dict:
    if library_path not in _library_cache:
        with open(library_path, encoding="utf-8") as f:
            _library_cache[library_path] = json.load(f)
    return _library_cache[library_path]


# 卖家避讳词允许的屈折后缀：复数、副词、现在分词、过去式。
# 刻意不含任意后缀——见 _hits_user_banned 的取舍表。
_INFLECTION_SUFFIX = r"(?:s|es|ies|ly|ing|ed)?"


def _hits_user_banned(text: str, term: str) -> bool:
    """卖家避讳词命中判定：**词首对齐 + 仅允许屈折后缀**，外加分隔符混淆检测。

    和平台受限词库的规则有意不同，两者期望不一样：
    - 受限词库是人工维护的短语表，走整词匹配，`best` 不该命中 `bestseller`；
    - 卖家避讳词是"这个词别出现在我的 listing 里"，`EGG` 要能拦下 `EGGS`、
      `WIRELESS` 要能拦下 `WIRELESSLY`——CLAUDE.md 里 `[卖家偏好]` 的示例避讳词
      字面就是 `WIRELESS、EGG`，整词匹配会让文档自带的例子被复数和副词绕过。

    **四种规则的取舍**（改这里之前先看这张表，三种朴素规则都被试过并否掉了）：

    | 规则 | EGGS/WIRELESSLY | LEGGINGS | petite（term=pet）| cleanser（term=clean）|
    |---|---|---|---|---|
    | 纯子串 | 拦住 | **误报** | **误报** | **误报** |
    | 整词 | **漏报** | 不误报 | 不误报 | 不误报 |
    | 词首对齐（任意后缀）| 拦住 | 不误报 | **误报** | **误报** |
    | 词首 + 屈折后缀（现状）| 拦住 | 不误报 | 不误报 | 不误报 |

    误报的代价是批量链路 exit 2 直接阻断交付，比漏报更贵，所以不能用纯子串或
    任意后缀；漏报是静默放行，所以也不能退回整词。只放行 `s/es/ies/ly/ing/ed`
    这几个屈折形式，既拦住复数副词逃逸，又不会让 `pet` 撞上 `petite`、
    `clean` 撞上 `cleanser`。

    **已知局限，都是有意留的边界，不是 bug**：

    1. 变形词干不处理：`baby` 拦不住 `babies`。
    2. 复合词不拦：`EGG` 拦不住 `EGGSHELL`（色号），但拦得住 `EGG-FREE`（连字符断词，
       走的是屈折分支的词尾断言）。要改成拦复合词，把 `_INFLECTION_SUFFIX` 换成 `.*?`，
       但那等于回到"词首对齐（任意后缀）"那一行的代价。
    3. **派生后缀 `-er/-est/-ers` 不拦**：`clean` 拦不住 `cleaner` / `cleanest`，
       `wash` 拦不住 `washer`。这是刻意的：`-s/-ly/-ing/-ed` 是同一个词的语法屈折，
       而 `-er` 派生出的已经是另一个名词，语义漂移更远；更要命的是加上它会把短词误报
       带回来——实测 `pet`→`peter`、`cat`→`cater`、`art`→`arter` 全部命中。
       想拦 `cleaner` 就把它写进避讳词表，别改这里的后缀集。

    这处已经改过四轮（自写正则 → 收敛到 find_spans → 词首任意后缀 → 词首+屈折），
    每一轮都是"补一个漏报带回一个误报"。上表四种朴素规则都试过并否掉了；剩下的是
    派生词和变形词干，属于已知边界。**改正则前先把上表和这三条局限读完。**

    混淆写法（`c-u-r-e`）沿用受限词库的实现，不另写一套。
    """
    needle = term.casefold().strip()
    if not needle:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(needle) + _INFLECTION_SUFFIX + r"(?![a-z0-9])"
    if re.search(pattern, text.casefold()):
        return True
    return bool(restricted_content_scan.find_spans(text, term))


def _scan_banned(text: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """调用 restricted_content_scan.scan 扫描单字段文本，命中转 issue。

    除平台违禁词库外，还扫描 `spec.user_banned_terms`——卖家偏好红线段的避讳词
    和词表工作台的禁用词都走这里，强度与平台违禁词同级（fail）。
    """
    if not text:
        return []
    library = _load_library(spec["banned_library"])
    hits = restricted_content_scan.scan({"title": text}, library)
    issues = []
    for hit in hits:
        issues.append({
            "code": "banned_term",
            "detail": f"{hit['term']} ({hit['category']}): {hit['reason']}",
            "replacement": hit.get("replacement"),
            "_severity": "fail" if hit["severity"] == "block" else "warn",
        })
    for term in spec.get("user_banned_terms") or []:
        if not isinstance(term, str) or not term.strip():
            continue
        if _hits_user_banned(text, term):
            issues.append({
                "code": "banned_term",
                "detail": f"{term} (user_banned): 卖家避讳词/词表禁用词，禁止出现在任何字段",
                "replacement": None,
                "_severity": "fail",
            })
    return issues


def _brand_hits(text: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """竞品品牌词命中（casefold 词边界匹配）；owned 白名单跳过。"""
    if not text:
        return []
    brands = spec.get("brands", {})
    owned_cf = {b.casefold() for b in (brands.get("owned") or [])}
    competitor = brands.get("competitor") or []
    issues = []
    seen = set()
    for brand in competitor:
        cf = brand.casefold()
        if cf in owned_cf or cf in seen:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(cf) + r"(?![a-z0-9])"
        if re.search(pattern, text.casefold()):
            seen.add(cf)
            issues.append({
                "code": "competitor_brand",
                "detail": f"检测到竞品品牌词：{brand}",
                "replacement": None,
            })
    return issues


def _special_symbols(text: str) -> list[dict[str, Any]]:
    """禁用特殊符号与 emoji 区段。"""
    if not text:
        return []
    found = []
    seen = set()
    for m in _SPECIAL_SYMBOL_RE.finditer(text):
        ch = m.group(0)
        if ch in seen:
            continue
        seen.add(ch)
        found.append(ch)
    return [
        {"code": "special_symbol", "detail": f"检测到禁用特殊符号：{ch!r}", "replacement": None}
        for ch in found
    ]


def _fact_context_issues(text: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect categorical keyword conflicts derived from verified target facts."""
    age_months = ((spec.get("fact_constraints") or {}).get("age_months") or {})
    minimum = age_months.get("min")
    if isinstance(minimum, int) and minimum >= 4 and re.search(r"\bnewborns?\b", text, re.IGNORECASE):
        return [{
            "code": "fact_conflict",
            "detail": f"检测到 newborn，但已核验适用年龄从 {minimum} 个月起",
            "replacement": f"Use an age phrase consistent with {minimum}+ months.",
        }]
    return []


def _extract_unit_tokens(text: str) -> list[str]:
    if not text:
        return []
    return _UNIT_TOKEN_RE.findall(text)


def _normalize_fact_match_text(text: str) -> str:
    """Normalize punctuation separators without weakening numeric/unit matching."""
    normalized = unicodedata.normalize("NFKC", text or "").casefold()
    normalized = re.sub(r"[^\w.,°]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def _core_keyword_analysis(title: str, core_keywords: list[str]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """核心关键词完整性：连续子串命中 / 缺失 / 拆词（issues）。"""
    hits: list[str] = []
    misses: list[str] = []
    issues: list[dict[str, Any]] = []
    title_cf = (title or "").casefold()
    for kw in core_keywords:
        kw_cf = kw.casefold()
        if kw_cf and kw_cf in title_cf:
            hits.append(kw)
            continue
        words = kw_cf.split()
        all_present = bool(words) and all(
            re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", title_cf)
            for w in words
        )
        if all_present:
            issues.append({
                "code": "core_kw_split",
                "detail": f"核心关键词「{kw}」在标题中被拆开（各词都在但不连续）",
                "replacement": None,
            })
            misses.append(kw)
        else:
            misses.append(kw)
    return hits, misses, issues


def _tokenize(text: str) -> list[str]:
    """Return Unicode-aware lexical tokens for deterministic overlap checks.

    NFKC folds compatibility forms (for example full-width Latin characters)
    without stripping locale characters.  ``[^\\W_]`` is the stdlib ``re``
    spelling for Unicode letters/digits, so German umlauts and French accents
    stay inside their words instead of becoming one-letter fragments.
    """
    normalized = unicodedata.normalize("NFKC", text or "").casefold()
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


def _status_from_issues(issues: list[dict[str, Any]]) -> str:
    has_fail = False
    has_warn = False
    for issue in issues:
        sev = issue.get("_severity") or _ISSUE_SEVERITY.get(issue["code"], "warn")
        if sev == "fail":
            has_fail = True
        elif sev == "warn":
            has_warn = True
    if has_fail:
        return "fail"
    if has_warn:
        return "warn"
    return "pass"


def _clean_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """去掉内部记账字段 `_severity`，只保留报告契约中的 code/detail/replacement。"""
    return [{"code": i["code"], "detail": i["detail"], "replacement": i.get("replacement")} for i in issues]


def _check_title(title: str, spec: dict[str, Any]) -> dict[str, Any]:
    chars = len(title)
    limit = spec["limits"]["title_max"]
    issues: list[dict[str, Any]] = []
    if limit is not None and chars > limit:
        issues.append({"code": "over_limit", "detail": f"标题超长：{chars} > {limit}", "replacement": None})
    issues += _scan_banned(title, spec)
    issues += _brand_hits(title, spec)
    issues += _special_symbols(title)
    issues += _fact_context_issues(title, spec)
    core_keywords = spec.get("keywords", {}).get("core_to_title") or []
    _, _, split_issues = _core_keyword_analysis(title, core_keywords)
    issues += split_issues
    return {
        "status": _status_from_issues(issues),
        "chars": chars,
        "limit": limit,
        "issues": _clean_issues(issues),
    }


def _check_description(description: str, spec: dict[str, Any]) -> dict[str, Any]:
    chars = len(description)
    limit = spec["limits"]["description_max"]
    issues: list[dict[str, Any]] = []
    if limit is not None and chars > limit:
        issues.append({"code": "over_limit", "detail": f"描述超长：{chars} > {limit}", "replacement": None})
    issues += _scan_banned(description, spec)
    issues += _brand_hits(description, spec)
    issues += _special_symbols(description)
    issues += _fact_context_issues(description, spec)
    return {
        "status": _status_from_issues(issues),
        "chars": chars,
        "limit": limit,
        "issues": _clean_issues(issues),
    }


def _check_search_terms(search_terms: str, spec: dict[str, Any], front_dup_tokens: list[str]) -> dict[str, Any]:
    byte_len = len(search_terms.encode("utf-8"))
    limit = spec["limits"]["search_terms_bytes_max"]
    issues: list[dict[str, Any]] = []
    if limit is not None and byte_len > limit:
        issues.append({"code": "over_limit", "detail": f"后台词超长：{byte_len} bytes > {limit}", "replacement": None})
    issues += _scan_banned(search_terms, spec)
    issues += _brand_hits(search_terms, spec)
    issues += _special_symbols(search_terms)
    issues += _fact_context_issues(search_terms, spec)
    for token in front_dup_tokens:
        issues.append({
            "code": "front_dup",
            "detail": f"后台词「{token}」与前台（标题/五点）已含词重复",
            "replacement": None,
        })
    if len(front_dup_tokens) > _FRONT_DUP_FAIL_THRESHOLD:
        issues.append({
            "code": "front_dup_excess",
            "detail": (
                f"后台词与前台重复 {len(front_dup_tokens)} 个（阈值 {_FRONT_DUP_FAIL_THRESHOLD}）："
                f"{'、'.join(front_dup_tokens)}；这些词已在标题/五点覆盖，"
                "重写时必须全部移除并换成前台未出现的相关词"
            ),
            "replacement": None,
        })
    return {
        "status": _status_from_issues(issues),
        "chars": byte_len,
        "limit": limit,
        "issues": _clean_issues(issues),
    }


def _check_list_field(items: list[str], spec: dict[str, Any], limit_key: str) -> dict[str, Any]:
    limit = spec["limits"][limit_key]
    if isinstance(items, str):
        return {
            "status": "fail",
            "chars": None,
            "limit": limit,
            "issues": [{
                "code": "type_error",
                "detail": "expected list, got str",
                "replacement": None,
            }],
        }
    if not isinstance(items, list):
        return {
            "status": "fail",
            "chars": None,
            "limit": limit,
            "issues": [{
                "code": "type_error",
                "detail": f"expected list, got {type(items).__name__}",
                "replacement": None,
            }],
        }
    all_issues: list[dict[str, Any]] = []
    char_counts: list[int] = []
    for idx, item in enumerate(items):
        if not isinstance(item, str):
            all_issues.append({
                "code": "type_error",
                "detail": f"[第{idx + 1}条] expected str, got {type(item).__name__}",
                "replacement": None,
            })
            char_counts.append(0)
            continue
        char_counts.append(len(item))
        item_issues: list[dict[str, Any]] = []
        if not item.strip():
            item_issues.append({
                "code": "empty_item",
                "detail": f"第{idx + 1}条为空",
                "replacement": None,
            })
        if limit is not None and len(item) > limit:
            item_issues.append({"code": "over_limit", "detail": f"第{idx + 1}条超长：{len(item)} > {limit}", "replacement": None})
        item_issues += _scan_banned(item, spec)
        item_issues += _brand_hits(item, spec)
        item_issues += _special_symbols(item)
        item_issues += _fact_context_issues(item, spec)
        for issue in item_issues:
            issue = dict(issue)
            issue["detail"] = f"[第{idx + 1}条] {issue['detail']}"
            all_issues.append(issue)
    return {
        "status": _status_from_issues(all_issues),
        "chars": char_counts,
        "limit": limit,
        "issues": _clean_issues(all_issues),
    }


def _check_bullets(bullets: list[str], spec: dict[str, Any]) -> dict[str, Any]:
    result = _check_list_field(bullets, spec, "bullet_each_max")
    if not isinstance(bullets, list):
        return result
    expected = spec.get("limits", {}).get("bullet_count")
    if expected is not None and len(bullets) != expected:
        result["issues"].append({
            "code": "bullet_count",
            "detail": f"五点条数不符：{len(bullets)} != {expected}",
            "replacement": None,
        })
        result["status"] = "fail"
    if not all(isinstance(item, str) for item in bullets):
        return result
    recommended_each = spec.get("authoring_recommendations", {}).get("bullet_each_max")
    if isinstance(recommended_each, int):
        for idx, item in enumerate(bullets):
            if len(item) > recommended_each:
                result["issues"].append({
                    "code": "recommended_length",
                    "detail": (
                        f"[第{idx + 1}条] 超过建议长度：{len(item)} > {recommended_each}；"
                        "不超过平台硬限制时无需为此重写"
                    ),
                    "replacement": None,
                })
    total_limit = spec.get("limits", {}).get("bullet_total_max")
    total_chars = sum(len(item) for item in bullets)
    result["total_chars"] = total_chars
    result["total_limit"] = total_limit
    if isinstance(total_limit, int) and total_chars > total_limit:
        result["issues"].append({
            "code": "over_limit",
            "detail": f"五点合计超长：{total_chars} > {total_limit}",
            "replacement": None,
        })
    result["status"] = _status_from_issues(result["issues"])
    return result


def _check_item_highlights(item_highlights: list[str], spec: dict[str, Any]) -> dict[str, Any]:
    result = _check_list_field(item_highlights, spec, "item_highlights_max")
    if not isinstance(item_highlights, list) or any(not isinstance(item, str) for item in item_highlights):
        return result
    combined = " ".join(item.strip() for item in item_highlights if item.strip())
    combined_chars = len(combined)
    limit = spec["limits"]["item_highlights_max"]
    result["chars"] = combined_chars
    if len(item_highlights) != 1:
        result["issues"].append({
            "code": "item_highlights_single_line",
            "detail": f"Item Highlights 必须是单行单字段，不得拆成 {len(item_highlights)} 条 Bullet Point",
            "replacement": None,
        })
        result["status"] = "fail"
    if any("\n" in item or "\r" in item for item in item_highlights):
        result["issues"].append({
            "code": "item_highlights_line_break",
            "detail": "Item Highlights 必须写在一行，不得换行",
            "replacement": None,
        })
        result["status"] = "fail"
    if any(re.match(r"^\s*(?:[-*•‣▪●]|\d+[.)])\s+", item) for item in item_highlights):
        result["issues"].append({
            "code": "item_highlights_bullet_format",
            "detail": "Item Highlights 不得使用 Bullet Point 符号或序号前缀",
            "replacement": None,
        })
        result["status"] = "fail"
    if limit is not None and combined_chars > limit:
        result["issues"] = [issue for issue in result["issues"] if issue.get("code") != "over_limit"]
        result["issues"].append({
            "code": "over_limit",
            "detail": f"Item Highlights 单行字段超长：{combined_chars} > {limit}",
            "replacement": None,
        })
        result["status"] = "fail"
    return result


def _check_subject_matter(subject_matter: list[str], spec: dict[str, Any]) -> dict[str, Any]:
    """后台主题词：可选字段。无平台统一上限时 limit=None，只做禁词/品牌/符号安检。"""
    return _check_list_field(subject_matter, spec, "subject_matter_max")


def _compute_front_dup(search_terms: str, title: str, bullets: list[str]) -> list[str]:
    front_tokens = set(_tokenize(title)) | set(_tokenize(" ".join(bullets or [])))
    dup = []
    seen = set()
    for token in _tokenize(search_terms):
        if token in front_tokens and token not in seen:
            seen.add(token)
            dup.append(token)
    return dup


def _compute_fact_faithfulness(draft: dict[str, Any], facts_text: str) -> dict[str, Any]:
    if not facts_text:
        return {"skipped": True}
    normalized_facts = _normalize_fact_match_text(facts_text)
    tokens: list[str] = []
    seen = set()
    for field in ("title", "description", "search_terms"):
        value = draft.get(field)
        if isinstance(value, str):
            for tok in _extract_unit_tokens(value):
                if tok not in seen:
                    seen.add(tok)
                    tokens.append(tok)
    for field in ("bullets", "item_highlights"):
        value = draft.get(field)
        if isinstance(value, list):
            for item in value:
                for tok in _extract_unit_tokens(str(item)):
                    if tok not in seen:
                        seen.add(tok)
                        tokens.append(tok)
    unsupported = [
        token for token in tokens
        if _normalize_fact_match_text(token) not in normalized_facts
    ]
    return {"unsupported_claims": unsupported}


def check_fields(draft: dict[str, Any], spec: dict[str, Any], facts_text: str = "") -> dict[str, Any]:
    """字段级安检汇总（无级联）。逐字段 try/except，单字段异常不阻断其它字段。"""
    fields: dict[str, Any] = {}

    title = draft.get("title")
    bullets = draft.get("bullets")
    description = draft.get("description")
    search_terms = draft.get("search_terms")
    item_highlights = draft.get("item_highlights")

    required_fields = ("title", "bullets", "description", "search_terms", "item_highlights")
    for field in required_fields:
        if draft.get(field) is None:
            fields[field] = {
                "status": "fail",
                "chars": None,
                "limit": None,
                "issues": [{
                    "code": "missing_field",
                    "detail": f"缺少必填字段：{field}",
                    "replacement": None,
                }],
            }

    if title is not None:
        try:
            fields["title"] = _check_title(title, spec)
        except Exception as exc:  # noqa: BLE001
            fields["title"] = {"status": "fail", "chars": None, "limit": None, "issues": [], "_error": str(exc)}

    if bullets is not None:
        try:
            fields["bullets"] = _check_bullets(bullets, spec)
        except Exception as exc:  # noqa: BLE001
            fields["bullets"] = {"status": "fail", "chars": None, "limit": None, "issues": [], "_error": str(exc)}

    if description is not None:
        try:
            fields["description"] = _check_description(description, spec)
        except Exception as exc:  # noqa: BLE001
            fields["description"] = {"status": "fail", "chars": None, "limit": None, "issues": [], "_error": str(exc)}

    front_dup_tokens: list[str] = []
    if search_terms is not None:
        try:
            front_dup_tokens = _compute_front_dup(search_terms, title or "", bullets or [])
            fields["search_terms"] = _check_search_terms(search_terms, spec, front_dup_tokens)
        except Exception as exc:  # noqa: BLE001
            fields["search_terms"] = {"status": "fail", "chars": None, "limit": None, "issues": [], "_error": str(exc)}

    if item_highlights is not None:
        try:
            fields["item_highlights"] = _check_item_highlights(item_highlights, spec)
        except Exception as exc:  # noqa: BLE001
            fields["item_highlights"] = {"status": "fail", "chars": None, "limit": None, "issues": [], "_error": str(exc)}

    # subject_matter 是可选字段：缺失不算 fail，给了就必须过禁词/品牌/符号安检
    subject_matter = draft.get("subject_matter")
    if subject_matter is not None:
        try:
            fields["subject_matter"] = _check_subject_matter(subject_matter, spec)
        except Exception as exc:  # noqa: BLE001
            fields["subject_matter"] = {"status": "fail", "chars": None, "limit": None, "issues": [], "_error": str(exc)}

    for field in ("title", "description", "search_terms"):
        if isinstance(draft.get(field), str) and not draft[field].strip():
            fields[field]["issues"].append({
                "code": "empty_field",
                "detail": f"必填字段为空：{field}",
                "replacement": None,
            })
            fields[field]["status"] = "fail"
    if isinstance(item_highlights, list) and not item_highlights:
        fields["item_highlights"]["issues"].append({
            "code": "empty_field",
            "detail": "必填字段为空：item_highlights",
            "replacement": None,
        })
        fields["item_highlights"]["status"] = "fail"

    try:
        core_keywords = spec.get("keywords", {}).get("core_to_title") or []
        title_hits, title_misses, _ = _core_keyword_analysis(title or "", core_keywords)
    except Exception:  # noqa: BLE001
        title_hits, title_misses = [], []

    try:
        scene_pain = list(spec.get("keywords", {}).get("scene_to_bullets") or []) + \
            list(spec.get("keywords", {}).get("pain_to_bullets") or [])
        bullets_text = " ".join(bullets or [])
        bullets_cf = bullets_text.casefold()
        covered = sum(1 for kw in scene_pain if kw and kw.casefold() in bullets_cf)
        bullets_scene_pain_pct = int(round(100 * covered / len(scene_pain))) if scene_pain else 100
    except Exception:  # noqa: BLE001
        bullets_scene_pain_pct = 0

    coverage = {
        "title_core_hit": title_hits,
        "title_core_miss": title_misses,
        "bullets_scene_pain_pct": bullets_scene_pain_pct,
        "search_terms_front_dup": front_dup_tokens,
        "search_terms_front_dup_threshold": _FRONT_DUP_FAIL_THRESHOLD,
    }

    try:
        fact_faithfulness = _compute_fact_faithfulness(draft, facts_text)
    except Exception as exc:  # noqa: BLE001
        fact_faithfulness = {"unsupported_claims": [], "_error": str(exc)}

    return {
        "kind": "listingCheckReport",
        "schema_version": 1,
        "fields": fields,
        "coverage": coverage,
        "fact_faithfulness": fact_faithfulness,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="validate_fields — 字段级安检（无级联）")
    parser.add_argument("--draft", required=True, help="listing-draft.json 绝对路径")
    parser.add_argument("--spec", required=True, help="spec.json 绝对路径")
    parser.add_argument("--facts", default=None, help="product-facts.md 绝对路径（可选）")
    parser.add_argument("--out", required=True, help="check-report.json 输出绝对路径")
    args = parser.parse_args()

    with open(args.draft, encoding="utf-8") as f:
        draft = json.load(f)
    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    facts_text = ""
    if args.facts and os.path.isfile(args.facts):
        with open(args.facts, encoding="utf-8") as f:
            facts_text = f.read()

    report = check_fields(draft, spec, facts_text=facts_text)

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Saved full response: {out_path}")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
