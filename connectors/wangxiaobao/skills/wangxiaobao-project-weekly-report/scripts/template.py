#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地产项目营销周报生成器 - 完整HTML模板
使用方法：
  1. 修改顶部 DATA 区的数据变量和洞察文本
  2. 运行: python template.py
  3. 输出: [项目名]_周报_[日期].html + [项目名]_周报_[日期].pdf
"""

import datetime
import subprocess
import os
import sys

# ================================================================
#  DATA 区 - 修改这里的数据和洞察即可，其余全部自动生成
# ================================================================

# -- 基本信息 --
# 项目标识默认从环境变量读取，未设置时使用中性占位符。
# 实际运行时这些值会被 generate_report.py 用 weekly_report_data.json 覆盖。
project_name = os.environ.get("XIAOBAO_PROJECT_NAME", "<项目名>")
brand_text = os.environ.get("XIAOBAO_BRAND_TEXT", "<项目名>项目 · 周度来访与成交深度分析")
week_label = "W1"
date_start = "2026.01.01"
date_end = "2026.01.07"
data_date = "2026.01.07 23:30"

# 注意：以下业务数据变量仅为占位/结构示例，运行时由 generate_report.py
# 用 weekly_report_data.json 的真实数据覆盖。请勿在此填写特定项目数据。

# -- 本周每日来访 [(日期str, 星期str, 来访量int), ...] --
week_days = []

# -- 上周每日来访 --
last_week_days = []

# -- 本月每日来访 [(日期str, 星期str, 来访量int), ...] --
may_days = []

# -- 顾问本周接待 [(姓名, 本周量, 占比%, 上周量, 环比%)] --
consultants_this = []

# -- 首访/复访 --
first_visit = 0
repeat_visit = 0

# -- 盘客完成量 --
panke_done = 0

# -- 意向等级：旺小宝API {"等级": 数量, ...} --
intent_api = {}

# -- 意向等级：盘客系统 {"等级": 数量, ...} --
intent_panke = {}

# -- 横向柱状图数据 [(标签, 值, 占比%), ...] --
house_types = []
budgets = []
channels = []
resistance = []
purposes = []
focus_points = []
payments = []
cycles = []
downpay = []

# -- 成交数据 --
deals_total = 0
deals_amount = 0
house_type_deals = []
channel_deals = []
deal_cycle = []

# -- 月度目标（示例值，可通过环境变量或 generate_report.py 覆盖）--
visit_target = int(os.environ.get("XIAOBAO_VISIT_TARGET", 500))   # 示例值
sales_target = int(os.environ.get("XIAOBAO_SALES_TARGET", 21000))  # 示例值

# -- 月度成交趋势 [(月份, 2025套数, 2025金额, 2026套数, 2026金额, 同比str)] --
monthly_trend = []
monthly_trend_total = ("合计/平均", "", "", "", "", "")

# -- 交叉分析表：看房周期 × 意向等级 --
# [周期, A, B, C, D, E, F, 合计]
cross_cycle_intent = []

# -- 交叉分析表：置业目的 × 意向等级 --
# [目的, A, B, C, D, E, 合计]
cross_purpose_intent = []

# -- 交叉分析表：渠道 × 意向等级 --
# [渠道, A, B, C, D, E, F, 合计, A+B率]
cross_channel_intent = []

# -- 下周建议 [(优先级, 行动项, 责任人, 时间节点)] --
suggestions = []

# ================================================================
#  洞察文本 - 根据新数据重新撰写，支持 {变量} 引用
#  注意：以下均为占位，运行时由 generate_report.py 根据数据覆盖。
#  *_tpl 变量保留 {占位符} 以便 fmt() 正常格式化；请勿在此填写特定项目内容。
# ================================================================

insight_core_tpl = "<运行时由数据生成>"

insight_trend_tpl = "<运行时由数据生成>"

risk_trend_tpl = "<运行时由数据生成>"

insight_budget = ""

insight_cycle = ""

insight_purpose = ""

insight_channel = ""

risk_resistance = ""

insight_resistance = ""

insight_consultant = ""

finding_intent_tpl = "<运行时由数据生成>"

insight_intent = ""

insight_deals = ""

finding_deals = ""

insight_monthly_tpl = "<运行时由数据生成>"

summary_text_tpl = "<运行时由数据生成>"


# ================================================================
#  自动计算 - 以下不需要修改
#  （含 0 除保护，使占位空数据下 import 不报错；generate_html() 会按
#    实际数据重算并覆盖这些派生变量）
# ================================================================

week_total = sum(v for _, _, v in week_days)
week_avg = week_total / 7 if week_days else 0
last_week_total = sum(v for _, _, v in last_week_days)
may_total = sum(v for _, _, v in may_days)
wow_change = (week_total - last_week_total) / last_week_total * 100 if last_week_total > 0 else 0
wow_pct = abs(wow_change)
wow_direction = "下降" if wow_change < 0 else "增长"
first_pct = first_visit / week_total * 100 if week_total > 0 else 0
repeat_pct = repeat_visit / week_total * 100 if week_total > 0 else 0
panke_rate = panke_done / week_total * 100 if week_total > 0 else 0
intent_api_total = sum(intent_api.values())
intent_panke_total = sum(intent_panke.values())
api_ab = (intent_api.get('A', 0) + intent_api.get('B', 0)) / intent_api_total * 100 if intent_api_total > 0 else 0
panke_ab = (intent_panke.get('A', 0) + intent_panke.get('B', 0) + intent_panke.get('C+', 0)) / intent_panke_total * 100 if intent_panke_total > 0 else 0
api_c = intent_api.get('C', 0) / intent_api_total * 100 if intent_api_total > 0 else 0
panke_c = intent_panke.get('C', 0) / intent_panke_total * 100 if intent_panke_total > 0 else 0
visit_progress = may_total / visit_target * 100 if visit_target > 0 else 0
time_progress = 18 / 31 * 100
achievement_rate = visit_progress / time_progress * 100 if time_progress > 0 else 0
may_days_count = len(may_days)

# 工作日/周末均值
wd_this = week_days[0:4]
wd_last = last_week_days[0:4]
wd_avg = round(sum(v for _, _, v in wd_this) / len(wd_this), 1) if wd_this else 0
last_wd_avg = round(sum(v for _, _, v in wd_last) / len(wd_last), 1) if wd_last else 0
wd_drop = round((1 - sum(v for _, _, v in wd_this) / sum(v for _, _, v in wd_last)) * 100, 0) if wd_last and sum(v for _, _, v in wd_last) > 0 else 0

# 填充洞察变量
def fmt(template, **kw):
    try:
        return template.format(**kw)
    except Exception:
        return template

insight_core = fmt(insight_core_tpl, week_total=week_total, wow_pct=f"{wow_pct:.1f}",
    wd_avg=wd_avg, last_wd_avg=last_wd_avg, wd_drop=wd_drop,
    sat_val=week_days[4][2] if len(week_days) > 4 else 0, repeat_pct=f"{repeat_pct:.1f}",
    repeat_up=f"{repeat_pct - 16.1:.1f}", panke_pct=f"{panke_rate:.1f}")

insight_trend = fmt(insight_trend_tpl, wd_avg=wd_avg, last_wd_avg=last_wd_avg, wd_drop=wd_drop,
    sat_val=week_days[4][2] if len(week_days) > 4 else 0,
    last_sat=last_week_days[4][2] if len(last_week_days) > 4 else 0,
    sat_drop=f"{(1 - week_days[4][2]/last_week_days[4][2]) * 100:.1f}" if len(week_days) > 4 and len(last_week_days) > 4 and last_week_days[4][2] > 0 else "0.0",
    sun_val=week_days[5][2] if len(week_days) > 5 else 0,
    last_sun=last_week_days[5][2] if len(last_week_days) > 5 else 0,
    sun_drop=f"{(1 - week_days[5][2]/last_week_days[5][2]) * 100:.1f}" if len(week_days) > 5 and len(last_week_days) > 5 and last_week_days[5][2] > 0 else "0.0",
    wknd_loss=((last_week_days[4][2]+last_week_days[5][2])-(week_days[4][2]+week_days[5][2])) if len(week_days) > 5 and len(last_week_days) > 5 else 0,
    retention=f"{week_days[5][2]/week_days[4][2]*100:.1f}" if len(week_days) > 5 and week_days[4][2] > 0 else "0.0")

risk_trend = fmt(risk_trend_tpl, mon_val=week_days[6][2] if len(week_days) > 6 else 0)

insight_monthly = fmt(insight_monthly_tpl, achieve_rate=f"{achievement_rate:.1f}",
    no_holiday_avg=round((may_total - 166) / 14, 0) if may_total > 166 else 0,
    projected=round((may_total - 166) / 14 * 31 + 166, 0) if may_total > 166 else 0)

finding_intent = fmt(finding_intent_tpl, api_ab=f"{api_ab:.1f}", panke_ab=f"{panke_ab:.1f}",
    api_c=f"{api_c:.1f}", panke_c=f"{panke_c:.1f}")

summary_text = fmt(summary_text_tpl, week_total=week_total, wow_pct=f"{wow_pct:.1f}",
    panke_pct=f"{panke_rate:.1f}", repeat_pct=f"{repeat_pct:.1f}")


# ================================================================
#  HTML 生成函数 - 以下不需要修改
# ================================================================

def hbar(data, max_val=None):
    """横向柱状图"""
    if not data:
        return ""
    if max_val is None:
        max_val = max(v for _, v, _ in data) or 1
    lines = []
    for label, val, pct in data:
        width = val / max_val * 100
        lines.append(f'<div class="bar-row"><span class="bar-label">{label}</span><div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div><span class="bar-val">{val}组<small>({pct:.1f}%)</small></span></div>')
    return "\n".join(lines)


def donut_svg(data, size=160, stroke=24):
    """SVG圆环图"""
    if not data:
        return ""
    total = sum(v for _, v, _ in data) or 1
    colors = ["#1A3C6E", "#3B7DD8", "#63B3ED", "#A0D2F5", "#C6E0F7", "#E2E8F0"]
    cx, cy = size // 2, size // 2
    r = (size - stroke) // 2
    circ = 2 * 3.14159265 * r
    segs = []
    offset = 0
    for i, (label, val, pct) in enumerate(data):
        dash = val / total * circ
        color = colors[i % len(colors)]
        segs.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}" stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-dashoffset="-{offset:.1f}" />')
        offset += dash
    legend = ""
    for i, (label, val, pct) in enumerate(data):
        color = colors[i % len(colors)]
        legend += f'<div class="donut-legend-item"><span class="dot" style="background:{color}"></span><span>{label} {val}({pct:.1f}%)</span></div>'
    svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(segs)}</svg>'
    return f'<div class="donut-wrap"><div class="donut-chart">{svg}</div><div class="donut-legend">{legend}</div></div>'


def vbar_week(days_data, last_data):
    """本周每日柱状图（含环比）"""
    if not days_data:
        return ""
    max_val = max(v for _, _, v in days_data) or 1
    bars = []
    for i, (date, wd, val) in enumerate(days_data):
        height = val / max_val * 100
        prev = last_data[i][2] if i < len(last_data) else 0
        change = val - prev
        cls = "up" if change > 0 else "down"
        change_str = f"+{change}" if change > 0 else str(change)
        bars.append(f'<div class="bar-day"><div class="bar-day-val">{val}</div><div class="bar-day-col"><div class="bar-day-fill" style="height:{height:.1f}%"></div></div><div class="bar-day-label">{date}<br><small>{wd}</small></div><div class="bar-day-change {cls}">{change_str}</div></div>')
    return "\n".join(bars)


def vbar_month(days_data):
    """月度每日柱状图"""
    if not days_data:
        return ""
    max_val = max(v for _, _, v in days_data) or 1
    bars = []
    for date, wd, val in days_data:
        height = val / max_val * 100
        is_wkend = wd in ["周六", "周日"]
        cls = "month-bar" + (" weekend" if is_wkend else "")
        day_num = date.split(".")[1]
        bars.append(f'<div class="{cls}"><div class="month-bar-val">{val}</div><div class="month-bar-col"><div class="month-bar-fill" style="height:{height:.1f}%"></div></div><div class="month-bar-label">{day_num}<br><small>{wd}</small></div></div>')
    return "\n".join(bars)


def cross_cycle_table(rows):
    """看房周期 × 意向等级"""
    h = '<table class="cross-table">\n<tr><th>周期</th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>F</th><th>合计</th></tr>\n'
    for r in rows:
        h += f'<tr><td>{r[0]}</td>'
        for c in r[1:]:
            h += f'<td>{c}</td>'
        h += '</tr>\n'
    h += '</table>'
    return h


def cross_purpose_table(rows):
    """置业目的 × 意向等级"""
    h = '<table class="cross-table">\n<tr><th>目的</th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>合计</th></tr>\n'
    for r in rows:
        h += f'<tr><td>{r[0]}</td>'
        for c in r[1:]:
            h += f'<td>{c}</td>'
        h += '</tr>\n'
    h += '</table>'
    return h


def cross_channel_table(rows):
    """渠道 × 意向等级"""
    h = '<table class="cross-table">\n<tr><th>渠道</th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>F</th><th>合计</th><th>A+B率</th></tr>\n'
    for r in rows:
        h += f'<tr><td>{r[0]}</td>'
        for c in r[1:]:
            h += f'<td>{c}</td>'
        h += '</tr>\n'
    h += '</table>'
    return h


def render_suggestions(items):
    """建议表格"""
    tag_map = {"P0": "tag-red", "P1": "tag-yellow", "P2": "tag-blue"}
    h = '<table>\n<tr><th>优先级</th><th>行动项</th><th>责任人</th><th>时间节点</th></tr>\n'
    for p, action, person, deadline in items:
        cls = tag_map.get(p, "tag-blue")
        h += f'<tr>\n  <td><span class="tag {cls}">{p}</span></td>\n  <td>{action}</td>\n  <td>{person}</td>\n  <td>{deadline}</td>\n</tr>\n'
    h += '</table>'
    return h


def render_consultants(data):
    """顾问表格"""
    h = '<table>\n<tr><th>排名</th><th>顾问</th><th class="num">本周接待</th><th class="num">占比</th><th class="num">上周接待</th><th class="num">环比</th><th class="num">人均/天</th><th>状态</th></tr>'
    for i, (name, cnt, pct, last_cnt, chg) in enumerate(data, 1):
        if chg > 0:
            status, color = "↑", "#38A169"
        elif chg < -20:
            status, color = "↓", "#E53E3E"
        else:
            status, color = "→", "#A0AEC0"
        h += f'<tr><td>{i}</td><td><b>{name}</b></td><td class="num">{cnt}</td><td class="num">{pct:.1f}%</td><td class="num">{last_cnt}</td><td class="num" style="color:{color}">{chg:+.1f}%</td><td class="num">{cnt/7:.1f}</td><td><span style="color:{color};font-weight:600;">{status}</span></td></tr>'
    h += '</table>'
    return h


def render_intent_bars(data_dict):
    """意向等级柱状图"""
    max_val = max(data_dict.values())
    lines = []
    total = sum(data_dict.values())
    for label, val in data_dict.items():
        pct = val / total * 100
        width = val / max_val * 100
        lines.append(f'<div class="bar-row"><span class="bar-label">{label}级</span><div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div><span class="bar-val">{val}组<small>({pct:.1f}%)</small></span></div>')
    return "\n".join(lines)


def render_monthly_trend(rows, total_row):
    """月度成交趋势表"""
    h = '<table>\n<tr><th>月份</th><th class="num">2025套数</th><th class="num">2025金额(万)</th><th class="num">2026套数</th><th class="num">2026金额(万)</th><th class="num">同比</th></tr>\n'
    for r in rows:
        yoy = r[5]
        yoy_style = f' style="color:#E53E3E"' if yoy not in ["—", "待更新"] else ""
        h += f'<tr><td>{r[0]}</td><td class="num">{r[1]}</td><td class="num">{r[2]}</td><td class="num">{r[3]}</td><td class="num">{r[4]}</td><td class="num"{yoy_style}>{yoy}</td></tr>\n'
    h += f'<tr style="background:#F7FAFC; font-weight:600;"><td>{total_row[0]}</td><td class="num">{total_row[1]}</td><td class="num">{total_row[2]}</td><td class="num">{total_row[3]}</td><td class="num">{total_row[4]}</td><td class="num">{total_row[5]}</td></tr>\n'
    h += '</table>'
    return h


# ================================================================
#  完整 HTML 模板 - 以下不需要修改
# ================================================================

CSS = """  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif; background: #F0F4F8; color: #1A202C; line-height: 1.6; padding: 24px; }
  .container { max-width: 1200px; margin: 0 auto; }
  .header {
    background: linear-gradient(135deg, #1A3C6E 0%, #2A5298 100%);
    color: #fff; padding: 24px 32px; border-radius: 12px; margin-bottom: 20px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;
  }
  .header-brand { display: flex; align-items: center; gap: 12px; align-self: flex-start; margin-top: 2px; }
  .header-brand img { height: 32px; width: auto; }
  .header-center { text-align: center; flex: 1; }
  .header-center h1 { font-size: 26px; font-weight: 700; letter-spacing: 2px; }
  .header-center .sub { font-size: 13px; color: rgba(255,255,255,0.7); margin-top: 4px; }
  .header-right { text-align: right; }
  .header-right .period { font-size: 18px; font-weight: 600; }
  .header-right .cumulative { font-size: 13px; color: rgba(255,255,255,0.8); margin-top: 4px; }
  .header-right .cumulative b { font-size: 22px; color: #90CDF4; }
  .header-right .gen-time { font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 4px; }
  .card { background: #fff; border-radius: 10px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); padding: 20px 28px; margin-bottom: 20px; }
  .section-num { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: #1A3C6E; color: #fff; border-radius: 50%; font-size: 14px; font-weight: 700; margin-right: 8px; flex-shrink: 0; }
  .section-header { display: flex; align-items: center; font-size: 17px; font-weight: 700; color: #1A3C6E; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 2px solid #E2E8F0; }
  .section-sub { font-size: 14px; font-weight: 600; color: #2D3748; margin: 16px 0 10px; padding-left: 12px; border-left: 3px solid #3B7DD8; }
  .kpi-row { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }
  .kpi-card { flex: 1; min-width: 140px; background: #F7FAFC; border-radius: 8px; padding: 14px 16px; text-align: center; border-left: 3px solid #CBD5E0; }
  .kpi-card.primary { border-left-color: #1A3C6E; background: linear-gradient(135deg,#EDF2F7 0%,#E2E8F0 100%); }
  .kpi-card.success { border-left-color: #38A169; }
  .kpi-card.warning { border-left-color: #D69E2E; }
  .kpi-label { font-size: 12px; color: #718096; margin-bottom: 4px; }
  .kpi-value { font-size: 26px; font-weight: 700; color: #1A202C; }
  .kpi-delta { font-size: 11px; margin-top: 4px; }
  .kpi-delta.up { color: #E53E3E; }
  .kpi-delta.down { color: #38A169; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 10px 0; }
  th, td { padding: 9px 10px; text-align: left; border-bottom: 1px solid #EDF2F7; }
  th { background: #F7FAFC; font-weight: 600; color: #4A5568; font-size: 12px; }
  tr:hover td { background: #F7FAFC; }
  th.num, td.num { text-align: right; font-family: monospace; }
  .summary-table { table-layout: fixed; }
  .summary-table th:first-child, .summary-table td:first-child { width: 20%; }
  .summary-table th.num, .summary-table td.num { width: 16%; }
  .bar-chart { display: flex; flex-direction: column; gap: 8px; margin: 12px 0; }
  .bar-row { display: flex; align-items: center; gap: 10px; font-size: 13px; }
  .bar-label { width: 100px; flex-shrink: 0; text-align: right; color: #4A5568; }
  .bar-track { flex: 1; height: 22px; background: #EDF2F7; border-radius: 4px; overflow: hidden; position: relative; }
  .bar-fill { height: 100%; background: linear-gradient(90deg, #3B7DD8, #63B3ED); border-radius: 4px; }
  .bar-val { width: 90px; flex-shrink: 0; text-align: left; color: #2D3748; font-weight: 500; }
  .bar-val small { color: #A0AEC0; font-size: 11px; margin-left: 3px; }
  .vbar-chart { display: flex; align-items: flex-end; justify-content: center; gap: 16px; height: 260px; padding: 20px 10px 0; margin: 14px 0; border-bottom: 1px solid #E2E8F0; }
  .bar-day { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; max-width: 80px; }
  .bar-day-val { font-size: 14px; font-weight: 700; color: #1A202C; }
  .bar-day-col { width: 36px; height: 180px; background: #EDF2F7; border-radius: 4px 4px 0 0; position: relative; display: flex; align-items: flex-end; }
  .bar-day-fill { width: 100%; background: linear-gradient(180deg, #3B7DD8, #1A3C6E); border-radius: 4px 4px 0 0; min-height: 4px; }
  .bar-day-label { font-size: 12px; color: #4A5568; text-align: center; line-height: 1.3; }
  .bar-day-change { font-size: 10px; font-weight: 600; }
  .bar-day-change.up { color: #E53E3E; }
  .bar-day-change.down { color: #38A169; }
  .month-chart { display: flex; align-items: flex-end; gap: 4px; height: 200px; padding: 10px 4px 0; margin: 14px 0; border-bottom: 1px solid #E2E8F0; overflow-x: auto; }
  .month-bar { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; min-width: 36px; }
  .month-bar-val { font-size: 10px; font-weight: 600; color: #4A5568; }
  .month-bar-col { width: 24px; height: 140px; background: #EDF2F7; border-radius: 3px 3px 0 0; position: relative; display: flex; align-items: flex-end; }
  .month-bar-fill { width: 100%; background: linear-gradient(180deg, #63B3ED, #3B7DD8); border-radius: 3px 3px 0 0; min-height: 3px; }
  .month-bar.weekend .month-bar-fill { background: linear-gradient(180deg, #4299E1, #2B6CB0); }
  .month-bar-label { font-size: 9px; color: #718096; text-align: center; line-height: 1.2; }
  .donut-wrap { display: flex; align-items: center; gap: 24px; margin: 14px 0; flex-wrap: wrap; }
  .donut-chart { flex-shrink: 0; }
  .donut-legend { display: flex; flex-direction: column; gap: 6px; }
  .donut-legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #4A5568; }
  .donut-legend-item .dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .two-col { display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-start; }
  .two-col > div { flex: 1; min-width: 300px; align-self: flex-start; display: flex; flex-direction: column; justify-content: flex-start; }
  .insight { background: linear-gradient(135deg, #EBF8FF 0%, #E6FFFA 100%); border-left: 3px solid #3B7DD8; padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; color: #2D3748; margin: 14px 0; line-height: 1.7; }
  .insight strong { color: #1A3C6E; }
  .finding { background: #FFFBEB; border-left: 3px solid #D69E2E; padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; color: #744210; margin: 14px 0; line-height: 1.7; }
  .finding .tag { display: inline-block; background: #D69E2E; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 8px; }
  .risk-box { background: #FFF5F5; border-left: 3px solid #E53E3E; padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 12px; color: #742A2A; margin: 10px 0; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 6px; }
  .tag-blue { background: #EBF8FF; color: #2B6CB0; }
  .tag-green { background: #F0FFF4; color: #276749; }
  .tag-yellow { background: #FFFBEB; color: #975A16; }
  .tag-red { background: #FFF5F5; color: #C53030; }
  .cross-table th, .cross-table td { font-size: 12px; padding: 6px 8px; text-align: center; }
  .cross-table th { background: #EDF2F7; }
  .cross-table td:first-child { text-align: left; font-weight: 500; background: #F7FAFC; }
  .footer-bar { background: #fff; border-radius: 10px; padding: 14px 24px; margin-top: 16px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #718096; box-shadow: 0 1px 8px rgba(0,0,0,0.06); }
  .footer-brand { display: flex; align-items: center; gap: 8px; }
  .footer-brand img { height: 20px; width: auto; }
  @media (max-width: 768px) {
    .header { flex-direction: column; text-align: center; }
    .header-brand { order: 1; } .header-center { order: 2; } .header-right { order: 3; text-align: center; }
    .two-col { flex-direction: column; }
  }

  /* ===== 打印/PDF 优化 ===== */
  @page {
    size: 1200px 1697px;
    margin: 0;
  }
  @media print {
    body { margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .container { box-shadow: none; margin: 0; }
    .card { break-inside: avoid; }
    canvas { max-width: 100% !important; }
  }"""


# ================================================================
#  PDF 生成
# ================================================================

HTML2PDF_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html2pdf_fast.py")
# 使用当前 Python 解释器；若不可用则回退到 PATH 中的 python3。
PYTHON_EXE = sys.executable or "python3"
# PDF 页面尺寸：A4 横向（标准尺寸，显示兼容性好）
PDF_ARGS = ["--landscape"]

def generate_pdf(html_path: str) -> str:
    """
    调用 html2pdf.py 将 HTML 转换为 PDF。
    返回生成的 PDF 文件路径；失败时返回 None。
    """
    if not os.path.exists(HTML2PDF_SCRIPT):
        print(f"WARN: html2pdf.py not found at {HTML2PDF_SCRIPT}, skipping PDF generation.")
        return None

    pdf_path = html_path.rsplit(".", 1)[0] + ".pdf"
    print(f"Generating PDF (landscape): {pdf_path} ...")
    try:
        result = subprocess.run(
            [PYTHON_EXE, HTML2PDF_SCRIPT, html_path, pdf_path] + PDF_ARGS,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            print(f"OK: PDF generated ({os.path.getsize(pdf_path)} bytes)")
            return pdf_path
        else:
            print(f"ERROR: PDF generation failed (returncode={result.returncode})")
            print(f"stdout: {result.stdout[-500:]}")
            print(f"stderr: {result.stderr[-500:]}")
            return None
    except Exception as e:
        print(f"ERROR: Exception during PDF generation: {e}")
        return None


# ================================================================
#  HTML 生成
# ================================================================

def generate_html():

    # ── 重新计算派生变量（支持从外部覆盖数据）──
    week_total = sum(v for _, _, v in week_days)
    week_avg = week_total / 7
    last_week_total = sum(v for _, _, v in last_week_days)
    may_total = sum(v for _, _, v in may_days)
    wow_change = (week_total - last_week_total) / last_week_total * 100 if last_week_total > 0 else 0
    wow_pct = abs(wow_change)
    wow_direction = "下降" if wow_change < 0 else "增长"
    first_pct = first_visit / week_total * 100 if week_total > 0 else 0
    repeat_pct = repeat_visit / week_total * 100 if week_total > 0 else 0
    panke_rate = panke_done / week_total * 100 if week_total > 0 else 0
    intent_api_total = sum(intent_api.values())
    intent_panke_total = sum(intent_panke.values())
    api_ab = (intent_api.get('A', 0) + intent_api.get('B', 0)) / intent_api_total * 100 if intent_api_total > 0 else 0
    panke_ab = (intent_panke.get('A', 0) + intent_panke.get('B', 0) + intent_panke.get('C+', 0)) / intent_panke_total * 100 if intent_panke_total > 0 else 0
    api_c = intent_api.get('C', 0) / intent_api_total * 100 if intent_api_total > 0 else 0
    panke_c = intent_panke.get('C', 0) / intent_panke_total * 100 if intent_panke_total > 0 else 0
    visit_progress = may_total / visit_target * 100 if visit_target > 0 else 0
    time_progress = 18 / 31 * 100
    achievement_rate = visit_progress / time_progress * 100 if time_progress > 0 else 0
    may_days_count = len(may_days)
    wd_this = week_days[0:4]
    wd_last = last_week_days[0:4]
    wd_avg = round(sum(v for _, _, v in wd_this) / len(wd_this), 1) if wd_this else 0
    last_wd_avg = round(sum(v for _, _, v in wd_last) / len(wd_last), 1) if wd_last else 0
    wd_drop = round((1 - sum(v for _, _, v in wd_this) / sum(v for _, _, v in wd_last)) * 100, 0) if wd_last and sum(v for _, _, v in wd_last) > 0 else 0
    
    # 重新格式化洞察变量
    def fmt(template, **kw):
        try:
            return template.format(**kw)
        except:
            return template
    
    insight_core = fmt(insight_core_tpl, week_total=week_total, wow_pct=f"{wow_pct:.1f}",
        wd_avg=wd_avg, last_wd_avg=last_wd_avg, wd_drop=wd_drop,
        sat_val=week_days[4][2] if len(week_days) > 4 else 0, repeat_pct=f"{repeat_pct:.1f}",
        repeat_up=f"{repeat_pct - 16.1:.1f}", panke_pct=f"{panke_rate:.1f}")
    
    insight_trend = fmt(insight_trend_tpl, wd_avg=wd_avg, last_wd_avg=last_wd_avg, wd_drop=wd_drop,
        sat_val=week_days[4][2] if len(week_days) > 4 else 0,
        last_sat=last_week_days[4][2] if len(last_week_days) > 4 else 0,
        sat_drop=f"{(1 - week_days[4][2]/last_week_days[4][2]) * 100:.1f}" if len(week_days) > 4 and len(last_week_days) > 4 and last_week_days[4][2] > 0 else "0.0",
        sun_val=week_days[5][2] if len(week_days) > 5 else 0,
        last_sun=last_week_days[5][2] if len(last_week_days) > 5 else 0,
        sun_drop=f"{(1 - week_days[5][2]/last_week_days[5][2]) * 100:.1f}" if len(week_days) > 5 and len(last_week_days) > 5 and last_week_days[5][2] > 0 else "0.0",
        wknd_loss=((last_week_days[4][2]+last_week_days[5][2])-(week_days[4][2]+week_days[5][2])) if len(week_days) > 5 and len(last_week_days) > 5 else 0,
        retention=f"{week_days[5][2]/week_days[4][2]*100:.1f}" if len(week_days) > 5 and week_days[4][2] > 0 else "0.0")
    
    risk_trend = fmt(risk_trend_tpl, mon_val=week_days[6][2] if len(week_days) > 6 else 0)
    
    insight_monthly = fmt(insight_monthly_tpl, achievement_rate=f"{achievement_rate:.1f}",
        no_holiday_avg=round((may_total - 166) / 14, 0) if may_total > 166 else 0,
        projected=round((may_total - 166) / 14 * 31 + 166, 0) if may_total > 166 else 0)
    
    finding_intent = fmt(finding_intent_tpl, api_ab=f"{api_ab:.1f}", panke_ab=f"{panke_ab:.1f}",
        api_c=f"{api_c:.1f}", panke_c=f"{panke_c:.1f}")
    
    summary_text = fmt(summary_text_tpl, week_total=week_total, wow_pct=f"{wow_pct:.1f}",
        panke_pct=f"{panke_rate:.1f}", repeat_pct=f"{repeat_pct:.1f}")
    
    """生成完整HTML"""
    # 意向等级bar chart
    intent_api_bars = render_intent_bars(intent_api)
    intent_panke_bars = render_intent_bars(intent_panke)

    # 关注点表格
    fp_table = '<table>\n        <tr><th>关注点</th><th class="num">提及组数</th><th class="num">提及率</th></tr>\n'
    for label, val, pct in focus_points:
        fp_table += f'        <tr><td>{label}</td><td class="num">{val}</td><td class="num">{pct:.1f}%</td></tr>\n'
    fp_table += '      </table>'

    # 关注点圆环图
    fp_donut = donut_svg(focus_points)

    # 环比颜色
    wow_color = "#38A169" if wow_change < 0 else "#E53E3E"
    wow_arrow = "↓" if wow_change < 0 else "↑"
    first_chg = (first_visit - 130) / 130 * 100
    repeat_chg = (repeat_visit - 25) / 25 * 100
    avg_chg = (week_avg - 22) / 22 * 100
    repeat_delta = f"{repeat_pct - 16.1:+.1f}"

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} 周报 {date_start}-{date_end}</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <div class="header-brand">
    <img src="logo_wangai.png" alt="WangAI" title="WangAI智能分析引擎">
  </div>
  <div class="header-center">
    <h1>{project_name} 营销周报</h1>
    <div class="sub">{brand_text}</div>
  </div>
  <div class="header-right">
    <div class="period">{date_start} — {date_end.split(".")[1]}（{week_label}）</div>
    <div class="cumulative">累计成交 <b>{deals_total}</b> 套 / <b>{deals_amount:,}</b> 万元</div>
    <div class="gen-time">数据截至 {data_date} | 旺小宝WangAI生成</div>
  </div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">一</span> 核心数据一览</div>
  <div class="kpi-row">
    <div class="kpi-card primary">
      <div class="kpi-label">本周来访</div>
      <div class="kpi-value">{week_total}</div>
      <div class="kpi-delta down">较上周{last_week_total}组 {wow_pct:.1f}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">首访 / 复访</div>
      <div class="kpi-value">{first_visit} / {repeat_visit}</div>
      <div class="kpi-delta">首访占比{first_pct:.1f}% | 复访{repeat_pct:.1f}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">日均来访</div>
      <div class="kpi-value">{int(round(week_avg))}</div>
      <div class="kpi-delta down">上周日均{int(round(last_week_total/7))}组</div>
    </div>
    <div class="kpi-card warning">
      <div class="kpi-label">月度累计（1-18日）</div>
      <div class="kpi-value">{may_total}</div>
      <div class="kpi-delta">目标{visit_target}组 | 完成率{visit_progress:.1f}%</div>
    </div>
    <div class="kpi-card success">
      <div class="kpi-label">累计签约</div>
      <div class="kpi-value">{deals_total}</div>
      <div class="kpi-delta">总额{deals_amount/10000:.1f}亿 | 均价{deals_amount//deals_total if deals_total > 0 else 0}万</div>
    </div>
  </div>
  <table class="summary-table">
    <tr><th>指标</th><th class="num">本周</th><th class="num">上周</th><th class="num">环比</th><th class="num">本月累计</th><th class="num">年度累计</th></tr>
    <tr><td>来访量（组）</td><td class="num"><b>{week_total}</b></td><td class="num">{last_week_total}</td><td class="num" style="color:{wow_color}">{wow_pct:.1f}%</td><td class="num">{may_total}</td><td class="num">—</td></tr>
    <tr><td>首访量（组）</td><td class="num">{first_visit}</td><td class="num">130</td><td class="num" style="color:#38A169">{first_chg:.1f}%</td><td class="num">—</td><td class="num">—</td></tr>
    <tr><td>复访量（组）</td><td class="num">{repeat_visit}</td><td class="num">25</td><td class="num" style="color:#38A169">{repeat_chg:.1f}%</td><td class="num">—</td><td class="num">—</td></tr>
    <tr><td>复访率</td><td class="num">{repeat_pct:.1f}%</td><td class="num">16.1%</td><td class="num" style="color:#E53E3E">{repeat_delta}pct</td><td class="num">—</td><td class="num">—</td></tr>
    <tr><td>日均来访</td><td class="num">{int(round(week_avg))}</td><td class="num">{int(round(last_week_total/7))}</td><td class="num" style="color:#38A169">{avg_chg:.1f}%</td><td class="num">{may_total//may_days_count if may_days_count > 0 else 0}</td><td class="num">—</td></tr>
    <tr><td>盘客完成率</td><td class="num">{panke_rate:.1f}%</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">—</td></tr>
    <tr><td>签约套数（累计）</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">待更新</td><td class="num">{deals_total}</td></tr>
    <tr><td>签约金额万元（累计）</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">待更新</td><td class="num">{deals_amount:,}</td></tr>
  </table>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_core}
  </div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">二</span> 本周每日来访走势</div>
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <span style="font-size:13px; color:#718096;">本周 {week_total} 组 vs 上周 {last_week_total} 组 | 环比 <span style="color:#38A169; font-weight:600;">{wow_pct:.1f}%</span></span>
    <span style="font-size:12px; color:#A0AEC0;">柱子高度 = 实际来访量（最大{max(v for _,_,v in week_days)}组）</span>
  </div>
  <div class="vbar-chart">
    {vbar_week(week_days, last_week_days)}
  </div>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_trend}
  </div>
  <div class="risk-box">
    {risk_trend}
  </div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">三</span> 客户深度分析</div>
  <p style="font-size:12px; color:#A0AEC0; margin-bottom:14px;">数据来源：盘客管理系统客户画像 + 旺小宝实时 API 客户样本</p>

  <div class="section-sub">3.1 总价预算与支付力分析</div>
  <div class="two-col">
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">总价预算分布</p>
      <div class="bar-chart">{hbar(budgets)}</div>
    </div>
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">付款方式偏好</p>
      <div class="bar-chart">{hbar(payments)}</div>
      <p style="font-size:12px; color:#4A5568; margin:16px 0 8px; font-weight:600;">首付能力判断</p>
      <div class="bar-chart">{hbar(downpay)}</div>
    </div>
  </div>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_budget}
  </div>

  <div class="section-sub">3.2 看房周期与决策成熟度</div>
  <div class="two-col">
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">看房周期分布</p>
      <div class="bar-chart">{hbar(cycles)}</div>
    </div>
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">看房周期 × 意向等级交叉（有周期记录组）</p>
      {cross_cycle_table(cross_cycle_intent)}
      <p style="font-size:11px; color:#A0AEC0; margin-top:6px;">关注 A 级客户的看房周期分布，1 周内决策窗口的客户需优先跟进</p>
    </div>
  </div>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_cycle}
  </div>

  <div class="section-sub">3.3 置业目的与客户需求层级</div>
  <div class="two-col">
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">置业目的分布</p>
      <div class="bar-chart">{hbar(purposes)}</div>
      <p style="font-size:12px; color:#4A5568; margin:16px 0 8px; font-weight:600;">置业目的 × 意向等级交叉</p>
      {cross_purpose_table(cross_purpose_intent)}
    </div>
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">客户关注层级（第一关注点）</p>
      {fp_table}
      <p style="font-size:11px; color:#A0AEC0; margin-top:6px;">注：盘客系统仅记录第一关注点，二三关注未完整采集</p>
    </div>
  </div>
  <div style="margin:14px 0;">{fp_donut}</div>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_purpose}
  </div>

  <div class="section-sub">3.4 来访渠道与客户结构</div>
  <div class="two-col">
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">渠道来访占比</p>
      <div class="bar-chart">{hbar(channels)}</div>
    </div>
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">渠道 × 意向等级交叉</p>
      {cross_channel_table(cross_channel_intent)}
    </div>
  </div>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_channel}
  </div>

  <div class="section-sub">3.5 核心抗性分析</div>
  <div class="bar-chart">{hbar(resistance)}</div>
  <div class="risk-box">{risk_resistance}</div>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_resistance}
  </div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">四</span> 置业顾问来访承接情况</div>
  {render_consultants(consultants_this)}
  <div class="insight">
    <strong>专家洞察：</strong>{insight_consultant}
  </div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">五</span> 意向等级分布</div>
  <div class="two-col">
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">本周旺小宝实时样本</p>
      <div class="bar-chart">{intent_api_bars}</div>
    </div>
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">盘客系统存量画像</p>
      <div class="bar-chart">{intent_panke_bars}</div>
    </div>
  </div>
  <div class="finding">{finding_intent}</div>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_intent}
  </div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">六</span> 成交数据分析</div>
  <div class="kpi-row">
    <div class="kpi-card primary">
      <div class="kpi-label">累计签约套数</div>
      <div class="kpi-value">{deals_total}</div>
      <div class="kpi-delta">历年累计签约</div>
    </div>
    <div class="kpi-card success">
      <div class="kpi-label">累计签约金额</div>
      <div class="kpi-value">{deals_amount/10000:.1f}亿</div>
      <div class="kpi-delta">均价{deals_amount//deals_total if deals_total > 0 else 0}万/套</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">月均签约</div>
      <div class="kpi-value">—</div>
      <div class="kpi-delta">按成交台账统计</div>
    </div>
    <div class="kpi-card warning">
      <div class="kpi-label">近期签约</div>
      <div class="kpi-value">待更新</div>
      <div class="kpi-delta">以最新成交台账为准</div>
    </div>
  </div>
  <div class="two-col">
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">成交户型分布（{deals_total}套）</p>
      <div class="bar-chart">{hbar(house_type_deals)}</div>
    </div>
    <div>
      <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">成交渠道分布（{deals_total}套）</p>
      <div class="bar-chart">{hbar(channel_deals)}</div>
    </div>
  </div>
  <p style="font-size:12px; color:#4A5568; margin:16px 0 8px; font-weight:600;">成交周期分布</p>
  <div class="bar-chart">{hbar(deal_cycle)}</div>
  <p style="font-size:12px; color:#4A5568; margin:16px 0 8px; font-weight:600;">2025-2026月度成交趋势</p>
  {render_monthly_trend(monthly_trend, monthly_trend_total)}
  <div class="insight">
    <strong>专家洞察：</strong>{insight_deals}
  </div>
  <div class="finding">{finding_deals}</div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">七</span> 月度累计进度（截至5.18）</div>
  <div class="kpi-row">
    <div class="kpi-card primary">
      <div class="kpi-label">本月来访累计</div>
      <div class="kpi-value">{may_total}</div>
      <div class="kpi-delta">目标{visit_target}组</div>
    </div>
    <div class="kpi-card success">
      <div class="kpi-label">来访完成率</div>
      <div class="kpi-value">{visit_progress:.1f}%</div>
      <div class="kpi-delta">时间进度{time_progress:.1f}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">进度达成率</div>
      <div class="kpi-value" style="color:#38A169">{achievement_rate:.1f}%</div>
      <div class="kpi-delta">超额完成</div>
    </div>
    <div class="kpi-card warning">
      <div class="kpi-label">本月签约金额</div>
      <div class="kpi-value">待更新</div>
      <div class="kpi-delta">目标2.1亿</div>
    </div>
  </div>
  <p style="font-size:12px; color:#4A5568; margin-bottom:8px; font-weight:600;">5月每日来访走势（1-18日）</p>
  <div class="month-chart">{vbar_month(may_days)}</div>
  <p style="font-size:11px; color:#A0AEC0; text-align:center; margin-top:4px;">深蓝色=周末 | 浅蓝色=工作日 | 柱子高度=实际来访量</p>
  <table>
    <tr><th>指标</th><th class="num">目标值</th><th class="num">实际值</th><th class="num">完成率</th><th class="num">缺口</th></tr>
    <tr><td>来访量（组）</td><td class="num">{visit_target}</td><td class="num">{may_total}</td><td class="num" style="color:#38A169; font-weight:600">{visit_progress:.1f}%</td><td class="num">{visit_target - may_total}</td></tr>
    <tr><td>日均来访</td><td class="num">16</td><td class="num">{may_total//may_days_count if may_days_count > 0 else 0}</td><td class="num" style="color:#38A169">{(may_total//may_days_count)/16*100:.1f}%</td><td class="num">—</td></tr>
    <tr><td>签约金额（万）</td><td class="num">21,000</td><td class="num">待更新</td><td class="num">—</td><td class="num">—</td></tr>
    <tr><td>时间进度</td><td class="num">31天</td><td class="num">18天</td><td class="num">{time_progress:.1f}%</td><td class="num">13天</td></tr>
  </table>
  <div class="insight">
    <strong>专家洞察：</strong>{insight_monthly}
  </div>
</div>

<div class="card">
  <div class="section-header"><span class="section-num">八</span> 下周工作建议</div>
  {render_suggestions(suggestions)}
  <div class="finding">
    <span class="tag">总结</span>{summary_text}
  </div>
</div>

  <div class="footer-bar">
    <div class="footer-brand">
      <img src="logo_wangxiaobao.png" alt="旺小宝">
      <span>数据来源：旺小宝智能案场系统 · 项目营销数据中台</span>
    </div>
    <div class="footer-brand">
      <span>AI生成：WangAI 智能分析引擎</span>
      <img src="logo_wangai.png" alt="WangAI">
    </div>
  </div>

</div>
</body>
</html>'''
    return html


# ================================================================
#  输出
# ================================================================

if __name__ == "__main__":
    output_file = f"{project_name.replace('·','').replace(' ','_')}_周报_{date_start.replace('.','')}-{date_end.replace('.','')}.html"
    html = generate_html()
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {output_file} ({len(html)} chars)")

    # 生成 PDF
    pdf = generate_pdf(output_file)
    if pdf:
        print(f"DONE: HTML + PDF 已全部生成")
        print(f"  HTML: {os.path.abspath(output_file)}")
        print(f"  PDF:  {os.path.abspath(pdf)}")
    else:
        print(f"DONE: HTML 已生成，PDF 生成失败（详见上方错误信息）")
