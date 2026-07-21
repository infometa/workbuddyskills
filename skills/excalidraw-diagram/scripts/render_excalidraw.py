from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_diagram(path: Path) -> dict:
    if not path.exists():
        fail(f"File not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {exc}")


def validate_diagram(data: dict) -> None:
    if data.get("type") != "excalidraw":
        fail("Top-level field 'type' must be 'excalidraw'.")
    elements = data.get("elements")
    if not isinstance(elements, list):
        fail("Top-level field 'elements' must be an array.")
    if not elements:
        fail("Diagram contains no elements.")


def element_bounds(element: dict) -> tuple[float, float, float, float]:
    x = float(element.get("x", 0))
    y = float(element.get("y", 0))
    width = abs(float(element.get("width", 0)))
    height = abs(float(element.get("height", 0)))

    if element.get("type") in {"arrow", "line"} and isinstance(element.get("points"), list) and element["points"]:
        xs = [x + float(point[0]) for point in element["points"]]
        ys = [y + float(point[1]) for point in element["points"]]
        return min(xs), min(ys), max(xs), max(ys)

    return x, y, x + width, y + height


def compute_viewport(elements: list[dict], max_width: int) -> tuple[int, int]:
    active = [el for el in elements if not el.get("isDeleted")]
    if not active:
        return 1200, 800

    min_x = min(element_bounds(el)[0] for el in active)
    min_y = min(element_bounds(el)[1] for el in active)
    max_x = max(element_bounds(el)[2] for el in active)
    max_y = max(element_bounds(el)[3] for el in active)

    padding = 96
    width = int(max_x - min_x + padding * 2)
    height = int(max_y - min_y + padding * 2)
    width = max(800, min(width, max_width))
    height = max(600, height)
    return width, height


def expand_viewport_if_needed(page, svg, viewport_width: int, viewport_height: int, max_width: int) -> tuple[int, int]:
    box = svg.bounding_box()
    if not box:
        return viewport_width, viewport_height

    target_width = max(viewport_width, int(box["x"] + box["width"] + 64))
    target_height = max(viewport_height, int(box["y"] + box["height"] + 64))
    target_width = min(target_width, max_width)

    if target_width != viewport_width or target_height != viewport_height:
        page.set_viewport_size({"width": target_width, "height": target_height})

    return target_width, target_height


def render(diagram_path: Path, output_path: Path | None, scale: int, max_width: int) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail("playwright is not installed. Run 'uv sync --project {baseDir}/scripts' first.")

    data = load_diagram(diagram_path)
    validate_diagram(data)

    output = output_path or diagram_path.with_suffix(".png")
    template = Path(__file__).with_name("render_template.html")
    if not template.exists():
        fail(f"Render template not found: {template}")

    viewport_width, viewport_height = compute_viewport(data["elements"], max_width)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": viewport_width, "height": viewport_height},
            device_scale_factor=scale,
        )
        page.goto(template.as_uri())
        page.wait_for_function("window.__moduleReady === true", timeout=30000)

        result = page.evaluate("payload => window.renderExcalidraw(payload)", data)
        if not result or not result.get("ok"):
            browser.close()
            fail(result.get("error", "Unknown render failure") if result else "Renderer returned empty result")

        page.wait_for_function("window.__renderDone === true", timeout=30000)
        svg = page.query_selector("#root svg")
        if svg is None:
            browser.close()
            fail("No SVG element produced by renderer.")

        expand_viewport_if_needed(page, svg, viewport_width, viewport_height, max_width)
        svg = page.query_selector("#root svg")
        if svg is None:
            browser.close()
            fail("No SVG element produced after viewport resize.")

        svg.screenshot(path=str(output))
        browser.close()

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Excalidraw JSON to PNG")
    parser.add_argument("input", type=Path, help="Path to .excalidraw file")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output PNG path")
    parser.add_argument("--scale", "-s", type=int, default=2, help="Device scale factor")
    parser.add_argument("--width", "-w", type=int, default=6000, help="Max viewport width")
    args = parser.parse_args()

    output = render(args.input, args.output, args.scale, args.width)
    print(output)


if __name__ == "__main__":
    main()
