---
name: weaver-e10-meeting-connector
display_name: 泛微会议管理
display_name_en: Weaver Meeting Management
description: "泛微 E10 会议管理（标准版）：环境模式探测、会议列表、会议室与占用、会议类型、强制冲突检测、预约会议（prepare/apply 确认链）、回执与签到查询。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "泛微 E10 会议管理（标准版）：模式探测、会议/会议室/类型查询、冲突检测、预约会议确认链、回执更新确认链与签到统计。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Weaver E10 meeting management (standard edition): environment detection, meeting/room/type queries, conflict checks, booking with prepare/apply confirmation chain, receipt updates and sign-in summary. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
cliHelp: "weaver-work-cli meeting --help"
---

# 泛微 E10 会议管理 Skill（标准版）

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

凭证边界：所有 E10 调用凭证一律由 `weaver-work-cli` 的登录托管凭据（`auth` 命令/profile 体系）提供，禁止硬编码任何密钥，禁止向用户索取 Cookie、ETEAMSID、Token 或密码。

本 Skill 通过 `weaver-work-cli meeting` 命令调用真实 operation，不绕过 CLI 直接拼接口。

## 认证与请求头契约

登录与会话由 E10 登录能力统一提供：文档型约定为 `weaver-e10-login` 技能；连接器场景下由连接器完成授权（`weaver-work-cli auth login`），业务命令统一通过 `--profile eteams` 读取该登录态。业务 Skill 不自建登录流程，不索取、打印或转存任何凭证。

CLI 发往 E10 的每个请求都自动携带以下三项用户信息参数，**缺一不可**（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## 适用场景（何时使用本技能）

用户提到会议、会议室、预约/建会、会议冲突、改期/改地点/改参会人、取消/删除会议、回执、签到、会议类型或会议室占用视图时，使用本技能。

用户要处理的是日程、审批流程或组织人员查询时，分别转 `weaver-e10-calendar-connector` / `weaver-e10-workflow-connector` / `weaver-e10-hrm-connector`。

## 路由优先级

1. 先判断用户意图是否属于会议域：会议、会议室、预约/建会、会议冲突、签到、回执、会议类型、占用视图。
2. **属于本模块 → 第一步强制跑 `meeting.env.detect` 确定环境模式**（默认按 baseUrl 读缓存；用户说"重新探测/刷新模式"时传 `refresh:true`）：
   - `mode=standard` → 继续按「命令表」选择 operation；
   - `mode=eb` → **明确告知"EB 版会议链路 CLI 未实现"并停止**，禁止拿标准接口的结果冒充 EB 环境数据；
   - `env_unavailable` → 提示环境会议应用未安装或接口未配置完整，停止。
3. 不确定字段先跑 `weaver-work-cli --profile eteams meeting schema`。
4. 不属于本模块（日程、审批流程、组织查询）→ 转对应 Skill（calendar / workflow / hrm）。

## 高优先级语义

- 「今天的会议 / 下一个会」→ `meeting.list`（`filterDate` 客户端过滤；接口 body 过滤实测不生效，不要现场试 body）。
- 「会议室占用 / 空闲 / 推荐」→ `meeting.room.list`（必须成对传 `beginDate`/`endDate`；`disabled=true` 已占用，不得推荐）。
- 「预约会议 / 建会」→ 先 `meeting.create.prepare`（内部强制冲突检测），用户确认后 `meeting.create.apply`。
- 「改期 / 换会议室 / 改参会人 / 变更会议」→ `meeting.change.prepare` → 确认后 `apply`。CLI 按会议状态**自动分流**：草稿走 `UPDATE`、正常会议走 `CHANGE`；权限由服务端判定并返回原文提示（如"您没有变更权限！"），必须原样转达用户。
- 「取消会议 / 不开了」→ `meeting.cancel.prepare` → 确认后 `apply`。
- 「删除会议记录」→ `meeting.delete.prepare` → 确认后 `apply`。
- 「提前结束会议」→ **CLI 不支持**（服务端 `overMeeting` 为空实现，调用会假成功但不生效），如实告知用户并建议在系统页面操作。
- 「回执为否 / 请假」→ `meeting.receipt.update.prepare`（自动回查回执记录 id）→ 确认后 `apply`。
- 「签到情况」→ `meeting.sign.list`（输出已签/未签统计）。

## 命令表

| 用户意图 | CLI operation | Reference |
| --- | --- | --- |
| 探测环境模式（EB/标准） | `meeting.env.detect` | [meeting-queries.md](references/meeting-queries.md) |
| 建会前置判断（onlyFlowCreate/工作流） | `meeting.calendar.base` | [meeting-queries.md](references/meeting-queries.md) |
| 会议列表 / 今天的会议 | `meeting.list`（便捷命令 `weaver-work-cli --profile eteams meeting today`） | [meeting-queries.md](references/meeting-queries.md) |
| 会议详情表单结构 / 提醒 options | `meeting.detail.field` | [meeting-queries.md](references/meeting-queries.md) |
| 会议室列表与占用 | `meeting.room.list` | [meeting-queries.md](references/meeting-queries.md) |
| 会议室占用视图 | `meeting.room.usage` | [meeting-queries.md](references/meeting-queries.md) |
| 会议类型列表 | `meeting.type.list` | [meeting-queries.md](references/meeting-queries.md) |
| 会议室/人员/属性冲突检测 | `meeting.conflict.room` / `member` / `roomAttribute` | [meeting-create.md](references/meeting-create.md) |
| 预约会议 | `meeting.create.prepare` → `meeting.create.apply` | [meeting-create.md](references/meeting-create.md) |
| 会议变更（改期 / 改地点 / 改参会人） | `meeting.change.prepare` → `meeting.change.apply` | [meeting-change.md](references/meeting-change.md) |
| 取消会议 | `meeting.cancel.prepare` → `meeting.cancel.apply` | [meeting-lifecycle.md](references/meeting-lifecycle.md) |
| 删除会议记录 | `meeting.delete.prepare` → `meeting.delete.apply` | [meeting-lifecycle.md](references/meeting-lifecycle.md) |
| 回执列表 | `meeting.receipt.list` | [meeting-receipts-signs.md](references/meeting-receipts-signs.md) |
| 更新回执 | `meeting.receipt.update.prepare` → `apply` | [meeting-receipts-signs.md](references/meeting-receipts-signs.md) |
| 签到记录与统计 | `meeting.sign.list` | [meeting-receipts-signs.md](references/meeting-receipts-signs.md) |

## 处理链：预约会议（高风险写，强制确认链）

1. **环境模式确定（强制第一步）**：跑 `meeting.env.detect`（默认读缓存，`refresh:true` 强制刷新）；`mode=eb` → 提示 EB 未实现并停止；`env_unavailable` → 提示并停止。
2. 解析意图：名称 / 时间（`yyyy-MM-dd HH:mm`）/ 会议室 / 参会人 / 类型；缺失字段先向用户确认，**禁止字段未确认直接建会**。
3. `meeting.room.list`（带时间范围）推荐空闲会议室、`meeting.type.list` 推荐类型，交用户点选。
3. `meeting.create.prepare`：自动执行建会路径检查（`onlyFlowCreate=1` 或周期工作流 → 拒绝并提示走流程）与**强制冲突检测**（接口失败视为冲突；`cansub=false` 直接拒绝；`cansub=true` 有冲突描述 → warnings 提醒并建议换时间/地点，**绝不提供"强制新建"选项**）。
4. 向用户摘要 preview（含 caller/contacter 默认当前用户、周期 `repeatDesc` 自动拼接）。
5. 用户明确确认 → `meeting.create.apply`（`confirm: true` + continuation，**10 分钟内有效，过期重新 prepare**）。
6. 结果回读用 `meeting.list`，会议链接由 Agent 按 `{baseUrl}/sp/meeting/meetingSingle?meetingId={id}` 内联输出。

## 处理链：变更 / 取消 / 删除会议（高风险写，强制确认链）

1. 先用 `meeting.list`（或用户给出的会议 id）定位目标会议，必要时把 `[名称]({baseUrl}/sp/meeting/meetingSingle?meetingId={id})` 给用户核对。
2. `meeting.change.prepare`（变更）/ `meeting.cancel.prepare` / `meeting.delete.prepare`（入参 `id`）：CLI 先**回查会议存在性**；`change` 还会按会议状态自动决定 `operateType`（草稿=UPDATE、正常=CHANGE）。**权限判定交给服务端**，CLI 不做权限预判。成功返回 `preview` + `continuation`（10 分钟有效）。
3. 向用户摘要动作与不可逆性（变更=覆盖所提交字段、当前状态与分流类型；取消=会议进入取消状态、占用/回执/签到失效；删除=彻底移除记录），**取得明确确认**。变更只提交 preview 中列出的字段。
4. 用户确认 → `meeting.*.apply`（`confirm: true` + continuation）。
5. 结果回读：`meeting.list` 确认状态（取消/删除后该会议不应再出现在正常列表）。
6. **禁止**跳过 prepare 直接 apply；**禁止**在未确认目标存在时执行写操作。

## 执行原则

- 最小必要查询；列表结果默认摘要输出，不粘贴超长 JSON。
- 长 id（`address`/`mtId`/`hrmMembers` 等）一律字符串传递（超 2^53 数字会失真）。
- **服务端业务/权限提示必须原文转达用户**：如"您没有变更权限！""您没有取消权限！""您没有删除权限！""您没有读取权限！"——不得改写成模糊说法，也不得建议用户绕过 CLI 自行拼接口。
- 错误驱动：`error.type/subtype` 决定下一步（`session_expired` → 登录流程；`conflict_rejected` → 停止；`confirmation.required` → 补 confirm；`meeting_not_operable` → 核对会议 id 与可见性）。

## 写操作失败决策树

- 写请求发出后网络中断 / 超时 → CLI 返回 `partial/write_uncertain`：**立即停止，禁止自动重试**，先 `meeting.list` / `meeting.receipt.list` 只读回查确认是否已生效，确未生效才可重新 prepare。
- `apply` 返回 `target_changed` / `continuation_expired` → 重新执行 prepare，向用户重新确认。
- 冲突 `conflict_rejected` → 直接停止，不提供任何绕过选项。
- `session_expired` → 先完成 E10 登录，再从失败步骤续跑，已成功的步骤不重做。

## 不在范围

- 禁止绕过 CLI 直接 `curl`/`fetch` E10 接口；禁止读取认证目录与 Cookie。
- **历史变更**：旧 `meeting.update.*` 已下线（它固定发送 `operateType=UPDATE`，与业务语义不符），改由 `meeting.change.*` 按会议状态自动分流；迁移说明见 [meeting-update.md](references/meeting-update.md)。
- **提前结束会议（meeting.over）不提供**：服务端接口为空实现（源码中 service 调用被注释、直接返回成功），调用只会得到"假成功"；请引导用户在系统页面操作，禁止绕过 CLI 自行拼接口。
- EB 版业务链路（`query_mtDetail_list`、`create_meeting`、占用/回执/签到三件套、议题、纪要、报表）未随 v1 实现，见 manifest `withheldOperations`。
- 周期会议走工作流（`repeatWorkFlowBaseIds` 非空）与 `onlyFlowCreate=1` 的流程建会需要工作流集成，CLI 会主动拒绝。
- 签到二维码、签到写操作、会议室/类型的增删改管理未实现（查询与占用可用，见命令表）。
- 会议变更（`meeting.change.*`）与取消（`meeting.cancel.*`）**已实现**，按上文「处理链：变更 / 取消 / 删除会议」执行；只有「提前结束会议」不支持，见上一条。
