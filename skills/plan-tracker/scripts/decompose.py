#!/usr/bin/env python3
"""
decompose.py - 目标拆解核心逻辑库（纯函数，无副作用）

提供 SMART → OKR → 每日 ABC 三层拆解的核心算法。
被 init_plan.py 调用，也可单独被其他脚本/AI 复用。

核心方法论（融合参考）：
  1. SMART —— 把"我想搞定 X"变成 Specific/Measurable/Achievable/Relevant/Time-bound
  2. OKR  —— 月度 Objective + 周度 Key Results（量化的领先指标）
  3. ABC  —— 每日任务三档（Ambitious/Baseline/Comeback），永不全员清零
            （来自 huntsyea/thinking-skills · habits-and-goals）
  4. Anti-Goals —— 拒绝牺牲什么（睡眠/运动/家庭），写进 plan.meta
  5. If-Then Plans —— 障碍预演（"如果 X 发生，就做 Y"）

零网络、零三方包、Python 3.8+ 标准库。
"""

import re
from datetime import date, datetime, timedelta


# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────

# 单计划硬上限（与 _plan_utils.MAX_PLAN_DAYS=180 对齐）
MAX_PLAN_DAYS = 180

# ABC 三档时间分配比例（基于 daily_budget）
ABC_RATIO = {
    "a": 1.00,  # Ambitious: 完美日，跑满 budget
    "b": 0.65,  # Baseline:  普通日，约 2/3
    "c": 0.15,  # Comeback:  最低日，10% 左右（≥ 10min，2 分钟法则向上取整）
}

# C 档绝对下限（无论 budget 多大，C 档必须 ≤ 这个值才能"无法拒绝"）
C_LEVEL_MAX_MIN = 15
# C 档绝对下限（≥ 5min，避免出现 0 分钟）
C_LEVEL_MIN_MIN = 5

# 单任务时长上限（番茄钟友好，与 study-planner 对齐）
MAX_TASK_MIN = 45

# 每日任务条数上限（防止"任务列表恐惧症"）
MAX_DAILY_TASKS = 5

# 类目推断关键词（与 study-planner 共享语料；保持触发词一致）
# ⚠️ 顺序敏感：高优先级类目放前面（避免"复盘"先命中导致整周分类全归 review）
# review 关键词放最后，作为兜底
CATEGORY_HINTS = [
    # —— 编程 / 技术（dev/coding）——
    ("代码", "coding"), ("写代码", "coding"), ("编程", "coding"),
    ("python", "coding"), ("java", "coding"), ("golang", "coding"),
    ("javascript", "coding"), ("typescript", "coding"),
    ("算法", "coding"), ("leetcode", "coding"), ("刷题", "coding"),
    ("调试", "coding"), ("debug", "coding"),
    ("框架", "coding"), ("django", "coding"), ("flask", "coding"), ("spring", "coding"),
    ("数据库", "coding"), ("sql", "coding"),
    # —— 听力 ——
    ("听力", "listening"), ("精听", "listening"), ("听写", "listening"),
    # —— 阅读 ——
    ("阅读", "reading"), ("精读", "reading"),
    # —— 写作 ——
    ("写作", "writing"), ("作文", "writing"), ("范文", "writing"),
    # —— 口语 ——
    ("口语", "speaking"), ("speaking", "speaking"),
    # —— 词汇 ——
    ("词汇", "vocabulary"), ("单词", "vocabulary"), ("背词", "vocabulary"),
    # —— 语法 ——
    ("语法", "grammar"),
    # —— 模考 ——
    ("模考", "exam"), ("套题", "exam"), ("限时", "exam"), ("真题", "exam"),
    # —— 输出 ——
    ("项目", "output"), ("产出", "output"), ("文章", "output"), ("博客", "output"),
    # —— 休息 ——
    ("休息", "rest"), ("早睡", "rest"),
    ("运动", "rest"), ("散步", "rest"),
    # —— 复盘（放最后，作为兜底，避免"复盘 + 错题"误吞整组任务）——
    ("错题", "review"), ("回顾", "review"), ("复盘", "review"),
]


# ──────────────────────────────────────────────
# 0. slug 工具（plan_id 用）
# ──────────────────────────────────────────────

def slugify(text: str, max_len: int = 30) -> str:
    """中英文混合 → URL-safe slug。

    策略：
      1. 优先保留 ASCII 字母 / 数字 / 连字符（plan_id 用作目录名 + URL 友好）
      2. 中文等非 ASCII 字符**整体丢弃**（避免 `plan-20260512-考研英语-65` 这种含中文的目录名
         在跨平台 / shell 引号 / dashboard URL 时翻车）
      3. 若 ASCII 化后 slug 太短（< 3 字符，常见于纯中文标题），追加原文 4 字符短哈希
         以保证唯一性 + 与原文的可追溯性
      4. 完全空 → "unnamed"
    """
    text = (text or "").strip()
    if not text:
        return "unnamed"
    raw_low = text.lower()
    # 仅保留 ASCII 字母数字与连字符；其他字符（含中文 / 标点）全部替换为 -
    ascii_slug = re.sub(r"[^a-z0-9-]+", "-", raw_low)
    ascii_slug = re.sub(r"-+", "-", ascii_slug).strip("-")

    if len(ascii_slug) >= 3:
        return ascii_slug[:max_len]

    # ASCII 太少（多为纯中文标题）→ 用 4 字符短哈希做后缀
    import hashlib
    short_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:6]
    if ascii_slug:
        candidate = f"{ascii_slug}-{short_hash}"
    else:
        candidate = f"plan-{short_hash}"
    return candidate[:max_len] or "unnamed"


def infer_category(title: str) -> str:
    """根据任务标题推断 category。

    规则升级：
      - 优先匹配高优先级类目（按 CATEGORY_HINTS 顺序，coding > listening/reading/... > review）
      - review 是最后的兜底，避免"复盘 + 错题"这种关键词组合让整组任务都被归到 review
    """
    if not title:
        return "review"
    lt = title.lower()
    for kw, cat in CATEGORY_HINTS:
        if kw in lt:
            return cat
    return "review"


def infer_category_for_items(items: list) -> str:
    """对一组任务项分别 infer，取众数（mode）作为整组的 category。

    历史 bug：之前用 `" ".join(items)` 拼一个长串再 infer，导致
    `["背词 30", "阅读 1 篇", "复盘错题"]` 因为命中"复盘"被错归到 review，
    实际上 3 项里有 2 项是单词/阅读。改为各项独立 infer 再取众数。

    若众数有并列（如 1:1:1），按 CATEGORY_HINTS 顺序优先（coding > listening > ...）。
    """
    if not items:
        return "review"
    cats = [infer_category(s) for s in items if s]
    if not cats:
        return "review"
    # 取众数
    counter = {}
    for c in cats:
        counter[c] = counter.get(c, 0) + 1
    max_count = max(counter.values())
    winners = [c for c, n in counter.items() if n == max_count]
    if len(winners) == 1:
        return winners[0]
    # 并列：按 CATEGORY_HINTS 优先级（出现越早越优先）
    priority_order = []
    for kw, cat in CATEGORY_HINTS:
        if cat in winners and cat not in priority_order:
            priority_order.append(cat)
    return priority_order[0] if priority_order else winners[0]


# ──────────────────────────────────────────────
# 1. SMART 校验
# ──────────────────────────────────────────────

def validate_smart(goal: dict) -> list:
    """检查目标是否符合 SMART 五要素。

    Args:
        goal: {
            "title": "搞定考研英语二",
            "specific": "做对真题英二平均 65 分以上",  # M（可衡量验收标准）
            "deadline": "2026-07-15",                  # T
            "current_level": "四级 480，没做过英二",   # 起点
            "daily_minutes": {"weekday": 60, "weekend": 120},  # A（可达成）
            "relevance": "考研需要"                    # R（与更高目标的关联，可空）
        }

    Returns:
        缺陷列表 [str]，空列表表示完全通过 SMART。
    """
    issues = []
    if not goal.get("title", "").strip():
        issues.append("S: 目标标题为空（请用一句话说清要搞定什么）")
    if not goal.get("specific", "").strip():
        issues.append("M: 缺少可衡量的验收标准（如『真题 65 分』『跑完 5 公里』）")

    deadline = goal.get("deadline")
    if not deadline:
        issues.append("T: 缺少截止日期")
    else:
        try:
            d = datetime.strptime(deadline, "%Y-%m-%d").date()
            today = date.today()
            if d < today:
                issues.append(f"T: 截止日 {deadline} 已过期")
            elif (d - today).days > MAX_PLAN_DAYS:
                issues.append(
                    f"T: 截止日距今 {(d - today).days} 天，超过 {MAX_PLAN_DAYS} 天上限。"
                    f"建议拆成多阶段（先搞定首阶段）"
                )
            elif (d - today).days < 7:
                issues.append(f"T: 截止日距今仅 {(d - today).days} 天，太短可能产出不可达计划")
        except (ValueError, TypeError):
            issues.append(f"T: 截止日格式错误『{deadline}』（应为 YYYY-MM-DD）")

    db = goal.get("daily_minutes")
    if not db or not isinstance(db, dict):
        issues.append("A: 缺少每日可投入时间（请提供工作日/周末的分钟数）")
    else:
        wd = db.get("weekday", 0)
        we = db.get("weekend", 0)
        if not (isinstance(wd, int) and 0 <= wd <= 600):
            issues.append(f"A: weekday 时长不合理（{wd}），合理区间 0-600 分钟")
        if not (isinstance(we, int) and 0 <= we <= 600):
            issues.append(f"A: weekend 时长不合理（{we}），合理区间 0-600 分钟")
        if (wd or 0) + (we or 0) == 0:
            issues.append("A: 工作日和周末时长都为 0，无法生成计划")

    if not goal.get("current_level", "").strip():
        issues.append("起点: 缺少当前水平描述（用于估算可达性）")

    return issues


# ──────────────────────────────────────────────
# 2. OKR 月度/周度拆解
# ──────────────────────────────────────────────

def split_into_phases(start: date, end: date, max_phase_days: int = 30) -> list:
    """把总周期均分成 N 个阶段（每阶段 ≤ max_phase_days）。

    Returns:
        [{"id": "phase-1", "start": "2026-05-12", "end": "2026-06-10", "days": 30}, ...]
    """
    total_days = (end - start).days + 1
    if total_days <= 0:
        return []

    n_phases = max(1, (total_days + max_phase_days - 1) // max_phase_days)
    phases = []
    consumed = 0
    for i in range(n_phases):
        if i == n_phases - 1:
            days = total_days - consumed
        else:
            days = max(7, total_days // n_phases)  # 单阶段最少 7 天
        p_start = start + timedelta(days=consumed)
        p_end = p_start + timedelta(days=days - 1)
        if p_end > end:
            p_end = end
        phases.append({
            "id": f"phase-{i + 1}",
            "start": p_start.isoformat(),
            "end": p_end.isoformat(),
            "days": (p_end - p_start).days + 1,
        })
        consumed += days
        if consumed >= total_days:
            break
    return phases


def build_okr_skeleton(goal: dict, phases: list) -> list:
    """为每个 phase 生成 OKR 骨架（Objective + 3 KR 占位）。

    设计原则：
      - 每个 Objective 是这一阶段的"主关键词"（如 M1: 词汇 + 阅读基础）
      - KR 用领先指标（"完成 X 道题""背完 X 个词"），而非滞后指标（"考 65 分"）
      - 此函数只产出骨架，**具体 KR 内容由 AI 在拆解对话中填充**
    """
    title = goal.get("title", "目标")
    okrs = []
    for i, phase in enumerate(phases, 1):
        okrs.append({
            "phase_id": phase["id"],
            "phase_range": f"{phase['start']} ~ {phase['end']}",
            "objective": f"M{i}: {title} 阶段 {i}（待 AI 在拆解对话中具体化）",
            "key_results": [
                # 领先指标占位 ×3，AI 应替换为具体可量化项
                {"kr": "（待填）量化产出 1", "target": 0, "unit": "件", "current": 0},
                {"kr": "（待填）量化产出 2", "target": 0, "unit": "件", "current": 0},
                {"kr": "（待填）量化产出 3", "target": 0, "unit": "件", "current": 0},
            ],
        })
    return okrs


# ──────────────────────────────────────────────
# 3. ABC 三档每日任务
# ──────────────────────────────────────────────

def compute_abc_minutes(daily_budget_min: int) -> dict:
    """根据当日可投入分钟数，算出 A/B/C 三档时长。

    规则：
      - A 档 = budget × 100%（向下取整到 5 的倍数）
      - B 档 = budget × 65%
      - C 档 = max(C_LEVEL_MIN_MIN, min(C_LEVEL_MAX_MIN, budget × 15%))
              确保 C 档总在 [5, 15] 分钟，"短到无法拒绝"
    """
    if daily_budget_min <= 0:
        return {"a": 0, "b": 0, "c": 0}

    a = (int(daily_budget_min * ABC_RATIO["a"]) // 5) * 5
    a = max(5, a)

    b = (int(daily_budget_min * ABC_RATIO["b"]) // 5) * 5
    b = max(5, b)

    c_raw = int(daily_budget_min * ABC_RATIO["c"])
    c = max(C_LEVEL_MIN_MIN, min(C_LEVEL_MAX_MIN, (c_raw // 5) * 5 if c_raw >= 5 else C_LEVEL_MIN_MIN))

    return {"a": a, "b": b, "c": c}


def split_into_pomodoros(total_min: int, max_each: int = MAX_TASK_MIN) -> list:
    """把总分钟数拆成 ≤ max_each 的番茄段，余数 < 5 合并到上一段。"""
    if total_min <= max_each:
        return [total_min]
    chunks = []
    remaining = total_min
    while remaining > max_each:
        chunks.append(max_each)
        remaining -= max_each
    if remaining < 5 and chunks:
        chunks[-1] += remaining
    elif remaining > 0:
        chunks.append(remaining)
    return chunks


def build_abc_levels(
    a_items: list,
    b_items: list,
    c_items: list,
    a_min: int,
    b_min: int,
    c_min: int,
) -> dict:
    """组装 task.abc_levels 子结构。

    Args:
        a_items: A 档要做的事项标题列表，如 ["背词 30", "阅读 1 篇", "精翻 1 段"]
        b_items: B 档（应是 a_items 的子集，去掉最低优先级的项）
        c_items: C 档（最简化版本，1-2 项即可，10 分钟法则）

    Returns:
        {
          "a": {"items": [...], "minutes": 90},
          "b": {"items": [...], "minutes": 60},
          "c": {"items": [...], "minutes": 10}
        }
    """
    return {
        "a": {"items": list(a_items), "minutes": int(a_min)},
        "b": {"items": list(b_items), "minutes": int(b_min)},
        "c": {"items": list(c_items), "minutes": int(c_min)},
    }


def derive_bc_from_a(a_items: list) -> tuple:
    """从 A 档自动派生 B/C 档默认值（AI 没有显式拆分时的兜底）。

    策略：
      - B = A 去掉最后 1 项（通常是最累/最低优先级）
      - C = A 的第一项 + "（精简版）"后缀，且只保留这 1 项

    返回 (b_items, c_items)
    """
    if not a_items:
        return [], []
    if len(a_items) == 1:
        # 只有 1 项：B = A 同款；C = A[0] 精简版
        return [a_items[0]], [f"{a_items[0]}（精简版）"]
    if len(a_items) == 2:
        return [a_items[0]], [f"{a_items[0]}（精简版）"]
    # ≥ 3 项：B = 前 N-1 项；C = 第一项的最简版本
    return a_items[:-1], [f"{a_items[0]}（10 分钟版）"]


# ──────────────────────────────────────────────
# 4. Anti-Goals 与 If-Then Plans
# ──────────────────────────────────────────────

def normalize_anti_goals(items) -> list:
    """规范化 anti_goals 列表。
    输入可以是字符串列表或单字符串（顿号/逗号分隔）。
    """
    if not items:
        return []
    if isinstance(items, str):
        items = re.split(r"[、,，;；]", items)
    cleaned = []
    seen = set()
    for x in items:
        s = (x or "").strip()
        if not s or len(s) > 50:
            continue
        if s in seen:
            continue
        seen.add(s)
        cleaned.append(s)
    return cleaned[:10]  # 最多 10 条，防 anti_goal 通胀


def normalize_if_then_plans(items) -> list:
    """规范化 if-then 应急方案列表。

    每条结构：{"if": "加班到 21 点后", "then": "只做 C 档", "trigger_kind": "low_energy"}

    输入可以是：
      - dict 列表（直接使用）
      - 字符串列表（"如果 X 那就 Y" 形式自动 split）
    """
    if not items:
        return []
    if isinstance(items, str):
        items = [items]

    cleaned = []
    for x in items:
        if isinstance(x, dict):
            cond = (x.get("if") or "").strip()
            act = (x.get("then") or "").strip()
            kind = (x.get("trigger_kind") or "general").strip()
            if cond and act:
                cleaned.append({"if": cond[:80], "then": act[:80], "trigger_kind": kind})
            continue
        s = (x or "").strip()
        if not s:
            continue
        # 尝试解析"如果 X 那就/就/则 Y"
        m = re.match(r"^(?:如果|if)\s*(.+?)(?:那就|就|则|那么|then|，then)\s*(.+)$", s, re.IGNORECASE)
        if m:
            cleaned.append({
                "if": m.group(1).strip()[:80],
                "then": m.group(2).strip()[:80],
                "trigger_kind": "general",
            })
    return cleaned[:8]


# ──────────────────────────────────────────────
# 5. 顶层装配：build_decomposition
# ──────────────────────────────────────────────

def build_decomposition(goal: dict, daily_skeleton: dict = None) -> dict:
    """把 SMART 目标 + 用户提供的每日骨架，组装成 plan.json 的 meta + stages + daily_tasks。

    Args:
        goal: 见 validate_smart 文档
        daily_skeleton: AI 在对话中提供的每日 ABC 骨架，结构如：
            {
              "weekday_a_items": ["背词 30", "阅读 1 篇", "精翻 1 段"],
              "weekend_a_items": ["背词 30", "阅读 2 篇", "精翻 1 段", "作文 1 篇"],
              # 以下 4 项可选，缺失会用 derive_bc_from_a 自动派生
              "weekday_b_items": [...],
              "weekday_c_items": [...],
              "weekend_b_items": [...],
              "weekend_c_items": [...],
            }
            完全省略时 → 用通用骨架（"复盘+错题+薄弱项"）

    Returns:
        {
          "meta": {...},  # 含 anti_goals / if_then_plans / okr_phases / current_level 等
          "stages": [...],  # phase
          "daily_tasks": [...],  # 含 abc_levels 的每日任务列表
        }

    NOTE：此函数不写盘、不调用任何 AI。所有"创意决策"（用户该做什么）必须由
        调用方（AI 拆解对话）在传入 goal/daily_skeleton 时给出。
    """
    issues = validate_smart(goal)
    if issues:
        raise ValueError("目标 SMART 校验失败：\n  - " + "\n  - ".join(issues))

    today = date.today()
    deadline_date = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
    total_days = (deadline_date - today).days + 1

    phases = split_into_phases(today, deadline_date, max_phase_days=30)
    okrs = build_okr_skeleton(goal, phases)

    # 每日 ABC 时长
    db = goal["daily_minutes"]
    abc_min_wd = compute_abc_minutes(db.get("weekday", 0))
    abc_min_we = compute_abc_minutes(db.get("weekend", 0))

    # 每日骨架（AI 提供 or 通用兜底）
    skel = daily_skeleton or {}
    wd_a = skel.get("weekday_a_items") or ["每日复盘 + 错题回顾", "薄弱项专项 30 min", "睡前复现今日重点"]
    we_a = skel.get("weekend_a_items") or wd_a + ["综合训练 / 模拟测试"]

    wd_b = skel.get("weekday_b_items") or derive_bc_from_a(wd_a)[0]
    wd_c = skel.get("weekday_c_items") or derive_bc_from_a(wd_a)[1]
    we_b = skel.get("weekend_b_items") or derive_bc_from_a(we_a)[0]
    we_c = skel.get("weekend_c_items") or derive_bc_from_a(we_a)[1]

    # 装配每日任务
    daily_tasks = []
    task_counter = 0
    for offset in range(total_days):
        d = today + timedelta(days=offset)
        is_weekend = d.weekday() >= 5
        a_items = we_a if is_weekend else wd_a
        b_items = we_b if is_weekend else wd_b
        c_items = we_c if is_weekend else wd_c
        abc_min = abc_min_we if is_weekend else abc_min_wd

        # 选当天所属 phase
        phase_id = "phase-1"
        for p in phases:
            if p["start"] <= d.isoformat() <= p["end"]:
                phase_id = p["id"]
                break

        # 每日生成"主任务"，把 ABC 三档塞进去
        task_counter += 1
        a_items = a_items[:MAX_DAILY_TASKS]
        b_items = b_items[:MAX_DAILY_TASKS]
        c_items = c_items[:MAX_DAILY_TASKS]

        title_main = f"{goal['title']} · 主任务"
        # 各项独立 infer 再取众数（避免"复盘 + 错题"让整组都归到 review）
        category = infer_category_for_items(a_items)

        task = {
            "id": f"t-{task_counter:03d}",
            "title": title_main,
            "duration_min": abc_min["a"],  # 默认显示 A 档时长（today.py 渲染时可切换）
            "category": category,
            "priority": "high",
            "checkable": True,
            "abc_levels": build_abc_levels(
                a_items, b_items, c_items,
                abc_min["a"], abc_min["b"], abc_min["c"],
            ),
            "_origin": "decompose",
        }

        daily_tasks.append({
            "date": d.isoformat(),
            "stage_id": phase_id,
            "tasks": [task],
        })

    # stages（与 phase 对齐，但语义更接近 study-planner 的 stage）
    stages = [{
        "id": p["id"],
        "name": f"阶段 {i + 1}",
        "duration_days": p["days"],
        "start_date": p["start"],
        "end_date": p["end"],
        "goals": [okrs[i]["objective"]] if i < len(okrs) else [],
    } for i, p in enumerate(phases)]

    # meta（核心：anti_goals + if_then_plans + okr_phases）
    meta = {
        "title": goal["title"],
        "goal": goal.get("specific", ""),  # SMART 的 M：可衡量验收标准
        "deadline": goal["deadline"],
        "start_date": today.isoformat(),
        "current_level": goal.get("current_level", ""),
        "daily_budget": dict(goal["daily_minutes"]),
        "weak_points": list(goal.get("weak_points") or []),
        "resources": list(goal.get("resources") or []),
        "methodology": ["smart", "okr", "abc-tiers", "anti-goals", "if-then"],
        "anti_goals": normalize_anti_goals(goal.get("anti_goals")),
        "if_then_plans": normalize_if_then_plans(goal.get("if_then_plans")),
        "okr_phases": okrs,
        "decomposed_by": "plan-tracker.decompose v1.0",
        "decomposed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {"meta": meta, "stages": stages, "daily_tasks": daily_tasks}


# ──────────────────────────────────────────────
# 6. 演示
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # 演示：60 天考研英语二
    demo_goal = {
        "title": "考研英语二 65+",
        "specific": "做对真题英二平均 65 分以上",
        "deadline": (date.today() + timedelta(days=60)).isoformat(),
        "current_level": "四级 480，没系统做过英二",
        "daily_minutes": {"weekday": 90, "weekend": 180},
        "anti_goals": ["晚于 23:30 睡", "周末完全不休"],
        "if_then_plans": [
            {"if": "加班到 21 点后", "then": "只做 C 档", "trigger_kind": "low_energy"},
            {"if": "连续 3 天落后", "then": "削减最弱模块的 30%", "trigger_kind": "fall_behind"},
        ],
    }
    skeleton = {
        "weekday_a_items": ["背词 30", "阅读 1 篇", "精翻 1 段"],
        "weekday_b_items": ["背词 30", "阅读 1 篇"],
        "weekday_c_items": ["背词 20"],
        "weekend_a_items": ["背词 30", "阅读 2 篇", "精翻 1 段", "作文 1 篇"],
    }
    decomp = build_decomposition(demo_goal, skeleton)
    print(f"✓ 拆解完成：{decomp['meta']['title']}")
    print(f"  阶段数: {len(decomp['stages'])}")
    print(f"  每日任务条数: {len(decomp['daily_tasks'])}")
    print(f"  首日 ABC 时长: A={decomp['daily_tasks'][0]['tasks'][0]['abc_levels']['a']['minutes']}分钟"
          f", B={decomp['daily_tasks'][0]['tasks'][0]['abc_levels']['b']['minutes']}分钟"
          f", C={decomp['daily_tasks'][0]['tasks'][0]['abc_levels']['c']['minutes']}分钟")
    print(f"  Anti-Goals: {decomp['meta']['anti_goals']}")
    print(f"  If-Then 数: {len(decomp['meta']['if_then_plans'])}")
