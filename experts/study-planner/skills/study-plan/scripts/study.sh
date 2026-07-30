#!/usr/bin/env bash
# study-plan: 学习计划生成器
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

CMD="${1:-help}"
shift 2>/dev/null || true

python3 - "$CMD" "$@" << 'PYTHON_EOF'
# -*- coding: utf-8 -*-
import sys
import json
import math
from datetime import datetime, timedelta

def show_help():
    print("""
=== 学习计划生成器 ===

用法:
  study.sh plan "考试类型" "备考天数"              生成完整备考计划
  study.sh daily "今天要学的内容"                  生成当日详细计划
  study.sh review "已学内容"                       基于艾宾浩斯遗忘曲线生成复习安排
  study.sh pomodoro "学习内容" [--rounds 4]        番茄钟学习安排
  study.sh help                                    显示此帮助

支持考试类型: 考研、高考、四六级、公务员、雅思、托福 等
""".strip())

EXAM_CONFIGS = {
    "考研": {
        "subjects": ["政治", "英语", "数学/专业课一", "专业课二"],
        "phases": [
            {"name": "基础阶段", "ratio": 0.35, "desc": "系统学习教材，打牢基础，不求速度求理解"},
            {"name": "强化阶段", "ratio": 0.30, "desc": "专题训练，重难点突破，形成知识框架"},
            {"name": "冲刺阶段", "ratio": 0.20, "desc": "真题演练，模拟考试，查漏补缺"},
            {"name": "考前阶段", "ratio": 0.15, "desc": "回归基础，重点记忆，调整心态"},
        ],
        "daily_hours": 10,
        "tips": ["政治可以晚些开始，9月后重点突击", "英语阅读每天至少2篇", "数学要大量刷题"],
    },
    "高考": {
        "subjects": ["语文", "数学", "英语", "理综/文综"],
        "phases": [
            {"name": "一轮复习", "ratio": 0.40, "desc": "全面回顾，逐章过知识点，建立完整知识体系"},
            {"name": "二轮复习", "ratio": 0.30, "desc": "专题突破，串联知识点，提升综合能力"},
            {"name": "三轮复习", "ratio": 0.20, "desc": "套卷训练，限时做题，适应考场节奏"},
            {"name": "考前调整", "ratio": 0.10, "desc": "回归课本，看错题本，保持手感"},
        ],
        "daily_hours": 12,
        "tips": ["语文作文每周至少练1篇", "数学错题要反复做3遍", "英语每天背30个单词"],
    },
    "四六级": {
        "subjects": ["听力", "阅读", "写作", "翻译"],
        "phases": [
            {"name": "词汇阶段", "ratio": 0.30, "desc": "突击词汇量，每天100-150词"},
            {"name": "专项阶段", "ratio": 0.35, "desc": "分项训练听力、阅读、写作、翻译"},
            {"name": "真题阶段", "ratio": 0.25, "desc": "刷近10年真题，总结出题规律"},
            {"name": "模考阶段", "ratio": 0.10, "desc": "全真模考，调整做题顺序和时间分配"},
        ],
        "daily_hours": 4,
        "tips": ["听力要精听+泛听结合", "阅读先看题再看文", "作文背诵模板很有效"],
    },
    "公务员": {
        "subjects": ["行测-言语理解", "行测-数量关系", "行测-判断推理", "行测-资料分析", "申论"],
        "phases": [
            {"name": "基础学习", "ratio": 0.30, "desc": "系统学习各模块知识点和解题方法"},
            {"name": "专项突破", "ratio": 0.30, "desc": "大量刷题，总结规律，提升速度"},
            {"name": "套题训练", "ratio": 0.25, "desc": "做套卷，训练时间分配和做题顺序"},
            {"name": "冲刺备考", "ratio": 0.15, "desc": "查漏补缺，申论热点梳理，模拟面试"},
        ],
        "daily_hours": 8,
        "tips": ["行测重在速度，要严格限时", "申论多看人民日报评论员文章", "资料分析是提分最快的模块"],
    },
}

def plan(args):
    if len(args) < 2:
        print("[错误] 用法: study.sh plan \"考试类型\" \"备考天数\"")
        print("支持类型: {}".format("、".join(EXAM_CONFIGS.keys())))
        sys.exit(1)

    exam_type = args[0]
    try:
        total_days = int(args[1])
    except ValueError:
        print("[错误] 备考天数请输入数字")
        sys.exit(1)

    config = EXAM_CONFIGS.get(exam_type)
    if not config:
        # 通用模板
        config = {
            "subjects": ["科目一", "科目二", "科目三"],
            "phases": [
                {"name": "基础阶段", "ratio": 0.35, "desc": "系统学习，打牢基础"},
                {"name": "强化阶段", "ratio": 0.30, "desc": "专题训练，重难点突破"},
                {"name": "冲刺阶段", "ratio": 0.20, "desc": "真题演练，查漏补缺"},
                {"name": "考前阶段", "ratio": 0.15, "desc": "回归基础，调整心态"},
            ],
            "daily_hours": 8,
            "tips": ["制定计划要留有余量", "保证睡眠质量", "定期做模拟测试"],
        }
        print("⚠️  未找到「{}」的专项配置，使用通用模板".format(exam_type))
        print()

    today = datetime.now()
    exam_date = today + timedelta(days=total_days)

    print("=" * 60)
    print("  📚 {} 备考计划".format(exam_type))
    print("  📅 备考周期：{} → {}（共{}天）".format(
        today.strftime("%Y-%m-%d"), exam_date.strftime("%Y-%m-%d"), total_days))
    print("  ⏰ 建议每日学习时长：{}小时".format(config["daily_hours"]))
    print("=" * 60)

    print("\n📋 【科目清单】")
    for i, s in enumerate(config["subjects"], 1):
        print("  {}. {}".format(i, s))

    print("\n📊 【阶段规划】\n")
    start = today
    for phase in config["phases"]:
        days = max(1, int(total_days * phase["ratio"]))
        end = start + timedelta(days=days)
        print("┌─ {} ({} 天)".format(phase["name"], days))
        print("│  📅 {} → {}".format(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
        print("│  📝 {}".format(phase["desc"]))
        print("│")

        # 每周任务建议
        weeks = max(1, days // 7)
        subjects_per_week = config["subjects"]
        print("│  📌 每周任务分配：")
        hours_per_subject = config["daily_hours"] * 7.0 / len(subjects_per_week)
        for subj in subjects_per_week:
            print("│     • {} — 约{:.1f}小时/周".format(subj, hours_per_subject))
        print("└" + "─" * 50)
        print()
        start = end

    print("\n💡 【备考建议】\n")
    for i, tip in enumerate(config["tips"], 1):
        print("  {}. {}".format(i, tip))

    print("\n⚡ 【通用提醒】\n")
    general = [
        "每周至少休息半天，避免疲劳作战",
        "保持规律作息，保证7-8小时睡眠",
        "每完成一个阶段做一次自我检测",
        "建立错题本，定期回顾",
        "找学习伙伴互相监督，效果更好",
    ]
    for tip in general:
        print("  • {}".format(tip))

def daily(args):
    if not args:
        print("[错误] 用法: study.sh daily \"今天要学的内容\"")
        sys.exit(1)

    content = args[0]
    today = datetime.now()

    print("=" * 60)
    print("  📅 {} 每日学习计划".format(today.strftime("%Y-%m-%d %A")))
    print("  📖 学习内容：{}".format(content))
    print("=" * 60)

    schedule = [
        {"time": "08:00-08:30", "task": "晨读/回顾昨日内容", "detail": "花30分钟回顾昨天的笔记，巩固记忆"},
        {"time": "08:30-10:00", "task": "核心学习时段①", "detail": "学习「{}」的重点知识（最佳精力时段）".format(content)},
        {"time": "10:00-10:15", "task": "☕ 休息", "detail": "站起来活动，喝水，远眺"},
        {"time": "10:15-11:45", "task": "核心学习时段②", "detail": "继续深入学习，做课后习题"},
        {"time": "11:45-14:00", "task": "🍚 午餐+午休", "detail": "午休30-40分钟，不要超过1小时"},
        {"time": "14:00-15:30", "task": "练习与巩固", "detail": "针对「{}」做练习题，加深理解".format(content)},
        {"time": "15:30-15:45", "task": "☕ 休息", "detail": "短暂休息，切换状态"},
        {"time": "15:45-17:15", "task": "拓展学习", "detail": "学习相关联的知识点，构建知识网络"},
        {"time": "17:15-18:30", "task": "🏃 运动+晚餐", "detail": "运动30分钟，保持身体状态"},
        {"time": "18:30-20:00", "task": "错题整理与复习", "detail": "整理今天的错题，标注原因"},
        {"time": "20:00-21:30", "task": "自由学习/薄弱补强", "detail": "查漏补缺或预习明天内容"},
        {"time": "21:30-22:00", "task": "今日总结", "detail": "回顾今天学了什么，写学习日记"},
        {"time": "22:00-22:30", "task": "📖 轻松阅读", "detail": "读点课外书放松大脑"},
        {"time": "22:30", "task": "🌙 休息", "detail": "保证充足睡眠"},
    ]

    print("\n⏰ 【时间表】\n")
    for item in schedule:
        print("  {} │ {}".format(item["time"], item["task"]))
        print("  {} │   └ {}".format(" " * len(item["time"]), item["detail"]))

    print("\n📝 【今日目标清单】\n")
    goals = [
        "完成「{}」核心知识点学习".format(content),
        "做至少20道相关练习题",
        "整理3-5个易错点",
        "写200字学习总结",
        "预习明天的内容大纲",
    ]
    for i, g in enumerate(goals, 1):
        print("  ☐ {}. {}".format(i, g))

def review(args):
    if not args:
        print("[错误] 用法: study.sh review \"已学内容\"")
        sys.exit(1)

    content = args[0]
    today = datetime.now()

    # 艾宾浩斯遗忘曲线间隔（天）
    intervals = [1, 2, 4, 7, 15, 30]
    retention = [58, 44, 36, 31, 25, 21]  # 对应遗忘后的大致记忆保持率(%)

    print("=" * 60)
    print("  🧠 艾宾浩斯复习安排")
    print("  📖 复习内容：{}".format(content))
    print("  📅 学习日期：{}".format(today.strftime("%Y-%m-%d")))
    print("=" * 60)

    print("\n📊 【遗忘曲线原理】\n")
    print("  德国心理学家艾宾浩斯发现，遗忘在学习后立即开始，")
    print("  且先快后慢。通过科学的间隔复习，可以有效对抗遗忘。\n")
    print("  遗忘规律：")
    print("  ├─ 20分钟后 → 记忆保持 58%")
    print("  ├─ 1小时后  → 记忆保持 44%")
    print("  ├─ 1天后    → 记忆保持 36%")
    print("  ├─ 6天后    → 记忆保持 25%")
    print("  └─ 1个月后  → 记忆保持 21%")

    print("\n📅 【复习时间表】\n")
    print("  {:>4}   {:>12}   {:>8}   {}".format("轮次", "复习日期", "间隔", "复习要求"))
    print("  " + "-" * 55)

    review_methods = [
        "快速浏览笔记，重点回忆关键概念",
        "不看笔记尝试回忆，标记遗忘部分",
        "只复习遗忘部分，做变式练习题",
        "整体回顾，尝试给别人讲解",
        "快速检测，关注仍有遗忘的部分",
        "最终巩固，确认长期记忆形成",
    ]

    for i, (interval, method) in enumerate(zip(intervals, review_methods)):
        review_date = today + timedelta(days=interval)
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][review_date.weekday()]
        print("  第{}轮   {} {}   {}天后    {}".format(
            i + 1,
            review_date.strftime("%Y-%m-%d"),
            weekday,
            interval,
            method
        ))

    print("\n💡 【复习技巧】\n")
    tips = [
        "主动回忆 > 被动阅读：先合上书试着回忆，再对照检查",
        "间隔重复 > 集中复习：分散到多天比一次突击更有效",
        "理解记忆 > 死记硬背：用自己的话复述知识点",
        "教学相长：尝试把学到的内容教给别人",
        "多感官结合：读出来、写出来、画思维导图",
    ]
    for i, tip in enumerate(tips, 1):
        print("  {}. {}".format(i, tip))

def pomodoro(args):
    if not args:
        print("[错误] 用法: study.sh pomodoro \"学习内容\" [--rounds 4]")
        sys.exit(1)

    content = args[0]
    rounds = 4
    for i, a in enumerate(args):
        if a == "--rounds" and i + 1 < len(args):
            try:
                rounds = int(args[i + 1])
            except ValueError:
                pass

    print("=" * 60)
    print("  🍅 番茄钟学习安排")
    print("  📖 学习内容：{}".format(content))
    print("  🔄 计划轮次：{} 轮".format(rounds))
    print("=" * 60)

    print("\n📋 【番茄钟规则】\n")
    print("  • 每个番茄钟 = 25分钟专注学习")
    print("  • 短休息 = 5分钟（每个番茄钟后）")
    print("  • 长休息 = 15-20分钟（每4个番茄钟后）")
    print("  • 专注期间：关闭手机通知，不看社交媒体")

    print("\n⏰ 【今日安排】\n")

    now = datetime.now().replace(second=0, microsecond=0)
    current = now
    total_focus = 0

    for r in range(1, rounds + 1):
        focus_end = current + timedelta(minutes=25)
        print("  🍅 第{}个番茄钟".format(r))
        print("  │  ⏰ {} → {} (25分钟)".format(
            current.strftime("%H:%M"), focus_end.strftime("%H:%M")))

        # 每轮不同的任务建议
        if r == 1:
            task = "回顾上次学习内容，明确今日目标"
        elif r == rounds:
            task = "总结归纳，整理笔记，标记疑问"
        elif r % 2 == 0:
            task = "做练习题，加深理解"
        else:
            task = "学习新知识点，做标记笔记"

        print("  │  📝 建议任务：{}".format(task))

        current = focus_end

        if r < rounds:
            if r % 4 == 0:
                rest_time = 20
                rest_type = "☕ 长休息"
                rest_tip = "站起来走动，吃点零食，远眺放松"
            else:
                rest_time = 5
                rest_type = "💤 短休息"
                rest_tip = "闭眼休息，深呼吸，喝口水"

            rest_end = current + timedelta(minutes=rest_time)
            print("  │  {} {} → {} ({}分钟) — {}".format(
                rest_type,
                current.strftime("%H:%M"),
                rest_end.strftime("%H:%M"),
                rest_time, rest_tip))
            current = rest_end

        print("  │")
        total_focus += 25

    total_time = (current - now).seconds // 60
    print("  └─ 完成！\n")
    print("  📊 统计：")
    print("     • 总专注时间：{}分钟（{:.1f}小时）".format(total_focus, total_focus / 60.0))
    print("     • 总用时（含休息）：约{}分钟（{:.1f}小时）".format(total_time, total_time / 60.0))
    print("     • 完成番茄钟：{}个 🍅".format(rounds))

    print("\n💡 【注意事项】\n")
    print("  • 如果25分钟内走神了，重新开始这个番茄钟")
    print("  • 休息时间一定要真正休息，不要看手机")
    print("  • 记录每天完成的番茄钟数量，追踪进步")
    print("  • 找到自己的最佳番茄钟数量（通常4-8个/天）")

def main():
    args = sys.argv[1:]
    if not args:
        show_help()
        return

    cmd = args[0]
    rest = args[1:]

    commands = {
        "help": lambda _: show_help(),
        "plan": plan,
        "daily": daily,
        "review": review,
        "pomodoro": pomodoro,
    }

    func = commands.get(cmd)
    if func:
        func(rest)
    else:
        print("[错误] 未知命令: {}".format(cmd))
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
PYTHON_EOF

echo ""
echo "  Powered by BytesAgain | bytesagain.com | hello@bytesagain.com"
