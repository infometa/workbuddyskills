#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_outputs.py —— 知识框架梳理 Skill · 多格式渲染器(v0.5.0)

功能:
  - 读取 result.json,从 framework_tree / node_explanations / concept_dependencies 派生:
      framework.md             —— Markdown 大纲(主资产,含顶部 warnings banner + 节点讲解折叠 + 依赖关系)
      framework.markmap.html   —— Markmap 单文件(浏览器双击即开,讲解显示在 tooltip 注释)
      framework.mermaid.md     —— Mermaid mindmap + flowchart 双视图
      framework.opml           —— OPML 2.0(可导入 XMind / 幕布,讲解写入 _note 字段)
      concept-dependencies.md  —— 仅当 concept_dependencies 非空时输出(独立 Mermaid flowchart + 表格)
  - 顶部 banner 由 result.warnings 驱动:
      level=high   → ⚠️ 红色背景(topic_only 强制)
      level=medium → 黄色提示
      level=low    → 灰色 informational(不显示在 banner,仅 result.warnings JSON)

设计原则:
  - 无第三方依赖(纯标准库)
  - Markmap 用 CDN autoloader,无需本地编译
  - 全部输出可独立分享(单文件)

用法:
  python3 scripts/render_outputs.py result.json   # 默认全 4 种 + 可选 concept-deps,输出到 result.json 同级目录
  python3 scripts/render_outputs.py \
      --result result.json \
      --formats markdown,markmap,mermaid,opml,concept_deps \
      --out-dir ./output/

退出码:
  0  渲染完成
  1  参数 / 文件错误
  2  result.json 缺关键字段
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import sys
from pathlib import Path

SCRIPT_VERSION = "0.5.0"

ALL_FORMATS = ["markdown", "markmap", "mermaid", "opml", "concept_deps"]

# 概念依赖类型 → mermaid 边样式
DEP_STYLE = {
    "prerequisite": {"arrow": "-->", "label_prefix": "先修"},
    "generalization": {"arrow": "==>", "label_prefix": "总→分"},
    "specialization": {"arrow": "==>", "label_prefix": "分→总"},
    "contrast": {"arrow": "-.->", "label_prefix": "易混"},
    "application": {"arrow": "-->", "label_prefix": "应用"},
    "tool": {"arrow": "-.->", "label_prefix": "工具"},
}


def walk_tree(node: dict, level: int = 0):
    yield node, level
    for c in node.get("children", []) or []:
        yield from walk_tree(c, level + 1)


def get_banner_lines(warnings: list[dict]) -> list[str]:
    """返回 markdown blockquote 风格的 banner 行(仅 high / medium)。"""
    out: list[str] = []
    for w in warnings or []:
        lv = w.get("level")
        if lv not in ("high", "medium"):
            continue
        icon = "⚠️" if lv == "high" else "ℹ️"
        out.append(f"> {icon} **{w.get('message', '')}**")
    return out


def get_html_banner(warnings: list[dict]) -> str:
    """Markmap HTML 顶部 banner。"""
    parts = []
    for w in warnings or []:
        lv = w.get("level")
        if lv not in ("high", "medium"):
            continue
        bg = "#fff7e6" if lv == "high" else "#e6f7ff"
        border = "#fa8c16" if lv == "high" else "#1890ff"
        color = "#874d00" if lv == "high" else "#003a8c"
        icon = "⚠️" if lv == "high" else "ℹ️"
        parts.append(
            f'<div class="banner" style="background:{bg};border-bottom:2px solid {border};color:{color};">'
            f'<span class="icon">{icon}</span> <strong>{html_lib.escape(w.get("message", ""))}</strong>'
            f"</div>"
        )
    return "\n".join(parts)


def index_explanations(result: dict) -> dict[str, dict]:
    return {e["node_id"]: e for e in (result.get("node_explanations") or [])}


# ---------- Markdown ----------

def render_markdown(result: dict) -> str:
    meta = result.get("meta", {})
    stats = result.get("tree_stats", {})
    tree = result.get("framework_tree", {})
    warnings = result.get("warnings", [])
    questions = result.get("recommended_questions", []) or []
    deps = result.get("concept_dependencies") or []
    exps = index_explanations(result)

    title = tree.get("title", meta.get("course_topic", "知识框架"))
    depth = " + ".join(meta.get("depth_used", ["skim"]))

    out: list[str] = []
    out.append(f"# {title} · 知识框架({depth} 骨架)")
    out.append("")
    if warnings:
        banner = get_banner_lines(warnings)
        if banner:
            out.extend(banner)
            out.append(">")
    out.append(f"> **生成模式**:`{meta.get('mode', 'topic_only')}` × `{depth}`")
    out.append(
        f"> **层级**:{stats.get('max_depth', 0) + 1}"
        f"(根 + {stats.get('level_counts', {}).get('1', 0)} 大模块"
        f" + {stats.get('level_counts', {}).get('2', 0)} 二级"
        f" + {stats.get('leaf_count', 0)} 叶子,共 {stats.get('total_nodes', 0)} 节点)"
    )
    if exps:
        out.append(f"> **节点讲解**:{len(exps)} 个(详见下方折叠块)")
    if deps:
        out.append(f"> **概念依赖边**:{len(deps)} 条(详见 `concept-dependencies.md` 与文末)")
    out.append(f"> **生成时间**:{meta.get('generated_at', '')[:10]}")
    out.append("")
    out.append("---")
    out.append("")

    for child in tree.get("children", []) or []:
        out.append(f"## {child.get('title')}")
        _render_node_explanation(out, child, exps)
        out.append("")
        for grand in child.get("children", []) or []:
            line = f"- **{grand.get('title')}**"
            if grand.get("id") in exps:
                line += "  📖"
            out.append(line)
            _render_node_explanation(out, grand, exps, indent=2)
            for s in grand.get("children", []) or []:
                leaf_line = f"  - {s.get('title')}"
                if s.get("id") in exps:
                    leaf_line += "  📖"
                out.append(leaf_line)
                _render_node_explanation(out, s, exps, indent=4)
        out.append("")

    if deps:
        out.append("---")
        out.append("")
        out.append(f"## 概念依赖关系({len(deps)} 条)")
        out.append("")
        out.append("> 完整 Mermaid flowchart 见 `concept-dependencies.md`。下面是按类型分组的列表。")
        out.append("")
        by_type: dict[str, list[dict]] = {}
        for d in deps:
            by_type.setdefault(d.get("type", "prerequisite"), []).append(d)
        for dtype, items in by_type.items():
            label = DEP_STYLE.get(dtype, {}).get("label_prefix", dtype)
            out.append(f"### {label}({dtype}) · {len(items)} 条")
            out.append("")
            for d in items:
                conf = d.get("confidence", "medium")
                out.append(
                    f"- `{d['from']}` → `{d['to']}`  _[{conf}]_  —— {d.get('rationale', '')}"
                )
            out.append("")

    if questions:
        out.append("---")
        out.append("")
        out.append("## AI 推荐的追问")
        out.append("")
        out.append("> 用户可基于这些追问继续向 Skill 提问,触发 `guided` 或 `deep` 模式自动升档。")
        out.append("")
        for i, q in enumerate(questions, 1):
            out.append(f"{i}. **「{q.get('q', '')}」**")
            if q.get("why"):
                out.append(f"   _why_:{q['why']}")
            out.append("")

    out.append("---")
    out.append("")
    out.append("## 下一步建议")
    out.append("")
    out.append(f"_{result.get('next_step_hint', '')}_")
    out.append("")

    return "\n".join(out)


def _render_node_explanation(out: list[str], node: dict, exps: dict, indent: int = 0) -> None:
    """如果该节点有 explanation,渲染为 <details> 折叠块。"""
    nid = node.get("id")
    exp = exps.get(nid)
    if not exp:
        return
    pad = " " * indent
    title = node.get("title", "")
    wc = exp.get("word_count", 0)
    user_level = exp.get("user_level_match", "intermediate")
    out.append(f"{pad}<details>")
    out.append(
        f"{pad}<summary>📖 <strong>{title}</strong> 的讲解 "
        f"<em>({wc} 字 · {user_level})</em></summary>"
    )
    out.append("")
    if exp.get("selection_reason"):
        out.append(f"{pad}**入选理由**:{exp['selection_reason']}")
        out.append("")
    text = exp.get("explanation", "")
    for line in text.splitlines():
        out.append(f"{pad}{line}")
    out.append("")
    drill = exp.get("drill") or {}
    if drill.get("confusables"):
        out.append(f"{pad}**易混对比**:")
        for c in drill["confusables"]:
            out.append(f"{pad}- {c}")
        out.append("")
    if drill.get("examples"):
        out.append(f"{pad}**例题/示例**:")
        for e in drill["examples"]:
            out.append(f"{pad}- `{e}`")
        out.append("")
    if exp.get("cross_ref"):
        refs = ", ".join(f"`{r}`" for r in exp["cross_ref"])
        out.append(f"{pad}**关联节点**:{refs}")
        out.append("")
    out.append(f"{pad}</details>")
    out.append("")


# ---------- Markmap HTML ----------

def render_markmap_html(result: dict) -> str:
    meta = result.get("meta", {})
    stats = result.get("tree_stats", {})
    tree = result.get("framework_tree", {})
    warnings = result.get("warnings", [])
    exps = index_explanations(result)
    title = tree.get("title", meta.get("course_topic", "知识框架"))
    depth = " + ".join(meta.get("depth_used", ["skim"]))

    md_lines: list[str] = [f"# {title}", ""]
    for child in tree.get("children", []) or []:
        suffix = " 📖" if child.get("id") in exps else ""
        md_lines.append(f"## {child.get('title')}{suffix}")
        md_lines.append("")
        for grand in child.get("children", []) or []:
            suffix = " 📖" if grand.get("id") in exps else ""
            md_lines.append(f"### {grand.get('title')}{suffix}")
            for s in grand.get("children", []) or []:
                suffix = " 📖" if s.get("id") in exps else ""
                md_lines.append(f"- {s.get('title')}{suffix}")
            md_lines.append("")
    body_md = "\n".join(md_lines)

    banner_html = get_html_banner(warnings) or ""
    n_exps = len(exps)
    n_deps = len(result.get("concept_dependencies") or [])
    extra_meta = []
    if n_exps:
        extra_meta.append(f"📖 节点讲解 {n_exps}")
    if n_deps:
        extra_meta.append(f"🔗 概念依赖 {n_deps}")
    extra_meta_str = (" · " + " · ".join(extra_meta)) if extra_meta else ""

    meta_text = (
        f"(模式 {meta.get('mode', '')} × {depth} · {stats.get('total_nodes', 0)} 节点 · "
        f"{stats.get('max_depth', 0) + 1} 层{extra_meta_str})"
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{html_lib.escape(title)} · 知识框架(Markmap)</title>
<meta name="generator" content="knowledge-framework-builder@{meta.get('skill_version', SCRIPT_VERSION)}">
<style>
  body {{ margin: 0; font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }}
  .banner {{ padding: 10px 16px; font-size: 14px; display: flex; align-items: center; gap: 10px; }}
  .banner .icon {{ font-size: 20px; }}
  .markmap {{ width: 100vw; height: calc(100vh - 50px); }}
  .footer {{ position: fixed; bottom: 8px; right: 12px;
    background: rgba(255,255,255,0.85); padding: 4px 10px; border-radius: 4px;
    font-size: 11px; color: #888; }}
</style>
</head>
<body>
{banner_html}
<div style="padding:6px 16px;color:#666;font-size:12px;border-bottom:1px solid #eee;">{meta_text}</div>
<div class="markmap">
<script type="text/template">
---
title: {html_lib.escape(title)}
markmap:
  colorFreezeLevel: 2
  initialExpandLevel: 2
  maxWidth: 320
---

{body_md}
</script>
</div>
<div class="footer">Markmap Autoloader · 浏览器双击本文件即可查看 · 📖 表示该节点有 200-500 字讲解(详见 framework.md)</div>
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@latest"></script>
</body>
</html>
"""


# ---------- Mermaid ----------

def render_mermaid(result: dict) -> str:
    meta = result.get("meta", {})
    tree = result.get("framework_tree", {})
    warnings = result.get("warnings", [])
    deps = result.get("concept_dependencies") or []
    title = tree.get("title", meta.get("course_topic", "知识框架"))

    out: list[str] = []
    out.append(f"# {title} · Mermaid Mindmap")
    out.append("")
    if warnings:
        banner = get_banner_lines(warnings)
        if banner:
            out.extend(banner)
            out.append("")
    out.append("> 在 GitHub / Notion / VSCode Mermaid 预览器中可直接渲染。")
    out.append("")
    out.append("```mermaid")
    out.append("mindmap")
    out.append(f"  root(({title}))")

    def emit(node: dict, indent: int):
        prefix = "    " * indent
        out.append(f"{prefix}{node.get('title', '')}")
        for c in node.get("children", []) or []:
            emit(c, indent + 1)

    for c in tree.get("children", []) or []:
        emit(c, 1)

    out.append("```")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 流程图视角(含概念依赖)" if deps else "## 流程图视角")
    out.append("")
    if deps:
        out.append(
            f"> 共 {len(deps)} 条依赖边,按 6 类样式区分:实线 → 先修/应用,粗实线 ⇒ 总分,虚线 ⇢ 易混/工具。"
        )
    else:
        out.append("> 当用户提供 `concept_dependency_strategy` 后,以下 flowchart 会被填充依赖箭头。")
    out.append("")
    out.append("```mermaid")
    out.append("flowchart TD")
    out.append(f"    Root[{title}]")
    used_ids: list[str] = []
    for i, c in enumerate(tree.get("children", []) or [], 1):
        nid = f"M{i}"
        used_ids.append(nid)
        title_clean = (c.get("title") or "").replace("[", "(").replace("]", ")")
        out.append(f"    {nid}[{title_clean}]")
        out.append(f"    Root --> {nid}")

    if deps:
        out.append("")
        out.append("    %% concept dependencies")
        title_by_id = {n.get("id"): n.get("title", "") for n, _ in walk_tree(tree)}
        for d in deps:
            arrow = DEP_STYLE.get(d["type"], {}).get("arrow", "-->")
            label = DEP_STYLE.get(d["type"], {}).get("label_prefix", d["type"])
            u = d["from"].replace(".", "_").replace("-", "_")
            v = d["to"].replace(".", "_").replace("-", "_")
            u_label = title_by_id.get(d["from"], d["from"])[:18]
            v_label = title_by_id.get(d["to"], d["to"])[:18]
            out.append(f"    {u}[{u_label}] {arrow}|{label}| {v}[{v_label}]")

    out.append("")
    out.append("    classDef ai_inferred fill:#fff7e6,stroke:#fa8c16,stroke-width:1px;")
    out.append(f"    class Root,{','.join(used_ids)} ai_inferred;")
    out.append("```")
    out.append("")
    if meta.get("mode") == "topic_only":
        out.append("> ⚠️ 黄色填充 = `evidence_source: ai_inference`(AI 推断,建议核对教材)。")

    return "\n".join(out) + "\n"


# ---------- OPML ----------

def render_opml(result: dict) -> str:
    meta = result.get("meta", {})
    tree = result.get("framework_tree", {})
    title = tree.get("title", meta.get("course_topic", "知识框架"))
    generated = meta.get("generated_at", "")
    exps = index_explanations(result)

    def esc_attr(s: str) -> str:
        return html_lib.escape(s or "", quote=True)

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<opml version="2.0">')
    lines.append("  <head>")
    lines.append(f"    <title>{esc_attr(title)} · 知识框架</title>")
    lines.append("    <ownerName>knowledge-framework-builder</ownerName>")
    lines.append(f"    <generator>knowledge-framework-builder@{meta.get('skill_version', SCRIPT_VERSION)}</generator>")
    lines.append(f"    <dateCreated>{generated}</dateCreated>")
    lines.append("  </head>")
    lines.append("  <body>")

    note_text = ""
    if meta.get("mode") == "topic_only":
        stats = result.get("tree_stats", {})
        note_text = (
            f"⚠️ 本框架完全为 AI 推断,建议核对教材。生成模式 topic_only × "
            f"{' + '.join(meta.get('depth_used', ['skim']))},共 {stats.get('total_nodes', 0)} 节点"
        )

    def emit(node: dict, indent: int, root: bool = False):
        ind = "    " + "  " * indent
        attrs = f'text="{esc_attr(node.get("title", ""))}"'
        nid = node.get("id")
        if root and note_text:
            attrs += f' _note="{esc_attr(note_text)}"'
        elif nid in exps:
            note = (exps[nid].get("explanation") or "")[:300]
            attrs += f' _note="{esc_attr(note)}"'
        children = node.get("children") or []
        if children:
            lines.append(f"{ind}<outline {attrs}>")
            for c in children:
                emit(c, indent + 1)
            lines.append(f"{ind}</outline>")
        else:
            lines.append(f"{ind}<outline {attrs}/>")

    emit(tree, 0, root=True)

    lines.append("  </body>")
    lines.append("</opml>")
    return "\n".join(lines) + "\n"


# ---------- concept-dependencies.md ----------

def render_concept_dependencies(result: dict) -> str:
    meta = result.get("meta", {})
    tree = result.get("framework_tree", {})
    deps = result.get("concept_dependencies") or []
    if not deps:
        return ""

    title = tree.get("title", meta.get("course_topic", "知识框架"))
    title_by_id = {n.get("id"): n.get("title", "") for n, _ in walk_tree(tree)}
    strategy = result.get("inputs_summary", {}).get("concept_dependency_strategy", "off")

    out: list[str] = []
    out.append(f"# {title} · 概念依赖关系图")
    out.append("")
    out.append(f"> 共 **{len(deps)}** 条边,策略:`{strategy}`,模式:`{meta.get('mode', '')}`")
    out.append("")

    by_type: dict[str, list[dict]] = {}
    for d in deps:
        by_type.setdefault(d.get("type", "prerequisite"), []).append(d)
    summary_line = " · ".join(f"{DEP_STYLE.get(t, {}).get('label_prefix', t)} {len(v)}" for t, v in by_type.items())
    out.append(f"> 类型分布:{summary_line}")
    out.append("")
    out.append("---")
    out.append("")

    out.append("## Mermaid Flowchart")
    out.append("")
    out.append("```mermaid")
    out.append("flowchart LR")
    seen_node_ids: set[str] = set()
    for d in deps:
        for nid in (d["from"], d["to"]):
            if nid not in seen_node_ids:
                seen_node_ids.add(nid)
                lbl = title_by_id.get(nid, nid)[:20].replace("[", "(").replace("]", ")")
                safe = nid.replace(".", "_").replace("-", "_")
                out.append(f'    {safe}["{nid} {lbl}"]')

    for d in deps:
        u = d["from"].replace(".", "_").replace("-", "_")
        v = d["to"].replace(".", "_").replace("-", "_")
        arrow = DEP_STYLE.get(d["type"], {}).get("arrow", "-->")
        label = DEP_STYLE.get(d["type"], {}).get("label_prefix", d["type"])
        out.append(f"    {u} {arrow}|{label}| {v}")

    out.append("")
    out.append("    classDef cN fill:#f5f5f5,stroke:#888,stroke-width:1px;")
    if seen_node_ids:
        all_ids = ",".join(nid.replace(".", "_").replace("-", "_") for nid in seen_node_ids)
        out.append(f"    class {all_ids} cN;")
    out.append("```")
    out.append("")

    out.append("---")
    out.append("")
    out.append("## 边明细(按类型分组)")
    out.append("")
    for dtype, items in by_type.items():
        label = DEP_STYLE.get(dtype, {}).get("label_prefix", dtype)
        out.append(f"### {label}({dtype}) · {len(items)} 条")
        out.append("")
        out.append("| from | → | to | confidence | rationale |")
        out.append("|---|:---:|---|:---:|---|")
        for d in items:
            from_lbl = f"`{d['from']}` {title_by_id.get(d['from'], '')[:14]}"
            to_lbl = f"`{d['to']}` {title_by_id.get(d['to'], '')[:14]}"
            arrow_md = "→" if dtype != "contrast" else "↔"
            conf = d.get("confidence", "medium")
            rationale = (d.get("rationale", "") or "").replace("|", "\\|")
            out.append(f"| {from_lbl} | {arrow_md} | {to_lbl} | {conf} | {rationale} |")
        out.append("")

    return "\n".join(out)


# ---------- main ----------

def main() -> int:
    p = argparse.ArgumentParser(description="知识框架多格式渲染器")
    p.add_argument("result", nargs="?", help="result.json 路径(位置参数,与 --result 二选一)")
    p.add_argument("--result", dest="result_flag", help="result.json 路径")
    p.add_argument(
        "--formats",
        default="markdown,markmap,mermaid,opml,concept_deps",
        help="逗号分隔: " + ",".join(ALL_FORMATS),
    )
    p.add_argument("--out-dir", help="输出目录(默认 result.json 同级)")
    args = p.parse_args()

    rpath_str = args.result_flag or args.result
    if not rpath_str:
        print("[render] 错误: 必须提供 result.json 路径", file=sys.stderr)
        return 1
    rpath = Path(rpath_str)
    if not rpath.exists():
        print(f"[render] 错误: result.json 不存在 {rpath}", file=sys.stderr)
        return 1

    try:
        result = json.loads(rpath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[render] 错误: result.json 解析失败: {e}", file=sys.stderr)
        return 1
    if "framework_tree" not in result:
        print("[render] 错误: result.json 缺 framework_tree", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir) if args.out_dir else rpath.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    fmts = [f.strip() for f in args.formats.split(",") if f.strip()]
    invalid = [f for f in fmts if f not in ALL_FORMATS]
    if invalid:
        print(f"[render] 错误: 非法 format {invalid},允许 {ALL_FORMATS}", file=sys.stderr)
        return 1

    written: list[str] = []
    if "markdown" in fmts:
        path = out_dir / "framework.md"
        path.write_text(render_markdown(result), encoding="utf-8")
        written.append(path.name)
    if "markmap" in fmts:
        path = out_dir / "framework.markmap.html"
        path.write_text(render_markmap_html(result), encoding="utf-8")
        written.append(path.name)
    if "mermaid" in fmts:
        path = out_dir / "framework.mermaid.md"
        path.write_text(render_mermaid(result), encoding="utf-8")
        written.append(path.name)
    if "opml" in fmts:
        path = out_dir / "framework.opml"
        path.write_text(render_opml(result), encoding="utf-8")
        written.append(path.name)
    if "concept_deps" in fmts:
        text = render_concept_dependencies(result)
        if text:
            path = out_dir / "concept-dependencies.md"
            path.write_text(text, encoding="utf-8")
            written.append(path.name)

    print(f"[render] ✓ 已渲染 {len(written)} 文件 → {out_dir}: {written}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
