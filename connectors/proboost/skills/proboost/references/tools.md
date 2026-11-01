# OpenBoost MCP 工具清单

按当前已连接的 OpenBoost MCP 服务整理。调用前先选最少必要的工具，不要一次枚举全部接口。

## Amazon（36）

| 工具 | 用途 |
| --- | --- |
| `amz_sku_query` | 按 ASIN 与站点查询商品详情（标题、价格、品牌、卖家、类目、BSR、评价、主图等） |
| `amz_category_query` | 按类目 ID 查询类目层级、父子与路径 |
| `amz_category_query_v2` | 按类目层级与站点分页拉取类目树（推荐） |
| `amz_sales_query` | 按 ASIN 预估 SKU 及父 ASIN（SPU）销量 |
| `amz_sales_prediction_bsr` | 按站点、一级类目与目标 BSR 预测月销量、日销量 |
| `amz_review_query` | 分页查询商品评论，按时间从新到旧 |
| `amz_product_selection` | 多条件选产品：类目、关键词、卖家、品牌、BSR、销量、徽章、变体 |
| `amz_product_competitor` | 按品牌、卖家、ASIN、类目、关键词等分页查竞品 |
| `amz_market_research` | 类目市场规模分页查询（销量、销售额、集中度、新品、卖家结构） |
| `amz_market_statistics` | 类目市场聚合统计（商品/品牌/卖家数、均价、BSR、新品指标） |
| `amz_market_goods` | 类目自然月销量 Top100 商品 |
| `amz_market_price` | 销量 TopN SKU 的价格带分布 |
| `amz_market_brand` | 类目品牌集中度 |
| `amz_market_seller` | 类目卖家集中度 |
| `amz_market_seller_type` | 卖家类型分布（AMZ / FBA / FBM） |
| `amz_market_seller_location` | 卖家所属地分布 |
| `amz_market_rating` | 评分值分布 |
| `amz_market_ratings` | 评分数分布 |
| `amz_market_shelf_time` | 上架时间分布 |
| `amz_market_shelf_trend` | 上架趋势分布 |
| `amz_hot_amz_hot_cat_tree` | 榜单类目树 |
| `amz_hot_amz_hot_list_v2` | 榜单商品列表（排名、销量、价格、评价） |
| `amz_keyword_miner` | 按种子词挖掘关键词（搜索量、SPR、标题密度、竞品数等） |
| `amz_keyword_research` | 关键词选品（搜索量、点击、增长率、类目占比、Top ASIN） |
| `amz_keyword_research_trends` | 关键词月搜索趋势 |
| `amz_keyword_order` | 按 ASIN 反查 Top 出单词 |
| `amz_research_monthly` | ABA 关键词月度统计 |
| `amz_aba_research_weekly` | ABA 关键词周度统计 |
| `amz_aba_research_trends` | ABA 关键词排名趋势（月/周） |
| `amz_google_trends` | Google Trends 近 5 年兴趣度 |
| `amz_traffic_keyword` | ASIN 近月前三页流量词（自然/广告位次、搜索量、SPR） |
| `amz_traffic_keyword_stat` | 流量词条数及自然/广告类型分布 |
| `amz_traffic_source` | 流量来源（关键词流向） |
| `amz_traffic_extend` | 按 ASIN 列表拓展前三页流量词，可含变体 |
| `amz_traffic_listing_page` | 产品关联流量来源（关联商品列表） |
| `amz_traffic_listing_stat` | 关联流量条数及类型分布 |

## TikTok Shop（32）

| 工具 | 用途 |
| --- | --- |
| `tt_commodity_get_commodity_cat_tree` | 商品类目树 |
| `tt_commodity_info_list` | 选品商品分页列表 |
| `tt_commodity_detail` | 商品详情（价格、销量、达人/视频数、佣金、店铺） |
| `tt_commodity_sales_trend` | 商品销售趋势（销量、销售额、价格） |
| `tt_commodity_expert_draw_expert_trend` | 带货达人数量按月趋势 |
| `tt_commodity_voice_analyze` | 商品评论口碑分析（观点、提及次数、占比） |
| `tt_commodity_voice_read` | 商品评论/原声分页读取 |
| `tt_commodity_statistics_get_total_statistics` | 大盘-商品总览（近 7 日/近 30 日的销量、销售额、动销、均价、新品及环比） |
| `tt_commodity_statistics_get_category_statistics` | 品类热力图 |
| `tt_commodity_statistics_get_price_statistics` | 价格带分布 |
| `tt_commodity_statistics_get_expert_statistics` | 带货达人矩阵 |
| `tt_dashboard_overview` | 大盘-数据总览（可选类目与周期；含当期值、环比、变化方向和每日趋势） |
| `tt_expert_info_list` | 达人列表 |
| `tt_expert_detail` | 达人详情 |
| `tt_expert_basic_analyze` | 达人基础趋势（点赞、播放、转发） |
| `tt_expert_fans_portrait` | 粉丝画像 |
| `tt_expert_fans_analyze` | 带货达人粉丝档位分析 |
| `tt_expert_category_analyze` | 带货达人类目分布 |
| `tk_expert_sale_show` | 达人销售表现（渠道与类目 GMV 占比） |
| `tt_shop_info_list` | 店铺列表 |
| `tt_shop_detail` | 店铺详情 |
| `tt_shop_market_info` | 店铺经营指标 |
| `tt_shop_sales_trend` | 店铺销售/评论趋势 |
| `tt_shop_commodity_account_list` | 店铺类目数量与销量占比 |
| `tt_video_info_list` | 视频列表 |
| `tt_video_detail` | 视频详情 |
| `tt_video_content` | 口播/语音转写原文 |
| `tt_video_new_video_summary` | 视频总结 |
| `tt_video_script_diy_query` | DIY 脚本 |
| `tt_video_voice_read` | 视频评论 |
| `tt_video_voice_summary` | 视频评论总结 |
| `tt_hashtag_list` | 视频标签（hashtag） |

## 社媒（11）

| 工具 | 用途 |
| --- | --- |
| `instagram_fetch_user_info` | Instagram 用户信息 |
| `instagram_fetch_user_reels` | Instagram 用户视频列表 |
| `instagram_fetch_post_info` | Instagram 帖子信息 |
| `instagram_fetch_reel_info` | Instagram 视频帖详情 |
| `instagram_fetch_post_comments` | Instagram 帖子评论 |
| `instagram_fetch_hashtag_posts` | Instagram 话题标签下的帖子 |
| `youtube_fetch_user_info` | YouTube 频道详情 |
| `youtube_fetch_post_info` | YouTube 视频详情（返回评论用 review_token） |
| `youtube_fetch_post_comments` | YouTube 视频评论（需先取 review_token） |
| `reddit_fetch_post_details` | Reddit 帖子详情 |
| `reddit_fetch_post_comments` | Reddit 帖子评论 |

## 专利（17）

| 工具 | 用途 |
| --- | --- |
| `patent_query_search` | 检索式检索专利 |
| `patent_query_count` | 检索式统计专利件数 |
| `patent_query_search_with_agg` | 检索并按维度聚合 |
| `patent_semantic_search` | 语义相似专利检索 |
| `patent_image_search_single` | 单图图像检索 |
| `patent_image_search_multiple` | 多图图像检索 |
| `patent_bibliography` | 著录项目 |
| `patent_legal_status` | 法律状态 |
| `patent_family` | 专利家族 |
| `patent_claim_data` | 权利要求原文 |
| `patent_claim_translated` | 权利要求翻译 |
| `patent_description` | 说明书原文 |
| `patent_description_translated` | 说明书翻译 |
| `patent_abstract_translated` | 摘要翻译 |
| `patent_abstract_image` | 摘要附图 |
| `patent_fulltext_image` | 全文附图 |
| `patent_pdf` | PDF 全文 |

## 账号（8）

用户问账号、额度、充值、续费或官网时调用。返回的 URL 展示为可点击链接。

| 工具 | 用途 |
| --- | --- |
| `account_info` | 已开通服务、套餐状态、剩余额度 |
| `account_catalog` | 可购买套餐目录 |
| `account_recharge` | 充值/续费直达链接 |
| `account_portal` | 官网首页、价格、目录链接 |
| `account_links` | 官网、价格、目录、企业微信客服链接 |
| `account_order_create` | 按套餐下单并返回支付链接 |
| `account_order_status` | 按订单号查询支付状态 |
| `account_orders` | 分页查询支付订单 |
