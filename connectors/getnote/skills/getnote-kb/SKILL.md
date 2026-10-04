---
name: getnote-kb
description: 查看和管理得到大脑的个人、书籍、客户及团队知识库、目录、笔记归档、订阅博主与直播，并使用真实权限和字符串 ID 操作。
---

# 得到大脑知识库

知识库、目录、笔记、博主、内容和直播 ID 都是不透明字符串。先读取真实对象和权限，再执行写操作；不能用名称猜 ID。

## 工具路由

| 用户意图 | MCP Tool |
|---|---|
| 列出自有/可管理知识库 | `list_topics` |
| 列出订阅知识库 | `list_subscribe_topics` |
| 创建知识库 | `create_topic` |
| 浏览知识库笔记 | `list_topic_notes` |
| 批量加入笔记 | `batch_add_notes_to_topic` |
| 从知识库移出笔记 | `remove_note_from_topic` |
| 浏览目录与资源 | `list_topic_directories` |
| 创建目录 | `create_topic_directory` |
| 重命名或移动目录 | `update_topic_directory` |
| 删除空目录 | `delete_topic_directory` |
| 查看关注博主 | `list_topic_bloggers` |
| 关注博主 | `follow_topic_blogger` |
| 浏览博主内容 | `list_topic_blogger_contents` |
| 读取博主内容详情 | `get_blogger_content_detail` |
| 查看关注直播 | `list_topic_lives` |
| 读取直播详情 | `get_live_detail` |
| 关注直播 | `follow_topic_live` |

## 选择知识库

- `list_topics` 和 `list_subscribe_topics` 的 `scope` 可为 `DEFAULT`、`CUSTOMER`、`BOOKSPACE`、`TEAMSPACE`，省略时只查询 `DEFAULT`。用户问“全部知识库”时，应按这四种 Scope 分别查询并标明类型，不能只返回默认知识库。
- `page` 首次省略，按返回的分页信息继续；不要把页码当游标。
- 自有/可管理知识库与订阅知识库分别展示，不能混成同一种权限。订阅知识库默认按只读理解，除非返回结果明确证明可写。
- 按名称和 Scope 匹配；同名或用户意图不明确时让用户选择真实 `topic_id`。

## 笔记归档与目录

- `list_topic_notes` 使用 `topic_id` 和可选 `page`。
- `batch_add_notes_to_topic` 使用 `topic_id`、`note_ids[]` 和可选 `directory_id`；所有 ID 必须来自真实结果。写入后如果需要确认最终目录归属，应重新调用 `list_topic_directories` 或 `list_topic_notes`。
- `remove_note_from_topic` 会改变知识库归属，执行前确认目标知识库与笔记；成功只表示从该知识库移出，不代表删除笔记。
- `list_topic_directories` 省略 `directory_id` 浏览根目录，进入子目录时传服务返回的真实目录 ID。
- 创建目录使用 `topic_id`、`name` 和可选 `parent_id`；重命名/移动使用 `topic_id`、`directory_id`，仅传需改变的 `name` 或 `parent_id`。
- `delete_topic_directory` 只能删除空目录，且必须在调用前取得用户明确确认。目录非空时不重试删除，应让用户先处理目录内容。

## 博主与直播

- 关注前确认目标知识库及写入意图，不因用户只是查看一条内容而自动建立订阅。
- `follow_topic_blogger` 使用 `topic_id`、主页 `link` 和可选 `platform`，平台省略时默认 `douyin`。
- 博主列表返回的真实关注 ID 用作 `list_topic_blogger_contents.follow_id`；内容详情使用返回的真实 `post_id`。
- 直播列表返回的真实 `live_id` 用于 `get_live_detail`；`follow_topic_live` 使用直播 `link`。
- 内容详情中的完整正文与摘要必须区分；没有完整正文时不能用摘要补写。

## 失败处理

空列表是成功结果，不自动创建知识库、目录或订阅。权限不足、目录非空、对象不存在等失败必须如实说明；保留 `reason`、`retryable` 和 `request_id`，不能绕过权限或伪造成功。
