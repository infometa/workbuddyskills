---
name: xuanxing-training-admin
description: Management view of training projects and plans on 绚星 (Xuanxing), for users who run training - a project's current status and task outline, who is falling behind, and annual training plan completion for reporting upward. Use when the user asks 这个项目现在什么情况 / 项目跑得怎么样 / 谁拖后腿 / 谁没完成 / 年度培训完成率 / 我要汇报培训情况. Requires管理者 permission; it returns other people's data.
description_en: Management view of Xuanxing training projects and plans - project status and outline, who is behind, and annual plan completion for reporting. Requires manager permission and returns other people's data.
description_zh: 培训管理者视角：查看绚星培训项目的进展与任务大纲、谁没完成，以及年度培训计划完成率，需要管理权限。
allowed-tools:
disable: false
version: 1.0.2
author: 绚星
---

# 项目与计划运营（管理端）

## 前置

先读 `xuanxing-shared`，确认连接与授权。

⚠️ **本技能返回的是他人数据**，需要管理者权限。权限由服务端强制校验，
没权限会返回 `FORBIDDEN` —— 此时如实告知，**不要重试、不要换参数绕**。

## 何时使用

- 「我负责的这个项目现在什么情况」「跑成什么样了」
- 「XX 项目大家完成得怎么样」「哪个任务通过率低」「哪个环节卡住了」
- 「谁拖后腿」「谁还没完成」
- 「年度培训做得怎么样」「我要向上汇报」

⚠️ 注意区分「**这个项目大家**完成得怎么样」（本技能，管理端汇总）和
「**我**在这个项目完成得怎么样」（`xuanxing-study-progress`，学员本人视角）。
问法很像，数据完全不同。

## 何时不要使用

| 用户想问 | 用哪个 |
|---|---|
| **我自己**的学习进度 | `xuanxing-study-progress` |
| **我自己**的待办 | `xuanxing-study-todo` |
| 待批阅的考试 / 作业（教学视角） | `xuanxing-teaching-todo` |

**判别要点**：用户说「我的项目」时要分清是**我在学的**还是**我在管的**。
不确定就问一句：「你是想看自己的学习进度，还是这个项目整体的推进情况？」

## 调用流程

**问某个项目的情况**

1. 调 `get_project_overview`，用**项目名称**检索 —— 它支持按名字模糊搜，
   不需要先取 ID
2. 匹配到多个项目时列出来**问用户**是哪一个
3. 一个都没匹配上，如实说没找到
4. **拿到 `project_id` 后必须再调一次 `get_project_overview(project_id=...)`**
   （明细模式），把 `outline`（任务大纲）、`is_overdue`（是否已截止）、
   `student_count`、学分/积分/证书汇总一并给出。⛔ **不许说"接口不展开"
   或"这部分要到项目页看"就跳过大纲**——明细模式已经按阶段给了大纲
   （`outline[].item_count`），不存在"展不展开"这回事，只有调没调这一步

⚠️ **不要自己传 `scope`。** 默认 `auto` 已经把「我创建的 / 我负责的 / 我管辖的」
三个范围都查过并合并去重了（`meta.scopes_queried`）。
手动指定一个范围反而会漏 —— 同一个项目可能在 `owned` 下查不到、在 `managed` 下才有。

⚠️ 即便三个范围都查过，没找到时也**只能**说「我在你创建/负责/管辖的项目里没找到」，
**不许**说「平台上没有这个项目」—— 它可能只是不归这个人管。

⚠️ `meta.paging_suspect` 为 true 时，返回的条数被上游静默截短了，
**不要**把这几条当成「全部匹配结果」，要说明只看到了一部分。

⚠️ `auto` 时**没有** `meta.total` —— 三个范围有重叠，加起来是个假数字。
每个范围各自的总数在 `meta.total_by_scope` 里，要说总数就说清是哪个范围的。

**问这个项目大家完成得怎么样 / 哪个任务卡住了** → `get_project_task_completion`

⚠️ 它要 `project_id`，用户给的是名字，所以同样是两步：
先 `get_project_overview` 按名字拿到 `project_id`，再调它。

它按**阶段 → 任务**两层返回，每个任务给通过人数、通过率、积分、学分。
这是**全项目所有学员的汇总**，不是某个人的进度：

| 用户想问 | 用哪个 |
|---|---|
| 这个项目大家完成得怎么样、哪个任务通过率低 | `get_project_task_completion` |
| **谁**没完成（要名单） | `list_project_member_progress` |
| **我自己**在这个项目的进度 | `xuanxing-study-progress` 的 `get_my_project_progress` |

**问年度培训 / 计划完成情况** → `get_training_plan_summary`

平台「培训规划 → 培训计划」页有**两个独立的页签**——**组织培训计划**和**个人培训计划**，
是**两个不同的计划集合**（个人 = 员工的个人发展计划，不是组织计划的子集）。工具把它们
分开返回在 `data.organization` / `data.personal`，每块都带：`label`（与平台页签同名）、
`page_url`（该页签的平台页面地址）、`statistics`（全量统计）、`plans`（前 `limit` 条，上限 20）。

- **数字一律读 `statistics`**（计划数、完成数、延期数、进行中 / 已结束 / 未开始数、下挂项目数）——
  服务端聚合的全量值，与平台页面统计条同口径。**不要**数 `plans` 的条数，它只是前 20 条；
  `truncated=true` 时要说「共 N 个，这里列出前几个」。
- **两个页签分开讲、各给各的数**：不要相加成一个总数，也不要只报其中一个，
  更不要说「这是我管辖范围内的」之类自创的范围。用户只问其中一个时传
  `scope=personal` 或 `scope=organization`，不问就默认两个都给。
- **问「年度」**（「年度培训」「今年」「2026 年度」）→ 传 `year`。它**只作用于组织页签里该年度的
  年度计划**，个人页签不分年度、不受影响——回答里要把这个范围说清；不传 `year` 时是全部计划，
  **不要**把它说成年度数据。
  用了 `year` 且得到 0 个时，先对照 `meta.current_year`（服务器按北京时间算的当前年份）确认没传错年份，
  **不要**直接说「今年没有年度计划」。
- 筛选后一个都没有时，`statistics` 的计数是 **0**（上游此时给全 null，工具已按列表的 0 条归零），
  这就是真的「没有」；比例（`*_rate_percent`）为 null 是因为没有分母，不要说成 0%。
- 某一块带 `error` / `statistics_error` / `plans_error` 时，那一块**没取到**，不是 0、也不是「没有」：
  如实说是哪一块没查到，另一块照常给。整体失败时顶层 `errors` 里有每个页签各自的原因，要分别说
  （比如一个没权限、另一个只是暂时不可达——后者值得重试）。
- 某一块带 `count_mismatch` 时，`statistics.plan_count` 与列表总数对不上（两次调用之间数据变了，
  或上游没按同一条件筛）：两个数都如实说，不要挑一个当真。
- 回答里带上各页签的 `page_url`，方便对照平台页面核对（需要管理后台权限才能打开）。
- 筛选（执行状态 `running_status`、`delayed_only`、名称 `keyword`、`year`）都是上游筛选，
  `statistics` 与 `plans` 用同一个条件，数字对得上。
- `related_project_count` 是计划下挂的培训项目数；已完成项目数 `finished_project_count`
  **只有组织计划行有**，个人计划行没有。要项目叫什么名字才传 `include_projects=True`
  （真正的 N+1，用户问到具体项目名才开）。

**问谁拖后腿** → `list_project_member_progress`

⚠️ 它要 `project_id`，而用户给的是**项目名字**。必须两步：

1. **先**调 `get_project_overview`，用项目名称检索，拿到 `project_id`
2. **再**调 `list_project_member_progress`
3. 名字匹配到多个项目时**问用户**，不要挑一个就查

想只看没完成的人，传 `complete_status=1`（未开始）或 `2`（学习中），
**不要**自己拿完成率去筛。

拿到 `FORBIDDEN`「你不是部门经理或直属经理」时，如实说没有团队管理身份 ——
这和「没有人落后」是两回事，**绝不能**说成后者。

## 输出规范

- 汇报类问题（「向上汇报」）要给**结论先行**：整体完成率是多少、
  有几个计划延期、最需要关注的是哪个。再给明细。
  ⛔ **数据已经查到了就直接给答案，不要反问"是要汇报个人学习还是所管计划"
  "要 Word/PPT/Excel 哪种格式"**——查完数据后卡在这类问题上，
  等于没给出汇报内容。默认按**管理端视角**（本技能查的
  就是这个）、默认用**聊天里的文字 + 表格**呈现，用户没要求导出文件就不要主动问。
- ⚠️ **「计划信息 + 培训项目完成情况」两部分缺一不可**——统计里的
  `related_project_count` 和组织计划行的 `finished_project_count` 已经随结果给了，
  直接展示即可。要讲**具体项目**（个人计划行没有已完成项目数）时，对要重点说的几个计划传
  `include_projects=True` 取项目清单，再用 `get_project_task_completion`（按 `project_id`）
  看各项目的完成情况。计划数多于个位数时只展开**延期或完成率低**的那几个计划细说，
  不要每个计划都展开成一大段，但**不能一个都不提项目完成情况**。
- 计划列表要标出**延期**的；`is_overdue` 是代码算好的，不要自己拿
  `end_time` 减当前日期心算。
- 涉及具体人员时，只给完成情况相关的字段，**不要**附带其他个人信息。
- 数字一律来自工具返回，**不要自己算平均值、同比、环比**。

### 项目任务完成情况怎么展示（`get_project_task_completion` 的结果）

开头一句交代范围，然后**按阶段分段，每段一张表**。表头固定这四列：

```markdown
**示例项目** · 共 200 名学员 · 2 个阶段 3 个任务

#### 阶段一（2 个任务）

| 任务 | 通过 | 通过率 | 积分 / 学分 |
|---|---|---|---|
| 任务 A（必修） | 150/200 | 75.00% | 10 / 2 |
| 任务 B | 96/200 | 48.00% | — |

#### 阶段二（1 个任务）

| 任务 | 通过 | 通过率 | 积分 / 学分 |
|---|---|---|---|
| 任务 C | 12/200 | 6.00% | — |
```

填表规则：

| 列 | 取值 |
|---|---|
| 任务 | `name`；`required` 为真加 `（必修）` |
| 通过 | `passed` **原样**（已是 `"12/200"` 这种格式） |
| 通过率 | `pass_rate` **原样**（已是 `"6.00%"`） |
| 积分 / 学分 | `points / credits`；**两个都是 0 就写 `—`** |

⚠️ **`passed` 和 `pass_rate` 是上游算好的字符串，原样贴。**
不要自己用分子分母重算百分比 —— 分母是项目学员数，我们这儿没有更准的口径。

⚠️ **`has_stages` 为 false 时不要写阶段小标题。** 那说明项目没分阶段，
`stages[0].name` 是 `null`，直接给一张表就行，别写成「阶段 None」。

⚠️ **空阶段照实说。** `tasks` 为空数组是真的没挂任务，
写成 `#### <阶段名>（0 个任务）` 一行带过，或直接略过 —— 但**不要**说「查不到」。

⚠️ 阶段很多（超过 5 个）时，先给一张**阶段汇总表**（阶段名 + 任务数 +
该阶段平均通过率**如果工具给了的话**），再问用户看哪个阶段的明细 ——
几十个任务铺开就是几十行，一屏放不下。
**工具没给阶段级平均值，就不要自己算**（数字只能来自工具返回）。

⚠️ 通过率低不等于"有问题"。可以客观指出「X 任务通过率最低（6.00%）」，
**不要**替用户下「这个任务设计有问题」「需要催办」这类结论。

### 已知限制（照实说，不要编）

> ⚠️ 本表是**预期管理**，不是本次调用的观察结果。
> 照实回答要以工具返回的 `not_available` 为准（见 `xuanxing-shared` 的「说查不到」硬规矩）。
> **没调过的工具，不要替它声明限制。**

| 用户可能会问 | 现状 | 你该怎么回答 |
|---|---|---|
| 谁拖后腿（**具体到人**） | 用 `list_project_member_progress` | 按上面「问谁拖后腿」的两步查；返回 `FORBIDDEN` 就如实说没有团队管理身份 |
| 这个计划下面挂了哪些项目 | 默认只给 `related_project_count` | 传 `include_projects=True` 取清单；本次返回里没有就说需到平台看 |

**绝不要**因为没取到成员明细（`FORBIDDEN` 或调用失败），就用项目完成率去推断
「谁没完成」——那是编造。

## 错误处理

按 `xuanxing-shared` 的错误码表。特别注意：

- `FORBIDDEN`：说明用户对这个项目没有管理权限。如实说，
  **不要**改成查自己的数据来「凑一个答案」。
- 项目存在但没有成员数据时返回空，不是错误。
