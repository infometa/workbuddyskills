---
name: gaia-wfm-openapi-attendance-travel-apply-la
description: 处理个人出差申请、修改和撤回。用户说“我要申请出差”“帮我提交出差申请”“修改出差”“变更出差时间”“撤回出差申请”“取消出差单”等与本人出差流程相关的话时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 出差申请流程

通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 业务命令处理当前用户的出差申请、修改和撤回。执行任何 Gaia CLI 工作流前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)，确认 WorkBuddy 连接器认证状态、权限和安全确认规则。

## 适用场景

支持以下意图：

- 申请出差：先检查出差权限，再获取可用出差类型和模式，收集申请信息后提交。
- 修改出差：根据表单号和用户给出的新信息修改已有出差单。
- 撤回出差：根据表单号撤回已有出差单。

不负责查询出差单列表或详情、审批他人的出差、上传附件、删除附件、代替管理员授予权限，也不调用本 Skill 未列出的命令来猜测业务数据。

## Gaia CLI 命令

```bash
gaia YA ATD_FORM_APPLY travelGetAccess
gaia YA ATD_FORM_APPLY travelGetAccess --help
gaia YA ATD_FORM_APPLY travelGetType
gaia YA ATD_FORM_APPLY travelApply
gaia YA ATD_FORM_APPLY travelModify
gaia YA ATD_FORM_APPLY travelCancel
```

## 通用规则

- 只能使用 `gaia module resource method` 三段式命令，并按契约追加 `--body JSON` 或 `--header JSON` 调用业务能力。禁止使用 curl、wget、SDK、自建 HTTP 客户端或直接业务 URL。
- `Authorization` 由 Gaia CLI 自动注入。不得索取、显示或写入 Token、密码、Client Secret、私钥或其他凭据。
- Discovery 对本 Skill 的所有业务 Header 和 Body 字段均标记为 `unspecified`，不要擅自宣称它们是接口必填字段。
- 优先使用用户在当前对话中已经明确提供的值。可选或未声明字段不为填满请求而追问；但完成用户目标所必需的业务信息缺失时，一次追问最关键的缺口。
- `employeeNum`、`tenantCode`、`language` 若当前上下文已有可信值则原样放入 `--header`；没有时不要猜测。实际调用因缺少字段失败后，根据 CLI 原始错误向用户追问。
- 日期和时间格式未在契约中声明。将“今天”“明天”“下周”等相对时间按当前日期和 `Asia/Shanghai` 时区解析为明确值，并在执行摘要中展示；如表达存在歧义则先追问。不要猜测接口未声明的精度或格式。
- `startModel` 和 `endModel` 仅在半天模式相关时使用：`0` 表示上半天，`1` 表示下半天。其他枚举值不得猜测。
- `attachmentOperateType` 的可选值未在当前契约中定义。只有用户提供明确值或可信上游结果时才传入，否则省略；不要自行推断附件操作。
- 申请、修改属于写操作，撤回属于破坏性操作。执行对应写命令前必须展示操作对象、关键参数和影响范围，并获得用户明确确认。只读的权限和类型查询无需额外确认。
- 用户在同一对话中修正参数后，保留其他已确认信息并继续当前流程，不要求用户重新开始。

## 触发场景与用户意图

根据用户当前表达选择一个流程：

典型用户说法包括：

- “我要申请出差”“帮我提交出差申请”“新建出差单”进入申请流程。
- “修改出差”“变更出差日期/时间/类型”“调整出差单”进入修改流程。
- “撤回出差”“取消出差申请”“撤销出差单”进入撤回流程。
- 意图不明确时先确认用户要申请、修改还是撤回，不并行执行多个写操作。
- “帮我申请明天全天的公出”进入申请流程；类型和模式分别与 `travelGetType` 返回的 `公出`、`全天` 完整匹配时自动填入，不再次询问这两个字段。

## 操作风险与确认条件

| 命令 | 操作类型 | 风险来源 | 确认条件 |
|---|---|---|---|
| `travelGetAccess` | read | 只读取当前用户出差权限 | 无需额外确认 |
| `travelGetType` | read | 只读取可用出差类型和模式 | 无需额外确认 |
| `travelApply` | write | 创建或提交出差单，影响本人考勤数据 | 展示申请关键字段和影响范围，用户明确确认后执行 |
| `travelModify` | write | 更改指定出差单，影响本人考勤数据 | 展示表单号、变更字段和影响范围，用户明确确认后执行 |
| `travelCancel` | destructive | 撤回指定出差单，改变已有业务状态 | 展示表单号、撤回说明和影响范围，用户明确确认后执行 |

## 跨命令字段映射

| 来源命令与字段 | 目标命令与参数 | 前置条件 | 失败策略 |
|---|---|---|---|
| `travelGetAccess.code` | 申请流程状态门禁 | 值为 `200`，且响应没有明确拒绝权限 | 停止，不调用 `travelGetType` 或 `travelApply` |
| 权限步骤使用的 `employeeNum`、`tenantCode` | `travelGetType` 同名 Header | 来源值已经用户确认 | 缺失时不猜测；接口报缺少字段后追问 |
| `travelGetType.details.travelType` 与用户申请描述 | `travelApply.body.travelType` | 接口返回类型非空，且该完整类型值出现在用户描述中 | 未匹配时追问类型；类型为空时停止提交 |
| `travelGetType.details.travelModeList` 与用户申请描述 | `travelApply.body.travelMode` | 列表中恰有一个完整模式值出现在用户描述中 | 零个或多个匹配时展示候选并追问；空列表时停止提交 |
| `travelApply.details.formNumber` | 后续 `travelModify.body.formNumber` 或 `travelCancel.body.formNumber` 的候选值 | 申请成功且用户确认操作该表单 | 无返回值或未确认时追问表单号 |

申请以外的独立修改或撤回没有可自动查询表单号的跨命令依赖，必须使用用户明确提供或在当前对话中已确认的 `formNumber`。

## 申请流程

### 1. 获取出差权限

调用：

```bash
gaia YA ATD_FORM_APPLY travelGetAccess
```

调用时按当前已确认值追加 `--header` JSON，字段为 `employeeNum` 和 `tenantCode`。

Header 字段：

| 字段 | 状态 | 含义 | 来源与缺失处理 |
|---|---|---|---|
| `employeeNum` | unspecified | 员工工号 | 使用当前用户已确认工号；未知时不猜测，接口因缺失失败后再追问 |
| `tenantCode` | unspecified | 租户代码 | 使用当前已确认租户代码；未知时不猜测，接口因缺失失败后再追问 |

响应中的 `code=200` 表示接口调用成功。若不是 200，或 CLI 返回认证、权限、网络或业务错误，停止申请流程，保留并说明 `code`、`message`、`reason` 等原始上下文，不继续获取类型或提交申请。`details` 的权限字段结构未在 Discovery 中定义，不根据字段名猜测权限结论；如服务返回明确的允许或拒绝语义，则按原始结果处理，拒绝时停止。

### 2. 获取出差类型和模式

只有权限步骤成功后调用：

```bash
gaia YA ATD_FORM_APPLY travelGetType
```

调用时按当前已确认值追加 `--header` JSON，字段为 `employeeNum`、`language` 和 `tenantCode`。

Header 字段：

| 字段 | 状态 | 含义 | 来源与缺失处理 |
|---|---|---|---|
| `employeeNum` | unspecified | 当前操作人工号 | 复用权限步骤使用的已确认值 |
| `language` | unspecified | 当前语种 | 使用上下文明确值；未知时省略，不能自行设定默认值 |
| `tenantCode` | unspecified | 租户代码 | 复用权限步骤使用的已确认值 |

成功响应的业务字段为：

- `details.travelType`：出差类型。
- `details.travelModeList`：可用出差模式列表。

先使用用户的原始申请描述与接口返回候选值做完整字面包含匹配，不做同义词、拆词、拼音、模糊匹配或自行推断：

- 类型：若非空的 `details.travelType` 完整出现在用户描述中，将该返回值原样映射到 `travelApply.body.travelType`；否则展示该类型并只追问类型确认。
- 模式：在 `details.travelModeList` 中查找完整出现在用户描述里的值。恰有一个匹配时，将该返回值原样映射到 `travelApply.body.travelMode`；零个匹配或多个匹配时，展示真实候选项并只追问模式确认。
- 类型或模式候选为空时停止提交，说明实际返回结果，不自行创造或放宽选项。

例如，用户说“帮我申请明天的公出”，接口返回 `travelType=公出`、`travelModeList=[全天, 时段]` 时，类型自动传入 `公出`；用户描述没有包含任一完整模式值，因此只追问在 `全天` 和 `时段` 中选择哪一个。用户说“帮我申请明天全天的公出”时，自动传入 `travelType=公出` 和 `travelMode=全天`，无需再次选择。

### 3. 收集并确认申请信息

申请接口可接受以下 Body 字段，契约均为 `unspecified`：

| 字段 | 类型 | 含义 | 处理规则 |
|---|---|---|---|
| `startDate` | string | 出差开始日期 | 从用户请求提取并消除相对日期歧义 |
| `endDate` | string | 出差结束日期 | 从用户请求提取并核对不早于开始日期 |
| `startTime` | string | 出差开始时间 | 仅在用户提供或所选模式需要时传入 |
| `endTime` | string | 出差结束时间 | 仅在用户提供或所选模式需要时传入 |
| `startModel` | string | 开始半天模式 | 仅使用 `0` 上半天或 `1` 下半天 |
| `endModel` | string | 结束半天模式 | 仅使用 `0` 上半天或 `1` 下半天 |
| `travelType` | string | 出差类型 | 用户描述包含接口返回的完整 `travelType` 时自动映射；否则追问确认 |
| `travelMode` | string | 出差模式 | 用户描述与 `travelModeList` 恰好匹配一个完整值时自动映射；否则追问确认 |
| `remark` | string | 详细说明 | 使用用户明确提供的出差说明 |
| `confirm` | boolean | 是否提交 | 必须根据用户明确选择设置，不猜测 |
| `attachmentIds` | array | 附件 ID 列表 | 仅使用用户或可信上游明确提供的 ID |
| `attachmentOperateType` | string | 附件操作类型 | 枚举未定义；无可信值时省略 |

准备执行前，展示开始和结束日期/时间、出差类型、出差模式、详细说明、是否提交以及附件摘要。获得明确确认后才调用：

```bash
gaia YA ATD_FORM_APPLY travelApply
```

实际调用追加 `--header` JSON 和 `--body` JSON；Body 只加入本次已确认且契约支持的字段，不发送占位符，不为了匹配示例而补空字符串。

### 4. 解释申请结果

先根据顶层 `code`、`message`、`reason` 判断调用结果，再读取 `details.resultFlag`：

- `resultFlag=success`：说明申请成功，并展示 `formNumber`、日期时间、`travelType`、`travelMode` 和 `remark` 中实际返回的字段。
- `resultFlag=fail`：说明申请失败，展示 `errorMsg` 及顶层错误信息，不把已发送请求等同于申请成功。
- `details` 为空：说明接口未返回表单详情，展示顶层结果，不能虚构表单号。

申请成功返回的 `details.formNumber` 可在同一对话中作为后续修改或撤回的候选表单号，但执行前仍需让用户确认目标表单。

## 修改流程

修改命令：

```bash
gaia YA ATD_FORM_APPLY travelModify
```

实际调用追加包含 `employeeNum`、`tenantCode` 的 `--header` JSON，以及包含已确认 `formNumber` 和变更字段的 `--body` JSON。

修改接口使用与申请接口相同的 Body 字段，并增加：

| 字段 | 类型 | 状态 | 含义与处理 |
|---|---|---|---|
| `formNumber` | string | unspecified | 待修改的表单号；修改目标无法确定时必须追问，不得猜测 |

修改时只传入用户已经确认、且接口契约支持的字段。契约未提供“只传变更字段”还是“必须传完整表单”的语义，因此不要自动补齐未知的原值；若 CLI 或服务要求完整字段，保留错误并向用户索取明确缺口。

执行前展示表单号、每个待修改字段的新值、`confirm`、附件变化和可能影响，并获得明确确认。成功和失败解释与申请相同，以 `details.resultFlag`、`details.formNumber`、`details.errorMsg` 及顶层字段为准。

## 撤回流程

撤回命令：

```bash
gaia YA ATD_FORM_APPLY travelCancel
```

实际调用追加包含 `employeeNum`、`tenantCode` 的 `--header` JSON，以及包含已确认 `formNumber` 和可选 `remark` 的 `--body` JSON。

Body 字段：

| 字段 | 类型 | 状态 | 含义与处理 |
|---|---|---|---|
| `formNumber` | string | unspecified | 待撤回的表单号；目标不明确时必须追问，不得猜测 |
| `remark` | string | unspecified | 撤回详细说明；有则原样传入，未知时不虚构 |

撤回属于破坏性操作。执行前必须展示表单号、撤回说明和影响，并取得用户对该表单撤回的明确确认。不得因为用户之前表达过一般性的撤回意愿而跳过最终确认。

根据顶层结果和 `details.resultFlag` 判断成功或失败。成功时展示实际返回的 `formNumber`、`remark`、`cancelTravelSign` 和 `cancelTravelDetails`；失败时展示 `details.errorMsg` 和顶层错误上下文。没有明确成功标志时不要声称已撤回。

## 错误与恢复

- 认证或 401：遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证恢复流程；恢复后只重试原命令一次。
- 权限拒绝：报告 Gaia CLI 给出的缺失 scope 或诊断信息，不自动申请权限、不绕过权限检查。
- 参数错误：指出接口返回的具体字段问题，只追问相应缺口；用户修正后再执行。
- 空结果：说明调用的命令、已使用的非敏感 Header 条件和实际空字段。权限或类型结果为空时停止申请，不自动放宽条件。
- 业务失败：保留 `code`、`message`、`reason`、`details.resultFlag` 和 `details.errorMsg`，不静默吞掉错误。
- 服务或网络异常：说明原始错误，不更换租户、员工、表单号或业务参数碰运气。
- 除 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 明确允许的认证恢复外，不自动重复写操作，避免重复申请、修改或撤回。

## 契约记录

- 来源：Gaia CLI `commands list`、`api check`、动态命令 `--help` 和 Discovery 文档。
- CLI 版本：不在业务 Skill 中固定版本；以 WorkBuddy 连接器当前安装的 Gaia CLI 及其实际 Discovery/`--help` 契约为准。
- 模块版本：YA Discovery `v1`。
- 在线核验：测试环境，2026-08-20。
- 已核验命令：
  - `gaia YA ATD_FORM_APPLY travelGetAccess`
  - `gaia YA ATD_FORM_APPLY travelGetType`
  - `gaia YA ATD_FORM_APPLY travelApply`
  - `gaia YA ATD_FORM_APPLY travelModify`
  - `gaia YA ATD_FORM_APPLY travelCancel`

## 验证用例

| 用户请求 | `travelGetType` 返回 | 预期行为 |
|---|---|---|
| “帮我申请明天全天的公出” | `travelType=公出`；`travelModeList=[全天, 时段]` | 自动传入 `travelType=公出`、`travelMode=全天`，不追问类型或模式；仍在申请前请求写操作确认 |
| “帮我申请明天的公出” | `travelType=公出`；`travelModeList=[全天, 时段]` | 自动传入 `travelType=公出`；模式无匹配，只展示 `全天`、`时段` 并追问模式 |
| “帮我申请明天全天的出差” | `travelType=公出`；`travelModeList=[全天, 时段]` | 自动传入 `travelMode=全天`；类型无匹配，只追问类型确认 |
| 用户描述同时包含多个完整模式值 | 返回包含相同多个模式 | 不自动选择，展示候选项并追问模式 |
