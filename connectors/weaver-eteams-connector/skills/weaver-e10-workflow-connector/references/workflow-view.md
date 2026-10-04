# 流程查看（detail / summary / open / requestLog / pageOpen）

## 什么时候读取

用户要查看某条流程的完整详情、生成业务摘要、打开流程，或查看签字意见/流转日志，或打开常用/动态 OA 页面时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `workflow.detail` | 优先用 `requestId`；列表序号定位用 `index`（分组场景加 `group`）。固定以"用户主动查看"语义调用（标记已读）。只读，无需 confirm。 |
| `workflow.summary` | 优先用 `requestId`；生成业务摘要上下文，**不标记已读**。`summaryFields` 默认 12。只读，无需 confirm。 |
| `workflow.open` | 优先用 `requestId`；生成打开动作（URL + clientAction）。`openMode` 默认 `auto`、`noOpen` 默认 false。只读，无需 confirm。 |
| `workflow.requestLog` | **必带 `requestId`**；按页查询签字意见/流转日志。`current` 默认 1、`pageSize` 默认 10（最大 50）。只读，无需 confirm。 |
| `workflow.pageOpen` | **必带 `page`**；动态页 `create` 配 `workflowId`、`view` 配 `requestId`。`openMode` 默认 `auto`、`noOpen` 默认 false。只读，无需 confirm。 |

## 输入 —— 定位方式（requestId 与 index 二选一）

- `requestId`：流程请求 ID（整数或纯数字字符串）。用户已给出 ID 时直接用，不要先查列表再过滤。
- `index`：基于当前会话最近一次查询结果的序号（从 1 开始）。
- `group`：分组标识（`urgent`/`overdue`/`batch`/`pending`），**仅分组场景必填**——低版本模式（OA < `10.0.9909.01`）通用待办分组展示时每个分组序号独立从 1 开始，必须同时传 `group` + `index`。
- 只传 `index` 不传 `group` 会定位到其他分组的同序号流程。

**智能分组模式（OA ≥ `10.0.9909.01`）查询不产生分组，定位时只传 `index`，不传 `group`。**

## 输入 —— 各 operation 字段

| Operation | 关键字段 | 说明 |
| --- | --- | --- |
| `workflow.detail` | `requestId` / `index` / `group` | `requestLogCurrent`（签字意见当前页，默认 1）、`requestLogPageSize`（每页条数，默认 10，最大 50） |
| `workflow.summary` | `requestId` / `index` / `group` | `summaryFields`（摘要关注字段数，默认 12） |
| `workflow.open` | `requestId` / `index` / `group` | `openMode`（`auto`/`localBrowser`/`clientAction`/`url`，默认 `auto`）、`noOpen`（默认 false） |
| `workflow.requestLog` | `requestId`（必填） | `current`（默认 1）、`pageSize`（默认 10，最大 50） |
| `workflow.pageOpen` | `page`（必填） | `workflowId`（create 页）、`requestId`（view 页）、`openMode`、`noOpen` |

### pageOpen 页面 key（page）

| key | 页面 | 额外必填 |
| --- | --- | --- |
| `center` | 流程首页 | — |
| `todo` | 待办列表 | — |
| `done` | 已办列表 | — |
| `mine` | 我发起的 | — |
| `share` | 共享 | — |
| `attention` | 关注 | — |
| `draft` | 草稿 | — |
| `subordinates` | 下属待办 | — |
| `all` | 全部 | — |
| `newflow` | 提交申请/可发起流程页 | — |
| `monitor` | 流程监控 | — |
| `create` | 发起流程 | `workflowId` |
| `view` | 流程详情 | `requestId` |

> `pageOpen` 的地址由 CLI 按内置地址表生成，**不要自行拼接 OA URL**（不要手动拼 baseUrl + 路径）——只传 `page`，动态页再配 `workflowId`/`requestId`。

## 详情输出规则（按用户问法选择）

**A. 用户要看完整详情**（"打开这条／看完整详情／详情是啥"）→ 直接原样输出 `renderMarkdown` 全部三部分（基础信息 + 表单内容 + 签字意见）。不要输出 HTML 面板、不要输出 Markdown 表格、不要拆多个卡片。字段值必须原样展示，长文本保留换行，链接字段用超链接渲染。

**B. 用户对流程具体内容提问**（"审批人发表了什么意见／某字段是什么／为什么退回了／流程走到哪了"）→ **不要原样输出完整详情**（三段堆出来对内容提问是噪音）。从 `renderMarkdown` / 返回数据里提取用户问的相关部分，用一段话直接回答；只引用相关的签字意见段、字段值或基础信息片段。后续用户明确要"看完整详情／打开流程"才输出完整 `renderMarkdown`。

签字意见每条三行（不论 A/B 场景，提取签字意见时按此格式组织）：

1. 操作人、操作方式、操作时间。
2. 接收人员。
3. 签字意见。

详情规则补充：

- 标题用流程请求标题，不单独展示"流程名称"字段；`workflowName` 只能叫"工作流名称"，默认不展示。
- 第一条分隔线只能在基础信息区之后；标题下方不要加横线。
- 表单字段值必须原样展示，不能摘要、改写、删减字段值中自带的"需求概述："等文字。
- 字段有 `valueHtml`/`links` 时优先渲染为超链接；长文本字段全宽展示，保留原文换行。
- 只有签字意见 `hasMore=true` 才显示下一页提示。
- 详情面板后不要输出固定建议列表或"如果想进一步操作"类尾巴。

## 摘要规则

模型基于返回的摘要上下文提炼业务摘要，**不默认展示完整详情**。摘要先一句话概括业务事项，再列 4–7 条要点；不要体现发起人/申请人姓名，不要只复述标题，不要编造。流程状态和当前节点只在用户明确询问或确实影响业务判断时补充。

## 示例

### 按 requestId 查看详情

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.detail --input-json '{"requestId":"1307945196792242242"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.detail --input-json '{"requestId":"1307945196792242242"}'
```

### 分组场景按序号查看（待处理组第 3 条，低版本模式）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.detail --input-json '{"group":"pending","index":3}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.detail --input-json '{"group":"pending","index":3}'
```

### 生成业务摘要

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.summary --input-json '{"requestId":"1307945196792242242"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.summary --input-json '{"requestId":"1307945196792242242"}'
```

### 打开流程

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.open --input-json '{"requestId":"1307945196792242242"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.open --input-json '{"requestId":"1307945196792242242"}'
```

### 查询签字意见（第 2 页）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.requestLog --input-json '{"requestId":"1307945196792242242","current":2}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.requestLog --input-json '{"requestId":"1307945196792242242","current":2}'
```

### 打开常用 OA 页面

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.pageOpen --input-json '{"page":"todo"}'
weaver-work-cli --profile eteams --json workflow run workflow.pageOpen --input-json '{"page":"create","workflowId":"100003460000000060"}'
weaver-work-cli --profile eteams --json workflow run workflow.pageOpen --input-json '{"page":"view","requestId":"1307945196792242242"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.pageOpen --input-json '{"page":"todo"}'
weaver-work-cli --profile eteams --json workflow run workflow.pageOpen --input-json '{"page":"create","workflowId":"100003460000000060"}'
weaver-work-cli --profile eteams --json workflow run workflow.pageOpen --input-json '{"page":"view","requestId":"1307945196792242242"}'
```

## 返回

| Operation | 关键返回字段 | 渲染说明 |
| --- | --- | --- |
| `workflow.detail` | `renderMarkdown`（基础信息 + 表单内容 + 签字意见） | 直接原样输出，不改成 HTML/表格/多卡片；字段值原样展示，长文本保留换行，链接字段渲染为超链接 |
| `workflow.summary` | 业务摘要上下文 | 一句话概括业务事项 + 4–7 条要点；默认不体现发起人姓名 |
| `workflow.open` | `opened`、`requiresHostAction`、URL/clientAction | 仅 `opened=true` 才说已打开；`requiresHostAction=true` 时说明已生成宿主打开动作，等待客户端执行 |
| `workflow.requestLog` | 签字意见数组（操作人/方式/时间、接收人、签字意见）、`hasMore` | 每条三行组织；仅 `hasMore=true` 才提示下一页 |
| `workflow.pageOpen` | `opened`、`requiresHostAction`、URL | 同 `open`；动态页按 `page` 生成对应地址 |

## 注意

- **禁止事项**：不要把详情/摘要/打开结果改写、压缩或重排成自己的话；`renderMarkdown`/`finalMarkdown` 必须一字不改原样呈现。详情面板后不要加固定建议尾巴。
- **摘要不标记已读**：`workflow.summary` 不改变流程未读状态；`workflow.detail` 会标记已读（用户主动查看语义），按需选择。
- **定位纪律**：用户已给 `requestId` 时不要先查列表再过滤；分组场景必须 `group` + `index` 同时传；智能分组模式只传 `index`。
- **大结果**：详情签字意见按 `requestLogPageSize` 分页，仅 `hasMore=true` 提示下一页；需要原始 JSON 时落本地文件返回路径。
- **`warnings`（取不到详情时必须如实说）**：`workflow.detail` 在**接口返回成功但什么都没取到**（流程标题/编号/发起人/当前节点/表单字段全为空）时，会在 `warnings` 里给出原因提示。出现 `warnings` 时**必须原样转述给用户**——不要静默忽略，也不要把空详情当成"这个流程没有内容"就照常渲染空白面板；先核对 `requestId` 是否取自本环境查询结果的 `cards[].requestId`，确实取不到就如实说明详情不可见，不要编造流程内容。
- **失败/停止**：CLI 失败时在 **stderr** 返回 `ok:false` + `error.type`/`error.subtype`/`error.message`/`error.retryable`（**没有** `success`/`stopReason`/`userMessage` 字段）——`retryable=true` 时最多重试一次，否则原样转述 `error.message` 并停止，不重试、不换接口。入参类错误（如 `locate_required`）按 `error.message` 补齐参数后重试一次。
- **未登录/登录失效**：按 `weaver-e10-shared-connector` 的 `references/e10-auth-and-session.md` 引导用户登录，登录后重放原请求（读操作可重放）。
- **凭据禁止**：业务输入里禁止传入 Cookie、ETEAMSID、Token、`header.operator`，这些由 CLI 托管。
