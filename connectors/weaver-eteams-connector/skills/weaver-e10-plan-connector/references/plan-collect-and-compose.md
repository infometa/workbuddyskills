# 汇总生成报告：多模块数据采集作业链

## 何时使用

意图判定为 **A 生成链路**（汇总 / 生成 / 写 / 整理 + 周期词 + 报告类名词，且未命中查询类信号）时，读取本 reference 并按步骤链完整执行，**禁止跳步、禁止二次询问是否开始采集**。

## 技能调用对应关系（数据来源唯一指定）

凡是已安装对应模块的技能，**必须且只能**调用下表中给定的技能获取数据，严禁跳过，也严禁改用指定技能之外的其他技能；无相关数据的模块可不做统计、汇总与分析。

| 数据类别 | 唯一指定技能 |
| --- | --- |
| IM 消息 | `weaver-e10-yimiaoban-connector` |
| 客户、联系人、商机、线索 | `weaver-e10-jiuchuanhui-connector` |
| 项目、任务 | `weaver-e10-shijingran-connector` |
| 日报 | `weaver-e10-blog` |
| 日程 | `weaver-e10-calendar-connector` |
| 会议 | `weaver-e10-meeting-connector` |
| 流程 | `weaver-e10-workflow-connector` |

技能调用名一律使用已安装技能 frontmatter 的 `name` 字段（个别技能目录名可能带 `__skillhub` 等后缀，以 `name` 为准）。人员姓名与人员 ID 解析使用 `weaver-e10-hrm-connector`。

## 作业步骤链

### Step 0 前置准备（禁止调用任何报告接口）

- 若尚未确认登录态，先按共享规则读取 `../weaver-e10-shared-connector/references/e10-auth-and-session.md` 并通过 `weaver-work-cli auth ...` 确认会话（Cookie 完整原始串 + eteamsid + User-Agent 三件套，缺一不可）。
- 根据用户表述计算报告周期时间范围（周报遵循 ISO8601，例如「上周」= 上周一至上周日）；未明确周期类型时先向用户确认周/月/季/年，确认前不得臆造区间。
- 确定数据归属主体：默认当前登录人本人；若判定涉及他人且已获用户确认，则主体为该人。

### Step 1~7 依序采集周期内数据

顺序可调，但每个已安装模块都必须采集，不得因顺序原因遗漏。每个技能加载后按其自身 SKILL.md 与接口文档执行，**不要在本技能内自行构造该模块的 HTTP 请求**。

| Step | 模块 | 采集内容与筛选规则 |
| --- | --- | --- |
| 1 | IM 消息（`weaver-e10-yimiaoban-connector`） | 仅统计发言时间落在周期内、本人发送的全部单聊与群聊消息内容，且必须完全统计不能只统计一部分。若某群聊中不含本人实际发言的消息，则不统计该群聊 |
| 2 | 日报（`weaver-e10-blog`） | 仅筛选周期内本人提交的日报内容 |
| 3 | 日程（`weaver-e10-calendar-connector`） | 本人为创建人或参与人，且日程开始时间、结束时间任意一项落在周期内的日程；**排除请假类型日程** |
| 4 | 会议（`weaver-e10-meeting-connector`） | 本人为创建人或参会人，且会议开始时间、结束时间任意一项落在周期内的会议 |
| 5 | 项目、任务（`weaver-e10-shijingran-connector`） | 本人为创建人、负责人或参与人，且创建时间、完成时间均在周期内的项目与任务 |
| 6 | 客户/联系人/商机/线索（`weaver-e10-jiuchuanhui-connector`） | 仅统计创建时间落在周期内的相关数据 |
| 7 | 流程（`weaver-e10-workflow-connector`） | 本人创建的流程，以周期内创建时间为准；非本人创建的流程，仅统计与本人岗位相关且本人实际批准处理的流程；**待办、转办、知会、请假类流程不予统计**。汇总需结合表单内容、流转意见、签字意见归纳分析 |

**失败兜底（严格执行）**

- Step 1~7 中任一已安装技能调用失败或返回错误 → 停止采集并向用户说明是哪个模块失败；不得跳过该模块、不得改用其他技能、不得直接调用该模块 HTTP 接口、不得静默继续生成。
- 若确认某模块技能未安装 → 告知用户该模块无数据来源，由用户决定是否安装后重试，不得静默忽略。
- 查不到数据即该模块记为空，不影响其它模块继续。

### Step 8 汇总润色

按输出规范整合 Step 1~7 的数据，形成分节内容稿。禁止堆砌原始数据、禁止出现计数统计类内容。

### Step 9 呈现并确认

把汇总润色后的内容直观呈现给用户，并提示「是否生成对应周期的报告」，等待用户确认。

### Step 10 重复性检查与创建

用户确认后：

1. 先调用 `plan.report.get` 按周期（报告年份 + 报告类型 + 报告周期，创建人取当前登录人）判断该周期报告是否已存在——**此时才允许触发版本路由与报告侧接口**。
2. 已存在 → 不得重复创建，明确告知用户并征询是否改为编辑（改走 `plan.report.update.prepare`）。
3. 不存在 → 按 [`plan-report-write.md`](plan-report-write.md) 走 `plan.report.create.prepare` → `plan.report.create.apply`。

## 内容提取与输出规范

1. **周期严格限定**：所有业务数据严格按报告周期的起止时间筛选。例如 2026 年第 36 周的报告，周期为 2026-08-31 ~ 2026-09-06。
2. **按业务板块分节**：例如项目任务推进、会议日程执行、流程审批办理、内外沟通协作、客户营销运维、日常工作汇报等；禁止直接堆砌原始数据。
3. **不暴露数据来源**：统计业务模块数据时，不要显示数据的来源模块、依据和获取方式，只呈现最终获取到的数据。
4. **润色整合**：对原始数据进行润色整合、去重合并、提炼总结，剔除冗余信息，保证内容通顺、重点清晰、逻辑完整。
5. **禁止计数统计**：汇总结果中禁止出现会话数、消息条数、被 @ 次数、被回复次数、会议场次、任务条数等任何计数统计类内容；只提炼有效工作事项，不统计无关闲聊。
6. **先呈现后创建**：汇总内容必须先直观呈现给用户，并提示是否生成对应周期的报告；用户确认后才执行创建。

## 命令

判断某周期是否已提交（Step 10 第 1 步）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

查看当前租户报告链路（仅在需要诊断时使用，采集阶段不要调用）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.version.check --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.version.check --input-json '{}'
```

## 输出处理

- Step 8 产物是给用户看的分节内容稿，**不包含**任何计数统计、来源模块说明或数据库字段名。
- Step 9 必须显式询问用户是否生成报告。
- Step 10 的 `exists` 为 `true` 时停止创建，转为询问是否编辑。

## 注意

- 采集阶段（Step 1~7）**禁止**调用 `plan.version.check`、`plan_searchAppver` 或任何报告侧接口。
- 不要因为一次汇总任务去调用指定技能之外的业务能力；只使用上表列出的技能。
- 数据主体默认当前登录人；涉及他人时必须先取得用户确认。

## 失败处理

- 任一业务模块技能调用失败：停止采集，明确告知失败模块，不得静默跳过或改用其它技能。
- 模块技能未安装：告知用户该模块无数据来源，由用户决定是否安装后重试。
- 周期不明确：先向用户确认，确认前不臆造时间区间。
- 报告侧接口失败（`authentication` / `policy` / `api`）：按 [`plan-overview-and-routing.md`](plan-overview-and-routing.md) 的失败处理执行。
