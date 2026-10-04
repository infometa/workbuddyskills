#!/usr/bin/env python3
"""Build deterministic layout JSON from a validated content-state (v1 or v2)."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
try:
    from validate_content_state import validate_state
except ImportError:
    from scripts.validate_content_state import validate_state

ALLOWED_TYPES = {"authoritative", "visual", "digest", "synthesis"}
GEO_KEYS = ("x", "y", "w", "h", "x1", "y1", "x2", "y2")


def _resolve_path(value: str, base_dir: Path) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return str(path.resolve())


def _load_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"state file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid state JSON: {exc}") from exc
    errors = validate_state(state, path.parent, check_files=True)
    if errors:
        raise ValueError("content-state invalid: " + "; ".join(errors))
    return state


def _template_value_map(state: dict[str, Any], state_path: Path) -> dict[str, str]:
    photo = state["primary_photo"]
    photo_path = photo.get("path", "")
    resolved_photo = _resolve_path(photo_path, state_path.parent) if photo_path else ""
    sub = state.get("sub_headline") or {}
    return {
        "masthead": state["masthead"]["text"],
        "date": state["date"]["text"],
        "headline": state["headline"]["original"],
        "sub_headline": sub.get("text", "") if isinstance(sub, dict) else "",
        "primary_photo_path": resolved_photo,
    }


def _replace_tokens(value: Any, values: dict[str, str]) -> Any:
    if isinstance(value, str):
        result = value
        for token, replacement in values.items():
            result = result.replace("{" + token + "}", replacement)
        return result
    if isinstance(value, list):
        return [_replace_tokens(item, values) for item in value]
    if isinstance(value, dict):
        return {key: _replace_tokens(item, values) for key, item in value.items()}
    return value


def _load_template(template_type: str) -> dict[str, Any]:
    if template_type not in ALLOWED_TYPES:
        raise ValueError(f"unknown template type: {template_type}")
    path = TEMPLATES_DIR / f"{template_type}.json"
    try:
        template = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"template not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid template JSON: {path}: {exc}") from exc
    if not isinstance(template.get("layers"), list) or not template["layers"]:
        raise ValueError(f"template has no layers: {path}")
    return template


def _eval_expression(expression: str, variables: dict[str, int | float], where: str) -> int | float:
    """Evaluate a template coordinate expression like '=photo_bottom + 40'.

    Only literals, the four basic operations, unary minus/plus and known
    variable names are allowed. Anything else is an error, never a fallback.
    """
    source = expression.strip()
    if not source.startswith("="):
        raise ValueError(f"{where}: expression must start with '=': {expression!r}")
    tree = ast.parse(source[1:], mode="eval")

    def visit(node: ast.AST) -> int | float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv)):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            return left // right
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = visit(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            available = ", ".join(sorted(variables))
            raise ValueError(f"{where}: unknown variable {node.id!r}; available: {available}")
        raise ValueError(f"{where}: unsupported expression element in {expression!r}")

    return visit(tree)


def _expression_variables(layers: list[dict[str, Any]]) -> dict[str, int | float]:
    """Derive named geometry anchors from layers that use static numeric values."""
    variables: dict[str, int | float] = {"canvas_w": 1080, "canvas_h": 1920}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        field = layer.get("field")
        if layer.get("type") == "image" and field == "primary_photo.path":
            x, y, w, h = layer.get("x"), layer.get("y"), layer.get("w"), layer.get("h")
            if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (x, y, w, h)):
                variables.update(photo_top=y, photo_bottom=y + h, photo_w=w, photo_h=h)
        if layer.get("type") == "text" and field == "headline.original":
            y = layer.get("y")
            size, lines, spacing = layer.get("size"), layer.get("max_lines", 1), layer.get("line_spacing", 0)
            if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (y, size, lines)):
                variables.update(headline_top=y, headline_bottom=y + size * lines + spacing * (lines - 1))
    return variables


def _resolve_expressions(layers: list[dict[str, Any]], variables: dict[str, int | float]) -> None:
    for index, layer in enumerate(layers):
        where = f"layer[{index}]"
        for key in GEO_KEYS:
            value = layer.get(key)
            if isinstance(value, str) and value.strip().startswith("="):
                layer[key] = _eval_expression(value, variables, f"{where}.{key}")


def _resolve_item_list(layer: dict[str, Any], state: dict[str, Any]) -> dict[str, Any] | None:
    """Attach the selected, weight-sorted items to an item_list layer.

    Returns None when the layer must be dropped (no items in state or none
    selected): the layout shrinks naturally instead of leaving dead space.
    """
    items = state.get("items")
    if not isinstance(items, list) or not items:
        return None
    selected = [item for item in items if isinstance(item, dict) and item.get("selected") is True]
    if not selected:
        return None
    selected.sort(key=lambda item: (-(item.get("weight") or 0), item.get("id", "")))
    item_max = int(layer.get("item_max", 4))
    resolved: list[dict[str, str]] = []
    for item in selected[: max(0, item_max)]:
        entry = {"headline": str(item.get("headline", ""))}
        summary = item.get("summary")
        entry["summary"] = str(summary) if isinstance(summary, str) else ""
        if not entry["headline"].strip():
            raise ValueError(f"item_list: selected item {item.get('id', '?')} has an empty headline")
        resolved.append(entry)
    if not resolved:
        return None
    layer["items"] = resolved
    return layer


def build_layout(state: dict[str, Any], state_path: Path, template_type: str) -> dict[str, Any]:
    template = _load_template(template_type)
    values = _template_value_map(state, state_path)
    layers: list[dict[str, Any]] = []
    for original_layer in template["layers"]:
        layer = _replace_tokens(original_layer, values)
        if layer.get("type") == "image":
            photo = state["primary_photo"]
            layer["focal_point"] = photo.get("focal_point", {"x": 0.5, "y": 0.5})
            if not values["primary_photo_path"]:
                layers.append({
                    "type": "rect",
                    "x": layer.get("x", 0),
                    "y": layer.get("y", 0),
                    "w": layer.get("w", 100),
                    "h": layer.get("h", 100),
                    "fill": "#f5f5f5",
                    "outline": "#cccccc",
                    "label": layer.get("placeholder", "图片占位"),
                    "label_size": 30,
                    "label_max_width": max(100, layer.get("w", 100) - 40),
                })
            else:
                layers.append(layer)
        elif layer.get("type") == "item_list":
            resolved = _resolve_item_list(layer, state)
            if resolved is not None:
                layers.append(resolved)
        elif layer.get("type") == "text" and not layer.get("text", ""):
            continue
        else:
            layers.append(layer)

    _resolve_expressions(layers, _expression_variables(layers))

    return {
        "schema_version": "layout.v1",
        "template": template_type,
        "revision_id": state["revision_id"],
        "source_state_revision": state["revision_id"],
        "canvas": {"width": 1080, "height": 1920},
        "background": template.get("background", "#FFFFFF"),
        "layers": layers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Tietu Toutiao layout JSON")
    parser.add_argument("--state", "--summary", dest="state", required=True, help="content-state JSON path (v1 or v2)")
    parser.add_argument("--type", required=True, choices=sorted(ALLOWED_TYPES), help="template type")
    parser.add_argument("--output", required=True, help="output layout.v1 JSON path")
    args = parser.parse_args()

    try:
        state_path = Path(args.state).resolve()
        state = _load_state(state_path)
        layout = build_layout(state, state_path, args.type)
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] layout.v1 generated: {output_path} ({args.type})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
