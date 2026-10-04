#!/usr/bin/env python3
"""Render validated PROPDB curve-image-data as a standalone SVG image."""

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


SCHEMA_VERSION = "1.0"
TEMPLATE_VERSION = "propdb-curve-image-v1.0"
MAX_CURVE_POINTS = 200
WIDTH = 1200
PANEL_HEIGHT = 430
COLORS = ["#356ae6", "#1b9a96", "#e99b37", "#d95757", "#7b61c9", "#3b8fb8"]
MARKER_COLORS = {"brand": "#356ae6", "teal": "#1b9a96", "warning": "#e99b37", "critical": "#d95757"}
FORBIDDEN_KEYS = {
    "authkey", "authorization", "accesstoken", "refreshtoken", "password", "cookie", "headers",
    "simlevel", "proplevel", "rawresponse", "stacktrace", "exceptionstack", "toolname", "endpoint",
}
FORBIDDEN_TEXT = {"authkey", "authorizationbearer", "simlevel", "proplevel", "rawresponse", "stacktrace"}
FORBIDDEN_VISIBLE_PHRASES = {
    "旧版", "25 接口版", "25接口版", "propdb_old", "propdb-skill-old",
    "propdb_full", "propdb-full", "propdb-skill-full",
}


class CurveImageDataError(ValueError):
    """Raised when curve-image-data violates the display contract."""


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise CurveImageDataError(message)


def xh(value: Any) -> str:
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


def scan_forbidden(value: Any, path: str = "curve-image-data") -> None:
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


def is_binary_phase_panel(panel: dict[str, Any]) -> bool:
    text = " ".join(str(panel.get(key, "")) for key in ("title", "caption", "xLabel", "yLabel")).casefold()
    return bool(re.search(r"(?:\btxy\b|\bpxy\b|t\s*[–—-]\s*x\s*[–—-]\s*y|p\s*[–—-]\s*x\s*[–—-]\s*y|泡点|露点)", text))


def validate_panel(panel: Any, path: str, *, require_phase_pair: bool = False) -> None:
    ensure(isinstance(panel, dict), f"{path} 必须是对象")
    exact_keys(panel, {"title", "caption", "xValues", "xLabel", "xUnit", "yLabel", "yUnit", "series", "markers"}, path)
    ensure({"title", "xValues", "xLabel", "xUnit", "yLabel", "yUnit", "series"} <= set(panel), f"{path} 缺少必需字段")
    text_value(panel["title"], f"{path}.title", 60)
    if "caption" in panel:
        text_value(panel["caption"], f"{path}.caption", 160, allow_empty=True)
    for key in ("xLabel", "yLabel"):
        text_value(panel[key], f"{path}.{key}", 32)
    for key in ("xUnit", "yUnit"):
        text_value(panel[key], f"{path}.{key}", 20, allow_empty=True)
    xs = panel["xValues"]
    ensure(isinstance(xs, list) and 2 <= len(xs) <= MAX_CURVE_POINTS, f"{path}.xValues 必须包含 2–{MAX_CURVE_POINTS} 个点")
    ensure(all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in xs), f"{path}.xValues 必须是有限数值")
    ensure(all(left < right for left, right in zip(xs, xs[1:])), f"{path}.xValues 必须严格递增")
    series = panel["series"]
    ensure(isinstance(series, list) and 1 <= len(series) <= 6, f"{path}.series 必须包含 1–6 组")
    if require_phase_pair:
        ensure(len(series) == 2, f"{path} 二元相平衡面板必须包含液相线和汽相线两条系列")
    names: set[str] = set()
    for index, item in enumerate(series):
        item_path = f"{path}.series[{index}]"
        ensure(isinstance(item, dict), f"{item_path} 必须是对象")
        exact_keys(item, {"name", "values"}, item_path)
        ensure(set(item) == {"name", "values"}, f"{item_path} 必须包含 name 和 values")
        name = text_value(item["name"], f"{item_path}.name", 56)
        ensure(name not in names, f"{path}.series 名称必须唯一")
        names.add(name)
        values = item["values"]
        ensure(isinstance(values, list) and len(values) == len(xs), f"{item_path}.values 数量必须与 xValues 一致")
        valid = 0
        for value_index, value in enumerate(values):
            ensure(value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)), f"{item_path}.values[{value_index}] 必须是数值或 null")
            if value is not None:
                ensure(math.isfinite(value), f"{item_path}.values[{value_index}] 不能是 NaN 或无穷值")
                valid += 1
        ensure(valid >= 2, f"{item_path} 至少需要 2 个有效点")
    markers = panel.get("markers", [])
    ensure(isinstance(markers, list) and len(markers) <= 10, f"{path}.markers 最多 10 个")
    for index, marker in enumerate(markers):
        marker_path = f"{path}.markers[{index}]"
        ensure(isinstance(marker, dict), f"{marker_path} 必须是对象")
        exact_keys(marker, {"x", "label", "tone"}, marker_path)
        ensure({"x", "label"} <= set(marker), f"{marker_path} 缺少 x 或 label")
        ensure(isinstance(marker["x"], (int, float)) and not isinstance(marker["x"], bool) and math.isfinite(marker["x"]), f"{marker_path}.x 必须是有限数值")
        ensure(xs[0] <= marker["x"] <= xs[-1], f"{marker_path}.x 超出曲线范围")
        text_value(marker["label"], f"{marker_path}.label", 48)
        ensure(marker.get("tone", "teal") in MARKER_COLORS, f"{marker_path}.tone 不受支持")


def validate_curve_image_data(data: Any) -> dict[str, Any]:
    ensure(isinstance(data, dict), "curve-image-data 顶层必须是对象")
    exact_keys(data, {"schemaVersion", "templateVersion", "image", "conditions", "adjustables", "limitations", "panels"}, "curve-image-data")
    scan_forbidden(data)
    ensure(data.get("schemaVersion") == SCHEMA_VERSION, f"schemaVersion 必须为 {SCHEMA_VERSION}")
    ensure(data.get("templateVersion") == TEMPLATE_VERSION, f"templateVersion 必须为 {TEMPLATE_VERSION}")
    image = data.get("image")
    ensure(isinstance(image, dict), "image 必须是对象")
    exact_keys(image, {"groupKind", "title", "subtitle", "generatedAt", "objectLabel", "scopeLabel", "unitSet", "dataStatus"}, "image")
    required = {"groupKind", "title", "generatedAt", "objectLabel", "scopeLabel", "unitSet", "dataStatus"}
    ensure(required <= set(image), f"image 缺少字段: {', '.join(sorted(required - set(image)))}")
    ensure(image["groupKind"] in {"single-curve", "coupled-curve-group"}, "image.groupKind 不受支持")
    ensure(image["unitSet"] in {"SI", "MET", "ENG"}, "image.unitSet 仅支持 SI、MET 或 ENG")
    ensure(image["dataStatus"] in {"complete", "partial"}, "image.dataStatus 不受支持")
    for key, maximum in (("title", 80), ("generatedAt", 40), ("objectLabel", 120), ("scopeLabel", 160)):
        text_value(image[key], f"image.{key}", maximum)
    if "subtitle" in image:
        text_value(image["subtitle"], "image.subtitle", 160, allow_empty=True)
    conditions = data.get("conditions")
    ensure(isinstance(conditions, list) and 1 <= len(conditions) <= 12, "conditions 必须包含 1–12 项")
    for index, condition in enumerate(conditions):
        path = f"conditions[{index}]"
        ensure(isinstance(condition, dict), f"{path} 必须是对象")
        exact_keys(condition, {"label", "value", "unit", "source"}, path)
        ensure({"label", "value", "source"} <= set(condition), f"{path} 缺少必需字段")
        text_value(condition["label"], f"{path}.label", 36)
        ensure(condition["value"] is None or isinstance(condition["value"], (str, int, float, bool)), f"{path}.value 必须是标量")
        if isinstance(condition["value"], float):
            ensure(math.isfinite(condition["value"]), f"{path}.value 不能是 NaN 或无穷值")
        if isinstance(condition["value"], str):
            text_value(condition["value"], f"{path}.value", 80, allow_empty=True)
        if "unit" in condition:
            text_value(condition["unit"], f"{path}.unit", 20, allow_empty=True)
        ensure(condition["source"] in {"user-input", "automatic-default"}, f"{path}.source 不受支持")
    adjustables = data.get("adjustables")
    ensure(isinstance(adjustables, list) and 1 <= len(adjustables) <= 8, "adjustables 必须包含 1–8 项")
    for index, value in enumerate(adjustables):
        text_value(value, f"adjustables[{index}]", 100)
    limitations = data.get("limitations", [])
    ensure(isinstance(limitations, list) and len(limitations) <= 6, "limitations 最多 6 项")
    for index, value in enumerate(limitations):
        text_value(value, f"limitations[{index}]", 160)
    ensure(image["dataStatus"] != "partial" or limitations, "部分数据图片必须包含 limitations")
    panels = data.get("panels")
    ensure(isinstance(panels, list) and 1 <= len(panels) <= 2, "panels 必须包含 1–2 个同族曲线面板")
    ensure(image["groupKind"] != "single-curve" or len(panels) == 1, "single-curve 只能包含 1 个面板")
    ensure(image["groupKind"] != "coupled-curve-group" or len(panels) == 2, "coupled-curve-group 必须包含 2 个面板")
    for index, panel in enumerate(panels):
        require_phase_pair = image["dataStatus"] == "complete" and (
            image["groupKind"] == "coupled-curve-group" or (isinstance(panel, dict) and is_binary_phase_panel(panel))
        )
        validate_panel(panel, f"panels[{index}]", require_phase_pair=require_phase_pair)
    return data


def format_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value == 0:
        return "0"
    if abs(value) < 0.001:
        return f"{value:.4e}"
    return f"{value:.4f}".rstrip("0").rstrip(".")


def format_scalar(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return format_number(value)
    return str(value)


def svg_text(x: float, y: float, value: Any, css_class: str, *, anchor: str = "start", extra: str = "") -> str:
    return f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" class="{css_class}"{extra}>{xh(value)}</text>'


def render_panel(panel: dict[str, Any], y0: float, panel_number: int) -> str:
    x0, width, height = 40.0, 1120.0, float(PANEL_HEIGHT)
    head_height = 58.0
    plot_left, plot_right = x0 + 84.0, x0 + width - 32.0
    plot_top, plot_bottom = y0 + 92.0, y0 + height - 72.0
    plot_width, plot_height = plot_right - plot_left, plot_bottom - plot_top
    xs = [float(value) for value in panel["xValues"]]
    ys = [float(value) for series in panel["series"] for value in series["values"] if value is not None]
    x_low, x_high = xs[0], xs[-1]
    y_low, y_high = min(ys), max(ys)
    if math.isclose(y_low, y_high):
        padding = max(abs(y_low) * 0.05, 1.0)
    else:
        padding = (y_high - y_low) * 0.08
    y_low, y_high = y_low - padding, y_high + padding

    def px(value: float) -> float:
        return plot_left + (value - x_low) / (x_high - x_low) * plot_width

    def py(value: float) -> float:
        return plot_top + (y_high - value) / (y_high - y_low) * plot_height

    parts = [f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" rx="10" class="panel"/>',
             f'<path d="M{x0 + 10},{y0} H{x0 + width - 10} Q{x0 + width},{y0} {x0 + width},{y0 + 10} V{y0 + head_height} H{x0} V{y0 + 10} Q{x0},{y0} {x0 + 10},{y0}" class="panel-head"/>',
             svg_text(x0 + 20, y0 + 28, f"{panel_number:02d}", "eyebrow"),
             svg_text(x0 + 56, y0 + 30, panel["title"], "panel-title")]

    legend_x = x0 + 570
    for index, series in enumerate(panel["series"]):
        lx = legend_x + (index % 3) * 175
        ly = y0 + 22 + (index // 3) * 18
        parts.append(f'<line x1="{lx}" y1="{ly}" x2="{lx + 20}" y2="{ly}" stroke="{COLORS[index]}" stroke-width="3"/>')
        parts.append(svg_text(lx + 27, ly + 4, series["name"], "legend"))

    for index in range(6):
        ratio = index / 5
        y = plot_top + ratio * plot_height
        value = y_high - ratio * (y_high - y_low)
        parts.append(f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" class="grid"/>')
        parts.append(svg_text(plot_left - 10, y + 3, format_number(value), "tick", anchor="end"))
        x = plot_left + ratio * plot_width
        x_value = x_low + ratio * (x_high - x_low)
        parts.append(svg_text(x, plot_bottom + 20, format_number(x_value), "tick", anchor="middle"))
    parts.append(f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" class="axis"/>')
    parts.append(f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" class="axis"/>')
    parts.append(svg_text((plot_left + plot_right) / 2, y0 + height - 30, f'{panel["xLabel"]} ({panel["xUnit"]})', "axis-label", anchor="middle"))
    axis_y = (plot_top + plot_bottom) / 2
    parts.append(svg_text(x0 + 20, axis_y, f'{panel["yLabel"]} ({panel["yUnit"]})', "axis-label", anchor="middle", extra=f' transform="rotate(-90 {x0 + 20:.2f} {axis_y:.2f})"'))

    for marker in panel.get("markers", []):
        marker_x = px(float(marker["x"]))
        color = MARKER_COLORS[marker.get("tone", "teal")]
        parts.append(f'<line x1="{marker_x:.2f}" y1="{plot_top}" x2="{marker_x:.2f}" y2="{plot_bottom}" stroke="{color}" stroke-width="1.5" stroke-dasharray="5 5"/>')
        parts.append(svg_text(marker_x + 4, plot_top + 12, marker["label"], "caption", extra=f' fill="{color}"'))

    for series_index, series in enumerate(panel["series"]):
        path_parts: list[str] = []
        points: list[tuple[float, float]] = []
        pen_down = False
        for x_value, y_value in zip(xs, series["values"]):
            if y_value is None:
                pen_down = False
                continue
            x, y = px(x_value), py(float(y_value))
            path_parts.append(f'{"L" if pen_down else "M"}{x:.2f},{y:.2f}')
            points.append((x, y))
            pen_down = True
        color = COLORS[series_index]
        parts.append(f'<path d="{" ".join(path_parts)}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
        if len(xs) <= 80:
            for x, y in points:
                parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.5" fill="#fff" stroke="{color}" stroke-width="1.6"/>')
    if panel.get("caption"):
        parts.append(svg_text(x0 + 20, y0 + height - 10, panel["caption"], "caption"))
    return "".join(parts)


def render_document(data: dict[str, Any], script_path: Path) -> str:
    data = validate_curve_image_data(data)
    css_path = script_path.resolve().parent.parent / "assets" / "chart" / "curve-image.css"
    ensure(css_path.is_file() and css_path.stat().st_size > 0, "缺少曲线图片固定样式")
    stylesheet = css_path.read_text(encoding="utf-8")
    logo_path = script_path.resolve().parent.parent / "assets" / "brand" / "company-logo.png"
    ensure(logo_path.is_file() and logo_path.stat().st_size > 0, "缺少公司 Logo")
    logo_data_uri = "data:image/png;base64," + base64.b64encode(logo_path.read_bytes()).decode("ascii")
    condition_rows = math.ceil(len(data["conditions"]) / 4)
    condition_height = condition_rows * 76
    header_height = 206 + condition_height
    limitations = data.get("limitations", [])
    footer_lines = len(data["adjustables"]) + len(limitations)
    footer_height = 72 + footer_lines * 20
    height = int(header_height + len(data["panels"]) * (PANEL_HEIGHT + 18) + footer_height + 40)
    image = data["image"]
    parts = [f'<rect width="{WIDTH}" height="{height}" class="background"/>',
             f'<rect x="20" y="20" width="{WIDTH - 40}" height="{height - 40}" rx="14" class="frame"/>',
             f'<rect x="20" y="20" width="{WIDTH - 40}" height="64" rx="14" class="topbar"/>',
             '<rect x="20" y="20" width="530" height="4" class="accent-brand"/><rect x="550" y="20" width="300" height="4" class="accent-cyan"/><rect x="850" y="20" width="330" height="4" class="accent-teal"/>',
             f'<image x="42" y="30" width="44" height="44" href="{logo_data_uri}" preserveAspectRatio="xMidYMid slice"/>',
             svg_text(98, 49, "辛孚科技", "brand"),
             svg_text(98, 69, "PROPDB 物性数据库", "product"),
             svg_text(40, 112, "PROPDB CURVE", "eyebrow"),
             svg_text(40, 148, image["title"], "title"),
             svg_text(40, 174, image.get("subtitle", "基于本次计算结果生成的静态曲线图片"), "subtitle"),
             svg_text(780, 112, "分析对象", "meta-label"), svg_text(1170, 112, image["objectLabel"], "meta-value", anchor="end"),
             svg_text(780, 136, "分析范围", "meta-label"), svg_text(1170, 136, image["scopeLabel"], "meta-value", anchor="end"),
             svg_text(780, 160, "单位集", "meta-label"), svg_text(1170, 160, image["unitSet"], "meta-value", anchor="end"),
             svg_text(780, 184, "生成时间", "meta-label"), svg_text(1170, 184, image["generatedAt"], "meta-value", anchor="end")]

    card_width, card_gap = 264, 16
    for index, condition in enumerate(data["conditions"]):
        row, column = divmod(index, 4)
        x = 40 + column * (card_width + card_gap)
        y = 202 + row * 76
        source_class = "source-default" if condition["source"] == "automatic-default" else "source-user"
        source_label = "自动默认" if condition["source"] == "automatic-default" else "用户输入"
        value = format_scalar(condition["value"])
        if condition.get("unit"):
            value = f'{value} {condition["unit"]}'
        parts.extend([
            f'<rect x="{x}" y="{y}" width="{card_width}" height="62" rx="8" class="condition-card"/>',
            svg_text(x + 12, y + 20, condition["label"], "condition-label"),
            svg_text(x + 12, y + 45, value, "condition-value"),
            f'<rect x="{x + card_width - 72}" y="{y + 12}" width="60" height="18" rx="9" class="{source_class}"/>',
            svg_text(x + card_width - 42, y + 25, source_label, "source-text", anchor="middle"),
        ])

    panel_y = float(header_height)
    for index, panel in enumerate(data["panels"], start=1):
        parts.append(render_panel(panel, panel_y, index))
        panel_y += PANEL_HEIGHT + 18

    footer_y = panel_y + 4
    parts.append(f'<rect x="40" y="{footer_y}" width="1120" height="{footer_height - 20}" rx="9" class="adjust-bg"/>')
    cursor = footer_y + 24
    parts.append(svg_text(58, cursor, "可调整项", "adjust-title"))
    for value in data["adjustables"]:
        cursor += 20
        parts.append(svg_text(58, cursor, f"• {value}", "adjust-text"))
    if limitations:
        cursor += 28
        parts.append(svg_text(58, cursor, "适用性说明", "adjust-title"))
        for value in limitations:
            cursor += 20
            parts.append(svg_text(58, cursor, f"• {value}", "warning-text"))

    digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    title = xh(image["title"])
    description = xh(image.get("subtitle") or image["scopeLabel"])
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- template={TEMPLATE_VERSION}; data-sha256={digest} -->\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="curve-title curve-description">'
        f'<title id="curve-title">{title}</title><desc id="curve-description">{description}</desc><style>{stylesheet}</style>{"".join(parts)}</svg>\n'
    )


def self_check(script_path: Path) -> None:
    ensure(sys.version_info >= (3, 9), "需要 Python 3.9+")
    root = script_path.resolve().parent.parent / "assets" / "chart"
    ensure((root / "curve-image.css").is_file(), "缺少曲线图片样式")
    ensure((root / "curve-image-data.schema.json").is_file(), "缺少曲线图片数据合同")
    logo_path = script_path.resolve().parent.parent / "assets" / "brand" / "company-logo.png"
    ensure(logo_path.is_file() and logo_path.stat().st_size > 0, "缺少公司 Logo")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render PROPDB curve-image-data v1.0 as standalone SVG")
    parser.add_argument("--input", default="-", help="UTF-8 curve-image-data JSON file, or - for stdin")
    parser.add_argument("--output", type=Path, help="Output .svg file")
    parser.add_argument("--check-only", action="store_true", help="Validate curve-image-data without writing")
    parser.add_argument("--self-check", action="store_true", help="Check Python and bundled assets")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.self_check:
            self_check(Path(__file__))
            print(f"OK: PROPDB curve image renderer {TEMPLATE_VERSION}; Python {sys.version_info.major}.{sys.version_info.minor}; standard library only")
            return 0
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        data = validate_curve_image_data(json.loads(raw))
        if args.check_only:
            print(f"OK: curve-image-data conforms to schema {SCHEMA_VERSION}")
            return 0
        ensure(args.output is not None, "未使用 --check-only 时必须提供 --output")
        ensure(args.output.suffix.casefold() == ".svg", "--output 必须使用 .svg 扩展名")
        ensure(not args.output.exists(), "输出文件已存在；请使用新的文件名")
        document = render_document(data, Path(__file__))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8", newline="\n")
        print(f"Rendered: {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, CurveImageDataError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
