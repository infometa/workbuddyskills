---
name: emes-ai
description: "eMES AI Connector - 智连 eMES 制造执行系统，通过 MCP 协议对接鼎华 eMES 的 AI 能力（开发环境：amos-dev.digihua.com）。通过 OAuth 授权后，可调用 eMES 提供的 AI 工具进行生产数据查询、智能问数、派工调度、库存分析等业务场景的智能化操作。"
description_zh: "eMES AI 连接器 - 通过 MCP 协议对接鼎华 eMES（开发环境：amos-dev.digihua.com:14000）。OAuth 授权后即可调用 eMES 提供的 AI 工具，覆盖生产数据查询、智能问数、派工调度、库存分析等业务场景。"
description_en: "eMES AI Connector - Bridges to Dinghua eMES via MCP (dev: amos-dev.digihua.com:14000). After OAuth authorization, invoke eMES AI tools for production data queries, smart reporting, dispatch scheduling, inventory analysis, and other manufacturing execution scenarios."
version: "1.0.0"
author: "鼎华"
category: manufacturing
---

# eMES AI Connector

eMES AI 是鼎华 eMES（制造执行系统）的 AI 能力 MCP 连接器，对接开发环境 `amos-dev.digihua.com:14000`。**首次调用前需完成 OAuth 授权**。

## 使用流程

1. **首次使用**：点击 Connector 的「连接」按钮，按提示在浏览器完成 OAuth 授权（鼎华账号登录）。
2. **授权成功后**：调用 MCP 服务即可，无需手动填 API Key。
3. **Token 失效**：断开连接后重新授权即可。

## 鉴权说明

- **Connector 类型**：MCP Streamable HTTP + OAuth
- **MCP 地址**：`https://amos-dev.digihua.com:14000/mcp-platform/mcp/oauth/emes-ai`
- **认证方式**：WorkBuddy 第 11 章 MCP OAuth 流程（浏览器跳转授权页 → 用户登录 → 回调换取 token → 以 `Authorization: Bearer` 调 MCP）
- **不是 API Key 模式**：不要在工具调用时传任何 `api_key` / `token` / `user_id` 等字段，全部走 OAuth 透传

## 工具调用约定

- **可用工具**：通过 OAuth 连接后由 MCP 服务端动态暴露，具体工具列表在连接建立后通过 `list_tools` 获取
- **工具路由**：根据用户的具体业务诉求（如「查某工单进度」「派某设备」「看库存」）选择最匹配的 MCP 工具
- **参数口径**：以 MCP 服务端返回的工具描述（inputSchema）为准，**不要靠模型记忆编造工具名或参数**
- **结果呈现**：完整呈现 MCP 返回的结构化数据，保留口径（车间、设备、时间、单位等），空值不填 0、不得用模型常识补数

## 错误与边界

| 场景 | 处理建议 |
| --- | --- |
| 未 OAuth 授权 / 401 | 引导用户断开重连并完成浏览器登录 |
| 工具调用 401/403 | 检查 OAuth 授权是否过期，必要时重新连接 |
| 工具调用 5xx | 检查 eMES 开发环境 `amos-dev.digihua.com:14000` 是否可达；询问用户是否切到生产环境 |
| 返回空结果 | 检查参数口径（工单单号、设备编号、时间范围等），不要编造数据 |
| 工具列表为空 | 确认 OAuth 已授权；如仍为空请联系 eMES 开发确认服务端工具注册 |
| `isError: true` | 把错误原文贴给用户，并提示可能的原因（参数缺失、口径错误、服务端异常） |

## 注意事项

- 本 Connector 当前指向**开发环境**（`amos-dev.digihua.com`），发布到生产前需更新 `mcp.json` 中的 URL 为生产地址
- OAuth token 由 WorkBuddy 客户端统一管理，业务侧无需关心 token 刷新
- 涉及 eMES 业务口径（派工/工单/工艺/产能）时，严格遵循 eMES 产品口径，详见内部 eMES 文档