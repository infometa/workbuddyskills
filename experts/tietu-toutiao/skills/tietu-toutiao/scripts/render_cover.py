#!/usr/bin/env python3
"""Render layout.v1 as a deterministic 1080x1920 RGB PNG."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    print(f"[ERROR] Pillow is required. Install with: python -m pip install -r requirements.txt ({exc})")
    sys.exit(2)

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
LONG_TEXT_THRESHOLD = 12  # characters; longer text starts at 0.85x size on a two-line path
WINDOWS_FONT_DIR = Path("C:/Windows/Fonts")
FONT_CANDIDATES = [
    WINDOWS_FONT_DIR / "simhei.ttf",
    WINDOWS_FONT_DIR / "msyh.ttc",
    WINDOWS_FONT_DIR / "msyhbd.ttc",
    WINDOWS_FONT_DIR / "simsun.ttc",
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
]


def _font_has_cjk_glyphs(font: ImageFont.FreeTypeFont, size: int) -> bool:
    for char in ("民", "报", "头", "条"):
        bbox = font.getbbox(char)
        if bbox is None or bbox[2] - bbox[0] < max(8, size * 0.45):
            return False
    return True


def load_font(size: int, font_path: str | None = None) -> ImageFont.FreeTypeFont:
    """Load a real CJK font; never silently fall back to Pillow's bitmap font."""
    candidates = [Path(font_path)] if font_path else FONT_CANDIDATES
    failures: list[str] = []
    for path in candidates:
        if not path or not path.is_file():
            continue
        try:
            font = ImageFont.truetype(str(path), size)
            if _font_has_cjk_glyphs(font, size):
                return font
            failures.append(f"{path}: no usable CJK glyphs")
        except OSError as exc:
            failures.append(f"{path}: {exc}")
    searched = ", ".join(str(path) for path in candidates if path)
    detail = "; ".join(failures)
    raise RuntimeError(f"no usable Chinese font found; searched [{searched}]. {detail}")


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).splitlines() or [""]:
        current = ""
        for char in paragraph:
            candidate = current + char
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if current and bbox[2] - bbox[0] > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        lines.append(current)
    return lines or [""]


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    size: int,
    min_size: int,
    max_width: int,
    max_lines: int,
    font_path: str | None = None,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    if not str(text).strip():
        return load_font(max(min_size, 12), font_path), []
    # Long-text strategy: skip the initial full-size attempts and start at 0.85x
    # so a long headline wraps onto two lines instead of stretching edge to edge.
    if len(str(text)) > LONG_TEXT_THRESHOLD and max_lines >= 2:
        size = max(min_size, int(size * 0.85))
    for candidate_size in range(size, min_size - 1, -1):
        font = load_font(candidate_size, font_path)
        lines = _wrap_lines(draw, text, font, max_width)
        widths = [draw.textbbox((0, 0), line, font=font)[2] for line in lines]
        if len(lines) <= max_lines and all(width <= max_width for width in widths):
            return font, lines
    raise ValueError(f"text cannot fit: {text!r} within {max_width}px and {max_lines} line(s)")


def _fit_crop(image: Image.Image, width: int, height: int, focal_point: dict[str, Any] | None) -> Image.Image:
    if width <= 0 or height <= 0:
        raise ValueError("image target dimensions must be positive")
    image = image.convert("RGB")
    scale = max(width / image.width, height / image.height)
    resized = image.resize((max(width, round(image.width * scale)), max(height, round(image.height * scale))), Image.Resampling.LANCZOS)
    point = focal_point or {"x": 0.5, "y": 0.5}
    fx = min(1.0, max(0.0, float(point.get("x", 0.5))))
    fy = min(1.0, max(0.0, float(point.get("y", 0.5))))
    left_space = resized.width - width
    top_space = resized.height - height
    left = min(left_space, max(0, round(left_space * fx)))
    top = min(top_space, max(0, round(top_space * fy)))
    return resized.crop((left, top, left + width, top + height))


def _line_height(font: ImageFont.FreeTypeFont, line_spacing: int) -> int:
    return max(font.getbbox("民")[3] - font.getbbox("民")[1], font.size) + line_spacing


def _draw_text_layer(draw: ImageDraw.ImageDraw, layer: dict[str, Any], width: int, height: int, font_path: str | None) -> None:
    text = str(layer.get("text", ""))
    if not text.strip():
        return
    x = int(layer.get("x", 0))
    y = int(layer.get("y", 0))
    max_width = int(layer.get("max_width", width - x - 40))
    max_lines = int(layer.get("max_lines", 3))
    size = int(layer.get("size", 48))
    min_size = int(layer.get("min_size", max(16, size // 2)))
    line_spacing = int(layer.get("line_spacing", 6))
    if x < 0 or y < 0 or max_width <= 0 or x + max_width > width:
        raise ValueError(f"text layer outside canvas: {layer}")
    font, lines = fit_text(draw, text, size, min_size, max_width, max_lines, font_path)
    line_height = _line_height(font, line_spacing)
    for index, line in enumerate(lines):
        line_y = y + index * line_height
        bbox = draw.textbbox((x, line_y), line, font=font)
        if bbox[2] > x + max_width or bbox[3] > height:
            raise ValueError(f"text layer overflow: {text!r}")
        draw.text((x, line_y), line, fill=layer.get("color", "#000000"), font=font)


def _draw_rect_layer(draw: ImageDraw.ImageDraw, layer: dict[str, Any], width: int, height: int, font_path: str | None) -> None:
    x = int(layer.get("x", 0))
    y = int(layer.get("y", 0))
    w = int(layer.get("w", 100))
    h = int(layer.get("h", 100))
    if x < 0 or y < 0 or x + w > width or y + h > height:
        raise ValueError(f"rectangle outside canvas: {layer}")
    draw.rectangle([x, y, x + w, y + h], fill=layer.get("fill", "#000000"), outline=layer.get("outline"))
    label = str(layer.get("label", ""))
    if label:
        label_width = int(layer.get("label_max_width", max(80, w - 40)))
        font, lines = fit_text(draw, label, int(layer.get("label_size", 30)), 16, label_width, 3, font_path)
        line_height = max(font.size, font.getbbox("民")[3] - font.getbbox("民")[1]) + 4
        total_height = len(lines) * line_height
        for index, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tx = x + max(0, (w - (bbox[2] - bbox[0])) // 2)
            ty = y + max(0, (h - total_height) // 2 + index * line_height)
            draw.text((tx, ty), line, fill="#666666", font=font)


def _draw_item_list_layer(draw: ImageDraw.ImageDraw, layer: dict[str, Any], width: int, height: int, font_path: str | None) -> None:
    """Draw the selected news items: headline + wrapped summary per entry.

    Items were resolved by the layout engine (selected, weight-sorted, top
    item_max). Each entry takes only the height it needs; when there are fewer
    items the block simply ends higher -- no dead space, no placeholders.
    """
    items = layer.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("item_list layer reached the renderer without resolved items")
    x = int(layer.get("x", 0))
    y = int(layer.get("y", 0))
    block_width = int(layer.get("w", width - x - 40))
    if x < 0 or y < 0 or block_width <= 0 or x + block_width > width:
        raise ValueError(f"item_list layer outside canvas: {layer}")
    headline_size = int(layer.get("headline_size", 40))
    headline_min_size = int(layer.get("headline_min_size", max(16, headline_size // 2)))
    headline_color = layer.get("headline_color", "#1a1a1a")
    summary_size = int(layer.get("summary_size", 28))
    summary_min_size = int(layer.get("summary_min_size", max(14, summary_size // 2)))
    summary_color = layer.get("summary_color", "#666666")
    summary_max_lines = int(layer.get("summary_max_lines", 2))
    item_spacing = int(layer.get("item_spacing", 36))
    divider = bool(layer.get("divider", False))
    divider_color = layer.get("divider_color", "#e0e0e0")
    number_style = layer.get("number_style", "bullet")

    cursor = y
    for index, item in enumerate(items):
        headline = str(item.get("headline", ""))
        summary = str(item.get("summary", "")).strip()
        if not headline.strip():
            raise ValueError(f"item_list entry {index} has an empty headline")
        prefix = f"{index + 1}. " if number_style == "number" else "· "
        prefix_width = draw.textbbox((0, 0), prefix, font=load_font(headline_size, font_path))[2]
        font, headline_lines = fit_text(
            draw, headline, headline_size, headline_min_size, block_width - prefix_width, 1, font_path
        )
        line_height = _line_height(font, 4)
        line_y = cursor
        draw.text((x, line_y), prefix, fill=headline_color, font=load_font(headline_size, font_path))
        draw.text((x + prefix_width, line_y), headline_lines[0], fill=headline_color, font=font)
        if draw.textbbox((x + prefix_width, line_y), headline_lines[0], font=font)[2] > x + block_width:
            raise ValueError(f"item_list headline overflow: {headline!r}")
        cursor += line_height
        if summary:
            summary_font, summary_lines = fit_text(
                draw, summary, summary_size, summary_min_size, block_width, summary_max_lines, font_path
            )
            summary_height = _line_height(summary_font, 4)
            if cursor + summary_height * len(summary_lines) > height:
                raise ValueError(f"item_list summary overflow at item {index}: {summary!r}")
            for summary_line in summary_lines:
                draw.text((x + prefix_width, cursor), summary_line, fill=summary_color, font=summary_font)
                cursor += summary_height
        cursor += item_spacing
        if divider and index < len(items) - 1:
            draw.line([(x, cursor - item_spacing // 2), (x + block_width, cursor - item_spacing // 2)], fill=divider_color, width=2)
    if cursor - item_spacing > height:
        raise ValueError(f"item_list block exceeds canvas: ends at {cursor}")


def render_cover(layout_path: Path, output_path: Path, font_path: str | None = None) -> None:
    try:
        spec = json.loads(layout_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"layout file not found: {layout_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid layout JSON: {exc}") from exc

    if spec.get("schema_version") != "layout.v1":
        raise ValueError("layout schema_version must equal layout.v1")
    canvas_spec = spec.get("canvas", {})
    if canvas_spec.get("width") != CANVAS_WIDTH or canvas_spec.get("height") != CANVAS_HEIGHT:
        raise ValueError("layout canvas must be exactly 1080x1920")
    layers = spec.get("layers")
    if not isinstance(layers, list) or not layers:
        raise ValueError("layout must contain layers")

    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), spec.get("background", "#FFFFFF"))
    draw = ImageDraw.Draw(canvas)
    for layer in layers:
        layer_type = layer.get("type")
        if layer_type == "text":
            _draw_text_layer(draw, layer, CANVAS_WIDTH, CANVAS_HEIGHT, font_path)
        elif layer_type == "image":
            src = str(layer.get("src", ""))
            image_path = Path(src)
            if not src or not image_path.is_file():
                if layer.get("allow_placeholder"):
                    _draw_rect_layer(draw, {**layer, "type": "rect", "label": layer.get("placeholder", "图片占位"), "fill": "#f5f5f5", "outline": "#cccccc"}, CANVAS_WIDTH, CANVAS_HEIGHT, font_path)
                    continue
                raise ValueError(f"image source not found: {src}")
            with Image.open(image_path) as source:
                image = _fit_crop(source, int(layer["w"]), int(layer["h"]), layer.get("focal_point"))
            x = int(layer.get("x", 0))
            y = int(layer.get("y", 0))
            if x < 0 or y < 0 or x + image.width > CANVAS_WIDTH or y + image.height > CANVAS_HEIGHT:
                raise ValueError(f"image layer outside canvas: {layer}")
            canvas.paste(image, (x, y))
        elif layer_type == "rect":
            _draw_rect_layer(draw, layer, CANVAS_WIDTH, CANVAS_HEIGHT, font_path)
        elif layer_type == "line":
            x1, y1 = int(layer.get("x1", 0)), int(layer.get("y1", 0))
            x2, y2 = int(layer.get("x2", 0)), int(layer.get("y2", 0))
            if min(x1, y1, x2, y2) < 0 or max(x1, x2) > CANVAS_WIDTH or max(y1, y2) > CANVAS_HEIGHT:
                raise ValueError(f"line layer outside canvas: {layer}")
            draw.line([(x1, y1), (x2, y2)], fill=layer.get("color", "#000000"), width=int(layer.get("width", 2)))
        elif layer_type == "item_list":
            _draw_item_list_layer(draw, layer, CANVAS_WIDTH, CANVAS_HEIGHT, font_path)
        else:
            raise ValueError(f"unsupported layer type: {layer_type}")

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    canvas.save(temporary, "PNG")
    temporary.replace(output_path)
    print(f"[OK] cover generated: {output_path} ({CANVAS_WIDTH}x{CANVAS_HEIGHT})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Tietu Toutiao layout.v1")
    parser.add_argument("--input", required=True, help="layout.v1 JSON path")
    parser.add_argument("--output", required=True, help="output PNG path")
    parser.add_argument("--font-path", help="explicit CJK font file path")
    args = parser.parse_args()
    try:
        render_cover(Path(args.input), Path(args.output), args.font_path)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
