---
name: dowsure-ai
display_name: Dowsure AI
display_name_en: Dowsure AI
description: Read peer benchmarks, authorized stores and operating data, and Dowsure product and service-provider knowledge for comparison and multi-store analysis.
description_zh: 查询同行业基准、授权店铺和经营数据，以及 Dowsure 产品和服务商知识，支持同行对比与多店铺经营分析。
description_en: Read peer benchmarks, authorized stores and operating data, and Dowsure product and service-provider knowledge for comparison and multi-store analysis.
version: 1.0.2
author: Dowsure
category: data
---

Connect your Dowsure AI account through WorkBuddy's browser OAuth flow before use.
WorkBuddy performs comparison, aggregation, provider recommendation and customer copy from the factual read Tools. These Tools wrap atomic Harness capabilities and do not invoke an LLM or Subagent.

## benchmark-query
Read published peer benchmark aggregates for one approved metric and marketplace. Example metricKey values include net_proceeds_margin, aged_inventory_ratio and cash_locked_ratio. Input requires metricKey and marketplaceId; categoryId is optional for the published whole-category all-GMV aggregate. Returns metricKey, marketplaceId, sampleSize, true p20/p50/p80, referenceMonth, freshness and resolvedScope. Unsafe or unavailable evidence returns status no_data; invalid_input, insufficient_scope, tool_timeout and tool_unavailable are stable error categories. WorkBuddy performs the comparison and customer-facing interpretation.
Example: call benchmark-query with {"metricKey":"net_proceeds_margin","marketplaceId":"amazon_us"}.
Required approved metric key, maximum 128 characters. Valid keys: fee_ratio (平台费用率; percent; 每产生 100 元净商品销售额，平台费用占多少元；越低代表平台费用负担越轻。); ads_fee_ratio (广告费用率; percent; 每产生 100 元净商品销售额，广告费用占多少元；越低代表广告成本压力越小。); refund_amount_ratio (退款金额率; percent; 每产生 100 元净商品销售额，退款金额占多少元；越低代表售后损失越小。); net_proceeds_margin (净回款率; percent; 扣除来源数据中已包含的平台费用、广告费用和退款等项目后，净回款占净商品销售额的比例；它反映回款留存，不是净利润率或完整成本核算。); aged_inventory_ratio (超 180 天库存占比; percent; 可售库存中库龄超过 180 天的比例；越低代表长期滞销和仓储风险越小。); sell_through_rate (售罄率; percent; 库存在一段时间内被销售消化的速度；越高代表库存周转越快。); days_of_supply_median (库存可售天数; days; 按当前销售速度，现有可售库存预计还能销售多少天；30–60 天较合理。); gmv_growth_90d (近 90 天销售额环比增长率; percent; 最近 90 天销售额相较此前 90 天的变化幅度；越高代表销售增长更快。); cash_locked_ratio (回款占用率; percent; 未结算销售额、在途应收和预留资金占近 90 天销售额的比例；越低代表资金占用越少。); ahr_score (账户健康评分; score; Amazon 对店铺合规与经营健康的综合评分；越高代表账户风险越低。); top5_parent_asin_gmv_ratio (Top 5 SKU 销售额集中度; percent; 销售额最高的 5 个 SKU 占总销售额的比例；过高代表对少数商品依赖较强。).
Required authorized marketplace ID, maximum 128 characters. Supported IDs and legacy aliases: ATVPDKIKX0DER, amazon-us, amazon_us, amazon us (Amazon 美国站); A1F83G8C2ARO7P, amazon-uk, amazon_uk, amazon uk (Amazon 英国站); A1PA6795UKMFR9, amazon-de, amazon_de, amazon de, amazon-germany, amazon_germany, amazon germany (Amazon 德国站); A1VC38T7YXB528, amazon-jp, amazon_jp, amazon jp, amazon-japan, amazon_japan, amazon japan (Amazon 日本站); A2EUQ1WTGCTBG2, amazon-ca, amazon_ca, amazon ca, amazon-canada, amazon_canada, amazon canada (Amazon 加拿大站); A39IBJ37TRP1C6, amazon-au, amazon_au, amazon au (Amazon 澳大利亚站); A1AM78C64UM0Y8, amazon-mx, amazon_mx, amazon mx (Amazon 墨西哥站); A2Q3Y263D00KWC, amazon-br, amazon_br, amazon br (Amazon 巴西站); A13V1IB3VIYZZH, amazon-fr, amazon_fr, amazon fr (Amazon 法国站); APJ6JRA9NG5V4, amazon-it, amazon_it, amazon it (Amazon 意大利站); A1RKKUPIHCS9HS, amazon-es, amazon_es, amazon es (Amazon 西班牙站); A1805IZSGTT6HS, amazon-nl, amazon_nl, amazon nl (Amazon 荷兰站); A2NODRKZP88ZB9, amazon-se, amazon_se, amazon se (Amazon 瑞典站); A1C3SOZRARQ6R3, amazon-pl, amazon_pl, amazon pl (Amazon 波兰站); AMEN7PMS3EDWL, amazon-be, amazon_be, amazon be (Amazon 比利时站); A21TJRUUN4KGV, amazon-in, amazon_in, amazon in (Amazon 印度站); A19VAU5U5O7RUS, amazon-sg, amazon_sg, amazon sg (Amazon 新加坡站); A2VIGQ35RCS4UG, amazon-ae, amazon_ae, amazon ae (Amazon 阿联酋站); A17E79C6D8DWNP, amazon-sa, amazon_sa, amazon sa (Amazon 沙特站); A33AVAJ2PDY3EV, amazon-tr, amazon_tr, amazon tr (Amazon 土耳其站); ARBP9OOSHTCHU, amazon-eg, amazon_eg, amazon eg (Amazon 埃及站).
Optional category value, maximum 128 characters. Valid values: Home; Electronics; Beauty; Home Improvement; Toys. Omit for the exact published whole-category, all-GMV aggregate. Category aliases are normalized by the shared Tool.
Required permission: agent_os.benchmark.read.

## product-knowledge-search
Search bounded Dowsure product knowledge. query is required and limit is optional (default 5, maximum 8). Returns documents with opaque documentId, title and content plus truncated when bounded. No matches return status no_data; invalid_input, insufficient_scope, tool_timeout and tool_unavailable are stable error categories.
Input example: {"query":"产品功能说明","limit":5}.
Required permission: agent_os.product_knowledge.read.

## provider-knowledge-search
Search bounded factual cross-border provider knowledge. query is required and limit is optional (default 5, maximum 8). Returns documents with opaque documentId, title and content plus truncated when bounded; no matches return status no_data. WorkBuddy performs recommendation and provider matching from these facts. Stable errors are invalid_input, insufficient_scope, tool_timeout and tool_unavailable.
Input example: {"query":"美国站物流服务商服务范围","limit":5}.
Required permission: agent_os.provider_knowledge.read.

## marketplace-context
Read authorized marketplace site context for the selected seller. sellerContextId is optional; marketplaceId is optional. Omit marketplaceId to read all authorized marketplaces; Do not pass marketplaceId=ATVPDKIKX0DER unless you intentionally want the US marketplace only. With omission, returns marketplaces and coverage; with a marketplaceId, returns one single site context object. Partial site evidence remains explicit. Stable errors include authorization_denied, insufficient_scope, invalid_input, tool_timeout and tool_unavailable. WorkBuddy performs cross-site analysis.
For multi-seller analysis, call seller-context-list first and pass its sellerContextId.
Required permission: agent_os.store.read.

## seller-context-list
List all seller contexts authorized for the OAuth account. This read-only tool takes an empty object and returns sellerContexts with opaque sellerContextId, displayName, availability and marketplaceIds, or status no_data when no context is available. Raw sellerId values are never accepted. No valid mapping returns the account error 403; stable errors also include insufficient_scope and tool_unavailable.
Use the returned sellerContextId on seller-store-snapshot, operating-metric-catalog,
operating-metric-snapshot, operating-data-drilldown and marketplace-context. Omit it only for the
active seller. Do not send raw sellerId.
Required permission: agent_os.store.read.

## metric-catalog
Read approved peer benchmark metric definitions. metricKeys is optional and filters the returned metrics; omit it for the complete catalog. Returns metric definitions with names, units and descriptions, or status no_data when no requested definition is available. Stable errors are invalid_input, insufficient_scope and tool_unavailable.
Required permission: agent_os.benchmark.read.

## seller-store-snapshot
Read authorized seller marketplace and category snapshots. sellerContextId is optional. Use marketplaceScope.kind = `all_marketplaces` for every authorized marketplace; marketplaceScope.kind is `all_marketplaces` when you need every authorized site; use kind `exact` with marketplaceId for one site. Do not use kind `exact` with marketplaceId=ATVPDKIKX0DER unless you intentionally want the US marketplace only. period is optional. Returns marketplace/category snapshots with coverage and opaque store identifiers; missing snapshots return status no_data. Stable errors include authorization_denied, insufficient_scope, invalid_input, tool_timeout and tool_unavailable.
Use {"marketplaceScope":{"kind":"all_marketplaces"}} for all authorized sites. Use
{"marketplaceScope":{"kind":"exact","marketplaceId":"amazon_us"}} for one site. Do not use exact
with ATVPDKIKX0DER unless the US-only result is intentional.
Required permission: agent_os.store.read.

## operating-metric-catalog
Read approved operating metric definitions and formulas for an authorized seller. sellerContextId and metricKeys are optional; omit metricKeys for the full catalog. Returns metric definitions and supported section semantics, or status no_data when unavailable. Stable errors are authorization_denied, insufficient_scope, invalid_input, tool_timeout and tool_unavailable.
Pass sellerContextId from seller-context-list for a non-active seller.
Required permission: agent_os.store.read.

## operating-metric-snapshot
Read authorized operating observations. sellerContextId, marketplaceId and metricKeys are optional; omit marketplaceId for the seller scope and omit metricKeys for all approved metrics. Returns observations, rows, freshness and source-date status; unavailable observations return status no_data; incomplete evidence remains explicit and no business conclusion is produced. Stable errors are authorization_denied, insufficient_scope, invalid_input, tool_timeout and tool_unavailable.
Pass sellerContextId from seller-context-list for a non-active seller. No business conclusion is
produced by this Tool.
Required permission: agent_os.store.read.

## operating-data-drilldown
Read bounded authorized operating evidence pages. sellerContextId, sectionIds, metricKeys, itemIds and period are optional; cursor is an opaque continuation token, limit defaults to 100 and is capped at 200. Returns rows, coverage and nextCursor; continue until coverage.complete is true. Invalid or mismatched cursors return invalid_input; no evidence returns status no_data. WorkBuddy performs diagnosis and aggregation.
Pass sellerContextId from seller-context-list for a non-active seller. Keep marketplace, currency and
period coordinates separate.
Required permission: agent_os.store.read.

## Errors and recovery
On expired or revoked authorization, reconnect through WorkBuddy. Missing permission requires
reauthorization for the indicated scope. HTTP 403 账号异常，请联系工作人员处理 requires staff assistance;
do not provision or repair accounts. Retry temporary upstream outages later. Empty results mean
no matching knowledge; do not fabricate an answer. Invalid inputs must be corrected before retry.
Requests have a 30-second deadline; cancellation stops upstream work.
