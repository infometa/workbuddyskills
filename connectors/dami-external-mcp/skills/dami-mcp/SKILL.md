---
name: dami-mcp
display_name: 达秘-TikTok批量建联&达人管理工具
display_name_en: Dami TikTok Bulk Outreach & Creator Management Tool
description: 使用达秘 MCP 查询 TikTok 店铺、商品和达人，并执行批量建联、邀约或私信任务；每次业务 Tool 调用都必须动态生成幂等键。
description_zh: 使用达秘 MCP 查询 TikTok 店铺、商品和达人，并执行批量建联、邀约或私信任务；每次业务 Tool 调用都必须动态生成幂等键。
description_en: Use Dami MCP to query TikTok shops, products, and creators, and perform bulk outreach, invitation, or messaging tasks with a dynamic idempotency key for every business tool call.
version: 1.0.0
author: 达秘
---

# 达秘-TikTok批量建联&达人管理工具 External MCP 使用说明

## 基本流程

1. 先调用 `shop_auth_list` 获取当前账号可访问的店铺。
2. 后续需要店铺的 Tool 使用返回的真实 `shopId`。
3. 严格按照 `tools/list` 返回的实时 Schema 传参，不要猜测旧参数。
4. `Idempotency-Key` 不要写进静态请求头配置；在每次新的 `tools/call` 里由 agent 按规则动态生成并拼接到请求头，同一次网络重试复用原值。

## 安全约束

不要传入 `tenantId`、`billingUserId`、`accessToken`、`current_user`、`xShopId`、`xShopRegion`、`sessionId` 或 `selectionRequired`。

## 高风险操作

执行邀约、私信、自动匹配创建等有副作用的操作前，先向用户说明将执行的操作并获得确认。

## 结果和错误

Tool 业务结果读取 `result.structuredContent`；失败时读取 `result.isError`、`result.structuredContent.code` 和 `message`。HTTP 200 不代表业务成功。
