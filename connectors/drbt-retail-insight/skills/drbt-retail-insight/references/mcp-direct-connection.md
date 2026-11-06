# MCP 直连通道

## 为什么需要它

drbt MCP 服务会在会话中途**从工具注册表掉线**。症状固定：

```
ToolSearch(tool_names=["mcp__drbt-retail-insight__销售明细表查询"])  -> No matching tools found
DeferExecuteTool("mcp__drbt-retail-insight__销售明细表查询", ...)     -> Tool "..." not found in the deferred tools index
```

换关键词搜工具索引（销售明细 / 进销存 / 库存报表 / 报表 / 销售 / 零售）也全部无结果。
**这不是参数错误，重试不会恢复。** 服务端本身仍然健康。

## 配置位置

```
C:\Users\11691\.workbuddy\mcp.json
```

结构：

```json
{
  "mcpServers": {
    "drbt-retail-insight": {
      "type": "http",
      "url": "https://api.drumbeatsoft.com/agent-mcp-v3/mcp",
      "headers": { "Authorization": "Bearer mcp_pat_..." },
      "disabled": false
    }
  }
}
```

`scripts/mcp_client.py` 在运行时读取该文件拿 url 与鉴权头，**skill 内不存 token**。

## 协议要点（streamable HTTP / JSON-RPC）

1. `POST` 同一个 url，body 为 JSON-RPC 2.0。
2. 必须的请求头：
   - `Content-Type: application/json`
   - `Accept: application/json, text/event-stream` ← **两个媒体类型都要写**，否则服务端拒绝
   - `Authorization: Bearer <token>`（来自配置）
   - `MCP-Protocol-Version: 2024-11-05`
3. 握手顺序：
   - `initialize` → 响应头 `mcp-session-id` 要保存下来
   - `notifications/initialized`（通知，无 id，无响应）
   - 之后每个请求都带上 `mcp-session-id`
4. 响应体可能是 **SSE**（逐行 `data: {...}`）也可能是**纯 JSON**，必须两种都兼容。
   服务端返回的 `protocolVersion` 是 `2025-11-25`（比客户端请求的新），无需校验。
5. `tools/call` 的结果在 `result.content[]` 里，`type == "text"` 的那一项 `text` 字段是**被 JSON 字符串包了一层**的业务数据，要再 `json.loads` 一次。

## 已注册的两个工具

| 工具 | 用途 |
|---|---|
| `销售明细表查询` | 销售明细 / 销售额 / 毛利 / 排名（金额可用） |
| `进销存报表` | 期初期末库存、出入库**数量**（金额被掩码） |

字段语义详见 `data-fields.md`。

## 排障顺序

1. 先跑 `drbt.py list` —— 能列出两个工具说明通道正常，问题在别处。
2. 报 `HTTPError 401/403` → token 失效，检查 `mcp.json`。
3. 报 `HTTPError 406` → 漏了 `Accept: text/event-stream`。
4. 报 session 相关错误 → 重新 `initialize` 拿新的 `mcp-session-id`。
5. 全部正常但仍取不到数 → 换日期区间试；注意 `total_row` 是全局汇总，`total` 才是行数。
