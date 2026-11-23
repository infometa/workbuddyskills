# gaia-wfm-openapi-attendance-leave-apply-la 完整业务流程

本流程在 WorkBuddy Connector 中由 `gaia-cli` 执行。认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。

# 请假申请流程

通过 Gaia CLI 的 `YA/ATD_FORM_APPLY` 业务命令处理当前用户的请假申请、修改和撤回。执行任何 Gaia CLI 工作流前先阅读并遵循 `gaia-cli`，确认 Gaia CLI External 认证状态、权限和安全确认规则。

使用本 Skill 前按 `gaia-cli` 执行 `gaia status --json`，核对当前租户的 `release_channel` 为 `LA` 且与本 Skill 的 `metadata.releaseChannel` 匹配；不匹配或无法确认时停止使用，不执行其中的业务命令。

## 当前业务接口契约

本 Skill 维护当前业务范围、方法目录和业务流程，不固化任何方法的请求参数、响应字段、Header、路径或示例值。执行任一方法前，先使用方法表中的“当前契约查询命令”读取该方法的最新 `--help`；帮助不足时，再运行 `gaia api show <module> <resource> --json`。仅按本次读取到的当前业务契约组装命令和解释结果。

如果方法不存在、当前契约无法读取，或当前方法含义已经变化，停止执行并说明原因；不要猜测其他方法替代。

## 适用场景

支持以下意图：

- 申请请假：先获取请假权限，再获取可用请假类型，最后调用申请接口。
- 修改请假：根据用户明确提供的表单号和新信息调用修改接口。
- 撤回请假：根据用户明确提供的表单号调用撤回接口。

不负责查询请假单列表或详情、审批他人的请假、上传或删除附件、代替管理员授予权限，也不调用本 Skill 未列出的命令猜测业务数据。

## Gaia CLI 命令

| 用途 | 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 获取请假权限 | `gaia YA ATD_FORM_APPLY getLeaveAccess` | read | `gaia YA ATD_FORM_APPLY getLeaveAccess --help` |
| 获取请假类型和模式 | `gaia YA ATD_FORM_APPLY getLeaveTypeAndMode` | read | `gaia YA ATD_FORM_APPLY getLeaveTypeAndMode --help` |
| 获取请假原因 | `gaia YA ATD_FORM_APPLY getLeaveReason` | read | `gaia YA ATD_FORM_APPLY getLeaveReason --help` |
| 申请请假 | `gaia YA ATD_FORM_APPLY leaveApply` | write | `gaia YA ATD_FORM_APPLY leaveApply --help` |
| 修改请假 | `gaia YA ATD_FORM_APPLY leaveModify` | write | `gaia YA ATD_FORM_APPLY leaveModify --help` |
| 撤回请假 | `gaia YA ATD_FORM_APPLY leeaveCancel` | destructive | `gaia YA ATD_FORM_APPLY leeaveCancel --help` |

## 通用规则

- 只能使用 `gaia module resource method` 三段式命令，并按 CLI 契约追加 当前方法支持的 Header 参数、查询参数 或 当前方法支持的请求参数；不发送占位符或自行猜测字段。
- `Authorization` 由 Gaia CLI 自动注入；其他参数位置和字段按执行时当前契约处理。
- 业务上下文中的人员、租户或语言信息只在当前契约要求且当前对话已确认时传入；不猜测字段名或默认值。
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
- `leaveApply` 成功返回的表单号 只能作为同一对话中后续修改或撤回的候选；执行后续写操作前仍需确认目标表单。
- 修改和撤回是独立流程：只接受用户明确提供或当前对话已确认的表单号，不得从未声明的查询接口猜测。

### 跨命令字段映射

| 来源 | 目标 | 映射规则 | 失败策略 |
|---|---|---|---|
| `getLeaveAccess` 的已确认业务 Header | `getLeaveTypeAndMode`、`leaveApply`、`leaveModify`、`leeaveCancel` 的同名 Header | 仅复用用户或可信上游已确认的值 | 缺失时追问；不猜测 |
| `getLeaveTypeAndMode` 的请假类型候选 | `leaveApply` 对应类型字段 | 用户原始描述唯一完整匹配时原样传入 | 无匹配或多匹配时追问 |
| `leaveApply` 的成功响应中的表单号 | 后续 `leaveModify`/`leeaveCancel` 的表单号候选 | 仅在用户确认操作该表单时使用 | 未返回或未确认时追问 |

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

根据顶层 `code`、`message`、`reason` 以及 响应内容中明确的成功标志解释结果。只有返回明确成功时才展示实际返回的表单号；失败时保留错误信息，不把“已发起调用”描述为成功。

如果 CLI 以非零状态退出，或返回 HTTP 4xx/5xx，即使响应中同时出现了表单号，也不能直接声称申请成功：先按错误恢复规则判断结果是否明确。对于写操作的超时或连接中断，必须把结果标记为“提交结果未知”，而不是“没有返回信息”。

## 修改流程

用户明确表达修改意图时调用：

```bash
gaia YA ATD_FORM_APPLY leaveModify
```

调用要求：

- 必须有明确的表单号；目标不明确时先追问，不得猜测。
- 只传入用户已确认的新值和 CLI 契约支持的字段；不自动补齐未知原值。
- 执行前展示表单号、待修改字段、确认标志及影响范围并取得明确确认。
- 根据顶层结果和 响应内容中明确的成功标志反馈；若接口要求额外字段，保留原始参数错误并只追问对应缺口。

## 撤回流程

用户明确表达撤回意图时调用：

```bash
gaia YA ATD_FORM_APPLY leeaveCancel
```

调用要求：

- 必须有明确的表单号；目标不明确时先追问。
- 撤回说明仅在用户明确提供或 CLI 返回可信值时传入。
- 撤回属于破坏性操作，执行前必须再次展示表单号、说明和影响并取得明确确认。
- 只有接口返回明确成功标志时才声称已撤回；否则展示顶层错误和 响应内容中的错误信息。

## 空结果与错误恢复

空结果不是成功：说明实际筛选条件和接口返回的空字段，给出下一步可操作的补充信息；权限或请假类型为空时停止申请，不扩大查询范围、不创造默认值。

- 认证或 401：遵循 `gaia-cli` 的认证恢复流程，恢复后只重试原命令一次。
- 权限拒绝：报告 CLI 给出的缺失 scope 或诊断信息，不自动申请权限或绕过检查。
- 参数错误：指出具体字段，只追问相应缺口；用户修正后再执行。
- 空权限或空类型：说明实际返回结果并停止申请，不自动放宽条件。
- 服务或网络异常：保留原始错误，不更换租户、员工、表单号或业务参数碰运气。
- CLI 非零退出或 HTTP 4xx/5xx：向用户展示可获得的 HTTP 状态码、Gaia `code`、`message`、`reason` 和关键响应内容，并说明下一步；不得只说“请求已发出”或“没有返回信息”。
- 写操作遇到 HTTP 502/504、超时、连接中断或其他无法确认服务端最终状态的异常：明确说明“提交结果未知，服务端可能已写入，也可能未写入”，禁止自动重试，提醒用户先到考勤系统核对对应日期或表单记录，再决定是否继续。
- 只有明确成功标志（例如成功状态及可核验的业务结果）才能声称申请、修改或撤回成功；明确的 4xx/业务失败才能声称失败；其余情况均按结果未知处理。
- 除认证恢复外，不自动重复写操作，避免重复申请、修改或撤回。

写操作超时或网关错误时，反馈至少包含以下信息（按实际返回填充，不得编造）：

```text
Gaia 返回 HTTP <status>（code: <code>，message: <message>）。由于这是写操作，当前无法确认服务端是否已完成写入，提交结果未知。为避免重复提交，我不会自动重试；请先在考勤系统核对 <日期/表单号> 的记录，确认后再决定下一步。
```

## 统一权限与排障输出

权限错误按证据区分三层：租户未获得 OpenAPI 授权时提示联系租户管理员；当前登录账号未获得业务接口权限时提示联系公司管理员或业务负责人；前两层通过后接口仍返回 403 时，标记为接口自身业务或数据限制，携带任务 ID 联系 CLI 业务负责人排查。无法从响应确认具体层级时，不武断归因，保留原始诊断和任务 ID。

缺少必填参数时只询问缺失字段；认证失败按 WorkBuddy `gaia-cli` 基础 Skill 恢复；业务接口 4xx/5xx、网络错误、解析失败或未知异常时停止依赖步骤，说明具体操作、接口错误信息和下一步。写操作超时、连接中断或最终状态无法确认时报告“提交结果未知”，不自动重试或重复提交。普通回复先给问题摘要、已确认事实、用户动作和任务 ID；用户明确要求完整链路时才使用 `gaia logs --info` 整理 stages、请求方法/路径、脱敏参数、响应、权限判断、重试关系和 Correlation/Trace ID，不原样转发日志 JSON。业务流程不得使用 `--debug`，不得展示 Token、密码、Secret 或服务地址。

## 契约记录

- 来源：请假申请接口 接口文档、用户指定的 `YA ATD_FORM_APPLY` 请假业务范围、现有同类 Skill 结构及 Gaia CLI 三段式命令约定。
- 运行时契约来源：对应方法的 `--help`，必要时补充 `gaia api show <module> <resource> --json`。
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

验证只检查业务意图、方法顺序、权限门禁和运行时契约读取；不把参数或响应字段写入固定用例。

## 契约适用说明

本次调整仅校正WorkBuddy Connector 适配，未在线调用业务接口。正文中的历史核验记录不代表当前租户的最新契约；首次使用时，在入口模式和 `release_channel=LA` 检查通过后，通过对应方法的 `--help` 或 `gaia api show` 核对当前 Discovery。出现差异时停止使用旧字段并报告差异，不猜测替代接口。
