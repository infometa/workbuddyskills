---
name: speechclaw-openclaw
description: 访问思必驰AI办公产品的笔记、知识库、会议录音、总结和待办。
---

# 思必驰AI办公

通过 MCP 调用当前用户的思必驰 AI 办公产品服务，访问 AI 办公本、录音卡、超级笔等产品产生的笔记、会议录音、总结、知识库和待办。不要让用户在对话里提供 `userId`。

## 认证

- WorkBuddy 首次连接时完成 MCP OAuth 授权；服务端按授权会话绑定的用户和 scope 执行操作。
- 若工具返回未授权或权限不足，提示用户检查当前连接器授权或联系服务管理员重新授权。

## 工具选择

| 用户意图 | 工具 | 参数 |
| --- | --- | --- |
| 查询会议笔记 | `list_notes` / `get_note` / `get_note_content` | `note_uid`、`type` |
| 搜索笔记 | `search_note_knowledge` | `query` |
| 查询待办 | `list_todos` | 可选筛选条件 |
| 管理待办 | `create_todo` / `update_todo` / `delete_todo` | 按工具 schema |

## 调用顺序

1. 查询会议笔记正文时优先调用 `get_note_content(type=summary)`。
2. 只有摘要不足时，才按用户要求读取 `asr`、`ocr` 或 `insight`。
3. 不要自行拼接或猜测 `userId`，服务端会按当前授权绑定用户。

## 返回处理

- 优先用简短中文总结：笔记标题、时间、内容摘要、待办状态和截止时间。
- 不要完整复述授权 Token、密钥或大段原始 JSON。
- 搜索为空时，说明当前账号没有匹配的笔记或待办，并询问用户是否调整关键词或时间范围。
- 待办工具允许创建、更新和删除；笔记和知识库工具首期只读。
