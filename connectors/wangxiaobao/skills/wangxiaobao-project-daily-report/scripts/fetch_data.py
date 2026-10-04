# -*- coding: utf-8 -*-
"""
旺小宝项目日报数据拉取脚本
功能：拉取旺小宝API数据，生成日报所需数据
"""
import json
import subprocess
import os
import argparse
from collections import Counter

# 项目配置（优先级：命令行参数 > 环境变量 > 默认值）
TENANT_ID = os.environ.get("XIAOBAO_TENANT_ID", "")
PROJECT_ID = os.environ.get("XIAOBAO_PROJECT_ID", "")
PROJECT_NAME = os.environ.get("XIAOBAO_PROJECT_NAME", "<项目名>")
# KPI指标（示例值 500 / 21000，请按项目实际目标调整）
MONTH_VISIT_TARGET = int(os.environ.get("XIAOBAO_MONTH_VISIT_TARGET", "500"))
MONTH_SALES_TARGET = int(os.environ.get("XIAOBAO_MONTH_SALES_TARGET", "21000"))
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".openclaw/state/wangxiaobao/token.json")


def get_token():
    """获取旺小宝access token"""
    with open(TOKEN_PATH, 'r') as f:
        return json.load(f)['access_token']


def api_call(endpoint, body, token):
    """调用旺小宝API"""
    cmd = [
        'curl', '-s', '-X', 'POST',
        f'https://open-ai.wangxiaobao.com{endpoint}',
        '-H', f'Authorization: Bearer {token}',
        '-H', f'X-Tenant-Id: {TENANT_ID}',
        '-H', f'X-Project-Id: {PROJECT_ID}',
        '-H', 'Content-Type: application/json',
        '-d', body
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def get_yesterday_visits(token, yesterday):
    """获取昨日来访数据"""
    body = json.dumps({
        "current": 1, "size": 100,
        "startTime": f"{yesterday} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    })
    data = api_call("/ai-open/visits/page", body, token)
    all_visits = data.get('data', {}).get('content', [])
    # 过滤只保留昨日
    return [v for v in all_visits if v.get('visitTime', '').startswith(yesterday)]


def get_month_visits(token, month_start, yesterday):
    """获取本月来访数据"""
    body = json.dumps({
        "current": 1, "size": 500,
        "startTime": f"{month_start} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    })
    data = api_call("/ai-open/visits/page", body, token)
    all_visits = data.get('data', {}).get('content', [])
    # 过滤本月
    return [v for v in all_visits if v.get('visitTime', '').startswith('2026-05-')]


def get_customers(token, month_start, yesterday):
    """获取客户画像数据"""
    body = json.dumps({
        "page": 1, "size": 500,
        "startTime": f"{month_start} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    })
    data = api_call("/ai-open/customers/page", body, token)
    return data.get('data', {}).get('content', [])


def get_stock_customers(token, three_months_ago, yesterday):
    """获取存量客户（近3月未成交）"""
    body = json.dumps({
        "page": 1, "size": 100,
        "startTime": f"{three_months_ago} 00:00:00",
        "endTime": f"{yesterday} 23:59:59"
    })
    data = api_call("/ai-open/customers/page", body, token)
    all_custs = data.get('data', {}).get('content', [])
    # 过滤未成交
    return [c for c in all_custs if c.get('dealStatus') != 1]


def analyze_intent(customers):
    """分析意向等级分布"""
    intent_dist = Counter()
    for c in customers:
        level = c.get('intentLevel', '未知') or '未知'
        if level == '':
            level = '未知'
        intent_dist[level] += 1
    return dict(intent_dist)


def analyze_channel(customers):
    """分析渠道分布"""
    channel_dist = Counter()
    for c in customers:
        tags = c.get('dynamicTags', {})
        channel = tags.get('五大类来访渠道', '未知')
        if channel == '':
            channel = '未知'
        channel_dist[channel] += 1
    return dict(channel_dist)


def main(date_str='2026-05-21'):
    """主函数"""
    today = date_str
    yesterday = '2026-05-20'
    month_start = '2026-05-01'
    three_months_ago = '2026-02-20'

    print("="*60)
    print(f"{PROJECT_NAME}日报数据拉取 - {today}")
    print("="*60)

    token = get_token()

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
        print(f"      {level}: {cnt}组")

    # 渠道分布
    channel_dist = analyze_channel(customers)
    print("\n    渠道分布:")
    for ch, cnt in sorted(channel_dist.items(), key=lambda x: -x[1])[:5]:
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
    print("    成交意向等级:", deal_intent)

    # 保存数据
    report_data = {
        'date': today,
        'yesterday': yesterday,
        'project_name': PROJECT_NAME,
        'month_visit_target': MONTH_VISIT_TARGET,
        'month_visit_actual': len(month_visits),
        'yesterday_visits': len(yesterday_visits),
        'yesterday_visit_list': [{
            'time': v['visitTime'].split(' ')[1],
            'advisor': v['userName'],
            'count': v['visitCount'],
            'duration': int(int(v.get('visitTimer', '0')) / 60000) if v.get('visitTimer', '0') != '0' else 0
        } for v in yesterday_visits],
        'month_sales_target': MONTH_SALES_TARGET,
        'month_deals': len(deal_customers),
        'visit_intent': intent_dist,
        'channel_dist': channel_dist,
        'stock_total': len(stock_customers),
        'deal_intent': deal_intent
    }

    output_path = os.path.join(os.getcwd(), "final_report_data.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n数据已保存: {output_path}")
    return report_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="旺小宝项目日报数据拉取")
    parser.add_argument("date", nargs="?", default="2026-05-21", help="日期 YYYY-MM-DD")
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
        MONTH_VISIT_TARGET = args.month_visit_target
    if args.month_sales_target is not None:
        MONTH_SALES_TARGET = args.month_sales_target

    main(args.date)
