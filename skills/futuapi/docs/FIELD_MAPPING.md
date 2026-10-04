# 持仓与资金字段映射（与 APP 对齐）

## 单只持仓字段

`position_list_query` 返回的字段中，有多组容易混淆的成本/盈亏字段。**必须使用与富途牛牛 APP 一致的字段**，否则盈亏数据会与用户在 APP 上看到的不符，导致信任问题。

| APP 显示 | 正确的 API 字段 | 说明 |
|----------|----------------|------|
| 平均成本价 | `average_cost` | 实际买入均价 |
| 现价 | `nominal_price` | 当前市场价 |
| 市值 | `market_val` | 单只持仓市值（按该持仓原始币种） |
| 持有数量 | `qty` | 持仓股数 |
| 可用数量 | `can_sell_qty` | 可卖股数 |
| 未实现盈亏 | `unrealized_pl` | 按均价计算的浮动盈亏 |
| 未实现盈亏比例 | `pl_ratio_avg_cost` | 按均价计算的盈亏百分比（默认按百分比计算，如 5.23 表示 5.23%） |
| 已实现盈亏 | `realized_pl` | 已平仓部分的盈亏 |
| 总盈亏金额 | `unrealized_pl + realized_pl` | 未实现 + 已实现 |
| 今日盈亏 | `today_pl_val` | 当日盈亏 |

## 持仓汇总字段（APP 顶部横栏）

| APP 显示 | 正确来源 | 说明 |
|----------|---------|------|
| 市值（CAD） | `accinfo_query(currency=CAD).market_val` | 取账户资金接口的 CAD 口径市值，**不能**直接累加持仓的 `market_val`（持仓市值可能是不同币种，如 USD 和 CAD 混合） |
| 持仓收益 | 需按 CAD 口径换算后汇总 | 直接累加 `unrealized_pl` 会因混币种导致不准确，应参考账户级汇总数据 |
| 今日盈亏 | 需按 CAD 口径换算后汇总 | 同上 |

> **币种换算注意**：当持仓涉及多币种（如同时持有 USD 和 CAD 标的）时，汇总市值和盈亏**必须进行币种换算**，不能直接累加不同币种的数值。优先使用 `accinfo_query(currency=目标币种)` 获取账户级汇总数据；如需手动换算，应通过网上查询实时汇率（如搜索 "USD to CAD exchange rate"）获取最新汇率进行计算，避免使用硬编码汇率。

## 禁止使用的字段

摊薄成本口径，与 APP 显示不一致：
- `cost_price` / `diluted_cost`：摊薄成本，包含分红、拆股等调整，会拉低成本价
- `pl_val`：按摊薄成本计算的盈亏，可能显示为盈利而实际是亏损
- `pl_ratio`：按摊薄成本计算的盈亏比例

> **已验证**：以上字段映射已通过 APP 截图与 API 返回值逐项比对验证（2026-03-20）。所有固定值完全匹配，实时价格相关字段的差异均来自查询时间差导致的价格波动。

## 账户资金字段映射

`accinfo_query` 返回的字段与 APP 对应关系：

| APP 显示 | API 字段 | 说明 |
|----------|---------|------|
| 总资产 | `total_assets` | 账户资产净值 |
| 证券市值 | `market_val` | 所有持仓市值合计 |
| 多头市值 | `long_mv` | 多头持仓市值 |
| 空头市值 | `short_mv` | 空头持仓市值 |
| 可用资金 | `total_assets - initial_margin` | API 的 `available_funds` 对加拿大账户返回 N/A，需手动计算 |
| 冻结资金 | `frozen_cash` | |
| 现金总值 | `cash` | 当前查询币种的现金 |
| USD 现金 | `us_cash` | |
| CAD 现金 | `ca_cash` | |
| 可提总值 | `avl_withdrawal_cash` | |
| USD 可提 | `us_avl_withdrawal_cash` | |
| CAD 可提 | `ca_avl_withdrawal_cash` | |
| 最大购买力 | `power` | |
| CAD 购买力 | `cad_net_cash_power` | |
| USD 购买力 | `usd_net_cash_power` | |
| 风控状态 | `risk_status` | LEVEL3=安全, LEVEL2=警告, LEVEL1=危险 |
| 初始保证金 | `initial_margin` | |
| 维持保证金 | `maintenance_margin` | |
| 剩余流动性 | 无直接字段 | API 未返回，需自行计算 |
| 杠杆倍数 | 无直接字段 | API 未返回，需自行计算 |

**注意**：
- 加拿大账户（FUTUCA）查询资金时必须指定 `currency`（`USD` 或 `CAD`），否则会报错 "This account does not support converting to this currency"
- `available_funds` 对部分账户类型返回 N/A，此时用公式 `total_assets - initial_margin` 计算可用资金
- `max_withdrawal` 对部分账户类型返回 N/A
