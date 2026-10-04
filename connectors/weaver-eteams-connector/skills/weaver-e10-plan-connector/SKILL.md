---
name: weaver-e10-plan-connector
display_name: 泛微e10计划报告
display_name_en: Weaver e10 Plan Reports
description: "E10 计划报告接口 Skill：负责报告的内容统计汇总、新建、查询、修改、发布、撤回、共享报告分页查询、提交提醒与评论查看。用户说 帮我写周报/月报/季报/年报、汇总本周/上周/本月/上月的工作内容或报告、汇总上周报告、生成周报、整理本周工作写报告、查报告、改报告、发布/撤回报告、查看共享给我的报告、提醒他人交报告、查看报告评论 等意图时使用。当判定为生成/汇总本人周期报告时，将自动调用已安装的 IM消息、日报、日程、会议、项目任务、客户营销、流程 等业务模块技能采集周期数据后再整合。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "E10 计划报告接口 Skill：负责报告的内容统计汇总、新建、查询、修改、发布、撤回、共享报告分页查询、提交提醒与评论查看。用户说 帮我写周报/月报/季报/年报、汇总本周/上周/本月/上月的工作内容或报告、汇总上周报告、生成周报、整理本周工作写报告、查报告、改报告、发布/撤回报告、查看共享给我的报告、提醒他人交报告、查看报告评论 等意图时使用。当判定为生成/汇总本人周期报告时，将自动调用已安装的 IM消息、日报、日程、会议、项目任务、客户营销、流程 等业务模块技能采集周期数据后再整合。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "E10 Plan Report API Skill: Handles report content aggregation, and supports creating, querying, modifying, publishing, and withdrawing reports, running paginated queries for shared reports, sending submission reminders, and viewing comments. Use this skill when users express intents such as writing weekly/monthly/quarterly/yearly reports, summarizing this week's/last week's/this month's/last month's work content or reports, generating weekly reports, writing reports from organized weekly work, or viewing/editing/publishing/withdrawing reports, viewing reports shared with them, reminding others to submit reports, or viewing report comments. When the intent is generating/aggregating the current user's periodic report, automatically call the installed business-module skills (IM messages, daily reports, calendar, meetings, projects/tasks, CRM, workflows) to collect in-period data before composing the report. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
cliHelp: "weaver-work-cli plan --help"
---

# 泛微E10计划报告

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**


本技能覆盖报告业务域：**汇总生成报告**（多模块采集后整合）、**查询报告详情**、**分页查询报告**、**新建**、**修改**、**发布**、**撤回**、**发送提交提醒**、**查看报告评论**。写操作全部走 prepare→apply 确认协议。

## 零、第一步：意图判定（先于任何接口调用）

自上而下命中即止，不需要二次询问：

| 命中信号 | 走向 | 是否采集业务数据 |
| --- | --- | --- |
| 查看 / 查询 / 列表 / 共享给我的 / 团队 / 下属 / 成员 / 某某某的报告 / 已提交 / 发布 / 撤回 / 修改 / 提醒他们交报告 | B 查询与管理链路 | **禁止**调用任何业务模块采集数据 |
| 动词（汇总 / 生成 / 写 / 整理 / 总结 / 帮我出一份）+ 对象（周期词 + 报告类名词），且未命中上面任何信号 | A 生成与汇总链路 | 必须按采集作业链采集 |

歧义消解：「汇总上周报告」「生成本周报告」「帮我写周报 / 写月报 / 写季报 / 写年报」「帮我整理上周工作写报告」「把上周的工作总结成周报」一律归入 **A 生成链路**，不得因为出现「报告」二字而改走查询链路。

A 链路细节（采集模块、时间范围、输出规范）读 [`references/plan-collect-and-compose.md`](references/plan-collect-and-compose.md)；B 链路读 [`references/plan-report-query.md`](references/plan-report-query.md)。

## 命令入口

```text
weaver-work-cli plan --help
weaver-work-cli --profile eteams plan schema
weaver-work-cli --profile eteams --json plan run <operation> --input-json '{"key":"value"}'
```

`plan schema` 是可用能力的唯一事实来源。禁止把源文档里的接口路径当成 Agent 可直接调用的地址，也禁止把未出现在 `schema` 中的能力当作可用 operation。

## Reference 路由表

命中任一条件时，执行下一步前读取对应 reference。

| 触发条件 | Reference |
| --- | --- |
| 意图判定 A/B、版本路由与租户缓存、operation 总表、通用基础规则（周期、跳转、分页表格、人员 ID、字段名禁止项） | [`references/plan-overview-and-routing.md`](references/plan-overview-and-routing.md) |
| 查看/查询某份报告、查看共享给我的报告或下属报告、查看报告评论 | [`references/plan-report-query.md`](references/plan-report-query.md) |
| 新建报告、修改报告、发布报告、撤回报告 | [`references/plan-report-write.md`](references/plan-report-write.md) |
| 提醒他人提交报告、生成提交提醒默认文案 | [`references/plan-report-remind.md`](references/plan-report-remind.md) |
| 汇总本周/上周/本月/上月工作并生成报告（多模块采集、去重润色、输出规范） | [`references/plan-collect-and-compose.md`](references/plan-collect-and-compose.md) |

## 高优先级语义

- **报告**：work report，用户常说「周报」「月报」「季报」「年报」「年中报告」「工作总结」「汇报」。
- **报告类型**：`week`（周报）/ `month`（月报）/ `season`（季报）/ `halfYear`（年中报告）/ `year`（年报）。
- **报告周期**：`year`（年份）+ `serialNumber`（周期序号）。**周报年份与周数严格遵循 ISO8601，1 月 4 日所在周为当年第 1 周**；「上周」= 上周一至上周日。
- **发布状态**：`0` 草稿 / `1` 已发布 / `2` 已撤回 / `3` 审批中 / `4` 被退回。CLI 输出已附带 `postStatusLabel`。
- **报告详情链接**：查询与写入成功后 CLI 会在 `detailUrl` 返回可点击的详情页地址，必须呈现给用户。

## 版本路由（CLI 已内置，不要手工选择接口）

报告侧接口存在标准版与 e10-ebuilder 版两套链路。判定规则：先读租户缓存（有效期 1 天），命中即复用；未命中调用版本接口读取 `ver_name`，`V2` → e10-ebuilder 链路，其它 → 标准版链路，并写回租户缓存。

- 判断当前链路：`plan.version.check`（`plan route` 同义）。
- **禁止**跳过版本判定硬编码选择链路，禁止在某条链路命中后混用另一条链路的接口。
- 采集业务数据阶段（A 链路第 1~7 步）**禁止**调用版本接口或任何报告侧接口。
- eb 链路报告详情页链接依赖报告详情 eb 表单 id，`plan.eb.form.resolve` 会解析并长期缓存；不要手工拼链接。

## 报告侧 operation 表

| 用户意图 | operation |
| --- | --- |
| 判断当前租户报告链路 | `plan.version.check` |
| 解析 eb 报告详情表单 id | `plan.eb.form.resolve` |
| 查询某份报告（按 id 或按周期），判断某周期是否已提交 | `plan.report.get` |
| 分页查询报告列表（共享给我的、下属的） | `plan.report.page` |
| 查看报告评论内容 | `plan.comment.list` |
| 新建报告 | `plan.report.create.prepare` → `plan.report.create.apply` |
| 修改报告 | `plan.report.update.prepare` → `plan.report.update.apply` |
| 发布报告 | `plan.report.publish.prepare` → `plan.report.publish.apply` |
| 撤回报告 | `plan.report.withdraw.prepare` → `plan.report.withdraw.apply` |
| 发送提交提醒 | `plan.report.remind.prepare` → `plan.report.remind.apply` |

## 写操作确认链（必须遵守）

1. 先调用 `*.prepare`：只做只读回查、字段归一化、差异摘要并签发 continuation，**不写入**。
2. 把目标、差异、风险读给用户，并明确询问是否执行。
3. 用户明确确认后，才调用 `*.apply`，并**原样**传入 `confirm=true` 与 prepare 返回的 `continuation`。
4. `*.apply` 遇到网络中断或 `partial/write_uncertain` 时**立即停止，禁止自动重试**，先做一次只读回查（`plan.report.get`）再决定下一步。
5. `continuation` 不可手工构造、不可跨操作复用；过期或上下文变化时重新 `prepare`。

**判断某周期是否已提交报告，只能通过 `plan.report.get` 按周期查询**（必须传报告年份、报告类型、报告周期，创建人缺省为当前登录人）完成；只有确认需要创建时才做重复性判断，已存在时**不得重复创建**，必须告知用户并征询是否改为编辑。

## 通用基础规则（两条链路均生效）

1. 周期计算遵循 ISO8601；未明确周期类型（周/月/季/年）时先向用户确认，确认前不得臆造区间。
2. 报告新建/查询/修改/发布/撤回成功后，必须呈现 `detailUrl`，支持点击跳转详情页。
3. 分页结果必须用表格展示，固定列为 **报告名称 / 报告创建人名称 / 发布时间**，报告名称可点击跳转 `detailUrl`。
4. 涉及人员 ID 时只取 `id` 或 `employeeId` 字段，**禁止取 `userId`**；人员信息通过 weaver-e10-hrm-connector skill 获取。
5. 请求体中的雪花 ID（人员 ID、报告 ID 等）必须加引号包裹为字符串，避免精度丢失；直接用 CLI 的业务字段即可，CLI 会完成归一化。
6. 执行阶段与创建出的报告内容中，**决不允许出现报告相关的数据库英文字段名**（如 `content`、`f_content`、`summary`、`f_summary`、`plans`、`f_plans`、`year`、`f_year`、`type`、`f_type`、`serial_number`、`f_serial_number`）。CLI 已把 eb 链路返回值归一化为业务字段，Agent 直接使用 `report.*` 业务键即可，不要向用户复述接口原始结构。
7. 认证与会话由 CLI 托管（Cookie 完整原始串、eteamsid、User-Agent 三件套缺一不可）；若未登录先按共享规则读取 `../weaver-e10-shared-connector/references/e10-auth-and-session.md` 并通过 `weaver-work-cli auth ...` 完成会话确认，禁止输出或索取任何凭证。

## 失败处理

- 认证类错误（`authentication` / `session_expired`）：引导用户断开并重新连接本连接器以重新登录，不要用其他方式排查。
- `policy` / `link_unsupported`：该能力在当前链路不可用（例如 eb 链路的撤回、提交提醒、评论），按错误 `message` 给出的替代路径处理。
- `validation` / `not_found` / `report_exists` / `already_published` / `not_published`：属业务前置条件不满足，先向用户说明再决定下一步，禁止反复重试。
- `partial` / `write_uncertain`：立即停止写入流程，做一次只读回查后向用户说明。
- 其它业务失败看 stderr JSON 的 `error.type` / `error.subtype` / `error.message`。

## 不在范围

- 不绕过 CLI 直接 curl/fetch 访问 E10 接口，不自行拼报告侧接口路径。
- 业务数据采集不在本技能内实现：按 [`references/plan-collect-and-compose.md`](references/plan-collect-and-compose.md) 的对应关系调用已安装的业务模块技能。
- eb 链路的「撤回报告」为 ESB 动作流，CLI 返回 `policy/link_unsupported`；改由 `weaver-e10-esb` skill 用 `esb.input-format` + `esb.trigger.prepare/apply` 触发同名动作流（需要动作流 ID 或唯一值，见该 skill）。
- 人员「姓名 → 人员 ID」解析交给 weaver-e10-hrm-connector skill。
- 禁止把未出现在 `plan schema` 中的能力当作可用 operation。

## 平台兼容

命令示例同时兼容 Windows 与 macOS/Linux。简单 JSON 用 `--input-json`，复杂或多行 JSON 存为 UTF-8 文件后用 `--input <path>`。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"type":"week","serialNumber":36}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"type":"week","serialNumber":36}'
```
