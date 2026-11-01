#!/usr/bin/env python3
"""
可比公司数据看板 —— 单 HTML 报告生成器 v2。
图表类型按指标语义自动分配：规模用横柱、增速用竖柱、质量用点图、估值用点图（线性刻度）。
新增双维度气泡散点图（PE × 营收增速），零外部依赖，纯 Python 标准库。
用法：
    python3 report_html.py --data data.json --title "源杰科技 · 可比公司数据看板" --out report.html
"""

import argparse, json, os, re, sys, math

# ── 调色板（精炼版） ──────────────────────────────────────
C_TARGET   = "#c53030"   # 目标公司 — 暖朱红
C_PEER     = "#4a6996"   # 可比公司 — 钢蓝
C_PEER_LT  = "#90aec8"   # 浅钢蓝（vbar 用）
C_ACCENT   = "#c53030"
C_TEXT      = "#1a202c"   # 正文深色（提升对比度）
C_MUTED     = "#718096"
C_BG        = "#fafbfc"   # 页面底色（更浅更透气）
C_CARD      = "#ffffff"
C_BORDER    = "#e8ecf0"   # 边框（更冷调）
C_BG_TGT    = "#fff5f5"   # 目标行底色
C_HERO_FROM = "#1a202c"
C_HERO_TO   = "#4a5568"

# ── SVG 画布常量 ─────────────────────────────────────────
# 横向柱 (规模类)
HBAR_W = 600; HBAR_ML = 155; HBAR_MR = 35; HBAR_TOP = 36; HBAR_BOT = 28
HBAR_RH = 34; HBAR_BH = 18; HBAR_BAR_W = HBAR_W - HBAR_ML - HBAR_MR

# 垂直柱 (增速类)
VW = 560; V_TOP = 38; V_BOT = 32; V_BAR_W = 62; V_GAP = 18; V_H = 230
V_TXT_Y = V_H - 10

# 圆点图 (质量类)
DW = 580; D_TOP = 38; D_BOT = 28; D_RH = 36; D_R = 7

# 散点图 (双维度)
SC_W = 560; SC_H = 380; SC_ML = 72; SC_MR = 48; SC_TOP = 42; SC_BOT = 48


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ─────────────────────────────────────────────────────────
# Chart 1: 横向柱状图 — 规模类 (营业收入/净利润/总市值)
# ────────────────────────────────────────────────────────
def svg_hbar(companies, vals, title, unit, ti=0):
    n = len(companies)
    vv = [v for v in vals if v is not None]
    mv = max(abs(v) for v in vv) if vv else 1
    if mv == 0: mv = 1
    w = HBAR_BAR_W
    h = HBAR_TOP + n * HBAR_RH + HBAR_BOT + 6
    avg = sum(vv) / len(vv) if vv else 0

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{HBAR_W}" height="{h}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">',
        f'<rect width="100%" height="100%" fill="{C_CARD}" rx="8"/>',
        f'<text x="28" y="20" font-size="13" '
        f'font-weight="700" fill="{C_TEXT}">{esc(title)}</text>',
        f'<text x="28" y="34" font-size="10" '
        f'fill="{C_MUTED}">{unit}</text>',
    ]

    # 均值参考线（轻量虚线）
    ax = HBAR_ML + (avg / mv) * w if mv > 0 else HBAR_ML
    lines.append(
        f'<line x1="{ax}" y1="{HBAR_TOP}" x2="{ax}" y2="{HBAR_TOP + n * HBAR_RH}" '
        f'stroke="{C_MUTED}" stroke-dasharray="4,4" stroke-width="0.8" opacity="0.3"/>'
    )

    for i, (nm, v) in enumerate(zip(companies, vals)):
        y = HBAR_TOP + i * HBAR_RH
        is_tgt = i == ti
        if v is None:
            lines.append(
                f'<text x="{HBAR_ML - 6}" y="{y + 15}" text-anchor="end" '
                f'font-size="11" fill="{C_TEXT}">{esc(nm)}</text>'
            )
            lines.append(
                f'<text x="{HBAR_ML + 8}" y="{y + 15}" font-size="10" '
                f'fill="{C_MUTED}">—</text>'
            )
            continue
        bw_i = max(abs(v) / mv * w, 3)
        # 渐变柱——深色端在右侧，视觉重量向右渐淡
        gid = f"hbar_{i}"
        if is_tgt:
            lines.append(
                f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
                f'<stop offset="0%" stop-color="#e06b6b"/>'
                f'<stop offset="100%" stop-color="{C_TARGET}" /></linearGradient></defs>'
            )
        else:
            lines.append(
                f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
                f'<stop offset="0%" stop-color="#7b9bc0"/>'
                f'<stop offset="100%" stop-color="{C_PEER}" /></linearGradient></defs>'
            )
        lines.append(
            f'<rect x="{HBAR_ML}" y="{y + 4}" width="{bw_i}" height="{HBAR_BH}" rx="3" '
            f'fill="url(#{gid})" opacity="{0.95 if is_tgt else 0.80}"/>'
        )
        # 公司名——目标公司朱红色加粗
        lines.append(
            f'<text x="{HBAR_ML - 6}" y="{y + 15}" text-anchor="end" font-size="11" '
            f'fill="{C_TARGET if is_tgt else C_TEXT}" '
            f'font-weight="{700 if is_tgt else 400}">{esc(nm)}</text>'
        )
        # 数值标签——悬挂在柱右侧
        lines.append(
            f'<text x="{HBAR_ML + bw_i + 10}" y="{y + 15}" font-size="11" '
            f'font-weight="600" fill="{C_TARGET if is_tgt else C_MUTED}">{v:.1f}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# Chart 2: 垂直柱状图 — 增速类 (营收增速/净利润增速)
# ────────────────────────────────────────────────────────
def svg_vbar(companies, vals, title, unit, ti=0):
    n = len(companies)
    vv = [v for v in vals if v is not None]
    mx = max(vv) if vv else 1
    if mx <= 0: mx = 1
    mn = min(vv) if vv else 0
    total_w = n * (V_BAR_W + V_GAP) + V_GAP + 100
    h = V_TOP + V_H + V_BOT + 36

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{h}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">',
        f'<rect width="100%" height="100%" fill="{C_CARD}" rx="8"/>',
        f'<text x="{total_w / 2}" y="20" text-anchor="middle" font-size="13" '
        f'font-weight="700" fill="{C_TEXT}">{esc(title)}</text>',
        f'<text x="{total_w / 2}" y="33" text-anchor="middle" font-size="10" '
        f'fill="{C_MUTED}">{unit}</text>',
    ]

    # 零线 / 基线
    base_y = V_TOP + V_H
    lines.append(
        f'<line x1="50" y1="{base_y}" x2="{total_w - 30}" y2="{base_y}" '
        f'stroke="{C_BORDER}" stroke-width="1" stroke-dasharray="3,3"/>'
    )

    for i, (nm, v) in enumerate(zip(companies, vals)):
        x = 50 + V_GAP + i * (V_BAR_W + V_GAP)
        if v is None:
            lines.append(
                f'<text x="{x + V_BAR_W / 2}" y="{base_y + 18}" text-anchor="middle" '
                f'font-size="9" fill="{C_MUTED}">{esc(nm)}</text>'
            )
            continue
        bar_h = max(abs(v) / mx * V_H, 3) if mx > 0 else 3
        is_tgt = i == ti
        y0 = V_TOP + V_H - bar_h if v >= 0 else V_TOP + V_H
        # 正负值分开处理：正向上、负向下（从零线开始）
        if v >= 0:
            gid = f"vbar_{i}"
            lines.append(
                f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0%" stop-color="{C_TARGET if is_tgt else C_PEER}"/>'
                f'<stop offset="100%" stop-color="#e06b6b" /></linearGradient></defs>'
                if is_tgt
                else f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                     f'<stop offset="0%" stop-color="{C_PEER}"/>'
                     f'<stop offset="100%" stop-color="#6b8bb8" /></linearGradient></defs>'
            )
            lines.append(
                f'<rect x="{x}" y="{y0}" width="{V_BAR_W}" height="{bar_h}" rx="3" '
                f'fill="url(#{gid})" opacity="{0.92 if is_tgt else 0.78}"/>'
            )
        lines.append(
            f'<text x="{x + V_BAR_W / 2}" y="{y0 - 6}" text-anchor="middle" '
            f'font-size="10" font-weight="{700 if is_tgt else 400}" '
            f'fill="{C_TARGET if is_tgt else C_MUTED}">{v:.1f}</text>'
        )
        lines.append(
            f'<text x="{x + V_BAR_W / 2}" y="{base_y + 18}" text-anchor="middle" '
            f'font-size="9" fill="{C_TEXT if is_tgt else C_MUTED}">{esc(nm)}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# Chart 3: 圆点对比图 — 质量类 (毛利率/净利率/ROE)
# ────────────────────────────────────────────────────────
def svg_dot_compare(companies, vals, title, unit, ti=0):
    n = len(companies)
    vv = [v for v in vals if v is not None]
    mx = max(vv) if vv else 100
    mn = min(vv) if vv else 0
    if mx <= 0: mx = 100
    h = D_TOP + n * D_RH + D_BOT + 10
    span = mx - mn if mx > mn else mx * 0.1
    if span == 0: span = 1

    # 横向画布：DW 宽，左留白 120 写公司名
    dot_ml = 120; dot_mr = 40
    w = DW - dot_ml - dot_mr

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{DW}" height="{h}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">',
        f'<rect width="100%" height="100%" fill="{C_CARD}" rx="8"/>',
        f'<text x="{DW / 2}" y="20" text-anchor="middle" font-size="13" '
        f'font-weight="700" fill="{C_TEXT}">{esc(title)}</text>',
        f'<text x="{DW / 2}" y="33" text-anchor="middle" font-size="10" '
        f'fill="{C_MUTED}">{unit}</text>',
    ]

    # 背景带（浅灰横条，增加可读性）
    for i in range(n):
        y = D_TOP + i * D_RH
        if i % 2 == 0:
            lines.append(
                f'<rect x="{dot_ml}" y="{y - 2}" width="{w}" height="{D_RH}" '
                f'fill="#f8fafc" rx="2" opacity="0.5"/>'
            )

    for i, (nm, v) in enumerate(zip(companies, vals)):
        y = D_TOP + i * D_RH
        if v is not None:
            px = dot_ml + ((v - mn) / span) * w if span > 0 else dot_ml + w / 2
            is_tgt = i == ti
            r = D_R + 2 if is_tgt else D_R
            c = C_TARGET if is_tgt else C_PEER
            lines.append(
                f'<circle cx="{px}" cy="{y + 12}" r="{r}" fill="{c}" '
                f'opacity="0.92" stroke="#fff" stroke-width="1.5"/>'
            )
            lines.append(
                f'<text x="{px}" y="{y - 2}" text-anchor="middle" font-size="10" '
                f'font-weight="{700 if is_tgt else 400}" '
                f'fill="{C_TARGET if is_tgt else C_MUTED}">{v:.1f}{unit}</text>'
            )
        lines.append(
            f'<text x="{dot_ml - 8}" y="{y + 14}" text-anchor="end" font-size="11" '
            f'fill="{C_TARGET if i == ti else C_TEXT}" '
            f'font-weight="{700 if i == ti else 400}">{esc(nm)}</text>'
        )

    # 均值虚线
    avg = sum(vv) / len(vv)
    ax_px = dot_ml + ((avg - mn) / span) * w if span > 0 else dot_ml + w / 2
    lines.append(
        f'<line x1="{ax_px}" y1="{D_TOP}" x2="{ax_px}" y2="{D_TOP + n * D_RH}" '
        f'stroke="{C_MUTED}" stroke-dasharray="5,5" stroke-width="0.8" opacity="0.4"/>'
    )
    lines.append(
        f'<text x="{ax_px}" y="{D_TOP + n * D_RH + 6}" text-anchor="middle" '
        f'font-size="8" fill="{C_MUTED}">均值 {avg:.1f}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# Chart 4: 气泡散点图 — 双维度交叉 (PE × 营收增速)
# ────────────────────────────────────────────────────────
def svg_scatter(companies, x_vals, y_vals, x_label, y_label,
                size_vals=None, size_label=None, ti=0):
    """散点图：X=PE(倍), Y=营收增速(%)"""
    n = len(companies)
    # 过滤有效数据点
    x_valid = [v for v in x_vals if v is not None]
    y_valid = [v for v in y_vals if v is not None]
    x_min = min(x_valid) if x_valid else 0
    x_max = max(x_valid) if x_valid else 100
    y_min = min(y_valid) if y_valid else 0
    y_max = max(y_valid) if y_valid else 100
    # 留 10% 边距
    x_span = x_max - x_min if x_max > x_min else max(x_max * 0.1, 10)
    y_span = y_max - y_min if y_max > y_min else max(y_max * 0.1, 10)
    if x_span == 0: x_span = 10
    if y_span == 0: y_span = 10
    x_pad = x_span * 0.12
    y_pad = y_span * 0.12
    x_lo = x_min - x_pad
    x_hi = x_max + x_pad
    y_lo = y_min - y_pad
    y_hi = y_max + y_pad

    # 宽度/高度
    plot_w = SC_W - SC_ML - SC_MR
    plot_h = SC_H - SC_TOP - SC_BOT
    h_total = SC_H

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SC_W}" height="{h_total}" '
        f'font-family="PingFang SC,Microsoft YaHei,sans-serif">',
        f'<rect width="100%" height="100%" fill="{C_CARD}" rx="8"/>',
        f'<text x="{SC_W / 2}" y="20" text-anchor="middle" font-size="13" '
        f'font-weight="700" fill="{C_TEXT}">{esc(x_label)} × {esc(y_label)}</text>',
        f'<text x="{SC_W / 2}" y="33" text-anchor="middle" font-size="10" '
        f'fill="{C_MUTED}">气泡大小 = {esc(size_label or "总市值")}</text>',
    ]

    # 网格线
    for j in range(5):
        frac = j / 4
        gy = SC_TOP + frac * plot_h
        gx_val = y_hi - frac * (y_hi - y_lo)
        lines.append(
            f'<line x1="{SC_ML}" y1="{gy}" x2="{SC_ML + plot_w}" y2="{gy}" '
            f'stroke="{C_BORDER}" stroke-width="0.5" stroke-dasharray="3,4"/>'
        )
        lines.append(
            f'<text x="{SC_ML - 8}" y="{gy + 4}" text-anchor="end" font-size="8" '
            f'fill="{C_MUTED}">{gx_val:.0f}</text>'
        )
    for j in range(5):
        frac = j / 4
        gx = SC_ML + frac * plot_w
        gv_val = x_lo + frac * (x_hi - x_lo)
        lines.append(
            f'<line x1="{gx}" y1="{SC_TOP}" x2="{gx}" y2="{SC_TOP + plot_h}" '
            f'stroke="{C_BORDER}" stroke-width="0.5" stroke-dasharray="3,4"/>'
        )
        lines.append(
            f'<text x="{gx}" y="{SC_TOP + plot_h + 14}" text-anchor="middle" '
            f'font-size="8" fill="{C_MUTED}">{gv_val:.0f}</text>'
        )

    # 轴标签
    lines.append(
        f'<text x="{SC_W / 2}" y="{SC_TOP + plot_h + 32}" text-anchor="middle" '
        f'font-size="10" fill="{C_MUTED}">{esc(x_label)}</text>'
    )
    lines.append(
        f'<text x="14" y="{SC_TOP + plot_h / 2}" text-anchor="middle" font-size="10" '
        f'fill="{C_MUTED}" transform="rotate(-90,14,{SC_TOP + plot_h / 2})">{esc(y_label)}</text>'
    )

    # 数据点
    for i, nm in enumerate(companies):
        xv = x_vals[i] if i < len(x_vals) else None
        yv = y_vals[i] if i < len(y_vals) else None
        sz = size_vals[i] if size_vals and i < len(size_vals) else None
        if xv is None or yv is None:
            continue
        px = SC_ML + ((xv - x_lo) / (x_hi - x_lo)) * plot_w if x_hi > x_lo else SC_ML + plot_w / 2
        py = SC_TOP + plot_h - ((yv - y_lo) / (y_hi - y_lo)) * plot_h if y_hi > y_lo else SC_TOP + plot_h / 2
        is_tgt = i == ti
        # 气泡半径基于市值（可选），默认 r=8
        base_r = 8
        if sz is not None and size_vals:
            sz_valid = [s for s in size_vals if s is not None]
            sz_max = max(sz_valid) if sz_valid else 1
            sz_min = min(sz_valid) if sz_valid else 1
            if sz_max > sz_min:
                base_r = 5 + (sz - sz_min) / (sz_max - sz_min) * 12
            else:
                base_r = 8
        r = base_r + 2 if is_tgt else base_r
        c = C_TARGET if is_tgt else C_PEER
        lines.append(
            f'<circle cx="{px}" cy="{py}" r="{r}" fill="{c}" opacity="0.85" '
            f'stroke="#fff" stroke-width="1.5"/>'
        )
        if is_tgt:
            lines.append(
                f'<text x="{px}" y="{py - r - 6}" text-anchor="middle" font-size="10" '
                f'font-weight="700" fill="{C_TARGET}">{esc(nm)}</text>'
            )
            lines.append(
                f'<text x="{px}" y="{py + r + 12}" text-anchor="middle" font-size="9" '
                f'fill="{C_TARGET}">PE {xv:.0f} · 增速 {yv:.1f}%</text>'
            )
        else:
            lines.append(
                f'<text x="{px}" y="{py - r - 6}" text-anchor="middle" font-size="9" '
                f'fill="{C_MUTED}">{esc(nm)}</text>'
            )
    lines.append("</svg>")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# 汇总表
# ────────────────────────────────────────────────────────
def table_html(data):
    labels = [
        "公司", "营业收入(亿元)", "营业收入增速(%)", "净利润(亿元)", "净利润增速(%)",
        "毛利率(%)", "净利率(%)", "ROE(%)", "PE(倍)", "总市值(亿元)",
    ]
    keys = [
        "name", "revenue", "revenue_growth", "net_profit", "net_profit_growth",
        "gross_margin", "net_margin", "roe", "pe", "market_cap",
    ]
    target = data.get("target", "")
    rows = []
    # 表头
    rows.append("<tr>" + "".join(f"<th>{l}</th>" for l in labels) + "</tr>")
    for c in data["companies"]:
        is_tgt = c["name"] == target
        cls = ' class="tgt"' if is_tgt else ""
        cells = []
        for j, k in enumerate(keys):
            v = c.get(k)
            if j == 0:
                cells.append(f'<td{cls}>{esc(str(v))}</td>')
            elif v is not None:
                cells.append(f'<td{cls}>{v:.1f}</td>')
            else:
                cells.append('<td class="na">—</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    # 均值行
    avg_cells = ['<td class="avg">可比均值</td>']
    for j in range(1, len(keys)):
        vv = [c.get(keys[j]) for c in data["companies"] if c.get(keys[j]) is not None]
        if vv:
            a = sum(vv) / len(vv)
            avg_cells.append(f'<td class="avg">{a:.1f}</td>')
        else:
            avg_cells.append('<td class="avg na">—</td>')
    rows.append("<tr>" + "".join(avg_cells) + "</tr>")
    return f"""<table class="summary-table">
<thead>{"".join(rows[:1])}</thead>
<tbody>{"".join(rows[1:])}</tbody>
</table>"""


# ─────────────────────────────────────────────────────────
# Markdown → HTML
# ────────────────────────────────────────────────────────
def md_to_html(md):
    out = []; in_list = False
    for line in md.strip().split("\n"):
        line = line.rstrip()
        if not line:
            if in_list:
                out.append("</ul>"); in_list = False
            continue
        m = re.match(r"^###\s+(.*)", line)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            out.append(f'<h4>{esc(m.group(1))}</h4>')
            continue
        m = re.match(r"^##\s+(.*)", line)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            out.append(f'<h3>{esc(m.group(1))}</h3>')
            continue
        m = re.match(r"^[-*]\s+(.*)", line)
        if m:
            if not in_list: out.append("<ul>"); in_list = True
            t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(m.group(1)))
            out.append(f"<li>{t}</li>")
            continue
        if in_list: out.append("</ul>"); in_list = False
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(line))
        out.append(f"<p>{t}</p>")
    if in_list: out.append("</ul>")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--title", default="可比公司数据看板")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    data = load(args.data)
    companies = [c["name"] for c in data["companies"]]
    target = data.get("target", companies[0])
    ti = next(i for i, c in enumerate(data["companies"]) if c["name"] == target)

    # ── 指标 → 图表类型映射（语义驱动）──
    # 规模 → hbar | 估值 → vbar | 质量 → dot（线性刻度）
    # 营收增速 / 净利润增速 单独不画图（仅在散点图 X 轴使用）
    metric_map = [
        ("revenue",       "营业收入", "亿元", "hbar"),
        ("net_profit",    "净利润",   "亿元", "hbar"),
        ("gross_margin",  "毛利率",   "%",    "dot"),
        ("net_margin",    "净利率",   "%",    "dot"),
        ("roe",           "ROE",      "%",    "dot"),
        ("market_cap",    "总市值",   "亿元", "vbar"),
        ("pe",            "PE(TTM)",  "倍",   "vbar"),
    ]

    # ── 按类别分组生成图表 ──
    groups = {
        "📊 规模对比": [],
        "🎯 盈利质量": [],
        "💰 估值对比": [],
    }

    chart_count = 0
    for key, title, unit, chtype in metric_map:
        vals = [c.get(key) for c in data["companies"]]
        if not any(v is not None for v in vals):
            continue

        if chtype == "hbar":
            svg = svg_hbar(companies, vals, title, unit, ti)
            group = "📊 规模对比"
        elif chtype == "vbar":
            svg = svg_vbar(companies, vals, title, unit, ti)
            group = "💰 估值对比"
        elif chtype == "dot":
            svg = svg_dot_compare(companies, vals, title, unit, ti)
            group = "🎯 盈利质量"
        else:
            svg = svg_hbar(companies, vals, title, unit, ti)
            group = "📊 规模对比"

        groups[group].append(f'<div class="chart-card">{svg}</div>')
        chart_count += 1

    # ── 双维度散点图（PE × 营收增速，气泡=总市值）──
    pe_vals = [c.get("pe") for c in data["companies"]]
    rev_growth_vals = [c.get("revenue_growth") for c in data["companies"]]
    mcap_vals = [c.get("market_cap") for c in data["companies"]]
    if any(v is not None for v in pe_vals) and any(v is not None for v in rev_growth_vals):
        scatter_svg = svg_scatter(
            companies, pe_vals, rev_growth_vals,
            "PE(TTM) · 倍", "营业收入增速 · %",
            size_vals=mcap_vals, size_label="总市值(亿元)", ti=ti,
        )
        # 散点图放入估值对比组末尾
        groups["💰 估值对比"].append(f'<div class="chart-card chart-scatter">{scatter_svg}</div>')
        chart_count += 1

    # ── 分析文本 ──
    analysis = md_to_html(data.get("analysis", "")) if data.get("analysis") else ""

    # ── KPI 速览 ──
    tgt_c = data["companies"][ti]
    kpi_map = [
        ("营业收入", "revenue", "亿元"),
        ("毛利率",   "gross_margin", "%"),
        ("净利率",   "net_margin", "%"),
        ("ROE",      "roe", "%"),
        ("PE(TTM)",  "pe", "倍"),
        ("总市值",   "market_cap", "亿元"),
    ]
    kpi_items = ""
    for lbl, k, unit in kpi_map:
        v = tgt_c.get(k)
        if v is not None:
            kpi_items += (
                f'<div class="kpi-item">'
                f'<div class="kpi-val">{v:.1f}{unit}</div>'
                f'<div class="kpi-lbl">{lbl}</div>'
                f'</div>\n'
            )

    # ── 分组图表 HTML ──
    groups_html = ""
    for group_label, group_charts in groups.items():
        if group_charts:
            groups_html += f"""
            <div class="section">
              <div class="section-head">{group_label}</div>
              <div class="charts-grid">{''.join(group_charts)}</div>
            </div>"""

    # ── 完整 HTML ──
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(args.title)}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  font-family:'PingFang SC','Heiti SC','Microsoft YaHei',sans-serif;
  color:{C_TEXT};
  background:{C_BG};
  padding:0;
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
}}

/* ── 页面顶部（轻量渐变，干净有质感） ── */
.hero{{
  background:linear-gradient(165deg,#f7f8fa 0%,#eef1f5 40%,#e8ecf1 100%);
  color:{C_TEXT};
  padding:48px 32px 40px;
  text-align:center;
  border-bottom:1px solid {C_BORDER};
  position:relative;
}}
.hero::after{{
  content:'';
  position:absolute;
  bottom:0;
  left:0;
  right:0;
  height:3px;
  background:linear-gradient(90deg,transparent,{C_TARGET}40 50%,transparent);
  opacity:0.15;
}}
.hero h1{{
  font-size:28px;
  font-weight:600;
  letter-spacing:0.8px;
  color:{C_TEXT};
  margin-bottom:6px;
}}
.hero .sub{{
  font-size:13px;
  color:{C_MUTED};
  letter-spacing:0.5px;
  margin-bottom:4px;
}}
.hero .tagline{{
  font-size:11px;
  color:#a0aec0;
  margin-top:8px;
}}

/* ── 主容器 ── */
.container{{
  max-width:1100px;
  margin:0 auto;
  padding:52px 32px 64px;
}}

/* ── KPI 卡片 ── */
.kpi-label{{
  font-size:14px;
  font-weight:700;
  color:{C_MUTED};
  text-align:center;
  margin-bottom:16px;
  letter-spacing:1.2px;
}}
.kpi-row{{
  display:flex;
  flex-wrap:wrap;
  gap:14px;
  justify-content:center;
  margin-bottom:40px;
}}
.kpi-item{{
  background:{C_CARD};
  border:1px solid {C_BORDER};
  border-radius:12px;
  padding:18px 22px;
  min-width:120px;
  text-align:center;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
  transition:all .22s ease;
}}
.kpi-item:hover{{
  transform:translateY(-3px);
  box-shadow:0 8px 24px rgba(0,0,0,.09);
}}
.kpi-item:first-child{{
  border-left:3px solid {C_ACCENT};
  box-shadow:0 2px 8px rgba(197,48,48,.08);
}}
.kpi-val{{
  font-size:22px;
  font-weight:700;
  color:{C_TEXT};
  line-height:1.2;
}}
.kpi-lbl{{
  font-size:10px;
  color:{C_MUTED};
  margin-top:6px;
  letter-spacing:0.5px;
}}

/* ── 区段 ── */
.section{{
  margin-bottom:56px;
}}
.section-head{{
  font-size:15px;
  font-weight:700;
  color:{C_TEXT};
  margin-bottom:20px;
  padding-bottom:14px;
  border-bottom:2px solid #edf2f7;
  display:flex;
  align-items:center;
  gap:10px;
  letter-spacing:0.6px;
}}

/* ── 汇总表 ── */
.summary-table{{
  width:100%;
  border-collapse:collapse;
  font-size:12px;
  border:1px solid {C_BORDER};
  border-radius:10px;
  overflow:hidden;
  background:{C_CARD};
  box-shadow:0 1px 3px rgba(0,0,0,.04);
}}
.summary-table th{{
  background:#f7f8fa;
  padding:14px 10px;
  font-weight:600;
  text-align:center;
  border-bottom:2px solid {C_BORDER};
  font-size:11px;
  color:{C_MUTED};
  white-space:nowrap;
  letter-spacing:0.4px;
}}
.summary-table td{{
  padding:12px 10px;
  text-align:right;
  border-bottom:1px solid #f1f5f9;
  font-size:12px;
}}
.summary-table td:first-child{{
  text-align:left;
  font-weight:500;
}}
.summary-table tr:last-child td{{
  border-bottom:none;
}}
.summary-table .tgt{{
  background:{C_BG_TGT};
  font-weight:700;
  color:{C_TARGET};
}}
.summary-table .avg{{
  background:#f8fafc;
  color:{C_MUTED};
  font-style:italic;
  font-size:11px;
}}
.summary-table .na{{
  color:#cbd5e0;
  text-align:center;
}}

/* ── 图表网格（CSS Grid 保证对齐） ── */
.charts-grid{{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(520px,1fr));
  gap:20px;
}}
.chart-card{{
  background:{C_CARD};
  border:1px solid {C_BORDER};
  border-radius:12px;
  padding:18px 22px;
  box-shadow:0 1px 3px rgba(0,0,0,.04);
  transition:all .25s ease;
}}
.chart-card:hover{{
  box-shadow:0 8px 28px rgba(0,0,0,.10);
  transform:translateY(-3px);
}}
.chart-scatter{{
  grid-column:1 / -1;
  min-width:560px;
}}

/* ── 分析区（精排，字号层级清晰） ── */
.analysis{{
  font-size:14px;
  color:{C_TEXT};
  background:{C_CARD};
  border-radius:14px;
  padding:40px 44px;
  border:1px solid {C_BORDER};
  box-shadow:0 2px 8px rgba(0,0,0,.05);
}}
.analysis h3{{
  font-size:19px;
  font-weight:700;
  margin:32px 0 14px;
  color:{C_TEXT};
  padding-bottom:10px;
  border-bottom:2px solid #edf2f7;
  letter-spacing:0.6px;
}}
.analysis h3:first-child{{margin-top:0}}
.analysis h4{{
  font-size:16px;
  font-weight:600;
  margin:22px 0 10px;
  color:{C_TEXT};
}}
.analysis p{{
  margin:14px 0;
  line-height:1.85;
  color:#4a5568;
  font-size:14px;
}}
.analysis ul{{
  margin:10px 0;
  padding-left:24px;
}}
.analysis li{{
  margin:8px 0;
  line-height:1.85;
  color:#4a5568;
  font-size:14px;
}}
.analysis b{{
  color:{C_TARGET};
  font-weight:600;
}}

/* ── 页脚 ── */
.footer{{
  text-align:center;
  padding:32px 0 0;
  border-top:2px solid #edf2f7;
  margin-top:56px;
}}
.footer p{{
  font-size:12px;
  color:{C_MUTED};
  line-height:2.0;
}}
.footer .disclaimer{{
  font-size:10px;
  color:#a0aec0;
  margin-top:4px;
}}

/* ── 响应式 ── */
@media(max-width:768px){{
  .container{{padding:28px 18px}}
  .hero{{padding:36px 20px 28px}}
  .hero h1{{font-size:22px}}
  .kpi-item{{min-width:90px;padding:14px 16px}}
  .kpi-val{{font-size:18px}}
  .analysis{{padding:28px 22px;font-size:13px}}
  .summary-table{{font-size:10px}}
  .chart-card{{padding:12px 14px}}
  .charts-grid{{grid-template-columns:1fr;gap:16px}}
}}
</style>
</head>
<body>

<div class="hero">
  <h1>{esc(args.title)}</h1>
  <div class="sub">{len(data['companies'])} 家可比公司 · 可比公司数据看板</div>
  <div class="tagline">聚焦 {esc(target)} · 数据截至最新报告期 · 人民币亿元 / %</div>
</div>

<div class="container">

<!-- KPI 速览 -->
<div class="kpi-label">{esc(target)} · 核心指标速览</div>
<div class="kpi-row">
{kpi_items}
</div>

<!-- 关键指标表 -->
<div class="section">
  <div class="section-head">📋 关键指标一览</div>
  {table_html(data)}
</div>

<!-- 图表分组 -->
{groups_html}

<!-- 综合分析 -->
<div class="section">
  <div class="section-head">💡 综合研判</div>
  <div class="analysis">
{analysis}
  </div>
</div>

<!-- 免责声明 -->
<div class="footer">
  <p>以上内容由 AI 辅助生成，不构成投资建议。</p>
  <p class="disclaimer">投资有风险，入市需谨慎。数据来源：云极数据服务，仅供参考。</p>
</div>

</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 报告已生成 → {args.out}")
    print(f"   包含：KPI 速览 + 汇总表 + {chart_count} 张图表(含散点图) + 分析 + 免责声明")


if __name__ == "__main__":
    main()