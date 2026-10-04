# -*- coding: utf-8 -*-
"""经营诊断报告 PDF 模板：数据与布局分离。

目的：诊断内容（数据）与排版（布局）解耦。复跑或诊断另一家店时，
只改数据 JSON，不动本文件；布局问题修复后对所有报告生效。

用法：
    python report_template.py <data.json> <out.pdf>

data.json 结构见同目录 report_data_example.json。页面按 type 渲染：
  cover        首页：三栏发现 + 关键建议卡
  journey      顾客旅程：图例 + 6 节点网格
  bars         横条图 + 判断 + 笔记样张卡
  before_after 标题升级：左原样右样张对照行
  text_card    左侧文字块 + 右侧设计稿卡
  plan         行动计划表（5 列）
  sources      数据与来源页
"""
import sys, json, os

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

PALETTE = {
    "INK": "#193A32", "MUTED": "#64736D", "GREEN": "#2E6B4F",
    "ORANGE": "#B4632A", "GRAY": "#7A8280", "BLUE": "#3D6B8E",
    "BROWN": "#8A6A4F", "BAR": "#7A9485",
}

def chip(rc, x, top, label, color, width=64):
    rc.rect(x, top, width, 22, fill=color, radius=6)
    rc.text(label, x, top + 3, width, 16, size=9.5, bold=True, color="#FFFFFF")

def render_cover(rc, p, C):
    rc.page(p["title"], p["subtitle"], p["note"])
    cols = p["cols"]  # [(label, colorkey, body)]
    cw = (515 - 32) / 3
    fills = ["#EDF2EC", "#F5EFE7", "#EFF1F0"]
    for i, (t, ck, body) in enumerate(cols):
        x = 40 + i * (cw + 16)
        rc.rect(x, 225, cw, 235, fill=fills[i], radius=8)
        rc.text(t, x + 14, 239, cw - 28, 24, size=14, bold=True, color=C[ck])
        rc.text(body, x + 14, 272, cw - 28, 180, size=9.8, color=C["INK"])
    rc.text(p["advice_title"], 40, 480, 515, 22, size=13, bold=True, color=C["INK"])
    for i, (t, body, ck) in enumerate(p["advice"]):
        x = 40 + i * (cw + 16)
        rc.rect(x, 508, cw, 165, fill="#FFFFFF", radius=10)
        rc.text(t, x + 14, 522, cw - 28, 24, size=12, bold=True, color=C[ck])
        rc.text(body, x + 14, 552, cw - 28, 112, size=9.8, color=C["INK"])

def render_journey(rc, p, C):
    rc.page(p["title"], p["subtitle"], p["note"])
    lx = 40
    for t, ck in p["legend"]:
        chip(rc, lx, 214, t, C[ck], width=72)
        lx += 84
    nodes = p["nodes"]  # [(title, body, status_label, colorkey)]
    nw, nh = 163, 175
    for i, (t, body, st, ck) in enumerate(nodes):
        row, col = divmod(i, 3)
        x = 40 + col * (nw + 13)
        top = 258 + row * (nh + 44)
        rc.rect(x, top, nw, nh, fill="#FFFFFF", radius=10)
        rc.rect(x, top, nw, 6, fill=C[ck], radius=6)
        rc.text(t, x + 12, top + 16, nw - 24, 22, size=12, bold=True, color=C["INK"])
        rc.text(body, x + 12, top + 44, nw - 24, 92, size=9.3, color=C["INK"])
        chip(rc, x + 12, top + nh - 30, st, C[ck], width=64)
        if col < 2:
            rc.arrow(x + nw + 1, top + nh / 2, x + nw + 12, top + nh / 2, color="#B9C7BD")
    for col in (0, 1):
        ax = 40 + col * (nw + 13) + nw + 12
        rc.arrow(ax, 258 + nh + 2, ax, 258 + nh + 42, color="#B9C7BD")
    rc.text(p["footer"], 40, 700, 515, 40, size=10.5, color=C["MUTED"])

def render_bars(rc, p, C):
    rc.page(p["title"], p["subtitle"], p["note"])
    items = p["items"]  # [(name, value, label, colorkey)]
    vmax = p["max"]
    top0 = 250
    for i, (name, v, lab, ck) in enumerate(items):
        t = top0 + i * 52
        rc.text(name, 40, t, 240, 16, size=9.3, color=C["INK"])
        bw = max(3, 200 * v / vmax)
        rc.rect(40, t + 20, bw, 13, fill=C[ck], radius=3)
        rc.text(lab, 40 + bw + 6, t + 20, 80, 14, size=9, bold=(i == 0), color=C["INK"])
    rc.text(p["observation"], 40, 575, 250, 55, size=9.8, color=C["MUTED"])
    rc.text(p["insight"], 310, 250, 245, 150, size=10.5, color=C["INK"])
    rc.rect(310, 415, 245, 300, fill="#EDF2EC", radius=12)
    rc.text(p["mockup_title"], 326, 430, 213, 20, size=12, bold=True, color=C["GREEN"])
    rc.text(p["mockup_body"], 326, 458, 213, 245, size=9.6, color=C["INK"])

def render_before_after(rc, p, C):
    rc.page(p["title"], p["subtitle"], p["note"])
    rows = p["rows"]  # [(old_title, new_title)]
    rc.text(p["left_header"], 40, 240, 240, 20, size=11, bold=True, color=C["MUTED"])
    rc.text(p["right_header"], 330, 240, 225, 20, size=11, bold=True, color=C["GREEN"])
    for i, (old, new) in enumerate(rows):
        t = 268 + i * 92
        rc.rect(40, t, 240, 78, fill="#EFF1F0", radius=8)
        rc.text(old, 52, t + 12, 216, 58, size=9.6, color=C["INK"])
        rc.arrow(284, t + 39, 326, t + 39)
        rc.rect(330, t, 225, 78, fill="#EDF2EC", radius=8)
        rc.text(new, 342, t + 12, 201, 58, size=9.6, bold=True, color=C["INK"])
    rc.text(p["footer"], 40, 660, 515, 55, size=9.8, color=C["MUTED"])

def render_text_card(rc, p, C):
    rc.page(p["title"], p["subtitle"], p["note"])
    for b in p["left_blocks"]:  # {"top", "text", "size", "colorkey"}
        rc.text(b["text"], 40, b["top"], 245, b.get("h", 120),
                size=b.get("size", 10), color=C[b.get("colorkey", "INK")])
    card = p["card"]
    rc.rect(310, card["top"], 245, card["h"], fill="#FFFFFF", radius=12)
    rc.rect(310, card["top"], 245, 6, fill=C[card["colorkey"]], radius=6)
    rc.text(card["title"], 326, card["top"] + 17, 213, 22, size=12.5, bold=True, color=C[card["colorkey"]])
    rc.text(card["body"], 326, card["top"] + 47, 213, card["h"] - 60, size=9.8, color=C["INK"])
    if p.get("footer"):
        f = p["footer"]
        rc.text(f["text"], 40, f["top"], 245, 90, size=9.8, color=C["MUTED"])

def render_plan(rc, p, C):
    rc.page(p["title"], p["subtitle"], p["note"])
    headers = p["headers"]  # ["优先","动作","交付物","验证方法","依赖"]
    xs = [40, 86, 216, 342, 476]
    ws = [40, 120, 150, 140, 80]
    for x, w, h in zip(xs, ws, headers):
        rc.text(h, x, 240, w, 20, size=11, bold=True, color=C["MUTED"])
    for i, row in enumerate(p["rows"]):  # [(no, act, deliver, verify, dep)]
        t = 268 + i * 118
        rc.rect(40, t, 515, 104, fill="#FFFFFF", radius=10)
        rc.rect(40, t, 6, 104, fill=C["GREEN"], radius=6)
        rc.text(row[0], 52, t + 12, 28, 27, size=16, bold=True, color=C["GREEN"])
        rc.text(row[1], 86, t + 12, 122, 84, size=10.2, bold=True, color=C["INK"])
        for j, cell in enumerate(row[2:]):
            rc.text(cell, xs[j + 2], t + 12, ws[j + 2] - 10, 84, size=9.2, color=C["INK"])
    rc.text(p["footer"], 40, 640, 515, 40, size=9.8, color=C["MUTED"])

def render_sources(rc, p, C):
    rc.page(p["title"], p["subtitle"], p["note"])
    for b in p["blocks"]:  # {"top","title","body","h"}
        rc.text(b["title"], 40, b["top"], 515, 20, size=11.5, bold=True, color=C["INK"])
        rc.text(b["body"], 40, b["top"] + 26, 515, b["h"], size=9.4, color=C["INK"])
    rc.text(p["footer"], 40, p["footer_top"], 515, 60, size=9, color=C["MUTED"])

RENDERERS = {
    "cover": render_cover, "journey": render_journey, "bars": render_bars,
    "before_after": render_before_after, "text_card": render_text_card,
    "plan": render_plan, "sources": render_sources,
}

def main():
    if len(sys.argv) < 3:
        print("用法: python report_template.py <data.json> <out.pdf>")
        sys.exit(1)
    d = load(sys.argv[1])
    out = sys.argv[2]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pdf_components import ReportCanvas
    font = d.get("font") or r"C:\Windows\Fonts\Deng.ttf"
    bold = d.get("font_bold") or r"C:\Windows\Fonts\Dengb.ttf"
    palette = dict(PALETTE)
    palette.update(d.get("colors", {}))
    rc = ReportCanvas(out, font, bold, store=d["store"], observed=d["observed"])
    for p in d["pages"]:
        RENDERERS[p["type"]](rc, p, palette)
    rc.save()
    print("OK", out)

if __name__ == "__main__":
    main()
