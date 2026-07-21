# data-schema · 数据结构定义

> 所有数据文件存放于 `<cwd>/.plan-tracker/plans/<plan-id>/`
> 所有读写必须全本地，绝不调用外网 API（见 NEVER 5）

---

## plan.json

学习计划主文件，由 `init_plan.py` 写入（plan-tracker 自有拆解）或用户手动上传。所有读取脚本（`today.py / checkin.py / stats.py / revive.py / streak.py / dashboard.py`）共享此契约。

### Schema v2（plan-tracker 拆解版）完整示例

```json
{
  "id": "plan-20260512-kaoyan-en2",
  "version": 2,
  "schema": "plan-tracker.v2",
  "meta": {
    "title": "考研英语二 65+",
    "goal": "做对真题英二平均 65 分以上",
    "deadline": "2026-07-15",
    "start_date": "2026-05-12",
    "current_level": "四级 480，没系统做过英二",
    "daily_budget": { "weekday": 90, "weekend": 180 },
    "weak_points": ["长难句分析", "细节定位题"],
    "resources": ["黄皮书 2010-2024", "考研真相英二"],
    "methodology": ["smart", "okr", "abc-tiers", "anti-goals", "if-then"],
    "anti_goals": ["晚于 23:30 睡", "周末完全不休息"],
    "if_then_plans": [
      { "if": "加班到 21 点后", "then": "只做 C 档", "trigger_kind": "low_energy" },
      { "if": "连续 3 天落后", "then": "削减最弱模块的 30%", "trigger_kind": "fall_behind" }
    ],
    "okr_phases": [
      {
        "phase_id": "phase-1",
        "phase_range": "2026-05-12 ~ 2026-06-10",
        "objective": "M1: 词汇 + 阅读基础",
        "key_results": [
          { "kr": "完成核心 5500 词第一轮", "target": 5500, "unit": "词", "current": 0 },
          { "kr": "刷完真题 2010-2014",   "target": 5,    "unit": "套", "current": 0 },
          { "kr": "阅读正确率提升至 60%", "target": 60,   "unit": "%",  "current": 40 }
        ]
      }
    ],
    "decomposed_by": "plan-tracker.decompose v1.0",
    "decomposed_at": "2026-05-12 11:30:00"
  },
  "stages": [
    {
      "id": "phase-1",
      "name": "阶段 1",
      "duration_days": 30,
      "start_date": "2026-05-12",
      "end_date": "2026-06-10",
      "goals": ["M1: 词汇 + 阅读基础"]
    }
  ],
  "daily_tasks": [
    {
      "date": "2026-05-12",
      "stage_id": "phase-1",
      "tasks": [
        {
          "id": "t-001",
          "title": "考研英语二 65+ · 主任务",
          "duration_min": 90,
          "category": "review",
          "priority": "high",
          "checkable": true,
          "abc_levels": {
            "a": { "items": ["背词 30", "阅读 1 篇", "精翻 1 段"], "minutes": 90 },
            "b": { "items": ["背词 30", "阅读 1 篇"],             "minutes": 55 },
            "c": { "items": ["背词 20"],                            "minutes": 10 }
          },
          "_origin": "decompose"
        }
      ]
    }
  ]
}
```

### meta 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 目标短标题（≤ 30 字） |
| `goal` | string | ✅ | SMART 的 M（Measurable 验收标准） |
| `deadline` | `YYYY-MM-DD` | ✅ | SMART 的 T；距 `start_date` ≤ 180 天（NEVER 9） |
| `start_date` | `YYYY-MM-DD` | ✅ | 计划起始日 |
| `current_level` | string | ⚪ | 当前水平描述（拆解时校准可达性） |
| `daily_budget` | `{weekday:int, weekend:int}` | ✅ | 每日可投入分钟数（0-600） |
| `weak_points` | `string[]` | ⚪ | 薄弱知识点（用于优先排程） |
| `resources` | `string[]` | ⚪ | 资源清单（教材、视频、题库） |
| `methodology` | `string[]` | ⚪ | 应用的方法论标签 |
| `anti_goals` | `string[]` | ⚪ | **拒绝牺牲什么**（最多 10 条，每条 ≤ 50 字） |
| `if_then_plans` | `Object[]` | ⚪ | 障碍预演（最多 8 条），结构见下 |
| `okr_phases` | `Object[]` | ⚪ | 月度 OKR（自动按 30 天切分） |

### task.abc_levels 字段说明（核心创新）

ABC 三档对应 habits-and-goals 的 Ambitious/Baseline/Comeback 设计：

| 档位 | items 数量建议 | minutes | 用途 |
|------|---------------|---------|------|
| `a` | 3-5 项 | = `daily_budget` | 状态好、有大块时间 |
| `b` | 2-3 项 | ≈ `budget × 65%` | 普通工作日 |
| `c` | 1-2 项 | 5-15 分钟（**绝对硬上限 15 min**） | 加班/生病/心情差时的"保命档" |

**核心承诺**（NEVER 9 第 2 条）：A/B/C 任意一档完成都算 streak **不断**，因此 C 档必须**短到无法拒绝**。

### if_then_plans 字段说明

每条结构：

```json
{ "if": "加班到 21 点后", "then": "只做 C 档", "trigger_kind": "low_energy" }
```

`trigger_kind` 取值（供 `revive.py` 匹配预案）：

- `low_energy` — 体力不支
- `fall_behind` — 进度落后
- `over_pressure` — 超额完成防疲劳
- `external_block` — 外部阻碍（出差/生病/家事）
- `general` — 通用（未指定）

### 向后兼容（Schema v1）

老的 plan.json（无 `version` 字段或 `version: 1`）：
- 没有 `abc_levels` / `anti_goals` / `if_then_plans` / `okr_phases`
- `today.py` 渲染时静默跳过 ABC 块（仅显示单版本任务）
- `checkin.py` 不接受 `--level`，按 25 分钟/任务估算 duration

> 升级路径：用户上传老 plan 后，可手动跑 `init_plan.py --upgrade <plan-id>`（v1.1 计划支持）将其升到 v2 schema。

---

## checkin-log.json

打卡记录文件，由 `checkin.py` 写入，供 `streak.py` / `stats.py` / `dashboard.py` 读取。

```json
{
  "plan_id": "plan-20260506-ielts-65",
  "checkins": [
    {
      "date": "2026-05-07",
      "task_ids": ["t-001", "t-002"],
      "duration_min": 60,
      "status": "done",
      "mood": "great",
      "note": "听力提前完成了，口语有点卡",
      "created_at": "07:30"
    },
    {
      "date": "2026-05-08",
      "task_ids": ["t-003"],
      "duration_min": 25,
      "status": "partial",
      "mood": "tired",
      "note": "今天状态一般，只做了阅读"
    }
  ]
}
```

### 字段说明（NEVER 2 低摩擦原则）

除 `date` / `task_ids` 必填外，其余字段**全部选填**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | `YYYY-MM-DD` | ✅ | 打卡日期 |
| `task_ids` | `string[]` | ✅ | 完成/部分完成的任务 ID |
| `duration_min` | `int` | ⚪ | 实际耗时；缺省按 `level` 取 abc_levels.minutes，无 level 则按每任务 25min 估算 |
| `status` | `enum` | ⚪ | `done`(完成) / `partial`(部分完成) / `missed`(未完成)，缺省 `done` |
| `level` | `enum` | ⚪ | `a` / `b` / `c`（ABC 档位）；任意一档完成都算 streak 不断（NEVER 9 第 2 条） |
| `mood` | `enum` | ⚪ | `great` / `ok` / `tired` / `bad`，**仅在用户主动 `--mood` 时记录** |
| `note` | `string` | ⚪ | 一句话备注，≤ 200 字符 |
| `created_at` | `"HH:MM"` | ⚪ | 打卡时间，用于 weekday × timeslot 诊断 |

> 🔒 **NEVER 2 重申**：CLI 不会主动弹问 mood/status/duration/note/level，全部需用户显式 `--mood / --status / --duration / --note / --level`。默认 `checkin --tasks t-001` 仍只写最小字段，零摩擦。
>
> 🆎 **Two-Day Rule**（NEVER 9 第 3 条）：当本次 `level=c` 且历史最后一条非今日 checkin 也是 `level=c` 时，`checkin.py` 会输出"Two-Day Rule 警告"——不阻塞打卡，仅提醒"明天试试 B 档"。

---

## streak.json

Streak 状态 + 成就 + 瓶颈任务，由 `streak.py` / `stats.py` 写入，供所有展示脚本读取。

```json
{
  "plan_id": "plan-20260506-ielts-65",
  "current": 12,
  "longest": 28,
  "last_checkin": "2026-05-18",
  "broken_dates": ["2026-05-15"],
  "milestones_unlocked": [7, 30],
  "achievements": [
    {
      "id": "early_bird",
      "name": "早起鸟",
      "unlocked_at": "2026-05-10",
      "description": "连续 7 天在 8 点前开始学习"
    }
  ],
  "bottleneck_tasks": [
    {
      "task_id": "t-speaking-daily",
      "title": "口语录音 P2 话题",
      "category": "speaking",
      "miss_count": 5,
      "last_missed": "2026-05-17"
    }
  ],
  "bottleneck_updated_at": "2026-05-18 10:32:11"
}
```

### bottleneck_tasks 自动持久化（`stats.py` 写入）

- 每次跑周报 / 月报时，`compute_bottleneck_tasks` 会扫描过去 14 天内 miss 次数 ≥ 3 的 checkable 任务，写入 `streak.bottleneck_tasks`（最多 5 条，按 miss_count 倒序）
- 下游 Agent 可直接读 `streak.json.bottleneck_tasks`，**无需重复扫描** plan + checkin-log

---

## user-config.json

用户配置，由 plan-tracker 写入和读取。

```json
{
  "persona": "gentle-senior",
  "active_plan_id": "plan-20260506-ielts-65",
  "checkin_channel": "daily",
  "reminder_time": "09:00",
  "revive_threshold_days": 2,
  "do_not_disturb": {
    "start": "22:00",
    "end": "08:00"
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `persona` | `string` | 是 | 4 选 1：`gentle-senior` / `strict-coach` / `humorous-buddy` / `zen-master` |
| `active_plan_id` | `string` | 是 | 当前激活的计划 ID（plan-tracker 写入或用户上传） |
| `checkin_channel` | `enum` | 是 | `daily`（每日推送）/ `pull`（仅主动查看） |
| `reminder_time` | `"HH:MM"` | 是 | 每日提醒时间（仅 channel=daily 生效） |
| `revive_threshold_days` | `int` | 否 | 断签提醒阈值（天数），范围 [1, 7]；默认 **2**（连续 2 天未打卡触发温和提醒） |
| `do_not_disturb` | `object \| null` | 否 | 免打扰时段，默认 `null` 不启用 |
| `do_not_disturb.start` | `"HH:MM"` | — | 静默开始时间 |
| `do_not_disturb.end` | `"HH:MM"` | — | 静默结束时间，支持跨午夜（如 22:00 → 08:00） |

### 免打扰生效规则（见 `scripts/_plan_utils.py::is_quiet_hours`）

1. 落入 `[start, end)` 时段内，`today.py / streak.py` 的输出会被 `silence_if_quiet` 降级——去除 emoji、仅保留首行简讯，前缀加 `[quiet]`
2. `start <= end` 视为同日窗口（如 12:00 → 14:00 午休）；`start > end` 视为跨午夜窗口（如 22:00 → 08:00 夜间）
3. 字段缺失或 HH:MM 格式非法 → 静默时段功能不生效（向后兼容）
4. `checkin.py` **不受免打扰影响**（用户主动操作）

