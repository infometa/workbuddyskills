# WorkBuddy 工具与常用流程

先按主 Skill 确认授权，再执行用户任务。工具名称、可选参数和限制以本连接器的实时 schema 为准。

## 需求与工具

| 用户需求 | 工具 | 关键参数/后续 |
| --- | --- | --- |
| 连接检查、当前账户 | `patchxnote_get_current_user` | `{}`；成功才确认账户可访问 |
| 绑定的录音卡 | `patchxnote_list_recorder_cards` | `{}`；只展示返回的设备信息 |
| 剩余额度 | `patchxnote_get_quota_summary` | `{}` |
| 模型使用情况 | `patchxnote_get_model_usage_summary` | `{}` |
| 最近记录/总结 | `patchxnote_list_memories` | `platform`，按需 `limit`、`cursor` |
| 按关键词找记录 | `patchxnote_search_memories` | `platform`、`query`；按当前服务的搜索说明处理 |
| 一条记录的详情/元数据 | `patchxnote_get_memory` | `platform`、`memory_id`，ID 来自列表/搜索 |
| 可复制的 Markdown 笔记 | `patchxnote_render_webhook_message` | `memory_id`、明确 `platform`；读取返回的 Markdown |
| 可用模板 | `patchxnote_list_webhook_templates` | `{}`；选返回的模板标识 |
| 已配置的投递目标 | `patchxnote_list_webhook_targets` | 按需 `include_disabled` |
| 配置/移除目标 | `patchxnote_configure_webhook_target` / `patchxnote_remove_webhook_target` | 使用 `alias` 和当前 schema 的字段 |
| 用户明确要求投递 | `patchxnote_send_webhook` | `target_aliases`，以及用户选择的 `memory_id` 或 `markdown` |
| 查找 AI 处理记录 | `patchxnote_list_model_io_traces` | `platform`，按需日期、任务类型和分页 |
| 查看实际整理结果 | `patchxnote_get_model_io_parsed_result` / `patchxnote_get_model_io_packaged_result` | 使用实际返回的 `request_id` 或 `memory_id`，并明确 `platform` |
| 用户明确要求查看处理输入/响应 | `patchxnote_get_model_io_source_text` / `patchxnote_get_model_io_provider_response` | 同上；仅按用户需要读取相应字段 |
| 用户明确要求导出模型数据 | `patchxnote_export_model_io` | 先检查当前远程模式的内容返回能力，不能假定可写本地路径 |

## 最近记录

```json
{"platform":"mobile","limit":5}
```

将以上参数传给 `patchxnote_list_memories`。用户指定桌面端时使用 `desktop`；不要混合两个平台的统计。时间范围由真实时间戳判断，不用标题推断日期。

“最近一次”从列表选最近的可读记录。调用详情时使用参数名 `memory_id`，值取真实记录 ID，不编造 ID，也不要求首次用户先提供“这条记录”。

搜索未找到时可以检查当前平台的列表；分页使用服务器返回的 cursor。计数时区分 `event_summary` 与 `daily_digest`，说明是否已遍历所有页。

## 三句首次使用示例

1. 登录连接：账户工具 → 手机端列表。空列表也能证明读取链路成功，但应明确暂无记录。
2. 最近总结：取得最近记录及其可读总结，展示时间、标题和主要内容；需要更多正文时使用记录渲染或实际整理结果工具。
3. 可复制笔记：列表 → 实际 `memory_id` → `patchxnote_render_webhook_message` → 读取 Markdown → 展示笔记。只有元数据不算完成；若返回内容不可用，说明对应记录的可用状态，不编造正文。

渲染参数形状如下，将 `memory_id` 替换为上一工具真实返回的 ID：

```json
{"memory_id":"<returned-id>","platform":"mobile"}
```

当前本地 stdio 转发到远程服务，渲染结果返回内容；不要设置 `save_draft=true`、`out` 或本地文件路径。不因工具名中有 webhook 就执行发送。

## 手动投递与模型字段

Webhook 配置、删除和发送按用户明确请求执行；先确认目标别名和内容来源，不从“整理成笔记”推导出发送动作。远程模式不使用本地 `draft_dir`。

模型字段按用户请求读取，使用列表返回的真实标识。普通总结查询优先读取整理结果，不默认获取完整原文或 provider payload。回复保留任务所需内容即可。
