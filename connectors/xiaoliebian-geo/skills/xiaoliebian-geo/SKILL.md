---
name: xiaoliebian-geo
display_name: 小裂变GEO
display_name_en: Xiaoliebian GEO
description: 小裂变 GEO 业务查询、分析与管理技能。用户说“看一下 GEO 数据”“查看竞品表现”“创建优化单元”“生成文章”“提交发布记录”，或要求管理 GEO 品牌、目标用户、优化单元、用户意图、引文检测、文章、内容优化、知识库或发布记录时使用。
description_zh: 小裂变 GEO 业务查询、分析与管理技能，覆盖品牌、目标用户、优化单元、用户意图、引文检测、看板、产品、文章、内容优化、知识库和发布记录。
description_en: Query, analyze, and manage Xiaoliebian GEO brands, target users, topics, questions, citations, dashboards, products, articles, content optimization, knowledge bases, and publishing records.
version: 1.0.2
author: 小裂变
allowed-tools: geo_brand_list,geo_brand_get,geo_brand_seat_count,geo_brand_agent_access,geo_brand_create,geo_brand_update,geo_brand_target_user_list,geo_brand_target_user_get,geo_brand_target_user_create,geo_brand_target_user_update,geo_brand_target_user_delete,geo_topic_list,geo_topic_get,geo_topic_questions,geo_topic_count,geo_topic_question_count,geo_topic_task_result,geo_topic_create,geo_topic_update,geo_topic_delete,geo_topic_batch_create,geo_topic_batch_delete,geo_topic_batch_status,geo_topic_expand,geo_topic_expand_questions,geo_question_list,geo_question_add,geo_question_batch_add,geo_question_update,geo_question_delete,geo_detection_list,geo_detection_stats,geo_detection_brand_records,geo_detection_rank,geo_detection_detail,geo_detection_emotion_overview,geo_detection_emotion_trend,geo_detection_competitor_matrix,geo_detection_competitor_question,geo_detection_manual_resume,geo_template_list,geo_article_list,geo_article_get,geo_article_create,geo_article_generate,geo_article_generation_task_result,geo_article_douyin_image_progress,geo_article_update,geo_article_update_cover,geo_article_update_douyin_detail,geo_article_regenerate_cover,geo_image_material_list,geo_article_delete,geo_article_history_list,geo_article_recover,geo_dashboard_summary,geo_dashboard_trend,geo_dashboard_topic_page,geo_content_list,geo_content_get,geo_content_delete,geo_kb_list,geo_kb_get,geo_kb_preview,geo_kb_articles,geo_publish_platform_types,geo_publish_account_list,geo_publish_record_list,geo_publish_submit,geo_product_page,geo_product_analysis_overview
---

# 小裂变 GEO 业务操作

## 执行约束

- 远程 MCP 工具目录是能力唯一事实源。当前注册 71 个后端直连工具；不要调用未注册函数，也不要替用户猜测缺失参数。
- 远程 MCP 使用标准 OAuth，WorkBuddy 自动携带 Bearer Token；不得向用户索要 Token、API Key 或认证文件。
- 品牌不明确时先查询品牌列表并让用户选择；品牌维度统计和管理必须确认单一品牌。
- 调用参数严格使用 MCP 工具 Schema 的键名和类型；不确定时先读取工具描述。
- 工具返回 JSON 只在内部处理；对用户用中文表格、列表或摘要展示。
- 向用户询问时间时只使用“开始时间/结束时间”和具体年月日、时分秒。只提供日期时，开始时间按当天 `00:00:00`、结束时间按当天 `23:59:59`；只到分钟时秒数补 `00`。
- 检测数据内部解析字段含义：`brandName`/`competitorName` 表示品牌，`visibility`/`visibilityRate` 表示可见度，`recommendRate` 表示推荐度；`KIMI`、`WENXIN`、`DOUBAO`、`QWEN`/`QIANWIAN`、`DEEPSEEK`、`YUANBAO` 分别对应 Kimi、文心一言、豆包、通义千问、DeepSeek、腾讯元宝。
- 对用户只输出中文业务名称和已确认的指标含义；不展示 camelCase 字段、接口键名、品牌/优化单元内部 ID 或平台代码。ID 只在调用工具时内部使用。
- 可见度、推荐度等数值按接口原值展示；接口未明确百分比单位时，不得自行添加 `%` 或换算。
- 空结果、接口错误和“品牌版本不支持”必须如实反馈；不得用浏览器、其他插件或手工数据兜底。
- 授权失效时引导用户重新连接小裂变GEO；其他错误保留可读信息，不暴露完整 JSON 或原始凭证。

## 高风险操作规则

- 创建和更新操作必须来自用户明确请求；目标、名称、归属品牌和必填业务字段完整后才可调用。
- 创建文章或抖音图文前，必须先调用 `geo_template_list` 按内容场景取模板；普通文章用 `CONTENT`、抖音图文用 `DOUYIN_IMAGE_TEXT`，`templateId` 必填且必须来自该工具返回结果。模板列表为空时告知用户需先配置模板，不得自行编造模板 ID。
- 删除、批量删除、恢复历史版本、提交发布记录前，必须向用户复述将操作的对象、范围、内容和发布账号，并获得明确确认。
- 批量启用/禁用前必须确认优化单元范围和新状态。
- `geo_publish_submit` 只创建发布记录，不承诺平台最终发布成功；调用后按返回记录说明已提交。
- 异步拓展工具只返回任务 ID；需要调用 `geo_topic_task_result` 轮询，间隔不要太短，最终结果以后端状态为准。

## 能力映射

| 业务对象 | 工具范围 | 规则 |
|---|---|---|
| 品牌 | `geo_brand_list`、`geo_brand_get`、`geo_brand_seat_count`、`geo_brand_agent_access`、`geo_brand_create`、`geo_brand_update` | 查询、创建和编辑品牌 |
| 目标用户 | `geo_brand_target_user_list`、`geo_brand_target_user_get`、`geo_brand_target_user_create`、`geo_brand_target_user_update`、`geo_brand_target_user_delete` | 在已确认品牌下管理用户画像；删除前确认 |
| 优化单元 | `geo_topic_list`、`geo_topic_get`、`geo_topic_count`、`geo_topic_create`、`geo_topic_update`、`geo_topic_delete`、`geo_topic_batch_create`、`geo_topic_batch_delete`、`geo_topic_batch_status` | 支持查询、创建、编辑、删除和批量状态 |
| 用户意图 | `geo_question_list`、`geo_question_add`、`geo_question_batch_add`、`geo_question_update`、`geo_question_delete`、`geo_topic_questions`、`geo_topic_question_count` | 在已确认优化单元下管理意图 |
| AI 拓展 | `geo_topic_expand`、`geo_topic_expand_questions`、`geo_topic_task_result` | 异步任务，先提交再轮询 |
| 引文检测 | `geo_detection_list`、`geo_detection_stats`、`geo_detection_brand_records`、`geo_detection_rank`、`geo_detection_detail`、`geo_detection_emotion_overview`、`geo_detection_emotion_trend`、`geo_detection_competitor_matrix`、`geo_detection_competitor_question`、`geo_detection_manual_resume` | 查询记录、统计、排名、明细、情感、竞品分析；人工恢复前确认机器人账号 |
| 创作模板 | `geo_template_list` | 创建普通文章或抖音图文前必须先按内容场景查询模板：普通文章用 `CONTENT`，抖音图文用 `DOUYIN_IMAGE_TEXT`；取得模板 ID 后在创建/生成时作为必填 `templateId` 传入，没有无模板的创建路径 |
| 文章 | `geo_article_list`、`geo_article_get`、`geo_article_create`、`geo_article_generate`、`geo_article_generation_task_result`、`geo_article_douyin_image_progress`、`geo_article_update`、`geo_article_update_cover`、`geo_article_update_douyin_detail`、`geo_article_regenerate_cover`、`geo_image_material_list`、`geo_article_delete`、`geo_article_history_list`、`geo_article_recover` | 支持查询、创建、异步生成、轮询、正文/封面/抖音详情编辑、删除、历史和恢复；创建前必须先查创作模板，抖音图文最终状态以后端文章状态为准，删除/恢复前确认 |
| 数据看板 | `geo_dashboard_summary`、`geo_dashboard_trend`、`geo_dashboard_topic_page` | 查询总览、趋势和优化单元排行 |
| 产品分析 | `geo_product_page`、`geo_product_analysis_overview` | 在已确认品牌下查询产品与分析概览 |
| 内容优化 | `geo_content_list`、`geo_content_get`、`geo_content_delete` | 查询和删除历史记录；删除前确认 |
| 知识库 | `geo_kb_list`、`geo_kb_get`、`geo_kb_preview`、`geo_kb_articles` | 查询知识库、详情、内容预览和文章 |
| 发布 | `geo_publish_platform_types`、`geo_publish_account_list`、`geo_publish_record_list`、`geo_publish_submit` | 查询平台、账号、历史记录；仅提交已确认发布记录 |

## 暂缓能力

以下原插件本地闭环能力当前不注册，收到请求时说明“当前 WorkBuddy MCP 连接器暂未开放该能力”：

- 前端 SSE 直连生成和轻量生成本地闭环：`geo_article_create_and_generate`、`geo_article_create_and_generate_light`；MCP 已提供 `geo_article_generate` 非 SSE 异步生成路径
- 本地保存并打开 GEO HTML 报告：`geo_dashboard_report`
- 本地后台发布队列：`geo_publish_run_pending`、`geo_publish_auto`
- 知识库语义搜索：`geo_kb_search`（当前后端无真实语义检索实现）

## 典型流程

1. 品牌不唯一时，先查询品牌列表并让用户选择。
2. 查询类请求按品牌 → 优化单元 → 用户意图 → 检测记录/看板趋势的归属链路调用。
3. 管理类请求先补齐必填业务字段；高风险操作获得确认后调用。
4. 异步拓展提交后轮询任务结果，不编造成功状态。
5. 只根据接口返回字段总结，不补充推荐度、排名、状态或趋势结论。
6. 创建普通文章或抖音图文时，先调用 `geo_template_list` 取同场景模板，再调用 `geo_article_create` 与 `geo_article_generate`；模板停用或场景不符时按接口报错如实反馈，不擅自换用其他模板。

## 回复规则

- 始终用中文；调用前可说明“正在查询/创建/提交……”，不暴露 `geo_*` 工具名。
- 对用户统一使用“品牌”“目标用户”“优化单元”“用户意图”“引文检测记录”“知识库”“发布记录”等业务词。
- 分页默认第一页、每页 10 条；继续翻页前先询问用户，不自动遍历全部记录。
- 如果工具返回「您当前的品牌版本暂不支持该功能，请联系顾问」，最终回复必须逐字输出这句话，不加前后缀。
- 接口错误包含程序化时间格式提示时，不原样转述；改用中文时间说明，并可在安全修正时间边界后重试一次。
