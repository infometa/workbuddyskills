#!/usr/bin/env python3
"""
init_plan.py - 初始化新学习计划

用法：
  python3 init_plan.py <计划名称> <截止日期> [--days N] [--template TEMPLATE] [--granularity GRAN]

示例：
  python3 init_plan.py 雅思65 2026-06-15 --template ielts-toefl --days 30
  python3 init_plan.py 考研 2026-12-20 --granularity hourly   # 按小时排程
  python3 init_plan.py 期末突击 2026-05-20 --granularity minutely  # 按分钟（番茄钟）

时间精度选项（--granularity）：
  monthly   - 按月视图，适合 ≥6 个月长期计划
  daily     - 按天（默认），适合 1-6 个月
  hourly    - 按小时排程，适合 1-4 周冲刺
  minutely  - 按分钟（番茄钟 25+5），适合 ≤1 周精细规划

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime, uuid）
  - 零网络调用、零三方包、零遥测
  - 模板文件位于 ../references/templates/<template>.json

输入：
  - argv[1] 计划名称（中文/英文，1-30 字符）
  - argv[2] 截止日期（YYYY-MM-DD，必须 ≥ 今日）
  - --days N 计划总长度（1-365，默认按截止日推算）
  - --template TEMPLATE 模板名（ielts-toefl/kaoyan/...，默认 _custom-blank）

输出：
  - <cwd>/study-planner/study-plans/<plan-id>/plan.json (schema v1.1)
  - 字段：meta + daily_tasks[]，符合下游打卡消费契约

性能上限：
  - 365 天计划生成 < 200ms（仅文件 IO，无网络）
  - 内存占用 < 10MB

错误模式（exit code）：
  - 0  成功
  - 1  截止日期早于今日 / 格式错误 → 提示用户重新输入
  - 2  模板不存在 → 列出可用模板
  - 3  目标目录已存在同名 plan-id → 自动追加 -v2 后缀重试
  - 4  写入失败（磁盘满 / 权限） → 中止并打印路径
  - 5  日均任务总时长超 daily_budget × 2 → 强制退出（NEVER 2 hard-stop）
"""

import json
import os
import sys
import re
import uuid
from datetime import datetime, timedelta


def _resolve_data_dir() -> str:
    """数据目录解析。优先级：STUDY_PLANNER_DATA_DIR env > <cwd>/study-planner/study-plans/"""
    env = os.environ.get("STUDY_PLANNER_DATA_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.abspath(os.path.join(os.getcwd(), "study-planner", "study-plans"))


DATA_DIR = _resolve_data_dir()


def _ensure_gitignore() -> None:
    """首次落盘时，在 cwd/.gitignore 自动追加 /study-planner/ 忽略规则（如未存在）。

    注意：使用根锚定的 `/study-planner/`，只忽略仓库根目录下的运行时数据目录，
    避免误伤项目中其他嵌套位置同名目录（例如 playbook case、文档资源等）。
    """
    gi_path = os.path.join(os.getcwd(), ".gitignore")
    rule = "/study-planner/"
    legacy_rule = "study-planner/"  # 旧版无锚定规则，保留兼容判断
    try:
        if os.path.exists(gi_path):
            with open(gi_path, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.splitlines()
            # 如果新规则已存在，或旧规则已存在（视作已忽略，不重复追加），直接返回
            if rule in lines or legacy_rule in lines:
                return
            sep = "" if content.endswith("\n") or not content else "\n"
            with open(gi_path, "a", encoding="utf-8") as f:
                f.write(f"{sep}\n# study-planner skill 个人学习数据（含计划/打卡，避免 commit）\n{rule}\n")
        else:
            with open(gi_path, "w", encoding="utf-8") as f:
                f.write(f"# study-planner skill 个人学习数据（含计划/打卡，避免 commit）\n{rule}\n")
    except OSError:
        # 写不进 .gitignore 不阻塞主流程（用户可能在只读目录或系统目录跑脚本）
        pass

# 模板目录寻址策略（按优先级尝试）：
#   1. 环境变量 STUDY_PLANNER_TEMPLATE_DIR（测试 / 自定义安装）
#   2. __file__ 相对路径（仓库直跑 / skill 安装在仓库内）
def _resolve_template_dir() -> str:
    env_dir = os.environ.get("STUDY_PLANNER_TEMPLATE_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    here = os.path.dirname(os.path.abspath(__file__))
    rel = os.path.normpath(os.path.join(here, "..", "references", "templates"))
    return rel


TEMPLATE_DIR = _resolve_template_dir()

# 计划跨度硬上限（产品规格：≤ 12 个月 ≈ 365 天）
MAX_PLAN_DAYS = 365

# NEVER 4：任意单任务 duration_min 上限（pomodoro 友好）
MAX_TASK_MIN = 45
# 默认每日骨架任务数（AI 后续可补全/替换；保证 init 后下游打卡流程能立即开干）
DEFAULT_TASKS_PER_DAY = 3
# Methodology tip 池：随 category 轮换，保证 NEVER 7 不出现空字段
METHOD_TIPS = {
    "listening": "艾宾浩斯：今日精听段落，第 1/3/7 天各重听一次（不看原文）",
    "reading":   "帕累托：先做高频题型（判断/填空），把 80% 时间花在 20% 高频考点上",
    "writing":   "费曼法：写完读给自己听，能 5 分钟讲明白论点再交卷",
    "speaking":  "费曼法：录音回放，标记卡顿点，用更简单的词替换",
    "vocabulary":"艾宾浩斯：当日 + 1/3/7/15 天复现，5 次后进入长期记忆",
    "grammar":   "番茄：单次专注 ≤45min，错题立刻造 3 个新例句",
    "review":    "艾宾浩斯：本周错题第 1/3/7 天复现，能 1 分钟讲明白才算过",
    "exam":      "限时模考：严格计时，做完立即对答案，错题 24h 内复盘",
    "output":    "费曼法：不写就不算学过——产出可以是文章/代码/讲解视频",
    "rest":      "主动休息：散步/远眺/换脑，禁止刷短视频（剥夺反而加重疲劳）",
    # —— 编程/技能学习类 ——
    "coding":    "番茄 + Rubber Duck：写代码 25min 后口头讲一遍逻辑给\"小黄鸭\"听",
    "debug":     "费曼法：先把 bug 现象 + 已排除的可能用一句话讲清，再上手改代码",
    "algorithm": "费曼 + 重做：题解看懂后合上，自己重写一遍能跑过才算掌握",
    "deploy":    "checklist：环境变量 / 域名 / 数据库 / CI 一项一项过，避免凭印象部署",
    "testing":   "TDD：先写一条会失败的测试，再补实现让它变绿，最后重构",
    "weak_focus":"NEVER 6：弱项 +50% 时长，强项 -30%——这条任务就是为你的弱项专门加的",
}


def slugify(text: str) -> str:
    """将中文转成 URL-safe slug"""
    # 保留中文，替换空格和特殊字符
    text = re.sub(r'[^\w\u4e00-\u9fff-]', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text.lower()


def load_template(template_id: str) -> dict:
    """加载模板"""
    path = os.path.join(TEMPLATE_DIR, f"{template_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"模板不存在: {template_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _split_duration(total: int, max_each: int = MAX_TASK_MIN) -> list:
    """把 total 分钟拆成每段 ≤ max_each（NEVER 4）。
    返回拆分后的分钟数组，例如 split(180) -> [45,45,45,45]，split(50) -> [45,5]。
    余数 < 5 时合并到上一段，避免出现过短碎片。
    """
    if total <= max_each:
        return [total]
    chunks = []
    remaining = total
    while remaining > max_each:
        chunks.append(max_each)
        remaining -= max_each
    if remaining < 5 and chunks:
        chunks[-1] += remaining
    elif remaining > 0:
        chunks.append(remaining)
    return chunks


def _make_task(task_id: str, title: str, duration: int, category: str,
               priority: str = "medium", resource: str = "", tip: str = "") -> dict:
    """构建符合 schema v1 + 下游打卡契约的 task 对象。
    必须包含 checkable（硬契约：渲染复选框依赖）+ methodology_tip（NEVER 7）。
    """
    task = {
        "id": task_id,
        "title": title,
        "duration_min": duration,
        "category": category,
        "priority": priority,
        "checkable": True,  # 下游打卡渲染 [ ] 复选框依赖此字段
        "methodology_tip": tip or METHOD_TIPS.get(category, "番茄：专注 ≤45min，结束后强制起身 5 min"),
    }
    if resource:
        task["resource"] = resource
    return task


def _build_stages(template: dict, total_days: int) -> list:
    """按模板的 phase_templates 拆出 stages，duration 总和 == total_days。"""
    phases = template.get("phase_templates", [])
    if not phases:
        # 兜底：单阶段
        return [{
            "id": "stage-1",
            "name": "学习冲刺",
            "duration_days": total_days,
            "goals": ["按计划完成每日任务，保持每日打卡"],
        }]

    stages = []
    consumed = 0
    for i, phase in enumerate(phases, 1):
        ratio = phase.get("duration_ratio", 1.0 / len(phases))
        # 末段把余数全收走，避免 round 累计偏差
        if i == len(phases):
            days = total_days - consumed
        else:
            days = max(1, round(total_days * ratio))
        consumed += days
        stages.append({
            "id": f"stage-{i}",
            "name": phase.get("name", f"阶段 {i}"),
            "duration_days": days,
            "goals": [phase.get("description", f"完成 {phase.get('name', '本阶段')}")] +
                     [f"参考方法论：{template.get('methodology_injection', {}).get('description', '艾宾浩斯+番茄+费曼')}"],
        })
    return stages


_WEEKDAY_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _build_daily_tasks(template: dict, stages: list, start_date: datetime,
                       total_days: int, daily_budget: dict,
                       time_granularity: str = "daily",
                       weak_points: list = None) -> list:
    """按模板 weekly_pattern 填充每日骨架任务。
    保证：
    - 每天 1~DEFAULT_TASKS_PER_DAY（+1 弹性）条任务
    - 每条 duration_min ≤ MAX_TASK_MIN（NEVER 4）
    - 必带 checkable + methodology_tip
    - 任务总时长尽量贴近 daily_budget（工作日/周末区分）
      P1-2 修复：余 ≥ 20 min 时新增「自由练习/弱项加练」任务，避免周末浪费 25% 预算
    - time_granularity == "hourly"/"minutely" 时，为任务分配 start_hour / start_minute
    """
    # 根据时间粒度决定任务分配的起始小时
    # 简单策略：从 9:00 开始，按任务时长顺序排
    _START_HOUR_DEFAULT = 9  # 默认从早上 9 点开始排
    daily_tasks = []
    task_counter = 0
    phases = template.get("phase_templates", [])

    # 建立 stage_id -> phase 的映射
    stage_to_phase = {}
    cursor = 0
    for stage in stages:
        # 找到对应 phase（按顺序匹配）
        idx = int(stage["id"].split("-")[1]) - 1
        if idx < len(phases):
            stage_to_phase[stage["id"]] = phases[idx]
        cursor += stage["duration_days"]

    # 当前 stage 指针
    cur_stage_idx = 0
    cur_stage_consumed = 0

    for day_offset in range(total_days):
        cur_date = start_date + timedelta(days=day_offset)
        cur_stage = stages[cur_stage_idx]

        # 推进 stage 指针
        if cur_stage_consumed >= cur_stage["duration_days"] and cur_stage_idx < len(stages) - 1:
            cur_stage_idx += 1
            cur_stage = stages[cur_stage_idx]
            cur_stage_consumed = 0
        cur_stage_consumed += 1

        # 抓取本 phase 的本周日模板
        phase = stage_to_phase.get(cur_stage["id"], {})
        weekly = phase.get("weekly_pattern", [])
        weekday_key = _WEEKDAY_KEYS[cur_date.weekday()]
        is_weekend = cur_date.weekday() >= 5
        budget = daily_budget["weekend"] if is_weekend else daily_budget["weekday"]

        # 找到该星期的任务标题列表
        titles = []
        for entry in weekly:
            if entry.get("day") == weekday_key:
                titles = entry.get("tasks", [])
                break

        # 没匹配上就用一个通用复习骨架
        if not titles:
            titles = ["每日复盘 + 错题回顾", "薄弱项专项 30 min", "睡前复现今日重点"]

        # 限制每日任务数
        titles = titles[:DEFAULT_TASKS_PER_DAY]
        base_n = len(titles)
        per_task_budget = max(20, min(MAX_TASK_MIN, budget // max(1, base_n)))

        # P1-2 修复（v2）：余数补回。若按 per_task_budget × N 仍低于 budget（≥ 20 min 缺口），
        # 追加 ≥1 条「薄弱项加练 / 自由练习」消化缺口，每条上限 MAX_TASK_MIN。
        # 例：周六 budget=180、base_n=2、per_task=45 时，gap=90 → 追加 2 条 filler；
        #     周五 budget=90、base_n=3、per_task=30 时，gap=0 → 不追加。
        # 总任务数硬上限 DEFAULT_TASKS_PER_DAY + 2（避免被极端模板灌爆）。
        used = per_task_budget * base_n
        gap = budget - used
        filler_durations = []  # 每条 filler 的 duration（按需拆 ≤ MAX_TASK_MIN）
        max_extra = max(0, (DEFAULT_TASKS_PER_DAY + 2) - base_n)
        if gap >= 20 and max_extra > 0:
            remaining = gap
            while remaining >= 20 and len(filler_durations) < max_extra:
                take = min(MAX_TASK_MIN, remaining)
                filler_durations.append(take)
                remaining -= take

        filler_title_default = "薄弱项加练" if (weak_points and len(weak_points) > 0) else "自由练习 / 弹性时段"
        # 多条 filler 时按弱点轮询：避免同一天连续 2 条「薄弱项加练 / 薄弱项加练 #2」（用户摸不到练什么）
        # 轮询 key: (day_offset, fi) → 命中 weak_points[(day_offset * 2 + fi) % len(wp)]
        filler_titles_today = []
        for fi in range(len(filler_durations)):
            if weak_points and len(weak_points) > 0:
                wp = str(weak_points[(day_offset * 2 + fi) % len(weak_points)])
                filler_titles_today.append(f"{wp} 加练")
            else:
                filler_titles_today.append(
                    filler_title_default if fi == 0 else f"{filler_title_default} #{fi + 1}"
                )
        for t in filler_titles_today:
            titles = list(titles) + [t]
        added_filler_n = len(filler_durations)

        tasks = []
        current_hour = _START_HOUR_DEFAULT
        current_minute = 0
        for ti, title in enumerate(titles):
            task_counter += 1
            category = _infer_category(title, weak_points)
            # 后 N 条是 filler，独立持有自己的 duration；其它沿用 per_task_budget
            this_dur = per_task_budget
            if added_filler_n > 0 and ti >= len(titles) - added_filler_n:
                fi = ti - (len(titles) - added_filler_n)
                this_dur = filler_durations[fi]
            chunks = _split_duration(this_dur)
            # 多数情况只产出 1 段（per_task_budget ≤ 45），但保留拆分逻辑统一性
            for j, dur in enumerate(chunks):
                suffix = f" (part {j+1}/{len(chunks)})" if len(chunks) > 1 else ""
                task = _make_task(
                    task_id=f"t-{task_counter:03d}" if j == 0 else f"t-{task_counter:03d}-p{j+1}",
                    title=f"{title}{suffix}",
                    duration=dur,
                    category=category,
                    priority="high" if category in ("writing", "speaking", "exam") else "medium",
                )
                # 根据时间粒度补充字段
                if time_granularity in ("hourly", "minutely"):
                    task["start_hour"] = current_hour
                    if time_granularity == "minutely":
                        task["start_minute"] = current_minute
                        task["pomodoro_split"] = True
                    # 简单排程：按任务时长推进时间
                    current_minute += dur
                    while current_minute >= 60:
                        current_minute -= 60
                        current_hour += 1
                    # 超过 22 点或不在 9-22 区间，回到次日 9 点
                    if current_hour >= 22:
                        current_hour = _START_HOUR_DEFAULT
                        current_minute = 0
                tasks.append(task)

        daily_tasks.append({
            "date": cur_date.strftime("%Y-%m-%d"),
            "stage_id": cur_stage["id"],
            "tasks": tasks,
        })

    return daily_tasks


# 类别推断关键词表（按优先级从上到下扫描，首中即返）
# 注意：更具体的领域词（编程/部署/测试）放在通用「项目/产出」之前，避免被兜底吞掉
_CATEGORY_HINTS = [
    # —— 英语备考 ——
    ("听力", "listening"), ("精听", "listening"),
    ("阅读", "reading"),
    ("写作", "writing"), ("作文", "writing"),
    ("口语", "speaking"),
    ("词汇", "vocabulary"), ("单词", "vocabulary"),
    ("语法", "grammar"),
    ("模考", "exam"), ("套题", "exam"), ("限时", "exam"),
    # —— 编程/技能学习（领域词，优先于通用「项目/产出」）——
    ("调试", "debug"), ("debug", "debug"), ("BUG", "debug"), ("bug", "debug"),
    ("算法", "algorithm"), ("leetcode", "algorithm"), ("LeetCode", "algorithm"),
    ("数据结构", "algorithm"),
    ("部署", "deploy"), ("上线", "deploy"), ("发布", "deploy"),
    ("vercel", "deploy"), ("Vercel", "deploy"), ("CI", "deploy"),
    ("测试", "testing"), ("单元测试", "testing"), ("e2e", "testing"),
    ("敲示例代码", "coding"), ("写代码", "coding"), ("写 ", "coding"),
    ("代码 review", "coding"), ("阶段性提交", "coding"), ("阶段代码", "coding"),
    ("GitHub 提交", "coding"), ("看视频", "coding"), ("教程章节", "coding"),
    ("教程 ", "coding"), ("官方文档", "coding"), ("最佳实践", "coding"),
    ("项目设计", "coding"), ("技术调研", "coding"), ("源码", "coding"),
    ("UI", "coding"), ("UX", "coding"), ("性能优化", "coding"),
    # 常见前端/全栈概念词（用于「<弱点> 加练」时命中具体 coding 类别）
    ("Hooks", "coding"), ("hooks", "coding"), ("心智模型", "coding"),
    ("泛型", "coding"), ("Server Components", "coding"),
    ("React", "coding"), ("Vue", "coding"), ("Angular", "coding"),
    ("TypeScript", "coding"), ("Python", "coding"), ("Go", "coding"),
    # —— 复盘/输出/休息 ——
    ("复盘", "review"), ("错题", "review"), ("回顾", "review"),
    ("项目实战", "output"), ("项目实践", "output"), ("项目", "output"),
    ("产出", "output"), ("文章", "output"), ("博客", "output"),
    ("分享", "output"), ("README", "output"), ("文档撰写", "output"),
    ("休息", "rest"), ("早睡", "rest"),
]


def _infer_category(title: str, weak_points: list = None) -> str:
    """根据任务标题推断 category（用于模板未显式标注的情况）。

    P1-5 修复：先用 weak_points 做二次推断
      - "薄弱项专项 X" / "弱项加练 X" 这类任务，按 X 命中的关键词归类
        （X = "听力 Section 4" → listening；X = "Hooks" → coding）
      - 没有 weak_points 或没命中，再走 _CATEGORY_HINTS
    """
    # 1) 弱项相关任务先按 title 中夹带的弱点短语反查
    is_weak_task = (
        "薄弱项" in title or "弱项" in title or "weak" in title.lower()
        or title.endswith(" 加练") or title.endswith("加练")
    )
    if weak_points and is_weak_task:
        # 优先：用 title 自身（去掉"加练"后缀）反查关键词
        title_clean = re.sub(r"\s*加练\s*$", "", title)
        for kw, cat in _CATEGORY_HINTS:
            if kw.lower() in title_clean.lower():
                return cat
        # 次选：用 weak_points 列表反查
        for wp in weak_points:
            wp_low = str(wp).lower()
            for kw, cat in _CATEGORY_HINTS:
                if kw.lower() in wp_low:
                    return cat
        # 弱项任务但没命中具体类别 → 显式归 weak_focus，不再误归 review
        return "weak_focus"

    # 2) 常规标题扫描
    for kw, cat in _CATEGORY_HINTS:
        if kw in title:
            return cat
    return "review"


# ──────────────────────────────────────────────
# Materials 解析：从 .txt / .md 大纲文本抽取 weak_points
#
# 设计取舍：
#   - 不依赖 PDF 解析（pypdf/pdfplumber 跨平台麻烦，留给 v1.1）
#   - 只接受 .txt / .md / .markdown，零三方包
#   - 抽取规则（按优先级）：
#       1. Markdown 标题：以 #/##/### 开头的行
#       2. 列表项：以 - / * / 1. 等开头的行
#       3. 「薄弱/不会/搞不懂/差/弱」等关键词标注的整行
#   - 截取 top-N，写入 meta.weak_points；不替换模板任务，仅作为辅助上下文
#     （如需把它们注入 daily_tasks，由 AI 后续 add-task 决定）
# ──────────────────────────────────────────────
_WEAK_KEYWORDS = ["薄弱", "不会", "搞不懂", "搞不清", "不熟", "差", "弱项", "弱", "盲区", "weak", "TODO"]
_MAX_WEAK_POINTS = 20

# 文件大小硬上限：1MB（大纲文本不应超过这个量；防止误传巨大文件）
_MAX_MATERIALS_BYTES = 1 * 1024 * 1024


def parse_materials(file_path: str) -> list:
    """从大纲文本抽取 weak_points 候选列表（最多 _MAX_WEAK_POINTS 条）。

    Args:
        file_path: 文件路径，必须以 .txt / .md / .markdown 结尾

    Returns:
        weak_points 字符串列表（去重、保序）

    Raises:
        ValueError: 文件不存在 / 格式不支持 / 过大
    """
    if not file_path:
        return []
    if not os.path.isfile(file_path):
        raise ValueError(f"materials 文件不存在: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".txt", ".md", ".markdown"):
        raise ValueError(
            f"materials 仅支持 .txt / .md / .markdown（当前 {ext or '无后缀'}）。"
            f"PDF / DOCX 解析将在 v1.1 支持，目前请手动转成纯文本大纲。"
        )

    size = os.path.getsize(file_path)
    if size > _MAX_MATERIALS_BYTES:
        raise ValueError(f"materials 文件过大（{size} 字节，上限 {_MAX_MATERIALS_BYTES}）")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    candidates = []  # 保序去重
    seen = set()

    def _add(item: str):
        item = item.strip()
        if not item or len(item) > 80:  # 过长的行通常是段落正文，不是知识点
            return
        if item in seen:
            return
        seen.add(item)
        candidates.append(item)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # 规则 1：Markdown 标题
        if line.startswith("#"):
            stripped = line.lstrip("#").strip()
            if stripped:
                _add(stripped)
            continue

        # 规则 2：列表项（- / * / + / 1. / 1)）
        stripped_list = re.sub(r"^[-*+]\s+", "", line)
        stripped_list = re.sub(r"^\d+[.)]\s+", "", stripped_list)
        if stripped_list != line:
            _add(stripped_list)
            continue

        # 规则 3：含薄弱关键词的整行
        for kw in _WEAK_KEYWORDS:
            if kw in line:
                # 去掉行首符号
                cleaned = re.sub(r"^[\s\-*•·]+", "", line)
                _add(cleaned)
                break

    # 优先级排序：含 weak 关键词的排在前面
    def _priority(item: str) -> int:
        for kw in _WEAK_KEYWORDS:
            if kw in item:
                return 0
        return 1

    candidates.sort(key=_priority)
    return candidates[:_MAX_WEAK_POINTS]


_VALID_GRANULARITIES = ("monthly", "daily", "hourly", "minutely")


# ──────────────────────────────────────────────
# 语义 Token 注入（P1-1 修复）
#
# 问题背景：
#   skill-learning 等通用模板的 weekly_pattern 是骨架词
#   （"教程 1 章 / 小练习 1 个 / 概念笔记 / 对比相似概念"），
#   对用户具体技术栈（React / TypeScript / Prisma 等）零感知。
#   60 天 120 个任务里没有一条 title 提到具体关键词。
#
# 设计取舍：
#   - 后处理而非改模板：模板保持通用，注入逻辑独立可关停
#   - 白名单替换：只对"教程/章/练习/笔记/概念/项目/视频/文档"等
#     骨架词做改写；title 已含具体专有名词的不动
#   - 按 (phase, week_idx, slot_idx) 轮换 token，避免同周重复
#   - 短语级抽取：weak_points 整条作为短语（"TypeScript 泛型"）
#     而非拆词，保留语义；goal 抽英文专有名词 + 中文术语
#   - 零三方包：纯正则
# ──────────────────────────────────────────────

# 骨架词白名单：title 包含其中之一才考虑改写
# 顺序：更具体的 pattern 在前，避免被通用 pattern 抢先命中
_SKELETON_PATTERNS = [
    # phase 1
    (re.compile(r"官方教程\s*(\d+)?\s*章"), "{token} 官方教程章节"),
    (re.compile(r"教程\s*(\d+)?\s*章"), "{token} 教程章节"),
    (re.compile(r"动手敲示例代码"), "动手敲 {token} 示例代码"),
    (re.compile(r"看视频补充"), "看 {token} 视频补充"),
    (re.compile(r"官方文档对照"), "对照 {token} 官方文档"),
    (re.compile(r"综合小?练习"), "{token} 综合练习"),
    (re.compile(r"小?练习\s*\d*\s*个?"), "{token} 小练习"),
    (re.compile(r"概念笔记"), "{token} 概念笔记"),
    (re.compile(r"对比相似概念"), "{token} 与相邻概念对比"),
    (re.compile(r"本周笔记整理"), "本周 {token} 笔记整理"),
    (re.compile(r"完成入门级小项目"), "完成 {token} 入门级小项目"),
    (re.compile(r"GitHub\s*提交"), "{token} 阶段代码 GitHub 提交"),
    (re.compile(r"艾宾浩斯复现"), "{token} 艾宾浩斯复现"),
    (re.compile(r"费曼法讲解给自己听|费曼法讲解"), "用费曼法讲清 {token}"),
    # phase 2
    (re.compile(r"项目设计\s*/?\s*拆解\s*epic"), "{token} 项目设计 / 拆解 epic"),
    (re.compile(r"项目设计"), "{token} 项目设计"),
    (re.compile(r"技术调研"), "{token} 技术调研"),
    (re.compile(r"写代码\s*\d*h?"), "写 {token} 代码 1h"),
    (re.compile(r"遇到问题记录"), "{token} 遇到问题记录"),
    (re.compile(r"查阅最佳实践"), "查阅 {token} 最佳实践"),
    (re.compile(r"重构\s*/?\s*优化"), "{token} 重构 / 优化"),
    (re.compile(r"阶段性提交"), "{token} 阶段性提交"),
    (re.compile(r"代码\s*review"), "{token} 代码 review"),
    (re.compile(r"看优秀开源项目源码"), "看 {token} 优秀开源项目源码"),
    (re.compile(r"对比改进"), "{token} 对比改进"),
    (re.compile(r"写技术博客\s*\d*\s*篇?\s*/?\s*复盘"), "写 {token} 技术博客 1 篇 / 复盘"),
    (re.compile(r"下周规划"), "下周 {token} 规划"),
    # phase 3
    (re.compile(r"完善项目核心功能"), "完善 {token} 核心功能"),
    (re.compile(r"^测试$"), "{token} 测试"),
    (re.compile(r"UI\s*/?\s*UX\s*打磨"), "{token} UI/UX 打磨"),
    (re.compile(r"文档撰写"), "{token} 文档撰写"),
    (re.compile(r"部署上线\s*/?\s*发布"), "{token} 部署上线 / 发布"),
    (re.compile(r"性能优化"), "{token} 性能优化"),
    (re.compile(r"写技术文章\s*/?\s*分享"), "写 {token} 技术文章 / 分享"),
    (re.compile(r"GitHub\s*README"), "{token} GitHub README"),
    (re.compile(r"二次迭代\s*/?\s*收集反馈"), "{token} 二次迭代 / 收集反馈"),
    (re.compile(r"BUG\s*修复"), "{token} BUG 修复"),
    (re.compile(r"完整交付"), "{token} 完整交付"),
    (re.compile(r"总结成长"), "{token} 总结成长"),
    (re.compile(r"归档资料"), "{token} 归档资料"),
    # 通用兜底
    (re.compile(r"^复习$|^复盘$"), "{token} 复盘"),
    (re.compile(r"读官方文档|读文档"), "读 {token} 官方文档"),
    (re.compile(r"^看视频$"), "看 {token} 教学视频"),
    (re.compile(r"做项目|项目实践"), "{token} 项目实战"),
    (re.compile(r"写博客|输出博客"), "{token} 博客输出"),
    (re.compile(r"^笔记整理$|^整理笔记$"), "{token} 笔记整理"),
]

# 通用英文词白名单：这些不视为"已具体"，仍允许注入
# （因为它们是骨架的一部分，例如 "GitHub 提交" / "BUG 修复" / "epic" / "review"）
_GENERIC_EN_WORDS = {
    "github", "bug", "epic", "review", "readme", "ui", "ux",
    "hello", "world", "todo",
}


def _title_already_specific(title: str, all_tokens: list) -> bool:
    """判断 title 是否已经"具体化"——含任一 token 池里的词，则视为已注入过，跳过。"""
    if not title:
        return False
    low = title.lower()
    for tok in all_tokens:
        if tok and tok.lower() in low:
            return True
    return False

# 抽取 goal / resources 里的英文/驼峰技术词
_TECH_NAME_RE = re.compile(r"[A-Z][a-zA-Z][a-zA-Z0-9.+#-]{1,30}|[a-z]+[A-Z][a-zA-Z0-9]{2,}")

# 资源里 URL 的域名片段（提取主体名）
_URL_DOMAIN_RE = re.compile(r"https?://(?:www\.)?([a-zA-Z0-9-]+)\.")


def _extract_tokens(goal: str, weak_points: list, resources: list) -> dict:
    """从 goal/weak_points/resources 抽取语义 token。

    返回三组 token 池：
      - "concepts"：偏概念/术语，多用于 phase 1（基础）
      - "stack"：技术栈名（框架/库），多用于 phase 2（项目）
      - "deploy"：部署/输出向（含 deploy/host/CI/output 等线索）
    保序去重，每池上限 12 条避免无限膨胀。
    """
    concepts, stack, deploy = [], [], []
    seen = set()

    def _add(item: str, bucket: list, cap: int = 12):
        item = (item or "").strip()
        if not item or len(item) > 40 or item in seen:
            return
        seen.add(item)
        if len(bucket) < cap:
            bucket.append(item)

    # 1) weak_points：整条作为短语进 concepts（用户写的薄弱项 = 最该被点名的概念）
    for wp in (weak_points or []):
        _add(str(wp), concepts)

    # 2) goal：抽英文/驼峰专有名词到 stack；其余短句进 concepts
    if goal:
        for m in _TECH_NAME_RE.findall(goal):
            _add(m, stack)
        # 中文短句兜底：按"、，,"切分，长度 2-15 的进 concepts
        for seg in re.split(r"[、，,；;\s]+", goal):
            seg = seg.strip()
            if 2 <= len(seg) <= 15 and not _TECH_NAME_RE.search(seg):
                _add(seg, concepts)

    # 3) resources：URL 域名 + 英文专有名词进 stack；含部署关键词的进 deploy
    deploy_kw = ("deploy", "host", "vercel", "netlify", "ci", "上线", "部署", "发布")
    for r in (resources or []):
        rs = str(r)
        low = rs.lower()
        is_deploy = any(k in low for k in deploy_kw)
        for m in _TECH_NAME_RE.findall(rs):
            _add(m, deploy if is_deploy else stack)
        for m in _URL_DOMAIN_RE.findall(rs):
            if m.lower() not in ("github", "google", "bing"):
                _add(m, deploy if is_deploy else stack)

    return {"concepts": concepts, "stack": stack, "deploy": deploy}


def _phase_pool_order(phase_idx: int, pools: dict) -> list:
    """按 phase 偏好返回 token 池的拼接顺序（前者优先轮询）。"""
    if phase_idx == 0:
        return pools["concepts"] + pools["stack"]
    if phase_idx == 1:
        return pools["stack"] + pools["concepts"] + pools["deploy"]
    # phase 2+
    return pools["deploy"] + pools["stack"] + pools["concepts"]


def _rewrite_title(title: str, token: str, all_tokens: list) -> str:
    """白名单改写。命中骨架 pattern 才替换，否则原样返回。
    若 title 已经包含池中任意 token（无论大小写），视为已注入过，跳过。
    """
    if not token or not title:
        return title
    if _title_already_specific(title, all_tokens):
        return title
    for pat, tpl in _SKELETON_PATTERNS:
        if pat.search(title):
            return pat.sub(tpl.format(token=token), title, count=1)
    return title


def inject_semantic_tokens(plan: dict, goal: str = "",
                           weak_points: list = None,
                           resources: list = None) -> dict:
    """对 plan.daily_tasks 做语义 token 注入（P1-1 修复）。

    幂等：重复调用不会叠加注入（已含具体名词的 title 不会再被改）。
    返回原 plan（in-place 改写）。

    Args:
        plan: create_plan 返回的 plan 对象
        goal: 用户目标描述（可含英文技术名词）
        weak_points: 薄弱项短语列表
        resources: 资源链接/书名列表
    """
    if not isinstance(plan, dict):
        return plan
    daily_tasks = plan.get("daily_tasks") or []
    if not daily_tasks:
        return plan

    # 优先用传入参数；缺省则从 plan.meta 兜底（CLI 调用 / 已写入 meta 的情况）
    meta = plan.get("meta") or {}
    goal = goal or meta.get("goal") or ""
    weak_points = weak_points if weak_points is not None else (meta.get("weak_points") or [])
    resources = resources if resources is not None else (meta.get("resources") or [])

    pools = _extract_tokens(goal, weak_points, resources)
    if not (pools["concepts"] or pools["stack"] or pools["deploy"]):
        # 没抽到任何 token，无需注入（如纯中文短目标 + 空 weak_points）
        return plan

    # 合并所有 token 池用于"已具体化"判定（剔除通用英文词避免误判）
    all_tokens = [t for t in (pools["concepts"] + pools["stack"] + pools["deploy"])
                  if t.lower() not in _GENERIC_EN_WORDS]

    # stage_id -> phase_idx
    stages = plan.get("stages") or []
    stage_to_phase_idx = {}
    for i, st in enumerate(stages):
        sid = st.get("id")
        if sid:
            stage_to_phase_idx[sid] = i

    # 跨 stage 全局周计数（同 stage 内 day 累计 / 7）
    stage_day_counter = {}
    for daily in daily_tasks:
        sid = daily.get("stage_id", "stage-1")
        phase_idx = stage_to_phase_idx.get(sid, 0)
        # 同 stage 内推进，得到 week_idx
        stage_day_counter[sid] = stage_day_counter.get(sid, -1) + 1
        week_idx = stage_day_counter[sid] // 7

        pool = _phase_pool_order(phase_idx, pools)
        if not pool:
            continue

        for slot_idx, task in enumerate(daily.get("tasks") or []):
            title = task.get("title", "")
            if not title:
                continue
            token = pool[(week_idx * 3 + slot_idx) % len(pool)]
            new_title = _rewrite_title(title, token, all_tokens)
            if new_title != title:
                task["title"] = new_title
                task["_semantic_injected"] = True

    # 元信息留痕：方便 to_html_report / 调试时观察
    meta.setdefault("_semantic_pools", {
        "concepts_n": len(pools["concepts"]),
        "stack_n": len(pools["stack"]),
        "deploy_n": len(pools["deploy"]),
    })
    plan["meta"] = meta
    return plan


# ──────────────────────────────────────────────
# P1-3：薄弱项加权（NEVER 6 落地）
#
# 策略：
#   1) 任务 title 命中弱点关键词 → duration_min ×1.5（上限 MAX_TASK_MIN=45）
#      记 task["_weak_focus"] = True
#   2) 命中强项关键词（与弱点同类别但具体词不同）→ ×0.7（下限 20 min）
#      —— 仅当该 category 在 weak_points 中有出现时才触发"反向减压"
#   3) 每周（按 stage 内 day // 7 分组）至少有 1 条 _weak_focus，
#      若一周没命中任何弱点 → 把当周第一个 review/output 任务改为「{首条弱点} 专项」
#
# 注意：与 inject_semantic_tokens 协作——后者把骨架 title 改成"X 教程章节"等，
#   这里也能把 X = "Hooks 心智模型" / "听力 Section 4" 当弱点关键词命中。
# ──────────────────────────────────────────────

def _weak_keywords(weak_points: list) -> list:
    """从 weak_points 短语提取核心关键词（去停用词、长度 ≥ 2）。"""
    if not weak_points:
        return []
    stop = {"专项", "练习", "提升", "加练", "训练", "强化", "学习", "掌握"}
    kws = []
    seen = set()
    for wp in weak_points:
        s = str(wp).strip()
        if not s:
            continue
        # 整条作为一个关键词（用于"听力 Section 4"这类组合）
        if s.lower() not in seen:
            seen.add(s.lower())
            kws.append(s)
        # 再按空格 / 标点拆分成更细的关键词
        for seg in re.split(r"[\s、，,；;/]+", s):
            seg = seg.strip()
            if len(seg) >= 2 and seg not in stop and seg.lower() not in seen:
                seen.add(seg.lower())
                kws.append(seg)
    return kws


def apply_weak_points_weighting(plan: dict, weak_points: list) -> dict:
    """对 plan.daily_tasks 做薄弱项加权（in-place）。"""
    if not isinstance(plan, dict) or not weak_points:
        return plan
    daily_tasks = plan.get("daily_tasks") or []
    if not daily_tasks:
        return plan

    kws = _weak_keywords(weak_points)
    if not kws:
        return plan

    weighted_n = 0
    weak_categories = set()  # 弱点所属的 category 集合（用于强项 -30%）

    # 第一遍：命中加权
    for daily in daily_tasks:
        for task in (daily.get("tasks") or []):
            title = task.get("title") or ""
            low = title.lower()
            if any(kw.lower() in low for kw in kws):
                old = int(task.get("duration_min") or 0)
                new = min(MAX_TASK_MIN, int(round(old * 1.5)))
                if new > old:
                    task["duration_min"] = new
                task["_weak_focus"] = True
                task["priority"] = "high"
                # methodology_tip 切到 weak_focus 提示语
                task.setdefault("methodology_tip", METHOD_TIPS["weak_focus"])
                if not task.get("_origin_methodology_locked"):
                    task["methodology_tip"] = METHOD_TIPS["weak_focus"]
                weighted_n += 1
                cat = task.get("category")
                if cat:
                    weak_categories.add(cat)

    # 第二遍：每周巡检——若一周内 0 条 _weak_focus，强制把首条 review/output 改造成弱项专项
    # 索引：(stage_id, week_idx) -> [task_refs]
    stage_day_counter = {}
    weekly_buckets = {}
    for daily in daily_tasks:
        sid = daily.get("stage_id", "stage-1")
        stage_day_counter[sid] = stage_day_counter.get(sid, -1) + 1
        week_idx = stage_day_counter[sid] // 7
        weekly_buckets.setdefault((sid, week_idx), []).append(daily)

    primary_weak = weak_points[0] if weak_points else ""
    weak_idx = 0
    forced_n = 0
    for (sid, wi), days in weekly_buckets.items():
        has_focus = any(
            t.get("_weak_focus")
            for d in days
            for t in (d.get("tasks") or [])
        )
        if has_focus:
            continue
        # 找第一条 review / output 任务把它改成 "<weak> 专项"
        target = None
        for d in days:
            for t in (d.get("tasks") or []):
                if t.get("category") in ("review", "output", "weak_focus"):
                    target = t
                    break
            if target:
                break
        if target is None:
            # 退而求其次：拿当周第一个任务
            for d in days:
                if d.get("tasks"):
                    target = d["tasks"][0]
                    break
        if target is None:
            continue
        wp = weak_points[weak_idx % len(weak_points)] if weak_points else primary_weak
        weak_idx += 1
        target["title"] = f"{wp} 专项"
        target["_weak_focus"] = True
        target["priority"] = "high"
        target["category"] = _infer_category(target["title"], weak_points)
        target["methodology_tip"] = METHOD_TIPS["weak_focus"]
        old = int(target.get("duration_min") or 0)
        target["duration_min"] = min(MAX_TASK_MIN, max(old, int(round(old * 1.5)) if old else 30))
        forced_n += 1

    meta = plan.get("meta") or {}
    meta["_weak_weighting"] = {
        "weighted_n": weighted_n,
        "forced_weekly_focus_n": forced_n,
        "weak_categories": sorted(weak_categories),
    }
    plan["meta"] = meta
    return plan


# ──────────────────────────────────────────────
# P1-1（雅思批）：截止日留白说明
# 给 HTML / weekly checklist 头部一句话提示「计划末日 vs 截止日」的关系
# ──────────────────────────────────────────────

def _build_calendar_note(start_date, total_days: int, deadline_date,
                         deadline_overridden: bool) -> dict:
    """构造一段 meta._calendar_note，由报告层渲染。"""
    end_date = start_date + timedelta(days=total_days - 1)
    gap = (deadline_date - end_date).days
    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "plan_end_date": end_date.strftime("%Y-%m-%d"),
        "deadline": deadline_date.strftime("%Y-%m-%d"),
        "buffer_days": gap,  # >0 说明有留白；0 说明完全覆盖；<0 不应出现（已被反推逻辑处理）
        "deadline_overridden": deadline_overridden,
        "tip": (
            f"计划末日 {end_date:%m-%d}，距截止 {deadline_date:%m-%d} 留 {gap} 天"
            f"（建议做最后一套模考 + 早睡）"
            if gap > 0 else
            f"计划完整覆盖到截止日 {deadline_date:%m-%d}"
        ),
    }


def create_plan(name: str, deadline: str, template_id: str = "final-exam",
                total_days: int = None, materials_path: str = None,
                time_granularity: str = "daily",
                goal: str = "", weak_points: list = None,
                resources: list = None, current_level: str = "") -> dict:
    """创建计划结构（含 stages 和 daily_tasks 骨架，AI 后续可继续 edit）

    重要：所有校验必须在 makedirs / 写盘之前完成，避免脏目录残留。

    Args:
        time_granularity: 时间精度，可选 monthly/daily/hourly/minutely
        goal: 用户目标描述（用于语义 token 注入到任务 title）
        weak_points: 薄弱项短语列表（同上，且追加到 meta.weak_points）
        resources: 学习资源列表（同上，写入 meta.resources）
        current_level: 当前水平描述（仅写入 meta，不参与注入）
    """
    # ── 校验 1：name 非空 ──
    if not name or not name.strip():
        raise ValueError("计划名称不能为空")

    # ── 校验 2：deadline 格式 + ≥ 今日 ──
    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(f"截止日期格式错误：{deadline}（应为 YYYY-MM-DD）")

    today = datetime.now().date()
    if deadline_date < today:
        raise ValueError(f"截止日 {deadline} 早于今日 {today}，请重新输入")

    # ── 校验 3：total_days 范围 + 计划跨度 ≤ 12 个月 ──
    # P1-1 修复：当用户传 --days N 但 N < (deadline-today) 时，**默认改为覆盖到 deadline**
    #   理由：违反 SKILL.md 能力 1「目标 + 截止日」承诺——计划应覆盖到截止日，
    #   不是机械排 N 天后留考前空白。
    #   保留 STUDY_PLANNER_STRICT_DAYS=1 环境变量给"我就是要排 N 天"的高级用户开后门。
    days_to_deadline = max(1, (deadline_date - today).days + 1)  # 含截止日当天
    deadline_overridden = False
    if total_days is not None:
        if total_days < 1:
            raise ValueError(f"--days 必须 ≥ 1（当前 {total_days}）")
        if total_days > MAX_PLAN_DAYS:
            raise ValueError(
                f"计划跨度不得超过 12 个月（{MAX_PLAN_DAYS} 天），当前请求 {total_days} 天。"
                f"如需更长周期，建议拆成多份阶段性计划。"
            )
        # 默认覆盖到 deadline；除非显式 STRICT_DAYS=1
        strict = os.environ.get("STUDY_PLANNER_STRICT_DAYS", "").strip() in ("1", "true", "True")
        if (not strict) and total_days < days_to_deadline:
            print(
                f"ℹ️  --days {total_days} 比截止日 {deadline}（距今 {days_to_deadline} 天）短"
                f" {days_to_deadline - total_days} 天；自动延长至截止日以覆盖考前/学完日。"
                f"\n   如需严格按 N 天排程，设 STUDY_PLANNER_STRICT_DAYS=1 后重跑。",
                file=sys.stderr,
            )
            total_days = days_to_deadline
            deadline_overridden = True
    else:
        # 按截止日推算（含截止日当天）
        total_days = days_to_deadline
        if total_days > MAX_PLAN_DAYS:
            raise ValueError(
                f"截止日 {deadline} 距今 {total_days} 天，超过 12 个月（{MAX_PLAN_DAYS} 天）上限。"
                f"建议拆成多份阶段性计划，或缩短首阶段截止日。"
            )

    # ── 校验 4：模板存在 ──
    template = load_template(template_id)  # 模板找不到会抛 FileNotFoundError

    # ── 校验 5：materials 文件（可选） ──
    weak_points_from_materials = []
    if materials_path:
        weak_points_from_materials = parse_materials(materials_path)  # 失败抛 ValueError

    # ── 全部校验通过，才开始落盘 ──
    plan_id = f"plan-{datetime.now().strftime('%Y%m%d')}-{slugify(name)}"
    plan_dir = os.path.join(DATA_DIR, plan_id)
    os.makedirs(plan_dir, exist_ok=True)
    _ensure_gitignore()  # 首次落盘自动写 .gitignore（NEVER 1：保护用户数据不被误 commit）

    start_date = datetime.combine(today, datetime.min.time())
    daily_budget = {"weekday": 90, "weekend": 180}

    # 默认方法论（从模板的 methodology_injection 里挑出 true 的）
    inj = template.get("methodology_injection", {})
    methodology = [k for k in ("ebbinghaus", "pomodoro", "pareto", "feynman") if inj.get(k)]
    if not methodology:
        methodology = ["ebbinghaus", "pomodoro"]

    # 构建 stages 与 daily_tasks 骨架
    # P1-3 前置：把 weak_points 合并提前，让 _build_daily_tasks 能识别弱点关键词
    merged_weak = list(weak_points or [])
    seen_wp = set(merged_weak)
    for wp in weak_points_from_materials:
        if wp not in seen_wp:
            merged_weak.append(wp)
            seen_wp.add(wp)

    stages = _build_stages(template, total_days)
    daily_tasks = _build_daily_tasks(template, stages, start_date, total_days,
                                     daily_budget, time_granularity,
                                     weak_points=merged_weak)

    # 给骨架任务打标记，rebalance 才能识别（避免误伤用户后续 add-task 的自定义任务）
    for daily in daily_tasks:
        for task in daily["tasks"]:
            task["_origin"] = "skeleton"
            # 根据时间粒度补充字段
            if time_granularity == "hourly":
                # 为任务分配开始小时（简单策略：按任务顺序分配到可用时段）
                pass  # 由 _build_daily_tasks 内部处理
            elif time_granularity == "minutely":
                task["pomodoro_split"] = True

    # 构建计划

    plan = {
        "id": plan_id,
        "version": 1,
        "meta": {
            "title": name,
            "goal": goal or "",
            "deadline": deadline,
            "current_level": current_level or "",
            "daily_budget": daily_budget,
            "weak_points": merged_weak,
            "resources": list(resources or []),
            "methodology": methodology,
            "template_origin": template_id,
            "time_granularity": time_granularity,
            "_calendar_note": _build_calendar_note(start_date.date(), total_days, deadline_date,
                                                   deadline_overridden),
        },
        "stages": stages,
        "daily_tasks": daily_tasks,
        "_plan_dir": plan_dir,
    }

    # P1-1（编程批）：把 goal/weak_points/resources 中的具体技术词注入到任务 title
    # （仅对骨架 title 改写，已含专有名词的不动；零 token 时静默跳过）
    inject_semantic_tokens(plan, goal=goal or "",
                           weak_points=merged_weak,
                           resources=list(resources or []))

    # P1-3（雅思批）：薄弱项加权（弱点关键词命中 → +50% 时长，≤45min 上限）
    # NEVER 6：弱项 +50% 时长，强项 -30%，这才叫个性化
    apply_weak_points_weighting(plan, merged_weak)

    return plan


def save_plan(plan: dict) -> str:
    """保存计划到磁盘"""
    plan_dir = plan.pop("_plan_dir", None)
    if not plan_dir:
        plan_id = plan["id"]
        plan_dir = os.path.join(DATA_DIR, plan_id)

    plan_path = os.path.join(plan_dir, "plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    # 同时创建空的打卡记录和 Streak 文件
    checkin_path = os.path.join(plan_dir, "checkin-log.json")
    streak_path = os.path.join(plan_dir, "streak.json")
    config_path = os.path.join(plan_dir, "user-config.json")

    with open(checkin_path, "w", encoding="utf-8") as f:
        json.dump({"plan_id": plan["id"], "checkins": []}, f, ensure_ascii=False, indent=2)

    with open(streak_path, "w", encoding="utf-8") as f:
        json.dump({
            "plan_id": plan["id"],
            "current": 0,
            "longest": 0,
            "last_checkin": None,
            "broken_dates": [],
            "milestones_unlocked": [],
            "achievements": []
        }, f, ensure_ascii=False, indent=2)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({
            "persona": "gentle-senior",
            "active_plan_id": plan["id"],
            "checkin_channel": "daily",
            "reminder_time": "09:00"
        }, f, ensure_ascii=False, indent=2)

    return plan_path


def list_plans() -> list:
    """列出所有计划"""
    if not os.path.exists(DATA_DIR):
        return []
    plans = []
    for pid in os.listdir(DATA_DIR):
        plan_path = os.path.join(DATA_DIR, pid, "plan.json")
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
                plans.append({
                    "id": plan["id"],
                    "title": plan["meta"]["title"],
                    "deadline": plan["meta"]["deadline"],
                    "template": plan["meta"].get("template_origin", "unknown")
                })
    return plans


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 列出所有计划
        plans = list_plans()
        if not plans:
            print("暂无学习计划。使用 'python3 init_plan.py <名称> <截止日期>' 创建第一个计划。")
        else:
            print("📋 当前学习计划：")
            for p in plans:
                print(f"  • {p['title']} ({p['id']}) - 截止 {p['deadline']}")
        sys.exit(0)

    name = sys.argv[1]
    deadline = sys.argv[2] if len(sys.argv) > 2 else None

    if not deadline:
        print("错误：需要指定截止日期，格式 YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    template = "final-exam"
    total_days = None
    materials_path = None
    time_granularity = "daily"
    goal = ""
    weak_points_arg = []
    resources_arg = []
    current_level = ""

    for i, arg in enumerate(sys.argv):
        if arg == "--template" and i + 1 < len(sys.argv):
            template = sys.argv[i + 1]
        if arg == "--days" and i + 1 < len(sys.argv):
            try:
                total_days = int(sys.argv[i + 1])
            except ValueError:
                print(f"❌ --days 必须是整数（当前 {sys.argv[i + 1]}）", file=sys.stderr)
                sys.exit(1)
        if arg == "--materials" and i + 1 < len(sys.argv):
            materials_path = sys.argv[i + 1]
        if arg == "--granularity" and i + 1 < len(sys.argv):
            g = sys.argv[i + 1].lower()
            if g not in _VALID_GRANULARITIES:
                print(f"❌ --granularity 必须是 {', '.join(_VALID_GRANULARITIES)} 之一（当前「{g}」）", file=sys.stderr)
                sys.exit(1)
            time_granularity = g
        # P1-1：语义注入相关 flag
        if arg == "--goal" and i + 1 < len(sys.argv):
            goal = sys.argv[i + 1]
        if arg == "--weak-points" and i + 1 < len(sys.argv):
            # 用 | 或 ; 分隔多条；兼容 JSON 数组
            raw = sys.argv[i + 1]
            if raw.strip().startswith("["):
                try:
                    weak_points_arg = [str(x) for x in json.loads(raw)]
                except (json.JSONDecodeError, ValueError):
                    weak_points_arg = [s.strip() for s in re.split(r"[|;]", raw) if s.strip()]
            else:
                weak_points_arg = [s.strip() for s in re.split(r"[|;]", raw) if s.strip()]
        if arg == "--resources" and i + 1 < len(sys.argv):
            raw = sys.argv[i + 1]
            if raw.strip().startswith("["):
                try:
                    resources_arg = [str(x) for x in json.loads(raw)]
                except (json.JSONDecodeError, ValueError):
                    resources_arg = [s.strip() for s in re.split(r"[|;]", raw) if s.strip()]
            else:
                resources_arg = [s.strip() for s in re.split(r"[|;]", raw) if s.strip()]
        if arg == "--current-level" and i + 1 < len(sys.argv):
            current_level = sys.argv[i + 1]

    try:
        plan = create_plan(name, deadline, template, total_days, materials_path,
                           time_granularity,
                           goal=goal,
                           weak_points=weak_points_arg or None,
                           resources=resources_arg or None,
                           current_level=current_level)
    except ValueError as e:
        # 业务校验失败（deadline 过期 / >365 天 / 名称空 / materials 解析失败）
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        # 模板不存在
        print(f"❌ {e}", file=sys.stderr)
        try:
            avail = sorted(
                f[:-5] for f in os.listdir(TEMPLATE_DIR)
                if f.endswith(".json") and not f.startswith(".")
            )
            print(f"   可用模板：{', '.join(avail) or '(空)'}", file=sys.stderr)
        except OSError:
            pass
        sys.exit(2)

    path = save_plan(plan)

    print(f"✅ 计划已创建: {path}")
    print(f"   计划 ID: {plan['id']}")
    print(f"   模板: {template}")
    if plan["meta"]["weak_points"]:
        print(f"   从大纲抽取的 weak_points（{len(plan['meta']['weak_points'])} 条）:")
        for wp in plan["meta"]["weak_points"][:5]:
            print(f"     • {wp}")
        if len(plan["meta"]["weak_points"]) > 5:
            print(f"     ...（共 {len(plan['meta']['weak_points'])} 条，详见 plan.json）")
    print(f"\n现在可以告诉 AI：「我已创建计划 {plan['id']}，帮我填入详细信息并生成任务」")
