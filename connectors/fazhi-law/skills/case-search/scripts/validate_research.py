#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


SCHEMA_VERSION = "1.0"
REQUIRED_PLATFORMS = {"case_search", "case_browser", "legal_article_search", "law_content_visit"}
ALLOWED_PLATFORMS = REQUIRED_PLATFORMS | {"webpage_search", "webpage_visit"}
CATEGORIES = {"contract", "project", "financial", "transaction", "other"}
OUTCOME_CLASSES = {"支持", "部分支持", "不支持", "程序性处理", "未明确认定"}
DIRECTIONS = {"support", "partial", "oppose"}
PROHIBITED_TEXT = ("三、本案分析", "律师建议", "风险提示", "办案策略", "执行摘要", "法律依据专章")


def text_len(value: str) -> int:
    return len(re.sub(r"\s+", "", value or ""))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_object(value, path, errors):
    if not isinstance(value, dict):
        errors.append(f"{path} 必须是对象")
        return {}
    return value


def require_list(value, path, errors, minimum=None, maximum=None):
    if not isinstance(value, list):
        errors.append(f"{path} 必须是数组")
        return []
    if minimum is not None and len(value) < minimum:
        errors.append(f"{path} 至少包含 {minimum} 项")
    if maximum is not None and len(value) > maximum:
        errors.append(f"{path} 最多包含 {maximum} 项")
    return value


def require_string(obj, key, path, errors, allow_null=False):
    value = obj.get(key)
    if allow_null and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key} 必须是非空字符串")
        return ""
    return value.strip()


def check_date(value, path, errors):
    try:
        date.fromisoformat(value)
    except Exception:
        errors.append(f"{path} 必须使用 YYYY-MM-DD")


def check_url(value, path, expected_segment, errors):
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "www.fazhi.law" or expected_segment not in parsed.path:
        errors.append(f"{path} 必须是法智对应详情页 HTTPS 链接")


def check_unknown_keys(obj, allowed, path, errors):
    for key in sorted(set(obj) - set(allowed)):
        errors.append(f"{path} 含未定义字段：{key}")


def validate_data(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["根节点必须是 JSON 对象"]
    check_unknown_keys(data, {"matter", "search", "legal_rules", "cases"}, "$", errors)

    matter = require_object(data.get("matter"), "matter", errors)
    matter_keys = {"title", "case_number", "category", "parties", "legal_relationship", "facts", "claims", "issues"}
    check_unknown_keys(matter, matter_keys, "matter", errors)
    require_string(matter, "title", "matter", errors)
    require_string(matter, "case_number", "matter", errors, allow_null=True)
    category = require_string(matter, "category", "matter", errors)
    if category and category not in CATEGORIES:
        errors.append("matter.category 不属于受控分类")
    for field, minimum, maximum in (("parties", 2, None), ("facts", 1, None), ("claims", 1, None), ("issues", 1, 3)):
        values = require_list(matter.get(field), f"matter.{field}", errors, minimum, maximum)
        for idx, value in enumerate(values):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"matter.{field}[{idx}] 必须是非空字符串")
            if field == "issues" and isinstance(value, str) and text_len(value) > 45:
                errors.append(f"matter.issues[{idx}] 超过 45 字")
    require_string(matter, "legal_relationship", "matter", errors)

    search = require_object(data.get("search"), "search", errors)
    search_keys = {"search_date", "submitter", "submission_date", "platforms", "keywords", "date_from", "date_to", "time_scope", "area_scope", "screening_conditions", "candidate_count", "insufficient_reason", "result_conclusion"}
    check_unknown_keys(search, search_keys, "search", errors)
    for key in ("search_date", "submitter", "submission_date", "date_from", "date_to", "time_scope", "area_scope", "result_conclusion"):
        require_string(search, key, "search", errors)
    if isinstance(search.get("search_date"), str):
        check_date(search["search_date"], "search.search_date", errors)
    if isinstance(search.get("submission_date"), str):
        check_date(search["submission_date"], "search.submission_date", errors)
    date_from = date_to = None
    if isinstance(search.get("date_from"), str):
        check_date(search["date_from"], "search.date_from", errors)
        try:
            date_from = date.fromisoformat(search["date_from"])
        except ValueError:
            pass
    if isinstance(search.get("date_to"), str):
        check_date(search["date_to"], "search.date_to", errors)
        try:
            date_to = date.fromisoformat(search["date_to"])
        except ValueError:
            pass
    if date_from and date_to and date_from > date_to:
        errors.append("search.date_from 不得晚于 search.date_to")
    platforms = require_list(search.get("platforms"), "search.platforms", errors, 2)
    if any(p not in ALLOWED_PLATFORMS for p in platforms):
        errors.append("search.platforms 含未知工具")
    if not REQUIRED_PLATFORMS.issubset(set(platforms)):
        errors.append("search.platforms 必须包含四个核心案例/法条工具")
    if len(platforms) != len(set(platforms)):
        errors.append("search.platforms 不得重复")
    keywords = require_list(search.get("keywords"), "search.keywords", errors, 2, 12)
    if len(keywords) != len(set(keywords)):
        errors.append("search.keywords 不得重复")
    for idx, value in enumerate(keywords):
        if not isinstance(value, str) or text_len(value) < 2:
            errors.append(f"search.keywords[{idx}] 至少 2 字")
    require_list(search.get("screening_conditions"), "search.screening_conditions", errors, 2, 6)
    candidate_count = search.get("candidate_count")
    if not isinstance(candidate_count, int) or isinstance(candidate_count, bool) or candidate_count < 0:
        errors.append("search.candidate_count 必须是非负整数")
        candidate_count = 0
    conclusion = search.get("result_conclusion", "")
    if isinstance(conclusion, str) and not 30 <= text_len(conclusion) <= 800:
        errors.append("search.result_conclusion 必须为 30–800 字")

    legal_rules = require_list(data.get("legal_rules"), "legal_rules", errors, 1)
    seen_laws = set()
    for idx, item in enumerate(legal_rules):
        path = f"legal_rules[{idx}]"
        item = require_object(item, path, errors)
        allowed = {"law_id", "law_name", "article", "status", "url", "verified"}
        check_unknown_keys(item, allowed, path, errors)
        law_id = require_string(item, "law_id", path, errors)
        law_name = require_string(item, "law_name", path, errors)
        article = require_string(item, "article", path, errors)
        status = require_string(item, "status", path, errors)
        url = require_string(item, "url", path, errors)
        if status and status != "现行有效":
            errors.append(f"{path}.status 必须为现行有效")
        if item.get("verified") is not True:
            errors.append(f"{path}.verified 必须为 true")
        if url:
            check_url(url, f"{path}.url", "/law-saas/lawDetail/", errors)
            if law_id and law_id not in url:
                errors.append(f"{path}.url 未包含 law_id")
        key = (law_name, article)
        if key in seen_laws:
            errors.append(f"{path} 与其他法规条目重复")
        seen_laws.add(key)

    cases = require_list(data.get("cases"), "cases", errors, 0, 8)
    if candidate_count < len(cases):
        errors.append("search.candidate_count 不得小于纳入案例数")
    insufficient = search.get("insufficient_reason")
    if len(cases) < 5:
        if not isinstance(insufficient, str) or not insufficient.strip():
            errors.append("纳入案例少于 5 件时必须填写 search.insufficient_reason")
    else:
        if not 10 <= candidate_count <= 15:
            errors.append("纳入 5–8 件时，search.candidate_count 必须为 10–15")
        if insufficient not in (None, ""):
            errors.append("纳入案例不少于 5 件时 insufficient_reason 应为 null")

    seen_case_nos, seen_ids = set(), set()
    case_fields = {"lawsuit_id", "title", "case_no", "court", "judge_date", "case_url", "object_name", "issues", "holdings", "outcome_class", "outcome_detail", "direction", "summary_fact", "summary_reasoning", "full_text_verified", "source"}
    for idx, item in enumerate(cases):
        path = f"cases[{idx}]"
        item = require_object(item, path, errors)
        check_unknown_keys(item, case_fields, path, errors)
        values = {key: require_string(item, key, path, errors) for key in ("lawsuit_id", "title", "case_no", "court", "judge_date", "case_url", "object_name", "outcome_class", "outcome_detail", "direction", "summary_fact", "summary_reasoning", "source")}
        if values["judge_date"]:
            check_date(values["judge_date"], f"{path}.judge_date", errors)
            try:
                judge_date = date.fromisoformat(values["judge_date"])
                if date_from and judge_date < date_from or date_to and judge_date > date_to:
                    errors.append(f"{path}.judge_date 超出 search.date_from 至 search.date_to 的检索范围")
            except ValueError:
                pass
        if values["case_url"]:
            check_url(values["case_url"], f"{path}.case_url", "/law-saas/caseDetail/", errors)
            if values["lawsuit_id"] and values["lawsuit_id"] not in values["case_url"]:
                errors.append(f"{path}.case_url 未包含 lawsuit_id")
        if values["case_no"] in seen_case_nos:
            errors.append(f"{path}.case_no 重复")
        if values["lawsuit_id"] in seen_ids:
            errors.append(f"{path}.lawsuit_id 重复")
        seen_case_nos.add(values["case_no"])
        seen_ids.add(values["lawsuit_id"])
        issues = require_list(item.get("issues"), f"{path}.issues", errors, 1, 3)
        holdings = require_list(item.get("holdings"), f"{path}.holdings", errors, 2, 4)
        for pos, value in enumerate(issues):
            if not isinstance(value, str) or not value.strip() or text_len(value) > 45:
                errors.append(f"{path}.issues[{pos}] 必须为 1–45 字")
        total_holdings = 0
        for pos, value in enumerate(holdings):
            if not isinstance(value, str) or not value.strip() or text_len(value) > 90:
                errors.append(f"{path}.holdings[{pos}] 必须为 1–90 字")
            if isinstance(value, str):
                total_holdings += text_len(value)
        if total_holdings > 280:
            errors.append(f"{path}.holdings 合计超过 280 字")
        if values["outcome_class"] not in OUTCOME_CLASSES:
            errors.append(f"{path}.outcome_class 不属于受控词")
        if text_len(values["outcome_class"] + values["outcome_detail"]) > 45:
            errors.append(f"{path} 裁判结论超过 45 字")
        if values["direction"] not in DIRECTIONS:
            errors.append(f"{path}.direction 不属于受控方向")
        mapping = {"support": {"支持"}, "partial": {"部分支持", "程序性处理", "未明确认定"}, "oppose": {"不支持"}}
        if values["direction"] in mapping and values["outcome_class"] not in mapping[values["direction"]]:
            errors.append(f"{path} direction 与 outcome_class 不一致")
        if item.get("full_text_verified") is not True:
            errors.append(f"{path}.full_text_verified 必须为 true")
        if values["source"] != "fazhi":
            errors.append(f"{path}.source 必须为 fazhi")
        summary_length = text_len(values["summary_fact"]) + text_len(values["summary_reasoning"])
        if not 300 <= summary_length <= 500:
            errors.append(f"{path} 两段摘要合计必须为 300–500 字，当前 {summary_length} 字")
        if text_len(values["summary_fact"]) < 100 or text_len(values["summary_reasoning"]) < 100:
            errors.append(f"{path} 两段摘要各自不得少于 100 字")

    corpus = [str(search.get("result_conclusion", ""))]
    for item in cases:
        if isinstance(item, dict):
            corpus.extend([str(item.get("summary_fact", "")), str(item.get("summary_reasoning", ""))])
    joined = "\n".join(corpus)
    for phrase in PROHIBITED_TEXT:
        if phrase in joined:
            errors.append(f"研究数据含禁止内容：{phrase}")
    return errors


def marker_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.name + ".validated.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate case-search-report research JSON")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"校验失败：无法读取 JSON：{exc}", file=sys.stderr)
        return 2
    errors = validate_data(data)
    if errors:
        print("校验失败：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    marker = {
        "schema_version": SCHEMA_VERSION,
        "source_file": args.input.name,
        "sha256": sha256_file(args.input),
        "case_count": len(data["cases"]),
    }
    target = marker_path(args.input)
    target.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"校验通过：{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
