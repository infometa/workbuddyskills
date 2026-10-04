#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
营销周报生成器（完整版）
- 从 weekly_report_data.json 读取所有数据
- 覆盖 template.py 的 ALL 变量
- 调用 generate_html() + generate_pdf()
- 支持 --html-only：仅生成 HTML（<1秒）
"""

import sys, os, json, re, argparse
from collections import defaultdict

# 解析命令行参数
parser = argparse.ArgumentParser(description="周报生成器")
parser.add_argument("--html-only", action="store_true", help="仅生成 HTML，跳过 PDF（<1秒）")
args = parser.parse_args()

# 添加当前目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("营销周报生成器（完整版）")
print("=" * 60)

# ── 1. 读取数据 ──
print("\n[1/5] 读取 weekly_report_data.json...")
with open('weekly_report_data.json', encoding='utf-8') as f:
    data = json.load(f)

print(f"  项目: {data.get('project_name')}")
print(f"  周期: {data.get('date_start')} 至 {data.get('date_end')}")
week_total = sum(d['count'] for d in data.get('week_days', []))
print(f"  本周来访: {week_total} 组")

# ── 2. 导入 template 模块 ──
print("\n[2/5] 导入 template.py 模块...")
import template as tpl
print(f"  ✅ 已导入 template 模块")
print(f"  当前 project_name: {tpl.project_name}")

# ── 3. 覆盖 ALL 变量 ──
print("\n[3/5] 覆盖 template.py 的所有变量...")

def convert_date(date_str):
    """YYYY-MM-DD → YYYY.MM.DD（用于 week_days 等）"""
    if '-' in date_str and len(date_str) == 10:
        parts = date_str.split('-')
        return f"{parts[1]}.{parts[2]}"
    return date_str

def convert_date_start(date_str):
    """YYYY-MM-DD → YYYY.MM.DD（用于 date_start/date_end）"""
    if '-' in date_str and len(date_str) == 10:
        return date_str.replace('-', '.')
    return date_str

def convert_chart_data(raw):
    """
    将 [{"name":..., "count":...}] 或 [[name, count, pct], ...] 统一转为 [(name, count, pct), ...]
    template.py 的 hbar()/donut_svg() 需要此格式
    """
    converted = []
    for r in raw:
        if isinstance(r, dict):
            # JSON 中是 {"name": k, "count": v} 格式
            name = r.get('name', '')
            count = r.get('count', 0)
            total = sum(x.get('count', 0) for x in raw)
            pct = round(count / total * 100, 1) if total > 0 else 0
            converted.append((name, count, pct))
        elif isinstance(r, (list, tuple)) and len(r) >= 3:
            # JSON 中是 [name, count, pct] 格式
            converted.append((r[0], r[1], r[2]))
        elif isinstance(r, (list, tuple)) and len(r) >= 2:
            # [name, count] 格式，需要计算 pct
            total = sum(x[1] for x in raw if isinstance(x, (list, tuple)) and len(x) >= 2)
            pct = round(r[1] / total * 100, 1) if total > 0 else 0
            converted.append((r[0], r[1], pct))
    return converted

# 3.1 基本信息
tpl.project_name = data.get('project_name', tpl.project_name)
tpl.brand_text   = data.get('brand_text',   tpl.brand_text)
tpl.week_label    = data.get('week_label',    tpl.week_label)
tpl.date_start   = convert_date_start(data.get('date_start', tpl.date_start))
tpl.date_end     = convert_date_start(data.get('date_end',   tpl.date_end))
data_date = data.get('data_date', tpl.data_date)
if '-' in data_date:
    parts = data_date.split(' ')
    if len(parts) == 2:
        tpl.data_date = convert_date_start(parts[0]) + ' ' + parts[1]
else:
    tpl.data_date = data_date
print("  ✅ 基本信息")

# 3.2 week_days / last_week_days / may_days
def build_week_days(days_list):
    """将 [{'date':..., 'weekday':..., 'count':...}] 转换为 (date_str, weekday, count) 元组列表"""
    result = []
    for d in days_list:
        date_fmt = convert_date(d['date'])
        result.append((date_fmt, d['weekday'], d['count']))
    return result

if 'week_days' in data:
    tpl.week_days = build_week_days(data['week_days'])
    print(f"  ✅ week_days: {len(tpl.week_days)} 天")

if 'last_week_days' in data:
    tpl.last_week_days = build_week_days(data['last_week_days'])
    print(f"  ✅ last_week_days: {len(tpl.last_week_days)} 天")

if 'may_days' in data:
    tpl.may_days = build_week_days(data['may_days'])
    print(f"  ✅ may_days: {len(tpl.may_days)} 天")

# 3.3 顾问接待
if 'consultants_this' in data:
    tpl.consultants_this = []
    for c in data['consultants_this']:
        tpl.consultants_this.append((c['name'], c['count'], c['pct'], c['last_count'], c['change_pct']))
    print(f"  ✅ consultants_this: {len(tpl.consultants_this)} 人")

# 3.4 首访/复访/盘客完成率
tpl.first_visit = data.get('first_visit', tpl.first_visit)
tpl.repeat_visit = data.get('repeat_visit', tpl.repeat_visit)
tpl.panke_done   = data.get('panke_done',   tpl.panke_done)
print(f"  ✅ 首访={tpl.first_visit} 复访={tpl.repeat_visit} 盘客完成={tpl.panke_done}")

# 3.5 意向等级 API
if 'intent_api' in data:
    tpl.intent_api = {}
    for item in data['intent_api']:
        tpl.intent_api[item['level']] = item['count']
    print(f"  ✅ intent_api: {tpl.intent_api}")

# 3.6 意向等级 盘客
if 'intent_panke' in data:
    tpl.intent_panke = data['intent_panke']
    print(f"  ✅ intent_panke: {tpl.intent_panke}")

# 3.7 横向柱状图数据（预算/付款/户型/渠道/抗性/目的/关注点/周期/首付）
CHART_KEYS = [
    ('budgets',    'budgets'),
    ('payments',   'payments'),
    ('house_types', 'house_types'),
    ('channels',    'channels'),
    ('resistances', 'resistances'),
    ('purposes',    'purposes'),
    ('focus_points', 'focus_points'),
    ('cycles',       'cycles'),
    ('downpay',      'downpay'),
]
for json_key, tpl_var in CHART_KEYS:
    if json_key in data:
        # data[json_key] 是 [{"name":..., "count":...}], 或 [[name, count, pct], ...]
        raw = data[json_key]
        converted = []
        for r in raw:
            if isinstance(r, dict):
                # JSON 中是 {"name": k, "count": v} 格式
                name = r.get('name', '')
                count = r.get('count', 0)
                # 计算百分比
                total = sum(x.get('count', 0) for x in raw) if all(isinstance(x, dict) for x in raw) else 1
                pct = round(count / total * 100, 1) if total > 0 else 0
                converted.append((name, count, pct))
            elif isinstance(r, (list, tuple)) and len(r) >= 3:
                # JSON 中是 [name, count, pct] 格式（元组转为了列表）
                converted.append((r[0], r[1], r[2]))
            elif isinstance(r, (list, tuple)) and len(r) >= 2:
                # [name, count] 格式，需要计算 pct
                total = sum(x[1] for x in raw if isinstance(x, (list, tuple)) and len(x) >= 2)
                pct = round(r[1] / total * 100, 1) if total > 0 else 0
                converted.append((r[0], r[1], pct))
        setattr(tpl, tpl_var, converted)
        print(f"  ✅ {tpl_var}: {len(converted)} 项")

# 3.8 成交数据
tpl.deals_total  = data.get('deals_total',  tpl.deals_total)
tpl.deals_amount = data.get('deals_amount', tpl.deals_amount)
print(f"  ✅ deals_total={tpl.deals_total}  deals_amount={tpl.deals_amount}")

if 'house_type_deals' in data:
    tpl.house_type_deals = convert_chart_data(data['house_type_deals'])
    print(f"  ✅ house_type_deals: {len(tpl.house_type_deals)} 项")

if 'channel_deals' in data:
    tpl.channel_deals = convert_chart_data(data['channel_deals'])
    print(f"  ✅ channel_deals: {len(tpl.channel_deals)} 项")

if 'deal_cycle' in data:
    tpl.deal_cycle = convert_chart_data(data['deal_cycle'])
    print(f"  ✅ deal_cycle: {len(tpl.deal_cycle)} 项")

# 3.9 月度目标
tpl.visit_target = data.get('visit_target', tpl.visit_target)
tpl.sales_target = data.get('sales_target', tpl.sales_target)
print(f"  ✅ visit_target={tpl.visit_target}  sales_target={tpl.sales_target}")

# 3.10 月度成交趋势
if 'monthly_trend' in data:
    # data['monthly_trend'] 是 [{'month':..., 'count_2025':..., ...}]
    # 需要转为 (month, count2025, amt2025, count2026, amt2026, yoy)
    tpl.monthly_trend = []
    for r in data['monthly_trend']:
        tpl.monthly_trend.append((
            r['month'],
            r.get('count_2025', 0),
            str(r.get('amount_2025', 0)),
            r.get('count_2026', '待更新'),
            str(r.get('amount', r.get('amount_2026', '待更新'))),
            r.get('yoy', '—')
        ))
    # monthly_trend_total
    t2025 = sum(r.get('count_2025', 0) for r in data['monthly_trend'] if isinstance(r.get('count_2025'), int))
    a2025 = sum(r.get('amount_2025', 0) for r in data['monthly_trend'] if isinstance(r.get('amount_2025'), (int,float)))
    t2026 = sum(r.get('count_2026', 0) for r in data['monthly_trend'] if isinstance(r.get('count_2026'), int) and r.get('count_2026') != '待更新')
    a2026 = sum(r.get('amount', r.get('amount_2026', 0)) for r in data['monthly_trend'] if isinstance(r.get('amount', r.get('amount_2026')), (int,float)) and r.get('amount', r.get('amount_2026')) != '待更新')
    tpl.monthly_trend_total = ('合计/平均', t2025, f"{a2025:,}", t2026 if t2026 else '—', f"{a2026:,}" if a2026 else '—', '—')
    print(f"  ✅ monthly_trend: {len(tpl.monthly_trend)} 个月")

# 3.11 交叉分析表
def build_cross_table(json_key, default):
    """从 JSON 构建交叉表（列表的列表）"""
    if json_key not in data:
        return default
    return data[json_key]  # 已经是 [row_list, ...] 格式

if 'cross_cycle_intent' in data:
    tpl.cross_cycle_intent = data['cross_cycle_intent']
    print(f"  ✅ cross_cycle_intent: {len(tpl.cross_cycle_intent)} 行")

if 'cross_purpose_intent' in data:
    tpl.cross_purpose_intent = data['cross_purpose_intent']
    print(f"  ✅ cross_purpose_intent: {len(tpl.cross_purpose_intent)} 行")

if 'cross_channel_intent' in data:
    tpl.cross_channel_intent = data['cross_channel_intent']
    print(f"  ✅ cross_channel_intent: {len(tpl.cross_channel_intent)} 行")

# 3.12 下周建议
if 'suggestions' in data:
    tpl.suggestions = data['suggestions']
    print(f"  ✅ suggestions: {len(tpl.suggestions)} 条")

# 3.13 洞察文本（使用 JSON 中的值，若为空则保留 template 默认值）
INSIGHT_KEYS = [
    'insight_core', 'insight_trend', 'insight_budget',
    'insight_cycle', 'insight_purpose', 'insight_channel',
    'insight_resistance', 'insight_consultant',
    'insight_intent', 'insight_deals', 'insight_monthly',
    'finding_intent', 'finding_deals', 'summary_text',
    'risk_trend',
]
for key in INSIGHT_KEYS:
    if key in data and data[key] and not data[key].startswith('首付') and not data[key].startswith('看房'):
        # 有用数据，覆盖
        # 注意：变量名在 template.py 中是 insight_core（无 _tpl 后缀）
        # 但我们的 JSON key 也是 insight_core
        # template.py 在 generate_html() 中用 fmt() 格式化 *_tpl 变量
        # 所以我们需要同时设置 insight_core 和 insight_core_tpl
        setattr(tpl, key, data[key])
        # 同时设置 *_tpl 版本（用于格式化）
        tpl_var_tpl = key + '_tpl'
        if hasattr(tpl, tpl_var_tpl):
            setattr(tpl, tpl_var_tpl, data[key])
        print(f"  ✅ {key}: {len(data[key])} 字")
    elif key in data and data[key]:
        setattr(tpl, key, data[key])
        print(f"  ✅ {key}: {len(data[key])} 字 (占位符)")
    else:
        print(f"  ⚠️  {key}: 使用 template 默认值")

print(f"\n  ✅ 所有变量覆盖完成！")

# ── 4. 生成 HTML ──
print("\n[4/4] 生成 HTML..." if args.html_only else "\n[4/5] 生成 HTML...")
html_content = tpl.generate_html()
print(f"  ✅ HTML 已生成 ({len(html_content)} chars)")

# 写入 HTML 文件
output_file = f"{tpl.project_name.replace('·','').replace(' ', '_')}_周报_{tpl.date_start.replace('.','')}-{tpl.date_end.replace('.','')}.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"  ✅ HTML 已写入: {output_file}")

# 生成 PDF（除非 --html-only）
if args.html_only:
    print("\n⚡ --html-only 模式：跳过 PDF 生成")
    pdf_path = None
else:
    print("\n[5/5] 生成 PDF...")
    pdf_path = tpl.generate_pdf(output_file)
    if pdf_path:
        print(f"  ✅ PDF 已生成: {pdf_path}")
    else:
        print(f"  ⚠️  PDF 生成失败（可能缺少 playwright 或 html2pdf.py）")

print("\n" + "=" * 60)
print("✅ 周报生成完成！")
print(f"  HTML: {os.path.abspath(output_file)}")
if pdf_path:
    print(f"  PDF:  {os.path.abspath(pdf_path)}")
else:
    print(f"  PDF:  未生成")
print("=" * 60)
