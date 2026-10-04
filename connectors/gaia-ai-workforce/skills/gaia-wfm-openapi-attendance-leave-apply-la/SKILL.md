---
name: gaia-wfm-openapi-attendance-leave-apply-la
description: 处理当前用户的请假申请、请假修改和请假撤回。用户说“我要申请请假”“帮我提交请假”“修改请假”“变更请假时间或类型”“撤回请假”“取消请假单”等与本人请假流程相关的话时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 请假申请流程

通过 Gaia CLI 的 `YA/ATD_FORM_APPLY` 业务命令处理当前用户的请假申请、修改和撤回。执行任何 Gaia CLI 工作流前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)，确认 WorkBuddy 连接器的 External 认证状态、权限和安全确认规则。

## 适用场景

支持以下意图：

- 申请请假：先获取请假权限，再获取可用请假类型，最后调用申请接口。
- 修改请假：根据用户明确提供的表单号和新信息调用修改接口。
- 撤回请假：根据用户明确提供的表单号调用撤回接口。

不负责查询请假单列表或详情、审批他人的请假、上传或删除附件、代替管理员授予权限，也不调用本 Skill 未列出的命令猜测业务数据。

## Gaia CLI 命令

```bash
gaia YA ATD_FORM_APPLY getLeaveAccess
gaia YA ATD_FORM_APPLY getLeaveAccess --help
gaia YA ATD_FORM_APPLY getLeaveTypeAndMode
gaia YA ATD_FORM_APPLY getLeaveReason
gaia YA ATD_FORM_APPLY leaveApply
gaia YA ATD_FORM_APPLY leaveModify
gaia YA ATD_FORM_APPLY leeaveCancel
```

## 通用规则

- 只能使用 `gaia module resource method` 三段式命令，并按 CLI 契约追加 `--header JSON`、`--params JSON` 或 `--body JSON`；不发送占位符或自行猜测字段。
- `Authorization` 由 Gaia CLI 自动注入。禁止使用 curl、wget、SDK、自建 HTTP 客户端或直接业务 URL。
- `employeeNum`、`tenantCode`、`language` 等 Header 只有在当前对话或可信上游已明确提供时才原样传入；缺失时不猜测。
- 日期和时间先将“今天”“明天”“下周”等相对表达解析为 `Asia/Shanghai` 时区下的明确值；表达有歧义时只追问最关键的日期或时间缺口。
- 请假类型候选必须来自 `getLeaveTypeAndMode` 的真实返回；不做未经契约支持的同义词、拼音或模糊匹配。
- 申请和修改属于写操作，撤回属于破坏性操作。执行前展示目标、关键参数和影响范围，并获得用户明确确认。
- 读取权限和请假类型不需要额外确认；前置失败时停止后续调用。
- 不索取、显示或写入 Token、密码、Client Secret、私钥或其他凭据。

## 触发场景

- “我要申请请假”“帮我提交请假申请”“新建请假单”进入申请流程。
- “修改请假”“变更请假日期/时间/类型”“调整请假单”进入修改流程。
- “撤回请假”“取消请假申请”“撤销请假单”进入撤回流程。
- 意图不明确时先确认申请、修改还是撤回，不并行执行多个写操作。

## 操作风险与确认条件

| 命令 | 操作类型 | 风险来源 | 确认条件 |
|---|---|---|---|
| `getLeaveAccess` | read | 只读取当前用户请假权限 | 无需额外确认 |
| `getLeaveTypeAndMode` | read | 只读取可用请假类型和模式 | 无需额外确认 |
| `getLeaveReason` | read | 按需读取可用请假原因 | 仅在需要原因候选时调用，无需额外确认 |
| `leaveApply` | write | 创建请假单并影响本人考勤数据 | 展示申请摘要并明确确认 |
| `leaveModify` | write | 更改指定请假单并影响本人考勤数据 | 展示表单号、变更字段和影响并明确确认 |
| `leeaveCancel` | destructive | 撤回已有请假单并改变业务状态 | 展示表单号、撤回说明和影响并明确确认 |

## 跨命令调用顺序与映射

申请流程必须严格按以下顺序执行，不得跳过或并行：

```text
getLeaveAccess → getLeaveTypeAndMode → leaveApply
```

- `getLeaveAccess` 返回明确成功且未拒绝时，才调用 `getLeaveTypeAndMode`。
- `getLeaveTypeAndMode` 返回非空的真实请假类型候选后，才组装 `leaveApply`。
- `leaveApply` 成功返回的 `formNumber` 只能作为同一对话中后续修改或撤回的候选；执行后续写操作前仍需确认目标表单。
- 修改和撤回是独立流程：只接受用户明确提供或当前对话已确认的 `formNumber`，不得从未声明的查询接口猜测。

### 跨命令字段映射

| 来源 | 目标 | 映射规则 | 失败策略 |
|---|---|---|---|
| `getLeaveAccess` 的已确认业务 Header | `getLeaveTypeAndMode`、`leaveApply`、`leaveModify`、`leeaveCancel` 的同名 Header | 仅复用用户或可信上游已确认的值 | 缺失时追问；不猜测 |
| `getLeaveTypeAndMode` 的请假类型候选 | `leaveApply` 对应类型字段 | 用户原始描述唯一完整匹配时原样传入 | 无匹配或多匹配时追问 |
| `leaveApply` 的成功 `details.formNumber` | 后续 `leaveModify`/`leeaveCancel` 的 `formNumber` 候选 | 仅在用户确认操作该表单时使用 | 未返回或未确认时追问 |

除上述关系外，没有已确认的跨命令字段映射；未声明字段不自行推断。

`getLeaveReason` 是独立的只读辅助命令。除非用户明确要求列出或选择请假原因，否则申请主流程不调用它，以保持用户指定的“权限 → 类型和模式 → apply”顺序。

## 申请流程

### 1. 获取请假权限

```bash
gaia YA ATD_FORM_APPLY getLeaveAccess
```

按已确认值追加业务 Header。若返回非成功状态、明确拒绝、认证错误、权限错误、网络错误或业务错误，保留 CLI 原始上下文并停止；不得继续调用 `getLeaveTypeAndMode` 或 `leaveApply`。

### 2. 获取请假类型

仅在权限步骤成功后调用：

```bash
gaia YA ATD_FORM_APPLY getLeaveTypeAndMode
```

按 CLI 契约传入已确认的 Header。将响应中的真实请假类型候选展示给用户，并根据用户原始描述做完整字面匹配：

- 恰有一个候选完整出现在用户描述中时，原样映射到 `leaveApply` 的对应类型字段。
- 没有匹配或存在多个匹配时，展示真实候选并只追问类型选择。
- 候选为空时停止申请，不自行创建默认类型。

### 3. 收集、确认并提交请假申请

从用户请求中提取并核对请假日期、时间、类型、说明、表单相关字段及其他 CLI 契约明确支持的字段。未声明为必填的字段缺失时省略，不以空字符串填充。

执行前展示：

- 开始和结束日期/时间；
- 请假类型及其他已确认的类型信息；
- 详细说明和附件摘要（如有）；
- 将创建请假单并影响本人考勤数据的提示。

用户明确确认后调用：

```bash
gaia YA ATD_FORM_APPLY leaveApply
```

根据顶层 `code`、`message`、`reason` 以及 `details` 中明确的成功标志解释结果。只有返回明确成功时才展示实际返回的 `formNumber`；失败时保留错误信息，不把“已发起调用”描述为成功。

如果 CLI 以非零状态退出，或返回 HTTP 4xx/5xx，即使响应中同时出现了表单号，也不能直接声称申请成功：先按错误恢复规则判断结果是否明确。对于写操作的超时或连接中断，必须把结果标记为“提交结果未知”，而不是“没有返回信息”。

## 修改流程

用户明确表达修改意图时调用：

```bash
gaia YA ATD_FORM_APPLY leaveModify
```

调用要求：

- 必须有明确的 `formNumber`；目标不明确时先追问，不得猜测。
- 只传入用户已确认的新值和 CLI 契约支持的字段；不自动补齐未知原值。
- 执行前展示表单号、待修改字段、确认标志及影响范围并取得明确确认。
- 根据顶层结果和 `details` 中明确的成功标志反馈；若接口要求额外字段，保留原始参数错误并只追问对应缺口。

## 撤回流程

用户明确表达撤回意图时调用：

```bash
gaia YA ATD_FORM_APPLY leeaveCancel
```

调用要求：

- 必须有明确的 `formNumber`；目标不明确时先追问。
- 撤回说明仅在用户明确提供或 CLI 返回可信值时传入。
- 撤回属于破坏性操作，执行前必须再次展示表单号、说明和影响并取得明确确认。
- 只有接口返回明确成功标志时才声称已撤回；否则展示顶层错误和 `details` 中的错误信息。

## 空结果与错误恢复

空结果不是成功：说明实际筛选条件和接口返回的空字段，给出下一步可操作的补充信息；权限或请假类型为空时停止申请，不扩大查询范围、不创造默认值。

- 认证或 401：遵循 `gaia-cli` 的 WorkBuddy 认证恢复流程，恢复后只重试原命令一次。
- 权限拒绝：报告 CLI 给出的缺失 scope 或诊断信息，不自动申请权限或绕过检查。
- 参数错误：指出具体字段，只追问相应缺口；用户修正后再执行。
- 空权限或空类型：说明实际返回结果并停止申请，不自动放宽条件。
- 服务或网络异常：保留原始错误，不更换租户、员工、表单号或业务参数碰运气。
- CLI 非零退出或 HTTP 4xx/5xx：向用户展示可获得的 HTTP 状态码、Gaia `code`、`message`、`reason` 和关键 `details`，并说明下一步；不得只说“请求已发出”或“没有返回信息”。
- 写操作遇到 HTTP 502/504、超时、连接中断或其他无法确认服务端最终状态的异常：明确说明“提交结果未知，服务端可能已写入，也可能未写入”，禁止自动重试，提醒用户先到考勤系统核对对应日期或表单记录，再决定是否继续。
- 只有明确成功标志（例如成功状态及可核验的业务结果）才能声称申请、修改或撤回成功；明确的 4xx/业务失败才能声称失败；其余情况均按结果未知处理。
- 除认证恢复外，不自动重复写操作，避免重复申请、修改或撤回。

写操作超时或网关错误时，反馈至少包含以下信息（按实际返回填充，不得编造）：

```text
Gaia 返回 HTTP <status>（code: <code>，message: <message>）。由于这是写操作，当前无法确认服务端是否已完成写入，提交结果未知。为避免重复提交，我不会自动重试；请先在考勤系统核对 <日期/表单号> 的记录，确认后再决定下一步。
```

## 契约记录

- 来源：`D:\\OpenSceneAPI\\ya-doc\\请假申请接口` 接口文档、用户指定的 `YA ATD_FORM_APPLY` 请假业务范围、现有同类 Skill 结构及 Gaia CLI 三段式命令约定。
- CLI 契约来源：Gaia CLI 三段式命令约定、Discovery、各方法 `--help` 和 `gaia api check` 输出。
- 在线 Discovery 核验记录：测试环境 `la_test`，2026-09-04。当次核验中的命令均已通过 Discovery 或 `gaia api check` 核验。
- 已核验命令：
  - `gaia YA ATD_FORM_APPLY getLeaveAccess`
  - `gaia YA ATD_FORM_APPLY getLeaveTypeAndMode`
  - `gaia YA ATD_FORM_APPLY getLeaveReason`
  - `gaia YA ATD_FORM_APPLY leaveApply`
  - `gaia YA ATD_FORM_APPLY leaveModify`
  - `gaia YA ATD_FORM_APPLY leeaveCancel`（当前 Discovery 注册名称为双 `e`）
- 未在本地 Skill 中固化 Token、Secret、真实 URL 或未确认的字段必填性。

## 验证用例

| 用户请求 | 预期行为 |
|---|---|
| “我要申请请假” | 依次调用 `getLeaveAccess`、`getLeaveTypeAndMode`，收集并确认信息后调用 `leaveApply` |
| “修改请假单 LEAVE-123，改为明天” | 确认表单号和新日期后调用 `leaveModify` |
| “撤回请假单 LEAVE-123” | 展示撤回影响并确认后调用 `leeaveCancel` |
| 权限接口明确拒绝 | 停止，不调用 `getLeaveTypeAndMode` 或 `leaveApply` |
| 请假类型返回多个候选且用户描述未唯一匹配 | 展示真实候选并追问，不猜测类型 |
