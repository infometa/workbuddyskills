#!/usr/bin/env python3
"""Render a self-contained, escaped HTML writing review report from JSON."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def require_non_empty_string(value: Any, field_path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_path} must be a non-empty string")


def validate_object_items(
    items: list[Any],
    item_name: str,
    required_fields: tuple[str, ...],
    allow_empty: bool = True,
) -> None:
    if not allow_empty and not items:
        raise ValueError(f"{item_name} must contain at least one item")
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{item_name}[{index}] must be an object")
        for field in required_fields:
            require_non_empty_string(item.get(field), f"{item_name}[{index}].{field}")


def validate_data(data: dict[str, Any]) -> None:
    if data.get("schema_version") != "1.0":
        raise ValueError("schema_version must be '1.0'")
    if data.get("report_type") != "exam_review":
        raise ValueError("report_type must be 'exam_review'")
    for field in ("title", "summary"):
        require_non_empty_string(data.get(field), field)
    for field in ("meta", "score"):
        if not isinstance(data.get(field), dict):
            raise ValueError(f"{field} must be an object")
    for field in ("evidence", "issues", "actions"):
        if not isinstance(data.get(field), list):
            raise ValueError(f"{field} must be an array")

    score = data["score"]
    require_non_empty_string(score.get("band"), "score.band")
    for field in ("raw", "deduction", "final", "maximum"):
        value = score.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"score.{field} must be a number")
    raw = float(score["raw"])
    deduction = float(score["deduction"])
    final = float(score["final"])
    maximum = float(score["maximum"])
    if not all(math.isfinite(value) for value in (raw, deduction, final, maximum)):
        raise ValueError("score values must be finite numbers")
    if maximum <= 0 or not 0 <= raw <= maximum:
        raise ValueError("score.raw must be between 0 and score.maximum")
    if not 0 <= deduction <= raw:
        raise ValueError("score.deduction must be between 0 and score.raw")
    expected = max(0.0, raw - deduction)
    if abs(final - expected) > 1e-9:
        raise ValueError("score.final must equal max(0, score.raw - score.deduction)")

    validate_object_items(
        data["evidence"],
        "evidence",
        ("claim", "quote", "reason"),
        allow_empty=False,
    )
    validate_object_items(
        data["issues"],
        "issues",
        ("priority", "location", "original", "suggestion", "reason"),
    )
    if not data["actions"]:
        raise ValueError("actions must contain at least one item")
    for index, item in enumerate(data["actions"]):
        require_non_empty_string(item, f"actions[{index}]")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Input JSON not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read input JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Input JSON root must be an object")
    validate_data(data)
    return data


def render(data: dict[str, Any]) -> str:
    title = esc(data.get("title", "英语写作反馈报告"))
    summary = esc(data.get("summary", ""))
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    score = data.get("score") if isinstance(data.get("score"), dict) else {}
    evidence = data.get("evidence") if isinstance(data.get("evidence"), list) else []
    issues = data.get("issues") if isinstance(data.get("issues"), list) else []
    actions = data.get("actions") if isinstance(data.get("actions"), list) else []

    meta_html = "".join(
        f'<div class="chip"><span>{esc(key)}</span><strong>{esc(value)}</strong></div>'
        for key, value in meta.items()
    )
    score_html = "".join(
        f'<div class="score-item"><span>{esc(key)}</span><strong>{esc(value)}</strong></div>'
        for key, value in score.items()
    )
    evidence_html = "".join(
        '<article class="card">'
        f'<h3>{esc(item.get("claim", "证据"))}</h3>'
        f'<blockquote>{esc(item.get("quote", ""))}</blockquote>'
        f'<p>{esc(item.get("reason", ""))}</p>'
        '</article>'
        for item in evidence if isinstance(item, dict)
    )
    issues_html = "".join(
        '<article class="card issue">'
        f'<div class="priority">{esc(item.get("priority", ""))} · {esc(item.get("location", ""))}</div>'
        f'<p><b>原句：</b>{esc(item.get("original", ""))}</p>'
        f'<p><b>建议：</b>{esc(item.get("suggestion", ""))}</p>'
        f'<p><b>原因：</b>{esc(item.get("reason", ""))}</p>'
        '</article>'
        for item in issues if isinstance(item, dict)
    )
    actions_html = "".join(f"<li>{esc(item)}</li>" for item in actions)

    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#f7f8fc;--card:#fff;--ink:#1d2433;--muted:#657086;--accent:#7652d6;--line:#e4e7ef}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:920px;margin:0 auto;padding:40px 20px 64px}}header{{background:linear-gradient(135deg,#7652d6,#b14d9c);color:#fff;padding:30px;border-radius:18px}}
h1{{margin:0 0 10px;font-size:28px}}h2{{margin:34px 0 14px;font-size:20px}}h3{{margin:0 0 10px;font-size:16px}}
.meta,.score{{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}}.chip,.score-item{{background:rgba(255,255,255,.14);padding:8px 12px;border-radius:10px}}
.chip span,.score-item span{{margin-right:8px;opacity:.78}}.panel,.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:12px 0;box-shadow:0 5px 18px rgba(32,38,57,.05)}}
blockquote{{margin:10px 0;padding:10px 14px;border-left:4px solid var(--accent);background:#f7f4ff}}.priority{{color:var(--accent);font-weight:700}}ul{{padding-left:22px}}footer{{margin-top:36px;color:var(--muted);font-size:13px}}
</style>
</head>
<body><main>
<header><h1>{title}</h1><div class="meta">{meta_html}</div><div class="score">{score_html}</div></header>
<h2>整体判断</h2><section class="panel">{summary}</section>
<h2>评分证据</h2>{evidence_html or '<section class="panel">本报告未提供证据项。</section>'}
<h2>优先问题</h2>{issues_html or '<section class="panel">本报告未提供问题项。</section>'}
<h2>下一步动作</h2><section class="panel"><ul>{actions_html}</ul></section>
<footer>本报告用于学习反馈，不等于官方考试成绩。内容由本地模板生成，不加载外部资源。</footer>
</main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an English writing review HTML report")
    parser.add_argument("input", help="Input review JSON")
    parser.add_argument("--output", required=True, help="New HTML output file")
    args = parser.parse_args()

    output = Path(args.output)
    try:
        rendered = render(load_json(Path(args.input)))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            handle.write(rendered)
    except FileExistsError:
        parser.error(f"Output file already exists: {output}")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
