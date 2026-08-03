#!/usr/bin/env python3
"""
南非人力行政合规工具
====================
合规日历 / 签证清单 / B-BBEE评分卡 / 法定休假权益 / 通知期速查。
纯 Python 标准库，无外部依赖。

用法：
    python refs.py calendar
    python refs.py visa --type critical-skills
    python refs.py visa --type general-work
    python refs.py bbbee --level generic
    python refs.py leave
    python refs.py notice --years 3
"""

import argparse
import json
import sys
from pathlib import Path

# ============================================================
# 数据目录
# ============================================================
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ============================================================
# 合规日历
# ============================================================

COMPLIANCE_CALENDAR = [
    {
        "obligation": "EMP201 月度申报",
        "frequency": "月度",
        "deadline": "每月7日",
        "covers": "PAYE + UIF + SDL",
        "authority": "SARS",
        "penalty": "逾期10%罚金 + 利息",
        "law": "Tax Administration Act",
    },
    {
        "obligation": "EMP501 年度对账",
        "frequency": "半年度",
        "deadline": "5月31日（年度对账，覆盖3月1日-次年2月底）/ 10月31日（中期对账，覆盖3月1日-8月31日）",
        "covers": "PAYE/UIF/SDL 年度核对 + IRP5/IT3(a)",
        "authority": "SARS",
        "penalty": "逾期1%-10%罚金",
        "law": "Tax Administration Act",
    },
    {
        "obligation": "UIF 月度缴费",
        "frequency": "月度",
        "deadline": "随 EMP201（每月7日）",
        "covers": "UIF 雇主1% + 雇员1%",
        "authority": "SARS → UIF (DOL)",
        "penalty": "逾期利息 + 罚款",
        "law": "Unemployment Insurance Act",
    },
    {
        "obligation": "COIDA ROE 申报",
        "frequency": "年度",
        "deadline": "每年6月30日（3月31日财年截止后）",
        "covers": "Return of Earnings（年收入申报）",
        "authority": "Compensation Fund (DOL)",
        "penalty": "滞纳金 + Letter of Good Standing失效",
        "law": "COIDA",
    },
    {
        "obligation": "WSP/ATR 提交",
        "frequency": "年度",
        "deadline": "每年4月30日",
        "covers": "年度工作技能计划 + 年度培训报告",
        "authority": "所属 SETA",
        "penalty": "丧失Mandatory Grant（20%返还）",
        "law": "Skills Development Act / SDL",
    },
    {
        "obligation": "EEA2 就业公平年度报告",
        "frequency": "年度",
        "deadline": "每年1月15日（电子提交，首个工作日截止）",
        "covers": "指定雇主（50+员工）就业公平报告",
        "authority": "Department of Employment and Labour (DEL)",
        "penalty": "罚款最高R2.7M或10%营业额",
        "law": "Employment Equity Act",
    },
    {
        "obligation": "EEA4 收入差异分析",
        "frequency": "年度",
        "deadline": "随 EEA2（每年1月15日）",
        "covers": "收入差异分析报告",
        "authority": "DEL",
        "penalty": "同 EEA2",
        "law": "Employment Equity Act",
    },
    {
        "obligation": "EE 5年计划",
        "frequency": "5年一次",
        "deadline": "2025年8月31日（新周期截止）",
        "covers": "5年就业公平计划",
        "authority": "DEL",
        "penalty": "Section 53合规证书无法获取",
        "law": "EE Amendment Act 2022",
    },
    {
        "obligation": "CIPC 年度申报",
        "frequency": "年度",
        "deadline": "公司成立纪念日起30天内",
        "covers": "Annual Return + 受益所有权申报",
        "authority": "CIPC",
        "penalty": "公司被注销（deregistration）",
        "law": "Companies Act / General Laws Amendment Act 2022",
    },
    {
        "obligation": "VAT201 申报",
        "frequency": "双月（自然人/小企业）或月度（大企业）",
        "deadline": "申报期结束后最后一个工作日",
        "covers": "增值税申报（15%标准税率）",
        "authority": "SARS",
        "penalty": "逾期10%罚金 + 利息",
        "law": "VAT Act",
    },
    {
        "obligation": "POPIA 合规",
        "frequency": "持续",
        "deadline": "持续合规（信息官已指定）",
        "covers": "个人信息保护合规框架",
        "authority": "Information Regulator",
        "penalty": "罚款最高R10M + 民事诉讼",
        "law": "POPIA",
    },
    {
        "obligation": "OHSA 年度报告",
        "frequency": "年度",
        "deadline": "每年3月31日（WCL 3表）",
        "covers": "工伤年度统计报告",
        "authority": "DEL (Inspectorate)",
        "penalty": "行政罚款 + 刑事追诉",
        "law": "OHSA",
    },
]

# ============================================================
# 签证清单
# ============================================================

VISA_TYPES = {
    "critical-skills": {
        "name": "关键技能工作签证",
        "validity": "最长5年",
        "key_requirements": [
            "有效护照（有效期覆盖签证期限）",
            "关键技能清单上的职业（Critical Skills List）",
            "SAQA 学历认证",
            "职业机构注册证明（如SACPCMP/ECSA等，视职业而定）",
            "雇主聘用证明（2024改革后须有工作offer）",
            "体检报告（radiology + general）",
            "警局无犯罪证明（所有居住超12个月的国家）",
            "签证申请表 DHA-1738",
            "申请费缴费证明",
        ],
        "processing_time": "8-12周",
        "points_required": "100分（积分制PBS）",
        "notes": "2024年10月积分制改革，须达到100分阈值；SAQA认证须提前办理",
    },
    "general-work": {
        "name": "一般工作签证",
        "validity": "最长3年",
        "key_requirements": [
            "有效护照",
            "雇主聘用证明",
            "DOEL（劳工部）推荐信（证明无法在本地招到合适人选）",
            "SAQA 学历认证",
            "体检报告",
            "警局无犯罪证明",
            "签证申请表 DHA-1738",
            "申请费缴费证明",
        ],
        "processing_time": "8-12周（DOEL推荐信可能更长）",
        "points_required": "N/A（非积分制，须DOEL推荐）",
        "notes": "最难获取的工签类型，须证明本地招聘失败",
    },
    "intra-company-transfer": {
        "name": "公司内部调动签证",
        "validity": "4年（不可续签）",
        "key_requirements": [
            "有效护照",
            "母公司雇用证明（至少6个月）",
            "南非接收公司证明",
            "母公司与南非公司的关联关系证明",
            "SAQA 学历认证",
            "体检报告",
            "警局无犯罪证明",
            "签证申请表 DHA-1738",
        ],
        "processing_time": "8-12周",
        "points_required": "N/A",
        "notes": "4年到期不可续签，须离境重新申请；适合跨国公司外派",
    },
    "corporate": {
        "name": "企业签证",
        "validity": "3年（企业级），个人附属签证同期限",
        "key_requirements": [
            "南非注册公司证明",
            "企业签证申请表 DHA-1739",
            "60%以上本地雇员比例证明",
            "企业签证计划书（说明需引进外籍员工的理由）",
            "DOEL 推荐信",
            "注册资金/投资证明",
            "体检报告（每位申请人）",
            "无犯罪证明（每位申请人）",
        ],
        "processing_time": "12-16周",
        "points_required": "N/A",
        "notes": "适合需批量引进外籍员工的企业；先获批企业签证再为个人申请附属签证",
    },
    "business": {
        "name": "商务签证（投资移民）",
        "validity": "3年（可续签）",
        "key_requirements": [
            "有效护照",
            "最低投资额 R5,000,000（部分行业可豁免）",
            "投资计划书",
            "DTIC（贸易工业竞争部）推荐信",
            "企业注册证明（CIPC）",
            "体检报告",
            "警局无犯罪证明",
            "签证申请表",
        ],
        "processing_time": "12-16周",
        "points_required": "N/A",
        "notes": "投资移民途径，R500万最低投资额；部分行业可申请豁免",
    },
    "remote-work": {
        "name": "远程工作签证（数字游牧）",
        "validity": "3年",
        "key_requirements": [
            "有效护照",
            "年收入不低于 R650,976（约R54,248/月）",
            "境外雇主证明或自雇证明",
            "SARS 税务注册（如在南非停留超183天）",
            "无犯罪证明",
            "体检报告",
            "申请费 R425",
        ],
        "processing_time": "6-8周",
        "points_required": "N/A",
        "notes": "2024年10月9日Gazette发布，2025年3月全面实施；适合远程工作者",
    },
}

# ============================================================
# B-BBEE 评分卡
# ============================================================

BBBEE_GENERIC_SCORECARD = [
    {"element": "所有权 Ownership", "weight": 25, "bonus": 4, "priority": True,
     "sub_min": "40%（净值8分+投票权4分）",
     "description": "黑人所有权比例，含投票权、经济利益、净值"},
    {"element": "管理控制 Management Control", "weight": 15, "bonus": 4, "priority": True,
     "sub_min": "40%（董事会+执行董事+其他高管）",
     "description": "黑人在管理层的代表性"},
    {"element": "技能发展 Skills Development", "weight": 20, "bonus": 5, "priority": True,
     "sub_min": "40%",
     "description": "6%薪酬支出用于培训 + WSP/ATR + Section 12H"},
    {"element": "企业供应商发展 ESD", "weight": 40, "bonus": 0, "priority": True,
     "sub_min": "40%（PP 25+ED 5+SD 10）",
     "description": "优先采购25分+企业发展5分+供应商发展10分，最高权重"},
    {"element": "社会经济发展 Socio-Economic", "weight": 5, "bonus": 0, "priority": False,
     "sub_min": "N/A",
     "description": "1% NPAT 用于社会经济发展"},
]

BBBEE_LEVELS = [
    {"level": 1, "points_range": "100+", "recognition": "135%", "description": "最高级别"},
    {"level": 2, "points_range": "95-99.99", "recognition": "125%", "description": "优秀"},
    {"level": 3, "points_range": "90-94.99", "recognition": "110%", "description": "良好"},
    {"level": 4, "points_range": "80-89.99", "recognition": "100%", "description": "合规基准"},
    {"level": 5, "points_range": "75-79.99", "recognition": "80%", "description": "中等"},
    {"level": 6, "points_range": "70-74.99", "recognition": "70%", "description": "待提升"},
    {"level": 7, "points_range": "55-69.99", "recognition": "50%", "description": "较低"},
    {"level": 8, "points_range": "40-54.99", "recognition": "10%", "description": "最低合规"},
    {"level": "NC", "points_range": "<40", "recognition": "0%", "description": "不合规"},
]

BBBEE_CATEGORIES = {
    "eme": {"name": "EME 豁免微型企业", "threshold": "年营业额 < R10M", "auto_level": 4, "note": "自动Level 4，黑人所有权≥51%可升至Level 2/1"},
    "qse": {"name": "QSE 合格小企业", "threshold": "R10M ≤ 年营业额 < R50M", "auto_level": None, "note": "须评估优先要素（所有权+技能发展+ESD）"},
    "generic": {"name": "Generic 一般企业", "threshold": "年营业额 ≥ R50M", "auto_level": None, "note": "须评估全部五要素"},
}

# ============================================================
# 法定休假权益
# ============================================================

LEAVE_ENTITLEMENTS = {
    "annual": {"name": "年假", "days": "21天连续工作（=15个工作日/年）", "law": "BCEA Section 20", "note": "每12个月21天连续休假"},
    "sick": {"name": "病假", "days": "36天/3年周期（6周/年）", "law": "BCEA Section 22", "note": "3年周期内36天全薪病假"},
    "maternity": {"name": "产假", "days": "4个月（连续）", "law": "BCEA Section 25", "note": "产前/产后各至少4周（除非医生另有指示）"},
    "family_responsibility": {"name": "家庭责任假", "days": "3天/年", "law": "BCEA Section 27", "note": "子女出生/生病/家庭成员去世"},
    "parental": {"name": "育儿假（父亲）", "days": "10天/年", "law": "BCEA Section 25A (2023)", "note": "2023年修订新增；Van Wyk 2025判决后所有父母均享4月+10天"},
    "adoption": {"name": "收养假", "days": "10周（收养<2岁儿童）", "law": "BCEA Section 25B (2023)", "note": "2023年修订新增"},
    "commissioning": {"name": "代孕假", "days": "10周", "law": "BCEA Section 25C (2023)", "note": "2023年修订新增"},
}

# ============================================================
# 通知期
# ============================================================

NOTICE_PERIODS = [
    {"service": "≤6个月", "notice": "1周", "law": "BCEA Section 37"},
    {"service": "6个月-1年", "notice": "2周", "law": "BCEA Section 37"},
    {"service": ">1年", "notice": "4周", "law": "BCEA Section 37"},
]

# ============================================================
# 输出函数
# ============================================================

def print_calendar():
    print("\n" + "=" * 80)
    print("  南非人力行政合规日历")
    print("=" * 80)
    for item in COMPLIANCE_CALENDAR:
        print(f"\n  📋 {item['obligation']}")
        print(f"     频率: {item['frequency']}")
        print(f"     截止: {item['deadline']}")
        print(f"     范围: {item['covers']}")
        print(f"     主管: {item['authority']}")
        print(f"     罚则: {item['penalty']}")
        print(f"     依据: {item['law']}")
    print(f"\n  共 {len(COMPLIANCE_CALENDAR)} 项合规义务")


def print_visa(visa_type: str):
    if visa_type not in VISA_TYPES:
        print(f"未知签证类型: {visa_type}")
        print(f"可用类型: {', '.join(VISA_TYPES.keys())}")
        sys.exit(1)

    v = VISA_TYPES[visa_type]
    print("\n" + "=" * 80)
    print(f"  {v['name']}")
    print("=" * 80)
    print(f"\n  有效期: {v['validity']}")
    print(f"  处理时间: {v['processing_time']}")
    print(f"  积分要求: {v['points_required']}")
    print(f"\n  所需材料:")
    for i, req in enumerate(v['key_requirements'], 1):
        print(f"    {i}. {req}")
    print(f"\n  备注: {v['notes']}")


def print_bbbee(category: str):
    cat = BBBEE_CATEGORIES.get(category, BBBEE_CATEGORIES["generic"])
    print("\n" + "=" * 80)
    print(f"  B-BBEE 评分卡 — {cat['name']}")
    print("=" * 80)
    print(f"\n  适用门槛: {cat['threshold']}")
    if cat['auto_level']:
        print(f"  自动等级: Level {cat['auto_level']}")
    print(f"  备注: {cat['note']}")

    print(f"\n  五大要素:")
    for elem in BBBEE_GENERIC_SCORECARD:
        priority_mark = "★优先" if elem['priority'] else ""
        print(f"\n    {elem['element']} ({elem['weight']}分+{elem['bonus']}加分) {priority_mark}")
        print(f"      子最低要求: {elem['sub_min']}")
        print(f"      说明: {elem['description']}")

    print(f"\n  认证等级:")
    for level in BBBEE_LEVELS:
        print(f"    Level {level['level']}: {level['points_range']}分 → {level['recognition']} procurement认可 ({level['description']})")


def print_leave():
    print("\n" + "=" * 80)
    print("  南非法定休假权益（BCEA）")
    print("=" * 80)
    for key, leave in LEAVE_ENTITLEMENTS.items():
        print(f"\n  {leave['name']}: {leave['days']}")
        print(f"    依据: {leave['law']}")
        print(f"    说明: {leave['note']}")


def print_notice(years: float):
    print("\n" + "=" * 80)
    print("  法定通知期（BCEA Section 37）")
    print("=" * 80)
    for item in NOTICE_PERIODS:
        print(f"  服务 {item['service']}: 通知期 {item['notice']} ({item['law']})")

    if years <= 0.5:
        applicable = "1周"
    elif years <= 1:
        applicable = "2周"
    else:
        applicable = "4周"

    print(f"\n  按您输入的服务年限 {years} 年 → 适用通知期: {applicable}")
    print(f"  注意: 通知不可与休假同时进行；雇主或雇员均可发起终止")


def main():
    parser = argparse.ArgumentParser(
        description="南非人力行政合规工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("calendar", help="合规申报日历")
    p_visa = subparsers.add_parser("visa", help="签证申请清单")
    p_visa.add_argument("--type", required=True, choices=list(VISA_TYPES.keys()))
    p_bbbee = subparsers.add_parser("bbbee", help="B-BBEE 评分卡")
    p_bbbee.add_argument("--level", default="generic", choices=list(BBBEE_CATEGORIES.keys()))
    subparsers.add_parser("leave", help="法定休假权益")
    p_notice = subparsers.add_parser("notice", help="通知期速查")
    p_notice.add_argument("--years", type=float, required=True, help="服务年限")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "calendar":
        print_calendar()
    elif args.command == "visa":
        print_visa(args.type)
    elif args.command == "bbbee":
        print_bbbee(args.level)
    elif args.command == "leave":
        print_leave()
    elif args.command == "notice":
        print_notice(args.years)


if __name__ == "__main__":
    main()
