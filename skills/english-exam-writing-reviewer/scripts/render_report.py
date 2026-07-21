#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 english-exam-writing-reviewer 产出的 review JSON 渲染为中文 HTML 报告。

v1.2 起支持考研英语：
    - exam_level ∈ {CET4, CET6, Postgrad1A, Postgrad1B, Postgrad2A, Postgrad2B}
    - 考研场景新增 3 个专有区块：
        ① 考研 5 维诊断（任务完成/语法词汇/语言准确/衔接连贯/格式语域）
        ② Directions 原句照搬检测（A 节专有）
        ③ 词汇升档建议（vocabulary_upgrades，四层词汇库驱动）
    - 分数/档次同时兼容 CET（15 分×5 档）与 考研（10/15/20 分×5 档，允许 0.5 增量）

v1.6.1 新增 4 个可选展示区块（由 JSON 字段驱动，无则自动隐藏）：
    ① Calibration 状态横幅（calibration_status + calibration_note）
       —— 对 low_frequency_theoretical / out_of_calibration 降置信度警示
    ② Postgrad1B 三段落诊断（paragraph_diagnosis.para1/para2/para3）
       —— 描述/阐释/评论递进 + is_dialectical 辩证性检查
    ③ letter_category 专属检查（letter_category + category_specific_check）
       —— 投诉/回复/建议等 10 种信件的语域与要素检查
    ④ chart_subtype_specific（Postgrad2B / CET chart 题）
       —— 数据覆盖率、multi_bar 两组并列、趋势描述准确性


Usage:
    python render_report.py review.json
    python render_report.py review.json --template ../assets/report-template.html \
                                        --output ./review-reports/report.html

依赖：仅标准库（无外部依赖）。
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SEVERITY_LABELS = {
    "critical": "致命错误",
    "warning": "待优化",
    "tip": "提升点",
}

TYPE_LABELS = {
    "mechanical": "机械问题",
    "grammar": "语法问题",
    "lexical": "词汇问题",
    "discourse": "结构问题",
    "format":            "结构问题",
    "proverb_subtype":    "内容问题",
    "pronoun_reference":  "语法问题",
    "coherence":          "句式问题",
    "theme_deviation":    "结构问题",
    "vocabulary":         "词汇问题",
    "grammar":            "语法问题",
    "sentence_structure": "句式问题",
    "logic":              "结构问题",
    "content":            "内容问题",
}

# CET 隐含维度（4 维）
CET_DIMENSIONS = {
    "relevance": "切题度",
    "clarity": "表达清晰度",
    "coherence": "连贯性",
    "language_accuracy": "语言准确度",
}

# 考研 5 维（官方显式维度，非隐含）
POSTGRAD_DIMENSIONS = {
    "task_completion": "任务完成度",
    "grammar_lexis":   "语法结构与词汇",
    "accuracy":        "语言准确性",
    "cohesion":        "衔接与连贯",
    "format_register": "格式与语域",
}

VOCAB_TIER_LABELS = {
    "low":      "低阶",
    "mid":      "中阶",
    "high":     "高阶",
    "academic": "学术",
}

# 考试级别中文标签（用户面展示，内部 ID 仍为英文）
EXAM_LEVEL_LABELS = {
    "CET4":       "CET-4（大学英语四级）",
    "CET6":       "CET-6（大学英语六级）",
    "POSTGRAD1A": "考研英语一 A 节（应用文）",
    "POSTGRAD1B": "考研英语一 B 节（短文）",
    "POSTGRAD2A": "考研英语二 A 节（应用文）",
    "POSTGRAD2B": "考研英语二 B 节（短文）",
}

# task_subtype 中文标签（v1.6.0+ 题型子类，v1.7.3 起面向用户汉化）
TASK_SUBTYPE_LABELS = {
    # CET 共 7 种
    "prompt_essay":            "命题议论文",
    "proverb":                 "名言警句",
    "chart":                   "图表作文",
    "cartoon":                 "漫画作文",
    "news_report":             "新闻报道",
    "letter":                  "书信",
    "report":                  "调查报告",
    # 考研 A 节
    "notice":                  "通知",
    "announcement":            "告示",
    "memorandum":              "备忘录",
    "summary":                 "摘要",
    # 考研英一 B 节
    "cartoon_standard":        "漫画论述文",
    "descriptive_theoretical": "描写文（低频理论）",
    "narrative_theoretical":   "记叙文（低频理论）",
    "expository_theoretical":  "说明文（低频理论）",
    # 考研英二 B 节 / CET chart 共用
    "bar_chart":               "柱状图",
    "pie_chart":               "饼图",
    "table":                   "表格",
    "line_graph":              "折线图",
    "multi_bar":               "多组柱状图",
    "multi_pie":               "多组饼图",
    "mixed":                   "混合图表",
}


def format_reviewed_at(raw: str) -> str:
    """把 ISO-8601 时间戳（如 2026-04-23T12:00:00Z）格式化为中文本地时间。

    - 支持 `Z` 结尾（UTC）与 `+08:00` 等显式偏移
    - 无法解析时原样返回
    - 输出示例：`2026-04-23 20:00（北京时间）` / `2026-04-23 12:00 UTC`
    """
    if not raw:
        return ""
    s = raw.strip()
    try:
        iso = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        local = dt.astimezone()
        tz_label = "北京时间" if local.utcoffset() and local.utcoffset().total_seconds() == 8 * 3600 \
            else local.strftime("%Z") or "本地时间"
        return f"{local.strftime('%Y-%m-%d %H:%M')}（{tz_label}）"
    except (ValueError, TypeError):
        return s


def format_exam_level(exam_level: str) -> str:
    """把内部 ID（CET4 / POSTGRAD1A…）映射为用户面中文标签，未命中则回退原值。"""
    if not exam_level:
        return ""
    return EXAM_LEVEL_LABELS.get(exam_level.upper(), exam_level)


def format_task_subtype(task_subtype: str) -> str:
    """把 task_subtype 内部 ID 映射为中文标签（同时保留英文 ID 供调试可见）。"""
    if not task_subtype:
        return ""
    label = TASK_SUBTYPE_LABELS.get(task_subtype)
    return f"{label}（{task_subtype}）" if label else task_subtype

# CET 档次名（15 分制）
CET_BAND_NAMES = {
    14: "14 分档（第五档）",
    11: "11 分档（第四档）",
    8:  "8 分档（第三档）",
    5:  "5 分档（第二档）",
    2:  "2 分档（第一档）",
    0:  "0 分",
}

# 考研 5 档名（统一编号 1-5，具体分数随 10/15/20 总分而变）
POSTGRAD_BAND_NAMES = {
    5: "第五档（优秀）",
    4: "第四档（良好）",
    3: "第三档（中等）",
    2: "第二档（不足）",
    1: "第一档（较差）",
    0: "0 分（无效）",
}

# 各级别 band -> (raw_min, raw_max) 合法区间
BAND_RANGES = {
    "CET": {
        14: (13, 15), 11: (10, 12), 8: (7, 9),
        5: (4, 6),    2: (1, 3),    0: (0, 0),
    },
    "POSTGRAD_10": {  # A 节：满分 10 分
        5: (9, 10), 4: (7, 8), 3: (5, 6), 2: (3, 4), 1: (1, 2), 0: (0, 0),
    },
    "POSTGRAD_15": {  # 英二 B 节：满分 15 分
        5: (13, 15), 4: (10, 12), 3: (7, 9), 2: (4, 6), 1: (1, 3), 0: (0, 0),
    },
    "POSTGRAD_20": {  # 英一 B 节：满分 20 分
        5: (17, 20), 4: (13, 16), 3: (9, 12), 2: (5, 8), 1: (1, 4), 0: (0, 0),
    },
}


def is_postgrad(exam_level: str) -> bool:
    return exam_level.upper().startswith("POSTGRAD")


def get_score_max(exam_level: str) -> int:
    """返回该考试的满分。"""
    el = exam_level.upper()
    if el == "POSTGRAD1B":
        return 20
    if el == "POSTGRAD2B":
        return 15
    if el in ("POSTGRAD1A", "POSTGRAD2A"):
        return 10
    return 15  # CET4 / CET6


def get_band_ranges(exam_level: str) -> dict:
    sm = get_score_max(exam_level)
    if not is_postgrad(exam_level):
        return BAND_RANGES["CET"]
    return BAND_RANGES[f"POSTGRAD_{sm}"]


def get_band_names(exam_level: str) -> dict:
    if is_postgrad(exam_level):
        return POSTGRAD_BAND_NAMES
    return CET_BAND_NAMES


def validate(data: dict) -> None:
    """按 references/output-schema.md 校验关键字段（支持 CET + 考研）。"""
    band = data.get("band")
    raw = data.get("raw_score")
    final = data.get("final_score")
    meta = data.get("meta", {})
    exam_level = meta.get("exam_level", data.get("exam_level", "CET4"))

    legal_bands = set(get_band_ranges(exam_level).keys())
    if band not in legal_bands:
        raise ValueError(f"band 非法：{band}（{exam_level} 合法 band ∈ {sorted(legal_bands)}）")

    score_max = get_score_max(exam_level)
    if not (isinstance(raw, (int, float)) and 0 <= raw <= score_max):
        raise ValueError(f"raw_score 非法：{raw}（须为 0-{score_max} 数值）")

    # 考研允许 0.5 增量；CET 只允许整数
    if is_postgrad(exam_level):
        if not (isinstance(final, (int, float)) and 0 <= final <= raw + 0.01):
            raise ValueError(f"final_score 非法：{final}（须 ≤ raw_score={raw}）")
    else:
        if not (isinstance(final, int) and 0 <= final <= raw):
            raise ValueError(f"final_score 非法：{final}（须为整数且 ≤ raw_score）")

    lo, hi = get_band_ranges(exam_level)[band]
    if not (lo <= raw <= hi):
        raise ValueError(
            f"band={band} 与 raw_score={raw} 在 {exam_level} 下不一致，应在 {lo}-{hi}"
        )

    if not data.get("rationale_trace"):
        raise ValueError("rationale_trace 不可为空")

    # 考研 A 节必含 directions_copy_check；考研场景建议含 format_register 诊断
    task_subtype = meta.get("task_subtype", data.get("task_subtype", ""))
    if is_postgrad(exam_level) and task_subtype in ("letter", "notice", "announcement", "memorandum"):
        dcc = data.get("directions_copy_check")
        if dcc is None:
            raise ValueError("考研 A 节必须包含 directions_copy_check（即使 overall_risk=none）")


def render_dimensions(dims: dict, exam_level: str) -> str:
    """CET -> 4 隐含维度；考研 -> 5 官方显式维度。"""
    label_map = POSTGRAD_DIMENSIONS if is_postgrad(exam_level) else CET_DIMENSIONS
    rows = []
    for key, label in label_map.items():
        if key not in dims:
            continue
        val = dims[key]
        if isinstance(val, dict):
            # 嵌套对象（如 format_register: {format, register, signature_compliance}）
            parts = [f"<strong>{html.escape(str(k))}</strong>：{html.escape(str(v))}"
                     for k, v in val.items() if v]
            text = " · ".join(parts)
        else:
            text = html.escape(str(val))
        rows.append(
            f'        <div class="dim-row">'
            f'<span class="dim-name">{label}</span>'
            f'<span class="dim-text">{text}</span></div>'
        )
    if not rows:
        return '        <p class="empty">无诊断数据</p>'
    return "\n".join(rows)


SEV_EMOJI = {
    "critical": "🔴 严重",
    "warning":  "⚠️ 中等",
    "minor":    "🔵 轻微",
    "tip":      "🔵 轻微",
}


# 建议前缀推断：根据 suggestion 内容特征自动判断操作类型
def _infer_sug_prefix(sug: str, issue_type: str) -> str:
    """根据建议内容和问题类型推断操作前缀（改写 / 增加 / 删除 / 替换）。"""
    if not sug:
        return ""
    s = sug.strip()
    # 词汇替换：有 → 符号或 / 分隔的候选词
    if "→" in s or (" / " in s and len(s) < 80):
        return "替换："
    # 增加内容：建议以 In addition / Moreover / Furthermore / 增加 开头
    add_kws = ("In addition", "Moreover", "Furthermore", "Additionally",
               "Also,", "增加", "补充", "加入")
    if any(s.startswith(k) for k in add_kws):
        return "增加："
    # 删除：建议明确说删除/去掉
    del_kws = ("删除", "去掉", "移除", "Remove", "Delete")
    if any(k in s for k in del_kws):
        return "删除："
    # 默认：改写
    return "改写："


def render_issues(issues: list[dict], vocab_upgrades: list[dict] | None = None) -> str:
    """将 issues + vocabulary_upgrades 合并渲染为统一的问题清单表格。

    表格列：# / 位置 / 类型 / 严重度 / 原文 / 问题说明 / 建议
    词汇升级条目以"词汇问题"类型追加到表格末尾。
    """
    # 构建行列表：每行 = (loc, type_label, sev, original, reason_html, sug_html)
    rows: list[tuple[str, str, str, str, str, str]] = []

    for it in (issues or []):
        # 词汇层次「全文」汇总行跳过，词汇问题已由 vocabulary_upgrades 逐条展示
        if it.get("type") == "vocabulary" and str(it.get("location", "")).strip() in ("全文", "全篇", ""):
            continue
        loc = str(it.get("location", ""))
        typ = TYPE_LABELS.get(it.get("type", ""), it.get("type", ""))
        sev = it.get("severity", "tip")
        orig = str(it.get("original", ""))
        # JSON 实际字段名为 description，兼容 reason
        reason = str(it.get("description") or it.get("reason", ""))
        sug = it.get("suggestion", "")
        reason_html = html.escape(reason)
        if sug:
            prefix = _infer_sug_prefix(str(sug), it.get("type", ""))
            sug_html = f"<span style='color:var(--brand);'>{html.escape(prefix)}</span> <code style='font-size:12px;'>{html.escape(str(sug))}</code>"
        else:
            sug_html = '<span style="color:var(--muted);">—</span>'
        rows.append((loc, typ, sev, orig, reason_html, sug_html))

    # 词汇升级条目追加为"词汇问题"行
    for u in (vocab_upgrades or []):
        loc = str(u.get("location", ""))
        orig = str(u.get("original", ""))
        sug_list = u.get("suggestion", [])
        if isinstance(sug_list, list):
            sug_str = " / ".join(str(s) for s in sug_list)
        else:
            sug_str = str(sug_list)
        t_from = VOCAB_TIER_LABELS.get(u.get("tier_from", ""), u.get("tier_from", ""))
        t_to = VOCAB_TIER_LABELS.get(u.get("tier_to", ""), u.get("tier_to", ""))
        note = u.get("note", "")
        if note:
            reason_html = html.escape(str(note))
        else:
            reason_html = html.escape(f"词汇层次偏低（{t_from}），使用过于基础，影响档次上升，建议替换为{t_to}表达。")
        sug_html = (
            f"<span style='color:var(--brand);'>替换：</span> "
            f"<code style='font-size:12px;'>{html.escape(sug_str)}</code>"
            f"<span style='color:var(--muted);font-size:12px;'>（{html.escape(t_from)} → <strong>{html.escape(t_to)}</strong>）</span>"
        )
        rows.append((loc, "词汇问题", "tip", orig, reason_html, sug_html))

    if not rows:
        return '        <p class="empty">本文未发现问题 🎉</p>'

    # 渲染表格
    out = [
        '        <div style="overflow-x:auto;">',
        '        <table class="vocab-table" style="font-size:14px;min-width:700px;">',
        '          <thead><tr>'
        '<th style="width:32px;text-align:center;">#</th>'
        '<th style="width:60px;">位置</th>'
        '<th style="width:90px;">问题类型</th>'
        '<th style="width:68px;">严重度</th>'
        '<th style="width:150px;">原文</th>'
        '<th style="width:200px;">问题说明</th>'
        '<th>建议</th>'
        '</tr></thead>',
        '          <tbody>',
    ]
    for idx, (loc, typ, sev, orig, reason_html, sug_html) in enumerate(rows, 1):
        sev_label = SEV_EMOJI.get(sev, sev)
        tag_cls = f"tag-{sev}"
        out.append(
            f'          <tr>'
            f'<td style="text-align:center;color:var(--muted);">{idx}</td>'
            f'<td style="white-space:nowrap;">{html.escape(loc)}</td>'
            f'<td><span class="tag {tag_cls}" style="white-space:nowrap;">'
            f'{html.escape(typ)}</span></td>'
            f'<td style="white-space:nowrap;">{sev_label}</td>'
            f'<td><code style="font-size:12px;word-break:break-all;">'
            f'{html.escape(orig)}</code></td>'
            f'<td style="font-size:13px;line-height:1.7;">{reason_html}</td>'
            f'<td style="font-size:13px;line-height:1.7;">{sug_html}</td>'
            f'</tr>'
        )
    out.extend(['          </tbody>', '        </table>', '        </div>'])
    return "\n".join(out)

def render_deductions(deductions: list[dict]) -> str:
    if not deductions:
        return (
            '        <p style="color:#166534;background:#dcfce7;padding:10px 14px;'
            'border-radius:8px;margin:0;">'
            '✅ 本次批改已检查以下扣分项，均未触发：'
            '<ul style="margin:8px 0 0;padding-left:20px;font-size:13px;">'
            '<li>字数不足（有效字数低于最低要求）</li>'
            '<li>考研 A 节 Directions 原句照搬（连续 ≥8 词）</li>'
            '<li>作文与题目完全无关</li>'
            '</ul></p>'
        )
    out = ['        <ul class="deduction-list">']
    for d in deductions:
        out.append(
            f'          <li>'
            f'<strong>[{html.escape(d.get("type",""))}] -{d.get("amount",0)} 分</strong> '
            f'— {html.escape(d.get("reason",""))}'
            f'</li>'
        )
    out.append("        </ul>")
    return "\n".join(out)


def render_upgrade(up: dict) -> str:
    if not up:
        return ""
    actions = up.get("actions", [])
    out = [
        f'        <p>当前 <strong>{up.get("current")} 档</strong> → 目标 '
        f'<strong>{up.get("target")} 档</strong></p>',
        '        <ol class="upgrade-list">'
    ]
    for a in actions:
        out.append(f'          <li>{html.escape(str(a))}</li>')
    out.append("        </ol>")
    return "\n".join(out)


def render_rationale(trace: list[dict]) -> str:
    out = ['        <ul class="rationale">']
    for t in trace:
        step = html.escape(t.get("step", ""))
        claim = html.escape(t.get("claim", ""))
        evidence = t.get("evidence", [])
        ref = html.escape(t.get("rubric_ref", ""))
        ev_html = "".join(f"<li>{html.escape(str(e))}</li>" for e in evidence)
        out.append(
            f'          <li><strong>{claim}</strong>'
            f'<ul class="ev">{ev_html}</ul>'
            f'<div class="ref">依据：{ref}</div></li>'
        )
    out.append("        </ul>")
    return "\n".join(out)


def render_directions_copy(dcc: Any) -> str:
    """v1.2 新增：考研 A 节 Directions 原句照搬检测展示。"""
    if dcc is None or dcc == {}:
        return '        <p class="empty">本试题未触发 Directions 检测（非 A 节或不适用）</p>'
    if not dcc.get("applicable", True):
        return '        <p class="empty">该考试/题型不适用 Directions 照搬检测</p>'

    risk = dcc.get("overall_risk", "none")
    risk_label = {
        "none": "✅ 无风险",
        "tip":  "⚠️ 轻微（关键词级复用）",
        "warning": "⚠️⚠️ 中等（需关注）",
        "critical": "❌ 严重（触发扣分）",
    }.get(risk, risk)
    risk_class = f"dcc-risk-{risk}"

    out = [f'        <div class="dcc-risk {risk_class}"><strong>总体风险：</strong>{risk_label}</div>']
    segs = dcc.get("copied_segments", [])
    if not segs:
        out.append('        <p class="empty">未检测到连续 8 词以上的重合片段</p>'
                   if risk == "none" else '        <p>未列出具体片段。</p>')
    else:
        out.append('        <ul class="dcc-list">')
        for s in segs:
            words = s.get("consecutive_words", "?")
            sev = s.get("severity", "tip")
            deduction = s.get("deduction_risk", "none")
            note = html.escape(s.get("note", ""))
            essay_text = html.escape(s.get("essay_text", ""))
            matched = html.escape(s.get("matched_directions", ""))
            out.append(
                f'          <li class="dcc-item dcc-sev-{sev}">'
                f'<div class="dcc-head"><span class="tag tag-{sev}">{words} 词连续</span>'
                f' 扣分风险：<strong>{html.escape(str(deduction))}</strong></div>'
                f'<div class="dcc-body">作文原文：<code>{essay_text}</code></div>'
                f'<div class="dcc-body">Directions：<code>{matched}</code></div>'
                f'<div class="dcc-note">{note}</div>'
                f'</li>'
            )
        out.append("        </ul>")

    if dcc.get("deduction_amount"):
        out.append(
            f'        <p class="dcc-deduction">已扣分：<strong>-{dcc["deduction_amount"]} 分</strong>'
            f'（已计入下方"扣分明细"与最终分数）</p>'
        )
    return "\n".join(out)


# ========== v1.6.1 新增渲染函数 ==========

CALIBRATION_STATUS_META = {
    "normal":                    ("normal", "✅", "标准校准", "已对齐校准集；评分置信度高"),
    "low_frequency_theoretical": ("warn",   "⚠️", "理论题型（真题低频）",
                                  "本题型属大纲显性要求但真题出现频率极低，校准样本稀疏；"
                                  "评分置信度降低，以qualitative 反馈为主，档次可能存在 ±1 档浮动"),
    "out_of_calibration":        ("danger", "❌", "校准集外",
                                  "本题型未覆盖在当前校准集中；评分仅供参考，建议人工复核"),
}


def svg_progress_bar(pct: int, label: str = "",
                     color_ok: str = "#22c55e",
                     color_warn: str = "#f59e0b",
                     color_danger: str = "#ef4444",
                     width: int = 260, height: int = 18) -> str:
    """v1.7.0：通用 SVG 进度条（覆盖率/齐备度可视化）。

    - pct ∈ [0, 100]，自动按 ≥95 / ≥80 / <80 三段染色。
    - 无外部依赖，纯 inline SVG。
    """
    pct = max(0, min(100, int(pct)))
    if pct >= 95:
        color = color_ok
    elif pct >= 80:
        color = color_warn
    else:
        color = color_danger
    fill_w = int(width * pct / 100)
    lbl = html.escape(label or f"{pct}%")
    return (
        f'<svg class="svg-progress" width="{width}" height="{height}" role="img" aria-label="{lbl}">'
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="4" fill="#e5e7eb"/>'
        f'<rect x="0" y="0" width="{fill_w}" height="{height}" rx="4" fill="{color}"/>'
        f'<text x="{width // 2}" y="{height // 2 + 4}" text-anchor="middle" '
        f'font-size="12" fill="#111827" font-weight="600">{lbl}</text>'
        f'</svg>'
    )


def svg_radar_3axis(values: list[float], labels: list[str],
                    size: int = 180) -> str:
    """v1.7.0：三轴雷达图（段落诊断 descriptive / interpretive / analytical）。

    - values[i] ∈ [0, 1]（good=1.0 / fair=0.6 / poor=0.2）
    - 三顶点分别在 90°/210°/330°（正三角）
    """
    import math
    cx = cy = size // 2
    R = int(size * 0.38)
    # 三个轴角（度 → 弧度）
    angles_deg = [-90, 30, 150]
    axis_pts, data_pts = [], []
    for ang_deg, v in zip(angles_deg, values):
        ang = math.radians(ang_deg)
        x_outer = cx + R * math.cos(ang)
        y_outer = cy + R * math.sin(ang)
        axis_pts.append((x_outer, y_outer))
        x_d = cx + R * v * math.cos(ang)
        y_d = cy + R * v * math.sin(ang)
        data_pts.append((x_d, y_d))
    parts = [f'<svg class="svg-radar" width="{size}" height="{size}" viewBox="0 0 {size} {size}">']
    # 三圈网格（50% / 75% / 100%）
    for r_ratio in (0.5, 0.75, 1.0):
        poly = " ".join(
            f"{cx + R * r_ratio * math.cos(math.radians(a)):.1f},"
            f"{cy + R * r_ratio * math.sin(math.radians(a)):.1f}"
            for a in angles_deg
        )
        parts.append(
            f'<polygon points="{poly}" fill="none" stroke="#e5e7eb" stroke-width="1"/>'
        )
    # 轴线
    for x2, y2 in axis_pts:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="#d1d5db" stroke-width="1"/>')
    # 数据多边形
    data_poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)
    parts.append(
        f'<polygon points="{data_poly}" fill="#3b82f655" stroke="#3b82f6" stroke-width="2"/>'
    )
    for x, y in data_pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#3b82f6"/>')
    # 轴标签
    label_offset = 14
    for (ang_deg, lbl) in zip(angles_deg, labels):
        ang = math.radians(ang_deg)
        lx = cx + (R + label_offset) * math.cos(ang)
        ly = cy + (R + label_offset) * math.sin(ang)
        anchor = "middle"
        if ang_deg == 30:
            anchor = "start"
        elif ang_deg == 150:
            anchor = "end"
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'font-size="11" fill="#374151">{html.escape(lbl)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def render_calibration_banner(status: str | None, note: str | None) -> str:
    """v1.6.1：顶部 calibration_status 横幅。正常时返回空字符串（模板会隐藏容器）。"""
    if not status or status == "normal":
        return ""
    meta = CALIBRATION_STATUS_META.get(status)
    if not meta:
        return (
            f'        <div class="calib-banner calib-warn">'
            f'<strong>⚠️ 未知 calibration_status：</strong>{html.escape(status)}</div>'
        )
    cls, icon, title, default_note = meta
    note_text = html.escape(note) if note else default_note
    return (
        f'        <div class="calib-banner calib-{cls}">'
        f'<div class="calib-title">{icon} {title}</div>'
        f'<div class="calib-note">{note_text}</div></div>'
    )


def render_paragraph_diagnosis(diag: dict | None) -> str:
    """v1.6.1：Postgrad1B cartoon_standard 三段落递进诊断。

    期望 schema：
        diag = {
            "is_dialectical": bool,
            "dialectical_note": str,
            "para1": {"role": "descriptive", "quality": "good|fair|poor",
                       "comment": "...", "evidence": "..."},
            "para2": {"role": "interpretive", ...},
            "para3": {"role": "analytical",   ...},
        }
    """
    if not diag:
        return ""
    role_labels = {
        "descriptive":  "段一 · 描述图画（Descriptive）",
        "interpretive": "段二 · 阐释深意（Interpretive）",
        "analytical":   "段三 · 评论/对策（Analytical）",
    }
    quality_meta = {
        "good": ("excellent", "✅ 良好"),
        "fair": ("warn",      "⚠️ 一般"),
        "poor": ("danger",    "❌ 不足"),
    }
    out = []

    # v1.7.0：先画三段雷达图（descriptive / interpretive / analytical）
    quality_to_value = {"good": 1.0, "fair": 0.6, "poor": 0.25}
    radar_values, radar_labels = [], []
    for key in ("para1", "para2", "para3"):
        p = diag.get(key) or {}
        q = p.get("quality", "fair")
        radar_values.append(quality_to_value.get(q, 0.6))
        role = p.get("role", key)
        radar_labels.append({
            "descriptive":  "描述",
            "interpretive": "阐释",
            "analytical":   "评论",
        }.get(role, role))
    out.append('        <div class="para-radar-wrap">')
    out.append('          ' + svg_radar_3axis(radar_values, radar_labels))
    out.append('          <div class="radar-legend">'
               '<span class="lg-good">■ 良好（100%）</span> '
               '<span class="lg-fair">■ 一般（60%）</span> '
               '<span class="lg-poor">■ 不足（25%）</span>'
               '</div>')
    out.append('        </div>')

    out.append('        <ol class="para-diag-list">')
    for key in ("para1", "para2", "para3"):
        p = diag.get(key) or {}
        role = p.get("role", key)
        label = role_labels.get(role, role)
        quality = p.get("quality", "fair")
        q_cls, q_text = quality_meta.get(quality, ("warn", quality))
        comment = html.escape(str(p.get("comment", "")))
        evidence = html.escape(str(p.get("evidence", "")))
        out.append(
            f'          <li class="para-item para-{q_cls}">'
            f'<div class="para-head"><strong>{label}</strong>'
            f'<span class="para-q para-q-{q_cls}">{q_text}</span></div>'
            f'<div class="para-comment">{comment}</div>'
            + (f'<div class="para-evidence">证据：<code>{evidence}</code></div>' if evidence else "")
            + '</li>'
        )
    out.append("        </ol>")

    # 辩证性检查（2022+ 英一 B 节硬约束）
    is_dialectical = diag.get("is_dialectical")
    if is_dialectical is not None:
        d_note = html.escape(str(diag.get("dialectical_note", "")))
        if is_dialectical:
            out.append(
                '        <div class="dialectical-ok">'
                f'✅ 具备辩证性（让步 / 反驳视角）{"：" + d_note if d_note else ""}</div>'
            )
        else:
            out.append(
                '        <div class="dialectical-miss">'
                f'❌ 缺少辩证性（未见让步或反驳）{"：" + d_note if d_note else ""}'
                '<br><small>2022+ 英一 B 节鼓励 discursive 写作，纯正向论证易卡第四档</small></div>'
            )
    return "\n".join(out)


LETTER_CATEGORY_LABELS = {
    "inquiry":       "咨询信（Inquiry）",
    "application":   "申请信（Application）",
    "recommendation":"推荐信（Recommendation）",
    "invitation":    "邀请信（Invitation）",
    "suggestion":    "建议信（Suggestion）",
    "complaint":     "投诉信（Complaint）",
    "reply":         "回复信（Reply）",
    "apology":       "道歉信（Apology）",
    "congratulation":"祝贺信（Congratulation）",
    "thank_you":     "感谢信（Thank-you）",
    "other":         "其他信件",
}


def render_letter_category(category: str | None, confidence: float | None,
                           check: dict | None) -> str:
    """v1.6.1：Postgrad A 节 letter_category 专属识别 + 要素检查。

    期望 schema：
        check = {
            "opening_phrase_ok": true/false,
            "tone_ok": true/false,
            "required_elements": [
                {"name": "具体诉求", "present": true, "evidence": "..."},
                ...
            ],
            "category_pitfalls": ["..."],  # 本子类典型雷区本文是否踩中
        }
    """
    if not category:
        return ""
    label = LETTER_CATEGORY_LABELS.get(category, category)
    conf_pct = f"{confidence*100:.0f}%" if isinstance(confidence, (int, float)) else "—"
    out = [
        f'        <div class="letter-cat-head">'
        f'<strong>识别类型：</strong>{label} '
        f'<span class="letter-conf">识别置信度 {conf_pct}</span>'
        f'</div>'
    ]

    if not check:
        out.append('        <p class="empty">未启用 letter_category 专属检查</p>')
        return "\n".join(out)

    # 开头套语 + 语气
    open_ok = check.get("opening_phrase_ok")
    tone_ok = check.get("tone_ok")
    out.append('        <ul class="letter-check">')
    if open_ok is not None:
        mark = "✅ 标准" if open_ok else "⚠️ 不规范"
        cls = "ok" if open_ok else "warn"
        out.append(f'          <li class="lc-{cls}"><strong>开头套语：</strong>{mark}</li>')
    if tone_ok is not None:
        mark = "✅ 契合" if tone_ok else "❌ 偏离（本子类有专属语域要求）"
        cls = "ok" if tone_ok else "danger"
        out.append(f'          <li class="lc-{cls}"><strong>语域与语气：</strong>{mark}</li>')
    out.append('        </ul>')

    # v1.7.0：必备要素齐备度进度条
    elements = check.get("required_elements", []) or []
    if elements:
        present_cnt = sum(1 for e in elements if e.get("present"))
        total_cnt = len(elements)
        pct = int(present_cnt / total_cnt * 100) if total_cnt else 0
        label = f"{present_cnt}/{total_cnt} 项（{pct}%）"
        out.append(
            '        <div class="letter-elem-gauge">'
            f'<strong>要素齐备度：</strong>'
            + svg_progress_bar(pct, label=label)
            + '</div>'
        )
        out.append('        <table class="letter-elem-table">')
        out.append('          <thead><tr><th>本子类必备要素</th><th>是否出现</th><th>证据</th></tr></thead>')
        out.append('          <tbody>')
        for e in elements:
            name = html.escape(str(e.get("name", "")))
            present = e.get("present")
            flag = "✅" if present else "❌"
            ev = html.escape(str(e.get("evidence", ""))) if present else "—"
            out.append(
                f'          <tr><td>{name}</td><td>{flag}</td><td>{ev}</td></tr>'
            )
        out.append('          </tbody></table>')

    # 典型雷区
    pitfalls = check.get("category_pitfalls") or []
    if pitfalls:
        out.append('        <div class="letter-pitfalls">'
                   '<strong>本子类典型雷区（本文踩中）：</strong><ul>')
        for p in pitfalls:
            out.append(f'          <li>{html.escape(str(p))}</li>')
        out.append('        </ul></div>')

    return "\n".join(out)


CHART_SUBTYPE_LABELS = {
    "bar_chart":  "柱状图（Bar chart）",
    "pie_chart":  "饼图（Pie chart）",
    "table":      "表格（Table）",
    "line_graph": "折线图（Line graph）",
    "multi_bar":  "双柱/多柱并列图（Multi-bar）",
    "multi_pie":  "多饼对比图（Multi-pie）",
    "mixed":      "混合图（Mixed）",
}


def render_chart_subtype(subtype: str | None, info: dict | None) -> str:
    """v1.6.1：Postgrad2B / CET chart 题专属检查。

    期望 schema：
        info = {
            "data_coverage_ratio": 0.89,      # 数据点覆盖率
            "data_coverage_note": "...",
            "data_accuracy_errors": [         # 具体数据错位
                {"point": "...", "expected": "...", "actual": "..."}
            ],
            "trend_description_ok": true,
            "multi_group_parallel_ok": true,  # 仅 multi_bar / multi_pie
            "interpretation_present": true,   # 是否有原因/影响分析段
        }
    """
    if not subtype:
        return ""
    label = CHART_SUBTYPE_LABELS.get(subtype, subtype)
    out = [f'        <div class="chart-sub-head"><strong>图表子类：</strong>{label}</div>']

    if not info:
        out.append('        <p class="empty">未启用 chart_subtype 专属检查</p>')
        return "\n".join(out)

    # v1.7.0：数据覆盖率 SVG 进度条
    ratio = info.get("data_coverage_ratio")
    if isinstance(ratio, (int, float)):
        pct = int(ratio * 100)
        cls = "ok" if pct >= 95 else ("warn" if pct >= 80 else "danger")
        note = html.escape(str(info.get("data_coverage_note", "")))
        out.append(
            f'        <div class="chart-metric chart-{cls}">'
            f'<strong>数据覆盖率：</strong>'
            + svg_progress_bar(pct, label=f"{pct}%")
            + (f'<small class="chart-note">{note}</small>' if note else '')
            + '</div>'
        )

    # 数据准确性错位
    errs = info.get("data_accuracy_errors") or []
    if errs:
        out.append('        <div class="chart-errs"><strong>数据错位：</strong><ul>')
        for e in errs:
            pt = html.escape(str(e.get("point", "")))
            exp = html.escape(str(e.get("expected", "")))
            act = html.escape(str(e.get("actual", "")))
            out.append(f'          <li>{pt}：图中 <code>{exp}</code> → 本文 <code>{act}</code></li>')
        out.append('        </ul></div>')

    # 趋势描述
    trend_ok = info.get("trend_description_ok")
    if trend_ok is not None:
        mark = "✅ 准确描述" if trend_ok else "❌ 描述偏差（如把 increase 说成 decrease）"
        cls = "ok" if trend_ok else "danger"
        out.append(f'        <div class="chart-line chart-{cls}"><strong>趋势描述：</strong>{mark}</div>')

    # 两组并列（multi_bar / multi_pie 专属）
    if subtype in ("multi_bar", "multi_pie"):
        parallel = info.get("multi_group_parallel_ok")
        if parallel is not None:
            mark = "✅ 两组均有描述" if parallel else "❌ 只描述一组（multi_bar 硬失误）"
            cls = "ok" if parallel else "danger"
            out.append(f'        <div class="chart-line chart-{cls}">'
                       f'<strong>两组并列覆盖：</strong>{mark}</div>')

    # 归因/阐释段
    interp = info.get("interpretation_present")
    if interp is not None:
        mark = "✅ 已给出原因/影响分析" if interp else "⚠️ 缺归因段（止于描述数据易卡第三档）"
        cls = "ok" if interp else "warn"
        out.append(f'        <div class="chart-line chart-{cls}">'
                   f'<strong>数据归因：</strong>{mark}</div>')
    return "\n".join(out)


def render_rubric_table(exam_level: str) -> tuple[str, str]:
    """根据考试级别渲染官方评分标准表格，返回 (source_note, table_html)。"""
    if is_postgrad(exam_level):
        source_note = (
            "来源：《全国硕士研究生招生考试英语（一/二）考试大纲》（2025/2026 版）"
            "· 五档制，A/B 节共用档次描述，仅分数段不同。"
        )
        el = exam_level.upper()
        # 各档分数段
        if el == "POSTGRAD1A":
            bands = [
                ("第五档", "9–10 分"),
                ("第四档", "7–8 分"),
                ("第三档", "5–6 分"),
                ("第二档", "3–4 分"),
                ("第一档", "1–2 分"),
            ]
        elif el == "POSTGRAD1B":
            bands = [
                ("第五档", "17–20 分"),
                ("第四档", "13–16 分"),
                ("第三档", "9–12 分"),
                ("第二档", "5–8 分"),
                ("第一档", "1–4 分"),
            ]
        elif el == "POSTGRAD2A":
            bands = [
                ("第五档", "9–10 分"),
                ("第四档", "7–8 分"),
                ("第三档", "5–6 分"),
                ("第二档", "3–4 分"),
                ("第一档", "1–2 分"),
            ]
        else:  # POSTGRAD2B
            bands = [
                ("第五档", "13–15 分"),
                ("第四档", "10–12 分"),
                ("第三档", "7–9 分"),
                ("第二档", "4–6 分"),
                ("第一档", "1–3 分"),
            ]
        descs = [
            ("第五档", "很好地完成了试题规定的任务：包含所有内容要点；使用丰富的语法结构和词汇；语言自然流畅，语法错误极少；有效地采用了多种衔接手法，文字连贯，层次清晰；格式与语域恰当贴切。对目标读者完全产生了预期的效果。"),
            ("第四档", "较好地完成了试题规定的任务：包含所有内容要点，允许漏掉一、两个次重点；使用较丰富的语法结构和词汇；语言基本准确，只有在试图使用较复杂结构或较高级词汇时才有个别错误；采用了适当的衔接手法，层次清晰，组织较严密；格式与语域较恰当。对目标读者产生了预期的效果。"),
            ("第三档", "基本完成了试题规定的任务：虽漏掉一些内容，但包含多数内容要点；所使用的语法结构和词汇能满足任务的需求；存在一些语法及词汇错误，但不影响整体理解；采用了简单的衔接手法，内容基本连贯，层次基本清晰；格式与语域基本合理。对目标读者基本产生了预期的效果。"),
            ("第二档", "未能按要求完成试题规定的任务：漏掉或未能有效阐述一些内容要点，写了一些无关内容；语法结构单调、词汇项目有限；有较多语法结构或词汇方面的错误，影响了对写作内容的理解；未采用恰当的衔接手法，内容缺少连贯性；格式和语域不恰当。未能清楚地传达信息给读者。"),
            ("第一档", "未完成试题规定的任务：明显遗漏主要内容，且有许多不相关的内容；语法项目和词汇的使用单调、重复；语言错误多，有碍读者对内容的理解；未使用任何衔接手法，内容不连贯，缺少组织、分段；无格式与语域概念。未能传达信息给读者。"),
        ]
        desc_map = dict(descs)
        rows = []
        for band_name, score_range in bands:
            desc = html.escape(desc_map.get(band_name, ""))
            rows.append(
                f'          <tr><td style="white-space:nowrap;font-weight:600;">'
                f'{band_name}</td>'
                f'<td style="white-space:nowrap;color:var(--brand);font-weight:600;">'
                f'{score_range}</td>'
                f'<td style="font-size:13px;line-height:1.6;">{desc}</td></tr>'
            )
        table_html = (
            '        <table class="vocab-table" style="font-size:14px;">\n'
            '          <thead><tr>'
            '<th style="width:80px;">档次</th>'
            '<th style="width:80px;">分数段</th>'
            '<th>官方描述符（原文）</th>'
            '</tr></thead>\n'
            '          <tbody>\n'
            + "\n".join(rows)
            + '\n          </tbody>\n        </table>'
        )
        return source_note, table_html
    else:
        # CET
        source_note = (
            "来源：《全国大学英语四、六级考试大纲（2016 年修订版）》第 4.1 节"
            "· 总体印象评分法（holistic scoring），满分 15 分，五档制。"
            " PDF：https://cet.neea.edu.cn/res/Home/1704/55b02330ac17274664f06d9d3db8249d.pdf"
        )
        bands = [
            ("14 分档", "13–15 分", "切题。表达思想清楚，文字通顺、连贯，基本上无语言错误，仅有个别小错。"),
            ("11 分档", "10–12 分", "切题。表达思想清楚，文字连贯，但有少量语言错误。"),
            ("8 分档",  "7–9 分",  "基本切题。有些地方表达思想不够清楚，文字勉强连贯，语言错误相当多，其中有一些是严重错误。"),
            ("5 分档",  "4–6 分",  "基本切题。表达思想不清楚，连贯性差，有较多的严重语言错误。"),
            ("2 分档",  "1–3 分",  "条理不清，思路紊乱，语言支离破碎或大部分句子均有错误，且多数为严重错误。"),
            ("0 分",    "0 分",    "未作答，或只有几个孤立的词，或作文与主题毫不相关。"),
        ]
        rows = []
        for band_name, score_range, desc in bands:
            rows.append(
                f'          <tr><td style="white-space:nowrap;font-weight:600;">'
                f'{band_name}</td>'
                f'<td style="white-space:nowrap;color:var(--brand);font-weight:600;">'
                f'{score_range}</td>'
                f'<td style="font-size:13px;line-height:1.6;">{html.escape(desc)}</td></tr>'
            )
        table_html = (
            '        <table class="vocab-table" style="font-size:14px;">\n'
            '          <thead><tr>'
            '<th style="width:80px;">档次</th>'
            '<th style="width:80px;">分数段</th>'
            '<th>官方描述符（原文）</th>'
            '</tr></thead>\n'
            '          <tbody>\n'
            + "\n".join(rows)
            + '\n          </tbody>\n        </table>'
        )
        return source_note, table_html


def render_vocab_upgrades(upgrades: list[dict]) -> str:
    """v1.2 新增：词汇升档建议（基于 writing-vocabulary.md 四层库）。"""
    if not upgrades:
        return '        <p class="empty">当前词汇层级基本达标，未发现明显低阶词需升档 ✅</p>'

    out = ['        <p class="vocab-hint">以下是基于目标档次自动检出的可升级词汇（至多 5 条），'
           '请结合语境选择是否替换。</p>',
           '        <table class="vocab-table">',
           '          <thead><tr><th>位置</th><th>原词</th><th>升级建议</th>'
           '<th>层级跃迁</th><th>说明</th></tr></thead>',
           '          <tbody>']
    for u in upgrades[:10]:  # 理论最多 5，留余量
        loc = html.escape(str(u.get("location", "")))
        orig = html.escape(str(u.get("original", "")))
        sug_list = u.get("suggestion", [])
        if isinstance(sug_list, list):
            sug = " / ".join(html.escape(str(s)) for s in sug_list)
        else:
            sug = html.escape(str(sug_list))
        t_from = VOCAB_TIER_LABELS.get(u.get("tier_from", ""), u.get("tier_from", ""))
        t_to = VOCAB_TIER_LABELS.get(u.get("tier_to", ""), u.get("tier_to", ""))
        note = html.escape(str(u.get("note", "")))
        out.append(
            f'          <tr><td>{loc}</td><td><code>{orig}</code></td>'
            f'<td><code>{sug}</code></td>'
            f'<td><span class="tier-from">{t_from}</span> → '
            f'<span class="tier-to">{t_to}</span></td>'
            f'<td>{note}</td></tr>'
        )
    out.extend(['          </tbody>', '        </table>'])
    return "\n".join(out)


def render(data: dict, template: str) -> str:
    meta = data.get("meta", {})
    exam_level = meta.get("exam_level", data.get("exam_level", "CET4"))
    task_subtype = meta.get("task_subtype", data.get("task_subtype", ""))

    band = data["band"]
    final = data["final_score"]
    score_max = get_score_max(exam_level)
    raw = data.get("raw_score", final)

    # 仪表盘角度：按该考试满分归一化
    angle = int(float(final) / score_max * 360)

    # 报告分换算（仅 CET 有官方换算）
    if is_postgrad(exam_level):
        converted_hint = f"{final}/{score_max} 分（考研按原始分计入总分）"
    else:
        converted = data.get("converted_score", round(float(final) * 7.1, 1))
        converted_hint = f"{converted:g} / 106.5（报告分换算）"

    band_names = get_band_names(exam_level)
    bd = data.get("band_description", {})
    boundary = data.get("boundary_decision", {})
    intra = data.get("intra_band_adjustment", {})

    wc = data.get("word_count", {})
    wc_summary = (
        f'有效字数 <strong>{wc.get("effective", 0)}</strong> / '
        f'要求 {wc.get("requirement_min","?")}-{wc.get("requirement_max") or "不设上限"}'
        f'（{"达标" if wc.get("within_range") else "未达标"}）'
    )

    # 考研特有区块——根据 exam_level 决定是否显示
    postgrad_mode = is_postgrad(exam_level)
    postgrad_display = "" if postgrad_mode else "none"
    cet_display = "none" if postgrad_mode else ""

    dim_section_title = "2. 定档依据（考研 5 维评分维度）" if postgrad_mode \
        else "2. 定档依据"

    # v1.6.1 新区块：根据 JSON 是否提供相应字段决定展示
    calib_status = data.get("calibration_status")
    calib_note = data.get("calibration_note")
    calib_html = render_calibration_banner(calib_status, calib_note)
    calib_display = "" if calib_html else "none"

    para_diag = data.get("paragraph_diagnosis")
    para_html = render_paragraph_diagnosis(para_diag)
    para_display = "" if para_html else "none"

    letter_category = meta.get("letter_category", data.get("letter_category"))
    letter_conf = data.get("letter_category_confidence")
    dim_diag = data.get("dimension_diagnosis", {}) or {}
    letter_check = dim_diag.get("category_specific_check") \
        if isinstance(dim_diag, dict) else None
    letter_html = render_letter_category(letter_category, letter_conf, letter_check)
    letter_display = "" if letter_html else "none"

    chart_subtype = meta.get("chart_subtype", data.get("chart_subtype"))
    chart_info = data.get("chart_subtype_specific")
    chart_html = render_chart_subtype(chart_subtype, chart_info)
    chart_display = "" if chart_html else "none"

    rubric_source_note, rubric_table_html = render_rubric_table(exam_level)

    replacements = {
        "{{EXAM_LEVEL}}":     html.escape(format_exam_level(exam_level)),
        "{{TASK_SUBTYPE}}":   html.escape(format_task_subtype(task_subtype)) if task_subtype else "—",
        "{{BAND}}":           str(band),
        "{{BAND_NAME}}":      band_names.get(band, f"{band} 档"),
        "{{RAW_SCORE}}":      f"{raw:g}",
        "{{FINAL_SCORE}}":    f"{final:g}",
        "{{SCORE_MAX}}":      str(score_max),
        "{{CONVERTED_SCORE_HINT}}":  converted_hint,
        "{{SCORE_CIRCLE_ANGLE}}":    str(angle),
        "{{BAND_OFFICIAL_TEXT}}":    html.escape(bd.get("official_text", "")),
        "{{BAND_SOURCE}}":           html.escape(bd.get("source", "")),
        "{{WORD_COUNT_SUMMARY}}":    wc_summary,
        "{{COMPARED_HIGHER}}":       html.escape(boundary.get("compared_with_higher", "—")),
        "{{COMPARED_LOWER}}":        html.escape(boundary.get("compared_with_lower", "—")),
        "{{INTRA_DELTA}}":           f"{intra.get('delta', 0):+g}",
        "{{INTRA_REASON}}":          html.escape(intra.get("reason", "")),
        "{{DIMENSIONS_TITLE}}":      dim_section_title,
        "{{DIMENSIONS_HTML}}":       render_dimensions(data.get("dimension_diagnosis", {}), exam_level),
        "{{DEDUCTIONS_HTML}}":       render_deductions(data.get("deductions", [])),
        "{{ISSUES_HTML}}":           render_issues(data.get("issues", []), data.get("vocabulary_upgrades", [])),
        "{{UPGRADE_HTML}}":          render_upgrade(data.get("upgrade_path", {})),
        "{{RATIONALE_HTML}}":        render_rationale(data.get("rationale_trace", [])),
        "{{ESSAY_TEXT}}":            html.escape(data.get("essay", "")),
        "{{PROMPT_TEXT}}":           html.escape(data.get("prompt", "")),
        "{{REVIEWED_AT}}":           html.escape(format_reviewed_at(meta.get("reviewed_at", ""))),

        "{{POSTGRAD_BLOCK_STYLE}}":  f'style="display:{postgrad_display}"',
        "{{CET_BLOCK_STYLE}}":       f'style="display:{cet_display}"',
        "{{DIRECTIONS_COPY_HTML}}":  render_directions_copy(data.get("directions_copy_check")),
        "{{VOCAB_UPGRADES_HTML}}":   render_vocab_upgrades(data.get("vocabulary_upgrades", [])),
        "{{RUBRIC_SOURCE_NOTE}}":     html.escape(rubric_source_note),
        "{{RUBRIC_TABLE_HTML}}":      rubric_table_html,
        # v1.6.1 新增占位符
        "{{CALIB_BLOCK_STYLE}}":     f'style="display:{calib_display}"',
        "{{CALIB_BANNER_HTML}}":     calib_html,
        "{{PARA_DIAG_BLOCK_STYLE}}": f'style="display:{para_display}"',
        "{{PARA_DIAG_HTML}}":        para_html,
        "{{LETTER_CAT_BLOCK_STYLE}}":f'style="display:{letter_display}"',
        "{{LETTER_CAT_HTML}}":       letter_html,
        "{{CHART_SUB_BLOCK_STYLE}}": f'style="display:{chart_display}"',
        "{{CHART_SUB_HTML}}":        chart_html,
    }

    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def main() -> None:
    here = Path(__file__).resolve().parent
    default_template = here.parent / "assets" / "report-template.html"

    parser = argparse.ArgumentParser(description="渲染 英语考试作文批改 HTML 报告（CET + 考研）")
    parser.add_argument("json_file", help="review JSON 文件路径")
    parser.add_argument("--template", default=str(default_template), help="HTML 模板路径")
    parser.add_argument("--output", default="./review-reports/report.html", help="输出 HTML 路径（v1.7.1+ Step 7 规范目录）")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"❌ JSON 文件不存在: {args.json_file}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    try:
        validate(data)
    except ValueError as e:
        print(f"❌ JSON 校验失败: {e}", file=sys.stderr)
        sys.exit(2)

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"❌ 模板不存在: {args.template}", file=sys.stderr)
        sys.exit(1)

    template = template_path.read_text(encoding="utf-8")
    html_out = render(data, template)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_out, encoding="utf-8")

    meta = data.get("meta", {})
    exam_level = meta.get("exam_level", data.get("exam_level", "CET4"))
    score_max = get_score_max(exam_level)
    band_names = get_band_names(exam_level)

    print("✅ HTML 报告生成成功")
    print(f"   考试级别: {exam_level}")
    print(f"   最终分:   {data['final_score']}/{score_max}")
    if not is_postgrad(exam_level):
        print(f"   报告分:   {data.get('converted_score', '-')}/106.5")
    print(f"   档次:     {band_names.get(data['band'], '')}")
    print(f"   输出:     {output_path}")


if __name__ == "__main__":
    main()
