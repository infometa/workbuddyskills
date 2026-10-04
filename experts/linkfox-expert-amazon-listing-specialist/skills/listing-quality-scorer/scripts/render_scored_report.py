#!/usr/bin/env python3
"""Render an HTML quality report only after canonical scores are present."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _load_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise ValueError("HTML-ready JSON 顶层必须是对象")
    return value


def _record_panels(
    record: dict[str, Any], location: str, inherited_panel: Any
) -> list[tuple[str, Any]]:
    record_panel = record.get("scorePanel") or inherited_panel
    for variants_key in ("listings", "listingVariants", "versions", "variants"):
        variants = record.get(variants_key)
        if not isinstance(variants, list) or not variants:
            continue
        panels: list[tuple[str, Any]] = []
        for variant_index, variant in enumerate(variants):
            variant_panel = variant.get("scorePanel") if isinstance(variant, dict) else None
            panels.append((
                f"{location}{variants_key}[{variant_index}].scorePanel",
                variant_panel or record_panel,
            ))
        return panels
    return [(f"{location}scorePanel", record_panel)]


def _primary_panels(payload: dict[str, Any]) -> list[tuple[str, Any]]:
    """Return the effective panel used by every renderable product/version."""
    root_panel = payload.get("scorePanel")
    products = payload.get("products")
    if not isinstance(products, list) or not products:
        return _record_panels(payload, "", root_panel)

    panels: list[tuple[str, Any]] = []
    for product_index, product in enumerate(products):
        location = f"products[{product_index}]."
        if not isinstance(product, dict):
            panels.append((f"{location}scorePanel", None))
            continue
        panels.extend(_record_panels(product, location, root_panel))
    return panels


def validate_scored_report(payload: dict[str, Any]) -> None:
    errors: list[str] = []
    for location, panel in _primary_panels(payload):
        if not isinstance(panel, dict):
            errors.append(f"{location} 缺失")
            continue
        overall = panel.get("overall")
        if (
            not isinstance(overall, (int, float))
            or isinstance(overall, bool)
            or not 0 <= overall <= 100
        ):
            errors.append(f"{location}.overall 必须是 0-100 的 canonical 数字评分")
        if not str(panel.get("grade") or "").strip() or panel.get("grade") == "—":
            errors.append(f"{location}.grade 缺少 canonical 等级")
        if panel.get("insufficientData") is True:
            errors.append(f"{location}.insufficientData=true，不能生成评分报告")
        if not isinstance(panel.get("items"), list) or not panel["items"]:
            errors.append(f"{location}.items 必须是非空评分维度数组")
    if errors:
        raise ValueError("；".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 canonical score 后调用 Listing HTML renderer")
    parser.add_argument("--input", required=True, help="HTML-ready JSON 绝对路径")
    parser.add_argument("--renderer", required=True, help="render-and-validate-agent-listing.mjs 绝对路径")
    parser.add_argument("--output", required=True, help="HTML 输出绝对路径")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    renderer_path = Path(args.renderer).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    try:
        payload = _load_object(input_path)
        validate_scored_report(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            f"评分报告前置校验失败: {exc}。请先调用 listing-quality-scorer，"
            "并把其 scorePanel 合并到 HTML-ready JSON；禁止用 overall=null 的 Core 占位面板渲染。",
            file=sys.stderr,
        )
        return 2

    if not renderer_path.is_file():
        print(f"评分报告前置校验失败: renderer 不存在: {renderer_path}", file=sys.stderr)
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["node", str(renderer_path), str(input_path), str(output_path)],
        text=True,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
