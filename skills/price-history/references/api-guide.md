# 慢慢买 MCP 接入说明

> 真实信息以慢慢买官方 / MCPWorld 页面为准，本文档基于接入文档（抓取日期 2026-05-26）整理。
> MCPWorld：https://www.mcpworld.com/zh/detail/KwrNwkQznU9Xz3PJJqYuBG
> 官网：https://www.manmanbuy.com/

## 一、协议与传输

- 协议：MCP Server 1.0
- 传输：SSE（Server-Sent Events）
- SSE Endpoint：`https://mpc.manmanbuy.com/sse`

## 二、两种认证方式

### 方式一：Token 嵌入 URL

```json
{
  "mcpServers": {
    "mmb-mcp-server": {
      "url": "https://mpc.manmanbuy.com/sse?token=mmb_test_188"
    }
  }
}
```

### 方式二：Header 认证

```json
{
  "mcpServers": {
    "mmb-mcp-server": {
      "url": "https://mpc.manmanbuy.com/sse",
      "headers": {
        "Authorization": "认证的权限key"
      }
    }
  }
}
```

## 三、认证信息

| 项目 | 内容 |
|------|------|
| SSE Endpoint | `https://mpc.manmanbuy.com/sse` |
| 免费测试 Key | `mmb_test_188` / `mmb_baidu_188` |
| 免费有效期 | 文档写明 7.30 号前（可能延长，**以官方为准，可能调整**） |
| 计费模式 | 当前免费，后续可能调整为计费 |

> **Key 使用提示**：测试 Key 仅用于体验，额度/有效期有限且可能随时变更。正式、长期使用请向慢慢买申请专属授权 Key，避免共享测试 Key 失效导致服务中断。

## 四、可用工具（当前仅 1 个）

| 工具 | 参数 | 说明 |
|------|------|------|
| `searchZheKou`（搜索折扣） | `keyword`：搜索词 | 返回关键词相关的「参考好价」列表：商品名、参考价格、爆料时间、慢慢买导购页链接 |

- `keyword` 传入搜索词即可，如 `iphone16`。
- 实测返回为「参考好价」文本列表，**不含结构化的历史最低价/均价/价格曲线字段**。
- **注意**：平台对外宣传的"历史价格走势分析 / 降价监控 / 全网实时比价"等能力，在当前 MCP 工具列表中**尚未作为独立工具开放**。官方 FAQ 亦说明"目前提供全网折扣搜索，后续会持续更新工具接口"。因此本 Skill 的一切价格走势/历史分析均需基于该搜索工具的实际返回数据，不得假设其他工具存在。

## 五、使用步骤

1. 按上方 JSON 配置慢慢买 MCP Server。
2. 检查 server 是否连接成功。
3. 连接正常后，选择 Agent 交互模式。
4. 调用 `searchZheKou`（搜索折扣），`keyword` 传搜索词。

## 六、相关链接

- 官网：https://www.manmanbuy.com/
- 历史价格工具（网页版，非 MCP 工具）：https://tool.manmanbuy.com/HistoryLowest.aspx
- MCPWorld 页面：https://www.mcpworld.com/zh/detail/KwrNwkQznU9Xz3PJJqYuBG
