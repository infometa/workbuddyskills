---
name: hdd-erp
description: 使用货叮咚 ERP MCP 查询商品、订单、履约、营销、广告和利润数据，或在用户明确确认后创建商品导入任务并查询异步结果。
description_zh: 使用货叮咚 ERP MCP 查询商品、订单、履约、营销、广告和利润数据，或在用户明确确认后创建商品导入任务并查询异步结果。
description_en: Query products, orders, fulfillment, marketing, advertising, and profit data in Huodingdong ERP, or create product import tasks after explicit user confirmation and query their asynchronous results.
version: 1.0.0
author: yimai
---

# 货叮咚 ERP

## 使用范围

使用本连接器处理货叮咚 ERP 中当前账号有权访问的 TikTok Shop 和 Shopee 店铺数据。查询类 Tool 不修改业务数据。`hdd_product_collection_import_task_create` 是唯一写入 Tool，调用前必须让用户确认导入范围和可选认领目标。

## 调用原则

1. 先识别用户目标、平台、店铺和时间范围。平台使用 `SHOPEE` 或 `TIKTOK_SHOP`；店铺参数使用 `platform_shop_id`，不要转换成货叮咚数据库主键或货源店铺 ID。
2. 用户存在多个候选店铺且无法从上下文唯一确定时，先让用户选择。不得自行扩大到全部店铺。
3. 日期和分页参数遵循 Tool Schema。未指定页码时使用默认值；不要绕过服务端上限抓取无界数据。
4. 返回 `warnings`、`data_missing`、`unavailable_reason` 或 `meta.complete=false` 时，向用户说明数据范围和缺失原因，不把缺失值伪造成零。
5. 认证失效、Tool 停用、权限不足、限流或 Provider 不可用时，保留可展示的错误码和 `trace_id`，给出重新连接、缩小范围或稍后重试等可执行建议，不输出访问密钥。

## Tool 选择

| Tool | 用途 | 主要参数与注意事项 |
|---|---|---|
| `hdd_product_search` | 查询平台商品、草稿或采集箱 | `stage` 默认为 `LISTED`；在售商品还需传平台状态，Shopee 为 `NORMAL`，TikTok Shop 为 `ACTIVATE`；采集箱优先用 `keyword` 或 `product_id` |
| `hdd_product_pricing_simulation` | 查询模板或模拟定价 | 传入 `mode`、`platform` 时必须同时显式传 `region`；模拟时再按 Schema 补充模板、采购价、币种、重量和尺寸 |
| `hdd_product_publish_diagnosis` | 查询商品发布记录和失败状态 | 必填 `platform`、`start_at`、`end_at`；`target_item_id` 是平台商品 ID |
| `hdd_listing_health_overview` | 查看 ERP 库存快照和可取得的违规状态 | 必填 `platform`；库存不是平台实时可售库存，无违规数据不能解释为无违规 |
| `hdd_order_search` | 按店铺、时间和状态查询订单 | 必填 `platform`；可按订单处理状态、商家出货状态、货代进度及平台售后筛选 |
| `hdd_fulfillment_overview` | 汇总订单处理、商家出货、货代进度和平台售后 | 必填 `platform`、`start_date`、`end_date`；各统计维度可能重叠，不能直接相加 |
| `hdd_order_exception_overview` | 汇总订单异常 | 必填 `platform`、`start_date`、`end_date`，支持店铺和分页 |
| `hdd_marketing_campaign_search` | 查询营销活动、秒杀和优惠券 | 必填 `platform`；`ending_soon=true` 表示未来24小时内结束 |
| `hdd_ad_campaign_search` | 查询广告活动 | 必填 `platform`；支持店铺、关键词、活动 ID 和分页 |
| `hdd_ad_performance_analysis` | 分析广告花费、曝光、点击和转化 | 必填 `platform`、`platform_shop_id`、`start_date`、`end_date` |
| `hdd_profit_analysis` | 查询利润汇总、订单明细或商品明细 | 必填 `platform`、`start_date`、`end_date`；`view` 默认为 `SUMMARY` |
| `hdd_business_overview` | 查询经营概览 | 必填 `platform`、`start_date`、`end_date`，可限定 `platform_shop_id` |
| `hdd_product_collection_import_task_create` | 创建异步商品导入任务 | 必填唯一 `request_id`、固定 `collection_mode=STANDARD` 和 `products`；可选 `claim` 对整批商品生效 |
| `hdd_task_status_query` | 查询商品导入任务进度和明细 | 必填 `task_id`；对导入任务执行有限轮询，达到终态或轮询上限后停止 |

## 已知服务端限制

`hdd_product_pricing_simulation` 的当前 MCP 输入 Schema 尚未将 `region` 标记为必填，但服务端运行时要求该参数有值。每次调用该 Tool 都必须显式传入与目标市场一致的 `region`；无法从用户描述、店铺或其他可靠上下文确定时，应先询问用户，不得省略、猜测或固定使用某一区域。除这项已知差异外，Tool 参数和约束以 WorkBuddy 从 MCP 服务动态读取的最新 Tool Schema 为准。

## 典型业务场景

只调用满足当前问题所需的 Tool。需要从汇总下钻到明细时，再按用户目标继续调用，不要为了追求信息完整而默认调用全部相关 Tool。

- 用户询问销售额、销量、订单量或经营趋势时，使用 `hdd_business_overview`。用户进一步询问利润构成、订单利润或商品利润时，再使用 `hdd_profit_analysis`。
- 用户询问订单各阶段数量、商家出货、货代处理进度或平台售后数量时，使用 `hdd_fulfillment_overview`；需要具体订单时使用 `hdd_order_search`；需要问题订单或异常明细时使用 `hdd_order_exception_overview`。
- 用户询问商品列表、在售商品、草稿或采集箱时，使用 `hdd_product_search`；询问库存快照或违规风险时使用 `hdd_listing_health_overview`；询问发布失败原因和发布记录时使用 `hdd_product_publish_diagnosis`。
- 用户询问营销活动、秒杀、优惠券或未来24小时内即将结束的活动时，使用 `hdd_marketing_campaign_search`。用户询问广告活动及状态时使用 `hdd_ad_campaign_search`；询问广告花费、曝光、点击、转化或 ROAS 时使用 `hdd_ad_performance_analysis`。
- 用户询问模板售价、模拟定价或预计利润时，使用 `hdd_product_pricing_simulation`，并遵守上方 `region` 限制。模拟结果不等同于实际结算利润；实际账面利润使用 `hdd_profit_analysis`。
- 用户要求导入商品时，按下方商品导入规则先确认范围，再使用 `hdd_product_collection_import_task_create` 创建任务；需要进度或最终明细时，使用 `hdd_task_status_query` 做有限轮询。

## 商品导入规则

调用写入 Tool 前，向用户明确说明商品数量、只采集还是采集后认领、目标店铺以及是否继续执行发布检查。用户未明确同意时不要创建任务。

创建成功只表示异步任务已受理。随后使用 `hdd_task_status_query` 做有限轮询：

- `success_count` 表示采集成功数量，可能包含待认领、认领失败和已认领商品。
- 任务 `SUCCEEDED` 只表示采集完成，不代表认领全部成功。
- 认领结果必须结合 `claimed_count`、`claim_failed_count` 和商品明细状态判断。
- `CLAIM_FAILED` 应展示可读失败原因、错误码和 `trace_id`；不要把部分成功表述为全部成功。
- 未在有限轮询内结束时，返回 `task_id`、当前状态和稍后继续查询的建议。

未知结果重试时，复用原 `request_id` 和完全相同的载荷；新任务或载荷变化必须使用新的 `request_id`。

## 回答要求

1. 先给出直接回答用户问题的结论或汇总，再展示必要明细。不要原样堆砌完整 JSON，也不要扩展用户未要求的分析。
2. 明确说明本次查询的平台、店铺、时间范围和主要筛选条件。未限定店铺时说明查询范围，不要暗示结果只属于某一家店铺。
3. 分页结果说明当前页、每页数量和可取得的总量。需要继续查询时先征求用户意见，不要自动抓取全部分页。
4. 空结果应说明实际筛选条件，并表述为“当前条件下未查询到数据”。返回 `warnings`、`data_missing`、`unavailable_reason` 或 `meta.complete=false` 时，区分“没有数据”和“数据暂不可取得或不完整”。
5. 对状态码优先使用 Tool 返回的中文名称，不自行发明或合并状态。履约概览中的订单处理、商家出货、货代进度和平台售后属于不同维度且可能重叠，不得直接相加为订单总数。
6. 涉及金额时保留币种和原始精度。利润、广告和履约结果应说明数据口径、完整性和不可用原因；模拟利润不得表述为实际结算利润。
7. 明细较多时优先展示用户要求的字段，并保留可继续下钻的关键标识，例如订单编号、商品 ID、活动 ID、`task_id` 或 `trace_id`。
