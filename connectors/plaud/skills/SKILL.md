---
name: plaud
description: 连接 Plaud 录音与 AI：浏览查找录音、读取转写和 AI 摘要、汇总会议纪要，并生成跟进邮件与待办事项。
version: "1.0.0"
author: "Plaud"
---

# Plaud 录音与会议纪要 Skill

本 Skill 通过 WorkBuddy Connector 接入 Plaud 官方 MCP 服务器（`https://mcp.plaud.cn/mcp`），让 AI 能以当前授权用户的身份访问其 Plaud 录音库：浏览、搜索录音，读取带说话人标签的转写与 AI 摘要，并在此基础上生成会议纪要、跟进邮件与待办事项。

## 认证说明（OAuth 2.1 + PKCE）

- **认证流程**：由 WorkBuddy 在用户首次连接时自动完成（401 → 元数据发现 → 动态客户端注册 → 浏览器授权 → Token 交换）。用户在浏览器中看到 Plaud 授权页，登录并点击允许即可，全程无需手动复制粘贴任何 Token。
- **Token 管理**：访问令牌由 WorkBuddy 安全存储并自动刷新（`access_token` 过期自动续期），用户无感。
- **重新授权**：如授权失效（令牌吊销 / 授权被撤销 / `refresh_token` 过期），AI 遇到 401 应如实提示「授权已失效，请在连接器设置中重新连接」，不要尝试自行传 Token。
- **授权端点**（由 `/.well-known/oauth-protected-resource` + `/.well-known/oauth-authorization-server` 自动发现，无需手填）：授权 `https://mcp.plaud.cn/authorize`，Token `https://mcp.plaud.cn/token`。
- 绝不向用户索取 API Key、密码或其他凭证，也不在日志中暴露凭证、授权头或音频临时链接。

## 可用工具（以 tools/list 实际返回为准）

| 工具 | 功能 |
|------|------|
| `list_files` | 列出录音，支持关键词（query）、日期范围（date_from / date_to）与分页筛选 |
| `get_file` | 单个录音完整详情（含 24 小时有效的临时音频 URL、转写片段、AI 笔记） |
| `get_note` | AI 生成的摘要、行动项与关键主题 |
| `get_transcript` | 带时间戳与说话人标签的完整转写文本 |
| `get_current_user` | 当前授权账户信息 |

工具清单以服务端 `tools/list` 实际返回为准；若服务端暴露 `login` / `logout` 等账户类工具，优先依赖 WorkBuddy 托管的 OAuth 连接状态，不要调用 `login` 重复授权。

## 使用约束

- 只读取当前授权用户自己的录音数据；不得尝试访问、猜测或枚举他人录音。
- 录音、转写与摘要属用户敏感数据（存储于 Plaud 云端）：仅在用户明确请求时按需读取，不要主动批量拉取全库录音。
- `get_file` 返回的音频 URL 为 24 小时有效的临时链接，仅用于响应用户明确请求，不得存储或转发到无关渠道。
- 会议纪要、跟进邮件等生成内容必须基于已读取的真实转写 / 摘要，不得编造会议内容。
