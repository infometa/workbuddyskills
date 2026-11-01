---
name: proboost
display_name: OpenBoost 跨境数据
display_name_en: OpenBoost Cross-border Data
description: 跨境电商数据查询。用于市场研究、选品分析、竞对监控、VOC 洞察、关键词分析、listing 生成、社媒分析，以及 Amazon、TikTok Shop、Instagram、YouTube、Reddit 与全球专利检索。用户提到亚马逊、TikTok、达人、选品、评论、社媒、专利、OpenBoost 时使用。
description_zh: 查询 Amazon、TikTok Shop、社媒与专利数据，用于选品、竞对、关键词和 VOC 分析。
description_en: Query Amazon, TikTok Shop, social, and patent data for product research, competitors, keywords, and VOC.
category: research
version: 1.0.1
author: OpenBoost（案牍科技）
---

# OpenBoost 跨境数据

通过已启用的 OpenBoost MCP 连接器查询 Amazon、TikTok Shop、Instagram、YouTube、Reddit 与全球专利数据。不要编造数据；所有数字、排名、销量、评论、专利结果必须来自工具返回。

listing 文案只能基于关键词、流量词、评论和商品详情等工具结果生成。

详细工具清单见 @references/tools.md。Amazon 与 TikTok 站点对照见 @references/sites.md。

## 使用前

1. 确认 MCP 连接器 `proboost-tiktok-amazon-patent-mcp` 已连接（OAuth 授权成功，状态为绿色）。
2. 未授权时，引导用户完成 OpenBoost 登录授权；不要向用户索要或回显 secret-key。
3. 用户问账号、额度、充值、续费或官网时，调用 `account_info` / `account_recharge` / `account_portal`，把返回的 URL 展示为可点击链接。
4. 未订阅、套餐过期或额度用尽时，提示用户前往 https://openboostai.com/ 开通或续费。
5. 调用失败（401 / 业务码 -1）时，按顺序排查：未授权 → 套餐过期 → 额度用尽 → 参数错误。

## 能力边界

能做：

- Amazon：商品详情、类目、选品、选市场、关键词、ABA、流量词、竞品、评论、榜单、销量预估；据此做竞对监控、VOC 归纳、关键词分析和 listing 草稿
- TikTok Shop：商品选品、达人、视频、店铺、品类大盘、口碑
- 社媒：Instagram 用户/帖子/评论/话题、YouTube 频道/视频/评论、Reddit 帖子/评论
- 专利：检索式/语义/图像检索、著录项目、法律状态、同族、全文与翻译
- 账号：套餐、额度、充值链接、订单状态

不能做：

- 代用户下单、改广告、改 Listing、登录第三方后台
- 在没有工具结果时编造销量、排名、评论或专利结论
- 引导用户离开 WorkBuddy 去完成可在对话内完成的任务（OAuth / 开通套餐除外）

## 执行原则

1. 先判断任务属于 Amazon / TikTok / 社媒 / 专利 / 账号哪一类，再选最少必要的工具。
2. Amazon 查询默认美国站（`webSiteId=1`），用户指定站点时再切换；站点对照查 @references/sites.md 表 1.1。
3. TikTok 的 `countryRegion` 传中文站名，`region` 传区域代码，查 @references/sites.md 的 TikTok 表。不要套用 Amazon 的 webSiteId。
4. 缺关键参数时先问：站点、类目、ASIN、国家/地区、时间范围、帖子或视频标识、专利检索式。
5. 多步任务按流水线调用，每步用上一步结果，不要一次堆很多无关工具。
6. 结果用中文归纳：结论先行，再给关键数字、来源字段、下一步建议。
7. 列表类结果默认取 Top 10～20，并说明筛选条件。

## 典型工作流

### Amazon 选品 / 选市场

1. 用类目树确认类目 ID 或路径（`amz_category_query_v2` 或 `amz_hot_amz_hot_cat_tree`）。
2. 看市场容量与竞争（`amz_market_research` / `amz_market_statistics`）。
3. 看价格带、品牌、卖家结构（`amz_market_price` / `amz_market_brand` / `amz_market_seller`）。
4. 筛潜力款（`amz_product_selection` 或 `amz_market_goods` / `amz_hot_amz_hot_list_v2`）。
5. 对候选 ASIN 做详情与销量（`amz_sku_query` / `amz_sales_query`）。

### Amazon 关键词 / listing

1. 种子词挖掘：`amz_keyword_miner`
2. 选词与趋势：`amz_keyword_research` / `amz_research_monthly` / `amz_aba_research_trends`
3. 流量结构：`amz_traffic_keyword` / `amz_traffic_source`；出单词反查：`amz_keyword_order`
4. listing 草稿只用上述工具返回的词和商品详情，并标明依据

### 竞对监控 / VOC

1. 竞品列表：`amz_product_competitor`
2. 评论原文：`amz_review_query`；TikTok 商品口碑用 `tt_commodity_voice_analyze` / `tt_commodity_voice_read`
3. 归纳高频观点、差评点与可执行改动，引用评论原句

### TikTok 找品 / 找达人

1. 类目：`tt_commodity_get_commodity_cat_tree`
2. 商品列表或详情：`tt_commodity_info_list` / `tt_commodity_detail` / `tt_commodity_sales_trend`
3. 达人：`tt_expert_info_list` / `tt_expert_detail` / `tt_expert_fans_portrait`
4. 视频脚本与口播：`tt_video_info_list` / `tt_video_detail` / `tt_video_content` / `tt_video_new_video_summary`
5. 大盘-数据总览用 `tt_dashboard_overview`；大盘-商品总览用 `tt_commodity_statistics_get_total_statistics`；品类热力图用 `tt_commodity_statistics_get_category_statistics`

### 社媒

1. Instagram：用户 `instagram_fetch_user_info`，帖子 `instagram_fetch_post_info` / `instagram_fetch_reel_info`，评论 `instagram_fetch_post_comments`，话题 `instagram_fetch_hashtag_posts`
2. YouTube：先 `youtube_fetch_post_info` 取 `review_token`，再 `youtube_fetch_post_comments`；频道用 `youtube_fetch_user_info`
3. Reddit：`reddit_fetch_post_details` / `reddit_fetch_post_comments`
4. 社媒实时查询会阻塞等待。连接器超时为 120 秒，用来覆盖这类接口；Amazon、TikTok、专利、账号等其余接口单次应在 30 秒内返回。社媒超时后按返回的 `task_id` 再查，不要编造互动数据

### 专利预检

1. 先检索：文本用 `patent_query_search` 或 `patent_semantic_search`；外观用 `patent_image_search_single`
2. 看件数：`patent_query_count`
3. 对命中专利取著录/法律状态/同族：`patent_bibliography` / `patent_legal_status` / `patent_family`
4. 需要权利要求或说明书时再调全文/翻译工具
5. 结论必须区分「检索到相似专利」与「构成侵权」，后者需要专业律师判断，技能只做数据辅助。

## 输出格式

- 标题：一句话结论
- 关键数据：表格或要点（含站点、时间范围、类目）
- 依据：列出调用过的工具名
- 建议：下一步可继续查什么
- 风险：数据延迟、样本偏差、专利结论需人工复核

## 异常处理

- MCP 未连接 → 「请先在连接器中启用 OpenBoost，并完成 OAuth 授权。」
- 401 / 未授权 → 「当前授权无效或已过期，请重新授权；如未订阅请到 https://openboostai.com/ 开通。」
- 参数缺失 → 明确列出还缺哪些字段，不要空跑工具
- 无结果 → 说明筛选条件，建议放宽站点、类目或关键词后再查
- 工具超时 → 社媒接口可等待到 120 秒，超时后用 `task_id` 再查；其余接口超过 30 秒仍无结果时，缩小时间范围或分页后再试

## 隐私说明

本技能通过远程 MCP 查询 OpenBoost（案牍科技）数据服务。不在本地保存用户密钥。官网：https://openboostai.com/
