#!/usr/bin/env python3
"""Render validated PROPDB report-data v1.1 as standalone static HTML."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Optional


SCHEMA_VERSION = "1.1"
TEMPLATE_VERSION = "propdb-report-v1.1"
MAX_CURVE_POINTS = 200
REPORT_TYPES = {
    "query-result": "物性查询报告",
    "property-curve": "多曲线物性报告",
    "calculation-result": "热力学计算报告",
}
ROLE_LABELS = {
    "scope": "分析范围",
    "object": "对象信息",
    "conditions": "计算条件",
    "results": "结果数据",
    "curves": "物性曲线",
    "methodology": "方法与口径",
    "limitations": "限制与缺失",
    "appendix": "附录",
}
ROLE_ORDER = {role: index for index, role in enumerate(ROLE_LABELS)}
SOURCE_LABELS = {
    "propdb": "",
    "user-input": "用户输入",
    "agent-summary": "分析摘要",
    "combined": "综合整理",
}
CHART_COLORS = ["#356ae6", "#1b9a96", "#e99b37", "#d95757", "#7b61c9", "#3b8fb8"]
MARKER_COLORS = {"brand": "#356ae6", "teal": "#1b9a96", "warning": "#e99b37", "critical": "#d95757"}
TOP_KEYS = {"schemaVersion", "templateVersion", "report", "executiveSummary", "keyMetrics", "sections"}
REPORT_KEYS = {
    "type", "title", "subtitle", "generatedAt", "dataAsOf", "objectLabel", "scopeLabel",
    "unitSet", "coverage", "methodLabel", "resultReference", "layout", "language", "dataStatus", "curveFamilyCount",
}
SUMMARY_KEYS = {"text", "basis"}
METRIC_KEYS = {"label", "value", "unit", "note", "tone", "decimals", "grouping", "sourceKind"}
SECTION_KEYS = {
    "role", "kind", "sourceKind", "heading", "description", "paragraphs", "tone", "items",
    "columns", "rows", "caption", "xValues", "xLabel", "xUnit", "yLabel", "yUnit", "series", "markers",
}
COLUMN_KEYS = {"key", "label", "type", "unit", "decimals", "grouping"}
SERIES_KEYS = {"name", "values"}
MARKER_KEYS = {"x", "label", "tone"}
FORBIDDEN_KEYS = {
    "authkey", "authorization", "accesstoken", "refreshtoken", "password", "cookie", "headers",
    "simlevel", "proplevel", "rawresponse", "stacktrace", "exceptionstack", "toolname", "endpoint",
}
FORBIDDEN_TEXT = {"authkey", "authorizationbearer", "simlevel", "proplevel", "rawresponse", "stacktrace"}
FORBIDDEN_VISIBLE_PHRASES = {
    "旧版", "25 接口版", "25接口版", "propdb_old", "propdb-skill-old",
    "propdb_full", "propdb-full", "propdb-skill-full",
}


class ReportDataError(ValueError):
    """Raised when report-data violates the PROPDB display contract."""


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ReportDataError(message)


def h(value: Any) -> str:
    return html.escape(str(value), quote=True)


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def exact_keys(value: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    ensure(not unknown, f"{path} 含未允许字段: {', '.join(unknown)}")


def text_value(value: Any, path: str, maximum: int, *, allow_empty: bool = False) -> str:
    ensure(isinstance(value, str), f"{path} 必须是字符串")
    if not allow_empty:
        ensure(bool(value.strip()), f"{path} 不能为空")
    ensure(len(value) <= maximum, f"{path} 最多 {maximum} 个字符")
    return value


def scalar(value: Any, path: str) -> None:
    ensure(value is None or isinstance(value, (str, int, float, bool)), f"{path} 必须是标量")
    if isinstance(value, float):
        ensure(math.isfinite(value), f"{path} 不能是 NaN 或无穷值")
    if isinstance(value, str):
        ensure(len(value) <= 220, f"{path} 文本过长")


def scan_forbidden(value: Any, path: str = "report-data") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            ensure(normalized(str(key)) not in FORBIDDEN_KEYS, f"{path} 含禁止的内部字段: {key}")
            scan_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_forbidden(item, f"{path}[{index}]")
    elif isinstance(value, str):
        folded_text = value.casefold()
        ensure(not re.search(r"(?<![a-z0-9])inp(?![a-z0-9])", folded_text), f"{path} 含禁止展示的未请求导出术语")
        for phrase in FORBIDDEN_VISIBLE_PHRASES:
            ensure(phrase.casefold() not in folded_text, f"{path} 含禁止展示的内部版本标识")
        folded = normalized(value)
        for term in FORBIDDEN_TEXT:
            ensure(term not in folded, f"{path} 含禁止展示的内部术语")


def validate_column(column: Any, path: str) -> str:
    ensure(isinstance(column, dict), f"{path} 必须是对象")
    exact_keys(column, COLUMN_KEYS, path)
    ensure({"key", "label", "type"} <= set(column), f"{path} 缺少必需字段")
    ensure(bool(re.fullmatch(r"[a-z][a-zA-Z0-9_]{0,39}", column["key"])), f"{path}.key 格式无效")
    text_value(column["label"], f"{path}.label", 40)
    ensure(column["type"] in {"text", "number", "status"}, f"{path}.type 不受支持")
    if "unit" in column:
        text_value(column["unit"], f"{path}.unit", 24, allow_empty=True)
    if "decimals" in column:
        ensure(isinstance(column["decimals"], int) and 0 <= column["decimals"] <= 8, f"{path}.decimals 必须为 0–8")
    if "grouping" in column:
        ensure(isinstance(column["grouping"], bool), f"{path}.grouping 必须是布尔值")
    return column["key"]


def validate_table(section: dict[str, Any], path: str) -> None:
    columns, rows = section.get("columns"), section.get("rows")
    ensure(isinstance(columns, list) and 2 <= len(columns) <= 16, f"{path}.columns 必须包含 2–16 列")
    ensure(isinstance(rows, list) and 1 <= len(rows) <= 1000, f"{path}.rows 必须包含 1–1000 行")
    keys = [validate_column(column, f"{path}.columns[{index}]") for index, column in enumerate(columns)]
    ensure(len(keys) == len(set(keys)), f"{path}.columns 的 key 必须唯一")
    allowed = set(keys)
    for index, row in enumerate(rows):
        row_path = f"{path}.rows[{index}]"
        ensure(isinstance(row, dict), f"{row_path} 必须是对象")
        unknown = sorted(set(row) - allowed)
        ensure(not unknown, f"{row_path} 含未声明列: {', '.join(unknown)}")
        ensure(any(row.get(key) is not None for key in keys), f"{row_path} 不能是全空行")
        for key, value in row.items():
            scalar(value, f"{row_path}.{key}")


def validate_curve(section: dict[str, Any], path: str) -> None:
    x_values = section.get("xValues")
    ensure(isinstance(x_values, list) and 2 <= len(x_values) <= MAX_CURVE_POINTS, f"{path}.xValues 必须包含 2–{MAX_CURVE_POINTS} 个点")
    ensure(all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in x_values), f"{path}.xValues 必须是有限数值")
    ensure(all(left < right for left, right in zip(x_values, x_values[1:])), f"{path}.xValues 必须严格递增")
    for key in ("xLabel", "xUnit", "yLabel", "yUnit"):
        text_value(section.get(key), f"{path}.{key}", 40 if key.endswith("Label") else 24, allow_empty=key.endswith("Unit"))
    series = section.get("series")
    ensure(isinstance(series, list) and 1 <= len(series) <= 6, f"{path}.series 必须包含 1–6 组")
    names = []
    for index, item in enumerate(series):
        item_path = f"{path}.series[{index}]"
        ensure(isinstance(item, dict), f"{item_path} 必须是对象")
        exact_keys(item, SERIES_KEYS, item_path)
        ensure(set(item) == SERIES_KEYS, f"{item_path} 必须包含 name 和 values")
        text_value(item["name"], f"{item_path}.name", 60)
        values = item["values"]
        ensure(isinstance(values, list) and len(values) == len(x_values), f"{item_path}.values 数量必须与 xValues 一致")
        valid_count = 0
        for value_index, value in enumerate(values):
            ensure(value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)), f"{item_path}.values[{value_index}] 必须是数值或 null")
            if value is not None:
                ensure(math.isfinite(value), f"{item_path}.values[{value_index}] 不能是 NaN 或无穷值")
                valid_count += 1
        ensure(valid_count >= 2, f"{item_path} 至少需要 2 个有效点才能渲染曲线")
        names.append(item["name"])
    ensure(len(names) == len(set(names)), f"{path}.series 名称必须唯一")
    markers = section.get("markers", [])
    ensure(isinstance(markers, list) and len(markers) <= 12, f"{path}.markers 最多 12 个")
    for index, marker in enumerate(markers):
        marker_path = f"{path}.markers[{index}]"
        ensure(isinstance(marker, dict), f"{marker_path} 必须是对象")
        exact_keys(marker, MARKER_KEYS, marker_path)
        ensure({"x", "label"} <= set(marker), f"{marker_path} 缺少 x 或 label")
        ensure(isinstance(marker["x"], (int, float)) and math.isfinite(marker["x"]), f"{marker_path}.x 必须是有限数值")
        ensure(x_values[0] <= marker["x"] <= x_values[-1], f"{marker_path}.x 超出曲线范围")
        text_value(marker["label"], f"{marker_path}.label", 60)
        ensure(marker.get("tone", "teal") in MARKER_COLORS, f"{marker_path}.tone 不受支持")


def is_binary_phase_section(section: dict[str, Any]) -> bool:
    text = " ".join(str(section.get(key, "")) for key in ("heading", "description", "caption", "xLabel", "yLabel")).casefold()
    return bool(re.search(r"(?:\btxy\b|\bpxy\b|t\s*[–—-]\s*x\s*[–—-]\s*y|p\s*[–—-]\s*x\s*[–—-]\s*y|泡点|露点)", text))


def validate_section(section: Any, path: str) -> None:
    ensure(isinstance(section, dict), f"{path} 必须是对象")
    exact_keys(section, SECTION_KEYS, path)
    ensure({"role", "kind", "sourceKind"} <= set(section), f"{path} 缺少 role、kind 或 sourceKind")
    ensure(section["role"] in ROLE_LABELS, f"{path}.role 不受支持")
    ensure(section["kind"] in {"narrative", "callout", "table", "line-chart"}, f"{path}.kind 不受支持")
    ensure(section["sourceKind"] in SOURCE_LABELS, f"{path}.sourceKind 不受支持")
    for key, maximum in (("heading", 60), ("description", 180), ("caption", 220)):
        if key in section:
            text_value(section[key], f"{path}.{key}", maximum, allow_empty=True)
    kind = section["kind"]
    if kind == "narrative":
        values = section.get("paragraphs")
        ensure(isinstance(values, list) and 1 <= len(values) <= 4, f"{path}.paragraphs 必须包含 1–4 段")
        for index, value in enumerate(values):
            text_value(value, f"{path}.paragraphs[{index}]", 360)
    elif kind == "callout":
        values = section.get("items")
        ensure(isinstance(values, list) and 1 <= len(values) <= 12, f"{path}.items 必须包含 1–12 项")
        ensure(section.get("tone", "info") in {"info", "warning", "critical"}, f"{path}.tone 不受支持")
        for index, value in enumerate(values):
            text_value(value, f"{path}.items[{index}]", 220)
    elif kind == "table":
        validate_table(section, path)
    else:
        ensure(section["role"] == "curves", f"{path} 的 line-chart 只能使用 curves 角色")
        validate_curve(section, path)


def validate_report_data(data: Any) -> dict[str, Any]:
    ensure(isinstance(data, dict), "report-data 顶层必须是对象")
    exact_keys(data, TOP_KEYS, "report-data")
    scan_forbidden(data)
    ensure(data.get("schemaVersion") == SCHEMA_VERSION, f"schemaVersion 必须为 {SCHEMA_VERSION}")
    ensure(data.get("templateVersion") == TEMPLATE_VERSION, f"templateVersion 必须为 {TEMPLATE_VERSION}")
    report = data.get("report")
    ensure(isinstance(report, dict), "report 必须是对象")
    exact_keys(report, REPORT_KEYS, "report")
    required = {"type", "title", "generatedAt", "objectLabel", "scopeLabel", "dataStatus"}
    ensure(required <= set(report), f"report 缺少字段: {', '.join(sorted(required - set(report)))}")
    ensure(report["type"] in REPORT_TYPES, "report.type 不受支持")
    ensure(report["dataStatus"] in {"complete", "partial"}, "无结果不得生成报告")
    text_value(report["title"], "report.title", 80)
    text_value(report["generatedAt"], "report.generatedAt", 40)
    text_value(report["objectLabel"], "report.objectLabel", 120)
    text_value(report["scopeLabel"], "report.scopeLabel", 160)
    for key, maximum in (("subtitle", 160), ("dataAsOf", 40), ("coverage", 180), ("methodLabel", 120), ("resultReference", 80)):
        if key in report:
            text_value(report[key], f"report.{key}", maximum, allow_empty=True)
    ensure(report.get("unitSet", "SI") in {"SI", "MET", "ENG"}, "report.unitSet 仅支持 SI、MET 或 ENG")
    ensure(report.get("layout", "portrait") in {"portrait", "landscape"}, "report.layout 不受支持")
    ensure(report.get("language", "zh-CN") in {"zh-CN", "en"}, "report.language 不受支持")

    summaries = data.get("executiveSummary")
    ensure(isinstance(summaries, list) and 2 <= len(summaries) <= 4, "executiveSummary 必须包含 2–4 条结论")
    for index, item in enumerate(summaries):
        path = f"executiveSummary[{index}]"
        ensure(isinstance(item, dict), f"{path} 必须是对象")
        exact_keys(item, SUMMARY_KEYS, path)
        ensure(set(item) == SUMMARY_KEYS, f"{path} 必须包含 text 和 basis")
        text_value(item["text"], f"{path}.text", 180)
        ensure(item["basis"] in SOURCE_LABELS, f"{path}.basis 不受支持")

    metrics = data.get("keyMetrics")
    ensure(isinstance(metrics, list) and 2 <= len(metrics) <= 8, "keyMetrics 必须包含 2–8 项")
    for index, metric in enumerate(metrics):
        path = f"keyMetrics[{index}]"
        ensure(isinstance(metric, dict), f"{path} 必须是对象")
        exact_keys(metric, METRIC_KEYS, path)
        ensure({"label", "value", "sourceKind"} <= set(metric), f"{path} 缺少必需字段")
        text_value(metric["label"], f"{path}.label", 40)
        scalar(metric["value"], f"{path}.value")
        ensure(metric["sourceKind"] in SOURCE_LABELS, f"{path}.sourceKind 不受支持")
        ensure(metric.get("tone", "neutral") in {"neutral", "brand", "teal", "success", "warning", "critical"}, f"{path}.tone 不受支持")
        if "unit" in metric:
            text_value(metric["unit"], f"{path}.unit", 24, allow_empty=True)
        if "note" in metric:
            text_value(metric["note"], f"{path}.note", 100, allow_empty=True)
        if "decimals" in metric:
            ensure(isinstance(metric["decimals"], int) and 0 <= metric["decimals"] <= 8, f"{path}.decimals 必须为 0–8")
        if "grouping" in metric:
            ensure(isinstance(metric["grouping"], bool), f"{path}.grouping 必须是布尔值")

    sections = data.get("sections")
    ensure(isinstance(sections, list) and 1 <= len(sections) <= 12, "sections 必须包含 1–12 个章节")
    for index, section in enumerate(sections):
        validate_section(section, f"sections[{index}]")
    if report["dataStatus"] == "complete":
        for index, section in enumerate(sections):
            if section.get("kind") == "line-chart" and is_binary_phase_section(section):
                ensure(
                    len(section.get("series", [])) == 2,
                    f"sections[{index}] 二元相平衡曲线必须包含液相线和汽相线两条系列",
                )
    roles = {section["role"] for section in sections}
    if report["type"] == "query-result":
        ensure("curveFamilyCount" not in report, "curveFamilyCount 仅用于多曲线 property-curve 报告")
        ensure("results" in roles, "query-result 缺少结果数据章节")
    elif report["type"] == "property-curve":
        curves = [section for section in sections if section["kind"] == "line-chart"]
        ensure(isinstance(report.get("curveFamilyCount"), int) and 2 <= report["curveFamilyCount"] <= 12, "property-curve 必须声明 2–12 个独立曲线族")
        ensure(len(curves) >= report["curveFamilyCount"], "property-curve 的曲线章节少于独立曲线族数量")
    else:
        ensure("curveFamilyCount" not in report, "curveFamilyCount 仅用于多曲线 property-curve 报告")
        ensure(bool(roles & {"results", "curves"}), "calculation-result 缺少主要计算结果")
    if report["type"] in {"property-curve", "calculation-result"}:
        condition_tables = [
            section for section in sections
            if section["role"] == "conditions" and section["kind"] == "table"
        ]
        ensure(condition_tables, "计算或曲线报告必须包含计算条件表")
        for section in condition_tables:
            column_keys = {column["key"] for column in section["columns"]}
            ensure("source" in column_keys, "计算条件表必须用 source 列区分用户输入与自动默认")
            ensure(
                all(row.get("source") in {"用户输入", "自动默认"} for row in section["rows"]),
                "计算条件表 source 仅支持用户输入或自动默认",
            )
        ensure(
            any(section.get("heading") == "可调整项" for section in sections),
            "计算或曲线报告必须包含可调整项章节",
        )
    if report["dataStatus"] == "partial":
        ensure("limitations" in roles, "部分数据报告必须说明影响结论的限制与缺失")
    return data


def format_number(value: float | int, decimals: Optional[int] = None, *, grouping: bool = False) -> str:
    if isinstance(value, int):
        return f"{value:,}" if grouping else str(value)
    if value == 0:
        return "0"
    if abs(value) < 0.001:
        return f"{value:.4e}"
    digits = 4 if decimals is None else decimals
    rendered = f"{value:{',' if grouping else ''}.{digits}f}"
    return rendered if decimals is not None else rendered.rstrip("0").rstrip(".")


def format_scalar(value: Any, decimals: Optional[int] = None, *, grouping: bool = False) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return format_number(value, decimals, grouping=grouping)
    return str(value)


def status_tone(value: Any) -> str:
    text = str(value).casefold()
    if any(token in text for token in ("失败", "不可用", "不满足", "超出", "拒绝")):
        return "critical"
    if any(token in text for token in ("部分", "警告", "待确认", "限制")):
        return "warning"
    if any(token in text for token in ("成功", "可用", "满足", "通过")):
        return "success"
    return "neutral"


def render_meta(label: str, value: str) -> str:
    return f'<div class="meta-row"><dt>{h(label)}</dt><dd>{h(value)}</dd></div>'


def render_hero(report: dict[str, Any]) -> str:
    rows = [render_meta("分析对象", report["objectLabel"]), render_meta("分析范围", report["scopeLabel"]), render_meta("生成时间", report["generatedAt"])]
    if report.get("dataAsOf"):
        rows.insert(2, render_meta("数据时间", report["dataAsOf"]))
    if report.get("unitSet"):
        rows.append(render_meta("单位集", report["unitSet"]))
    if report.get("methodLabel"):
        rows.append(render_meta("方法口径", report["methodLabel"]))
    if report.get("resultReference"):
        rows.append(render_meta("结果凭据", report["resultReference"]))
    if report["dataStatus"] == "partial":
        rows.append(render_meta("数据完整性", "部分数据；限制见正文"))
    subtitle = f'<p class="report-subtitle">{h(report["subtitle"])}</p>' if report.get("subtitle") else ""
    return (
        '    <header class="report-hero">\n      <div class="hero-copy">'
        f'<div class="eyebrow">{h(REPORT_TYPES[report["type"]])}</div>'
        f'<h1 class="report-title">{h(report["title"])}</h1>{subtitle}</div>'
        f'<dl class="report-meta">{"".join(rows)}</dl>\n    </header>'
    )


def render_summary(items: list[dict[str, Any]]) -> str:
    rows = []
    for index, item in enumerate(items, start=1):
        source = SOURCE_LABELS[item["basis"]]
        basis = f' <small class="basis-label">依据：{h(source)}</small>' if source else ""
        rows.append(f'<li><span class="summary-index">{index}</span><span>{h(item["text"])}{basis}</span></li>')
    return f'<section class="executive-card"><h2 class="block-title">结论摘要</h2><ol class="summary-list">{"".join(rows)}</ol></section>'


def render_metrics(metrics: list[dict[str, Any]]) -> str:
    cards = []
    for metric in metrics:
        value = format_scalar(metric["value"], metric.get("decimals"), grouping=metric.get("grouping", False))
        unit = f'<span class="metric-unit">{h(metric["unit"])}</span>' if metric.get("unit") else ""
        source = SOURCE_LABELS[metric["sourceKind"]]
        note = metric.get("note") or (f"来源：{source}" if source else "")
        note_html = f'<div class="metric-note">{h(note)}</div>' if note else ""
        cards.append(
            f'<article class="metric-card" data-tone="{h(metric.get("tone", "neutral"))}">'
            f'<span class="metric-label">{h(metric["label"])}</span><div class="metric-value">{h(value)}{unit}</div>{note_html}</article>'
        )
    return f'<section class="metric-grid" aria-label="关键指标">{"".join(cards)}</section>'


def render_curve_overview(sorted_sections: list[tuple[int, dict[str, Any]]]) -> str:
    cards = []
    for section_number, (_, section) in enumerate(sorted_sections, start=1):
        if section["kind"] != "line-chart":
            continue
        series = "、".join(item["name"] for item in section["series"])
        cards.append(
            f'<a class="curve-index-card" href="#section-{section_number}"><span class="curve-index-number">{len(cards) + 1:02d}</span>'
            f'<span><strong>{h(section.get("heading") or section["yLabel"])}</strong><small>{h(section["xLabel"])} / {h(section["yLabel"])} · {h(series)}</small></span></a>'
        )
    return f'<nav class="curve-index" aria-label="曲线目录"><h2 class="block-title">曲线总览</h2><div class="curve-index-grid">{"".join(cards)}</div></nav>'


def render_table(section: dict[str, Any]) -> str:
    headers = []
    for column in section["columns"]:
        unit = f'<span class="column-unit">{h(column["unit"])}</span>' if column.get("unit") else ""
        headers.append(f'<th scope="col">{h(column["label"])}{unit}</th>')
    rows = []
    for row in section["rows"]:
        cells = []
        for column in section["columns"]:
            rendered = format_scalar(row.get(column["key"]), column.get("decimals"), grouping=column.get("grouping", False))
            if column["type"] == "status":
                content = f'<span class="status-pill" data-tone="{status_tone(rendered)}">{h(rendered)}</span>'
                css_class = ""
            else:
                content = h(rendered)
                css_class = ' class="cell-number"' if column["type"] == "number" else ""
            cells.append(f'<td{css_class}>{content}</td>')
        rows.append(f'<tr>{"".join(cells)}</tr>')
    caption = f'<p class="table-caption">{h(section["caption"])}</p>' if section.get("caption") else ""
    return f'<div class="table-wrap"><table class="data-table"><thead><tr>{"".join(headers)}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>{caption}'


def svg_text(x: float, y: float, value: Any, *, anchor: str = "middle", size: int = 10, fill: str = "#667085") -> str:
    return f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" font-size="{size}" fill="{fill}">{h(value)}</text>'


def render_curve_svg(section: dict[str, Any]) -> str:
    width, height = 1000.0, 420.0
    left, right, top, bottom = 84.0, 30.0, 28.0, 66.0
    plot_width, plot_height = width - left - right, height - top - bottom
    xs = [float(value) for value in section["xValues"]]
    values = [float(value) for series in section["series"] for value in series["values"] if value is not None]
    x_low, x_high = min(xs), max(xs)
    y_low, y_high = min(values), max(values)
    if math.isclose(y_low, y_high):
        padding = max(abs(y_low) * .05, 1.0)
        y_low, y_high = y_low - padding, y_high + padding
    else:
        padding = (y_high - y_low) * .08
        y_low, y_high = y_low - padding, y_high + padding

    def px(value: float) -> float:
        return left + (value - x_low) / (x_high - x_low) * plot_width

    def py(value: float) -> float:
        return top + (y_high - value) / (y_high - y_low) * plot_height

    parts = []
    for index in range(6):
        ratio = index / 5
        y = top + ratio * plot_height
        value = y_high - ratio * (y_high - y_low)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#e3e9ef"/>')
        parts.append(svg_text(left - 10, y + 4, format_number(value), anchor="end"))
        x = left + ratio * plot_width
        x_value = x_low + ratio * (x_high - x_low)
        parts.append(svg_text(x, top + plot_height + 23, format_number(x_value)))
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#9eabba"/>')
    parts.append(f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#9eabba"/>')
    parts.append(svg_text(left + plot_width / 2, height - 12, f'{section["xLabel"]} ({section["xUnit"]})', size=11, fill="#475467"))
    parts.append(f'<text x="18" y="{top + plot_height / 2}" text-anchor="middle" font-size="11" fill="#475467" transform="rotate(-90 18 {top + plot_height / 2})">{h(section["yLabel"])} ({h(section["yUnit"])})</text>')

    for marker in section.get("markers", []):
        x = px(float(marker["x"]))
        color = MARKER_COLORS[marker.get("tone", "teal")]
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}" stroke="{color}" stroke-width="1.5" stroke-dasharray="5 5"/>')
        parts.append(svg_text(x + 4, top + 12, marker["label"], anchor="start", size=9, fill=color))

    for series_index, series in enumerate(section["series"]):
        color = CHART_COLORS[series_index]
        path_parts: list[str] = []
        valid_points: list[tuple[float, float]] = []
        pen_down = False
        for x_value, y_value in zip(xs, series["values"]):
            if y_value is None:
                pen_down = False
                continue
            x, y = px(x_value), py(float(y_value))
            path_parts.append(f'{"L" if pen_down else "M"}{x:.2f},{y:.2f}')
            valid_points.append((x, y))
            pen_down = True
        parts.append(f'<path d="{" ".join(path_parts)}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
        if len(xs) <= 80:
            for x, y in valid_points:
                parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.7" fill="#fff" stroke="{color}" stroke-width="1.8"/>')
    return f'<svg class="chart-svg" viewBox="0 0 {int(width)} {int(height)}" role="img" aria-label="{h(section.get("heading") or section["yLabel"])}曲线图">{"".join(parts)}</svg>'


def render_curve_table(section: dict[str, Any]) -> str:
    headers = [f'<th>{h(section["xLabel"])}<span class="column-unit">{h(section["xUnit"])}</span></th>']
    headers.extend(f'<th>{h(series["name"])}<span class="column-unit">{h(section["yUnit"])}</span></th>' for series in section["series"])
    rows = []
    for index, x_value in enumerate(section["xValues"]):
        cells = [f'<td class="cell-number">{h(format_number(x_value))}</td>']
        cells.extend(f'<td class="cell-number">{h(format_scalar(series["values"][index]))}</td>' for series in section["series"])
        rows.append(f'<tr>{"".join(cells)}</tr>')
    point_count = len(section["xValues"])
    return (
        '<details class="data-disclosure curve-data-disclosure">'
        f'<summary>查看数据表（{point_count} 个数据点）</summary>'
        f'<div class="table-wrap curve-table"><table class="data-table"><thead><tr>{"".join(headers)}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div></details>'
    )


def render_curve(section: dict[str, Any]) -> str:
    legend = "".join(
        f'<li class="legend-item"><span class="legend-swatch" style="--swatch:{CHART_COLORS[index]}"></span>{h(series["name"])}</li>'
        for index, series in enumerate(section["series"])
    )
    markers = "".join(f'<li>{h(marker["label"])}：{h(format_number(marker["x"]))} {h(section["xUnit"])}</li>' for marker in section.get("markers", []))
    marker_html = f'<ul class="curve-marker-list">{markers}</ul>' if markers else ""
    caption = f'<p class="chart-caption">{h(section["caption"])}</p>' if section.get("caption") else ""
    return (
        '<div class="chart-frame"><div class="chart-title-row">'
        f'<span class="chart-title">{h(section["yLabel"])}随{h(section["xLabel"])}变化</span><span>单位：{h(section["yUnit"])}</span></div>'
        f'<div class="chart-scroll">{render_curve_svg(section)}</div><ul class="chart-legend">{legend}</ul>{marker_html}{caption}'
        f'{render_curve_table(section)}</div>'
    )


def render_section(section: dict[str, Any], number: int) -> str:
    heading = section.get("heading") or ROLE_LABELS[section["role"]]
    description = f'<p class="section-description">{h(section["description"])}</p>' if section.get("description") else ""
    source = SOURCE_LABELS[section["sourceKind"]]
    source_html = f'<span class="section-role">{h(source)}</span>' if source else ""
    if section["kind"] == "narrative":
        body = f'<div class="prose">{"".join(f"<p>{h(value)}</p>" for value in section["paragraphs"])}</div>'
    elif section["kind"] == "callout":
        body = f'<aside class="callout" data-tone="{h(section.get("tone", "info"))}"><h3 class="callout-title">{h(heading)}</h3><ul class="callout-list">{"".join(f"<li>{h(value)}</li>" for value in section["items"])}</ul></aside>'
    elif section["kind"] == "table":
        body = render_table(section)
    else:
        body = render_curve(section)
    return (
        f'<section class="report-section" id="section-{number}" data-role="{h(section["role"])}"><header class="section-heading"><div>'
        f'<h2 class="section-title"><span class="section-number">{number:02d}</span>{h(heading)}</h2>{description}</div>{source_html}</header>'
        f'<div class="section-body">{body}</div></section>'
    )


def requires_landscape(data: dict[str, Any]) -> bool:
    return any(section["kind"] == "table" and len(section["columns"]) >= 7 for section in data["sections"])


def asset_root(script_path: Path) -> Path:
    root = script_path.resolve().parent.parent / "assets" / "report" / "renderer"
    ensure((root / "report-shell.html").is_file(), "缺少报告页面骨架")
    ensure((root / "propdb-report.css").is_file(), "缺少报告样式")
    return root


def brand_logo_data_uri(script_path: Path) -> str:
    logo_path = script_path.resolve().parent.parent / "assets" / "brand" / "company-logo.png"
    ensure(logo_path.is_file() and logo_path.stat().st_size > 0, "缺少公司 Logo")
    payload = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def self_check(script_path: Path) -> None:
    ensure(sys.version_info >= (3, 9), "Python 版本必须不低于 3.9")
    root = asset_root(script_path)
    ensure((root / "report-shell.html").stat().st_size > 0, "报告页面骨架为空")
    ensure((root / "propdb-report.css").stat().st_size > 0, "报告样式为空")
    brand_logo_data_uri(script_path)


def render_document(data: dict[str, Any], script_path: Path) -> str:
    data = validate_report_data(data)
    root = asset_root(script_path)
    template = (root / "report-shell.html").read_text(encoding="utf-8")
    stylesheet = (root / "propdb-report.css").read_text(encoding="utf-8")
    report = data["report"]
    sorted_sections = sorted(enumerate(data["sections"]), key=lambda item: (ROLE_ORDER[item[1]["role"]], item[0]))
    main = [render_summary(data["executiveSummary"])]
    if report["type"] == "property-curve":
        main.append(render_curve_overview(sorted_sections))
    main.append(render_metrics(data["keyMetrics"]))
    main.extend(render_section(section, index) for index, (_, section) in enumerate(sorted_sections, start=1))
    layout = "landscape" if requires_landscape(data) else report.get("layout", "portrait")
    replacements = {
        "{{LANG}}": h(report.get("language", "zh-CN")),
        "{{DOCUMENT_TITLE}}": h(report["title"]),
        "{{PAGE_STYLE}}": f"@page {{ size: A4 {layout}; margin: 12mm; }}",
        "{{STYLESHEET}}": stylesheet,
        "{{LAYOUT}}": h(layout),
        "{{SCHEMA_VERSION}}": SCHEMA_VERSION,
        "{{TEMPLATE_VERSION}}": TEMPLATE_VERSION,
        "{{BRAND_LOGO_DATA_URI}}": brand_logo_data_uri(script_path),
        "{{HERO}}": render_hero(report),
        "{{MAIN_CONTENT}}": "\n".join(main),
    }
    output = template
    for marker, value in replacements.items():
        output = output.replace(marker, value)
    ensure(not re.search(r"\{\{[A-Z0-9_]+\}\}", output), "模板仍含未替换标记")
    digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return output.replace("<!doctype html>", f"<!doctype html>\n<!-- report-data-sha256: {digest} -->", 1)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render PROPDB report-data v1.1 as standalone HTML")
    parser.add_argument("--input", default="-", help="UTF-8 report-data JSON file, or - for stdin")
    parser.add_argument("--output", type=Path, help="Output .html file")
    parser.add_argument("--check-only", action="store_true", help="Validate report-data without writing")
    parser.add_argument("--self-check", action="store_true", help="Check Python and bundled assets")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.self_check:
            self_check(Path(__file__))
            print(f"OK: PROPDB report renderer {TEMPLATE_VERSION}; Python {sys.version_info.major}.{sys.version_info.minor}; standard library only")
            return 0
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        data = json.loads(raw)
        validate_report_data(data)
        if args.check_only:
            print(f"OK: report-data conforms to PROPDB schema {SCHEMA_VERSION}")
            return 0
        ensure(args.output is not None, "未使用 --check-only 时必须提供 --output")
        ensure(args.output.suffix.casefold() == ".html", "--output 必须使用 .html 扩展名")
        ensure(not args.output.exists(), "输出文件已存在；请使用新的文件名")
        document = render_document(data, Path(__file__))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8", newline="\n")
        print(f"Rendered: {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, ReportDataError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
