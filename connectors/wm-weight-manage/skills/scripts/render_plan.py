#!/usr/bin/env python3
"""Render a ready weight-management MCP envelope into the product HTML template."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REQUIRED_SECTION_KEYS = (
    "current_state",
    "phased_goals",
    "nutrition",
    "exercise",
    "sleep_hormone_signals",
    "stress_emotional_eating",
    "body_monitoring",
    "pitfalls",
    "special_cases",
    "weekly_checklist",
    "weight_tracker",
    "weekly_review",
    "safety_boundary",
)


class RenderError(ValueError):
    """The MCP envelope cannot be rendered as a personalized plan."""


class _BasicHTMLParser(HTMLParser):
    """Small structural check; the template remains the trusted HTML source."""

    def __init__(self) -> None:
        super().__init__()
        self.start_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        self.start_tags.append(tag.lower())


def _read_envelope(path: Path) -> dict[str, Any]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderError(f"无法读取 MCP JSON：{exc}") from exc

    # 允许直接保存 structuredContent，也允许保存某些客户端的完整工具响应。
    if isinstance(value, dict) and isinstance(value.get("structuredContent"), dict):
        value = value["structuredContent"]
    if isinstance(value, dict) and isinstance(value.get("result"), dict):
        result = value["result"]
        value = result.get("structuredContent") or result
    if isinstance(value, dict) and "status" not in value and isinstance(value.get("content"), list):
        for block in value["content"]:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    candidate = json.loads(block.get("text", ""))
                except (TypeError, json.JSONDecodeError):
                    continue
                if isinstance(candidate, dict) and "status" in candidate:
                    value = candidate
                    break
    if not isinstance(value, dict) or "status" not in value:
        raise RenderError("输入不是体重管理 MCP 响应信封")
    return value


def _escape(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _format_number(value: Any, decimals: int = 1, *, thousands: bool = True) -> str:
    """严格格式化数值占位符。

    输出会进入 HTML 文本与 ``<script>`` 数值字面量两种上下文：HTML 转义对 JS
    上下文无效，因此非数值/非有限数一律抛 RenderError，绝不降级为转义字符串。
    ``thousands=False`` 供注入 ``<script>`` 的数值字面量使用，避免千分位逗号
    破坏 JS 语法。
    """
    if isinstance(value, bool):
        raise RenderError(f"数值字段收到布尔值：{value!r}")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise RenderError(f"数值字段不是数字：{value!r}") from None
    if not math.isfinite(number):
        raise RenderError(f"数值字段不是有限数字：{value!r}")
    if decimals == 0 or number.is_integer():
        return f"{number:,.0f}" if thousands else f"{number:.0f}"
    return f"{number:,.{decimals}f}" if thousands else f"{number:.{decimals}f}"


def _require_positive_number(value: Any, field: str) -> float:
    """进度条计算依赖的正数校验（如 planned_loss_kg），非正数/非数值直接拒绝。"""
    if isinstance(value, bool):
        raise RenderError(f"{field} 收到布尔值：{value!r}")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise RenderError(f"{field} 不是数字：{value!r}") from None
    if not math.isfinite(number):
        raise RenderError(f"{field} 不是有限数字：{value!r}")
    if number <= 0:
        raise RenderError(
            f"{field} 必须为大于 0 的数值，当前值 {value!r}（为 0 或负数会使进度百分比得到 NaN/Infinity）"
        )
    return number


def _render_inline(value: str) -> str:
    escaped = _escape(value)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def _render_markdown_fragment(markdown: Any) -> str:
    lines = str(markdown or "").splitlines()
    output: list[str] = []
    in_list = False
    table_rows: list[str] = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    def is_table_row(line: str) -> bool:
        return line.startswith("|") and line.endswith("|") and line.count("|") >= 2

    def is_align_row(cells: list[str]) -> bool:
        return all(
            set(cell.strip()).issubset(set("-: ")) and "-" in cell
            for cell in cells
        )

    def flush_table() -> None:
        nonlocal table_rows
        if not table_rows:
            return
        rows_html: list[str] = []
        align_index = -1
        if len(table_rows) >= 2:
            second_cells = [c.strip() for c in table_rows[1].split("|")[1:-1]]
            if is_align_row(second_cells):
                align_index = 1

        for idx, row in enumerate(table_rows):
            if idx == align_index:
                continue
            cells = [c.strip() for c in row.split("|")[1:-1]]
            tag = "th" if align_index != -1 and idx == 0 else "td"
            rows_html.append(
                "<tr>" + "".join(f"<{tag}>{_render_inline(c)}</{tag}>" for c in cells) + "</tr>"
            )

        output.append('<div class="table-wrap"><table>')
        output.extend(rows_html)
        output.append("</table></div>")
        table_rows = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            close_list()
            flush_table()
            continue
        if is_table_row(line):
            close_list()
            table_rows.append(line)
            continue
        flush_table()
        if line.startswith(("- ", "* ", "• ")):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{_render_inline(line[2:] if line[:1] != '•' else line[1:])}</li>")
            continue
        close_list()
        if line.startswith("### "):
            output.append(f"<h3>{_render_inline(line[4:])}</h3>")
        elif line.startswith("## ") or line.startswith("# "):
            output.append(f"<h3>{_render_inline(line.lstrip('#').strip())}</h3>")
        else:
            output.append(f"<p>{_render_inline(line)}</p>")
    close_list()
    flush_table()
    return "\n".join(output)


def _sections(data: dict[str, Any]) -> list[dict[str, Any]]:
    sections = data.get("sections")
    if not isinstance(sections, list):
        raise RenderError("ready.data.sections 缺失或不是列表")
    by_key = {
        str(item.get("key")): item
        for item in sections
        if isinstance(item, dict) and item.get("key")
    }
    missing = [key for key in REQUIRED_SECTION_KEYS if key not in by_key]
    if missing:
        raise RenderError(f"ready.data.sections 缺少章节：{', '.join(missing)}")
    result = []
    for key in REQUIRED_SECTION_KEYS:
        item = by_key[key]
        if not str(item.get("body_markdown") or "").strip():
            raise RenderError(f"章节 {key} 没有个性化正文")
        result.append(item)
    return result


def _append_section_content(template: str, sections: list[dict[str, Any]]) -> str:
    rendered = template
    for item in sections:
        key = str(item.get("key") or "").strip()
        title = str(item.get("title") or "").strip()
        if not title:
            raise RenderError("章节缺少标题")
        # 体重记录器区域由模板本身的交互式历史列表承载，不再追加模型示例表格。
        if key == "weight_tracker":
            continue
        pattern = re.compile(
            rf"(<section>\s*<h2>{re.escape(title)}</h2>)(.*?)(</section>)",
            flags=re.DOTALL,
        )
        match = pattern.search(rendered)
        if not match:
            raise RenderError(f"产品模板找不到章节：{title}")
        body_html = _render_markdown_fragment(item.get("body_markdown"))
        injection = (
            "\n      <div class=\"note generated-plan-section\">"
            "<strong>本次个性化建议：</strong>"
            f"<div class=\"generated-markdown\">{body_html}</div></div>\n    "
        )
        rendered = pattern.sub(lambda m: m.group(1) + m.group(2) + injection + m.group(3), rendered, count=1)
    return rendered


def _append_photo_section(template: str, meal_analysis: dict[str, Any] | None) -> str:
    if not meal_analysis:
        return template
    if meal_analysis.get("needs_clarification"):
        raise RenderError("餐食照片分析仍需要澄清，不能渲染完成版 HTML")
    calorie_range = meal_analysis.get("calorie_range_kcal") or {}
    range_text = "暂无可靠范围"
    if calorie_range.get("low") is not None and calorie_range.get("high") is not None:
        range_text = f"约 {_format_number(calorie_range['low'], 0)}–{_format_number(calorie_range['high'], 0)} kcal"
    body = (
        "<section>"
        "<h2>餐食照片分析</h2>"
        f"<p><strong>可见食材：</strong>{_render_inline(meal_analysis.get('visible_items', ''))}</p>"
        f"<p><strong>估算热量范围：</strong>{_escape(range_text)}</p>"
        f"<p><strong>不确定因素：</strong>{_render_inline(meal_analysis.get('uncertainties', ''))}</p>"
        f"<p><strong>与每日目标关系：</strong>{_render_inline(meal_analysis.get('daily_target_relation', ''))}</p>"
        f"<p><strong>低摩擦调整：</strong>{_render_inline(meal_analysis.get('adjustments', ''))}</p>"
        f"<div class=\"note\">{_render_markdown_fragment(meal_analysis.get('markdown', ''))}</div>"
        "</section>"
    )
    return template.replace("\n    <p class=\"footer\">", f"\n    {body}\n    <p class=\"footer\">")


def _replace_scalars(template: str, data: dict[str, Any]) -> str:
    profile = data.get("profile") or {}
    metrics = data.get("metrics") or {}
    timeline = data.get("timeline") or {}
    phases = data.get("phases") or []
    if not isinstance(profile, dict) or not isinstance(metrics, dict) or not isinstance(timeline, dict):
        raise RenderError("ready.data 的 profile、metrics 或 timeline 格式错误")
    if len(phases) < 3 or not isinstance(phases[0], dict) or not isinstance(phases[1], dict):
        raise RenderError("ready.data.phases 格式错误")
    calorie_range = metrics.get("calorie_range_kcal_per_day") or {}
    # LOSS/CURRENT 会作为 <script> 中的 JS 数值字面量注入（template.html render()），
    # 必须校验为正数/数值且不带千分位逗号，防止 NaN、Infinity 或 JS 语法破坏。
    _require_positive_number(metrics.get("planned_loss_kg"), "metrics.planned_loss_kg")
    _require_positive_number(metrics.get("current_weight_kg"), "metrics.current_weight_kg")
    values = {
        "CURRENT": _format_number(metrics.get("current_weight_kg"), 1, thousands=False),
        "TARGET": _format_number(metrics.get("target_weight_kg"), 1),
        "HEIGHT": _format_number(profile.get("height_cm"), 1),
        "AGE": _format_number(profile.get("age"), 0),
        "ACTIVITY": _escape(profile.get("activity")),
        "HEALTH_NOTE": _escape(profile.get("health_context")),
        "BMI_CURRENT": _format_number(metrics.get("bmi_current"), 1),
        "BMI_TARGET": _format_number(metrics.get("bmi_target"), 1),
        "LOSS": _format_number(metrics.get("planned_loss_kg"), 1, thousands=False),
        "BMR": _format_number(metrics.get("bmr_kcal"), 0),
        "CAL_LOW": _format_number(calorie_range.get("low"), 0),
        "CAL_HIGH": _format_number(calorie_range.get("high"), 0),
        "WEEKS": _escape(timeline.get("estimated_weeks_label")),
        "M1": _format_number(phases[0].get("to_weight_kg"), 1),
        "M2": _format_number(phases[1].get("to_weight_kg"), 1),
    }
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    rendered = re.sub(r"生成日期：\d{4}-\d{2}-\d{2}", f"生成日期：{date.today().isoformat()}", rendered)
    return rendered


def _replace_product_blocks(template: str, data: dict[str, Any]) -> str:
    """将结构化阶段、清单、复盘和安全边界注入产品既有区块。"""

    phases = data.get("phases")
    if not isinstance(phases, list) or len(phases) < 3:
        raise RenderError("ready.data.phases 至少需要三个阶段")
    phase_html: list[str] = []
    required_phase_fields = ("title", "from_weight_kg", "to_weight_kg", "duration_label", "focus")
    for phase in phases[:3]:
        if not isinstance(phase, dict):
            raise RenderError("ready.data.phases 包含非法阶段")
        if any(not str(phase.get(field) or "").strip() for field in required_phase_fields):
            raise RenderError("ready.data.phases 缺少阶段字段")
        phase_html.append(
            '<div class="phase"><strong>'
            f"{_escape(phase['title'])}｜{_format_number(phase['from_weight_kg'], 1)} → "
            f"{_format_number(phase['to_weight_kg'], 1)} kg（{_escape(phase['duration_label'])}）"
            f"</strong><br>{_render_inline(phase['focus'])}</div>"
        )
    phases_pattern = re.compile(
        r"(<h2>二、分阶段目标</h2>).*?(?=<div class=\"warning\">)",
        flags=re.DOTALL,
    )
    if not phases_pattern.search(template):
        raise RenderError("产品模板找不到阶段目标区块")
    rendered = phases_pattern.sub(
        lambda match: match.group(1) + "\n      " + "\n      ".join(phase_html) + "\n      ",
        template,
        count=1,
    )

    checklist = data.get("checklist")
    if not isinstance(checklist, list) or not checklist:
        raise RenderError("ready.data.checklist 缺失或为空")
    checklist_html: list[str] = []
    for item in checklist:
        if (
            not isinstance(item, dict)
            or not str(item.get("key") or "").strip()
            or not str(item.get("label") or "").strip()
        ):
            raise RenderError("ready.data.checklist 包含非法条目")
        checklist_key = _escape(item["key"])
        checklist_label = _render_inline(item["label"])
        checklist_html.append(
            f'<label class="check"><input type="checkbox" data-key="{checklist_key}">'
            f"{checklist_label}</label>"
        )
    checklist_pattern = re.compile(
        r'(<h2>十、本周打卡</h2>.*?<div class="checklist">).*?(</div>)',
        flags=re.DOTALL,
    )
    if not checklist_pattern.search(rendered):
        raise RenderError("产品模板找不到打卡区块")
    rendered = checklist_pattern.sub(
        lambda match: match.group(1) + "\n        " + "\n        ".join(checklist_html) + "\n      " + match.group(2),
        rendered,
        count=1,
    )

    weekly_review = data.get("weekly_review")
    if not isinstance(weekly_review, list) or not weekly_review:
        raise RenderError("ready.data.weekly_review 缺失或为空")
    review_items = [str(item).strip() for item in weekly_review if str(item).strip()]
    if not review_items:
        raise RenderError("ready.data.weekly_review 为空")
    review_html = "".join(f"\n        <li>{_render_inline(item)}</li>" for item in review_items)
    review_pattern = re.compile(
        r'(<h2>十二、每周复盘问题</h2>\s*<ul>).*?(</ul>)',
        flags=re.DOTALL,
    )
    if not review_pattern.search(rendered):
        raise RenderError("产品模板找不到每周复盘区块")
    rendered = review_pattern.sub(
        lambda match: match.group(1) + review_html + "\n      " + match.group(2),
        rendered,
        count=1,
    )

    safety_boundary = str(data.get("safety_boundary") or "").strip()
    if not safety_boundary:
        raise RenderError("ready.data.safety_boundary 缺失")
    safety_pattern = re.compile(
        r'(<h2>十三、安全边界</h2>\s*<div class="warning">).*?(</div>)',
        flags=re.DOTALL,
    )
    if not safety_pattern.search(rendered):
        raise RenderError("产品模板找不到安全边界区块")
    return safety_pattern.sub(
        lambda match: match.group(1) + _render_inline(safety_boundary) + match.group(2),
        rendered,
        count=1,
    )


def validate_html(rendered: str) -> None:
    if "{{" in rendered or "}}" in rendered:
        raise RenderError("HTML 仍包含未替换的模板占位符")
    lowered = rendered.lower()
    for fragment in ("<!doctype html>", "<html", "</html>", "<style", "<script", "localstorage"):
        if fragment not in lowered:
            raise RenderError(f"HTML 缺少必要结构：{fragment}")
    parser = _BasicHTMLParser()
    try:
        parser.feed(rendered)
        parser.close()
    except Exception as exc:  # pragma: no cover - HTMLParser is deliberately permissive.
        raise RenderError(f"HTML 结构解析失败：{exc}") from exc
    if parser.start_tags.count("section") < 13:
        raise RenderError("HTML 少于产品要求的 13 个方案章节")


def render(envelope: dict[str, Any], template_path: Path) -> str:
    if envelope.get("status") != "ready":
        raise RenderError(f"当前 MCP 状态为 {envelope.get('status')}，不能渲染完成版 HTML")
    data = envelope.get("data")
    if not isinstance(data, dict):
        raise RenderError("ready.data 缺失")
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RenderError(f"无法读取产品模板：{exc}") from exc
    result = _replace_scalars(template, data)
    result = _replace_product_blocks(result, data)
    result = _append_section_content(result, _sections(data))
    result = _append_photo_section(result, data.get("meal_analysis"))
    validate_html(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a weight-management MCP response to standalone HTML")
    parser.add_argument("--input", type=Path, required=True, help="JSON file containing MCP structuredContent")
    parser.add_argument("--output", type=Path, required=True, help="Output HTML path")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "template.html",
    )
    args = parser.parse_args()
    try:
        rendered = render(_read_envelope(args.input), args.template)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    except RenderError as exc:
        raise SystemExit(f"render failed: {exc}") from exc
    print(f"generated: {args.output.resolve()}")


if __name__ == "__main__":
    main()
