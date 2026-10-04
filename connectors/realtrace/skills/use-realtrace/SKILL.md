---
name: use-realtrace
display_name: 使用 RealTrace
display_name_en: Use RealTrace
description: Use RealTrace MCP for evidence-based commerce and social media research when the user needs live products, reviews, posts, comments, creators, rankings, captions, or durable collection tasks.
description_zh: 使用 RealTrace MCP 查询和分析实时电商与社媒数据。
description_en: Use RealTrace MCP to query and analyze live commerce and social media data.
version: 1.0.1
author: Cangxuan Data
---

# 使用 RealTrace

当用户需要查询或分析电商、社媒、创作者、评论、榜单或字幕数据时，使用 RealTrace MCP。不要凭空补全实时数据，也不要把搜索结果描述成整个平台的完整快照。

## 开始调用

首次使用 RealTrace 时先调用 `get_agent_instructions(section="index")`。调用数据工具前读取 `section="core"`，再只读取当前任务对应的一层：

- 商品、店铺、评论或榜单：`commerce`
- 帖子、视频、社媒评论或回复：`social`
- 创作者、账号内容或字幕：`creators`
- 长时间采集任务：`tasks`

需要更多数据时读取 `more_data`，然后只读取对应的一个 `more_*` 层。遇到分页、错误恢复或费用问题时读取 `pagination_errors_billing`。工具的实时 `description` 和 `inputSchema` 始终优先于本文件中的静态说明。

## 选择工具

- `get_agent_instructions`：读取最新调用规则。
- `search_products`：按关键词搜索商品。
- `get_product_details`：读取单个商品详情。
- `get_product_reviews`：读取商品评论。
- `get_shop_info`：读取 TikTok Shop 店铺信息。
- `get_rankings`：读取 Amazon 排行榜。
- `get_brandshop_products`：读取 Amazon 品牌店商品。
- `search_posts`：搜索 TikTok、YouTube、Reddit、Facebook 或 Instagram 内容。
- `get_post_details`：读取单条帖子或视频详情。
- `get_social_comments`：读取社媒内容评论。
- `get_comment_replies`：读取支持平台的评论回复。
- `get_creator_info`：读取创作者资料。
- `get_creator_posts`：读取创作者发布的内容。
- `get_captions`：读取 YouTube 字幕。
- `start_product_review_collection`：启动可断点续跑的大批量商品评论采集。
- `list_collection_tasks`：列出当前用户的采集任务。
- `get_collection_task_status`：等待或检查任务进度。
- `cancel_collection_task`：取消任务；用户没有明确要求取消时，调用前先确认。
- `resume_collection_task`：恢复失败或部分取消的任务。
- `get_collection_task_result`：分页读取已持久化的任务结果。

## 工具参数速查（1.0.1）

以下是发布时的参数摘要：`*` 表示必填，`?` 表示可选，`=` 表示默认值。服务返回的实时 `description`、`inputSchema` 和 `tools/list` 始终优先；本节只用于帮助规划调用。

- `get_agent_instructions`：`section?` string=`index`。
- `search_products`：`keyword*` string；`platform?` string=`amazon`；`limit?` integer=10；`ai_enhance?` boolean=false；`cursor?` string=""；`domain_name?` string=""。
- `get_product_details`：`item_id*` string；`platform?` string=`amazon`；`ai_enhance?` boolean=false；`domain_name?` string=""。
- `get_product_reviews`：`item_id*` string；`platform?` string=`amazon`；`limit?` integer；`target_count?` integer；`ai_enhance?` boolean=false；`min_rating?` integer；`max_rating?` integer；`verified_only?` boolean=false；`sort_by?` string=`default`；`cursor?` string=""；`domain_name?` string=""。
- `get_social_comments`：`target_id*` string；`platform*` string；`limit?` integer=10；`ai_enhance?` boolean=false；`sort_by?` string=`default`；`cursor?` string=""。
- `get_comment_replies`：`comment_id*` string；`platform*` string；`limit?` integer=10；`ai_enhance?` boolean=false；`cursor?` string=""；`video_id?` string=""。
- `get_shop_info`：`product_id*` string；`platform?` string=`tkshop_us`；`ai_enhance?` boolean=false。
- `get_rankings`：`category_url?` string；`limit?` integer=10；`ai_enhance?` boolean=false；`cursor?` string=""。
- `search_posts`：`keyword*` string；`platform?` string；`limit?` integer；`ai_enhance?` boolean=false；`content_type?` string；`sort_by?` string；`cursor?` string；`platforms?` object。
- `get_post_details`：`url*` string；`platform*` string；`ai_enhance?` boolean=false。
- `get_creator_info`：`creator_id*` string；`platform*` string；`ai_enhance?` boolean=false。
- `get_creator_posts`：`platform*` string；`account_id*` string；`account_url?` string=""；`limit?` integer=10；`cursor?` string=""；`content_type?` string=`video`；`ai_enhance?` boolean=false。
- `get_captions`：`video_url*` string；`platform?` string=`youtube`；`ai_enhance?` boolean=false。
- `get_brandshop_products`：`brandshop_id*` string；`keyword?` string=""；`limit?` integer=10；`ai_enhance?` boolean=false；`enrich?` boolean=false；`domain_name?` string=""；`cursor?` string=""。
- `start_product_review_collection`：`item_id*` string；`platform?` string=`amazon`；`max_items?` integer=5000；`batch_limit?` integer=100；`min_rating?` integer；`max_rating?` integer；`verified_only?` boolean=false；`sort_by?` string=`default`；`domain_name?` string=""；`on_conflict?` string=`ask`；`force_refresh?` boolean=false。
- `list_collection_tasks`：`include_finished?` boolean=false；`limit?` integer=20。
- `get_collection_task_status`：`task_id*` string；`wait_seconds?` integer=0；`after_version?` string=""。
- `cancel_collection_task`：`task_id*` string。
- `resume_collection_task`：`task_id*` string。
- `get_collection_task_result`：`task_id*` string；`limit?` integer=100；`cursor?` string=""。

## 最小调用示例

以下示例用于说明参数形状；实际平台值、ID 和 URL 必须来自当前任务或上一步工具响应：

- `get_agent_instructions`: `{"section":"index"}`
- `search_products`: `{"keyword":"smoke alarm","platform":"amazon","limit":20}`
- `get_product_details`: `{"item_id":"B0CJMP7WHH","platform":"amazon"}`
- `get_product_reviews`: `{"item_id":"B0CJMP7WHH","min_rating":1,"max_rating":1,"limit":20}`
- `get_social_comments`: `{"target_id":"7123456789","platform":"tiktok","limit":10}`
- `get_comment_replies`: `{"comment_id":"UgxCommentId","video_id":"74-dXafKB4Y","platform":"youtube","limit":20}`
- `get_shop_info`: `{"product_id":"1730084177840870362","platform":"tkshop_us"}`
- `get_rankings`: `{"category_url":"https://www.amazon.com/Best-Sellers-Smoke-Detectors/zgbs/hi/495270","limit":30}`
- `search_posts`: `{"keyword":"fire safety home","platforms":{"youtube":{"limit":10,"sort_by":"newest"}}}`
- `get_post_details`: `{"url":"https://www.reddit.com/r/Home/comments/abc123","platform":"reddit"}`
- `get_creator_info`: `{"creator_id":"username","platform":"tiktok"}`
- `get_creator_posts`: `{"platform":"youtube","account_id":"UCxxxxxxxxxxxxxxxxxxxxxx","limit":10}`
- `get_captions`: `{"video_url":"https://www.youtube.com/watch?v=74-dXafKB4Y","platform":"youtube"}`
- `get_brandshop_products`: `{"brandshop_id":"F2EA1BDC-1CBB-45F8-A05E-EF75A20B8A50","limit":5,"enrich":true}`
- `start_product_review_collection`: `{"item_id":"B08N5WRWNW","platform":"amazon","max_items":1000,"batch_limit":100,"on_conflict":"ask"}`
- `list_collection_tasks`: `{"include_finished":false,"limit":20}`
- `get_collection_task_status`: `{"task_id":"collect_<task_id>"}`
- `cancel_collection_task`: `{"task_id":"collect_<task_id>"}`
- `resume_collection_task`: `{"task_id":"collect_<task_id>"}`
- `get_collection_task_result`: `{"task_id":"collect_<task_id>","limit":100,"cursor":""}`

## 调用与返回示例

首次读取契约，再读取对应业务层：

```json
{"section":"index"}
```

普通查询的典型成功结果是包含 `data` 的 JSON 对象；有更多结果时会返回不透明的 `next_cursor`：

```json
{"data":[{"item_id":"..."}],"next_cursor":"<opaque>","data_is_final":true}
```

调用可能转为持久后台任务时，响应会明确标记，不能把空 `data` 当作空结果，也不能重复提交原请求：

```json
{"response_type":"background_task_acknowledgement","data":[],"data_is_final":false,"task_id":"collect_<id>","progress_version":"<version>","next_action":{"tool":"get_collection_task_status"}}
```

先用 `get_collection_task_status` 等待进度变化，再用 `get_collection_task_result` 按 `next_cursor` 读取结果。`retryable=false` 或 `retry_with_same_arguments=false` 时按响应中的 `next_action` 处理，不要原参数重试。

## 输入与链路规则

1. 用户只给出名称、关键词或主题时，先搜索，再从搜索结果取工具要求的标准 ID。不要把名称、标题或关键词直接填入 `*_id`。
2. 只有实时 schema 明确允许 URL 的参数才可传 URL；无法安全转换时向用户索取所需标识。
3. 每个数据工具请求只访问一个平台。跨平台比较应按平台分别调用，再合并结果，并清楚标注数据来源。
4. 同一业务链路保持站点、平台和对象标识一致。例如 Amazon 搜索、详情和评论应使用同一站点。
5. Facebook 或 Instagram 等需要详情解析评论入口的平台，遵循“搜索 → 详情 → 评论”的返回指引。

## 分页与长任务

- `limit` 或 `target_count` 是目标上限，不是结果数量保证。
- `next_cursor` 是不透明值，只能逐字传回原工具、原平台和原查询条件。不得构造、修改、解码或跨查询复用。
- 当响应包含 `response_type=background_task_acknowledgement`、`execution_mode=background` 或 `data_is_final=false` 时，空 `data` 不代表没有结果。保存返回的 `task_id` 和 `progress_version`，按 `next_action` 查询状态并读取结果，不要重复提交原业务调用。
- 读取任务状态时原样传递最新 `progress_version`；读取任务结果时按返回的 `next_cursor` 续页。
- 用户要求数百条或尽可能多的数据时，先确认平台、对象、数量和筛选范围。若会明显增加 Credits 或调用次数，说明预计调用方式并取得用户同意后再扩大范围。

## 错误、安全与交付

- `retryable=false` 或 `retry_with_same_arguments=false` 时禁止原参数重试；优先执行响应中的 `next_action`。
- 授权失效时请用户在 WorkBuddy 中重新连接 RealTrace。不要让用户把 API Key 发到对话中，也不要在输出、日志或文件里展示凭证。
- 参数错误应在调用上游前纠正；暂时性错误只进行有界重试，不进行无限循环。
- 最终回答说明平台、查询范围、实际获得数量、时间或排序条件，以及结果不足或上游限制。区分实时查询结果、抽样结果和完整采集任务结果。
