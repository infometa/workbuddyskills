---
name: ai-html-auto-import
description: 将文章正文自动导入 135 编辑器，生成 AI 排版并返回排版 HTML 与编辑器链接。当用户要求自动导入文章、处理正文或生成 135 AI 排版内容时使用。
description_zh: 将文章正文自动导入 135 编辑器，生成 AI 排版并返回排版 HTML 与编辑器链接，每次成功生成扣除 1 点。
description_en: Automatically import article text into 135 Editor, generate AI layout and return the formatted HTML and editor URL. Each successful generation costs one point.
version: 1.0.1
author: 135editor
---

# 135 编辑器 AI 自动导入

## 前置条件

使用 `135ai-editor` MCP 连接器调用。本连接器使用 **MCP 原生 OAuth** 认证：
首次访问由 WorkBuddy 打开浏览器完成 135 编辑器账号授权，之后自动携带 Bearer
访问令牌并自动续期，不要求用户在对话中提供 API Key、Token 或验证码。
`connector-meta.json` 不设置 `auth_mode`、`mcp.json` 不写静态 `headers` 是有意设计。
仅在连接器显示「已连接」后调用工具。服务地址以连接器 `mcp.json` 为准。
调用工具 `auto_import_ai_html`（显示名「自动导入文章生成排版」），不要将 REST 路径当作 MCP 工具名称。

如果调用返回 401，说明授权已失效，提示用户在连接器设置中断开后重新连接。

用户需要提供文章正文；只有链接时，先通过可用的读取工具获取正文，无法读取则向用户索取正文。
每次成功生成扣除 1 点。执行前说明费用并确认用户同意；已明确同意本次费用时不重复询问。

## 参数与调用

- `content`：必填，非空字符串，原始文章正文。不要发送链接代替正文，不擅自改写用户提供的文章。
- `idempotency_key`：可选，非空字符串，最多 100 字节。每次新生成使用新的唯一标识，同一请求重试保持原标识；建议始终提供。

```json
{"name":"auto_import_ai_html","arguments":{"content":"这里是待处理的文章正文。","idempotency_key":"article-import-550e8400-e29b-41d4-a716-446655440000"}}
```

不要并发提交同一正文。服务仅复用同一授权身份下已完成的幂等请求，不保证处理中请求或失败请求不会再次生成、扣费。
请求超时或返回 500 时不要自动循环重试；告知结果可能不确定，确认用户同意后再使用原标识重试。
改变正文后必须换用新标识，否则可能返回旧结果。

## 返回与展示

成功时 `isError` 为 `false`，`structuredContent` 返回：

```json
{"content":"<section ...排版后的完整 HTML...</section>","url":"https://www.135editor.com/ai_editor/ai-style/editor/?id=456","remaining_num":371}
```

- `content`：排版后的完整 HTML（135editor onekey 格式，可直接渲染或写入文件）。排版脚本执行失败时为 `null`，此时正文未排版但不影响其余流程。
- `url`：135 AI 排版项目地址，打开可在编辑器中继续编辑该排版；排版失败时为 `null`。
- `remaining_num`：本次扣点后剩余的 AI 排版点数。

排版结果已入库：标题/正文/封面图存文章（WxMsg），排版规则存 AiHtmlParserMsg，可通过 `url` 在编辑器中继续编辑。
保留返回内容原样交付，可按用户需求写入文件。向用户展示 135 提供的编辑器链接时，使用 `<a>` 标签将其呈现为按钮，并将按钮文案统一设为「深度编辑」；同时展示剩余点数。用户需要修改排版时，引导其点击该按钮打开 `url`。
此工具生成内容并保存到用户文章列表，但不保证发布或发送；不要声称已完成这些操作。

失败时业务错误通过 `isError: true` 及 `structuredContent` 中的 `code`、`data`、`message` 返回：

- `400` 或 JSON-RPC `-32602`：检查正文和参数，不提交空正文或多余参数。
- `401`：授权已失效或已被撤销，提示用户在连接器设置中断开后重新连接。
- `402`：点数不足或扣点失败，提示用户检查余额，不继续生成。
- `500`：服务配置或生成失败，说明失败并停止，不编造结果或余额。

可以使用 `get_ai_html_balance` 查询余额，但余额检查不保证后续扣点一定成功。
