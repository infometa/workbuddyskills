#!/usr/bin/env python3
"""
generate_roadmap.py — 根据学习目标、水平和时间生成结构化学习路线图。

用法:
    python generate_roadmap.py --goal "两周学会R语言" --level zero --hours 1 --total-days 14
    python generate_roadmap.py --interactive
    python generate_roadmap.py --json         # JSON 输出供程序消费

水平: zero（零基础）, beginner（有基础）, exam（考试冲刺）
风格: academic（学术）, practical（实战）, exam（考试）, auto（自动）
"""

import argparse, json, sys, math
from datetime import datetime

# ── 阶段模板（通用） ──
PHASE_TEMPLATES = {
    "academic": {
        "name": ["基础概念", "核心知识", "进阶应用", "综合巩固"],
        "desc": ["环境搭建与基础概念理解", "掌握核心数据结构与操作", "目标领域关键能力训练", "综合项目与查漏补缺"],
    },
    "practical": {
        "name": ["环境搭建", "最小可用", "功能完善", "打磨发布"],
        "desc": ["搭好环境，跑通第一段代码", "实现最小可用功能", "补全核心功能模块", "优化、测试、收尾"],
    },
    "exam": {
        "name": ["知识梳理", "专题强化", "真题模拟", "冲刺查漏"],
        "desc": ["拆解考纲，梳理知识体系", "按题型/模块专项突破", "限时套题训练", "错题回顾与心态调整"],
    },
}

DAILY_RHYTHMS = {
    "academic": "理论学习 30min → 动手练习 20min → 回顾总结 10min",
    "practical": "动手练习 30min → 查阅资料 15min → 应用到项目 15min",
    "exam":    "刷题 25min → 知识点复习 15min → 错题整理 20min",
}

# ── 学科卡点库 ──
PITFALLS = {
    "sql": [
        "JOIN 逻辑混淆 → 用 Venn 图理解 INNER / LEFT 集合差异后再写查询",
        "GROUP BY 使用错误 → 非聚合列必须在 GROUP BY 中声明",
        "窗口函数 OVER 语法陌生 → 从 ROW_NUMBER 开始，理解 PARTITION BY 作用后再拓展",
        "日期格式不统一导致查询异常 → 比较前用 DATE() 标准化",
        "手写 SQL 漏分号 → 养成写完立即补分号的习惯",
    ],
    "r": [
        "向量索引从 1 开始 → 和 Python/Java 习惯不同，写代码时多检查",
        "包安装失败 → 检查 R 版本兼容性，优先用 install.packages()",
        "dataframe 操作不熟 → 先记住 5 个 dplyr 动词：filter/select/mutate/summarise/arrange",
        "因子（factor）类型隐式转换 → 用到 factor 时先 str() 查看结构",
    ],
    "python": [
        "缩进报错 → 编辑器设置自动格式化（Black / autopep8）",
        "包管理混乱 → 每个项目用独立虚拟环境（venv / conda）",
        "可变对象陷阱 → 列表传参时用 copy() 避免意外修改",
    ],
    "javascript": [
        "this 指向混乱 → 优先用箭头函数或 class 语法，避开 function 声明中的 this",
        "异步理解困难 → 按 callback → Promise → async/await 顺序学习",
        "== 和 === 混淆 → 全程使用 ===，避免类型强制转换",
    ],
    "ml": [
        "过拟合不知道怎么办 → 先用验证集 + 早停 + Dropout 三板斧",
        "数学公式看不懂 → 先看可视化理解，再回看公式",
        "模型选型困难 → 从最简单模型开始（线性 → 树 → 神经网络）",
    ],
    "default": [
        "计划过载 → 每天学习时间控制在可用时间的 80% 以内",
        "学了就忘 → 每天花 10 分钟回顾前一天内容",
        "遇到难题卡住 → 设 15 分钟计时，超时就跳过先学后面的",
    ],
}

RESOURCES = {
    "sql": {
        "beginner": [
            ("教程", "SQLBolt", "交互式，零基础友好，带实时反馈"),
            ("练习", "SQLZoo", "闯关式练习，难度递进"),
        ],
        "intermediate": [
            ("题库", "LeetCode SQL 50", "高频面试题集，按难度筛选"),
            ("文档", "W3Schools SQL", "函式速查，覆盖面广"),
        ],
    },
    "r": {
        "beginner": [
            ("教程", "R for Data Science (Hadley Wickham)", "最经典的 R 数据科学入门书，免费在线版"),
            ("视频", "R Programming 101 (YouTube)", "适合零基础，每个视频 10-15 分钟"),
        ],
        "intermediate": [
            ("教程", "Advanced R (Hadley Wickham)", "理解 R 底层机制，适合进阶"),
            ("课程", "Coursera: Data Science Specialization (Johns Hopkins)", "系统学习 R 数据分析"),
        ],
    },
    "python": {
        "beginner": [
            ("教程", "Automate the Boring Stuff (Al Sweigart)", "实战驱动，适合零基础"),
            ("视频", "Python for Everybody (Coursera/YouTube)", "最受欢迎的 Python 入门课"),
        ],
        "intermediate": [
            ("教程", "Python Crash Course (Eric Matthes)", "快速回顾 + 项目实践"),
            ("文档", "Real Python 教程库", "覆盖 Python 全栈的中高级主题"),
        ],
    },
    "javascript": {
        "beginner": [
            ("教程", "JavaScript.info", "现代 JavaScript 教程，中英文都有"),
            ("课程", "FreeCodeCamp JavaScript 课程", "交互式学习，边学边练"),
        ],
        "intermediate": [
            ("教程", "You Don't Know JS (Kyle Simpson)", "深入理解 JavaScript 核心机制"),
            ("文档", "MDN Web Docs", "最权威的 JavaScript 参考文档"),
        ],
    },
    "default": {
        "beginner": [
            ("教程", "官方文档 / 入门教程", "最权威的来源，适合有一定基础的学习者"),
            ("视频", "YouTube / Bilibili 搜索相关教程", "可视化学习效率高"),
        ],
        "intermediate": [
            ("教程", "相关主题经典书籍", "系统化学习的最佳选择"),
            ("课程", "Coursera / edX / Udemy 相关课程", "结构化课程路径"),
        ],
    },
}

def detect_subject(goal: str):
    """从目标中识别学科关键词"""
    goal_lower = goal.lower()
    subjects = {
        "sql": ["sql", "数据库", "mysql", "postgresql", "clickhouse", "查询"],
        "r": ["r语言", "r 语言", " r ", "rstats", "rstudio", "数据分析 r"],
        "python": ["python", "py", "django", "flask"],
        "javascript": ["javascript", "js", "node", "react", "vue", "前端", "web前端"],
        "ml": ["机器学习", "深度学习", "ml", "ai", "人工智能", "神经网络", "pytorch", "tensorflow"],
    }
    for key, triggers in subjects.items():
        for t in triggers:
            if t in goal_lower:
                return key
    return "default"

def detect_route(goal: str, level: str):
    """自动选择学习路线风格"""
    goal_lower = goal.lower()
    if level == "exam":
        return "exam"
    exam_kw = ["考试", "考研", "模拟", "真题", "冲刺", "考证", "认证"]
    practical_kw = ["项目", "动手", "实战", "工作", "求职", "做出来", "找工作"]
    subject = detect_subject(goal)
    # 编程/数据分析语言默认走实战
    if subject in ("python", "r", "javascript", "sql"):
        return "practical"
    # 机器学习默认学术 + 实战混合
    if subject == "ml":
        return "academic"
    for k in exam_kw:
        if k in goal_lower: return "exam"
    for k in practical_kw:
        if k in goal_lower: return "practical"
    return "academic"

def detect_level(level_str: str):
    """标准化水平参数"""
    level_str = level_str.strip().lower()
    if level_str in ("zero", "0", "零基础", "完全不会", "新手", "0基础"):
        return "zero"
    if level_str in ("beginner", "有基础", "入门", "会一点", "学过"):
        return "beginner"
    if level_str in ("exam", "考试", "冲刺", "考前"):
        return "exam"
    return "zero"  # default

def estimate_hours_per_day(available: str) -> int:
    """从用户描述中估算每天可用学习小时数"""
    import re
    nums = re.findall(r"(\d+(?:\.\d+)?)", available)
    if nums:
        return int(float(nums[0]))
    return 1  # default

def estimate_total_days(time_str: str) -> int:
    """从时间约束中估算总天数"""
    import re
    time_lower = time_str.lower()
    # 月份
    m = re.search(r"(\d+)\s*个?月", time_lower)
    if m: return int(m.group(1)) * 30
    # 周
    m = re.search(r"(\d+)\s*周", time_lower)
    if m: return int(m.group(1)) * 7
    # 天
    m = re.search(r"(\d+)\s*天", time_lower)
    if m: return int(m.group(1))
    # 暑期、寒假、暑假
    if "暑" in time_lower or "寒" in time_lower or "假" in time_lower:
        return 60
    return 30  # default to 1 month

def generate_phases(total_days: int, route: str, subject: str, level: str):
    """生成阶段划分"""
    tmpl = PHASE_TEMPLATES[route]
    phases = []
    ratios = [0.15, 0.35, 0.35, 0.15]
    current = 1
    allocated = 0
    buffer_day = None

    for i in range(4):
        if i < 3:
            phase_days = max(1, round(total_days * ratios[i]))
        else:
            phase_days = total_days - allocated
        if phase_days <= 0:
            continue

        end = current + phase_days - 1
        if end > total_days:
            end = total_days

        has_buffer = (i < 2 and end < total_days)  # buffer after phase 1 and 2

        phases.append({
            "phase": i + 1,
            "title": tmpl["name"][i],
            "days": f"Day {current}–{min(end, total_days)}",
            "duration_days": phase_days,
            "focus": tmpl["desc"][i],
            "has_buffer": has_buffer,
        })

        if has_buffer:
            current = end + 2
            allocated += phase_days + 1  # +1 for buffer
        else:
            current = end + 1
            allocated += phase_days

    return phases

def generate_weekly(total_days: int, daily_hours: int, route: str, subject: str):
    """生成周计划（仅当 >7 天时）"""
    if total_days <= 7:
        return []
    weeks = math.ceil(total_days / 7)
    weekly = []
    topic_phases = [
        ["环境搭建", "核心概念", "基本操作"],
        ["数据结构", "核心 API", "基础练习"],
        ["进阶功能", "目标领域能力", "项目起步"],
        ["项目深化", "优化调试", "收尾整理"],
    ]
    for w in range(weeks):
        topics = topic_phases[w % len(topic_phases)]
        hours = min(daily_hours * 6, daily_hours * 7)
        weekly.append({
            "week": w + 1,
            "topics": topics,
            "hours": hours,
            "risk": "学习曲线较陡" if w == 0 else ("容易松懈" if w == weeks - 1 else "进度容易漂移"),
        })
    return weekly

def get_pitfalls(subject: str, level: str) -> list:
    """获取学科相关卡点"""
    base = PITFALLS.get(subject, PITFALLS["default"])
    if level in ("zero", "beginner"):
        return base[:3]
    return base

def get_resources(subject: str, level: str, route: str) -> list:
    """获取推荐资源"""
    subj = subject if subject in RESOURCES else "default"
    # 映射 level
    if level in ("zero",):
        lvl = "beginner"
    elif level in ("beginner",):
        lvl = "intermediate"
    else:
        lvl = "beginner"
    pool = RESOURCES[subj].get(lvl, RESOURCES["default"][lvl])
    return [{"type": t, "title": n, "reason": r} for t, n, r in pool[:3]]

def generate_roadmap(goal: str, level_str: str, time_constraint: str = "",
                     daily_hours: int = 0, total_days: int = 0,
                     route: str = "auto", full_weeks: bool = True):
    """生成完整学习路线图"""
    # 解析参数
    level = detect_level(level_str)
    subject = detect_subject(goal)
    if route == "auto":
        route = detect_route(goal, level)

    # 时间解析
    if total_days <= 0:
        total_days = estimate_total_days(time_constraint)
    if daily_hours <= 0:
        daily_hours = estimate_hours_per_day(time_constraint if time_constraint else "")
    if daily_hours <= 0:
        daily_hours = 1

    # 生成内容
    phases = generate_phases(total_days, route, subject, level)
    weekly = generate_weekly(total_days, daily_hours, route, subject) if full_weeks else []
    pitfalls = get_pitfalls(subject, level)
    resources = get_resources(subject, level, route)
    rhythm = DAILY_RHYTHMS.get(route, DAILY_RHYTHMS["academic"])

    # 压力检查
    weekly_hours = daily_hours * 6  # 留一天缓冲
    max_safe = daily_hours * 7 * 0.8
    overload = "High" if weekly_hours > max_safe * 1.2 else ("Medium" if weekly_hours > max_safe else "Low")

    # 阶段产出物
    milestones = []
    for p in phases:
        milestones.append(f"{p['days']}: {p['focus']}")

    return {
        "goal": goal,
        "level": level,
        "route": route,
        "subject": subject,
        "total_days": total_days,
        "daily_hours": daily_hours,
        "phases": phases,
        "weekly_plan": weekly,
        "milestones": milestones,
        "resources": resources,
        "pitfalls": pitfalls,
        "daily_rhythm": rhythm,
        "pressure_check": {
            "weekly_study_hours": weekly_hours,
            "max_safe_hours": round(max_safe, 1),
            "overload_risk": overload,
        },
    }

def generate_success_criteria(goal: str, subject: str, level: str, route: str) -> list:
    """生成成功标准（4 条）"""
    standards = {
        "sql": [
            "独立编写包含 JOIN / GROUP BY / 子查询的多表查询",
            "使用窗口函数完成排名和分组计算",
            "解 medium 级别的 LeetCode SQL 题",
            "完成一个可用于简历的 SQL 分析项目（如电商销售分析）",
        ],
        "r": [
            "使用 dplyr 完成数据清洗与变换",
            "用 ggplot2 创建基础可视化图表",
            "从 CSV/Excel 文件读取并分析结构化数据",
            "用 R Markdown 输出一份完整的数据分析报告",
        ],
        "python": [
            "编写包含条件/循环/函数的 Python 脚本",
            "使用 pandas 完成数据加载与基本处理",
            "读写 CSV/JSON 文件并提取所需信息",
            "完成一个可运行的命令行小工具或分析脚本",
        ],
        "javascript": [
            "使用 ES6 语法操作数组和对象",
            "用 fetch API 完成数据请求与展示",
            "构建一个简单的交互式页面",
            "理解 Promise / async-await 异步模式",
        ],
        "ml": [
            "使用 sklearn 完成分类/回归模型的训练与评估",
            "理解过拟合的含义并能使用正则化/早停解决",
            "用 PyTorch 或 TensorFlow 搭建简单神经网络",
            "完成一个端到端的 ML 项目（数据→模型→评估）",
        ],
    }
    base = [
        "独立编写多表 JOIN 查询",
        "使用 GROUP BY + 聚合函数完成分组分析",
        "解 medium 级别的 LeetCode 题",
        "完成一个可用于简历的完整项目",
    ]
    result = standards.get(subject, base)
    if level == "zero":
        result = result[:4]
    return result


def generate_adaptive_notes(goal: str, subject: str, route: str) -> list:
    """生成动态调整说明"""
    notes = [
        {"if": "目标方向为后端开发", "then": "增加索引优化、查询性能和数据库设计章节"},
        {"if": "目标方向为数据分析", "then": "优先聚合查询、窗口函数和看板式查询训练"},
        {"if": "每日学习时间不足 1 小时", "then": "路线延长至 5 周，每个阶段天数翻倍"},
        {"if": "已有编程基础", "then": "跳过基础阶段，直接从核心语法开始"},
        {"if": "目标为考证/认证", "then": "切换为考试路线，增加真题模拟比例"},
    ]
    # 根据场景裁剪
    if route == "exam":
        notes = [n for n in notes if "认证" not in n["if"]]
        notes.insert(0, {"if": "当前为考试路线", "then": "考点覆盖率优先于项目完整性"})
    if subject == "default":
        notes = notes[:3]
    return notes


def format_output(result: dict) -> str:
    """格式化为人类可读的文本输出"""
    r = result
    lines = []

    level_names = {"zero": "零基础", "beginner": "有基础", "exam": "考试冲刺"}
    route_names = {"academic": "学术路线", "practical": "实战路线", "exam": "考试路线"}
    subject_names = {"sql": "SQL 数据分析", "r": "R 数据分析", "python": "Python 基础", "javascript": "JavaScript 开发",
                     "ml": "机器学习", "default": "通用"}
    level_name = level_names.get(r["level"], r["level"])
    route_name = route_names.get(r["route"], r["route"])
    subject_name = subject_names.get(r["subject"], r["subject"])

    pace = "适中"
    if r["daily_hours"] >= 3:
        pace = "紧凑"
    elif r["daily_hours"] <= 1:
        pace = "宽松"

    buffer_count = sum(1 for p in r["phases"] if p.get("has_buffer"))
    success_criteria = generate_success_criteria(r["goal"], r["subject"], r["level"], r["route"])
    adaptive_notes = generate_adaptive_notes(r["goal"], r["subject"], r["route"])

    # Learner Profile
    lines.append("=" * 60)
    lines.append("  学习路线图 — " + r["goal"])
    lines.append("=" * 60)
    lines.append("")
    lines.append("  学习者画像")
    lines.append(f"  {'属性':<16} {'值'}")
    lines.append(f"  {'───':<16} {'───'}")
    lines.append(f"  {'当前水平':<16} {level_name}")
    lines.append(f"  {'学习目标':<16} {r['goal']}")
    lines.append(f"  {'目标技能':<16} {subject_name}")
    lines.append(f"  {'时间周期':<16} {r['total_days']} 天（含 {buffer_count} 个缓冲日）")
    lines.append(f"  {'每日投入':<16} {r['daily_hours']} 小时")
    lines.append(f"  {'推荐节奏':<16} {pace}")

    # Success Criteria
    lines.append("")
    lines.append("=" * 60)
    lines.append("  成功标准")
    lines.append("=" * 60)
    lines.append("  完成本路线图后，应能：")
    for sc in success_criteria:
        lines.append(f"  - {sc}")

    # Phases
    lines.append("")
    lines.append("=" * 60)
    lines.append("  阶段计划")
    lines.append("=" * 60)
    lines.append(f"  {'阶段':<6} {'时间':<14} {'主题':<26} {'里程碑'}")
    lines.append(f"  {'───':<6} {'────':<14} {'────':<26} {'────'}")
    for p in r["phases"]:
        focus = p["focus"][:24]
        lines.append(f"  {p['phase']:<6} {p['days']:<14} {focus:<26} {p['focus']}")
        if p.get("has_buffer"):
            lines.append(f"  {'':<6} {'缓冲':<14}")

    # Weekly plan
    if r["weekly_plan"]:
        lines.append("")
        lines.append("=" * 60)
        lines.append("  每周计划")
        lines.append("=" * 60)
        lines.append(f"  {'周次':<6} {'主题':<34} {'时长':<8} {'风险'}")
        lines.append(f"  {'───':<6} {'────':<34} {'────':<8} {'────'}")
        for w in r["weekly_plan"]:
            topics = " / ".join(w["topics"])[:32]
            lines.append(f"  {w['week']:<6} {topics:<34} {w['hours']}h{'':<5} {w['risk']}")

    # Resources (learning stack)
    if r["resources"]:
        lines.append("")
        lines.append("=" * 60)
        lines.append("  推荐学习栈")
        lines.append("=" * 60)
        lines.append(f"  {'用途':<20} {'资源'}")
        lines.append(f"  {'────':<20} {'────'}")
        purposes = ["交互式入门", "语法练习", "面试准备", "文档参考"]
        for i, res in enumerate(r["resources"]):
            purpose = purposes[i] if i < len(purposes) else "参考"
            lines.append(f"  {purpose:<20} {res['title']}")

    # Pitfalls
    milestones_for_ref = ""
    if r["pitfalls"]:
        lines.append("")
        lines.append("=" * 60)
        lines.append("  常见卡点")
        lines.append("=" * 60)
        for p in r["pitfalls"]:
            lines.append(f"  - {p}")

    # Adaptive Notes
    lines.append("")
    lines.append("=" * 60)
    lines.append("  动态调整说明")
    lines.append("=" * 60)
    for note in adaptive_notes:
        lines.append(f"  - 若{note['if']} → {note['then']}")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="生成结构化学习路线图")
    ap.add_argument("--goal", "-g", help="学习目标，如'两周学会R语言'")
    ap.add_argument("--level", "-l", help="当前水平: zero（零基础）/ beginner（有基础）/ exam（考试）")
    ap.add_argument("--time", "-t", help="时间约束描述，如'两周'、'每天1小时'")
    ap.add_argument("--daily-hours", type=int, default=0, help="每天可用小时数")
    ap.add_argument("--total-days", type=int, default=0, help="总天数")
    ap.add_argument("--route", "-r", default="auto", choices=["auto", "academic", "practical", "exam"],
                    help="学习路线风格")
    ap.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    ap.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    if args.interactive:
        print("=" * 60)
        print("  学习路线生成器")
        print("=" * 60)
        goal = input("  学习目标（如'两周学会R语言'）: ").strip()
        level = input("  当前水平（zero/beginner/exam）: ").strip() or "zero"
        time_str = input("  时间约束（如'两周，每天1小时'）: ").strip() or ""
        result = generate_roadmap(goal, level, time_str)
    elif args.goal:
        result = generate_roadmap(
            args.goal, args.level or "zero",
            args.time or "",
            args.daily_hours, args.total_days,
            args.route,
        )
    else:
        ap.print_help()
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_output(result))


if __name__ == "__main__":
    main()
