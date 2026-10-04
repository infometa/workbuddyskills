---
name: wisenote
description: 使用百智 WiseNote 会议工具读取已授权的会议列表、会议摘要和会议转写内容。
version: "1.0.0"
author: "百智WiseNote"
---

# 百智 WiseNote

百智 WiseNote 提供只读的会议记录访问能力。仅在当前用户已经完成授权的前提下，可以读取该用户有权限访问的会议列表、会议详情摘要和会议转写内容。

当用户希望查询会议记录、回顾会议摘要、查找某次会议中的讨论内容，或基于会议转写定位信息时，可以使用本连接器。

## 可用工具

### wisenote_get_all_meeting

查询当前用户的 WiseNote 会议列表，支持分页和关键词搜索。

当用户询问最近会议、历史会议、会议列表，或者希望按标题/相关文本搜索会议时，优先使用这个工具。

参数：

| Name | Type | Required | Description |
| --- | --- | :---: | --- |
| pageNo | integer | No | 页码，默认值为 1。 |
| pageSize | integer | No | 每页数量，默认值为 10。 |
| search | string | No | 搜索关键词，可用于搜索会议标题或相关文本。 |

所需权限：`meeting.list`

### wisenote_get_meeting_summary

根据会议 ID 获取 WiseNote 会议详情和会议摘要。

当已经从会议列表或上下文中确定目标会议后，使用这个工具读取会议标题、时间、参会信息、详情和摘要。

参数：

| Name | Type | Required | Description |
| --- | --- | :---: | --- |
| meetingId | string | Yes | 来自会议列表返回结果的会议 ID。 |

所需权限：`meeting.read`

### wisenote_get_meeting_transcript

根据会议 ID 查询 WiseNote 会议转写片段。

当用户需要查看会议转写、发言内容、按说话人查看讨论，或者查找某个主题在会议中的原始讨论内容时，使用这个工具。

参数：

| Name | Type | Required | Description |
| --- | --- | :---: | --- |
| meetingId | string | Yes | 来自会议列表返回结果的会议 ID。 |

所需权限：`meeting.transcript.read`

## 使用规则

- 如果用户没有提供会议 ID，先调用 `wisenote_get_all_meeting` 查找目标会议。
- 如果用户提供了会议标题、参会人、日期或主题，优先使用更精确的搜索条件。
- 用户只需要会议概览、结论、待办或摘要时，优先使用 `wisenote_get_meeting_summary`。
- 只有在用户需要原始转写、逐字内容、发言人讨论或具体上下文时，才使用 `wisenote_get_meeting_transcript`。
- 不要声称可以访问当前授权账号以外的会议。
- 本连接器只提供只读能力，不能创建、编辑、删除或分享会议。
- 如果用户请求的能力没有获得授权，说明需要重新连接 WiseNote 并勾选对应权限。
