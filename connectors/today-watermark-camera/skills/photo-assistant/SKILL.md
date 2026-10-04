---
name: photo-assistant
description: 今日水印相机团队照片查询、统计、排行、原图查看和导出技能
version: "1.0.0"
author: "XHEY"
---

# 今日水印相机照片助手

本 Skill 用于在当前用户有权访问的团队范围内查询和导出今日水印相机照片。始终遵守工具返回的可见范围和实际生效时间，不要猜测团队 ID、用户 ID 或部门 ID。

## 调用原则

1. 统计总量优先用 `get_photos_count`，成员拍照张数排行必须用 `get_photo_ranking_by_user`。
2. 按关键词查照片用 `search_photos`；已有用户和时间、要原图链接时用 `query_photos`。
3. 分页工具必须按返回游标或 `count < limit` 判断结束，不可只取第一页后声称是全量。
4. 只有用户明确要求“导出、下载、打包”时才调用 `export_photos`。
5. `export_photos` 提交成功后直接提示用户在下载列表查看，不要轮询；`export_photos_downloads` 仅用于用户明确要求列出全部导出历史。
6. 时间格式使用 `2006-01-02 15:04:05`。未提供时间时，多数查询默认最近半年；以工具响应中的实际时间范围为准。
7. 单个用户仍必须使用数组参数 `user_ids: ["xuser-..."]`，单个部门也必须使用字符串数组 `department_ids: ["123"]`。所有工具的 `department_ids` 类型均为 `string[]`，不得传裸值或数字数组。
8. `caller_user_id`、当前用户 ID 和团队信息必须来自 MCP OAuth 鉴权上下文，不得要求用户手工输入，也不得根据昵称或历史对话猜测。
9. `search_photos` 建议从 `page_size: 500` 开始按游标分批查询；只有确有必要时才逐步增大，避免单次大查询超时。

## 可用工具

### `resolve_photo_view_scope`

解析调用者在指定团队中的照片可见范围。通常由服务端兜底调用，普通问答不要无故调用。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `group_id` | string | 是 | 团队短 ID |
| `caller_user_id` | string | 是 | 当前登录用户 ID；由 MCP OAuth 鉴权上下文提供，不是用户输入参数 |

### `search_photos`

按时间、关键词、拍摄者、部门和媒体类型分页搜索照片；`semantic` 模式适合自然语言或模糊关键词。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `group_id` | string | 是 | 团队短 ID |
| `group_id_real` | string | 否 | 团队长 ID；有可靠上下文时才传 |
| `user_id` | string | 否 | 当前用户 ID；必须来自可信上下文，不要猜测 |
| `search_mode` | string | 否 | `exact`（默认）或 `semantic` |
| `start_time` / `end_time` | string | 否 | 查询时间范围 |
| `keywords` | string[] | 否 | 水印关键词 |
| `watermark_name` | string | 否 | 水印模板名精确筛选 |
| `user_ids` | string[] | 否 | 拍摄者 ID 列表 |
| `department_ids` | string[] | 否 | 部门 ID 列表 |
| `media_types` | integer[] | 否 | `0` 照片、`1` 视频 |
| `source_types` | integer[] | 否 | 照片来源类型 |
| `is_and` | integer | 否 | `0` 任一关键词，`1` 全部关键词 |
| `exist_photo_comment` | integer | 否 | `0` 不筛选、`1` 无评论、`2` 有评论 |
| `page_size` | integer | 否 | 每页数量，最大 5000 |
| `last_page_cond` | string | 否 | 上一页游标；返回空表示结束 |

### `get_photos_count`

快速统计符合条件的照片数量。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `group_id` | string | 是 | 团队短 ID |
| `start_time` / `end_time` | string | 否 | 统计时间范围 |
| `user_ids` / `exclude_user_ids` | string[] | 否 | 包含或排除的用户 |
| `department_ids` | string[] | 否 | 部门 ID 列表，例如 `["123"]` |
| `keywords` / `exclude_keywords` | string[] | 否 | 包含或排除的水印关键词 |
| `watermark_name` | string | 否 | 水印模板名 |
| `media_types` / `source_types` | integer[] | 否 | 媒体和来源类型 |
| `is_and` | integer | 否 | 关键词关系；默认 `1` 全命中，`0` 任一命中 |
| `exist_watermark` | integer | 否 | 是否存在水印的筛选条件 |
| `locations` | string[] | 否 | 精确地点列表 |
| `location_key` | string | 否 | 地点关键词；只知道地名时优先使用 |
| `label_ids` | integer[] | 否 | 照片标签 ID 列表 |
| `label_match_all` | boolean | 否 | 是否要求命中全部标签 |

### `get_photo_ranking_by_user`

一次返回成员拍照张数 Top N。它统计的是照片张数，不是拍照天数。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `group_id` | string | 是 | 团队短 ID |
| `start_time` / `end_time` | string | 否 | 排行时间范围 |
| `user_ids` / `exclude_user_ids` | string[] | 否 | 限定或排除用户 |
| `department_ids` | string[] | 否 | 限定部门，例如 `["123"]` |
| `keywords` | string[] | 否 | 按水印关键词过滤 |
| `top_n` | integer | 否 | 默认 10，最大 50 |

### `query_photos`

按用户、时间、照片序号或文件名分页查询完整照片记录，结果自带原图和缩略图 URL。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `group_id` | string | 是 | 团队短 ID |
| `user_ids` | string[] | 否 | 用户 ID 列表 |
| `photo_seqs` | integer[] | 否 | 照片序号，优先级最高 |
| `file_names` | string[] | 否 | 文件名，优先级次之 |
| `start_time` / `end_time` | string | 否 | 照片时间范围 |
| `offset` | integer | 否 | 分页偏移，默认 0 |
| `limit` | integer | 否 | 每页数量，最大 500 |
| `order_by` | string | 否 | 例如 `photo_time DESC` |
| `select` | string | 否 | 需要返回的字段列表，逗号分隔；无明确需要时不传 |

### `export_photos`

异步打包导出原始照片和视频。仅在用户明确要求导出时调用。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `group_id` | string | 是 | 团队短 ID |
| `start_time` / `end_time` | string | 否 | 导出时间范围 |
| `department_ids` / `user_ids` | string[] | 否 | 部门或拍摄者过滤 |
| `keywords` / `exclude_keywords` | string[] | 否 | 包含或排除关键词 |
| `watermark_name` | string | 否 | 水印模板名 |
| `max_count` | integer | 否 | 本次任务的导出总量上限（不是分页大小），默认 5000，最大 15000 |

成功提交后告诉用户：“已开始打包，可在下载列表查看进度，完成后会有提示。”不要展示内部任务 ID，不要主动轮询。

### `export_photos_downloads`

列出当前团队的导出历史。不要用它轮询刚提交的单个任务。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `group_id` | string | 是 | 团队短 ID |
| `offset` | integer | 否 | 历史记录分页偏移量，默认 0 |
| `limit` | integer | 否 | 本次最多返回的历史记录数，默认 20，最大 100 |

## 常用调用链示例

### 查询并导出指定范围的照片

1. 用 `search_photos` 确认时间、成员或部门条件下是否有照片。
2. 用户明确要求下载后，使用相同筛选条件调用 `export_photos`。
3. 提交成功后提示用户去下载列表查看，不调用 `export_photos_downloads` 轮询单个任务。

### 统计并核对团队拍照情况

1. 用 `get_photos_count` 获取指定时间范围内的照片总数。
2. 需要成员对比时调用 `get_photo_ranking_by_user` 获取拍照张数排行。
3. 如需核对具体照片，再用 `search_photos` 或 `query_photos` 查询明细；统计结果仅辅助考勤核对，不直接判定出勤。

### 列出历史导出记录

只有用户明确要求查看全部历史导出时才调用 `export_photos_downloads`；从 `offset: 0, limit: 20` 开始，并根据返回的 `has_more` 翻页。刚提交的导出任务仍由下载列表展示进度。

## 错误与边界

- 工具返回权限不足或空可见范围时，不要换参数绕过权限。
- 非 VIP 团队可能只可见最近 91 天，以返回的生效范围为准。
- 排行结果如有 `truncated: true`，明确告知结果只覆盖已处理照片，并建议缩短时间范围。
- 上游不可用、限流或导出为空时，向用户说明当前状态；不要编造结果或下载链接。
- OAuth 过期由 WorkBuddy 自动刷新；若 Refresh Token 也失效，引导用户重新连接今日水印相机。

更完整的错误分类、用户提示和排查方式见 [`references/error-handling.md`](../../references/error-handling.md)。
