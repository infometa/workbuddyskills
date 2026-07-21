# goal-decomposition · 拆解方法论手册

> plan-tracker 的"目标拆解"是一等公民能力，不依赖 study-planner。
> 本文档定义拆解的**对话流程**、**输出结构**、**反模式**——AI 在用户说"帮我拆"时严格按此执行。

---

## 1. 何时触发拆解

### 触发词清单

```
帮我拆 / 拆解一下 / 帮我规划 / 帮我安排 / 给我安排一下
我想搞定 X / 我要在 N 天内 X / N 天 X
制定计划 / 做个计划 / 规划下 / 帮我做个 plan
没思路 / 不知道从哪开始 / 不知道每天该做什么
```

### 不触发拆解的场景

- 用户已有 active plan（用 `today.py` 看任务即可）
- 用户问"今天学什么"（走 NEVER 6 分支）
- 用户想改已有 plan（走 `task_edit.py`）

---

## 2. 拆解对话的 5 步法

### Step 1 · SMART 澄清（5 个问题，60 秒）

**严禁**直接开拆——必须先把"我想搞定 X"变成 SMART：

```
S (Specific):    具体要搞定什么？  →  goal.title
M (Measurable):  验收标准是什么？   →  goal.specific（如"真题 65 分"，不能是"学好"）
A (Achievable):  每天能投入多少？   →  goal.daily_minutes (weekday/weekend)
R (Relevant):    （可省略）这事和你更大的目标什么关系？
T (Time-bound):  截止日是哪天？     →  goal.deadline
```

**WHY**：模糊的目标拆出来一定是模糊的任务。"我要变厉害"→ 拆不出每日动作；"60 天内英二真题 65+"→ 才能反推每天 90 min 该干嘛。

### Step 2 · 起点校准（防"画大饼"）

补一个起点问题：

```
你目前真实水平如何？（做过什么、错率多少、有什么基础）  →  goal.current_level
```

用于校准可达性。如果用户说"零基础"+ "60 天考研"，**主动告知风险**而非沉默拆解。

### Step 3 · Anti-Goals（拒绝什么，关键差异化能力）

主动问：

```
你有什么不愿意为这个目标牺牲的？
（睡眠 / 锻炼 / 家人时间 / 周末完全休息……）
```

这一步是 plan-tracker 区别于市面上其他拆解工具的**核心创新**。  
写入 `meta.anti_goals[]`，最多 10 条。

**WHY**：传统拆解只问"你要什么"，导致用户为了完成计划牺牲一切——结果 2 周后崩溃。明确 anti-goals = 给目标设护栏。

### Step 4 · 每日 ABC 三档骨架

不要直接给"每天 90 分钟做 X"的单版本——必须给三档：

```
🅰️  完美档（90min）：背词 30 + 阅读 1 篇 + 精翻 1 段
🅱️  基础档（55min）：背词 30 + 阅读 1 篇
🆎 最低档（10min）：背词 20 ←  累的时候做这个，streak 不断
```

**ABC 时长规则**（来自 `decompose.compute_abc_minutes`）：

| 档 | 比例 | 备注 |
|----|------|------|
| A | 100% × budget | 跑满预算 |
| B | 65% × budget | 砍掉最低优先级项 |
| C | max(5, min(15, 15% × budget)) | **绝对硬上限 15 min**，"短到无法拒绝" |

C 档的设计依据是**2 分钟法则**（James Clear · 原子习惯）：开始做远比"做多少"更难。背 5 个词的人，往往会顺手再背 20 个。

### Step 5 · If-Then 障碍预演

收尾问：

```
如果出现以下情况，你打算怎么办？
- 加班到 21 点后  →  ?
- 连续 3 天落后    →  ?
- 突然超额完成（防疲劳） →  ?
```

允许用户选"用默认应急方案"（plan-tracker 兜底）：

```json
[
  { "if": "加班到 21 点后",  "then": "只做 C 档",  "trigger_kind": "low_energy" },
  { "if": "连续 3 天落后",   "then": "削减最弱模块的 30%", "trigger_kind": "fall_behind" },
  { "if": "提前完成本周",    "then": "周末完全休息一天",   "trigger_kind": "over_pressure" }
]
```

**WHY**：障碍预演（implementation intentions）的心理学效应——预先设定的应急方案，执行成功率比临场决策高 2-3 倍（Gollwitzer 1999）。  
写入 `meta.if_then_plans[]`；`revive.py` 在断签时会**优先匹配预案**而非默认重排。

---

## 3. 拆解的输出结构

调用 `decompose.build_decomposition(goal, daily_skeleton)`，得到：

```python
{
    "meta": {...},          # 含 anti_goals / if_then_plans / okr_phases / current_level
    "stages": [...],        # phase 列表（自动按 30 天切）
    "daily_tasks": [...],   # 每日任务，含 abc_levels
}
```

随后 `init_plan.save_plan()` 落盘到 `<cwd>/.plan-tracker/plans/<plan-id>/`。

### 标准 plan_id 命名

```
plan-YYYYMMDD-<slug>
例：plan-20260512-kaoyan-en2
    plan-20260512-考研英语二-65（中文也支持）
```

冲突时自动追加 `-v2 / -v3`（init_plan._resolve_unique_dir）。

---

## 4. AI 调用方式

### 方式 A：JSON 一次性传入（推荐生产）

```bash
python3 init_plan.py --goal-json /tmp/goal.json --skeleton-json /tmp/skel.json
```

`goal.json`：

```json
{
  "title": "考研英语二 65+",
  "specific": "真题英二平均 65 分",
  "deadline": "2026-07-15",
  "current_level": "四级 480",
  "daily_minutes": { "weekday": 90, "weekend": 180 },
  "anti_goals": ["晚于 23:30 睡", "周末完全不休"],
  "if_then_plans": [
    { "if": "加班到 21 点后", "then": "只做 C 档", "trigger_kind": "low_energy" }
  ],
  "weak_points": ["长难句", "细节定位题"],
  "resources": ["黄皮书 2010-2024"]
}
```

`skel.json`（可选；不提供则用通用骨架）：

```json
{
  "weekday_a_items": ["背词 30", "阅读 1 篇", "精翻 1 段"],
  "weekday_b_items": ["背词 30", "阅读 1 篇"],
  "weekday_c_items": ["背词 20"],
  "weekend_a_items": ["背词 30", "阅读 2 篇", "精翻 1 段", "作文 1 篇"]
}
```

### 方式 B：命令行参数（手动测试）

```bash
python3 init_plan.py \
    --title "考研英语二 65+" \
    --specific "真题英二平均 65 分" \
    --deadline 2026-07-15 \
    --current-level "四级 480" \
    --weekday-min 90 --weekend-min 180 \
    --anti-goals "晚于23:30睡,周末完全不休"
```

### 方式 C：Python 直接调用

```python
from init_plan import init_plan, save_plan
plan = init_plan(goal_dict, skel_dict)
plan_path = save_plan(plan)
```

---

## 5. 拆解对话示例（温柔学姐人设）

```
用户：我想 60 天搞定考研英语二，目前四级 480

AI：好，我们一起把它拆成每天能干的事。先 5 个问题（60 秒）：
   ①【验收标准】你希望 60 天后达到什么具体水平？（如"真题英二 65+"）
   ②【截止日】最晚交卷哪天？
   ③【时间预算】每天能投入多少分钟？工作日 vs 周末分开说
   ④【起点】当前真实水平？（做过什么、错率多少）
   ⑤【护栏】有什么不愿牺牲的？（睡眠 / 运动 / 家人时间……）

用户：65 分；7 月 15 日；工作日 90 分钟周末 180 分钟；做过 4 套真题英一阅读错率 50%；
     不能熬夜超过 23:30，周末必须留半天给家人

AI：拆好了 ✓
   📐 SMART：英二真题 65+，截止 2026-07-15
   🎯 OKR 阶段（自动按 30 天切，3 个 phase）：
       M1 词汇+阅读基础 / M2 真题强化 / M3 模考冲刺
   ⚡ 每日 ABC（工作日 90 min）：
      🅰️ 90min：背词 30 + 阅读 1 篇 + 精翻 1 段
      🅱️ 55min：背词 30 + 阅读 1 篇
      🆎 10min：背词 20  ← 累的时候做这个 streak 不断
   🛡️ 反目标：晚于 23:30 睡 / 周末完全不休
   🆘 If-Then：
      If 加班到 21 点 → 只做 C 档
      If 连续 3 天落后 → 削减最弱模块 30%

   写入 .plan-tracker/plans/plan-20260512-考研英语二-65/plan.json ✓
   下一步：跑「今日任务」就能开始打卡。
```

---

## 6. 反模式（参见 NEVER 9）

详见 `references/never-rules.md` NEVER 9 完整四条：

1. **拆解过粗**：直接给"每天背词阅读"，没量化没时长
2. **不给 C 档**：只有完美版 → 用户累一天就断签
3. **不问 anti-goals**：拆出"凌晨 1 点学到 3 点"的疯狂计划
4. **跨度爆炸**：把 365 天目标硬塞进 plan-tracker（应建议用户拆首阶段）

---

## 7. 与 study-planner 的边界

| 对比 | study-planner | plan-tracker（本 skill） |
|------|---------------|--------------------------|
| 拆解路径 | 模板路线（雅思/托福/考研... 模板填空） | 对话路线（SMART → OKR → ABC 通用） |
| 适用场景 | 学科类、有成熟备考路径的目标 | **任意目标**（学习/健身/写作/技能/项目） |
| ABC 三档 | ❌ 单版本任务 | ✅ A/B/C 三档每日任务 |
| Anti-Goals | ❌ | ✅ |
| If-Then | ❌ | ✅ |
| Streak/打卡/热力图 | ❌（仅生成 plan） | ✅ 完整闭环 |

> 当用户目标是"考研/雅思/托福"等明确学科时，可建议先用 study-planner 出大盘 plan.json，再用 plan-tracker 跑日常陪伴；其他场景直接用 plan-tracker 拆解即可。
