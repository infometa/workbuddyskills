# OpenBoost MCP 工具清单

按需加载。调用前先选最少必要的工具，不要一次枚举全部接口。

## Amazon（36）

| 工具 | 用途 |
| --- | --- |
| `amz_sku_query` | ASIN 商品详情 |
| `amz_category_query` | 类目信息 |
| `amz_category_query_v2` | 类目树（推荐） |
| `amz_sales_query` | ASIN 销量预估 |
| `amz_sales_prediction_bsr` | 按 BSR 预测销量 |
| `amz_review_query` | 商品评论 |
| `amz_product_selection` | 多条件选产品 |
| `amz_product_competitor` | 竞品查询 |
| `amz_market_research` | 选市场列表/容量 |
| `amz_market_statistics` | 市场聚合统计 |
| `amz_market_goods` | 类目 Top 商品 |
| `amz_market_price` | 价格带分布 |
| `amz_market_brand` | 品牌集中度 |
| `amz_market_seller` | 卖家集中度 |
| `amz_market_seller_type` | 卖家类型（FBA/FBM 等） |
| `amz_market_seller_location` | 卖家所属地 |
| `amz_market_rating` | 评分分布 |
| `amz_market_ratings` | 评分数分布 |
| `amz_market_shelf_time` | 上架时间分布 |
| `amz_market_shelf_trend` | 上架趋势 |
| `amz_hot_amz_hot_cat_tree` | 榜单类目树 |
| `amz_hot_amz_hot_list_v2` | 榜单商品列表 |
| `amz_keyword_miner` | 关键词挖掘 |
| `amz_keyword_research` | 关键词选品 |
| `amz_keyword_research_trends` | 关键词趋势 |
| `amz_keyword_order` | 出单词/出单反查 |
| `amz_research_monthly` | ABA 月度 |
| `amz_aba_research_weekly` | ABA 周度 |
| `amz_aba_research_trends` | ABA 趋势 |
| `amz_google_trends` | 谷歌趋势 |
| `amz_traffic_keyword` | 流量词列表 |
| `amz_traffic_keyword_stat` | 流量词统计 |
| `amz_traffic_source` | 流量来源 |
| `amz_traffic_extend` | 拓展流量词 |
| `amz_traffic_listing_page` | Listing 流量页 |
| `amz_traffic_listing_stat` | Listing 流量统计 |

## TikTok Shop（31）

| 工具 | 用途 |
| --- | --- |
| `tt_commodity_get_commodity_cat_tree` | 商品类目树 |
| `tt_commodity_info_list` | 选品商品列表 |
| `tt_commodity_detail` | 商品详情 |
| `tt_commodity_sales_trend` | 商品销售趋势 |
| `tt_commodity_expert_draw_expert_trend` | 带货达人趋势 |
| `tt_commodity_voice_analyze` | 商品口碑分析 |
| `tt_commodity_voice_read` | 商品评论读取 |
| `tt_commodity_statistics_get_total_statistics` | 大盘总览 |
| `tt_commodity_statistics_get_category_statistics` | 品类热力 |
| `tt_commodity_statistics_get_price_statistics` | 价格分布 |
| `tt_commodity_statistics_get_expert_statistics` | 达人矩阵 |
| `tt_expert_info_list` | 达人列表 |
| `tt_expert_detail` | 达人详情 |
| `tt_expert_basic_analyze` | 达人基础趋势 |
| `tt_expert_fans_portrait` | 粉丝画像 |
| `tt_expert_fans_analyze` | 粉丝档位分析 |
| `tt_expert_category_analyze` | 达人类目分析 |
| `tk_expert_sale_show` | 达人销售表现 |
| `tt_shop_info_list` | 店铺列表 |
| `tt_shop_detail` | 店铺详情 |
| `tt_shop_market_info` | 店铺经营指标 |
| `tt_shop_sales_trend` | 店铺销售趋势 |
| `tt_shop_commodity_account_list` | 店铺类目占比 |
| `tt_video_info_list` | 视频列表 |
| `tt_video_detail` | 视频详情 |
| `tt_video_content` | 口播原文 |
| `tt_video_new_video_summary` | 视频总结 |
| `tt_video_script_diy_query` | DIY 脚本 |
| `tt_video_voice_read` | 视频评论 |
| `tt_video_voice_summary` | 视频评论总结 |
| `tt_hashtag_list` | 视频标签（hashtag）查询 |

## 专利（17）

| 工具 | 用途 |
| --- | --- |
| `patent_query_search` | 检索式检索 |
| `patent_query_count` | 检索式统计件数 |
| `patent_query_search_with_agg` | 检索并聚合 |
| `patent_semantic_search` | 语义相似检索 |
| `patent_image_search_single` | 单图图像检索 |
| `patent_image_search_multiple` | 多图图像检索 |
| `patent_bibliography` | 著录项目 |
| `patent_legal_status` | 法律状态 |
| `patent_family` | 专利家族 |
| `patent_claim_data` | 权利要求 |
| `patent_claim_translated` | 权利要求翻译 |
| `patent_description` | 说明书 |
| `patent_description_translated` | 说明书翻译 |
| `patent_abstract_translated` | 摘要翻译 |
| `patent_abstract_image` | 摘要附图 |
| `patent_fulltext_image` | 全文附图 |
| `patent_pdf` | PDF 全文 |

接口说明：https://open.microdata-inc.com/catalog/all
