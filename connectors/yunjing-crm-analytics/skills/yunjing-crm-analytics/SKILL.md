---
name: yunjing-crm-analytics
display_name: 云净 CRM 经营与患者运营分析
display_name_en: Yunjing CRM Analytics
description: 查询云净 CRM 授权范围内的脱敏经营、患者、客户、工单和中心运营汇总数据。
description_zh: 查询云净 CRM 授权范围内的脱敏经营、患者、客户、工单和中心运营汇总数据。
description_en: Query masked business, patient, customer, work-order, and center-operations analytics within the user's Yunjing CRM permissions.
version: 0.1.0
author: 云净 CRM
---

# 云净 CRM 运营分析说明

仅使用连接器已提供的只读工具。每次调用均由 CRM 实时校验 API Key、用户状态、`clientId` 和当前菜单权限。

## 工具选择

优先按用户问题选择一个最窄的工具；不要为同一个问题重复调用多个工具。

- 经营总览使用 `get_business_overview`。
- 月度趋势使用 `get_business_metric_trend`，`metricKey` 仅可使用工具提供的枚举。
- 月度分布使用 `get_business_breakdown`。
- 患者跟进阶段汇总使用 `get_patient_ops_funnel`。
- 跟进待办、完成和逾期汇总使用 `get_follow_up_summary`。
- 仅在用户明确要求处理优先级或待办清单时使用 `get_masked_patient_worklist`；该工具最多返回 20 条脱敏任务。
- 用户询问工单总量、状态、类型、优先级或逾期时，使用 `get_work_order_summary`。它不返回工单标题、描述、患者或单条工单明细。
- 用户询问新客户、老客户、公海客户、已绑定客户或客户阶段分布时，使用 `get_customer_operations_summary`。
- 用户询问中心患者运营效率、员工跟进绩效、费用收支、耗材/库存使用情况或中心质控指标时，使用 `get_center_operations_summary`。仅在 CRM 已授予 `center_ops:statistics:query` 权限时调用。

## 口径与权限

- 传入日期时必须使用 `YYYY-MM-DD`。未传日期的患者、客户、工单和中心运营工具默认统计截至今天的最近 30 天；开始和结束日期必须同时传入，且时间跨度不得超过 366 天。
- `get_business_overview`、`get_business_metric_trend` 和 `get_business_breakdown` 使用 CRM 固定经营统计周期，不按工具日期参数重新计算。
- 工单和客户工具中，具有中心运营统计权限的账号可查看本中心汇总；其他账号只能查看本人负责的工单或客户汇总。
- 员工跟进绩效只对已获中心运营统计权限的账号返回员工名称及任务聚合数量；普通员工无权调用该工具。
- 中心运营返回的库存和费用指标均来自既有经营分析聚合口径，例如应收/实收/欠费、耗材品牌使用分布等。没有真实数据源或未采集历史的指标，必须明确说明“暂无可用数据源”或“历史口径未采集”，不得以当前状态推导历史转化率。

## 脱敏与限制

不要传递或请求 `clientId`、医院 ID、数据源、表名、SQL、患者姓名、手机号、患者编号、客户姓名、工单标题、工单描述、跟进正文、任务结果或任何可识别患者/客户的信息。不要把返回指标与外部数据合并以尝试识别个人。

结果是脱敏数据，但汇总指标返回实际计数。输出分析时注明所用日期范围和统计口径；遇到“口径待确认”“暂无可用数据源”或“暂不可用”时，如实说明限制，不补造数据或业务结论。

## 示例意图

- “本月工单有什么积压？”：调用 `get_work_order_summary`，说明状态、优先级和逾期汇总。
- “新老客户和公海客户各有多少？”：调用 `get_customer_operations_summary`。
- “哪些员工跟进完成率低？”：调用 `get_center_operations_summary`；仅依据返回的员工聚合数据排序和分析。
- “中心费用和耗材情况怎样？”：调用 `get_center_operations_summary`，仅解释返回的费用与耗材聚合指标。
