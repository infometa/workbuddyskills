#!/usr/bin/env python3
"""listing-copy-suite-writer 的公共字段安检入口。

读 stdin 的 listing bundle，用 listing-core 的 `validate_fields.check_fields` 做**一次
进程内**安检，落一份 compliance artifact，按 blocked / human_review / passed 返回
2 / 3 / 0。脚本从不截断、改写、删除或替换任何 Listing 正文。

本脚本在单进程内校验 5 个文本字段，避免额外子进程与中间产物。门禁映射见下表。

| 原 keyword_checker 门禁      | 迁移后                                              |
|-----------------------------|-----------------------------------------------------|
| trademark HIGH（竞品品牌）    | validate_fields `competitor_brand`（fail）            |
| banned_issues（用户禁用词）   | spec.user_banned_terms → banned_term（fail）           |
| restricted block             | validate_fields `_scan_banned` severity=block（fail） |
| restricted review            | validate_fields severity=review（warn）→ 退出码 3     |
| title/highlights/desc 长度    | validate_fields `over_limit`                          |
| search_terms 字节            | validate_fields `over_limit`                          |
| search_terms_dedup 零容忍     | 见 `_BLOCKING_CODES`：本脚本对 front_dup 零容忍        |

注意：`validate_fields` 自身对 front_dup 用阈值 3（超过才 fail），那是 listing-core 交互
链路的策略——写完可以就地局部重写。批量交付没有这个回环，所以本脚本沿用原门禁的零容忍，
两套策略是有意分开的，不要合并。
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any


# 列表字段（bullets / item_highlights）的 issue detail 前缀，如 "[第3条] "
_LIST_ITEM_PREFIX = re.compile(r"^\[第\d+条\]\s*")


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


SKILLS_DIR = Path(__file__).resolve().parents[2]
CORE_SCRIPTS = SKILLS_DIR / "listing-core" / "scripts"

if not CORE_SCRIPTS.is_dir():
    print(f"listing-core scripts not found: {CORE_SCRIPTS}", file=sys.stderr)
    raise SystemExit(2)

sys.path.insert(0, str(CORE_SCRIPTS))

import validate_fields as _vf  # noqa: E402
from build_spec import assemble_spec  # noqa: E402
from linkfox_paths import resolve_data_path  # noqa: E402
from listing_spec import field_enabled, load_spec, resolve_limit  # noqa: E402
from validate_fields import check_fields  # noqa: E402


# 命中的 issue code → 面向调用方的门禁名，拼进 blocked 报错，便于上游按门禁归因
_GATE_NAMES = {
    "competitor_brand": "竞品品牌零容忍",
    "banned_term": "受限内容/避讳词",
    "over_limit": "字段长度上限",
    "front_dup": "后台词前台重复",
    "front_dup_excess": "后台词前台重复",
    "bullet_count": "五点条数",
    "special_symbol": "特殊符号",
    "missing_field": "必填字段缺失",
    "empty_field": "必填字段为空",
    "empty_item": "列表项为空",
}


# 任一命中即判 blocked（退出码 2）。其余 issue 走 human_review（退出码 3）。
_BLOCKING_CODES = {
    "over_limit",
    "missing_field",
    "empty_field",
    "empty_item",
    "type_error",
    "bullet_count",
    "competitor_brand",
    "special_symbol",
    # 批量交付对后台词与前台重复零容忍，与原 keyword_checker 一致
    "front_dup",
    "front_dup_excess",
}


class PipelineError(RuntimeError):
    def __init__(self, stage: str, message: str, *, details: str = "", exit_code: int = 2):
        super().__init__(message)
        self.stage = stage
        self.details = details
        self.exit_code = exit_code


def _read_payload() -> tuple[dict[str, Any], str | None]:
    """读 payload，并解析用户规格路径（--spec / payload.spec_path）。"""
    argv = sys.argv[1:]
    spec_path: str | None = None
    remaining: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--spec" and i + 1 < len(argv):
            spec_path = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--spec="):
            spec_path = arg.split("=", 1)[1]
            i += 1
            continue
        remaining.append(arg)
        i += 1
    raw = remaining[0] if remaining else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError("input", f"输入不是合法 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PipelineError("input", "输入顶层必须是 JSON 对象")
    if not spec_path:
        candidate = str(payload.get("spec_path") or "").strip()
        spec_path = candidate or None
    if spec_path and not os.path.isfile(spec_path):
        raise PipelineError("input", f"spec 文件不存在: {spec_path}")
    return payload, spec_path


def _brands(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [item.strip() for item in value.replace(";", ",").split(",")]
    elif isinstance(value, list):
        candidates = [str(item).strip() for item in value]
    else:
        candidates = []
    return list(dict.fromkeys(item for item in candidates if item))


def _brands_from_product_detail(path: str) -> list[str]:
    if not path or not os.path.isfile(path):
        return []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key.casefold() in {"brand", "brandname", "brand_name"} and isinstance(value, str):
                    if value.strip():
                        found.append(value.strip())
                elif isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return list(dict.fromkeys(found))


def _blocking_banned_details(draft: dict[str, Any], spec: dict[str, Any]) -> set[tuple[str, str]]:
    """找出哪些 `banned_term` 命中是 block 级（必须 exit 2），哪些只是 review（exit 3）。

    `check_fields` 的报告经过 `_clean_issues` 洗掉了内部的 `_severity`，而 `banned_term`
    的强度是逐条命中决定的（受限词库的 block/review，以及 spec.user_banned_terms 一律
    fail）。这里复用 validate_fields 自己的 `_scan_banned` 重算一次，按 (字段, detail)
    精确配对——detail 字符串两边由同一个函数生成，可以逐字匹配。

    不这么做的话，受限内容的 block 词会和 review 词一样只判 human_review，
    从而放松正式交付门禁。
    """
    blocking: set[tuple[str, str]] = set()
    for field_name, value in draft.items():
        texts = value if isinstance(value, list) else [value]
        for text in texts:
            if not isinstance(text, str) or not text:
                continue
            for issue in _vf._scan_banned(text, spec):
                if issue.get("_severity") == "fail":
                    blocking.add((field_name, issue["detail"]))
    return blocking


def _draft_from_bundle(data: dict[str, Any]) -> dict[str, Any]:
    highlights = data.get("item_highlights")
    if isinstance(highlights, list):
        highlight_list = [str(item) for item in highlights if str(item).strip()]
    else:
        highlight_list = [str(highlights)] if str(highlights or "").strip() else []
    draft: dict[str, Any] = {
        "title": str(data.get("title") or ""),
        "bullets": data.get("bullets"),
        "description": str(data.get("description") or ""),
        "search_terms": str(data.get("search_terms") or ""),
        "item_highlights": highlight_list,
    }
    subject_matter = data.get("subject_matter")
    if subject_matter is not None:
        draft["subject_matter"] = subject_matter
    return draft


def _flatten_issues(
    report: dict[str, Any],
    exempt_fields: set[str] | None = None,
    banned_block: set[tuple[str, str]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """把 check-report 的逐字段 issue 摊平成 blocking / review 两组。

    `exempt_fields` 用于本次调用不适用的字段（如 `is_media` 或 spec 关闭了
    item_highlights）：check_fields 把它当必填，但调用方的门禁说它可以缺席。
    """
    exempt = exempt_fields or set()
    banned_block = banned_block or set()
    blocking: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    for field_name, detail in (report.get("fields") or {}).items():
        if not isinstance(detail, dict) or field_name in exempt:
            continue
        if detail.get("_error"):
            blocking.append({
                "type": "validator_error",
                "field": field_name,
                "detail": str(detail["_error"]),
            })
        for issue in detail.get("issues") or []:
            item = {
                "type": issue.get("code"),
                "field": field_name,
                "detail": issue.get("detail"),
                "replacement": issue.get("replacement"),
            }
            code = issue.get("code")
            if code == "banned_term":
                # 列表字段的 detail 带 `[第N条] ` 前缀，比对前去掉
                bare = _LIST_ITEM_PREFIX.sub("", str(issue.get("detail") or ""), count=1)
                is_blocking = (field_name, bare) in banned_block
            else:
                is_blocking = code in _BLOCKING_CODES
            if is_blocking:
                blocking.append(item)
            else:
                review.append(item)
    return blocking, review


def _save_compliance(report: dict[str, Any], blocking: list[dict[str, Any]], review: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    field_status = {
        name: detail.get("status")
        for name, detail in (report.get("fields") or {}).items()
        if isinstance(detail, dict)
    }
    doc = {
        "compliance_report": {
            "passed": not blocking and not review,
            "status": "blocked" if blocking else ("human_review" if review else "passed"),
            "requires_human_review": bool(review) and not blocking,
            "issues": [*blocking, *review],
            "summary": {
                "overall_pass": not blocking and not review,
                "blocking_count": len(blocking),
                "review_count": len(review),
                "fields": field_status,
            },
            "checks_executed": [
                "competitor_and_known_trademarks",
                "user_banned_terms",
                "restricted_content_versioned_library",
                "field_lengths",
                "search_terms_frontend_overlap",
                "fact_traceability",
            ],
            "validator": "listing-core/scripts/validate_fields.py",
        },
        "raw_check": report,
    }
    serialized = json.dumps(doc, ensure_ascii=False, indent=2)
    out_path = os.path.abspath(resolve_data_path("linkfox-listing-compliance-check", time.time()))
    Path(out_path).write_text(serialized, encoding="utf-8")
    print(f"Compliance artifact: {out_path}")
    return out_path, doc


def main() -> int:
    try:
        data, spec_path = _read_payload()

        user_spec = load_spec(spec_path) if spec_path else None
        highlights_required = not data.get("is_media")
        if user_spec is not None and not field_enabled(user_spec, "item_highlights"):
            highlights_required = False
        expected_bullets = resolve_limit(user_spec, "bullets", "count", 5)[0] or 5

        required_text = ("title", "description", "search_terms")
        if highlights_required:
            required_text += ("item_highlights",)
        missing = [name for name in required_text if not str(data.get(name) or "").strip()]
        if missing:
            raise PipelineError("input", "缺少必填字段: " + ", ".join(missing))
        bullets = data.get("bullets")
        if not isinstance(bullets, list) or len(bullets) != expected_bullets:
            raise PipelineError("input", f"bullets 必须是恰好 {expected_bullets} 条的数组")

        competitor_brands = _brands(data.get("competitor_brands") or data.get("competitor_brand"))
        assets_path = str(data.get("product_detail_path") or data.get("assets_path") or "").strip()
        if assets_path and not os.path.isfile(assets_path):
            raise PipelineError("input", f"product_detail_path 不存在: {assets_path}")
        competitor_brands.extend(
            brand for brand in _brands_from_product_detail(assets_path) if brand not in competitor_brands
        )

        workflow_mode = str(data.get("workflow_mode") or "benchmark").strip().casefold()
        used_competitors = data.get("competitors_used") or data.get("competitor_asins")
        if (workflow_mode == "benchmark" or bool(used_competitors)) and not competitor_brands:
            raise PipelineError(
                "compliance_check",
                "已使用竞品证据但缺少竞品品牌数据，无法完成竞品品牌零容忍检查",
            )

        matrix_path = str(data.get("matrix_path") or "").strip()
        if matrix_path and not os.path.isfile(matrix_path):
            raise PipelineError("input", f"matrix_path 不存在: {matrix_path}")

        own_brand = str(data.get("brand") or "").strip()
        owned = [own_brand] if own_brand else []
        # 自有品牌同时出现在竞品列表时以自有为准，避免 assemble_spec 的互斥校验直接抛错
        competitor_brands = [b for b in competitor_brands if b.casefold() not in {o.casefold() for o in owned}]

        spec_mode = workflow_mode if workflow_mode in {"benchmark", "rewrite", "create"} else "benchmark"
        # 调用方禁用词交给 spec.user_banned_terms（validate_fields 按 banned_term 判 fail），
        # 不再由本脚本单独扫一遍——两份实现会漂移
        spec = assemble_spec(
            spec_mode,
            owned,
            competitor_brands,
            {},
            [],
            user_spec=user_spec,
            marketplace=str(data.get("marketplace") or "US"),
            category=str(data.get("category") or ""),
            banned_terms=_brands(data.get("banned_terms")),
        )

        draft = _draft_from_bundle(data)
        report = check_fields(draft, spec)

        exempt: set[str] = set()
        if not highlights_required and not draft["item_highlights"]:
            exempt.add("item_highlights")
        blocking, review = _flatten_issues(report, exempt, _blocking_banned_details(draft, spec))

        compliance_path, compliance_doc = _save_compliance(report, blocking, review)
        compliance = compliance_doc["compliance_report"]

        if compliance["status"] == "blocked":
            gates = list(dict.fromkeys(
                _GATE_NAMES[item["type"]] for item in blocking if item.get("type") in _GATE_NAMES
            ))
            gate_text = "、".join(gates) if gates else "字段安检"
            raise PipelineError(
                "compliance_gate",
                f"合规门禁阻断（{gate_text}）：必须只重写命中字段后重新检查，原文未被脚本修改",
                details=json.dumps(
                    {"compliance_path": compliance_path, "issues": compliance["issues"]},
                    ensure_ascii=False,
                    indent=2,
                ),
                exit_code=2,
            )
        if compliance["status"] == "human_review":
            raise PipelineError(
                "compliance_gate",
                "检测到必须人工复核的受限内容，未生成可交付报告",
                details=json.dumps(
                    {"compliance_path": compliance_path, "issues": compliance["issues"]},
                    ensure_ascii=False,
                    indent=2,
                ),
                exit_code=3,
            )

        result = {
            "status": "success",
            "content_mutated_by_script": False,
            "compliance_path": compliance_path,
        }
        if matrix_path:
            result["matrix_path"] = matrix_path
        print(f"Saved full response: {compliance_path} ({os.path.getsize(compliance_path)} bytes)")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except PipelineError as exc:
        error = {"status": "error", "stage": exc.stage, "message": str(exc)}
        if exc.details:
            error["details"] = exc.details
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
