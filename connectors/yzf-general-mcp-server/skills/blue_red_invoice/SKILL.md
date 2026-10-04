---
name: yzf-invoice-mcp-server-skill
display_name: 云帐房AI开票
display_name_en: YZF AI Invoice
description: 通过MCP工具对接云帐房后端，支持蓝票开票/改票与红票红冲（仅单张），异步轮询实时获取开票进度
description_zh: AI开票员技能，通过MCP工具调用云帐房后端开票服务，支持蓝票（正常开票/改票）与红票（红冲/作废，仅单张），暂不支持批量开票与批量红冲。触发词：开票、开发票、专票、普票、改发票、红冲、冲红、红字、红票。
description_en: AI invoicing skill powered by MCP tools, supporting blue invoices (regular billing/modification) and red invoices (red-charge/cancellation, single only), with async polling for real-time progress. Batch billing and batch red-charge are not yet supported.
category: finance
version: "1.1.1"
author: 云帐房(YunzhangFang)
---

# AI 开票员 (yzf-invoice-mcp-server-skill)

本 Skill 提供智能开票的完整能力，通过 MCP 工具与后端税局系统交互，支持异步轮询实时获取开票进度。

> ⚠️ **当前支持范围**：支持**蓝票**（正常开票 / 修改发票信息）与**红票**（红冲、作废、负数发票，**仅限单张**）。
> **批量开票**（一次开多张、批量导入开票）与**批量红冲**（一次红冲多张、按清单批量红冲）**暂不支持**，命中即拦截并向客户说明，不调用后端工具。详见 [暂不支持场景](#暂不支持场景)。

---

## 环境配置

使用本技能前需完成以下配置：

1. **激活 MCP Connector**：在 WorkBuddy 的「Connector 管理」页面找到 `yzf-general-mcp-server`，点击「信任」并激活。激活后所有 MCP 工具（`invoice_company_management` / `invoice_intent_process` / `poll_invoice` / `apply_storage_pre_signature_url`）才能正常调用。
2. **云帐房账号登录**：首次使用时，后端会引导完成云帐房账号授权登录（如尚未登录）；登录状态由平台维护，后续无需重复操作。
3. **CODEBUDDY_SESSION_ID**：由平台在每次对话中自动注入为环境变量，技能内默认优先读取该环境变量；若环境中不存在，技能会通过标准库 UUID v4 自动生成兜底值，**无需手动配置**。

> ⚠️ 如果 MCP Connector 未激活，所有开票工具调用都会失败，技能无法正常使用。请务必先完成第 1 步。

---

## 可用工具

### invoice_company_management — 企业开票信息校验（**每次激活必调**）

> ⚠️ **铁律**：本技能被激活后，**必须最先调用此工具**校验当前用户的开票信息是否已维护完成，**未通过校验不得进入开票主流程**。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------:|------|------|
| `codebuddySessionId` | string | ✅ | 当前会话 ID。按下方规则自动获取，调用时必须传入 |
| `returnUrl` | boolean | 否 | 是否返回企业信息维护页面 URL。当用户表达**修改企业信息**意图时传 `true`；正常开票校验场景不传 |

> `codebuddySessionId` 获取规则与 `invoice_intent_process` / `poll_invoice` 一致：优先读取 `CODEBUDDY_SESSION_ID`，不存在则生成 UUID v4 并持久化到系统临时目录下的 `.wb_invoice_session_id`（Python `tempfile.gettempdir()` / Node `os.tmpdir()`）。

调用后返回当前用户默认企业的开票信息维护状态。

**返回值**：

```json
// 1) 开票信息已维护完成（可直接进入开票主流程）
{
  "code": "0",
  "message": "success",
  "cause": null,
  "result": {
    "invoice_info_filled": true,
    "company_info_maintenance_url": null,
    "company_info": {
      "company_name": "云账房测试公司",
      "taxlayer_no": "91110000123456789X"
    }
  }
}

// 2) 开票信息未维护完成（必须先引导用户去补全）
{
  "code": "0",
  "message": "success",
  "cause": null,
  "result": {
    "invoice_info_filled": false,
    "company_info_maintenance_url": "https://yunzhangfang.com/xxx/maintain",
    "company_info": null
  }
}

// 3) 修改企业信息意图（传入 returnUrl=true 时返回，引导用户修改后重新发起开票任务，而非接续之前的开票流程）
{
  "code": "0",
  "message": "success",
  "cause": null,
  "result": {
    "invoice_info_filled": false,
    "company_info_maintenance_url": "https://yunzhangfang.com/xxx/maintain",
    "company_info": null
  }
}
```

**字段说明**：

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `code` | String | 返回码，`"0"` 表示成功 |
| `message` | String | 返回信息 |
| `cause` | null / String | 错误原因（失败时非空） |
| `result.invoice_info_filled` | Boolean | **开票信息是否已维护完成**（核心判断字段） |
| `result.company_info_maintenance_url` | String | 维护页面 URL（未完成时返回，已完成时为 null 或不返回） |
| `result.company_info.company_name` | String | 企业名称 |
| `result.company_info.taxlayer_no` | String | 纳税人识别号 |

**逻辑说明**：

- `invoice_info_filled = false` → 必须返回 `company_info_maintenance_url`，引导用户去页面补全开票信息，**停止**（不进入开票主流程）
- `invoice_info_filled = true` → 不返回维护 URL，仅返回 `company_info` 和企业填写状态，**继续**进入开票主流程
- **修改企业信息意图**（传入 `returnUrl: true`）→ 返回结构与 `invoice_info_filled = false` 相同（`company_info_maintenance_url` 有值），但话术不同：引导用户去维护页面修改信息后**重新发起开票任务（而非接续之前的开票流程）**，**结束本次技能流程**

### 开票意图主流程

向后台提交开票/改票请求。对应 MCP 工具：`invoice_intent_process`。

**参数说明**（⚠️ 所有参数必须放在 `intentProcessRequest` 对象内，**不能**直接平级传；`intentProcessRequest` 内 5 个字段**全部必填**）：

| 参数 | 类型 | 必填 | 说明 |
|------|------:|------|------|
| `intentProcessRequest.userInput` | string | ✅ | 用户原始**文字**输入。**只放客户说的话**（如「按这个文件开票」），**绝对不要把文件 URL、文件路径、Base64 等任何文件相关信息拼进去** |
| `intentProcessRequest.files` | array | ✅ | 客户携带的文件列表。每个元素为 `{"file_url": "", "name": ""}`。`file_url` 来自 `apply_storage_pre_signature_url` 返回的 `publicUrl`。**无文件时传空数组 `[]`** |
| `intentProcessRequest.createTime` | integer | ✅ | 请求创建时间，毫秒时间戳。**调用时用当前毫秒时间戳**（Python `int(time.time()*1000)` / JS `Date.now()`） |
| `intentProcessRequest.invoiceType` | string | ✅ | 发票类型：`"1"`=蓝票；`"2"`=红票（红冲）。**必传，不能省略**：蓝票场景必须传入 `"1"`，红票/红冲场景必须传入 `"2"`；「不开了」等**取消语按会话上下文判定**（红冲任务→`"2"`，蓝票任务→`"1"`，无上下文默认`"1"`） |
| `intentProcessRequest.codebuddySessionId` | string | ✅ | 当前会话 ID。按下方「codebuddySessionId 获取规则」获取 |

**调用示例**：

```json
{
  "intentProcessRequest": {
    "createTime": 1786960385964,
    "codebuddySessionId": "5283efc9-11c8-4963-90eb-d270fc2d266c",
    "userInput": "开票",
    "invoiceType": "1",
    "files": []
  }
}
```

> ❌ 错误写法：`{"userInput": "开票", "invoiceType": "1"}`（缺 `intentProcessRequest` 包裹，会被拒绝）

**codebuddySessionId 获取规则**：

1. 优先读取 `CODEBUDDY_SESSION_ID`
2. 如果不存在，则使用 Python/Node 标准库生成 **UUID v4**（随机 UUID），并持久化到系统临时目录（Python `tempfile.gettempdir()` / Node `os.tmpdir()`）下的 `.wb_invoice_session_id` 作为兜底，保证同一调用链内会话 ID 一致。UUID v4 基于随机数生成，每个会话独立生成，不同用户、不同会话之间**绝不重复**

**返回值**：

```json
// 异步场景（需要轮询）
{"phase": "submitted", "taskId": "1521216305259118849", "message": "您的开票请求已提交...", "finished": false}

// 同步场景（直接完成）
{"phase": "completed", "finished": true, "ok": true, "data": {...}}
```

**使用示例**：

- 客户说「帮云账房开一张专票」：调用 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "帮云账房开一张专票", "invoiceType": "1", "files": []}`（蓝票，**`invoiceType` 必须传 `"1"`**）
- 客户说「金额改成2元」：调用 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "金额改成2元", "invoiceType": "1", "files": []}`（蓝票改票，**必须传 `"1"`**）
- 客户说「不开了」（**蓝票任务中**）：调用 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "不开了", "invoiceType": "1", "files": []}`（蓝票取消，**必须传 `"1"`**）
- 客户说「不开了」（**红冲任务中**）：调用 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "不开了", "invoiceType": "2", "files": []}`（红票取消，**必须传 `"2"`**，依据会话上下文判定）
- 客户说「红冲一下发票」：调用 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "红冲一下发票", "invoiceType": "2", "files": []}`（红票，**必须传 `"2"`**）
- 客户说「帮我红冲发票」：调用 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "帮我红冲发票", "invoiceType": "2", "files": []}`
- 客户说「红票」：调用 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "红票", "invoiceType": "2", "files": []}`（单关键词也可判定为红票场景）
- 客户发了一张采购清单图片并说「按这个开票」：先调 `apply_storage_pre_signature_url`（传 `{"request": {"fileName": "采购清单.png"}}`）拿到 uploadUrl + publicUrl，再跑 `python3 scripts/upload_file.py "文件路径" "uploadUrl" "publicUrl"` 上传，最后调 `invoice_intent_process`，传入 `intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "按这个开票", "invoiceType": "1", "files": [{"file_url": publicUrl, "name": "采购清单.png"}]}`

### poll_invoice — 轮询开票进度

对已提交的任务进行单次轮询查询。每次调用只做一次 HTTP 请求并立即返回本轮状态。

**参数说明**（⚠️ 所有参数必须放在 `pullInvoiceRequest` 对象内，**不能**直接平级传；3 个字段**全部必填**）：

| 参数 | 类型 | 必填 | 说明 |
|------|------:|------|------|
| `pullInvoiceRequest.taskId` | string | ✅ | `开票意图主流程`（invoice_intent_process）返回的 `taskId`。**⚠️ `invoice_intent_process` 返回值中的 `taskId` 可能变化**：以它**最新一次返回**的 `taskId` 为准，变了就用新 `taskId` 轮询。`poll_invoice` 本身不会返回新 `taskId` |
| `pullInvoiceRequest.codebuddySessionId` | string | ✅ | 当前会话 ID。与提交阶段保持一致；按上方「codebuddySessionId 获取规则」获取 |
| `pullInvoiceRequest.createTime` | integer | ✅ | 本次轮询请求创建时间，毫秒时间戳。**调用时用当前毫秒时间戳**（Python `int(time.time()*1000)` / JS `Date.now()`） |

**调用示例**：

```json
{
  "pullInvoiceRequest": {
    "createTime": 1786958782802,
    "codebuddySessionId": "46e5a450-b0f5-47e3-a97d-123f2616bfff",
    "taskId": "1538954991190966528"
  }
}
```

> ❌ 错误写法：`{"taskId": "1538954991190966528"}`（缺 `pullInvoiceRequest` 包裹，会被拒绝）

**返回值**：每次调用输出 NDJSON（多行 JSON），最后一行为状态摘要行：

```
# 中间消息（0 到多条，逐条展示给客户，不能丢）
{"phase":"progress", "taskId":"xxx", "message":"正在核对发票信息...", "finished":false}

# 最后一条 — 状态摘要（同样可能携带 message_list，必须展示）
# ⚠️ 若 message/message_list 中某条为图片 URL → 用 ![](url) 内联展示，不要折叠、不要只给链接（云帐房 fileserver.yunzhangfang.com 的 ?key= 链接无 Content-Type，需先跑 scripts/fetch_image.py 下载转存为本地图片再展示，见下方「信息不折叠」的 B 类规则）
# ⚠️ 所有文本消息必须逐字复制到对话正文（一字不差，禁止改写/加料），禁止用 <details> 标签、代码块包裹、折叠面板等任何折叠手段
```

> ⚠️ 严格遵守 [展示铁律](#展示铁律逐字复制--消息不丢--不折叠)，消息逐字复制（不丢字、不加字、不改字）、不丢、不折叠。

**最后一条可能的值**：

| phase | 含义 | 动作 |
|-------|------|------|
| `"summary"`, `current_round_finish_state: false`, `must_continue: true` | 轮次未结束 | **展示 message_list（如有）→ 继续轮询** |
| `"summary"`, `current_round_finish_state: true`, `confirm_invoice_flag: "async_login"` / `"submit_invoice"` | 客户确认动作完成，继续跟踪 | **展示 message_list（如有）→ 继续用当前 `taskId` 轮询**（`taskId` 以 `invoice_intent_process` 最新返回值为准；**不要**仅因 confirm_flag 而重调 `invoice_intent_process`，`poll_invoice` 也不会返回 `nextTaskId`） |
| `"summary"`, `current_round_finish_state: true`, 无 `confirm_invoice_flag` | 本轮结束 | **展示 message_list（如有）→** 展示结果，**停止** ✅ |
| `"completed"`, `finished: true` | 完全结束 | **展示 message_list（如有）→** 展示最终结果，**停止** ✅ |
| `"completed"`, `taskTerminated: true` | 任务终止（E200/E400/E500/E800/CANCELED） | **先展示 message_list 给客户**，再根据不同 taskRec 告知结果，**停止** ✅ |
| `"error"` | 网络错误 | **展示 message_list（如有）→** 输出错误，继续轮询 ❌ |

**使用示例**：
- 拿到 `taskId` 后循环调用：`poll_invoice(pullInvoiceRequest={"taskId": "1521216305259118849", "codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳})`
- 每次间隔 **5 秒**

### apply_storage_pre_signature_url — 获取文件上传预签名 URL

在调用 `invoice_intent_process` **之前**，如果客户发送了文件（图片、PDF、Excel 等），需要先将文件上传到 OBS 云存储获取可访问的 URL。上传分两步：**此工具是第一步**，只传文件名不传文件内容，拿到预签名上传地址；第二步用 `@scripts/upload_file.py` 脚本直传文件。

> ⚠️ **此工具不接收文件内容**，只签发上传地址。文件流不经过 MCP Server，直接从用户电脑传到 OBS。

**参数说明**（⚠️ 所有参数必须放在 `request` 对象内，**不能**直接平级传）：

| 参数 | 类型 | 必填 | 说明 |
|------|------:|------|------|
| `request.fileName` | string | ✅ | 文件名，含扩展名（如 `a.pdf`、`001.jpg`），必须带扩展名 |
| `request.fileSize` | integer | 否 | 文件大小（字节），服务端预校验是否超 100MB；不传则由脚本本地校验 |
| `request.fileType` | string | 否 | 文件类型（`pdf`、`png`、`jpg`、`xlsx` 等），不传则从 fileName 扩展名推断 |

**调用示例**：

```json
{
  "request": {
    "fileName": "invoice.png",
    "fileSize": 102400,
    "fileType": "png"
  }
}
```

> ❌ 错误写法：`{"fileName": "invoice.png"}`（参数必须用 `request` 包裹，平级传会被拒绝）

**返回值**：

```json
{
  "uploadUrl": "https://obs.xxx.com/bucket/path/a.pdf?X-Amz-Signature=...",
  "publicUrl": "https://obs.xxx.com/bucket/path/a.pdf",
  "objectKey": "bucket/path/a.pdf",
  "fileName": "a.pdf",
  "fileType": "pdf",
  "expiresInSeconds": 600
}
```

| 字段 | 说明 |
|------|------|
| `uploadUrl` | 预签名 PUT 地址，有效期 10 分钟，用 `curl -X PUT --upload-file` 上传 |
| `publicUrl` | 上传成功后的公网访问地址，传给 `invoice_intent_process` 的 `intentProcessRequest.files` |
| `expiresInSeconds` | 预签名有效期（600 秒 = 10 分钟） |

### upload_file.py — 本地上传脚本（第二步）

拿到 `uploadUrl` 后，用 Bash 执行此脚本，将文件直传到 OBS：

```bash
python3 scripts/upload_file.py <本地文件绝对路径> <uploadUrl> <publicUrl>
```

- 脚本内部用 `curl -X PUT --upload-file` 上传，不经过 MCP Server
- 失败自动指数退避重试（最多 3 次）
- 成功输出：`{"ok": true, "publicUrl": "...", "fileName": "...", "fileSize": ...}`
- 失败输出：`{"ok": false, "error": "..."}`
- PUT 时不携带鉴权 header（预签名 URL 自带授权）

**文件限制**：支持 PDF、PNG、JPG/JPEG、GIF、WEBP、XLSX、XLS；单文件 ≤ 100MB；一次只处理一个文件。

---

## ⚠️ 核心执行规则（最高优先级）

**当本技能被激活时，你必须无条件执行以下流程，不得跳过、不得追问、不得自行处理：**

### 第一步：开票信息校验（**每次激活最先调用**）

> ⚠️ **铁律**：本技能被激活时，**必须最先调用 `invoice_company_management` 工具**校验开票信息是否已维护完成。这是整个流程的强制前置步骤，**未通过校验不得进入开票主流程**。

**执行步骤**：

1. **判断用户意图**：
   - 若用户表达**修改企业信息**意图（如"修改企业信息""改一下公司信息""更新开票资料""修改销方的相关信息""修改销方抬头信息""销方信息我要更新一下""公司的开票资料不对，帮我处理一下""我要修改销方的基本信息和登录信息"等涉及销方/企业开票信息变更的表达）→ 调用 `invoice_company_management`，传入 `codebuddySessionId` + `returnUrl: true`，拿到 `company_info_maintenance_url` 后，引导用户去页面修改信息并**重新发起开票任务（而非接续之前的开票流程）**，**结束本次技能流程**（不进入第二步）
   - 其他开票意图 → 调用 `invoice_company_management`，仅传入 `codebuddySessionId`（不传 `returnUrl`）
2. **判断返回值**：
   - `result.invoice_info_filled = true` → 已维护完成，**直接进入下一步（意图拦截）**
   - `result.invoice_info_filled = false` → 未维护完成，向客户返回 `result.company_info_maintenance_url`，引导用户去页面补全开票信息，**结束本次技能流程**（不进入第二步、不调 `invoice_intent_process`、不轮询）
3. 若调用 `invoice_company_management` 失败（`code != "0"`），向客户说明「开票信息校验失败，请稍后重试」，**结束本次技能流程**

**向客户展示维护页面的示例话术**：

> 「您当前的开票信息还未完善，请先点击链接补全开票信息：[维护地址]。补全后再次发起开票即可。」

**修改企业信息意图的示例话术**：

> 「请点击链接修改您的企业开票信息：[维护地址]。修改完成后请重新发起开票任务，不要继续之前的开票流程。」

### 第二步：意图识别与拦截（提交前必做）

在调用任何 MCP 工具之前，先对用户输入做意图预判：

1. **红票 / 红冲意图识别（已支持，不拦截）**：用户输入包含红冲执行动作或红冲对象词（如：红冲、红冲发票、红冲一下发票、帮我红冲发票、冲红、红字、红票、我要红冲、我想红冲、需要红冲、帮我红冲、给我红冲、我要冲红、我想冲红 等）时，判定为**红票/红冲场景**，正常进入第三步，并在调用 `invoice_intent_process` 时传入 `intentProcessRequest`（其中 `invoiceType="2"`）。**即使输入仅为「红冲」「冲红」「红票」「红字」或其后仅带标点、空格，也必须判定为红票/红冲场景**，不得误判为其他意图或不激活技能。⚠️ **仅限单张红冲**：若红冲对象为多张（一次红冲多张 / 批量红冲 / 按清单全部红冲），按第 3 条批量红冲拦截，不进入主流程。
2. **批量开票意图（暂不支持，拦截）**（一次开多张 / 批量开票 / 把这个名单/Excel 都开了 / 帮这几家公司分别开票 / 一次开 N 张 …）→ 直接回复客户：
   > 「抱歉，目前暂不支持批量开票，请逐张提供开票信息，后续版本会支持批量开票，敬请谅解。」
3. **批量红冲意图（暂不支持，拦截）**（一次红冲多张 / 批量红冲 / 把这几张票都红冲了 / 按这个清单全部红冲 / 把 10 张发票都冲红 …）→ 直接回复客户：
   > 「抱歉，目前暂不支持批量红冲，请逐张提供需红冲的发票信息，后续版本会支持批量红冲，敬请谅解。」
4. **其他开票意图（正常开票 / 改票）→ 判定为蓝票场景**，正常进入第三步，调用 `invoice_intent_process` 时 `intentProcessRequest` 中**必须传 `invoiceType="1"`（不能省略）**。
5. **取消意图 → 按会话上下文判定 `invoiceType`**。取消话术 4 类（任一命中即取消意图）：
   - **直接否定**："不开了""先不开""这次不开了""算了不开了""不用开了""不需要开了""不要了""别开了""不办了"
   - **明确取消/撤回**："取消""取消吧""撤了吧""取消开票""撤销""撤回""取消这个任务"
   - **延后/暂停**："先放着吧""过会儿再说""以后再说""明天再开""稍后再说""缓缓""先等等"
   - **极简否定**："不了""算了""不用了""暂时不用""先不要了"
   - ⚠️ **对象区分**：话术指向**本次流程**（如"把这次开票取消/撤销了"）→ 取消意图，按上下文判定；话术指向**已开发票**（如"把那张发票撤销/作废掉"）→ **红冲意图，传 `invoiceType="2"`**，不受上下文影响
   - 判定规则：
     - 当前会话最近一次开票任务为**红票/红冲** → 传 `invoiceType="2"`
     - 当前会话最近一次开票任务为**蓝票** → 传 `invoiceType="1"`
     - **无上下文 / 无法判断 → 默认传 `invoiceType="1"`**

> 批量拦截（批量开票 / 批量红冲）后**结束本次技能流程**，不要进入第三步，也不要轮询。意图判定细节（红蓝票判定、红票触发关键词、批量开票/批量红冲特征）查阅 `@references/intent_prompt.md`。

### 第三步：提交

**立刻调用 `开票意图主流程`（invoice_intent_process）工具**，将用户原始输入传入。

**`invoiceType` 传参规则（重要）**：
- **蓝票场景（正常开票 / 改票）：必须传 `invoiceType="1"`，不能省略**
- **红票/红冲场景：必须传 `invoiceType="2"`**。判定为红票/红冲场景的依据见 [第二步](#第二步意图识别与拦截提交前必做) 与 `@references/intent_prompt.md`
- **取消场景（4 类取消话术：直接否定 / 明确取消 / 延后暂停 / 极简否定）：按会话上下文判定**——红冲任务→`"2"`，蓝票任务→`"1"`，无上下文默认`"1"`；⚠️ 话术指向**已开发票**（撤销/作废那张票）→ 红冲 `"2"`，不受上下文影响（判定依据见 [第二步](#第二步意图识别与拦截提交前必做)）

**客户携带文件时的处理流程**：

当客户发送了文件（图片、PDF、Excel、文档等），**不要解析或提取文件内容，不要转 Base64**，按以下步骤处理：

1. **获取文件路径**：从对话上下文中获取客户发送的文件本地路径（WorkBuddy 平台自动提供，无需手动拼接）
2. **调 `apply_storage_pre_signature_url` 拿预签名地址**：传入 `{"request": {"fileName": 文件名}}`（fileName 从文件路径提取），获取 `uploadUrl`（预签名 PUT 地址）和 `publicUrl`（公网访问地址）
3. **跑 `upload_file.py` 直传文件**：用 Bash 执行脚本，将文件 PUT 到 `uploadUrl`，文件从用户电脑直达 OBS，不经过 MCP Server：

   ```bash
   python3 scripts/upload_file.py "文件路径" "uploadUrl" "publicUrl"
   ```

4. **解析脚本输出**：成功时输出 `{"ok": true, "publicUrl": "...", ...}`，取 `publicUrl`
5. **调用 `invoice_intent_process`**：把 `publicUrl` 传入 `intentProcessRequest.files` 参数

```
客户发文件 → 取文件路径 → apply_storage_pre_signature_url（拿预签名URL）→ upload_file.py（curl直传OBS）→ 拿到publicUrl → invoice_intent_process
```

> ⚠️ **`userInput` 和 `files` 严格分离，绝对不要混在一起**：
> - `userInput` = 客户说的**文字**（如「按这个文件开票」），原样传入，不添加任何文件信息
> - `files` = 文件 URL 列表，`file_url` 来自 `publicUrl`，**不要把 URL 拼到 `userInput` 里**
>
> ❌ 错误：`userInput = "按这个文件开票，文件链接：https://obs.xxx.com/..."`
> ✅ 正确：`userInput = "按这个文件开票"`, `files = [{"file_url": "https://obs.xxx.com/...", "name": "采购清单.pdf"}]`
>
> ⚠️ 多个文件时，逐个执行步骤 2-4（每个文件单独拿预签名地址 + 上传），合并所有 `publicUrl` 到一个 `files` 数组，再传给 `invoice_intent_process`。
>
> ⚠️ 预签名 URL 有效期 10 分钟。如果脚本报告 URL 过期，重新调 `apply_storage_pre_signature_url` 拿新地址再上传，最多重来 1 次。
>
> ⚠️ 上传完成前（脚本未返回 `"ok": true` 前），**不要调用 `invoice_intent_process`**，必须先拿到 `publicUrl`。

解析返回值：
- `phase:"submitted"` → 立即展示 `message` 给客户，**记录 `taskId`**（⚠️ `invoice_intent_process` 返回值中的 `taskId` 可能变化，以最新一次返回为准）
- `phase:"completed"` → 同步结果，直接展示，**结束**
- 无 taskId → 同步结果，**结束**

### 第四步：轮询获取消息（有 taskId 时）

**⚠️ 铁律：只有以下 4 种情况可以停止轮询，除此之外绝对不能停止！**

1. 收到 `phase:"completed"`
2. 收到 `current_round_finish_state` 为真值（`true` 或 `"1"`）且 **无 confirm_invoice_flag**（`confirm_invoice_flag` 为 `"0"` 或空）
3. 总轮询时间超过 **1 小时**
4. `taskRec` 返回终止状态值（E200/E400/E500/E800/CANCELED）—— **注意：此时 `message_list` 仍需正常发送给客户**

> ⚠️ **消息内容不构成任何停止条件**：`message` / `message_list` 中出现「开票成功」「已完成」「已发送」等终态话术，**不算**上述 4 种情况之一。停止与否**只看字段**（详见下方 [绝对禁止的行为](#-绝对禁止的行为触犯即-bug) 与 [易错示例](#decision-flow)）。

> **⚠️ 关键澄清（防误判）**：
> - `task_rec: E100` 表示"任务进行中"，**但不等于"必须继续轮询"**！E100 时仍需检查 `current_round_finish_state`：若为真值且无 confirm_invoice_flag → **停止轮询**。
> - `current_round_finish_state` 后端可能返回字符串 `"1"`/`"0"` 而非布尔 `true`/`false`。`"1"` = true（轮次结束），`"0"` = false（继续）。
> - **判断优先级**：先看 `task_rec` 是否终止 → 若终止则停 → 若 E100 则看 `current_round_finish_state` → 若为真值且无 confirm_invoice_flag 则停，否则继续。
> - 详见 [Decision Flow](#decision-flow) 和 [taskRec 处理规则](#taskrec-处理规则)。

### ⛔ 绝对禁止的行为（触犯即 Bug）

在轮询循环中（从拿到 taskId 到满足上述 3 个停止条件之前），**绝对禁止**以下行为：

- ❌ **禁止说「请告诉我」「等我通知」「验证完成后告诉我」之类的话** —— 轮询是自动的，不需要客户触发！
- ❌ **禁止等待客户回复后再继续轮询** —— 展示完本轮消息后，立刻等待 5s 再调下一次 `poll_invoice`！
- ❌ **禁止因为返回了链接/验证码/登录页面就认为需要暂停** —— 链接是给客户点的，你的轮询不能停！
- ❌ **禁止输出任何暗示「我停下来等」的文字** —— 比如「我会继续轮询」「稍后查询」，这些话会让客户以为你停了！
- ❌ **禁止向客户展示 taskId** —— taskId 是内部技术标识，客户不需要知道。展示消息时只输出 `message` / `message_list` 的内容，绝不输出 taskId、task_id 等技术字段！
- ❌ **禁止改写后端话术** —— message / message_list 是后端定稿话术，只能逐字复制，不能润色、扩写、缩写、加 emoji、加客套话。错误示范：把「开票成功」改写成「🎉开票成功啦，请查收哦」
- ❌ **禁止折叠任何需要展示给客户的信息** —— `message` / `message_list` 中的每一条消息，必须以完整明文直接展示在对话中。禁止使用 `<details>` 标签、代码块包裹、折叠面板、"展开查看"等任何折叠/收起手段。图片 URL 用 `![](url)` 内联展示（A 类直接 `![](url)`；B 类云帐房 `fileserver.yunzhangfang.com` 的 `?key=` 链接先跑 `scripts/fetch_image.py` 转存为本地图片再 `![](本地路径)` 内联展示，**同样禁止折叠、禁止只给链接**），文本消息直接输出原文，让客户一眼就能看到全部内容，不需要任何额外点击或展开操作。
- ❌ **禁止根据 message / message_list 的内容判断停止轮询** —— 停止与否**只看字段（`task_rec` / `current_round_finish_state` / `confirm_invoice_flag` / `phase` / 超 1 小时），绝不看内容**。消息内容分两类，都**不构成停止条件**：
  - **终态话术**：「开票成功」「已完成」「已发送」等 → 字段未命中 4 个停止条件，必须继续轮询
  - **交互话术**：「确认红冲请回复」「请回复」「请发送」「请点击」等指令型话术 → 这是后端给**客户**的操作提示，**不是给 AI 的停止信号**；AI 不得等客户回复、不得代客户决策、不得因此重调 `invoice_intent_process`，**必须继续轮询**直到字段命中终态

  **消息内容 ≠ 任务状态**。

**正确做法：展示消息（即使消息是交互话术，也只展示不等客户）→ 等 5s → 自动调用下一轮 `poll_invoice` → 展示消息 → 等 5s → ... 循环直到字段命中终态**

### 展示铁律（逐字复制 + 消息不丢 + 不折叠）

> **最高优先级规则，覆盖所有轮询阶段。**

1. **消息不丢**：每一轮 `poll_invoice` 返回的所有 `message` / `message_list`，无论在哪条 NDJSON 行、无论 `phase` 是什么，**必须逐条展示给客户，一条都不能丢、不能省略、不能合并**。即使需要继续轮询，也**必须先把本轮全部消息展示完**再进入 5s 等待。

1.5. **逐字复制（VERBATIM）**：`message` / `message_list` 中的文字，必须**逐字复制粘贴**到回复正文中，一字不差：
   - ❌ 禁止改写、润色、扩写、缩写、总结
   - ❌ 禁止添加任何后端没有的文字：客套话（"好的""请稍等"）、emoji、表情符号、标点
   - ❌ 禁止多条合并成一条后重新组织语言
   - ✅ 正确：后端返回 `"开票成功，请查收"` → 回复正文出现 `开票成功，请查收`（原文）
   - ❌ 错误：后端返回 `"开票成功，请查收"` → 回复 `🎉 太好了！您的发票已经成功开出，请记得查收哦～`（改写+加料，违规）
   - 你只是一个"传声筒"，不是"播音员"：只搬运，不加工

2. **信息不折叠**：所有需要展示给客户的信息，**必须以完整内容直接展示在对话正文中，禁止任何形式的折叠**：
   - 文本消息：直接将原文输出到对话中，不截断、不省略
   - 图片 URL 分两类：
     - **A 类**（以 `http` 开头，结尾为 `.png` / `.jpg` / `.jpeg` / `.gif` / `.webp` / `.bmp`）：必须用 Markdown 图片语法 `![](url)` 内联展示
     - **B 类**（以 `https://fileserver.yunzhangfang.com/file/server/view?key=` 开头的云帐房文件服务 URL）：该服务响应头**无 Content-Type**，直接 `![](url)` 会渲染失败。先执行 `python3 scripts/fetch_image.py "<url>"` 下载转存为本地图片，再用 `![](本地路径)` 内联展示；脚本返回 `ok:false`（下载失败/非图片）则原样展示链接文本
   - 链接类消息：直接输出链接文本
   - 禁止使用 `<details>` / `<summary>` 标签、代码块包裹消息、"点击展开"等任何需要客户额外操作的手段
   - 每条消息独立展示，不合并多条为一条

**伪代码流程**：

```
# 第一步：开票信息校验（必须最先做）
# 判断是否为修改企业信息意图
if 用户表达修改企业信息意图:
    companyCheck = invoice_company_management(codebuddySessionId=会话ID, returnUrl=true)
    if companyCheck.code != "0":
        告知客户"开票信息校验失败，请稍后重试"，结束
    # 返回 company_info_maintenance_url，引导用户修改后重新发起开票任务（非接续之前流程）
    告知客户"请点击链接修改企业开票信息：[维护地址]。修改完成后请重新发起开票任务，不要继续之前的开票流程"，结束
else:
    companyCheck = invoice_company_management(codebuddySessionId=会话ID)
    if companyCheck.code != "0":
        告知客户"开票信息校验失败，请稍后重试"，结束
    if companyCheck.result.invoice_info_filled == false:
        告知客户"开票信息未完善，请先点击 [维护地址] 补全后再次发起开票"，结束

# 第二步：意图识别与拦截（已由 references/intent_prompt.md 完成判断）
# 命中红票/红冲（单张）→ 正常进入主流程，invoiceType="2"
# 命中批量开票 → 直接拦截，不进入主流程
# 命中批量红冲 → 直接拦截，不进入主流程

# 如果客户发了文件，预签名URL直传OBS（不走MCP传文件内容，不转Base64）
if 客户发送了文件:
    fileList = []
    for file_path in 客户发送的文件列表:
        # 第一步：调 MCP 工具拿预签名地址（只传文件名，不传文件内容）
        presign = apply_storage_pre_signature_url(request={"fileName": 文件名})
        uploadUrl = presign.uploadUrl
        publicUrl = presign.publicUrl

        # 第二步：Bash 执行脚本，curl 直传文件到 OBS
        # python3 scripts/upload_file.py "文件路径" "uploadUrl" "publicUrl"
        # 输出：{"ok": true, "publicUrl": "...", ...}
        uploadResult = 脚本输出
        fileList.append({"file_url": publicUrl, "name": 文件名})
else:
    fileList = None

# invoiceType 传参（必传，不能省略）：蓝票 → "1"；红票/红冲 → "2"
invoiceType = 意图识别结果（"1" 或 "2"）  # 根据用户意图判定，蓝票传 "1"、红票传 "2"，两者都不能省略；4 类取消话术（直接否定/明确取消/延后暂停/极简否定）按会话上下文判定（红冲任务→"2"，蓝票任务→"1"，无上下文默认"1"）；话术指向已开发票（撤销/作废那张票）→ 红冲 "2"
result = invoice_intent_process(intentProcessRequest={"codebuddySessionId": 会话ID, "createTime": 当前毫秒时间戳, "userInput": "用户原话", "invoiceType": invoiceType, "files": fileList if fileList is not None else []})  # 开票意图主流程

if result.phase == "submitted":
    # ⚠️ taskId 以 invoice_intent_process 最新返回值为准：其返回值中的 taskId 可能变化
    #（若再次调用 invoice_intent_process 且返回新 taskId，则更新 taskId，后续轮询用新值）
    taskId = result.taskId
    startTime = 当前时间

    while True:
        if 当前时间 - startTime > 1小时:
            告知客户"处理超时，请稍后重试"，结束

        result = poll_invoice(pullInvoiceRequest={
            "taskId": taskId,
            "codebuddySessionId": 提交阶段相同会话ID,
            "createTime": 当前毫秒时间戳
        })

        # 逐行处理 NDJSON 输出
        for line in result.lines:
            # ⚠️ 严格遵守展示铁律，所有消息逐条完整展示
            #
            # NDJSON 每行可能是以下几类之一（不要依赖 phase 字段做分支，直接读实际字段）：
            #   1) 进度行：{"message":"...", "phase":"progress", ...}
            #   2) 状态摘要行：{"current_round_finish_state":"1/0", "confirm_invoice_flag":"0/async_login/submit_invoice",
            #                    "task_rec":"E100/E200/...", "message_list":[...]}
            #   3) 终态行：{"finished":true, "ok":true, "message_list":[...], "task_rec":"E200/E400/...", ...}

            # 收集本行所有待展示消息
            pendingMessages = []
            if line.get("message"):                                    # 单条消息（进度行）
                pendingMessages.append(line["message"])
            if line.get("message_list") and len(line["message_list"]) > 0:  # 消息列表（状态摘要/终态行）
                pendingMessages.extend(line["message_list"])

            for msg in pendingMessages:
                # ⚠️ 所有消息必须完整展示给客户，禁止折叠、禁止用代码块包裹
                # ⚠️ 图片 URL 直接用 Markdown 内联展示，不要折叠、不要只给链接
                if msg 以 https://fileserver.yunzhangfang.com/file/server/view?key= 开头:
                    # B 类：云帐房文件服务 URL，响应头无 Content-Type，直接 ![](msg) 会渲染失败
                    fetchResult = 执行 python3 scripts/fetch_image.py "<msg>"（解析输出 JSON）
                    if fetchResult.ok:
                        用 Markdown 图片语法展示：![](fetchResult.path)   # 本地已转存文件
                    else:
                        展示 msg 链接文本给客户（原样输出）
                elif msg 匹配图片URL正则 (以 http 开头，结尾为 .png/.jpg/.jpeg/.gif/.webp/.bmp):
                    用 Markdown 图片语法展示：![](msg)
                else:
                    # 文本消息直接输出原文到对话正文，不截断、不省略、不用 <details> 或代码块折叠
                    展示 msg 文本给客户（完整原文，禁止折叠）

            # ── 状态判断：直接读后端字段，不依赖 phase ──
            #
            # ⚠️ 字段名以下划线为准（后端实际字段），值可能是字符串 "1"/"0"
            roundFinishedRaw = line.get("current_round_finish_state")  # "1"=true, "0"=false
            confirmFlagRaw = line.get("confirm_invoice_flag")          # "0"/""=无, "async_login"/"submit_invoice"=有
            taskRec = line.get("task_rec", "")                         # E100/E200/E400/E500/E800/CANCELED

            isRoundFinished = roundFinishedRaw in (True, "1", 1)
            hasConfirmFlag = confirmFlagRaw in ("async_login", "submit_invoice")

            # 按 [状态判断表](#第五步状态判断表唯一退出继续依据) 优先级 ①→②→③ 判断：
            #   ① taskRec 终止 → 按编码告知结果后停止
            #   ② confirm_invoice_flag → 继续用当前 taskId 轮询（taskId 以 invoice_intent_process 最新返回值为准；不要重调，poll_invoice 也不返回 nextTaskId）
            #   ③ roundFinished 真且无 confirm_invoice_flag → 停止（即使 taskRec=E100）；否则继续

        sleep(5秒)  # 等待 5 秒再轮下一次
```

### 第五步：状态判断表（唯一退出/继续依据）

> **⚠️ 按优先级①→②→③从上往下判断，命中即执行。不要自己加判断！**

| 优先级 | 条件 | 动作 |
|:---:|------|------|
| ① | `task_rec` = E200/E400/E500/E800/CANCELED（终止） | 展示 message_list → 按 [taskRec 处理规则](#taskrec-处理规则) 的客户提示语告知结果 → **停止** ✅ |
| ② | `confirm_invoice_flag` = async_login/submit_invoice | 展示 message_list → **继续用当前 `taskId` 轮询**（`taskId` 以 `invoice_intent_process` 最新返回值为准；不要仅因 confirm_flag 而重调 `invoice_intent_process`，`poll_invoice` 也不会返回 `nextTaskId`） |
| ③ | `current_round_finish_state` = false/"0" | 展示 message_list → **继续轮询** |
| ③ | `current_round_finish_state` = true/"1"，`confirm_invoice_flag` = "0"/空 | 展示 message_list → 展示结果 → **停止** ✅ |

> **⚠️ E100 特别注意**：`task_rec=E100` 只是"进行中"，非终止。必须继续向下判断 ②③。常见误判：看到 E100 就以为"继续"，但若 `current_round_finish_state` 已为真值且无 confirm_invoice_flag → 按优先级③停止！

**一句话记住：技能激活 = 开票意图主流程 → 死循环 poll_invoice 展示 → 直到终态才停。中间不说话、不等客户、不停顿。**

---

## 触发条件

**当客户表达与发票开具相关的意图时激活本技能。** 意图识别细节（意图分类、红蓝票判定、红票触发关键词、批量开票/批量红冲拦截、反例拦截、few-shot 示例）查阅 `@references/intent_prompt.md`。

### 强触发（激活技能）

- "开一张发票""开票""按这个开"
- "开 xxx 元给 xx 公司"
- "开 xxx 商品，普票/专票"
- "改成专票""金额改一下""增加一个发票项目"（修改发票信息，属蓝票流程）
- 取消类话术（取消尚未开具的发票，**invoiceType 按会话上下文判定**：红冲任务→`"2"`，蓝票任务→`"1"`，无上下文默认`"1"`，需记录拒绝原因）：
  - 直接否定："不开了""先不开""这次不开了""算了不开了""不用开了""不需要开了""不要了""别开了""不办了"
  - 明确取消/撤回："取消""取消吧""撤了吧""取消开票""撤销""撤回""取消这个任务"
  - 延后/暂停："先放着吧""过会儿再说""以后再说""明天再开""稍后再说""缓缓""先等等"
  - 极简否定："不了""算了""不用了""暂时不用""先不要了"
  - ⚠️ 话术指向已开发票（"把那张发票撤销/作废掉"）→ 属**红票/红冲**（`invoiceType="2"`），不是取消
- "修改企业信息""改一下公司信息""更新开票资料""修改销方的相关信息""修改销方抬头信息""销方信息我要更新一下""公司的开票资料不对，帮我处理一下""我要修改销方的基本信息和登录信息"（修改企业/销方开票信息，调 `invoice_company_management` 传 `returnUrl: true`）
- **红票/红冲（属红票流程，激活技能，`invoiceType="2"`）**：
  - "红冲""冲红""红字""红票"（**单独出现或仅带标点、空格也必须判定**）
  - "红冲发票""红冲一下发票""帮我红冲发票""帮我把这张票红冲一下"
  - "我要红冲""我想红冲""需要红冲""帮我红冲""给我红冲""我要冲红""我想冲红"
  - 发票作废、把这个票冲一下、退货冲红、负数金额开票、对上一张发票开红字、原发票金额错误冲红处理 等红冲执行动作/对象表达
  - ⚠️ **仅限单张红冲**：一次红冲多张 / 批量红冲 / 按清单全部红冲 → 激活技能但命中 [暂不支持场景](#暂不支持场景)，直接拦截，不调工具

### 暂不支持场景（激活后拦截，不调工具）

> 以下场景**会激活本技能**，但在第二步被拦截，**不调用 `invoice_intent_process`**，直接向客户说明暂不支持：

- **批量开票**：一次开多张、批量开票、把这个名单/Excel 都开了、帮这几家公司分别开票、一次开 N 张 等
- **批量红冲**：一次红冲多张、批量红冲、把这几张票都红冲了、按这个清单全部红冲、把 N 张发票都冲红 等

### 不触发

- "开账户""开户头"（开户 ≠ 开票）
- "开发""开门""开车"
- 单纯提供开户行信息无开票意图

> ⚠️ **意图判断职责**：本技能为 MCP 工具型，意图判断由后端 `invoice_intent_process` 接口完成。`intent_prompt.md` 作为 LLM 侧的意图识别参考，用于判断是否激活本技能、判定红/蓝票（决定 `invoiceType` 传参）、是否命中暂不支持场景（批量开票、批量红冲），以及在不激活时如何回复客户。激活后 LLM 不再做字段提取，直接把用户原话传入 `intentProcessRequest.userInput` 参数。

---

## 异步轮询协议详解

### 后端响应结构

`poll_invoice` 对应的后端接口返回：

```json
{
  "code": "0",
  "result": {
    "current_round_finish_state": true/false,
    "confirm_invoice_flag": "0" / "async_login" / "submit_invoice",
    "message_list": ["消息1", "消息2"],
    "task_rec": "E200" / "E101" / ...
  }
}
```

| 字段 | 含义 |
|------|------|
| `current_round_finish_state` | `true`/`"1"`=当前轮次结束，`false`/`"0"`=继续。⚠️ 后端可能返回字符串 `"1"`/`"0"` |
| `confirm_invoice_flag` | `"async_login"`=异步登录；`"submit_invoice"`=提交开票；`"0"`/空=无 confirm_invoice_flag |
| `message_list` | 后端消息列表（字符串数组），**定稿话术，逐字复制给客户（一字不差，禁止改写/加料）**，逐条展示。所有消息以完整原文直接展示在对话正文中，禁止折叠。若某条消息为图片 URL，用 `![](url)` 内联展示（云帐房 `fileserver.yunzhangfang.com` 的 `?key=` 链接响应头无 Content-Type，直接展示会渲染失败，需先跑 `python3 scripts/fetch_image.py "<url>"` 下载转存为本地图片再用 `![](本地路径)` 内联展示；脚本失败则原样展示链接文本） |
| `task_rec` | 任务终止标识（见下方）。E100=进行中（非终止），其余为终止 |

### Decision Flow

> ⚠️ 严格遵守 [展示铁律](#展示铁律逐字复制--消息不丢--不折叠)，每轮先逐字复制全部消息再判断状态。

```
【每轮通用】展示消息 → 按 [状态判断表](#第五步状态判断表唯一退出继续依据) 优先级 ①→②→③ 判断 → 停 / 继续轮询
```

> **⚠️ 字段值类型说明**：后端返回的 `current_round_finish_state` 可能是字符串 `"1"`/`"0"` 而非布尔 `true`/`false`。`"1"` 等价于 true（轮次结束），`"0"` 等价于 false（继续）。`confirm_invoice_flag` 为 `"0"` 表示无 confirm_invoice_flag。

**易错示例**：
```
返回：{"current_round_finish_state": "1", "confirm_invoice_flag": "0", "task_rec": "E100", "message_list": ["当前轮次已处理完成"]}
分析：task_rec=E100 → 非终止，继续判断 → current_round_finish_state="1"(真值) + confirm_invoice_flag="0"(无) → ✅ 终止轮询
⚠️ 常见误判：看到 E100 就认为"进行中→继续轮询"，忽略了 current_round_finish_state 已经为真值！
```

```
返回：{"current_round_finish_state": "0", "confirm_invoice_flag": "0", "task_rec": "E100",
       "message_list": ["发票已开具成功。更多文件可查看税局原始发票链接：…", "📄 [点击下载-xxx.pdf](https://…)", "开票成功！电子发票稍后发送给您。本次开票消耗 1 积分"]}
分析：task_rec=E100 → 非终止，继续判断 → confirm_invoice_flag="0" 无 → current_round_finish_state="0"(假值) → ✅ 必须继续轮询
⚠️ 常见误判：看到 message_list 内容是「开票成功」就停止轮询！消息内容 ≠ 任务状态，停止与否只看字段！后端可能先推送成功消息、终态字段（E200/finished/round_finish_state=1）在后续轮次才返回。
```

```
返回：{"current_round_finish_state": "0", "confirm_invoice_flag": "0", "task_rec": "E100",
       "message_list": ["我将帮您红冲发票【26322000006686693026】，确认红冲请回复：确认红冲。若红冲其他发票，请发送发票PDF文件。", "https://fileserver.yunzhangfang.com/file/server/view?key=..."]}
分析：task_rec=E100 → 非终止，继续判断 → confirm_invoice_flag="0" 无 → current_round_finish_state="0"(假值) → ✅ 必须继续轮询
⚠️ 常见误判：看到 message_list 内容是「确认红冲请回复」就以为要等客户回复而停止轮询！交互话术 ≠ 任务状态，这是后端给客户的操作提示，不是给 AI 的停止信号，必须继续轮询！
```

### taskRec 处理规则

`taskRec` 是 **后端开票任务的终止标识**。E100 为唯一非终止状态；其余值（E200/E400/E500/E800/CANCELED）均为终止状态，触发轮询停止。**但即使为终止状态，`message_list` 仍需正常发送给客户。**

> **⚠️ E100 ≠ 继续轮询**：E100 只表示"任务未终止"，是否继续轮询还需看 `current_round_finish_state`。若 `current_round_finish_state` 为真值且无 confirm_invoice_flag → 停止轮询。

| taskRec 值 | 含义 | 是否终止 | 客户提示语 | 轮询行为 |
|-----------|------|---------|-----------|---------|
| `"E100"` | 进行中 | ❌ 非终止 | — | **需结合 `current_round_finish_state` 判断**：真值+无 confirm_invoice_flag→停；假值→继续 |
| `"E200"` | 成功 | ✅ 终止 | 「开票成功，请查收发票」 | 正常发送 message_list 给客户，**停止轮询** |
| `"E400"` | 失败 | ✅ 终止 | 「开票失败，请检查信息后重试」 | 正常发送 message_list 给客户，**停止轮询** |
| `"E500"` | 超时 | ✅ 终止 | 「处理超时，请稍后重试」 | 正常发送 message_list 给客户，**停止轮询** |
| `"E800"` | 取消 | ✅ 终止 | 「开票已取消」 | 正常发送 message_list 给客户，**停止轮询** |
| `"CANCELED"` | 超时 | ✅ 终止 | 「处理超时，请稍后重试」 | 正常发送 message_list 给客户，**停止轮询** |

---

## 注意事项

- **轮询是自动的**：拿到 `taskId` 后 AI 必须自动循环调 `poll_invoice`，不需要客户任何操作
- **链接不影响轮询**：如果返回了验证链接，链接是给客户点的，AI 的轮询不能因此暂停
- **超时兜底**：总轮询超过 1 小时仍未结束时，告知客户「处理超时，请稍后重试」
- **confirm 标志处理**：遇到 `async_login` 或 `submit_invoice` 标志时，**继续用当前 `taskId` 轮询**（`taskId` 以 `invoice_intent_process` 最新返回值为准），不要仅因 confirm_flag 而重调 `invoice_intent_process`，也不要等新 `taskId`。`poll_invoice` 不会返回 `nextTaskId`
- **消息展示**：严格遵守 [展示铁律](#展示铁律逐字复制--消息不丢--不折叠)，消息逐字复制（不丢字、不加字、不改字）、不折叠、图片用 `![](url)` 内联
- **taskId 不展示**：taskId 是内部技术标识，**绝不向客户展示**。展示消息时只输出 `message` / `message_list` 的内容，不输出 taskId 等技术字段
- **跨平台兼容**：macOS 和 Windows 均可正常工作

---

## 子资源

- `@references/intent_prompt.md` — 意图识别 Prompt（LLM 用，意图分类 + 红蓝票判定（红票关键词触发） + 批量开票拦截 + 反例拦截 + few-shot 示例，不含字段提取）
