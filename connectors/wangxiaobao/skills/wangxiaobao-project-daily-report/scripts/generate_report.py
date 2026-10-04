# -*- coding: utf-8 -*-
"""
旺小宝项目日报生成脚本
功能：拉取旺小宝数据，生成完整HTML日报 + PDF

使用方法：
    python generate_report.py [日期]
    python generate_report.py 2026-05-19
    python generate_report.py 2026-05-19 --tenant-id <ID> --project-id <ID> --project-name "<项目名>"
"""
import json
import os
import sys
import ssl
import argparse
import subprocess
from urllib.request import Request, urlopen
from datetime import datetime, timedelta
from collections import Counter

# 查找系统可用的浏览器（Chrome/Edge）路径
import shutil
_BROWSER_PATH = None
for _p in [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]:
    if os.path.exists(_p):
        _BROWSER_PATH = _p
        break
if _BROWSER_PATH is None:
    _chrome = shutil.which("chrome")
    _edge = shutil.which("msedge")
    _BROWSER_PATH = _chrome or _edge

# ==================== 项目配置 ====================
# 优先级：命令行参数 > 环境变量 > 默认值
TENANT_ID = os.environ.get("XIAOBAO_TENANT_ID", "")
PROJECT_ID = os.environ.get("XIAOBAO_PROJECT_ID", "")
PROJECT_NAME = os.environ.get("XIAOBAO_PROJECT_NAME", "<项目名>")
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".openclaw/state/wangxiaobao/token.json")
OUTPUT_DIR = os.getcwd()

# KPI指标（示例值 500 / 21000，请按项目实际目标调整）
KPI_CONFIG = {
    "month_visit_target": int(os.environ.get("XIAOBAO_MONTH_VISIT_TARGET", "500")),  # 月度来访目标
    "month_sales_target": int(os.environ.get("XIAOBAO_MONTH_SALES_TARGET", "21000")),  # 月度销售目标（万元）
}


def get_token():
    """获取旺小宝access token"""
    with open(TOKEN_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['access_token']


def api_call(endpoint, body, token):
    """使用Python原生urllib调用旺小宝API，避免PowerShell编码问题"""
    url = f"https://open-ai.wangxiaobao.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": TENANT_ID,
        "X-Project-Id": PROJECT_ID,
        "Content-Type": "application/json"
    }
    req = Request(url, data=body.encode('utf-8'), headers=headers, method='POST')
    ctx = ssl.create_default_context()
    try:
        with urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"    API调用失败: {e}")
        return {'data': {'content': [], 'total': 0}}


def get_yesterday_visits(token, yesterday):
    """获取昨日来访数据"""
    body = json.dumps({
        "current": 1, "size": 100,
        "startTime": f"{yesterday} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    }, ensure_ascii=False)
    data = api_call("/ai-open/visits/page", body, token)
    all_visits = data.get('data', {}).get('content', [])
    return [v for v in all_visits if v.get('visitTime', '').startswith(yesterday)]


def get_month_visits(token, month_start, yesterday):
    """获取本月来访数据"""
    body = json.dumps({
        "current": 1, "size": 500,
        "startTime": f"{month_start} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    }, ensure_ascii=False)
    data = api_call("/ai-open/visits/page", body, token)
    all_visits = data.get('data', {}).get('content', [])
    month_prefix = yesterday[:7]  # e.g., "2026-05"
    return [v for v in all_visits if v.get('visitTime', '').startswith(month_prefix)]


def get_customers(token, month_start, yesterday):
    """获取客户画像数据"""
    body = json.dumps({
        "page": 1, "size": 500,
        "startTime": f"{month_start} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    }, ensure_ascii=False)
    data = api_call("/ai-open/customers/page", body, token)
    return data.get('data', {}).get('content', [])


def get_stock_customers(token, three_months_ago, yesterday):
    """获取存量客户（近3月未成交）"""
    body = json.dumps({
        "page": 1, "size": 100,
        "startTime": f"{three_months_ago} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    }, ensure_ascii=False)
    data = api_call("/ai-open/customers/page", body, token)
    all_custs = data.get('data', {}).get('content', [])
    return [c for c in all_custs if c.get('dealStatus') != 1]


def analyze_intent(customers):
    """分析意向等级分布"""
    intent_dist = {"A级": 0, "B级": 0, "C级": 0, "D级": 0, "未知": 0}
    for c in customers:
        level = c.get('intentLevel', '未知') or '未知'
        if level == '':
            level = '未知'
        # 映射
        if level in ['A', 'A1', 'A2']:
            intent_dist['A级'] += 1
        elif level in ['B', 'B1', 'B2']:
            intent_dist['B级'] += 1
        elif level in ['C', 'C+', 'C1', 'C2']:
            intent_dist['C级'] += 1
        elif level in ['D', 'D1', 'D2']:
            intent_dist['D级'] += 1
        else:
            intent_dist['未知'] += 1
    return intent_dist


def analyze_channel(customers):
    """分析渠道分布"""
    channel_dist = Counter()
    for c in customers:
        tags = c.get('dynamicTags', {})
        channel = tags.get('五大类来访渠道', '其他')
        if not channel or channel == '':
            channel = '其他'
        channel_dist[channel] += 1
    return dict(channel_dist)


def analyze_channel_with_intent(customers):
    """分析渠道分布及意向等级"""
    channel_data = {}
    for c in customers:
        tags = c.get('dynamicTags', {})
        channel = tags.get('五大类来访渠道', '其他')
        if not channel or channel == '':
            channel = '其他'
        
        if channel not in channel_data:
            channel_data[channel] = {'total': 0, 'A级': 0, 'B级': 0, 'C级': 0, 'D级': 0}
        
        channel_data[channel]['total'] += 1
        level = c.get('intentLevel', '') or ''
        if level in ['A', 'A1', 'A2']:
            channel_data[channel]['A级'] += 1
        elif level in ['B', 'B1', 'B2']:
            channel_data[channel]['B级'] += 1
        elif level in ['C', 'C+', 'C1', 'C2']:
            channel_data[channel]['C级'] += 1
        elif level in ['D', 'D1', 'D2']:
            channel_data[channel]['D级'] += 1
    
    return channel_data


def mask_name(name):
    """脱敏客户姓名"""
    if not name or len(name) < 2:
        return "***"
    return name[0] + '*' + name[-1] if len(name) > 1 else name[0] + '**'


def generate_html(report_data):
    """生成HTML日报"""
    today = report_data['date']
    yesterday = report_data['yesterday']
    month_start = report_data['month_start']
    month_visit_target = report_data.get('month_visit_target', 500)
    month_visit_actual = report_data['month_visit_actual']
    month_sales_target = report_data.get('month_sales_target', 21000)
    month_deals = report_data['month_deals']
    deal_amount = report_data.get('deal_amount', '待填报')
    yesterday_visits = report_data['yesterday_visits']
    yesterday_visit_list = report_data.get('yesterday_visit_list', [])
    intent_dist = report_data.get('intent_dist', {})
    channel_dist = report_data.get('channel_dist', {})
    stock_customers = report_data.get('stock_customers', [])
    stock_by_channel = report_data.get('stock_by_channel', {})
    deal_intent = report_data.get('deal_intent', {})
    
    # 计算指标
    days_in_month = 31
    day_of_month = int(yesterday.split('-')[2])
    time_progress = round(day_of_month / days_in_month * 100, 1)
    visit_completion = round(month_visit_actual / month_visit_target * 100, 1)
    progress_rate = round(visit_completion / time_progress * 100, 1) if time_progress > 0 else 0
    surplus = round(progress_rate - 100, 1)
    
    deal_amount_display = str(deal_amount) if deal_amount != '待填报' else '待填报'
    sales_completion = round(int(deal_amount) / month_sales_target * 100, 1) if deal_amount != '待填报' else '-'
    sales_progress_rate = round(sales_completion / time_progress * 100, 1) if deal_amount != '待填报' and time_progress > 0 else '-'
    
    # 意向等级
    intent_A = intent_dist.get('A级', 0)
    intent_B = intent_dist.get('B级', 0)
    intent_C = intent_dist.get('C级', 0)
    intent_D = intent_dist.get('D级', 0)
    intent_unk = intent_dist.get('未知', 0)
    intent_total = intent_A + intent_B + intent_C + intent_D + intent_unk
    
    intent_A_pct = round(intent_A / intent_total * 100, 1) if intent_total > 0 else 0
    intent_B_pct = round(intent_B / intent_total * 100, 1) if intent_total > 0 else 0
    intent_C_pct = round(intent_C / intent_total * 100, 1) if intent_total > 0 else 0
    intent_D_pct = round(intent_D / intent_total * 100, 1) if intent_total > 0 else 0
    
    # 成交意向
    deal_A = deal_intent.get('A级', 0)
    deal_B = deal_intent.get('B级', 0)
    deal_C = deal_intent.get('C级', 0) + deal_intent.get('C/C+级', 0)
    deal_D = deal_intent.get('D级', 0)
    
    deal_A_pct = round(deal_A / month_deals * 100, 1) if month_deals > 0 else 0
    deal_B_pct = round(deal_B / month_deals * 100, 1) if month_deals > 0 else 0
    deal_C_pct = round(deal_C / month_deals * 100, 1) if month_deals > 0 else 0
    deal_D_pct = round(deal_D / month_deals * 100, 1) if month_deals > 0 else 0
    
    # 来访渠道行（使用实际渠道数据）
    channel_rows = ""
    channel_total = sum(channel_dist.values())
    channel_notes = {
        '中介': '主力获客渠道',
        '自渠': '-',
        '顺访': '-',
        '中介,约访': '中介+约访',
        '顺访,中介': '顺访+中介',
        '约访': '-',
        '自渠,顺访': '自渠+顺访',
        '自渠,约访': '自渠+约访',
        '全民/全员/老带新': '老带新',
    }
    
    # 渠道备注映射
    channel_by_type = {
        '中介': '主力获客渠道',
        '自渠': '-',
        '顺访': '-',
        '约访': '-',
        '全民/全员/老带新': '老带新渠道',
    }
    
    # 显示所有渠道
    for ch, cnt in sorted(channel_dist.items(), key=lambda x: -x[1]):
        pct = round(cnt / channel_total * 100, 1) if channel_total > 0 else 0
        # 获取该渠道的备注
        note = '-'
        for key, val in channel_notes.items():
            if key in ch:
                note = val
                break
        
        channel_rows += f'''<tr>
<td><strong>{ch}</strong></td>
<td class="data-value">{cnt}</td>
<td>{pct}%</td>
<td>-</td>
<td>{note}</td>
</tr>
'''
    
    # 存量客户汇总行
    stock_summary_rows = ""
    stock_channel_order = ['顺访+中介', '顺访', '中介', '自渠+顺访', '自渠', '其他']
    stock_total = len(stock_customers)
    for ch in stock_channel_order:
        if ch in stock_by_channel:
            d = stock_by_channel[ch]
            pct = round(d['total'] / stock_total * 100, 1) if stock_total > 0 else 0
            stock_summary_rows += f'''<tr>
<td><strong>{ch}</strong></td>
<td class="data-value">{d['total']}</td>
<td>{d['A级']}</td>
<td>{d['B级']}</td>
<td>{d['C级']}</td>
<td>{d['D级']}</td>
<td>{pct}%</td>
</tr>
'''
    # 其他渠道
    other_stock = sum(d['total'] for k, d in stock_by_channel.items() if k not in stock_channel_order)
    if other_stock > 0:
        stock_summary_rows += f'''<tr class="light-bg">
<td><strong>其他渠道</strong></td>
<td class="data-value">{other_stock}</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
</tr>
'''
    stock_summary_rows += f'''<tr style="background:#1F4E79; color:#fff;">
<td><strong>合计</strong></td>
<td class="data-value" style="color:#fff;">{stock_total}</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>100%</td>
</tr>
'''
    
    # 存量客户明细
    stock_detail_rows = ""
    for i, c in enumerate(stock_customers[:10], 1):
        level = c.get('intentLevel', 'C级') or 'C级'
        level_display = f'<span class="data-value" style="color:#c00;">A级</span>' if level in ['A', 'A1', 'A2'] else f'{level}'
        channel = c.get('dynamicTags', {}).get('五大类来访渠道', '-')
        follow_status = '高意向' if level in ['A', 'A1', 'A2'] else '中等意向' if level in ['C', 'C+', 'C1', 'C2'] else '低意向'
        decision_cycle = c.get('dynamicTags', {}).get('看房周期', '-') or '-'
        no_deal_reason = c.get('dynamicTags', {}).get('购买抗性', '-') or '-'
        visit_prob = 90 if level in ['A', 'A1', 'A2'] else 70 if level in ['C', 'C+', 'C1', 'C2'] else 40
        deal_prob = 85 if level in ['A', 'A1', 'A2'] else 50 if level in ['C', 'C+', 'C1', 'C2'] else 20
        strategy = '重点跟进，推动签约' if level in ['A', 'A1', 'A2'] else '保持联系' if level in ['D', 'D1', 'D2'] else '强化产品价值'
        
        stock_detail_rows += f'''<tr>
<td class="no">{i}</td>
<td>{mask_name(c.get('customerName', ''))}</td>
<td>{channel}</td>
<td>{c.get('userName', '-')}</td>
<td>{c.get('lastVisitTime', '')[:10] if c.get('lastVisitTime') else '-'}</td>
<td>{level_display}</td>
<td>{follow_status}</td>
<td>{decision_cycle}</td>
<td>{no_deal_reason}</td>
<td>{visit_prob}%</td>
<td>{deal_prob}%</td>
<td>{strategy}</td>
</tr>
'''
    
    # 昨日来访明细
    yesterday_detail_rows = ""
    first_visit_count = sum(1 for v in yesterday_visit_list if v['count'] == 1)
    repeat_visit_count = len(yesterday_visit_list) - first_visit_count
    
    for i, v in enumerate(yesterday_visit_list, 1):
        visit_type = '首访' if v['count'] == 1 else '复访'
        note = '新客户' if v['count'] == 1 else '-'
        if v['count'] == 1 and v['duration'] > 60:
            note = '高意向'
        
        yesterday_detail_rows += f'''<tr>
<td class="no">{i}</td>
<td>{v['time']}</td>
<td>{v['advisor']}</td>
<td>第{v['count']}次</td>
<td>{v['duration']}分钟</td>
<td>{visit_type}</td>
<td>{note}</td>
</tr>
'''
    
    yesterday_analysis = f"首访{first_visit_count}组（{round(first_visit_count/len(yesterday_visit_list)*100,1) if yesterday_visit_list else 0}%" + \
                         f"），复访{repeat_visit_count}组（{round(repeat_visit_count/len(yesterday_visit_list)*100,1) if yesterday_visit_list else 0}%）"
    
    # 顾问来访统计
    advisor_stats = Counter()
    for v in yesterday_visit_list:
        advisor_stats[v['advisor']] += 1
    advisor_rows = ""
    for i, (advisor, cnt) in enumerate(advisor_stats.most_common(5), 1):
        remark = '存量客户多' if i == 1 else '-'
        advisor_rows += f'''<tr>
<td>{i}</td>
<td><strong>{advisor}</strong></td>
<td>{cnt}组</td>
<td>-</td>
<td>{remark}</td>
</tr>
'''
    
    # 成交金额警告
    deal_warning = '<span style="color:#f90;">成交金额待确认，建议从销售管理系统补充数据</span>' if deal_amount == '待填报' else '-'
    deal_amount_display = str(deal_amount) if deal_amount != '待填报' else '待填报'
    
    # 来访指标说明
    visit_comment = '大幅超额完成' if progress_rate > 130 else '超额完成' if progress_rate > 100 else '按计划推进'
    
    # 昨日来访评论
    yesterday_comment = '平稳' if 8 <= yesterday_visits <= 15 else '较好' if yesterday_visits > 15 else '较少'
    
    # ========== 方案A：纯CSS方案 =========
    # 不依赖 print-color-adjust，改用深色文字+边框，保证PDF可见
    # 表头背景用内联 style 强制写入，双重保险
    
    # 组装HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PROJECT_NAME} 日报 {yesterday}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; font-size: 12px; color: #333; background: #fff; padding: 15px; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: center; vertical-align: middle; font-size: 11px; }}
th {{ color: #fff; font-weight: bold; }}

/* 颜色 */
.title-bg {{ background: #1F4E79 !important; }}
.orange-bg {{ background: #975765 !important; }}
.pink-bg {{ background: #EEE2E6 !important; color: #333; }}
.peach-bg {{ background: #C59BA6 !important; }}
.light-bg {{ background: #f5f5f5 !important; }}

/* KPI卡片 */
.kpi-row {{ display: flex; gap: 8px; margin-bottom: 12px; }}
.kpi-card {{ flex: 1; border: 2px solid #1F4E79; border-radius: 4px; padding: 10px; text-align: center; background: #fafafa; }}
.kpi-card .label {{ font-size: 10px; color: #666; margin-bottom: 3px; }}
.kpi-card .value {{ font-size: 22px; font-weight: bold; color: #1F4E79; line-height: 1.2; }}
.kpi-card .sub {{ font-size: 9px; color: #888; margin-top: 3px; }}

/* 布局 */
.col-2 {{ display: flex; gap: 12px; margin-bottom: 12px; }}
.col-2 > div {{ flex: 1; }}

/* 表头 */
.section-title {{ background: #1F4E79 !important; color: #fff !important; font-size: 13px; font-weight: bold; padding: 8px; text-align: center; }}
.table-header {{ background: #975765 !important; color: #fff !important; font-weight: bold; }}
.table-header-pink {{ background: #EEE2E6 !important; color: #333 !important; font-weight: bold; }}
.table-header-peach {{ background: #C59BA6 !important; color: #fff !important; font-weight: bold; }}

/* 数据 */
.data-value {{ font-weight: bold; font-size: 14px; color: #1F4E79; }}
.data-red {{ color: #c00; font-weight: bold; }}
.highlight {{ background: #fff3cd; }}

/* 序号列 */
.no {{ width: 30px; }}

/* 明细表格 */
.detail-table td {{ text-align: left; font-size: 10px; }}
.detail-table td:nth-child(2) {{ text-align: center; }}
.detail-table td:nth-child(3) {{ text-align: center; }}
.detail-table td:nth-child(4) {{ text-align: center; }}
.detail-table td:nth-child(5) {{ text-align: center; }}
.detail-table td:nth-child(6) {{ text-align: center; }}

/* 交替行 */
tr:nth-child(even) {{ background: #f9f9f9; }}

/* 页脚 */
.footer {{ text-align: center; padding: 15px; color: #999; font-size: 10px; border-top: 1px solid #ddd; margin-top: 20px; }}

/* 渠道表 */
.channel-table td:first-child {{ text-align: left; font-weight: bold; }}

/* 合并标题 */
.merge-cell {{ background: #975765 !important; color: #fff !important; font-weight: bold; }}

/* 打印优化：强制背景色打印 + 文字深色fallback */
@media print {{
  @page {{ margin: 8mm; size: A4; }}
  body {{
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    background: #fff !important;
  }}
  table {{ break-inside: avoid; }}
  tr {{ break-inside: avoid; }}
  .kpi-row {{ display: flex !important; flex-wrap: nowrap; break-inside: avoid; }}
  .kpi-row > div {{ flex: 1; min-width: 0; }}
  .col-2 {{ display: block !important; break-inside: avoid; }}
  .col-2 > div {{ display: block; width: 100% !important; margin-bottom: 8px; }}
  .footer {{ break-inside: avoid; }}

  /* 强制所有深色背景元素的背景色打印 */
  .section-title, .title-bg {{
    background: #1F4E79 !important;
    color: #fff !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  .table-header td, .orange-bg, .merge-cell, th {{
    background: #975765 !important;
    color: #fff !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  .table-header {{ background: #975765 !important; }}
  .table-header-peach, .peach-bg {{
    background: #C59BA6 !important;
    color: #fff !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  .table-header-pink, .pink-bg {{
    background: #EEE2E6 !important;
    color: #333 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  .light-bg {{
    background: #f5f5f5 !important;
    color: #333 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
}}
</style>
</head>
<body>

<!-- 项目标题 -->
<table>
<tr>
<td class="title-bg" style="font-size: 18px; font-weight: bold; padding: 12px; text-align: center; color: #fff;">
{PROJECT_NAME} 营销日报
</td>
</tr>
<tr>
<td style="text-align: center; padding: 6px; color: #666; background: #f5f5f5; font-size: 11px;">
数据日期：{yesterday}（昨日） | 统计周期：{month_start} ~ {yesterday} | 截至时间：23:59
</td>
</tr>
</table>

<!-- KPI概览 -->
<div class="kpi-row">
<div class="kpi-card">
<div class="label">本月来访（组）</div>
<div class="value">{month_visit_actual}</div>
<div class="sub">目标{month_visit_target}组 | 完成率{visit_completion}%</div>
</div>
<div class="kpi-card">
<div class="label">来访进度达成</div>
<div class="value">{progress_rate}%</div>
<div class="sub">时间进度{time_progress}% | 超额{surplus}%</div>
</div>
<div class="kpi-card">
<div class="label">本月成交（组）</div>
<div class="value">{month_deals}</div>
<div class="sub">目标待确认 | 成交金额{deal_amount}</div>
</div>
<div class="kpi-card">
<div class="label">昨日来访（组）</div>
<div class="value">{yesterday_visits}</div>
<div class="sub">本周来访量{yesterday_comment}</div>
</div>
</div>

<!-- 来访指标 + 来访意向等级 -->
<div class="col-2">
<div>
<table>
<tr><td colspan="6" class="section-title" style="font-size:12px;">本月来访指标及达成</td></tr>
<tr class="table-header">
<td>月度客储指标</td>
<td>截至昨日来访</td>
<td>完成率</td>
<td>进度达成率</td>
<td>总组数</td>
<td>转化率</td>
</tr>
<tr>
<td class="data-value">{month_visit_target}</td>
<td class="data-value">{month_visit_actual}</td>
<td class="data-red">{visit_completion}%</td>
<td class="data-red">{progress_rate}%</td>
<td class="data-value">{month_visit_actual}</td>
<td>-</td>
</tr>
<tr style="background:#f5f5f5; font-size:9px;">
<td colspan="6" style="text-align:left; color:#888;">注：时间进度{time_progress}%（{day_of_month}/{days_in_month}天），来访指标{visit_comment}</td>
</tr>
</table>
</div>

<div>
<table>
<tr><td colspan="5" class="section-title" style="font-size:12px;">本月来访客户意向等级分析</td></tr>
<tr class="table-header">
<td>A级（高意向）</td>
<td>B级（中高）</td>
<td>C级（中意向）</td>
<td>D级（低意向）</td>
<td>合计</td>
</tr>
<tr>
<td class="data-value">{intent_A}</td>
<td class="data-value">{intent_B}</td>
<td class="data-value">{intent_C}</td>
<td class="data-value">{intent_D}</td>
<td class="data-value" style="font-size:16px;">{intent_total}</td>
</tr>
<tr style="background:#f5f5f5;">
<td>{intent_A_pct}%</td>
<td>{intent_B_pct}%</td>
<td>{intent_C_pct}%</td>
<td>{intent_D_pct}%</td>
<td>100%</td>
</tr>
</table>
</div>
</div>

<!-- 销售指标 + 成交意向等级 -->
<div class="col-2">
<div>
<table>
<tr><td colspan="6" class="section-title" style="font-size:12px;">本月销售指标及达成</td></tr>
<tr class="table-header">
<td>月度销售指标(万)</td>
<td>截至昨日成交(万)</td>
<td>完成率</td>
<td>进度达成率</td>
<td>总套数</td>
<td>转化率</td>
</tr>
<tr>
<td class="data-value">{month_sales_target}</td>
<td class="data-value">{deal_amount_display}</td>
<td class="data-red">{sales_completion}</td>
<td class="data-red">{sales_progress_rate}</td>
<td class="data-value">{month_deals}</td>
<td>-</td>
</tr>
<tr style="background:#fff3cd; font-size:9px;">
<td colspan="6" style="text-align:left;">{deal_warning}</td>
</tr>
</table>
</div>

<div>
<table>
<tr><td colspan="5" class="section-title" style="font-size:12px;">本月成交客户意向等级分析</td></tr>
<tr class="table-header">
<td>A级</td>
<td>B级</td>
<td>C/C+级</td>
<td>D级</td>
<td>合计</td>
</tr>
<tr>
<td class="data-value">{deal_A}</td>
<td>{deal_B if deal_B else '-'}</td>
<td>{deal_C if deal_C else '-'}</td>
<td>{deal_D if deal_D else '-'}</td>
<td class="data-value">{month_deals}</td>
</tr>
<tr style="background:#f5f5f5;">
<td>{deal_A_pct}%</td>
<td>{deal_B_pct}%</td>
<td>{deal_C_pct}%</td>
<td>{deal_D_pct}%</td>
<td>100%</td>
</tr>
</table>
</div>
</div>

<!-- 来访渠道分布 -->
<table>
<tr><td colspan="5" class="section-title" style="font-size:12px;">来访渠道分布（本月）</td></tr>
<tr class="table-header">
<td>渠道类型</td>
<td>来访组数</td>
<td>占比</td>
<td>意向等级分布</td>
<td>备注</td>
</tr>
{channel_rows}
<tr style="background:#1F4E79; color:#fff;">
<td><strong>合计</strong></td>
<td class="data-value" style="color:#fff;">{channel_total}</td>
<td>100%</td>
<td>A:{intent_A}, B:{intent_B}, C:{intent_C}, D:{intent_D}</td>
<td>-</td>
</tr>
</table>

<!-- 存量客户汇总 -->
<table>
<tr><td colspan="7" class="section-title" style="font-size:12px;">存量客户本周复访 - 近3月未成交（{report_data['three_months_ago']} ~ {yesterday}）</td></tr>
<tr class="table-header">
<td>渠道</td>
<td>未成交总数</td>
<td>A级</td>
<td>B级</td>
<td>C级</td>
<td>D级</td>
<td>占比</td>
</tr>
{stock_summary_rows}
</table>

<!-- 存量客户明细 -->
<table>
<tr><td colspan="12" class="section-title" style="font-size:12px; background:#C59BA6;">存量客户预计本周复访明细</td></tr>
<tr class="table-header-peach">
<td class="no">序号</td>
<td>客户姓名</td>
<td>来访渠道</td>
<td>置业顾问</td>
<td>最近来访</td>
<td>意向等级</td>
<td>跟进情况</td>
<td>决策周期</td>
<td>未成交原因</td>
<td>本周复访概率</td>
<td>复访成交概率</td>
<td>跟进策略</td>
</tr>
{stock_detail_rows}
<tr class="light-bg">
<td colspan="12" style="text-align:left; font-size:10px; color:#666;">
注：以上为近3月有来访记录但未成交的客户，按最近来访时间排序。高意向（A级）客户{intent_A}组，建议重点跟进。
</td>
</tr>
</table>

<!-- 昨日来访明细 -->
<table>
<tr><td colspan="7" class="section-title" style="font-size:12px;">昨日来访明细（{yesterday} 共{yesterday_visits}组）</td></tr>
<tr class="table-header">
<td class="no">序号</td>
<td>到访时间</td>
<td>顾问</td>
<td>到访次数</td>
<td>停留时长</td>
<td>首访/复访</td>
<td>备注</td>
</tr>
{yesterday_detail_rows}
<tr class="light-bg">
<td colspan="7" style="text-align:left; font-size:10px; color:#666;">
来访分析：{yesterday_analysis}。
</td>
</tr>
</table>

<!-- 顾问来访统计 -->
<table>
<tr><td colspan="5" class="section-title" style="font-size:12px;">顾问来访统计（本月截至{yesterday}）</td></tr>
<tr class="table-header">
<td>排名</td>
<td>顾问</td>
<td>昨日来访</td>
<td>本月来访</td>
<td>备注</td>
</tr>
{advisor_rows}
</table>

<!-- 数据说明 -->
<table>
<tr><td colspan="4" class="section-title" style="font-size:12px;">数据说明</td></tr>
<tr class="table-header-pink">
<td>数据项</td>
<td>数据来源</td>
<td>数据状态</td>
<td>备注</td>
</tr>
<tr>
<td>来访数据</td>
<td>旺小宝来访记录API</td>
<td class="data-value" style="color:#0a0;">已获取</td>
<td>{month_start}~{yesterday}共{month_visit_actual}组</td>
</tr>
<tr>
<td>意向等级</td>
<td>旺小宝客户画像API</td>
<td class="data-value" style="color:#0a0;">已获取</td>
<td>顾问评级(A/B/C/D)</td>
</tr>
<tr>
<td>渠道分类</td>
<td>旺小宝dynamicTags</td>
<td class="data-value" style="color:#0a0;">已获取</td>
<td>五大类来访渠道</td>
</tr>
<tr>
<td>成交数据</td>
<td>旺小宝客户画像API</td>
<td class="data-value" style="color:#f90;">待确认</td>
<td>本月成交{month_deals}组，金额{deal_amount}</td>
</tr>
<tr>
<td>月度KPI指标</td>
<td>IMA知识库/配置</td>
<td class="data-value" style="color:#0a0;">已配置</td>
<td>来访{month_visit_target}组/销售{month_sales_target}万</td>
</tr>
</table>

<!-- 页脚 -->
<div class="footer">
<p>{PROJECT_NAME} 营销日报 | 数据日期：{yesterday} | 生成时间：{today}</p>
<p>数据来源：旺小宝智能营销系统 | 本月来访{month_visit_actual}组 | 意向客户{intent_A}组（A级）</p>
<p style="color:#c00; font-weight:bold;">注：成交金额待从销售管理系统补充，建议每日同步</p>
</div>

</body>
</html>'''
    
    return html


def generate_pdf(html_path, pdf_path):
    """使用 Chrome/Edge headless 将 HTML 转为 PDF，排版与 HTML 完全一致"""
    if _BROWSER_PATH is None:
        print("    [PDF] 未找到 Chrome/Edge，跳过 PDF 生成")
        print("    请安装 Google Chrome 或 Microsoft Edge 浏览器")
        return False
    try:
        # 用浏览器 headless 打印 PDF
        cmd = [
            _BROWSER_PATH,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--print-background",
            f"--print-to-pdf={pdf_path}",
            f"file:///{html_path.replace(chr(92), '/')}"
        ]
        # 过滤掉可能导致编码问题的环境
        env = os.environ.copy()
        env.pop("PYTHONIOENCODING", None)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=60
        )
        if result.returncode == 0 and os.path.exists(pdf_path):
            print(f"    [PDF] 已生成: {pdf_path}")
            return True
        else:
            print(f"    [PDF] 浏览器打印失败: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"    [PDF] 生成失败: {e}")
        return False


def main(date_str=None):
    """主函数"""
    if date_str is None:
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = date_str
    
    # 月份第一天
    month_start = yesterday[:7] + '-01'
    # 3个月前
    three_months_ago = (datetime.strptime(yesterday, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d')
    
    print("=" * 60)
    print(f"{PROJECT_NAME} 日报生成 - {yesterday}")
    print("=" * 60)
    
    # 检查token
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: 未找到旺小宝授权token，请先授权")
        print("提示：系统会引导你完成OAuth授权")
        return None
    
    token = get_token()
    
    try:
        # 1. 昨日来访
        print("\n[1] 拉取昨日来访数据...")
        yesterday_visits = get_yesterday_visits(token, yesterday)
        print(f"    昨日来访: {len(yesterday_visits)}组")
        
        # 2. 本月来访
        print("\n[2] 拉取本月来访数据...")
        month_visits = get_month_visits(token, month_start, yesterday)
        print(f"    本月来访: {len(month_visits)}组")
        
        # 3. 客户画像
        print("\n[3] 拉取客户画像数据...")
        customers = get_customers(token, month_start, yesterday)
        print(f"    本月客户总数: {len(customers)}")
        
        # 意向等级
        intent_dist = analyze_intent(customers)
        print("\n    意向等级分布:")
        for level, cnt in sorted(intent_dist.items(), key=lambda x: -x[1]):
            if cnt > 0:
                print(f"      {level}: {cnt}组")
        
        # 渠道分布
        channel_dist = analyze_channel(customers)
        print("\n    渠道分布:")
        for ch, cnt in sorted(channel_dist.items(), key=lambda x: -x[1]):
            print(f"      {ch}: {cnt}组")
        
        # 4. 存量客户
        print("\n[4] 拉取存量客户数据...")
        stock_customers = get_stock_customers(token, three_months_ago, yesterday)
        print(f"    存量客户(未成交): {len(stock_customers)}组")
        
        # 5. 成交客户
        print("\n[5] 分析成交数据...")
        deal_customers = [c for c in customers if c.get('dealStatus') == 1]
        deal_intent = analyze_intent(deal_customers)
        print(f"    本月成交: {len(deal_customers)}组")
        
        # 6. 存量客户按渠道分析
        stock_by_channel = analyze_channel_with_intent(stock_customers)
        
        # 整理来访明细
        yesterday_visit_list = [{
            'time': v['visitTime'].split(' ')[1] if ' ' in v.get('visitTime', '') else v.get('visitTime', ''),
            'advisor': v.get('userName', ''),
            'count': v.get('visitCount', 1),
            'duration': int(int(v.get('visitTimer', '0')) / 60000) if v.get('visitTimer', '0') != '0' else 0
        } for v in yesterday_visits]
        
        # 构建报告数据
        report_data = {
            'date': today,
            'yesterday': yesterday,
            'month_start': month_start,
            'three_months_ago': three_months_ago,
            'project_name': PROJECT_NAME,
            'month_visit_target': KPI_CONFIG['month_visit_target'],
            'month_visit_actual': len(month_visits),
            'yesterday_visits': len(yesterday_visits),
            'yesterday_visit_list': yesterday_visit_list,
            'month_sales_target': KPI_CONFIG['month_sales_target'],
            'month_deals': len(deal_customers),
            'deal_amount': '待填报',
            'intent_dist': intent_dist,
            'channel_dist': channel_dist,
            'stock_customers': stock_customers[:10],  # 只取前10条
            'stock_by_channel': stock_by_channel,
            'deal_intent': deal_intent
        }
        
        # 生成HTML
        print("\n[6] 生成HTML日报...")
        html_content = generate_html(report_data)
        
        # 保存 HTML 文件
        date_str_short = yesterday.replace('-', '')
        html_path = os.path.join(OUTPUT_DIR, f"{PROJECT_NAME}_日报_{date_str_short}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\nHTML日报已生成: {html_path}")
        
        # 同时生成 PDF
        pdf_path = os.path.splitext(html_path)[0] + '.pdf'
        print("\n[7] 生成PDF日报...")
        pdf_ok = generate_pdf(html_path, pdf_path)
        if pdf_ok:
            print(f"PDF日报已生成: {pdf_path}")
        else:
            print("    PDF生成跳过（浏览器不可用）")
        print("\n" + "=" * 60)
        print("数据摘要")
        print("=" * 60)
        print(f"本月来访: {len(month_visits)}组 (目标{KPI_CONFIG['month_visit_target']}组)")
        print(f"昨日来访: {len(yesterday_visits)}组")
        print(f"本月成交: {len(deal_customers)}组")
        print(f"存量客户: {len(stock_customers)}组")
        print(f"\nHTML: {html_path}")
        if pdf_ok:
            print(f"PDF:  {pdf_path}")
        
        result = (html_path, pdf_path) if pdf_ok else (html_path, None)
        return result
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="旺小宝项目日报生成")
    parser.add_argument("date", nargs="?", default=None, help="日期 YYYY-MM-DD（默认昨日）")
    parser.add_argument("--tenant-id", help="旺小宝租户ID（覆盖环境变量）")
    parser.add_argument("--project-id", help="旺小宝项目ID（覆盖环境变量）")
    parser.add_argument("--project-name", help="项目名称（覆盖环境变量）")
    parser.add_argument("--month-visit-target", type=int, help="月度来访目标")
    parser.add_argument("--month-sales-target", type=int, help="月度销售目标（万元）")
    args = parser.parse_args()

    if args.tenant_id:
        TENANT_ID = args.tenant_id
    if args.project_id:
        PROJECT_ID = args.project_id
    if args.project_name:
        PROJECT_NAME = args.project_name
    if args.month_visit_target is not None:
        KPI_CONFIG["month_visit_target"] = args.month_visit_target
    if args.month_sales_target is not None:
        KPI_CONFIG["month_sales_target"] = args.month_sales_target

    main(args.date)
