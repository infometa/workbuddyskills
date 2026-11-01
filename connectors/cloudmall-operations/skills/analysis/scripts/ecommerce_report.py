#!/usr/bin/env python3
"""
ecommerce_report.py — 电商数据分析 HTML 报告生成器

读取 report_data.json（schema 见 references/domains/trade/report_data_schema.md），
渲染为精装 HTML 报告（CSS + Chart.js，零外部依赖除 CDN）。

report_data.json 包含两部分：
  1. SQL 原始数据（overview / daily_summary / refund_by_category / weekly_trend）
  2. 主控撰写的文案（executive_summary / highlights / insights / findings / recommendations）

CLI 接口：
  python ecommerce_report.py \
    --data-file report_data.json \
    --output report.html
"""

import argparse
import html as html_mod
import json
import os
from datetime import datetime
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
# 格式化工具
# ═══════════════════════════════════════════════════════════════

def _sf(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _si(val, default=0):
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _esc(s):
    return html_mod.escape(str(s)) if s else ""


def fmt_yuan(n):
    if n is None:
        return "-"
    v = _sf(n)
    if abs(v) >= 1e8:
        return f"¥{v / 1e8:.2f}亿"
    if abs(v) >= 1e4:
        return f"¥{v / 1e4:.2f}万"
    return f"¥{v:,.0f}"


def fmt_yuan_simple(n):
    if n is None:
        return "-"
    return f"¥{_sf(n):,.1f}"


def fmt_num(n):
    if n is None:
        return "-"
    return f"{_si(n):,}"


def fmt_pct(n, decimals=1):
    if n is None:
        return "-"
    return f"{_sf(n):.{decimals}f}%"


def fmt_decimal(n, decimals=2):
    if n is None:
        return "-"
    return f"{_sf(n):.{decimals}f}"


def fmt_change(current, previous, unit="%", positive_good=True):
    """计算变化并返回 (显示文本, css_class)"""
    c, p = _sf(current), _sf(previous)
    if p == 0:
        return "-", "neutral"
    if unit == "%":
        diff = (c - p) / abs(p) * 100
        text = f"{'▲' if diff > 0 else '▼'} {'+' if diff > 0 else ''}{diff:.1f}% 环比"
    elif unit == "pp":
        diff = c - p
        text = f"{'▲' if diff > 0 else '▼'} {'+' if diff > 0 else ''}{diff:.1f}个百分点"
    else:  # abs
        diff = c - p
        text = f"{'▲' if diff > 0 else '▼'} {'+' if diff > 0 else ''}{diff:.2f}"

    if diff > 0:
        cls = "up" if positive_good else "warn"
    elif diff < 0:
        cls = "down" if positive_good else "up"
    else:
        cls = "neutral"
    return text, cls


def fmt_date_short(d):
    """YYYYMMDD → MM-DD"""
    if isinstance(d, str) and len(d) == 8:
        return f"{d[4:6]}-{d[6:]}"
    return str(d)


def _weekday_cn(d):
    """YYYYMMDD → 星期X"""
    days = ["一", "二", "三", "四", "五", "六", "日"]
    try:
        dt = datetime.strptime(str(d), "%Y%m%d")
        return days[dt.weekday()]
    except (ValueError, TypeError):
        return ""


# ═══════════════════════════════════════════════════════════════
# 衍生指标计算
# ═══════════════════════════════════════════════════════════════

def compute_derived(ov: dict) -> dict:
    """从 overview 原始字段计算所有衍生指标。"""
    gmv = _sf(ov.get("gmv"))
    pay_uv = _sf(ov.get("pay_uv"))
    pay_cnt = _sf(ov.get("pay_cnt"))
    order_uv = _sf(ov.get("order_uv"))
    order_amt = _sf(ov.get("order_amt"))
    sales_qty = _sf(ov.get("sales_qty"))
    refund_amt = _sf(ov.get("refund_amt"))
    refund_uv = _sf(ov.get("refund_uv"))

    return {
        "aov": gmv / pay_uv if pay_uv else 0,
        "aov_order": gmv / pay_cnt if pay_cnt else 0,
        "attach_rate": sales_qty / pay_cnt if pay_cnt else 0,
        "buy_freq": pay_cnt / pay_uv if pay_uv else 0,
        "order_pay_cvr": pay_uv / order_uv if order_uv else 0,
        "order_pay_amt_loss": 1 - gmv / order_amt if order_amt else 0,
        "refund_rate": refund_amt / gmv * 100 if gmv else 0,
        "refund_penetration": refund_uv / pay_uv * 100 if pay_uv else 0,
        "refund_per_user": refund_amt / refund_uv if refund_uv else 0,
        "net_gmv": gmv - refund_amt,
    }


# ═══════════════════════════════════════════════════════════════
# 通用工具函数（供 report_plugins 引用）
# ═══════════════════════════════════════════════════════════════

def _color_span(val, fmt_str="+{:.1f}%", positive_good=True, unit=None):
    """生成带颜色的 HTML span。unit='pp' 时显示个百分点。"""
    v = _sf(val)
    if v > 0:
        color = "#22C55E" if positive_good else "#EF4444"
    elif v < 0:
        color = "#EF4444" if positive_good else "#22C55E"
    else:
        color = "#6B7B8D"
    if unit == "pp":
        text = f"{'+' if v > 0 else ''}{v:.1f}个百分点"
    else:
        text = fmt_str.format(v) if v >= 0 else fmt_str.replace("+", "").format(v)
    return f"<span style='color:{color}'>{text}</span>"


def _pct_change(cur, prev):
    """计算环比变化百分比，prev=0 时返回 None。"""
    c, p = _sf(cur), _sf(prev)
    if p == 0:
        return None
    return (c - p) / abs(p) * 100




# ═══════════════════════════════════════════════════════════════
# 插件化报告生成器（业务逻辑已拆到 report_plugins/ 目录）
# ═══════════════════════════════════════════════════════════════
# 注意：不能在模块级 import report_plugins（循环依赖），
# 改为在 build_html() 和 shim 函数中延迟导入。


# 保留原函数名作为 shim，兼容可能的外部调用
def generate_trade_findings(data: dict) -> list:
    """[已迁移] 实际逻辑在 report_plugins/trade_weekly.py"""
    from report_plugins.trade_weekly import generate_findings
    return generate_findings(data)


def generate_store_benchmark_findings(data: dict) -> list:
    """[已迁移] 实际逻辑在 report_plugins/store_benchmark.py"""
    from report_plugins.store_benchmark import generate_findings
    return generate_findings(data)


_ORIGINAL_CODE_REMOVED = True  # 原 ~880 行业务逻辑已搬到 report_plugins/


CSS = """\
:root {
    --primary: #0F172A; --primary-light: #1E3A8A; --secondary: #334155;
    --accent: #EF4444; --accent-gold: #CA8A04; --success: #22C55E;
    --warning: #F59E0B; --bg-primary: #FFFFFF; --bg-section: #F8FAFC;
    --bg-card: #FFFFFF; --bg-kpi: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
    --text-primary: #020617; --text-secondary: #334155; --text-muted: #6B7B8D;
    --text-on-dark: #FFFFFF; --border: #E2E8F0; --border-light: #F0F3F7;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06); --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
    --radius-sm: 6px; --radius-md: 10px; --radius-lg: 16px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif; color: var(--text-primary); background: var(--bg-primary); line-height: 1.7; font-size: 15px; -webkit-font-smoothing: antialiased; }
.container { max-width: 1080px; margin: 0 auto; padding: 0 40px; }
.cover { background: var(--bg-kpi); color: var(--text-on-dark); padding: 48px 0 36px; text-align: center; position: relative; overflow: hidden; border-bottom: 3px solid #CA8A04; }
.cover::before { content: ''; position: absolute; top: -50%; right: -20%; width: 600px; height: 600px; background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%); border-radius: 50%; }
.cover .brand { font-size: 13px; letter-spacing: 3px; text-transform: uppercase; opacity: 0.7; margin-bottom: 16px; }
.cover h1 { font-size: 36px; font-weight: 800; line-height: 1.3; margin-bottom: 10px; letter-spacing: -0.5px; }
.cover .subtitle { font-size: 15px; opacity: 0.8; margin-bottom: 20px; }
.cover .meta { font-size: 13px; opacity: 0.5; letter-spacing: 1px; }
.toc { background: var(--bg-section); border-bottom: 1px solid var(--border); padding: 12px 0; position: sticky; top: 0; z-index: 100; }
.toc-inner { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.toc-link { color: var(--text-secondary); text-decoration: none; font-size: 13px; font-weight: 500; padding: 6px 16px; border-radius: 20px; background: transparent; border: 1px solid var(--border); transition: all 0.2s; cursor: pointer; }
.toc-link:hover, .toc-link.active { color: #fff; background: var(--primary); border-color: var(--primary); }
.section { padding: 48px 0; border-bottom: 1px solid var(--border-light); }
.section:nth-child(even) { background: var(--bg-section); }
.section-header { margin-bottom: 32px; }
.section-header h2 { font-size: 26px; font-weight: 700; color: var(--primary); padding-bottom: 12px; border-bottom: 3px solid var(--primary); display: inline-block; }
.section-number { display: inline-block; background: var(--primary); color: white; width: 32px; height: 32px; border-radius: 50%; text-align: center; line-height: 32px; font-size: 14px; font-weight: 700; margin-right: 12px; vertical-align: middle; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin: 24px 0 32px; }
.kpi-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 20px 18px 16px; text-align: center; box-shadow: var(--shadow-sm); transition: transform 0.2s, box-shadow 0.2s; position: relative; overflow: hidden; }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
.kpi-card:nth-child(1)::before { background: #0F172A; } .kpi-card:nth-child(2)::before { background: #1E40AF; }
.kpi-card:nth-child(3)::before { background: #22C55E; } .kpi-card:nth-child(4)::before { background: #7C3AED; }
.kpi-card:nth-child(5)::before { background: #CA8A04; } .kpi-card:nth-child(6)::before { background: #06B6D4; }
.kpi-card:nth-child(7)::before { background: #EF4444; } .kpi-card:nth-child(8)::before { background: #F59E0B; }
.kpi-card:nth-child(9)::before { background: #059669; }
.kpi-card:hover { box-shadow: var(--shadow-md); }
.kpi-card .kpi-label { font-size: 12px; color: var(--text-muted); font-weight: 500; margin-bottom: 6px; }
.kpi-card .kpi-value { font-size: 28px; font-weight: 700; color: var(--primary); line-height: 1.2; font-variant-numeric: tabular-nums; }
.kpi-card .kpi-change { font-size: 12px; margin-top: 4px; font-weight: 600; }
.kpi-card .kpi-change.up { color: var(--success); } .kpi-card .kpi-change.down { color: var(--accent); } .kpi-card .kpi-change.warn { color: var(--warning); } .kpi-card .kpi-change.neutral { color: var(--text-muted); }
.kpi-card .kpi-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.kpi-flow-1::before { background: #0EA5E9; }
.kpi-flow-2::before { background: #38BDF8; }
.kpi-flow-3::before { background: #7C3AED; }
.insight-box { background: linear-gradient(135deg, #F0F7FF 0%, #E8F4FD 100%); border-left: 4px solid var(--secondary); border-radius: 0 var(--radius-md) var(--radius-md) 0; padding: 24px 28px; margin: 24px 0; }
.insight-box h3 { font-size: 16px; font-weight: 600; color: var(--primary); margin-bottom: 12px; }
.insight-list { list-style: none; padding: 0; }
.insight-list li { padding: 8px 0 8px 24px; position: relative; color: var(--text-secondary); font-size: 14px; line-height: 1.6; }
.insight-list li::before { content: ''; position: absolute; left: 0; top: 14px; width: 8px; height: 8px; background: var(--secondary); border-radius: 50%; }
.highlight-positive { background: #F0FFF4; border-left: 4px solid var(--success); border-radius: 0 var(--radius-sm) var(--radius-sm) 0; padding: 16px 20px; margin: 16px 0; }
.highlight-negative { background: #FFF5F5; border-left: 4px solid var(--accent); border-radius: 0 var(--radius-sm) var(--radius-sm) 0; padding: 16px 20px; margin: 16px 0; }
.highlight-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.highlight-positive .highlight-label { color: var(--success); } .highlight-positive .highlight-label::before { content: '▲ '; }
.highlight-negative .highlight-label { color: var(--accent); } .highlight-negative .highlight-label::before { content: '▼ '; }
.highlight-text { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }
.finding { margin-bottom: 40px; }
.finding h3 { font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; padding-left: 16px; border-left: 3px solid var(--secondary); }
.finding-content { font-size: 15px; color: var(--text-secondary); line-height: 1.8; }
.finding-content p { margin-bottom: 12px; }
.chart-container { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 24px; margin: 24px 0; box-shadow: var(--shadow-sm); }
.chart-container .chart-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; text-align: center; }
.chart-container canvas { max-height: 400px; }
.charts-pair-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 24px 0; }
.charts-pair-grid .chart-container { margin: 0; min-width: 0; }
.charts-pair-grid .chart-container canvas { max-height: 300px; }
.table-container { overflow-x: auto; margin: 20px 0; border-radius: var(--radius-md); box-shadow: var(--shadow-sm); border: 1px solid var(--border); }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
thead { background: var(--primary); color: white; }
thead th { padding: 12px 16px; text-align: left; font-weight: 600; font-size: 13px; letter-spacing: 0.3px; white-space: nowrap; }
tbody tr { border-bottom: 1px solid var(--border-light); transition: background 0.15s; }
tbody tr:nth-child(even) { background: var(--bg-section); }
tbody tr:hover { background: #E2E8F0; }
tbody td { padding: 10px 16px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
tbody td:first-child { font-weight: 500; color: var(--text-primary); }
.rec-grid { display: grid; grid-template-columns: 1fr; gap: 20px; margin: 24px 0; }
.rec-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 24px 24px 24px 28px; box-shadow: var(--shadow-sm); position: relative; overflow: hidden; display: flex; gap: 20px; align-items: flex-start; }
.rec-card::before { content: ''; position: absolute; top: 0; left: 0; bottom: 0; width: 4px; }
.rec-card:nth-child(1)::before { background: #EF4444; } .rec-card:nth-child(2)::before { background: #F59E0B; }
.rec-card:nth-child(3)::before { background: #22C55E; } .rec-card:nth-child(4)::before { background: #3B82F6; }
.rec-card:nth-child(5)::before { background: #8B5CF6; }
.rec-number { display: inline-flex; align-items: center; justify-content: center; min-width: 32px; width: 32px; height: 32px; border-radius: 50%; font-size: 14px; font-weight: 700; color: white; flex-shrink: 0; }
.rec-card:nth-child(1) .rec-number { background: #EF4444; } .rec-card:nth-child(2) .rec-number { background: #F59E0B; }
.rec-card:nth-child(3) .rec-number { background: #22C55E; } .rec-card:nth-child(4) .rec-number { background: #3B82F6; }
.rec-card:nth-child(5) .rec-number { background: #8B5CF6; }
.rec-card-body { flex: 1; min-width: 0; }
.rec-card h4 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; }
.rec-card .rec-content { font-size: 14px; color: var(--text-secondary); line-height: 1.7; }
.footer { text-align: center; padding: 32px 0; color: var(--text-muted); font-size: 12px; border-top: 1px solid var(--border); }
.footer .divider { width: 60px; height: 2px; background: var(--border); margin: 0 auto 16px; }
@media print { .toc { display: none; } .cover { padding: 40px 0 30px; } .section { page-break-inside: avoid; } .chart-container { page-break-inside: avoid; } body { font-size: 12px; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } }
@media (max-width: 768px) { .container { padding: 0 16px; } .cover h1 { font-size: 26px; } .kpi-grid { grid-template-columns: repeat(2, 1fr); } .charts-pair-grid { grid-template-columns: 1fr; } }
.funnel-chart { padding: 28px 32px 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md); margin: 24px 0; box-shadow: var(--shadow-sm); }
.funnel-chart-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 24px; text-align: center; }
.funnel-step { display: flex; align-items: center; gap: 16px; margin-bottom: 4px; }
.funnel-step-label { width: 68px; font-size: 12px; color: var(--text-muted); font-weight: 600; text-align: right; flex-shrink: 0; }
.funnel-bar-wrap { flex: 1; display: flex; align-items: center; }
.funnel-bar { height: 48px; border-radius: 6px; display: flex; align-items: center; padding: 0 16px; color: #fff; font-weight: 700; gap: 10px; min-width: 80px; }
.funnel-bar .f-num { font-size: 18px; font-weight: 800; }
.funnel-bar .f-pct { font-size: 12px; opacity: 0.85; background: rgba(0,0,0,0.15); padding: 2px 7px; border-radius: 10px; }
.funnel-step-rate { width: 130px; font-size: 12px; color: var(--text-secondary); flex-shrink: 0; padding-left: 12px; }
.funnel-step-rate .r-val { font-size: 14px; font-weight: 700; display: block; }
.funnel-step-rate .r-val.bad { color: var(--accent); }
.funnel-step-rate .r-val.good { color: var(--success); }
.funnel-arrow-row { display: flex; align-items: center; gap: 16px; margin: 3px 0; }
.funnel-arrow-row .arrow-spacer { width: 68px; flex-shrink: 0; }
.funnel-arrow-row .arrow-body { flex: 1; display: flex; align-items: center; gap: 6px; padding-left: 16px; font-size: 12px; color: var(--text-muted); }
.funnel-arrow-row .arrow-icon { font-size: 16px; color: #CBD5E1; }
"""


# ═══════════════════════════════════════════════════════════════
# HTML 渲染器
# ═══════════════════════════════════════════════════════════════

PRIORITY_EMOJI = {"P0": "🔴", "P1": "🟡", "P2": "🟢", "P3": "🔵"}
COLORS = ["#1E40AF", "#22C55E", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4", "#EC4899", "#0F172A"]


def _render_kpi_card(label, value_str, change_text, change_cls, sub=None, extra_class=""):
    sub_html = f'<div class="kpi-sub">{_esc(sub)}</div>' if sub else ""
    card_class = f"kpi-card {extra_class}".strip()
    return f"""\
<div class="{card_class}">
  <div class="kpi-label">{_esc(label)}</div>
  <div class="kpi-value">{value_str}</div>
  <div class="kpi-change {change_cls}">{_esc(change_text)}</div>
  {sub_html}
</div>"""


def _safe_rich(value):
    """Keep a small formatting vocabulary; never admit executable HTML or CSS."""
    from html.parser import HTMLParser
    import re

    class FormattingParser(HTMLParser):
        tags = {'span', 'strong', 'b', 'em', 'i', 'u', 'p', 'br', 'ul', 'ol', 'li', 'div', 'small'}
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
        def handle_starttag(self, tag, attrs):
            if tag not in self.tags:
                self.parts.append(html_mod.escape(self.get_starttag_text()))
                return
            safe = []
            for key, val in attrs:
                if key == 'class' and val and re.fullmatch(r'[A-Za-z0-9_ -]+', val):
                    safe.append(('class', val))
                elif key == 'style' and val:
                    declarations = []
                    for declaration in val.split(';'):
                        prop, sep, css = declaration.partition(':')
                        prop, css = prop.strip().lower(), css.strip()
                        valid = False
                        if prop in {'color', 'background', 'background-color'}:
                            valid = bool(re.fullmatch(r'#[0-9a-fA-F]{3,8}|(?:red|green|blue|white|black|transparent)', css))
                        elif prop == 'font-weight':
                            valid = bool(re.fullmatch(r'[1-9]00|bold|normal', css))
                        elif prop in {'width', 'height', 'font-size', 'margin-top', 'margin-bottom', 'padding-left'}:
                            valid = bool(re.fullmatch(r'\d+(?:\.\d+)?(?:px|%|em|rem)', css))
                        elif prop == 'text-align':
                            valid = css in {'left', 'right', 'center'}
                        if sep and valid:
                            declarations.append(prop + ':' + css)
                    if declarations:
                        safe.append(('style', ';'.join(declarations)))
            self.parts.append('<' + tag + ''.join(' ' + k + '="' + html_mod.escape(v, quote=True) + '"' for k, v in safe) + '>')
        def handle_endtag(self, tag):
            self.parts.append('</' + tag + '>' if tag in self.tags else html_mod.escape('</' + tag + '>'))
        def handle_data(self, data):
            self.parts.append(html_mod.escape(data))
        def handle_comment(self, data):
            pass
        def handle_decl(self, decl):
            pass

    parser = FormattingParser()
    parser.feed(str(value) if value is not None else '')
    parser.close()
    return ''.join(parser.parts)


def _render_table(headers, rows, summary_row=None):
    ths = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    trs = ""
    for row in rows:
        tds = "".join(f"<td>{_safe_rich(cell)}</td>" for cell in row)
        trs += f"<tr>{tds}</tr>\n"
    if summary_row:
        tds = "".join(f"<td>{_safe_rich(cell)}</td>" for cell in summary_row)
        trs += f'<tr style="font-weight:700;border-top:2px solid var(--border);background:#F0F3F7">{tds}</tr>\n'
    return f"""\
<div class="table-container">
  <table><thead><tr>{ths}</tr></thead>
  <tbody>{trs}</tbody></table>
</div>"""


def _script_json(value):
    """JSON embedded in HTML script text must not terminate its containing element."""
    return (json.dumps(value, ensure_ascii=True, allow_nan=False)
            .replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def _render_chart_script(chart_id, chart_type, data_cfg, options_cfg):
    """Render validated data, with callbacks selected only from trusted code."""
    import math
    import re

    def number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('chart numeric field must be a finite number')
        return value

    def color(value):
        if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', value):
            raise ValueError('chart color must be a six/eight-digit hex color')
        return value

    if chart_type not in ('line', 'bar', 'doughnut', 'radar', 'scatter'):
        raise ValueError('unsupported chart type')
    if not isinstance(chart_id, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', chart_id):
        raise ValueError('invalid chart id')
    allowed = {'y_format', 'hide_legend', 'index_axis', 'cutout', 'radar_max', 'x_title', 'y_title', 'stacked'}
    if not isinstance(options_cfg, dict) or set(options_cfg) - allowed:
        raise ValueError('unsupported chart option; raw JavaScript is forbidden')
    if options_cfg.get('y_format') not in (None, 'yuan', 'percent'):
        raise ValueError('unsupported y format')
    if options_cfg.get('index_axis') not in (None, 'x', 'y'):
        raise ValueError('unsupported index axis')
    datasets = []
    callbacks = []
    formatters = {
        'raw': 'function(v){return v;}',
        'yuan': "function(v){return '¥'+(v/10000).toFixed(1)+'万';}",
        'percent': "function(v){return (v>0?'+':'')+v+'%';}",
        'pct_plain': "function(v){return v+'%';}",
    }
    for i, ds in enumerate(data_cfg.get('datasets', [])):
        shade = color(ds.get('color', COLORS[i % len(COLORS)]))
        values = ds['data']
        if not isinstance(values, list):
            raise ValueError('chart data must be an array')
        for value in values:
            if value is None:
                continue
            if chart_type == 'scatter':
                if not isinstance(value, dict) or set(value) - {'x', 'y', 'label', 'r'}:
                    raise ValueError('invalid scatter point')
                number(value['x']); number(value['y'])
                if 'r' in value:
                    number(value['r'])
                if 'label' in value and not isinstance(value['label'], str):
                    raise ValueError('scatter label must be text')
            else:
                number(value)
        item = {'label': str(ds['label']), 'data': values}
        if chart_type == 'line':
            item.update(borderColor=shade, borderWidth=2.5, pointRadius=5, fill=bool(ds.get('fill')))
            if ds.get('fill'):
                item['backgroundColor'] = shade[:7] + '22'
            if ds.get('dash'):
                item.update(borderDash=[5, 5], pointRadius=3, borderWidth=1.5)
        elif chart_type in ('bar', 'doughnut'):
            shades = ds.get('colors')
            if shades is not None:
                if not isinstance(shades, list):
                    raise ValueError('colors must be an array')
                shades = [color(c) for c in shades]
            item['backgroundColor'] = shades or (shade if chart_type == 'bar' else [COLORS[j % len(COLORS)] for j in range(len(values))])
            if chart_type == 'bar':
                item['borderRadius'] = 4
            else:
                item.update(borderWidth=2, borderColor='#ffffff')
        elif chart_type == 'radar':
            item.update(borderColor=shade, backgroundColor=shade[:7] + '15', borderWidth=2.5, pointRadius=5)
        else:
            radius = number(ds.get('point_radius', 10))
            if radius < 0 or radius > 100:
                raise ValueError('point radius out of range')
            item.update(backgroundColor=shade, pointRadius=radius)
        if ds.get('show_datalabels'):
            fmt = ds.get('datalabel_format', 'raw')
            align = ds.get('datalabel_align', 'top')
            if fmt not in formatters or align not in ('top', 'bottom', 'left', 'right', 'center', 'start', 'end'):
                raise ValueError('unsupported data label format/alignment')
            item['datalabels'] = {'display': True, 'anchor': 'end', 'align': align, 'font': {'weight': 'bold', 'size': 10}, 'color': shade}
            callbacks.append(f'cfg.data.datasets[{i}].datalabels.formatter = {formatters[fmt]};')
        datasets.append(item)
    labels = data_cfg.get('labels', [])
    if not isinstance(labels, list) or any(not isinstance(v, (str, int, float)) or isinstance(v, bool) for v in labels):
        raise ValueError('invalid chart labels')
    options = {'responsive': True, 'maintainAspectRatio': True, 'layout': {'padding': {'top': 24}}}
    if options_cfg.get('index_axis'):
        options['indexAxis'] = options_cfg['index_axis']
    if chart_type == 'radar':
        maximum = number(options_cfg.get('radar_max', 100))
        if maximum <= 0:
            raise ValueError('radar maximum must be positive')
        options['scales'] = {'r': {'min': 0, 'max': maximum, 'ticks': {'display': False}, 'pointLabels': {'font': {'size': 12, 'weight': '600'}}}}
    elif chart_type == 'scatter':
        options['scales'] = {}
        for axis in ('x', 'y'):
            title = options_cfg.get(axis + '_title')
            if title:
                options['scales'][axis] = {'title': {'display': True, 'text': str(title)}}
    if options_cfg.get('y_format') and chart_type != 'radar':
        scales = options.setdefault('scales', {})
        y = scales.setdefault('y', {})
        y['ticks'] = {}
        y['grace'] = '10%' if options_cfg['y_format'] == 'yuan' else '15%'
        callback = "function(v){return '¥'+(v/10000).toFixed(0)+'万';}" if options_cfg['y_format'] == 'yuan' else "function(v){return v+'%';}"
        callbacks.append('cfg.options.scales.y.ticks.callback = ' + callback + ';')
    if chart_type == 'doughnut':
        cutout = options_cfg.get('cutout', '55%')
        if not isinstance(cutout, str) or not re.fullmatch(r'(?:[0-9]|[1-9][0-9]|100)%', cutout):
            raise ValueError('invalid doughnut cutout')
        options['cutout'] = cutout
    if 'stacked' in options_cfg:
        if not isinstance(options_cfg['stacked'], bool):
            raise ValueError('stacked must be boolean')
        scales = options.setdefault('scales', {})
        for axis in ('x', 'y'):
            scales.setdefault(axis, {})['stacked'] = options_cfg['stacked']
    if options_cfg.get('hide_legend'):
        options['plugins'] = {'legend': {'display': False}}
    cfg = {'type': chart_type, 'data': {'labels': labels, 'datasets': datasets}, 'options': options}
    return '(function(){var ctx=document.getElementById(' + _script_json(chart_id) + ');if(!ctx)return;var cfg=' + _script_json(cfg) + ';' + '\n'.join(callbacks) + 'new Chart(ctx,cfg);})();'


def build_html(data: dict) -> str:
    """构建完整 HTML 报告。

    Args:
        data: report_data.json 内容（数据 + 文案，schema 见 report_data_schema.md）
    """
    meta = data.get("meta", {})
    ov = data.get("overview", {})
    prev_ov = data.get("previous_overview", {})
    daily = data.get("daily_summary", [])
    prev_daily = data.get("previous_daily_summary", [])
    refund_cat = data.get("refund_by_category", [])
    weekly = data.get("weekly_trend", [])

    derived = compute_derived(ov)
    prev_derived = compute_derived(prev_ov) if prev_ov else {}

    brand = meta.get("brand_name", "")
    title = meta.get("title", "日常经营看板报告")
    cap_id = meta.get("capability_id", 1)
    _subtitle_map = {
        1: "周期经营全貌 · 增长驱动拆解 · 转化健康诊断",
        2: "门店效率对标 · 集中度分析 · 头尾差距诊断",
    }
    subtitle = _subtitle_map.get(cap_id, "经营数据分析报告")
    _raw_period = meta.get("period", f"{meta.get('start_date', '')} ~ {meta.get('end_date', '')}")
    period = f"统计周期：{_raw_period}"
    domain = meta.get("domain", "trade")
    domain_emoji = {"trade": "🟦", "commodity": "🟩", "user": "🟨", "marketing": "🟥", "cross": "🟪"}.get(domain, "🟦")
    generated_at = meta.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M"))

    chart_scripts = []

    # ── KPI Cards（按能力路由）──
    if cap_id == 2 and data.get("stores"):
        # 能力 2：门店对标 KPI
        stores = data.get("stores", [])
        n_stores = len(stores)
        total_gmv_s = sum(_sf(s.get("gmv")) for s in stores)
        top3_gmv_s = sum(_sf(s.get("gmv")) for s in stores[:3]) if n_stores >= 3 else total_gmv_s
        top3_pct_s = top3_gmv_s / total_gmv_s * 100 if total_gmv_s else 0
        best_s = stores[0] if stores else {}
        worst_s = stores[-1] if stores else {}
        best_aov = _sf(best_s.get("aov", _sf(best_s.get("gmv")) / _sf(best_s.get("pay_uv")) if _sf(best_s.get("pay_uv")) else 0))
        worst_aov = _sf(worst_s.get("aov", _sf(worst_s.get("gmv")) / _sf(worst_s.get("pay_uv")) if _sf(worst_s.get("pay_uv")) else 0))
        aov_ratio_s = best_aov / worst_aov if worst_aov else 0
        red_stores = sum(1 for s in stores if (_sf(s.get("refund_amt")) / _sf(s.get("gmv")) * 100 if _sf(s.get("gmv")) else 0) > 12)
        kpi_defs = [
            ("覆盖门店数", str(n_stores), None, None, "%", True, "全量在营门店"),
            (f"Top3 GMV 集中度", f"{top3_pct_s:.0f}%", None, None, "%", True, "⚠️ 头部依赖风险" if top3_pct_s > 60 else "健康"),
            ("最高客单价", fmt_yuan_simple(best_aov), None, None, "%", True, best_s.get("store_name", "")),
            ("最低客单价", fmt_yuan_simple(worst_aov), None, None, "%", True, worst_s.get("store_name", "")),
            ("头尾效率倍差", f"{aov_ratio_s:.1f}x", None, None, "%", True, "综合效率极差"),
            ("退款超标门店", str(red_stores) + " 家", None, None, "%", True, "退款率 >12%" if red_stores else "无"),
        ]
    else:
        # 能力 1：日常经营看板 KPI
        # ── 整体转化率（流量层第3张卡）──
        visit_uv_val    = _sf(ov.get("visit_uv"))
        prev_visit_uv_v = _sf(prev_ov.get("visit_uv")) if prev_ov else 0
        cvr_val      = _sf(ov.get("pay_uv")) / visit_uv_val * 100 if visit_uv_val else 0
        prev_cvr_val = _sf(prev_ov.get("pay_uv")) / prev_visit_uv_v * 100 if prev_visit_uv_v else 0
        kpi_defs = [
            # ── 流量层（3张，用 kpi-flow-N 固定颜色 class）──
            ("访问人数",  fmt_num(ov.get("visit_uv")), ov.get("visit_uv"),  prev_ov.get("visit_uv"),  "%",  True, "去重访客人数",  "kpi-flow-1"),
            ("访问次数",  fmt_num(ov.get("visit_pv")), ov.get("visit_pv"),  prev_ov.get("visit_pv"),  "%",  True, "总访问次数",    "kpi-flow-2"),
            ("转化率",  fmt_pct(cvr_val),            cvr_val,             prev_cvr_val,             "pp", True, "访问→支付",     "kpi-flow-3"),
            # ── 成交层（7张，去掉重复退款率和购买频次）──
            ("GMV（成交金额）", fmt_yuan(ov.get("gmv")),             ov.get("gmv"),            prev_ov.get("gmv"),            "%",  True,  None,          ""),
            ("支付人数",        fmt_num(ov.get("pay_uv")),            ov.get("pay_uv"),          prev_ov.get("pay_uv"),         "%",  True,  None,          ""),
            ("客单价",          fmt_yuan_simple(derived["aov"]),      derived["aov"],            prev_derived.get("aov"),       "%",  True,  None,          ""),
            ("笔单价",          fmt_yuan_simple(derived["aov_order"]),derived["aov_order"],      prev_derived.get("aov_order"), "%",  True,  "每笔订单金额",""),
            ("连带率",          fmt_decimal(derived["attach_rate"]),  derived["attach_rate"],    prev_derived.get("attach_rate"),"abs",True, "每单商品件数",""),
            ("退款率",          fmt_pct(derived["refund_rate"]),      derived["refund_rate"],    prev_derived.get("refund_rate"),"pp", False, None,         ""),
            ("净 GMV",          fmt_yuan(derived["net_gmv"]),         derived["net_gmv"],        prev_derived.get("net_gmv"),   "%",  True,  "GMV - 退款",  ""),
        ]

    kpi_cards_html = ""
    for item in kpi_defs:
        label, value_str, cur, prev, unit, pos_good = item[0], item[1], item[2], item[3], item[4], item[5]
        sub = item[6] if len(item) > 6 else None
        extra_class = item[7] if len(item) > 7 else ""
        change_text, change_cls = fmt_change(cur, prev, unit, pos_good) if prev else ("-", "neutral")
        kpi_cards_html += _render_kpi_card(label, value_str, change_text, change_cls, sub, extra_class) + "\n"

    # ── Highlights ──
    highlights = data.get("highlights", {})
    highlights_html = ""
    if highlights.get("positive"):
        h = highlights["positive"]
        highlights_html += f'<div class="highlight-positive"><div class="highlight-label">{_esc(h.get("label", "亮点"))}</div><div class="highlight-text">{_safe_rich(h.get("text", ""))}</div></div>\n'
    if highlights.get("negative"):
        h = highlights["negative"]
        highlights_html += f'<div class="highlight-negative"><div class="highlight-label">{_esc(h.get("label", "痛点"))}</div><div class="highlight-text">{_safe_rich(h.get("text", ""))}</div></div>\n'

    # ── Insights ──
    insights = data.get("insights", [])
    insights_html = ""
    if insights:
        items = "".join(f"<li>{_safe_rich(item)}</li>" for item in insights)
        insights_html = f'<div class="insight-box"><h3>关键洞察</h3><ul class="insight-list">{items}</ul></div>'

    # ── TOC sections (dynamic) ──
    toc_items = ["核心结论概览"]
    findings_narr = data.get("findings", [])
    # ★ 插件化：无 findings 时按 capability_id 路由到对应的自动生成器
    if not findings_narr:
        from report_plugins import get_findings_generator
        generate_fn = get_findings_generator(cap_id)
        findings_narr = generate_fn(data)
    if findings_narr:
        toc_items.append("核心分析发现")
    recommendations = data.get("recommendations", [])
    if recommendations:
        toc_items.append("业务优化建议")
    appendix = data.get("appendix_tables", [])
    # ★ 自动生成默认附录（按能力路由）
    if not appendix:
        if cap_id == 2:
            appendix = [
                {"title": "指标说明", "headers": ["指标名称", "说明"], "rows": [
                    ["Top 3 集中度", "销售额最高的 3 家门店合计占全网的比例，越高说明集中度越强"],
                    ["客单价", "每位实际付款顾客平均花了多少钱"],
                    ["下单转化率", "最终付款人数占下单人数的比例，越高说明支付流程越顺畅"],
                    ["退款率", "退款金额占成交金额的比例，越低越好"],
                    ["头尾效率倍差", "效率最高门店与最低门店之间的差距倍数，越小说明门店间均衡度越好"],
                    ["HHI 集中度指数", "衡量各门店销售额分布的集中程度，越小说明分布越均匀"],
                    ["连带率", "平均每笔订单购买了多少件商品，越高说明搭配销售越好"],
                ]},
            ]
        else:
            appendix = [
                {"title": "指标说明", "headers": ["指标", "说明"], "rows": [
                    ["GMV（成交金额）", "统计周期内所有订单的实际成交总金额"],
                    ["访问人数", "统计周期内访问店铺的去重用户数（访客数）"],
                    ["访问次数", "统计周期内店铺页面被浏览的总次数（同一用户多次访问计多次）"],
                    ["转化率", "最终支付人数占访问人数的比例，衡量从访问到购买的整体效率"],
                    ["支付人数", "统计周期内完成支付的去重用户数"],
                    ["客单价", "每位付款用户平均花费金额（GMV ÷ 支付人数）"],
                    ["笔单价", "每笔订单平均金额（GMV ÷ 支付订单数）"],
                    ["连带率", "平均每笔订单购买的商品件数，越高说明搭配购买越好"],
                    ["购买频次", "平均每位用户的购买笔数，越高说明复购越强"],
                    ["下单→支付转化率", "最终付款人数占下单人数的比例，越高说明支付流程越顺畅"],
                    ["金额折损率", "下单金额未转化为 GMV 的比例，反映优惠/取消对收入的侵蚀"],
                    ["退款率", "退款金额占 GMV 的比例，越低越好"],
                    ["退款渗透率", "申请退款的用户占支付用户的比例"],
                    ["退款人均金额", "每位退款用户平均退了多少钱"],
                    ["净 GMV", "GMV 扣除退款后的实际到手收入"],
                ]},
            ]
    if appendix:
        toc_items.append("附录")

    toc_html = ""
    for i, item in enumerate(toc_items):
        toc_html += f'<span class="toc-link" onclick="document.getElementById(\'s{i+1}\').scrollIntoView({{behavior:\'smooth\'}})">{_esc(item)}</span>\n'

    # ── Section 1: Executive Overview ──
    summary_html = _safe_rich(data.get("executive_summary", ""))

    # ── Section 2: Findings ──
    findings_html = ""
    for fi, finding in enumerate(findings_narr):
        ftitle = _esc(finding.get("title", ""))
        fcontent = _safe_rich(finding.get("content_html", ""))

        # tables
        tables_html = ""
        for tbl in finding.get("tables", []):
            tables_html += _render_table(tbl["headers"], tbl["rows"], tbl.get("summary_row"))

        # charts
        charts_in_finding = finding.get("charts", [])
        charts_html = ""
        half_charts = [c for c in charts_in_finding if c.get("half_width")]
        full_charts = [c for c in charts_in_finding if not c.get("half_width")]

        if half_charts:
            pair_inner = ""
            for c in half_charts:
                pair_inner += f'<div class="chart-container"><div class="chart-title">{_esc(c["title"])}</div><canvas id="{_esc(c["id"])}"></canvas></div>\n'
                chart_scripts.append(_render_chart_script(c["id"], c["type"], c.get("data", {}), c.get("options", {})))
            charts_html += f'<div class="charts-pair-grid">{pair_inner}</div>\n'

        for c in full_charts:
            charts_html += f'<div class="chart-container"><div class="chart-title">{_esc(c["title"])}</div><canvas id="{_esc(c["id"])}"></canvas></div>\n'
            chart_scripts.append(_render_chart_script(c["id"], c["type"], c.get("data", {}), c.get("options", {})))

        findings_html += f"""\
<div class="finding">
  <h3>2.{fi+1} {ftitle}</h3>
  <div class="finding-content">{fcontent}</div>
  {charts_html}
  {tables_html}
</div>
"""

    # ── Section 3: Recommendations ──
    recs_html = ""
    for ri, rec in enumerate(recommendations):
        priority = rec.get("priority", "P2")
        if priority not in PRIORITY_EMOJI:
            priority = "P2"
        emoji = PRIORITY_EMOJI.get(priority, "🔵")
        rtitle = _esc(rec.get("title", ""))
        items_html = "".join(f"<li>{_safe_rich(item)}</li>" for item in rec.get("items", []))
        recs_html += f"""\
<div class="rec-card">
  <div class="rec-number">{ri+1}</div>
  <div class="rec-card-body">
    <h4>{emoji} {priority} {'紧急' if priority == 'P0' else '重要' if priority == 'P1' else '提升' if priority == 'P2' else '机会'}：{rtitle}</h4>
    <div class="rec-content"><ul>{items_html}</ul></div>
  </div>
</div>"""

    # ── Section 4: Appendix ──
    appendix_html = ""
    for atbl in appendix:
        appendix_html += f'<div class="section-header"><h2>{_esc(atbl.get("title", "附录"))}</h2></div>\n'
        appendix_html += _render_table(atbl["headers"], atbl["rows"])

    # ── Assemble sections ──
    section_idx = 1
    sections_html = ""

    # S1: Overview
    sections_html += f"""\
<div class="section" id="s{section_idx}">
  <div class="container">
    <div class="section-header"><h2><span class="section-number">{section_idx}</span>核心结论概览</h2></div>
    <div class="finding-content">{summary_html}</div>
    <div class="kpi-grid">{kpi_cards_html}</div>
    {highlights_html}
    {insights_html}
  </div>
</div>
"""
    section_idx += 1

    # S2: Findings
    if findings_html:
        sections_html += f"""\
<div class="section" id="s{section_idx}">
  <div class="container">
    <div class="section-header"><h2><span class="section-number">{section_idx}</span>核心分析发现</h2></div>
    {findings_html}
  </div>
</div>
"""
        section_idx += 1

    # S3: Recommendations
    if recs_html:
        sections_html += f"""\
<div class="section" id="s{section_idx}">
  <div class="container">
    <div class="section-header"><h2><span class="section-number">{section_idx}</span>业务优化建议</h2></div>
    <div class="rec-grid">{recs_html}</div>
  </div>
</div>
"""
        section_idx += 1

    # S4: Appendix
    if appendix_html:
        sections_html += f"""\
<div class="section" id="s{section_idx}">
  <div class="container">
    {appendix_html}
  </div>
</div>
"""

    # ── Chart.js scripts ──
    all_chart_js = "\n".join(chart_scripts)

    # ── Final HTML ──
    return f"""\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)} — {_esc(brand)}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
{CSS}
</style>
</head>
<body>

<div class="cover">
  <div class="container">
    <h1>{_esc(title)}</h1>
    <div class="subtitle">{_esc(brand)} · {_esc(subtitle)}</div>
    <div class="meta">{_esc(period)}</div>
  </div>
</div>

<nav class="toc">
  <div class="container">
    <div class="toc-inner">
      {toc_html}
    </div>
  </div>
</nav>

{sections_html}

<div class="footer">
  <div class="container">
    <div class="divider"></div>
    <p>Generated by AI Analysis &middot; ecommerce-data-analyst Skill</p>
    <p style="margin-top: 4px; opacity: 0.6;">本报告由 AI 自动生成 &middot; {_esc(generated_at)}</p>
  </div>
</div>

<script>
Chart.register(ChartDataLabels);
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", sans-serif';
Chart.defaults.font.size = 12;
Chart.defaults.color = '#6B7B8D';
Chart.defaults.plugins.legend.position = 'bottom';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.elements.bar.borderRadius = 4;
Chart.defaults.elements.line.tension = 0.3;
Chart.defaults.scale.grid.color = '#F0F3F7';
Chart.defaults.plugins.datalabels = {{ display: false }};
const COLORS = {json.dumps(COLORS)};

{all_chart_js}
</script>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="电商数据分析 HTML 报告生成器")
    parser.add_argument("--data-file", required=True, help="report_data.json 路径（数据+文案）")
    parser.add_argument("--output", required=True, help="输出 HTML 文件路径")
    args = parser.parse_args()

    # 加载数据（数据 + 文案统一在一个 JSON）
    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = build_html(data)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 报告已生成: {args.output}")


if __name__ == "__main__":
    main()