#!/usr/bin/env python3
"""Deterministically assemble the canonical Listing quality score.

The semantic evaluator supplies evidence-backed deductions. This script owns
dimension weights, N/A normalization, hard-gate caps, grades, and the derived
AI shopping-assistant readiness panel.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from normalize_listing_input import _metrics as _listing_metrics  # noqa: E402


DIMENSIONS = (
    ("compliance_risk", "平台合规与风险", 20),
    ("fact_trust", "商品事实与声明可信度", 15),
    ("semantic_discoverability", "搜索匹配与语义可发现性", 15),
    ("title_first_screen", "标题点击与首屏识别质量", 10),
    ("decision_support", "五点转化与购买决策支持", 15),
    ("ai_answerability", "信息完整度与 AI 导购可回答性", 10),
    ("localization", "语言质量与站点本地化", 8),
    ("competitive_safety", "差异化与竞争安全", 7),
)

# check-report（validate_fields.py 产物）→ 维度扣分/上限的机检映射。
# 语义评估者只提供「解释」，字符超限、禁用词、竞品品牌这类客观事实由机检直接定分，
# 不依赖评估者自己如实填写 deductions —— 这是「Highlights 超 125c 仍拿 95 分」的堵漏点。
_MECHANICAL_CAPS = {
    # (字段, issue code) -> (维度, cap)；对应 scoring-rubric.md「Hard Gates」表
    ("title", "over_limit"): ("title_first_screen", 59),
    ("item_highlights", "over_limit"): ("title_first_screen", 69),
    ("bullets", "over_limit"): ("decision_support", 69),
    ("bullets", "bullet_count"): ("decision_support", 69),
    ("description", "over_limit"): ("ai_answerability", 79),
}

# (字段, issue code) -> (维度, 每次扣分, 该 code 的扣分上限)
_MECHANICAL_DEDUCTIONS = {
    ("search_terms", "over_limit"): ("semantic_discoverability", 10, 10),
    ("search_terms", "front_dup"): ("semantic_discoverability", 2, 12),
    ("search_terms", "front_dup_excess"): ("semantic_discoverability", 8, 8),
    ("*", "special_symbol"): ("compliance_risk", 5, 15),
}

_CORE_FIELDS = ("title", "bullets", "description", "search_terms")

# 机检有 fail 字段时的总分上限：落到「需要优化后使用」档，不允许显示 A/B+ 级
_MECHANICAL_FAILURE_OVERALL_CAP = 79

GATE_RULES = {
    "compliance_high_risk": {"cap": 59, "human_review": True},
    "unsupported_critical_fact": {"cap": 69, "human_review": True},
    "competitor_brand_trademark": {"cap": 59, "human_review": True},
    "missing_core_fields": {"cap": 70, "human_review": False},
    "title_without_highlights": {"cap": 79, "human_review": False},
    "compliance_unavailable": {"cap": 79, "human_review": False},
    "product_facts_unavailable": {"cap": 79, "human_review": False},
}

# 合规维度权重 20，是全表最高的一项。只有以下机检产物之一存在时，合规分才算「有来源」：
# listing-compliance-scan 的 compliance_report、独立 compliance_scan 结果，或 validate_fields.py
# 的 check-report（覆盖 banned_term / competitor_brand / special_symbol）。
# 评估者自己读一遍文案数「perfect 出现几次」不是机检——那种分不允许按 20% 权重计入 overall。
_COMPLIANCE_UNVERIFIED_CAP = 79
_COMPLIANCE_UNVERIFIED_NOTE = "合规待终检：未接入合规扫描或字段机检，本项为待验证分，不构成平台最终审核结论"

_CHECK_REPORT_REQUIRED_FIELDS = {
    "title", "bullets", "description", "search_terms", "item_highlights",
}


def _valid_field_report(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("status") in {"pass", "warn", "fail"}
        and isinstance(value.get("issues"), list)
    )


def _valid_check_report(value: Any) -> bool:
    """只接受 validate_fields.py 的完整、可识别产物。"""
    if not isinstance(value, dict):
        return False
    if value.get("kind") != "listingCheckReport" or value.get("schema_version") != 1:
        return False
    fields = value.get("fields")
    return (
        isinstance(fields, dict)
        and _CHECK_REPORT_REQUIRED_FIELDS.issubset(fields)
        and all(_valid_field_report(fields[field]) for field in _CHECK_REPORT_REQUIRED_FIELDS)
    )


def _valid_compliance_scan(value: Any) -> bool:
    """识别独立合规扫描产物；空结果数组有效，但必须有可信来源与结果结构。"""
    if not isinstance(value, dict):
        return False
    source = str(value.get("source") or value.get("kind") or "").strip()
    if source not in {"listing-compliance-scan", "listingComplianceScan"}:
        return False
    return any(
        isinstance(value.get(key), list)
        for key in ("riskTerms", "violations", "findings", "results")
    )


def _has_compliance_machine_evidence(payload: dict[str, Any]) -> bool:
    """合规证据是否来自机检产物。只认真实产物，不认评估者的自我声明。"""
    if _valid_check_report(payload.get("check_report")):
        return True
    for key in ("compliance_report", "compliance_scan"):
        value = payload.get(key)
        if _valid_compliance_scan(value):
            return True
        if isinstance(value, list) and any(_valid_compliance_scan(item) for item in value):
            return True
    return False


def _field_issue_codes(field_report: Any) -> list[str]:
    if not isinstance(field_report, dict):
        return []
    return [
        str(issue.get("code") or "")
        for issue in (field_report.get("issues") or [])
        if isinstance(issue, dict)
    ]


def _coverage_pct(coverage: dict[str, Any]) -> int | None:
    hit = len(coverage.get("title_core_hit") or [])
    miss = len(coverage.get("title_core_miss") or [])
    total = hit + miss
    if not total:
        return None
    return int(round(100 * hit / total))


def derive_check_report_findings(report: Any) -> dict[str, Any]:
    """把 validate_fields.py 的 check-report 翻译成机检扣分、维度上限和 hard gate。

    只处理客观事实（字符/字节超限、条数、禁用词、竞品品牌、特殊符号、前后台重复、
    关键词覆盖率）；语义判断仍由评估者的 deductions 承担。
    """
    findings: dict[str, Any] = {
        "deductions": {}, "caps": {}, "gates": [], "field_failures": [],
    }
    if not isinstance(report, dict):
        return findings

    def add_deduction(dimension: str, points: int, reason: str, field: str, evidence: str) -> None:
        findings["deductions"].setdefault(dimension, []).append({
            "points": points, "reason": reason, "field": field,
            "evidence": evidence, "source": "check_report",
        })

    def add_cap(dimension: str, cap: int) -> None:
        current = findings["caps"].get(dimension)
        findings["caps"][dimension] = cap if current is None else min(current, cap)

    def add_gate(key: str, evidence: str) -> None:
        for gate in findings["gates"]:
            if gate["key"] == key:
                gate["evidence"].append(evidence)
                return
        findings["gates"].append({"key": key, "triggered": True, "evidence": [evidence]})

    fields = report.get("fields") if isinstance(report.get("fields"), dict) else {}
    for field_name, field_report in fields.items():
        if not isinstance(field_report, dict):
            continue
        if field_report.get("status") == "fail":
            findings["field_failures"].append(field_name)
        codes = _field_issue_codes(field_report)
        counts: dict[str, int] = {}
        for code in codes:
            counts[code] = counts.get(code, 0) + 1

        for code, count in counts.items():
            detail = f"{field_name}.{code} ×{count}"
            capped = _MECHANICAL_CAPS.get((field_name, code))
            if capped:
                dimension, cap = capped
                add_cap(dimension, cap)
                add_deduction(
                    dimension, 0,
                    f"机检：{field_name} 命中 {code}，该维度按 rubric 上限 {cap}",
                    field_name, detail,
                )
            rule = _MECHANICAL_DEDUCTIONS.get((field_name, code)) or _MECHANICAL_DEDUCTIONS.get(("*", code))
            if rule:
                dimension, per, limit = rule
                add_deduction(
                    dimension, min(per * count, limit),
                    f"机检：{field_name} 命中 {code} {count} 次", field_name, detail,
                )
            if code == "competitor_brand":
                add_gate("competitor_brand_trademark", detail)
            if code == "banned_term":
                if field_report.get("status") == "fail":
                    add_gate("compliance_high_risk", detail)
                else:
                    add_deduction(
                        "compliance_risk", min(8 * count, 24),
                        f"机检：{field_name} 命中受限词 {count} 次（非高危）", field_name, detail,
                    )
            if code in ("missing_field", "empty_field") and field_name in _CORE_FIELDS:
                add_gate("missing_core_fields", detail)
            if code in ("missing_field", "empty_field") and field_name == "item_highlights":
                add_gate("title_without_highlights", detail)

    coverage = report.get("coverage") if isinstance(report.get("coverage"), dict) else {}
    pct = _coverage_pct(coverage)
    if pct is not None:
        if pct < 20:
            add_cap("semantic_discoverability", 69)
        elif pct < 40:
            add_cap("semantic_discoverability", 79)
        elif pct < 60:
            add_cap("semantic_discoverability", 89)
        if pct < 60:
            add_deduction(
                "semantic_discoverability", 0,
                f"机检：标题核心词覆盖 {pct}%，按 rubric 锚点限制该维度上限",
                "title", f"title_core_hit={pct}%",
            )
    scene_pain = coverage.get("bullets_scene_pain_pct")
    if isinstance(scene_pain, (int, float)) and not isinstance(scene_pain, bool) and scene_pain < 60:
        add_deduction(
            "semantic_discoverability", 6,
            f"机检：五点场景/痛点词覆盖 {int(scene_pain)}% 低于目标 60%",
            "bullets", f"bullets_scene_pain_pct={int(scene_pain)}",
        )

    faithfulness = report.get("fact_faithfulness")
    if isinstance(faithfulness, dict):
        unsupported = [str(x) for x in (faithfulness.get("unsupported_claims") or [])]
        if unsupported:
            add_deduction(
                "fact_trust", min(6 * len(unsupported), 24),
                f"机检：{len(unsupported)} 处数字/单位声明在商品事实中找不到依据",
                "listing", "、".join(unsupported[:10]),
            )
            add_cap("fact_trust", 79)
    return findings


# 归一化 Listing 输入（normalize_listing_input.py 产物）→ 标题维度的机检上限。
# 堵的是「把一条 186 字符的线上标题按 | 切成 Title 74c + Item Highlights 109c，
# 于是 title>75c 门禁不触发」这条路径：字符数由脚本按来源字段重算，评估者说了不算。
_TITLE_OVER_LIMIT_CAP = 59
_HIGHLIGHTS_OVER_LIMIT_CAP = 69


def _merge_listing_input(payload: dict[str, Any]) -> dict[str, Any]:
    """按归一化后的字段实测值施加标题维度上限与 title_without_highlights 门禁。"""
    listing = payload.get("listing")
    if not isinstance(listing, dict) or not listing:
        return payload

    provenance = payload.get("field_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    highlights = listing.get("item_highlights") or []
    highlights_state = str((provenance.get("item_highlights") or {}).get("state") or "")
    if highlights and highlights_state != "verified":
        raise ValueError(
            "item_highlights 有值但 field_provenance 未标 verified："
            "Item Highlights 必须来自来源的独立字段，不能从标题拆分补齐"
        )

    metrics = payload.get("field_metrics")
    if not isinstance(metrics, dict) or "title_chars" not in metrics:
        metrics = _listing_metrics(listing, None)

    merged = dict(payload)
    merged["field_metrics"] = metrics

    caps = dict(merged.get("dimension_caps") or {})

    def tighten(dimension: str, cap: int) -> None:
        current = caps.get(dimension)
        caps[dimension] = cap if not isinstance(current, (int, float)) or isinstance(current, bool) else min(int(current), cap)

    if metrics.get("title_over_limit"):
        tighten("title_first_screen", _TITLE_OVER_LIMIT_CAP)
    if metrics.get("item_highlights_over_limit"):
        tighten("title_first_screen", _HIGHLIGHTS_OVER_LIMIT_CAP)
    merged["dimension_caps"] = caps

    # 标题超限又没有 Item Highlights 承接迁出信息时，按 rubric 落 overall_cap 79
    if metrics.get("title_over_limit") and not highlights:
        gates = list(merged.get("hard_gates") or [])
        evidence = (
            f"标题 {metrics.get('title_chars')} 字符，超过 {metrics.get('title_limit')} 上限，"
            "且来源没有独立的 Item Highlights 字段承接"
        )
        existing = next(
            (g for g in gates if isinstance(g, dict) and g.get("key") == "title_without_highlights"),
            None,
        )
        if isinstance(existing, dict):
            existing["triggered"] = True
            existing["evidence"] = list(existing.get("evidence") or []) + [evidence]
        else:
            gates.append({
                "key": "title_without_highlights", "triggered": True, "evidence": [evidence],
            })
        merged["hard_gates"] = gates

    return merged


def _merge_check_report(payload: dict[str, Any], report: Any) -> dict[str, Any]:
    """把机检结论并入 payload 的 dimensions / dimension_caps / hard_gates。

    机检结论优先：cap 取更严格值；机检扣分追加到对应维度（去重按 evidence）；
    仅有机检证据的维度会被创建为可评分维度，避免「不填该维度就免罚」。
    """
    findings = derive_check_report_findings(report)
    if not any((findings["deductions"], findings["caps"], findings["gates"], findings["field_failures"])):
        return payload

    merged = dict(payload)
    raw_dimensions = merged.get("dimensions") or {}
    if isinstance(raw_dimensions, list):
        raw_dimensions = {
            str(item.get("key") or ""): item
            for item in raw_dimensions
            if isinstance(item, dict) and item.get("key")
        }
    dimensions = {k: dict(v) if isinstance(v, dict) else v for k, v in raw_dimensions.items()}

    for dimension, deductions in findings["deductions"].items():
        entry = dimensions.get(dimension)
        if not isinstance(entry, dict):
            entry = {}
        # 机检证据本身就是可评分证据：该维度不再允许停留在 N/A
        entry.pop("unavailable", None)
        if entry.get("state") == "na":
            entry.pop("state")
        existing = list(entry.get("deductions") or [])
        # evidence 的正式输入允许字符串、列表或嵌套对象。用稳定 JSON 表示做去重，
        # 避免列表直接进入 set 时触发 ``TypeError: unhashable type: 'list'``。
        def identity(deduction: dict[str, Any]) -> tuple[str, str]:
            evidence = json.dumps(
                deduction.get("evidence"), ensure_ascii=False, sort_keys=True, default=str,
            )
            return str(deduction.get("reason") or ""), evidence

        seen = {identity(d) for d in existing if isinstance(d, dict)}
        for deduction in deductions:
            if identity(deduction) not in seen:
                existing.append(deduction)
        entry["deductions"] = existing
        evidence = list(entry.get("evidence") or [])
        entry["evidence"] = evidence + [
            f"check-report：{d['evidence']}" for d in deductions
            if f"check-report：{d['evidence']}" not in evidence
        ]
        dimensions[dimension] = entry
    merged["dimensions"] = dimensions

    caps = dict(merged.get("dimension_caps") or {})
    for dimension, cap in findings["caps"].items():
        current = caps.get(dimension)
        caps[dimension] = cap if not isinstance(current, (int, float)) else min(int(current), cap)
    merged["dimension_caps"] = caps

    gates = list(merged.get("hard_gates") or [])
    by_key = {
        str(g.get("key") or ""): g for g in gates if isinstance(g, dict)
    }
    for gate in findings["gates"]:
        existing = by_key.get(gate["key"])
        if isinstance(existing, dict):
            existing["triggered"] = True
            existing["evidence"] = list(existing.get("evidence") or []) + gate["evidence"]
        else:
            gates.append(gate)
    merged["hard_gates"] = gates
    merged["_mechanical_field_failures"] = findings["field_failures"]
    return merged


def _deduction_points(deductions: Any, key: str) -> int:
    total = 0
    for index, item in enumerate(deductions if isinstance(deductions, list) else []):
        if not isinstance(item, dict):
            raise ValueError(f"{key}.deductions[{index}] must be an object")
        points = item.get("points")
        if not isinstance(points, (int, float)) or isinstance(points, bool) or points < 0:
            raise ValueError(f"{key}.deductions[{index}].points must be >= 0")
        total += int(round(points))
    return total


def _state(score: int | None) -> str:
    if score is None:
        return "na"
    if score >= 80:
        return "ok"
    if score >= 70:
        return "warn"
    return "bad"


def _readiness_state(score: int | None) -> str:
    if score is None:
        return "na"
    if score >= 80:
        return "pass"
    if score >= 70:
        return "weak"
    return "miss"


def _grade(overall: int | None) -> tuple[str, str]:
    if overall is None:
        return "—", "数据不足 · 无法评分"
    if overall >= 90:
        return "A", "准备度优秀"
    if overall >= 80:
        return "B+", "可使用 · 建议优化"
    if overall >= 70:
        return "B", "需要优化后使用"
    if overall >= 60:
        return "C", "关键字段需要重写"
    return "D", "不可直接使用"


def _normalize_gates(raw_gates: Any) -> tuple[list[dict[str, Any]], int | None, bool]:
    gates: list[dict[str, Any]] = []
    overall_cap: int | None = None
    requires_human_review = False
    for index, raw in enumerate(raw_gates if isinstance(raw_gates, list) else []):
        if not isinstance(raw, dict):
            raise ValueError(f"hard_gates[{index}] must be an object")
        key = str(raw.get("key") or "")
        if key not in GATE_RULES:
            raise ValueError(f"unknown hard gate: {key}")
        triggered = bool(raw.get("triggered"))
        rule = GATE_RULES[key]
        cap = rule["cap"] if triggered else None
        if cap is not None:
            overall_cap = cap if overall_cap is None else min(overall_cap, cap)
            requires_human_review = requires_human_review or bool(rule["human_review"])
        gates.append({
            "key": key,
            "status": "fail" if triggered else "pass",
            "cap": cap,
            "evidence": list(raw.get("evidence") or []),
        })
    return gates, overall_cap, requires_human_review


def _recommendation_readiness(
    items_by_key: dict[str, dict[str, Any]], hard_gates: list[dict[str, Any]]
) -> str:
    if any(gate["status"] == "fail" and gate["key"] in {
        "compliance_high_risk", "unsupported_critical_fact", "competitor_brand_trademark"
    } for gate in hard_gates):
        return "miss"
    component_keys = (
        "compliance_risk", "fact_trust", "semantic_discoverability",
        "decision_support", "ai_answerability",
    )
    states = [_readiness_state(items_by_key[key]["score"]) for key in component_keys]
    if states.count("miss") >= 2:
        return "miss"
    if "miss" in states or "weak" in states or "na" in states:
        return "weak"
    return "pass"


def score_quality(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _merge_listing_input(payload)
    check_report = payload.get("check_report")
    if check_report is not None:
        payload = _merge_check_report(payload, check_report)
    field_failures = list(payload.get("_mechanical_field_failures") or [])
    raw_dimensions = payload.get("dimensions") or {}
    if isinstance(raw_dimensions, list):
        raw_dimensions = {
            str(item.get("key") or ""): item
            for item in raw_dimensions
            if isinstance(item, dict) and item.get("key")
        }
    if not isinstance(raw_dimensions, dict):
        raise ValueError("dimensions must be an object or array")
    known_dimension_keys = {key for key, _name, _weight in DIMENSIONS}
    unknown_dimensions = set(raw_dimensions) - known_dimension_keys
    if unknown_dimensions:
        raise ValueError(f"unknown dimensions: {sorted(unknown_dimensions)}")

    dimension_caps = payload.get("dimension_caps") or {}
    if not isinstance(dimension_caps, dict):
        raise ValueError("dimension_caps must be an object")
    unknown_caps = set(dimension_caps) - known_dimension_keys
    if unknown_caps:
        raise ValueError(f"unknown dimension caps: {sorted(unknown_caps)}")

    # 机检没跑 → 合规分只能是待验证分：维度封顶 79，并在下面强制 compliance_unavailable 门禁。
    compliance_verified = _has_compliance_machine_evidence(payload)
    if not compliance_verified:
        existing_cap = dimension_caps.get("compliance_risk")
        if not isinstance(existing_cap, (int, float)) or isinstance(existing_cap, bool):
            existing_cap = _COMPLIANCE_UNVERIFIED_CAP
        dimension_caps = {
            **dimension_caps,
            "compliance_risk": min(_COMPLIANCE_UNVERIFIED_CAP, int(existing_cap)),
        }

    items: list[dict[str, Any]] = []
    items_by_key: dict[str, dict[str, Any]] = {}
    weighted_sum = 0
    active_weight = 0

    for key, name, weight in DIMENSIONS:
        raw = raw_dimensions.get(key) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"dimension {key} must be an object")
        unavailable = raw.get("state") == "na" or bool(raw.get("unavailable")) or not raw
        deductions = list(raw.get("deductions") or [])
        score = None if unavailable else max(0, 100 - _deduction_points(deductions, key))
        if score is not None and key in dimension_caps:
            cap = dimension_caps[key]
            if not isinstance(cap, (int, float)) or isinstance(cap, bool) or not 0 <= cap <= 100:
                raise ValueError(f"dimension cap for {key} must be 0..100")
            score = min(score, int(cap))
        item = {
            "key": key,
            "name": name,
            "score": score,
            "weight": weight,
            "state": _state(score),
            "note": str(raw.get("note") or ("数据未提供" if score is None else "")),
            "evidence": list(raw.get("evidence") or []),
            "deductions": deductions,
            "recommendation": str(raw.get("recommendation") or ""),
        }
        items.append(item)
        items_by_key[key] = item
        if score is not None:
            weighted_sum += score * weight
            active_weight += weight

    raw_gates = list(payload.get("hard_gates") or [])
    gate_keys = {
        str(gate.get("key") or "") for gate in raw_gates if isinstance(gate, dict)
    }
    if "compliance_unavailable" not in gate_keys and (
        items_by_key["compliance_risk"]["score"] is None or not compliance_verified
    ):
        raw_gates.append({
            "key": "compliance_unavailable", "triggered": True,
            "evidence": ["平台合规证据未提供"] if items_by_key["compliance_risk"]["score"] is None
            else ["未提供合规扫描结果或字段机检报告，合规分按待验证处理"],
        })
    if items_by_key["fact_trust"]["score"] is None and "product_facts_unavailable" not in gate_keys:
        raw_gates.append({
            "key": "product_facts_unavailable", "triggered": True,
            "evidence": ["商品事实证据未提供"],
        })
    if not compliance_verified and items_by_key["compliance_risk"]["score"] is not None:
        items_by_key["compliance_risk"]["note"] = _COMPLIANCE_UNVERIFIED_NOTE

    hard_gates, overall_cap, requires_human_review = _normalize_gates(raw_gates)
    if field_failures:
        # 字段级安检没过的 Listing 不能拿「可直接使用」的总分。单个维度被压低不够——
        # 该维度权重只有 10 时，Highlights 超限仍能算出 97 分 A 级，与 pass=false 自相矛盾。
        overall_cap = _MECHANICAL_FAILURE_OVERALL_CAP if overall_cap is None else min(
            overall_cap, _MECHANICAL_FAILURE_OVERALL_CAP
        )
    overall = int(round(weighted_sum / active_weight)) if active_weight else None
    if overall is not None and overall_cap is not None:
        overall = min(overall, overall_cap)
    grade, grade_text = _grade(overall)

    ai_context = payload.get("ai_context") if isinstance(payload.get("ai_context"), dict) else {}
    external_probe = ai_context.get("external_probe")
    if not isinstance(external_probe, dict):
        external_probe = {"probed": False}
    elif not external_probe.get("probed"):
        external_probe = {**external_probe, "probed": False}

    ai_readiness = {
        "kind": "listingAiReadiness",
        "schema_version": 1,
        "discoverability": _readiness_state(items_by_key["semantic_discoverability"]["score"]),
        "answerability": _readiness_state(items_by_key["ai_answerability"]["score"]),
        "recommendation_readiness": _recommendation_readiness(items_by_key, hard_gates),
        "four_pillars": dict(ai_context.get("four_pillars") or {}),
        "questions": list(ai_context.get("questions") or []),
        "question_coverage": ai_context.get("question_coverage") or {
            "answered": None, "total": None, "state": "na"
        },
        "external_probe": external_probe,
        "fix_suggestions": list(ai_context.get("fix_suggestions") or []),
    }
    insufficient = overall is None or any(item["score"] is None for item in items)
    panel = {
        "overall": overall,
        "grade": grade,
        "gradeText": grade_text,
        "basis": "Listing Conversion Readiness · canonical rubric v2",
        "insufficientData": insufficient,
        "hardGates": hard_gates,
        "items": items,
        "topIssues": list(payload.get("top_issues") or []),
        "quickFixes": list(payload.get("quick_fixes") or []),
        "dataConfidence": dict(payload.get("data_confidence") or {}),
        "mechanicalFieldFailures": field_failures,
        "fieldMetrics": dict(payload.get("field_metrics") or {}),
        "fieldProvenance": dict(payload.get("field_provenance") or {}),
    }
    # 机检有 fail 字段时不允许判 pass —— 字段级安检没过的 Listing 不是「可直接使用」
    passed = overall is not None and overall >= 80 and not field_failures and not any(
        gate["status"] == "fail" for gate in hard_gates
    )
    return {
        "kind": "listingQualityScore",
        "schema_version": 2,
        "scorePanel": panel,
        "aiReadiness": ai_readiness,
        "rewrite_brief": dict(payload.get("rewrite_brief") or {}),
        "pass": passed,
        "requiresHumanReview": requires_human_review,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble canonical Listing quality score")
    parser.add_argument("input", help="Evidence-backed deductions JSON")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument(
        "--check-report", default=None,
        help="validate_fields.py 产出的 check-report.json；提供后机检结论强制并入评分",
    )
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    if args.check_report:
        with open(args.check_report, encoding="utf-8") as f:
            payload["check_report"] = json.load(f)
    result = score_quality(payload)
    out = os.path.abspath(args.out)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved full response: {out}")


if __name__ == "__main__":
    main()
