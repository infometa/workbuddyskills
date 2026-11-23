---
name: tool4seller
description: 使用 tool4seller MCP 查询已授权亚马逊店铺的经营数据、分析销售利润与库存广告问题，并通过用户确认的计划管理广告。适用于 tool4seller 店铺分析与广告操作，不处理其他电商平台。
---

# tool4seller

通过 WorkBuddy 中已连接的 tool4seller MCP 工具操作。首次使用需完成浏览器中的 tool4seller OAuth 登录及权限选择；不要要求用户把密码或 Token 发到对话中。

## 选择工具

以当前 MCP 工具描述、inputSchema 和 initialize instructions 为准；以下名称为服务端名称，WorkBuddy 可能为它们增加连接器前缀。参数必须按实际 schema 构造。

| 需求 | 工具 |
| --- | --- |
| 账号、店铺与能力发现 | `get_current_user`、`list_stores`、`discover_capabilities` |
| 销售、利润、流量与评分 | `query_sales`、`query_profit`、`query_sales_traffic`、`query_review_ratings` |
| 库存、预警、入库货件及明细 | `query_inventory`、`query_inventory_alerts`、`list_inbound_shipments`、`list_inbound_shipment_items` |
| 广告表现、活动、广告组、广告及组合 | `query_advertising`、`query_advertising_campaigns`、`query_advertising_ad_groups`、`query_advertising_ads`、`query_advertising_portfolios` |
| 搜索词、投放、否定投放与购买商品 | `query_advertising_search_terms`、`query_advertising_targets`、`query_advertising_negative_targets`、`query_advertising_purchased_products` |
| Amazon 投放与出价建议 | `query_advertising_target_recommendations`、`query_advertising_bid_recommendations` |
| 诊断指引 | `diagnose_sales_change`、`diagnose_profit_anomaly`、`diagnose_ad_efficiency`、`inventory_risk_review` |
| 计划查看、确认与取消 | `get_workflow_plan`、`confirm_workflow_plan`、`cancel_workflow_plan` |
| 活动创建 | `prepare_campaign_creation`、`apply_campaign_creation` |
| 活动调整 | `prepare_campaign_changes`、`apply_campaign_changes` |
| 广告组创建 | `prepare_ad_group_creation`、`apply_ad_group_creation` |
| 广告组调整 | `prepare_ad_group_changes`、`apply_ad_group_changes` |
| 商品广告创建 | `prepare_product_ad_creation`、`apply_product_ad_creation` |
| 商品广告调整 | `prepare_product_ad_changes`、`apply_product_ad_changes` |
| 投放创建 | `prepare_targeting_creation`、`apply_targeting_creation` |
| 投放调整 | `prepare_targeting_changes`、`apply_targeting_changes` |
| 订单明细 | `query_sales_orders` |
| 账户额度 | `query_account_usages` |
| 关键词追踪与排名趋势 | `query_keyword_rank_trackers`、`query_keyword_rank_trends` |
| ABA与ASIN搜索词 | `query_aba_search_terms`、`query_aba_search_term_trends`、`query_asin_search_terms` |
| 关键词追踪创建 | `prepare_keyword_rank_tracking_creation`、`apply_keyword_rank_tracking_creation` |
| 关联竞品替换 | `prepare_keyword_rank_competitor_replacement`、`apply_keyword_rank_competitor_replacement` |
| 关键词追踪状态变更 | `prepare_keyword_rank_tracking_changes`、`apply_keyword_rank_tracking_changes` |
| 多阶段广告创建草稿 | `prepare_workflow_draft`、`get_workflow_draft`、`continue_workflow_draft` |

不确定支持哪些工作流或参数时先用 `discover_capabilities`。诊断工具返回的步骤和查询建议不是最终业务结论，应继续查询所需证据。

## 查询与分析

- 从 `list_stores` 的结果解析店铺名称、`storeId`、站点、币种和时区，不猜测 ID。无法唯一匹配时再询问用户。
- 日期使用 `yyyy-MM-dd`，`startDate` 和 `endDate` 均包含在范围内，单次报表范围最多 95 个自然日。按店铺时区解释相对日期，在结果中写出实际范围。
- 更长的只读查询拆成互不重叠的窗口；比例类指标如 ACOS、ROAS 根据累计基础指标重新计算，不平均各窗口的比例。不同币种分别汇总。
- 广告写计划及其指标筛选条件不自动拆分长日期范围；请用户选定支持的分析窗口。广告排期日期不受报表 95 天限制。
- 按工具 schema 和返回的分页信息继续读取；抽样或未取完时说明覆盖范围。空数据不等于零业绩，缺少权限不等于没有店铺。
- 结论应关联店铺、期间、币种和指标；审核沙箱的合成数据与模拟执行结果必须明确标注。

例：“查看最近七天销售额和利润” → 解析授权店铺与日期 → 分别调用 `query_sales` 和 `query_profit` → 按店铺和币种呈现。

## 广告变更

1. 依据用户目标选择对应的独立 `prepare_*` 工具，仅传符合该工具 schema 的 `parameters`，不传顶层 `workflowType` 或 `policyId`。准备计划后，向用户展示影响对象、旧值与新值、币种、数量和警告。
2. 用户明确确认这份计划后，才调用 `confirm_workflow_plan`，传入服务器返回的 `planId`、`planVersion`、`planHash` 和实际审核的 `expectedItemCount`。
3. 根据已确认计划的 `workflowType`，选择上表中匹配业务的独立 `apply_*` 工具，使用返回的一次性 `confirmationReceipt` 执行；每个新计划生成独立 `idempotencyKey`，同一计划重试必须复用原键。
4. 如执行超时或断线，先查 `get_workflow_plan`，不要创建替代计划重复执行。`INDETERMINATE` 表示结果未确定，须核实后再决定后续操作。

完整广告结构创建目前支持 SP 自动或手动广告。多阶段广告结构使用 `AD_STRUCTURE_CREATE` 草稿，通过 `continue_workflow_draft` 推进；传递其返回的 `applyContinuation`，并展示 apply 返回的下一阶段预览。不得手动跳过依赖阶段，每个写计划分别确认。已知输入下的查询和下一阶段预览可继续准备。

创建工具的支持范围按广告产品和实体类型区分，不推断所有创建操作都支持 SP、SB、SD。正向关键词和 ASIN 投放可按 schema 调整竞价或状态；否定投放没有竞价动作，支持恢复历史暂停记录或不可逆归档。Amazon 自动投放主题由创建广告组后生成，不手动创建。

取消尚未执行的计划使用 `cancel_workflow_plan`；取消不会撤销已发生的广告修改。不可逆归档等后果应在确认前明确说明。

## 异常恢复

- 401 / 授权失效：引导用户在 WorkBuddy 重新连接；凭证刷新由客户端 OAuth 管理器处理。
- 403 / scope 不足：说明所需权限并引导重新授权；套餐或账号限制按服务端错误说明处理。
- 参数错误：依据 schema 修正日期、ID 或枚举，不重复提交相同错误参数。
- 限流或查询超时：按服务端重试提示处理，可缩小只读查询范围；写操作遵循上述计划状态核实规则。

## 关键词追踪变更

先查询追踪配置与账户额度，新增使用 prepare_keyword_rank_tracking_creation，恢复/移除使用 prepare_keyword_rank_tracking_changes（items[].changes.status=ACTIVE/ARCHIVED），关联竞品替换使用 prepare_keyword_rank_competitor_replacement（items[].changes.competitorAsins 为完整集合）准备计划，展示变化并获得明确确认后调用 confirm_workflow_plan 和对应组的 apply 工具。prepare 仅传 parameters，apply 仅传 planId、confirmationReceipt、idempotencyKey，不传广告续接参数。删除保留排名历史；替换竞品关联必须先读取当前关联并提交完整的新集合。严格区分 PARENT/CHILD 与 OWN_PRODUCT/COMPETITOR，不自行替换商品范围。两个阶段都会核验适用额度；新增竞品及关联替换还会校验实时 Catalog 关系，关系变化后需要重新准备并确认计划。状态修改不读取 Catalog；ARCHIVED 是移除指令，查询返回 NOT_TRACKED。查询日期上限按各工具实际 Schema 执行；订单使用 UTC 时间且最多31天，不套用一般报表95天规则。
