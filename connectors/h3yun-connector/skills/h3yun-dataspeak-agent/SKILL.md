---
name: h3yun-dataspeak-agent
title: 氚云智数（Dataspeak）问数与报告导出
description: 氚云智数（Dataspeak）对话式数据分析技能的调用规范。当用户要求查询、统计、分析某个氚云应用中的业务数据，或把问数结果导出/下载为结构化原生 HTML 报告时使用。封装两个官方 MCP 工具 h3yun_dataspeak_chat 与 h3yun_dataspeak_report_export，并说明导出/下载时如何复用连接器的 OAuth 令牌。Use when querying/analyzing H3Yun business data with Dataspeak, or exporting the structured report to native HTML.
version: "1.0.0"
author: H3Yun
---

# 氚云智数（Dataspeak）技能

## 一、智数技能的作用和使用场景

### 作用
氚云智数（Dataspeak）是氚云平台的**对话式数据分析引擎**。本技能封装两个官方 MCP 工具，让智能体能够：
- 用自然语言查询、分析氚云应用内的业务数据；
- 把问数结果导出为**结构化的原生 HTML 报告**并下载。

导出与下载所需的身份凭证不额外获取：**直接复用客户端调用这两个 MCP 工具时传递的那枚 OAuth token**。

### 使用场景
- 用户要求「分析 / 统计 / 看看 / 导出」某个氚云应用（如销售、库存、工单、项目）的数据；
- 用户要求把分析结果「生成报告 / 下载报告 / 导出 HTML」；
- 希望答案来自智数本身（而非模型自行编造），结果以原生报告形式交付。

### 不适用
- 写回业务数据（本技能只读问数 + 导出，不含 createBizObject / updateBizObject 等写操作）。

### 跨宿主 / 跨平台
- **宿主**：WorkBuddy、千问办公、豆包工作 均通过各自的氚云连接器挂载同一组工具，**工具名完全一致**：
  `h3yun_dataspeak_chat` / `h3yun_dataspeak_report_export`。
  安装本技能即可在三处使用，无需改代码。
  导出/下载所需的 OAuth 令牌**不需要另行获取**——它就是客户端调用这两个 MCP 工具时已经传递的那一枚（详见「二、如何使用」）。
- **平台**：Mac / Windows 均支持。下载步骤用 `curl`（两平台自带）即可；无命令行环境时，直接把 `fileUrl` 在浏览器打开也能拿到报告。

## 二、如何使用（调用逻辑）

### 工具 1：`h3yun_dataspeak_chat` —— 问数
- 入参：`question`（必填，自然语言问题）、`contextId`（可选，续聊时传上轮返回的 contextId）。
- 返回：`answer`（正文）、`contextId`、`taskId`、`artifacts[]`。
- 行为要点：
  - 🔴 **这是长任务：工具返回之前，结果一律视为「未知」。** 不存在"看起来失败/无结果"的中间态可以判断，更不允许因为等待时间长就自行判定超时、判死、放弃或把问题改写后重发。按长超时持续等待，直到上游真正返回。
  - **等待期间必须告知用户「结果正在生成中」**，说明智数正在取数/计算，让用户知道任务在推进而非卡死；不要在无反馈的空窗里沉默等待。
  - **等待期间不得并行发起第二个 `chat`**：同一会话并发会触发服务端 `409 another turn is in progress`，重复投递还可能被服务端拒绝（"此指令已重复收到多次"）。要等就等上一次真正结束。
  - 若智数对业务口径有疑问，会先反问并给备选方案——续聊时把上轮 `contextId` 传回，并明确要求「立即生成完整报告，不要再次确认」；
  - **结果正文原样交付，AI 不二次总结 / 改写 / 重排 / 压缩**。

若返回含 `artifacts[].reportId`，说明本次结果是结构化报告，可继续走导出。

### 工具 2：`h3yun_dataspeak_report_export` —— 导出
**先解出真正的 `sessionId`**：
- `contextId` 形如 `ctx1_<base64>`；对 `ctx1_` 之后部分做 Base64 解码，得到一个**长度为 1 的 JSON 数组**，取第一个元素即 `sessionId`。
- 例：`ctx1_WyI4ZWY3MmFkMGZhYjM0Mjc4OTUxMGQ0ZmRlOTNjNmRlMyJd` → 解码为 `["8ef72ad0fab342789510d4fde93c6de3"]` → `sessionId = 8ef72ad0fab342789510d4fde93c6de3`。
- **不能直接传完整 contextId**。

然后调用（仅两个键）：
```json
{"sessionId": "<解码所得>", "reportId": "rep_xxxx"}
```
- **不要传 `mode`**：当前 `inputSchema` 只接受 `sessionId` + `reportId`，传 `mode` 会被参数校验拒绝。
- 返回含 `fileUrl`、`downloadUrl`、`exportId`。

### 第 3 步：下载原生 HTML（必须带三个请求头）
```http
GET {fileUrl}
Authorization: Bearer {oauthToken}
X-Dataspeak-Credential-Type: h3yun_oauth_access_token
X-Dataspeak-External-Tool: workbuddy
```
> `X-Dataspeak-External-Tool` 按宿主三选一：`workbuddy`（WorkBuddy）/ `qwenwork`（千问办公）/ `doubao`（豆包工作）。

🔴 **`Authorization` 头里的 `{oauthToken}` 直接复用客户端调用连接器 MCP 工具（`h3yun_dataspeak_chat` / `h3yun_dataspeak_report_export`）时传递的那枚 OAuth token，二者必须完全一致。**
- **不需要、也没有单独的"取令牌"步骤**：这枚令牌客户端调 MCP 工具时已经在用，导出/下载时原样搬到 `Authorization` 头即可。
- **不得替换**：不得换成其它来源、其它种类、其它作用域或其它账号的令牌（例如自行 OAuth 登录换来的 token、别的连接器的 token、上一次会话残留的旧 token、手工拼装的 JWT）。
- **不得省略**：该头缺失或为空 → 下载直接失败（401/500），没有任何降级路径。
- 判定标准只有一条：**这枚 token 是否就是刚才调 MCP 工具时客户端实际传递的那枚**。不确定就重新走一次 MCP 调用取当前值，不要猜、不要复用来源不明的缓存。

**Mac / Windows 通用命令**：
```bash
# $TOKEN 即客户端调连接器 MCP 工具时传递的那枚 OAuth token 原串，不加引号内换行、不截断
curl -L -o 报告.html \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Dataspeak-Credential-Type: h3yun_oauth_access_token" \
  -H "X-Dataspeak-External-Tool: workbuddy" \
  "$FILEURL"
```

### 令牌复用策略（推荐，非必须）
- **复用的就是同一枚，不是"随便一枚"**：导出与下载用的是客户端调 MCP 工具时那一枚 `h3oauth_*`（同一 `mcp:tool` 作用域 JWT）。任何时候重新取，都必须重新走一次 MCP 调用拿当前值；换成任何其它来源的 token 都属于「替换」，不允许。
- **单次/偶发下载**：用当前这一次 MCP 调用所携带的令牌即可，最简单、零 token 管理负担。
- **短时批量/脚本循环下载多份报告**：取一次、缓存、复用，更省：
  1. 从首次 MCP 调用中取到 `token` 及其 `exp`（JWT 载荷 `exp-iat = 3600` 秒）；
  2. 后续 `GET fileUrl` 直接带缓存 token；
  3. 下载返回 **401** → token 过期，重新走一次 MCP 调用取新的；
  4. 下载返回 **500 且提示 credential-type 不匹配** → 是**请求头配错**（不是 token 问题），去修 `X-Dataspeak-Credential-Type: h3yun_oauth_access_token` 这个头。
- ⚠️ 失败务必区分 **401（token 过期→重取）** 与 **500（credential-type 头错→改头）**：只对 401 走重取分支，否则会在 500 上无意义重试。
- 🔴 不要为了拿这枚令牌去读连接器加密态文件（`~/.workbuddy/connectors/` 下的 `connector-states*`、`AES-256-GCM` 密文，存在 v3/v4 版本差异、旧实例密文解不开），也不要从这些文件里"凑"一枚 token 顶上——那既解不出正确明文，也属于「替换」。

### 关键约束（必读，否则下载失败）
| 约束 | 说明 |
| --- | --- |
| `sessionId` 必须解码 | 直接传 `ctx1_xxx` 整串会失败；先解码取数组首元素 |
| 不要传 `mode` | 当前 schema 只接受 `sessionId` + `reportId` |
| 用 `fileUrl` 下载 | `downloadUrl` 仅供展示，不能作为下载入口 |
| 三个头缺一不可 | 缺 `Authorization: Bearer {oauthToken}` → **401/500**；缺 `X-Dataspeak-Credential-Type: h3yun_oauth_access_token` 会 **500**；缺 `X-Dataspeak-External-Tool` 会 **400** |
| 🔴 token 复用 MCP 通道那一枚 | `Authorization` 里的 `{oauthToken}` 直接复用**客户端调用连接器 MCP 工具时传递的那枚 OAuth token，二者必须完全一致**（同一枚 `h3oauth_*`，`mcp:tool` 作用域）。**不得替换**为其它 token，**不得省略**；也没有单独的取令牌步骤。可缓存复用（见「令牌复用策略」），但复用的必须是同一枚 |

### 端到端顺序
```
chat（长任务，返回前结果未知 → 持续等待，并告知用户"结果正在生成中"）
  → 取 contextId 解码得 sessionId + artifacts[0].reportId
  → report_export（得 fileUrl）
  → GET fileUrl + 三请求头（Authorization 复用客户端调 MCP 工具时那一枚 token，不替换、不省略）
  → 落盘 HTML
```

## 三、技能定位与边界（仅原始转发，AI 不自行添加内容与判断）

本技能是**氚云智数（Dataspeak）的纯转发通道**，边界如下：

- **输入转发**：把用户问题原样传给 `h3yun_dataspeak_chat`（续聊时回传 `contextId`），不替用户改写业务口径、不替用户做分析决策。
- **输出转发**：把智数返回的 `answer` / `artifacts` / 原生 HTML 报告**原样交付**；AI **不自行补全、不二次总结、不改写、不重排、不压缩、不添加任何模型自有判断或结论**。
- **唯一允许的"代传"**：仅当智数对业务口径反问时，按用户确认结果回传 `contextId` 并要求"立即生成报告"——这是转发用户的确认，不是 AI 自行判断。
- **不做的事**：不写回业务数据（无 create/update）、不对数据真实性或经营含义下结论（测试应用数据须标注"不可用于经营决策"，该标注由智数返回内容携带，AI 不额外发挥）。

> 一句话：用户要的是智数的答案，不是 AI 的答案。一切内容以智数返回为准。

## 四、输出约定
- 问数正文：**原样交付，不加工**。
- 长任务等待期：主动告知用户「结果正在生成中，请稍候」，直到上游返回；不要在结果未知时给出任何猜测性结论或占位答案。
- 报告：优先交付智数**原生 HTML**（即上一步落盘的文件）；用户未要求介质时不要主动生成文件。
