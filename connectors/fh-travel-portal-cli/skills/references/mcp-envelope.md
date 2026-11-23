# MCP 工具返回信封解析契约（references/mcp-envelope.md）

> 加载时机：任何 `tools/call` 返回需要判断成功/失败、或取出业务 JSON 时。
> 握手 `initialize.instructions` 与本文件同一套读法。失败分流见 [`error-handling.md`](error-handling.md)。

## 0. 两层返回，不要混

宿主眼里通常有两层：

1. **JSON-RPC / CallToolResult**：`result.content[]`，以及协议层 `structuredContent`（全部工具都有；失败也有占位）。
2. **content 信封**：`content[0].text` 是一份 JSON 字符串，`kind` 固定 `"mcp-tool-content"`。
   宿主通常**先**把这份全文给到 Agent：先看 `ok` / `error.message` / `summary`。

**读业务（全部工具统一）：**

```
落盘 shopping.json / tools/call
jsonrpc / id
└─ result
   ├─ content[0].text     ← 信封：kind/ok/summary（指引，不嵌业务）
   ├─ isError
   └─ structuredContent   ← 业务 JSON 对象，直接读
```

- 业务只在 `structuredContent`，就是 JSON 对象，直接读。
- `content[0].text` 信封：`ok=true` 时带 `hasMore=true` 与 `summary` 指引句；
  `ok=false` 读 `error.message`。**不要**把 `summary` 当业务。
- 正式 `outputSchema` 只在 `tools/list`（**可能没有**）；content 里不再带 outputSchema。

直接拆本轮工具返回（内联或本轮落盘文件）。不要去 skill 目录翻旧文件。大响应交给脚本。

## 1. 信封公共结构

- `kind`：固定字符串 `"mcp-tool-content"`
- `ok`：布尔值，决定走成功还是失败分支
- `requestSeqNo`：字符串

全部已启用工具都走这套信封，不是某一个工具的特例。

## 2. 成功信封（ok=true）

```json
{
  "kind": "mcp-tool-content",
  "ok": true,
  "requestSeqNo": "T260911124519B00000001",
  "hasMore": true,
  "summary": "工具从成功执行，返回结果请从MCP标准协议的structuredContent 字段获取，不在content里面。outputSchema请从tool/list调用的返回结果中获取"
}
```

**全部成功工具** content 都是这种形态。业务在 `structuredContent`，JSON 对象直接读。

解析规则：

1. **只认** `structuredContent` 为业务载荷，JSON 对象直接读。
2. `outputSchema` 去 `tools/list` 看（可能没有）；不在 content 里。
3. `summary` 指引句**不算**失败；「工具调用失败: …」且 `ok=false` 才是失败。

## 3. 失败信封（ok=false）

```json
{
  "kind": "mcp-tool-content",
  "ok": false,
  "requestSeqNo": "",
  "error": {
    "role": "error",
    "note": "本块是失败原因",
    "message": "业务错误: ... 或 工具调用失败: ...",
    "requestSeqNo": ""
  }
}
```

解析规则：

1. 以 `error.message` 作为失败原因，交给 [`error-handling.md`](error-handling.md)。
2. 失败分支**不得**使用成功字段（`summary` / `hasMore`）。

## 4. schema / 字段说明从哪来

1. **正式字段模式**：`tools/list` 该工具的 `outputSchema`（**可能没有**）。
2. content 信封不再嵌 schema。
3. 没有 tools/list schema 时按字段名/类型推断展示含义；决策只认 `structuredContent` 真值。

## 5. structuredContent / tools/list.outputSchema

- **全部成功工具**都带 `structuredContent`（最终业务；不再按是否挂 schema 分叉）。
- `tools/list.outputSchema`：有的工具有、有的没有（未挂为空）；信封内不重复下发。
- 解封用 `scripts/unwrap_content.py`。
