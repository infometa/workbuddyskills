---
name: gangtise-mcp
description: "Use Gangtise MCP tools for financial quotes, research reports, knowledge base, stock pools. WorkBuddy connects via standard MCP OAuth."
version: 1.1.0
author: Gangtise
metadata:
  category: connector
---

# Gangtise MCP

本 Skill 指导 AI 使用 **Gangtise MCP**。参数以 MCP `list_tools` schema 为准；下方为核心工具速查。

## 连接与凭证（WorkBuddy）

- **端点**：`https://open.gangtise.com/application/open-mcp/`
- **鉴权**：标准 MCP OAuth（OAuth 2.1 + PKCE）。用户点击连接后，WorkBuddy 自动完成元数据发现、动态客户端注册、浏览器授权，并在后续请求中注入 `Authorization: Bearer <access_token>`。
- **注册地址**（DCR）：`https://open.gangtise.com/application/oauth2server/oauth/register`
- 若授权失败 / 401：提示用户在连接器中重新连接并完成浏览器授权。

无需用户填写 Access Key / Secret Key。

## 能力总览（五域）

| 域 | 典型能力 |
|----|----------|
| **data** | 行情、财务、宏观 |
| **agent** | 研报、一页纸等 |
| **file** | 文件上传/解析 |
| **kb** | 知识库 |
| **private** | 股票池等 |

## 核心工具速查

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `quote` | 日 K / 分钟 K / 截面行情（CSV） | `securities` 或 `all_market_markets`；`data_type`；`start_date`/`end_date`；`adjust_mode` |
| `financial` | 利润表 / 资产负债 / 现金流 | `securities`；`table_type`；`period`；`fiscal_year` 或日期区间 |
| `opinion` | 国内机构首席观点检索 | `keyword`/`securities`；`start_date`/`end_date`；`institutions`/`chiefs` |
| `stock_one_pager` | 单标的「一页纸」投研摘要 | `security` 或 `securities`（推荐证券名称） |
| `viewpoint_debate` | 围绕投资观点生成多空辩论 | `viewpoint`（≤1000 字）；可选 `security`/`securities` |

其余工具（研报、纪要、估值、知识库、股票池等）以运行时 `list_tools` 返回为准。

## 使用原则

1. 先读 tool schema，勿臆造参数。
2. 标的代码与时间范围按工具说明填写；不确定时先向用户确认。
3. 无权限的工具不会出现在 `list_tools` 中，勿强行调用。
4. 超时可重试一次；业务错误说明原因后调整参数。

## English

- Transport: remote streamable HTTP.
- Auth (WorkBuddy): standard MCP OAuth (PKCE); WorkBuddy injects Bearer access token after browser consent.
- Prefer MCP tool schemas for parameters; see core tools table above for quick reference.
