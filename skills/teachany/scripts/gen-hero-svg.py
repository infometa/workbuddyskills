#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-hero-svg.py（v7.9.12）—— Hero 图 L3 SVG 兜底生成器

用途:
    当 L1（图床）+ L2（image_gen）都不可用时，用本脚本生成一张
    "知识结构信息图"风格的 SVG 作为 Hero 图。
    生成产物为**真实存在的 SVG 文件**（不是内联），直接放在
    `<course_dir>/assets/<course-id>-hero.svg`，让 HTML 引用即可。

产物规范:
    - 格式: SVG（viewBox 1280×720），无外部字体依赖（用 system-ui / sans-serif）
    - 内容: 中央主标题 + 2-6 个彩色卡片节点环绕 + 虚线连接
    - 语言: 按输入的 --lang zh / en 决定节点文字（默认 zh）
    - 文件大小通常 3-8 KB

用法:
    python3 scripts/gen-hero-svg.py <课件目录> \\
        --title "神经调节" \\
        --subtitle "高中生物·稳态与平衡" \\
        --nodes "动作电位,突触传递,反射弧,神经中枢" \\
        --lang zh

    最小用法（从 manifest.json 读取）:
    python3 scripts/gen-hero-svg.py community/bio-h-nervous-regulation

退出码:
    0 = 生成成功
    1 = 参数错误 / 无法读取 manifest
    2 = 写文件失败
"""

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape


# ─── 节点配色（信息图风格，6 组）───
NODE_PALETTE = [
    ("#6366f1", "#4f46e5", "#e0e7ff"),  # 靛
    ("#06b6d4", "#0891b2", "#cffafe"),  # 青
    ("#10b981", "#059669", "#d1fae5"),  # 绿
    ("#f59e0b", "#d97706", "#fef3c7"),  # 琥珀
    ("#ec4899", "#db2777", "#fce7f3"),  # 粉
    ("#8b5cf6", "#7c3aed", "#ede9fe"),  # 紫
]

BG_GRADIENT = ("#fafbff", "#eef2ff")

# 画布
VIEW_W, VIEW_H = 1280, 720


def load_manifest_if_any(course_dir: Path) -> dict:
    p = course_dir / "manifest.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def derive_course_id(course_dir: Path, override: str | None) -> str:
    if override:
        return override
    return course_dir.name


def compute_node_positions(n: int):
    """围绕中心 (640, 380) 放 n 个节点，半径 240。"""
    import math
    cx, cy, r = 640, 380, 250
    if n <= 0:
        return []
    # n=2 上下；n=3 三角；n=4 四角；n>=5 等分圆
    positions = []
    # 起始角（顶部 -90°）
    start = -math.pi / 2
    for i in range(n):
        ang = start + 2 * math.pi * i / n
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang) + 20  # 下偏一点让中心标题显著
        positions.append((x, y))
    return positions


def render_svg(title: str, subtitle: str, nodes: list[str], course_id: str) -> str:
    n = len(nodes)
    positions = compute_node_positions(n)

    # 节点卡片尺寸
    card_w, card_h, card_r = 200, 78, 16
    cx_center, cy_center = 640, 250  # 中心主标题区位置（上半）

    lines = []
    lines.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW_W} {VIEW_H}" '
        f'role="img" aria-label="{escape(title)} · 知识结构主图">'
    )
    # 定义渐变 + 样式
    lines.append('<defs>')
    lines.append('  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">')
    lines.append(f'    <stop offset="0%" stop-color="{BG_GRADIENT[0]}"/>')
    lines.append(f'    <stop offset="100%" stop-color="{BG_GRADIENT[1]}"/>')
    lines.append('  </linearGradient>')
    lines.append('  <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">')
    lines.append('    <feGaussianBlur in="SourceAlpha" stdDeviation="4"/>')
    lines.append('    <feOffset dx="0" dy="3" result="offsetblur"/>')
    lines.append('    <feComponentTransfer><feFuncA type="linear" slope="0.22"/></feComponentTransfer>')
    lines.append('    <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>')
    lines.append('  </filter>')
    lines.append('</defs>')

    # 背景
    lines.append(f'<rect width="{VIEW_W}" height="{VIEW_H}" fill="url(#bg)"/>')

    # 中心标题区（大号 + 副标题 + 装饰下划线）
    lines.append(
        f'<text x="{cx_center}" y="{cy_center - 10}" text-anchor="middle" '
        f'font-family="\'Noto Sans SC\', \'PingFang SC\', \'Microsoft YaHei\', system-ui, sans-serif" '
        f'font-size="58" font-weight="700" fill="#1e293b">{escape(title)}</text>'
    )
    if subtitle:
        lines.append(
            f'<text x="{cx_center}" y="{cy_center + 34}" text-anchor="middle" '
            f'font-family="\'Noto Sans SC\', \'PingFang SC\', \'Microsoft YaHei\', system-ui, sans-serif" '
            f'font-size="22" font-weight="400" fill="#64748b">{escape(subtitle)}</text>'
        )
    # 装饰线
    lines.append(
        f'<line x1="{cx_center - 80}" y1="{cy_center + 56}" x2="{cx_center + 80}" y2="{cy_center + 56}" '
        f'stroke="#6366f1" stroke-width="3" stroke-linecap="round"/>'
    )

    # 连接虚线（从中心到每个节点顶部）
    for (x, y), _ in zip(positions, nodes):
        lines.append(
            f'<line x1="{cx_center}" y1="{cy_center + 80}" x2="{x}" y2="{y}" '
            f'stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6 6"/>'
        )

    # 节点卡片
    for i, ((x, y), label) in enumerate(zip(positions, nodes)):
        stroke, deep, bg = NODE_PALETTE[i % len(NODE_PALETTE)]
        rx = x - card_w / 2
        ry = y - card_h / 2
        lines.append(
            f'<g filter="url(#softShadow)">'
            f'<rect x="{rx}" y="{ry}" width="{card_w}" height="{card_h}" rx="{card_r}" ry="{card_r}" '
            f'fill="white" stroke="{stroke}" stroke-width="3"/>'
            f'<rect x="{rx}" y="{ry}" width="6" height="{card_h}" rx="3" ry="3" fill="{stroke}"/>'
            f'<text x="{x + 3}" y="{y + 8}" text-anchor="middle" '
            f'font-family="\'Noto Sans SC\', \'PingFang SC\', \'Microsoft YaHei\', system-ui, sans-serif" '
            f'font-size="22" font-weight="600" fill="#1e293b">{escape(label)}</text>'
            f'</g>'
        )

    # 右下角签名
    lines.append(
        f'<text x="{VIEW_W - 24}" y="{VIEW_H - 20}" text-anchor="end" '
        f'font-family="system-ui, sans-serif" font-size="12" fill="#94a3b8">'
        f'TeachAny · knowledge-structure · {escape(course_id)}</text>'
    )

    lines.append('</svg>')
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course_dir", help="课件目录，如 community/bio-h-nervous-regulation")
    ap.add_argument("--title", help="主标题，默认从 manifest.json 读取")
    ap.add_argument("--subtitle", default="", help="副标题（学段·学科，可选）")
    ap.add_argument("--nodes", help="节点列表（逗号分隔），默认从 manifest.sections 推断")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--course-id", help="课件 ID 覆盖，默认取目录名")
    args = ap.parse_args()

    course_dir = Path(args.course_dir).resolve()
    if not course_dir.is_dir():
        print(f"❌ 课件目录不存在: {course_dir}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest_if_any(course_dir)
    course_id = derive_course_id(course_dir, args.course_id)

    title = args.title or manifest.get("title") or course_id
    subtitle = args.subtitle or manifest.get("subtitle") or manifest.get("subject_grade") or ""

    if args.nodes:
        nodes = [s.strip() for s in re.split(r"[,，]", args.nodes) if s.strip()]
    else:
        # 从 manifest.sections / manifest.modules 推断
        mods = manifest.get("modules") or manifest.get("sections") or []
        nodes = []
        for m in mods[:6]:
            if isinstance(m, dict):
                label = m.get("title") or m.get("name") or m.get("id")
            else:
                label = str(m)
            if label:
                nodes.append(label.strip()[:10])

    if not nodes:
        # 终极兜底（英中通用）
        if args.lang == "en":
            nodes = ["Concept 1", "Concept 2", "Concept 3", "Concept 4"]
        else:
            nodes = ["核心概念", "关键方法", "典型应用", "拓展迁移"]

    if len(nodes) < 2:
        nodes.append("拓展" if args.lang == "zh" else "Ext.")

    svg_text = render_svg(title, subtitle, nodes, course_id)

    # 写出文件
    out_dir = course_dir / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{course_id}-hero.svg"
    try:
        out_path.write_text(svg_text, encoding="utf-8")
    except Exception as e:
        print(f"❌ 写文件失败: {e}", file=sys.stderr)
        sys.exit(2)

    print(json.dumps({
        "level": "L3-svg",
        "source": "gen-hero-svg.py",
        "url": f"./assets/{course_id}-hero.svg",
        "path": str(out_path.relative_to(course_dir.parent)),
        "title": title,
        "nodes": nodes,
        "bytes": out_path.stat().st_size,
        "action": "generated",
    }, ensure_ascii=False, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
