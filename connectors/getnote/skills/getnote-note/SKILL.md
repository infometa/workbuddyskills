---
name: getnote-note
description: 使用得到大脑 MCP 保存、浏览和读取笔记，查看原文、转写、附件、时间线、快捷笔记和会议待办，并安全更新、删除或公开分享。
---

# 得到大脑笔记

所有笔记、任务和父笔记 ID 都是不透明字符串，必须原样传递。只在 MCP Tool 返回成功结果后确认操作完成。

## 工具路由

| 用户意图 | MCP Tool |
|---|---|
| 浏览最近笔记 | `list_notes` |
| 查看笔记详情 | `get_note` |
| 读取链接或文字原文 | `get_note_original` |
| 读取录音、会议或课堂转写 | `get_note_transcript` |
| 查看图片、音频和文件附件 | `get_note_attachments` |
| 查看录音/会议时间线 | `get_note_timeline` |
| 查看录音快捷笔记 | `get_note_quick_note` |
| 查看会议总结中解析的待办 | `get_note_todos` |
| 保存文字、链接或图片笔记 | `save_note` |
| 查询异步创建任务 | `get_note_task_progress` |
| 修改已有纯文本笔记 | `update_note` |
| 移入回收站 | `delete_note` |
| 创建公开分享链接 | `share_note` |
| 查询图片上传限制 | `get_upload_config` |
| 获取图片上传凭证 | `get_upload_token` |
| 上传图片 | `upload_image` |

## 浏览与读取

- `list_notes.cursor` 首次省略，翻页时只把上次返回的游标原样传回。
- `get_note` 使用 `id`；需要原图时设置 `image_quality: "original"`。
- 不确定笔记类型时先调用 `get_note`：原文使用 `get_note_original`，录音转写使用 `get_note_transcript`，附件、时间线、快捷笔记和会议待办分别使用对应 Tool。
- `get_note_todos` 返回的是从明确会议总结章节按规则解析的待办，应保留其 `source`，不能宣称为上游原生任务。
- AI 摘要、搜索片段和原文是不同内容，不能相互冒充。

## 保存笔记

`save_note` 支持以下输入：

- 公共字段：`title`、`content`、`tags[]`、`parent_id`、`topic_id`、`client_request_id`。
- 纯文本：`note_type: "plain_text"`，正文放在 `content`。
- 链接：使用服务支持的链接类型并传 `link_url`；若返回异步 `task_id`，继续调用 `get_note_task_progress`，只有最终成功并返回真实笔记 ID 才算完成。
- 图片：先用 `get_upload_config` 确认限制；`upload_image` 接收 `image_base64` 和可选 `mime_type`，返回 `image_url` 后再通过 `image_urls[]` 保存。远程 MCP 不能直接读取调用方本地文件路径。

同一次创建及其网络重试必须复用同一个 `client_request_id`。超时或断流后先查询原任务或最近笔记，不直接再次创建，避免重复笔记。

## 更新、删除与分享

- `update_note` 使用 `note_id`，并只传用户明确要改变的 `title`、`content` 或 `tags`；未指定字段保持不变。
- 覆盖正文或替换全部标签前先说明影响并取得确认。
- `delete_note` 会把笔记移入回收站。调用前必须确认目标笔记，并在执行前取得用户明确确认；成功后只能说“已移入回收站”。
- `share_note` 会创建任何获得链接者都可能访问的公开链接。用户意图不明确时先确认；录音类笔记用 `share_exclude_audio` 明确是否排除音频。
- 用户未要求公开分享时，仅返回服务端已有的私有笔记链接，不自动调用 `share_note`。

## 成功与失败

- 上传成功不等于笔记创建成功，出现 `task_id` 也不等于异步任务完成。
- 只返回服务端给出的真实 ID、标题和 URL，不自行拼接。
- 工具错误时读取 `reason`、`message`、`retryable` 和可选 `request_id`。认证错误引导重新连接；仅对明确可重试的瞬时失败重试。
