# WeStock Data - AI 深度参考指南

> **定位**：本文档提供详细的数据格式参考、分析模板。命令列表和基本用法请参见 [SKILL.md](../SKILL.md)。
> 完整分析场景示例请参见 [scenarios-guide.md](./scenarios-guide.md)。

---

## 一、输出格式

命令执行后输出 **Markdown 表格**，AI 直接从表格中读取数据进行分析。

**单股查询**：输出一个 Markdown 表格，每列对应一个数据字段。

**批量查询**：输出批量摘要行 + 每个 symbol 的独立表格。

**查询失败**：输出 JSON 格式的错误信息（含 `success: false` 和 `error` 对象）。



---

## 二、各命令数据格式

### 实时行情（`westock quote`）

输出表格列（共通字段，三市场均返回）：
`code | name | symbol | market_type | market_name | price | prev_close | open | high | low | volume | amount | change | change_percent | turnover_rate | volume_ratio | range_pct | avg_price | time | pe_ratio | pe_fwd | pe_lyr | pb_ratio | dividend_ratio_ttm | total_market_cap | circulating_market_cap | total_shares | float_shares | high_52week | low_52week | chg_5d | chg_10d | chg_20d | chg_60d | chg_ytd`

**区间涨跌幅**：`chg_5d`/`chg_10d`/`chg_20d`/`chg_60d` = 近 N 个交易日累计涨跌幅(%)，`chg_ytd` = 年初至今(%)。问「最近 5/10/20/60 天涨了多少」**直接读取即可，无需用 `kline` 自算**。口径 =（终点价 − 往前第 N 个交易日收盘）/该收盘×100；终点价为最新价，加 `--date` 时为该日收盘（`chg_ytd` 仅实时返回）。盘中读实时值时终点尚未定盘，需注明时点。

#### 市场差异化字段（按 `market_type` 区分）

| 字段 | 说明 | A股 | 港股 | 美股 |
|------|------|:---:|:---:|:---:|
| `price_ceiling` | 涨停价（元） | ✅ | — | — |
| `price_floor` | 跌停价（元） | ✅ | — | — |
| `inner_volume` | 内盘（主动卖出量） | ✅ | — | — |
| `outer_volume` | 外盘（主动买入量） | ✅ | — | — |
| `pre_quote_price` / `_change` / `_change_pct` / `_high` / `_low` / `_volume` / `_amount` / `_turnover_rate` | 盘前集合竞价（成交价/涨跌额/涨跌幅/最高/最低/成交量/成交额/换手率） | ✅ | — | — |
| `wb_ratio` | 委比（%） | ✅ | ✅ | — |
| `lot` | 每手股数 | — | ✅ | — |
| `adr_conversion_price` | ADR 换算价（港元） | — | ✅ | — |
| `relative_hk_stock_price` | 相对港股价格 | — | ✅ | — |
| `relative_hk_stock_chg_pct` | 相对港股涨跌幅（%） | — | ✅ | — |
| `dividend_ttm` | 股息 TTM（元） | — | ✅ | ✅ |
| `eps_ttm` | 每股收益 TTM（元） | — | — | ✅ |
| `pre_market_price` / `_chg` / `_chg_pct` | 盘前价 / 涨跌额 / 涨跌幅（美元） | — | — | ✅ |
| `post_market_price` / `_chg` / `_chg_pct` | 盘后价 / 涨跌额 / 涨跌幅（美元） | — | — | ✅ |

> `market_type` 取值：`1`=沪A，`51`=深A，`62`=北交所，`100`=港股，`200`=美股。
> 差异字段仅在对应市场返回，其他市场该字段为 `undefined`，分析时需先判断。

#### 可转债维度字段（仅可转债代码返回，来源 `Kzz_*`）

可转债（沪 `sh11xxxx`/`sh13xxxx`、深 `sz12xxxx`）走 `westock quote` 时，在上述通用 + A股交易机制字段之外，额外返回以下转债维度字段；单只查询以竖排「项目/内容」表展示（规模换算为亿元、日期规整为 `YYYY-MM-DD`，缺失字段自动跳过）。

| 字段 | 说明 |
|------|------|
| `bond_equity_value` | 转股价值 |
| `bond_pure_value` | 纯债价值 |
| `bond_equity_premium` | 转股溢价率（%） |
| `bond_pure_premium` | 纯债溢价率（%） |
| `bond_double_low` | 双低 |
| `bond_rating` | 转债评级 |
| `bond_total_size` | 总规模（万元） |
| `bond_undue_size` | 剩余规模（万元） |
| `bond_term` | 期限（年） |
| `bond_undue_term` | 剩余期限（年） |
| `bond_due_date` | 到期日期 |
| `bond_ytm` | 到期收益率（%） |
| `bond_convertible` | 是否转股 |
| `bond_convert_price` | 转股价（元） |
| `bond_convert_start_date` | 转股起始日 |
| `bond_redeem_price_due` | 到期赎回价（元） |
| `bond_redeem_price_compulsory` | 强制赎回价（元） |
| `bond_redeem_price_trigger` | 强赎触发价（元） |
| `bond_buyback_price_trigger` | 回售触发价（元） |
| `bond_buyback_start_date` | 回售起始日 |
| `bond_stock_pb` | 正股 PB |
| `bond_stock_code` | 正股代码 |

> 行情接口**不返回债券简称**（`name` 为空）；可交换债及临近到期老券可能缺失部分 `Kzz_*` 字段，分析时需判空。完整发行要素/条款/现金流用 `bond`。

### 财务三大表（`westock finance`）

默认输出**核心字段窄表**（`--fields core`，★ 标记字段）；`--fields all` 恢复全字段。

> **字段后缀**：`_Q` = 单季度值，`TTM` = 过去 12 月滚动值。无后缀 = 累计值。
> ⚠️ **易混淆**：`OperatingRevenue`（营业收入）≠ `OperatingProfit`（营业利润），二者数值差异大，切勿看错列。
> **比率类指标直读披露值**：ROE / ROA / 毛利率等比率类字段，优先直读报表返回值，**禁止**用「净利润 / 净资产」自行拼算后当作报表值。

#### ★ 常用中文指标 → 英文字段 快速映射

> 用户用中文问某个指标时，先查此表确定所在表 + 字段名，再发对应 `--type` 请求。

| 中文名称 | 所在表 | 英文字段 |
|---------|-------|---------|
| 营业总收入 | income | `TotalOperatingRevenue` |
| 营业收入 | income | `OperatingRevenue` |
| 营业成本 | income | `OperatingCost` |
| 营业利润 | income | `OperatingProfit` |
| 利润总额 | income | `TotalProfit` |
| 归母净利润 | income | `NPParentCompanyOwners` |
| 扣非净利润 | income | `NPDeductNonRecurringPL` |
| 研发费用 | income | `RAndD` |
| 毛利率 | income | `GrossIncomeRatio` |
| 净利率 | income | `NetProfitRatio` |
| ROE | income | `ROEWeighted` / `ROE` |
| ROA | income | `ROA` |
| 营收增长率 | income | `TORGrowRate` |
| 净利润增长率 | income | `NPParentCompanyYOY` |
| 基本每股收益 | income | `BasicEPS` |
| 营业收入TTM | income | `OperatingRevenueTTM` |
| 总资产 | balance | `TotalAssets` |
| 总负债 | balance | `TotalLiability` |
| 净资产(股东权益) | balance | `TotalShareholderEquity` |
| 资产负债率 | balance | `DebtAssetsRatio` |
| 流动比率 | balance | `CurrentRatio` |
| 速动比率 | balance | `QuickRatio` |
| 经营现金流净额 | cashflow | `NetOperateCashFlow` |
| 投资现金流净额 | cashflow | `NetInvestCashFlow` |
| 筹资现金流净额 | cashflow | `NetFinanceCashFlow` |
| 自由现金流(公司) | cashflow | `FCFF` |

> **使用规则**：用户只问营收/利润/ROE 等利润表指标 → `--type income`；只问资产/负债 → `--type balance`；只问现金流 → `--type cashflow`。**只在用户明确要求"三大报表""全面分析"时才不加 `--type`。**

#### 完整字段速查

三大表完整字段见运行时输出（`--fields all` / `--raw`）。字段名均为英文直译，可直接推断中文（如 `TotalAssets`=总资产、`Inventory`=存货、`GoodWill`=商誉、`ContractAssets`=合同资产、`TConstruInProcess`=在建工程、`DeferredTaxAssets`=递延所得税资产、`Deposit`=吸收存款）。

**关键易混淆（务必看准）**：
- `OperatingRevenue`（营业收入，主营业务）≠ `TotalOperatingRevenue`（营业总收入，含其他业务）≠ `OperatingProfit`（营业利润）
- A 股：`NPParentCompanyOwners`=归母净利润、`NPDeductNonRecurringPL`=扣非净利润
- 港股：`OperatingIncome`=营业收入、`EarningAfterTax`=税后利润、`ProfitToShareholders`=归股东利润
- 美股：多为 `_Q` 单季度值（`Sales_Q`=营收、`NetIncome_Q`=净利润、`GrossMargin_Q`=毛利率），累计值字段常为空

**同比增速：累计口径 vs 单季口径（`_Q` 后缀）**

A 股增速类字段成对提供，两者含义不同，**问「最新一季」须用 `_Q`**：

| 字段 | 口径 | 适用问法 |
|---|---|---|
| `NPParentCompanyYOY` | 归母净利同比（**本年累计** vs 去年同期累计）| 「今年以来净利增长多少」 |
| `NPParentCompanyYOY_Q` | 归母净利同比（**该单季** vs 去年同季）| 「最新一季净利同比增长多少」 |
| `TORGrowRate` / `TORGrowRate_Q` | 营业总收入同比（累计 / 单季）| 同上 |
| `NPParentCompanyCutYOY` / `_Q` | 扣非净利同比（累计 / 单季）| 同上 |

> 一季报期两者数值接近（累计=单季），但**半年报/三季报起会显著偏离**，不可混用。
> 单位是 **%**（如 `0.43` 即 +0.43%），不是倍数，转述时不要再乘 100。

**比率类指标**（ROE/ROA/毛利率等）直读披露值，禁止自行拼算。



### K线（`westock kline`）

输出表格列：`date | open | last | high | low | volume | amount | exchange | change_pct`

> `change_pct` = 当日涨跌幅（%），= (今收 - 前收) / 前收 × 100。

> K线数值为原始数值，AI 在分析时自行进行单位换算

> ⚠️ **周期支持差异**：**美股指数**（`us.DJI`/`us.IXIC`/`us.SPX` 等）**仅支持日K**（`--period day`），不支持分钟K和周/月/季/年K。

### 资金数据

#### 港股资金流向（`westock fund flow hk<代码>`）

| 字段 | 单位 | 说明 |
|------|------|------|
| `TotalNetFlow` | 港元 | 总净流入 |
| `MainNetFlow` | 港元 | 主力净流入 |
| `RetailNetFlow` | 港元 | 散户净流入 |

#### 港股卖空数据（`westock fund short hk<代码>`）

| 字段 | 单位 | 说明 |
|------|------|------|
| `ShortShares` | 股 | 卖空股数 |
| `ShortAmount` | 港元 | 卖空金额 |
| `ShortRatio` | % | 卖空比率（卖空股数/成交量） |

#### A股资金流向（`westock fund flow sh/sz<代码>`）

| 字段 | 单位 | 说明 |
|------|------|------|
| `MainNetFlow` | 元 | 主力净流入（正=流入，负=流出）|
| `JumboNetFlow` | 元 | 超大单净流入 |
| `BlockNetFlow` | 元 | 大单净流入 |
| `MidNetFlow` | 元 | 中单净流入 |
| `SmallNetFlow` | 元 | 小单净流入 |
| `MainInFlow` | 元 | 主力流入 |
| `MainOutFlow` | 元 | 主力流出 |
| `RetailInFlow` | 元 | 散户流入 |
| `RetailOutFlow` | 元 | 散户流出 |

> 扩展字段（历史数据）：`MainNetFlow5D`/`MainNetFlow10D`/`MainNetFlow20D`（5/10/20日主力净流入）、`MainInflowRank`（流入排名）、`MainInflowCircRate`（占流通盘比例）、`MainInflowIndustryRank`（行业排名）

#### 两融数据（`westock fund margin sh/sz<代码>`）

- `FinanceValue` **融资余额**（问「两融余额/融资余额」默认指此项）｜`FinanceValueDOD` 环比(%)
- `FinanceBuyValue` 融资买入额｜`FinanceRefundValue` 融资偿还额（买入>偿还则余额上升）
- `SecurityValue` 融券余额｜`SecurityValueDOD` 环比(%)
- `TradingValue` **两融余额合计**（=融资+融券，问「融资融券余额」读此项）｜`TradingValueDif` 差额（=融资−融券）
- `closePrice`/`changePct`/`date` 当日收盘价/涨跌幅/交易日（单位：元，比率为 %）
- 算「近 N 日趋势」用 `--start/--end` 取逐日序列（只返回已披露交易日）；单日用 `--date`，该日尚未披露时报 `NOT_DISCLOSED`（两融通常收盘后更新）

#### 大宗交易（`westock fund block sh/sz<代码>`）

- `TurnoverPrice` 成交价(元)｜`TurnoverValue` 成交金额(元)｜`CloseDiscountRate` **折溢价率(%)**（官方口径，正=溢价/负=折价/0=平价，直接读取）
- `TradingType` 交易类型｜`BuySalesDepartment`/`SellSalesDepartment` 买/卖方营业部｜`SerialNumber` 当日笔次序号
- `BlockTradingInfos` 当日全部笔次明细（**JSON 字符串**，解析后为数组，每笔含上述字段；**当日笔数 = 数组长度**）
- 按单个交易日返回，跨区间统计用 `--start/--end`（逐交易日返回、自动跳过无成交日）；「发生多少次大宗交易」通常指**有成交的交易日数**，与「总笔数」是两个口径，回答时说明所用口径

#### 美股卖空数据（`westock fund short us<代码>`）

> ⚠️ **美股限制**：美股不支持 `westock fund flow`（资金流向），只支持 `westock fund short`（卖空数据）

| 字段 | 单位 | 说明 |
|------|------|------|
| `ShortRatio` | % | 卖空比率（卖空股数/流通股数） |
| `ShortShares` | 股 | 卖空股数 |
| `ShortRecoverDays` | 天 | 回补天数（卖空股数/日均成交量） |

#### 北向季度持仓（`westock fund north-holding <股票代码>`）

> 同时查询 `north_holding_detail_cur_quarterly`（最新季）与 `prev_quarterly`（次新季），合并为一张表输出。

| 字段 | 单位 | 说明 |
|------|------|------|
| `EndDate` | YYYYMMDD | 披露截止日 |
| `HoldingCap` | 元 | 持股市值 |
| `HoldingRatio` | % | 持股比例 |
| `HoldingShares` | 股 | 持股数量 |
| `CapChgQ` / `CapChgY` | 元 | 持股市值季/年变动 |

> ⚠️ 与日度 `westock fund flow` 不同：`westock north-holding` 是**季度披露**口径的全市场持仓明细。

#### 港股南下资金持仓（`westock fund south-holding <港股代码>`）

> 通过 `stock_quote_snapshot` 的 `LgtHoldInfo` 字段解析，支持批量。

| 字段 | 单位 | 说明 |
|------|------|------|
| `LgtHoldRatio` | % | 南下资金持有比例 |
| `LgtCapChgDaily` | 港元 | 日变动市值 |
| `LgtShareChgDaily` | 股 | 日变动份额 |
| `LgtCapChgQuarterly` | 港元 | 季变动市值 |
| `LgtShareChgQuarterly` | 股 | 季变动份额 |

#### 申万行业北向资金持仓分布（`westock fund north-holding <板块代码>`）

> 根据 `sw1_/sw2_/sw3_` 或 `pt…` 板块代码，查询 `north_holding_statis_sw*` 并按行业名称过滤。仅支持申万行业，不支持概念/地域板块。

| 字段 | 单位 | 说明 |
|------|------|------|
| `SW` | — | 申万行业名称 |
| `HoldingCap` | 元 | 行业北向持股市值 |
| `CapChgQ` / `CapChgY` | 元 | 持股市值季/年变动 |

### 机构评级（`westock rating`）

> 自 [Unreleased] 起重构为 **3 段精简结构**，A 股/港股/美股按市场自动分发，输出一致。

#### 段 1：目标价 & 当前评级摘要

输出表格列：`code | name | targetPriceAvg | targetPriceMax | targetPriceMin | upsideAvg | upsideMax | currentBuyCnt | currentIncCnt | currentHoldCnt | currentDecCnt | currentSellCnt | totalRatingCnt | forecastInstitutions`

- `targetPriceAvg/Max/Min`：目标价的平均/最高/最低值
- `upsideAvg/Max`：上涨空间百分比（基于当前价）
- `currentBuyCnt/IncCnt/...`：当前评级分布

#### 段 2：评级月度趋势统计（近 7 个月）

输出表格按月分布：`month | buyCnt | incCnt | holdCnt | decCnt | sellCnt`，反映买入/增持/中性/减持/卖出 5 档评级在最近 7 个月的变化趋势。

#### 段 3：价格 vs 目标价历史走势对比

输出表格列：`date | closePrice | targetPriceAvg`，逐日对比股价与机构目标价均值。

> **分析要点**：
> - 段 1 看共识强度（买入家数 vs 卖出家数）和上涨空间（upside）
> - 段 2 看评级动量（最近 1-2 个月评级是否上调/下调）
> - 段 3 看股价是否已 price-in 机构预期，或仍有低估空间

### 一致预期（`westock consensus`）

按代码前缀自动分发：A 股走 `queryCNConsensusForecast`，港股走 `queryHKConsensusForecast`，美股暂不支持。

#### A 股

输出表格，列含 `code | name | targetPrice`，以及 `forecasts` 数组中的 `year | revenue | netProfit | eps | pe | pb | ps | revenueYoy | netProfitYoy | institutionCnt`

#### 港股

按"时间维度"展示（行=季度，列=各指标）。顶层字段：`code | name | quarters`。

##### `quarters` 主表（按 `period` 升序）

| 字段 | 下游字段 | 说明 |
|------|---------|------|
| `period` | `ForecastPeriod` | 预测报告期（如 `2025Q4`、`2026Q1`） |
| `epsForecast` | `EPSForecast` | 每股收益-预测 |
| `revenueForecast` | `RevenueForecast` | 营业收入-预测（亿港币） |
| `netProfitForecast` | `NetProfitForecast` | 净利润-预测（亿港币） |
| `peRatioForecast` | `PERatioForecast` | 市盈率-预测 |
| `psRatioForecast` | `PSRatioForecast` | 市销率-预测 |
| `roeForecast` | `ROEForecast` | 净资产收益率-预测 |

> 列顺序固定为 EPS → 营收 → 净利润 → PE → PS → ROE（与微证券页面 tab 顺序一致）；某指标在该季度没有预测时该列为 `undefined`/缺省。

**分析要点**：目标价 vs 当前价（上涨空间）、EPS增速（盈利确定性）、PE走势（估值消化）、机构数（共识可信度）

---

### ESG 评级（`westock esg`）

查询中证 / 聚源两套 ESG 字母档评级。**与 `westock rating`（券商研报评级）和 `westock score`（量化评分）不同**；仅 A 股（`sh`/`sz`/`bj`）。

**输出格式**：
- 单股：按来源分行（中证 / 聚源），列含 `评级 | 发布日 | 截止日 | 变动`
- 批量：宽表 `中证评级 | 聚源评级 | …`

**字段（归一化后）**：

| 字段 | 下游字段 | 说明 |
|------|---------|------|
| `grade` | `EsgGrade` | 当前评级（中证：AAA/BBB…；聚源：A/B/C…，**不可跨源比高低**） |
| `endDate` | `EndDate` | 数据截止日 |
| `publDate` | `InfoPublDate` | 评级发布日 |
| `prevGrade` | （chg 清单，字段名待首条非空样本确认） | 上次评级 |

> **数据说明**：中证覆盖约 900 只，聚源覆盖更广（约 5000+），单股可能仅有聚源数据。

---

### 技术指标（`westock technical`）

> **指标**：MA_5/10/20/60/120/250、MACD/DIF/DEA、KDJ_K/D/J、RSI_6/12/24、BOLL_UPPER/MID/LOWER。

#### 用法与输出

输出表格列：`code | date | period | closePrice | ma.MA_5 | ma.MA_10 | ... | macd.DIF | macd.DEA | macd.MACD | kdj.KDJ_K | ...`

嵌套对象（ma/macd/kdj/rsi/boll）的字段会展平为 `分组.字段名` 格式。`period` 字段标识 K 线周期（day/week/month 等）。不指定 `--start/--end` 时按默认返回最新一期全量指标；在截面模式（不传 `--date`/`--start`/`--end`）下附加 `--limit N` 表示"最近 N 期"（自动按区间拉取后取末尾 N 条）；指定 `--start/--end` 后按区间逐交易日返回，`--limit` 控制条数（默认 2000）。支持 A 股/港股/美股 个股及指数/ETF/板块（与 `kline` 同源；分钟 K 的标的限制同 `kline`：除美股指数外均支持）。

**典型用法**：
- `westock technical sh600000` — 日K最新一期指标
- `westock technical sh600000 --period week --start 2026-02-01 --end 2026-03-01` — 周K区间（支持 --date/--period/--start/--end/--limit，多股逗号分隔）

#### 解读要点

- **MA**：MA_5/10/20/60/120/250，短期均线在长期均线之上为多头排列
- **MACD**：DIF 上穿 DEA 为金叉（买入信号），下穿为死叉
- **KDJ**：K > 80 超买区，K < 20 超卖区
- **RSI**：RSI_6 > 70 超买，RSI_6 < 30 超卖

### 筹码成本（`westock chip`）

#### 截面

输出表格列：`code | name | date | closePrice | chipProfitRate | chipAvgCost | chipConcentration90 | chipConcentration70`

#### 历史区间

输出表格，每行一个交易日，列名同上。

**解读**：盈利率>80%=获利盘占优；收盘价>平均成本=整体盈利；集中度越低=筹码越集中（主力控盘可能）

### 市场/指数/板块（`market`）

#### 截面（`MarketQuoteData`）关键字段

| 字段 | 说明 |
|------|------|
| `closePrice`/`changePct` | 收盘价/涨跌幅 |
| `chg5D`/`chg10D`/`chg20D`/`chg60D`/`chgYtd` | 多日涨跌幅(%) |
| `advancingCount`/`decliningCount` | 上涨/下跌家数 |
| `mainNetFlow`/`jumboNetFlow`/`blockNetFlow` | 主力/超大单/大单净流入（沪深，元）|
| `midNetFlow`/`smallNetFlow` | 中单/小单净流入（沪深，元）|
| `totalNetFlow`/`retailNetFlow` | 总/散户净流入（港股，港元）|

> ⚠️ 美股不支持资金流向字段，仅支持 `westock fund short`（卖空数据）


### 行业经营数据（`westock sector oper`）

查询各行业经营指标的历史序列数据，覆盖29个申万一级行业。数据包括价格、产量、销量、收入等经营指标。

**输出格式**：
- 按行业分组输出
- 每个行业输出一个 Markdown 表格，列含 `指标代码 | 指标名称 | 数据点 | 最新日期 | 最新值`

**返回字段说明**：

| 字段 | 说明 |
|------|------|
| `指标代码` | 经营指标的唯一代码（如 `F_COAL_INV_COAL_QHD_D`） |
| `指标名称` | 经营指标的中文名称（如"库存:煤炭:秦皇岛港:日"） |
| `数据点` | 该指标可用的历史数据点数量 |
| `最新日期` | 最新数据点的日期（格式：`YYYYMMDD`） |
| `最新值` | 最新数据点的数值 |

**支持行业**（共29个）：
传媒、电力设备、电子、房地产、纺织服饰、非银金融、钢铁、公用事业、国防军工、环保、机械设备、基础化工、计算机、家用电器、建筑材料、建筑装饰、交通运输、煤炭、美容护理、农林牧渔、汽车、商贸零售、社会服务、石油石化、食品饮料、通信、医药生物、银行、有色金属

**参数说明**：
- `<行业>`：支持中文名称（如"煤炭"）或标识（如 `coal`），**不要**传板块代码（如 `pt02021291`）
- `--list`：列出所有支持经营数据的行业
- `--date`：查询日期 YYYY-MM-DD（默认今天）

---

### 板块估值（`westock sector valuation`）

查询单个或多个板块的 PE/PB/PS/PCF/DIV 及**历史百分位**（相对自身历史区间）。**与 `westock market-overview --type valuation`（中证全指大盘估值）不同**；与 `westock sector forecast`（未来一致预期估值）互补。

**输出格式**：
- 截面：Markdown 表，每行一个板块；支持多板块逗号批量对比
- 历史（`--start` + `--end`）：按 `EndDate` 升序的时间序列；**每次仅支持单板块**

**核心字段**（下游原始字段名，CLI 直接输出）：

| 字段 | 说明 |
|------|------|
| `code` / `name` | 板块代码 / 名称 |
| `EndDate` | 数据截止日（`YYYYMMDD`） |
| `PeTTM` / `PeTTMPct` | 市盈率 TTM / 历史百分位（**%**，越高表示相对历史越贵） |
| `PbLF` / `PbLFPct` | 市净率 LF / 历史百分位 |
| `PsTTM` / `PsTTMPct` | 市销率 TTM / 历史百分位 |
| `PcfTTM` / `PcfTTMPct` | 市现率 TTM / 历史百分位 |
| `DivTTM` / `DivTTMPct` | 股息率 TTM / 历史百分位 |
| `*PrevM/Q/W/Y` | 各指标相对上月/上季/上周/去年的变动 |

> **参数**：传**板块代码**（`pt*`）。支持申万行业及聚源概念/地域/产业。先用 `westock search --type sector` 获取代码。

**分析要点**：
- `PeTTMPct` / `PbLFPct` 等百分位：判断行业相对自身历史估值高低
- 与 `westock sector forecast` 的 `pe`/`peg` 对照：当前估值 vs 预期盈利增速是否匹配
- 与 `westock sector finance` 的 `roeTTM` 对照：盈利质量能否支撑估值

---

### 行业未来盈利预测（`westock sector forecast`）

查询申万一级/二级行业的机构一致预期盈利路径（未来 3 年）。**与 `westock consensus`（个股一致预期）不同**：无目标价/EPS，数值为**行业聚合**口径。

**输出格式**：
- 按行业分组，每组一个 Markdown 表（行=预测年度，按 `year` 升序）
- 顶层含行业名、`code`（pt 代码）、`swLevel`、`forecastDate`

**`forecasts` 主表字段**（列顺序：营收/利润 → 增速 → 估值）：

| 字段 | 下游字段 | 说明 |
|------|---------|------|
| `year` | `ConYear` | 一致预期年度 |
| `revenue` | `ConOr` | 一致预期营业收入（**万元**，行业加总） |
| `netProfit` | `ConNp` | 一致预期归母净利润（**万元**，行业加总） |
| `netAssets` | `ConNa` | 一致预期归母净资产（**万元**，行业加总） |
| `revenueYoy` | `ConOrYoy` | 营业收入同比增速（**%**） |
| `netProfitYoy` | `ConNpYoy` | 归母净利润同比增速（**%**） |
| `netProfitCagr2Y` | `ConNpYoy2Y` | 归母净利润两年复合增长率（**%**） |
| `pe` | `ConPe` | 一致预期市盈率（倍） |
| `pb` | `ConPb` | 一致预期市净率（倍） |
| `ps` | `ConPs` | 一致预期市销率（倍） |
| `roe` | `ConRoe` | 一致预期 ROE（**%**） |
| `peg` | `ConPeg` | 一致预期 PEG（**%**，清单口径，非常见 PEG 倍数） |

> **参数**：仅支持申万一级/二级板块代码（`pt*`）。**不支持**申万三级、聚源地域/产业/风格概念（如 `pt03001176` 海南地域概念会明确报错）。先用 `westock search --type sector` 获取申万行业代码。

**分析要点**：
- `netProfitYoy` / `netProfitCagr2Y`：盈利增速路径与确定性
- `pe` + `peg`：估值水平与成长性匹配（注意 `peg` 为 % 口径）
- `roe`：行业整体盈利能力
- 与 `westock sector valuation`（当前估值百分位）对照：预期利润增速能否消化估值

---

### 申万行业财务指标（`westock sector finance`）

查询申万行业成份股聚合的财报 TTM 指标。**与个股 `westock finance`（三大表）不同**；与 `westock sector forecast`（未来一致预期）互补。

**输出格式**：
- 默认：多行业合并为一张截面表（含 `name | code | swLevel`）
- `--start` + `--end`：按 `endDate` 升序的历史序列（同期业内变动）

**核心字段（归一化后）**：

| 字段 | 下游字段 | 说明 |
|------|---------|------|
| `endDate` | `EndDate` | 财报期（`YYYYMMDD`） |
| `revenueTTM` | `RevenueTTM` | 营业收入 TTM（**万元**，行业加总） |
| `netProfitTTM` | `NetProfitTTM` | 归母净利润 TTM（**万元**） |
| `netProfitYoY` | `NetProfitYoY` | 净利同比增速（**%**） |
| `roeTTM` | `RoeTTM` | ROE TTM（**%**） |
| `debtRatio` | `DebtRatio` | 资产负债率（**%**） |
| `grossProfitRatioTTM` | `GrossProfitRatioTTM` | 毛利率 TTM（%） |
| `netProfitRatioTTM` | `NetProftRatioTTM` | 净利率 TTM（%，下游字段有拼写 typo） |

> **参数**：支持 sw1/sw2/sw3；聚源概念/地域会明确报错。历史查询需同时指定 `--start` 与 `--end`（与 `westock sector valuation` 一致）。

**分析要点**：`netProfitYoY`+`roeTTM` 看盈利质量；`debtRatio` 看杠杆；配合 `westock sector valuation` / `westock sector forecast` 构成基本面→估值→预期链。

---

### 市场总览（`westock market-overview`，A 股大盘画像）

8 个子类（type）归并到单一入口，提供 A 股大盘"宏观体检"。来源是 8 个 `market_statis_*` 后端清单。

| type | 中文 | 说明 |
|------|------|------|
| `summary` | 画像总评（默认） | 14 维度得分 + 状态文案（估值/情绪/技术/趋势/风格轮动/股市规模/宏观情绪/北向资金/两融情绪/PMI 等） |
| `trade` | 三大指数收盘统计 | 上证/深证/创业板 + 成交额多周期均值（5D/20D/60D） |
| `interval` | 三大指数多周期涨跌 | 5D/20D/60D/250D 涨跌 + 52 周高低 |
| `westock technical` | 大盘技术面 | MACD / KDJ / RSI / BOLL / MA |
| `updown` | A 股涨跌停 / 红绿盘 | 涨停/跌停家数 + 红绿盘比 + 创新高/新低家数 |
| `margin` | 两融余额变动 | 两融余额 + 多周期变动 |
| `valuation` | 估值百分位 | 中证全指 PE/PB/PS + 历史百分位 |
| `rotation` | 风格轮动 | 沪深300 / 中证1000 / 成长 / 价值 板块轮动 |

**用法**：`westock market-overview`（默认 summary）、`--type trade|technical,updown|all`（单/多/全量）、`list`（列所有 type）

**summary 14 维度** 每个维度含：`name`（维度名）、`westock score`（0~100 得分）、`status`（状态文案，如"估值偏高"、"情绪乐观"）。**这是给 AI 做今日市场点评最直接的入口** —— 一次调用即可得到"估值/情绪/技术/趋势/风格"5 大类共 14 个维度的状态画像。

### 排行数据（`rank`）

输出 Markdown 表格，列头为字段中文标签（来自 `list_data_schema`），如"市盈率TTM(倍)"、"股息率TTM(%)"等。

**返回信息**：清单名称/查询日期/总条数、排序字段与方向、分页信息（offset/limit/hasMore）、每行含代码/名称/各指标字段。

> 参数：`--limit`(默认20/最大50)、`--offset`(默认0)、`--desc`(默认true降序)；清单代码见 SKILL.md 排行清单表。字段中文标签由 `list_data_schema` 自动解析。

---

### 市场/大盘资讯（`westock news list` + 指数代码）

传**指数代码**查询，多指数逗号批量；常用代码见 [commands.md](./commands.md)。全市场热文榜用 `westock hot news`。

### 分红数据（`westock dividend/calendar`）

输出表格，字段因市场不同：

- **A股**：`reportEndDate | dividendFlag | procedure | dividendType | proposalSn | rightRegDate | exDiviDate | bonusShareRatio | tranAddShareRatio | cashDiviRMB | totalCashDiviComRMB | dividendPlan`
- **港股**：`reportEndDate | exDiviDate | cashPayDate | cashDivPerShare | specialDivPerShare | totalCashDivi | dividendPlan`
- **美股**：`exDivDate | regDate | payDate | dividendCurrency | dividend | dividendPlan`

> 美股可能额外含 `splitInfo`。参数：`--years N` 查近 N 年分红历史；`--all` 返回所有记录（含未实施方案，默认只返回已实施）；返回按报告期/除权日降序。

### 财报披露日历（`westock disclosure`）

- **A股**：`reportEndDate | disclosureEndDate | disclosureDate | disclosureDesc`
- **港股**：`reportEndDate | disclosureDesc`
- **美股**：`reportEndDate | disclosureDate | disclosureDesc`

## 三、货币单位处理

> ⚠️ **重要**：港股财报返回港元/美元，美股返回美元，展示时**必须**标注正确货币单位

**港股**：检查 `CurrencyType`（"港币"/"美元"/"人民币"）和 `CurrencyUnit` 字段
- ✅ 正确：`营业收入：832.3亿港元`
- ❌ 错误：`营业收入：¥832.3亿`

**跨期对比注意**：同比/环比增长率可能受汇率换算影响，展示时建议添加说明：`"注：同比数据可能受汇率波动影响"`

---

## 四、单位换算

### 4.1 各市场每手股数（⚠️ 换算手数时必须先确认）

> **`quote` 返回的 `volume` 字段单位是「股」（shares），不是「手」（lots）。** 将成交量折算为手数时，必须按市场使用对应的每手股数，**禁止统一按 A 股 100 股/手计算**。

| 市场 | 每手股数 | 来源 |
|------|---------|------|
| **A 股** | **100 股/手** | 固定值，全市场统一 |
| **港股** | **各股不同**，以接口返回值为准 | `quote` 返回的 **`lot` 字段**（每手股数） |
| **美股** | **1 股 = 1 手** | 美股无"手"概念，1 股即为最小交易单位 |

**换算公式**：
- A 股：`手数 = volume ÷ 100`
- 港股：`手数 = volume ÷ lot`（lot 取自 `quote` 返回值）
- 美股：不换算为"手"，直接用股数

### 4.2 常用换算

| 数据类型 | 原始单位 | 转换 |
|---------|---------|------|
| 成交量（A 股） | 股 | 先 `÷100`=手，再 `÷10000`=万手；或直接 `÷1000000`=万手 |
| 成交量（港股） | 股 | 先 `÷lot`（取 quote 的 lot 字段）=手，再 `÷10000`=万手 |
| 成交额/市值/主力资金 | 元/港元/美元 | ÷100000000=亿元/亿港元/亿美元 |
| 卖空数量 | 股 | ÷1000000=百万股 |

---

## 四点五、ETF 数据字段

> **子命令**（必填）：`westock profile` 档案+资产配置 | `overview` 运作概览 | `holdings` 申赎清单+重仓涨跌 | `nav` 净值时序。

### ETF 档案（`westock etf profile`）

| 字段 | 说明 |
|------|------|
| `trackIndexCode/Name` | 跟踪指数（清单 `etf_track_index`） |
| `establishDate` | 成立日期 |
| `trusteeInstitution` | 托管人 |
| `purchaseStatus` / `redemptionStatus` | 申购/赎回状态 |
| `investScope` / `investStrategy` | 投资范围/策略 |
| `isTPlus0` | 是否支持 T+0 |
| `subscriptionFee` / `managementFee` / `custodyFee` / `serviceFee` | 认购/管理/托管/销售服务费率(%) |
| `managers` | 基金经理履历（snapshot `EtfManagerInfo`） |
| `classification` | 4 级分类（清单 `etf_classification`）：`primary`/`secondary`/`tertiary`/`quaternary`/`memo` |
| `managerHistory` | 经理历史（清单 `etf_manager`）：`current`/`first`/`longest`/`history` |
| `allocation` | 资产配置（snapshot `EtfAssetAllocation` + 清单规模） |

### ETF 运作概览（`westock etf overview`）

| 字段 | 说明 |
|------|------|
| `totalAsset` / `etfSize` | 总资产/规模及周月季年变化 |
| `chgPct` / `chgPct5D` / `chgPct20D` / `chgPct60D` / `chgPct52W` / `chgPctYtd` | 涨跌幅（多周期） |
| `etfDisc` / `etfDiscAvg*` | 溢折率及同指数均值 |
| `turnoverRate` / `turnoverValue` / `etfTurnover*` | 换手率/成交额 |
| `ytdMaxDrawdown` / `maxDrawdown1M/3M/6M/1Y/3Y` | 最大回撤（snapshot `EtfPerformance`） |
| `etfInFlow` / `etfInFlow*Avg` | 净申购及周月季年均值 |
| `peTtm` / `pb` / `psTtm` / `pcfTtm` / `peg` / `roe` / `divTtm` | 估值绝对值 |
| `peTtmPct` / `pbPct` / … | 估值历史百分位 |

### ETF 持仓（`westock etf holdings`）

| 字段 | 说明 |
|------|------|
| `holdings` | 申赎清单成分股（清单 `etf_prlist_{code}` 优先，snapshot 兜底） |
| `topStockChanges` | 重仓股涨跌：`code`/`name`/`ratio`/`rate`/`change` |

### ETF 净值时序（`westock etf nav`）

| 字段 | 说明 |
|------|------|
| `date` | 交易日 |
| `nav` | 单位净值（优先 `EtfNav`，缺失时回退 `ClosePrice`） |
| `closePrice` | 场内收盘价（可能与 nav 不同） |
| `navChange` | 净值涨跌额（相邻两日 `EtfNav` 差分；区间内首日不返回） |
| `navChangePct` | 净值涨跌幅(%)（同上） |

> ⚠️ `nav` 的涨跌由客户端按 `EtfNav` 差分计算，**不是** `ChangePrice`（收盘价涨跌）。查场内 OHLC 用 `westock kline`，不是 `westock etf nav`。

---

## 四点六、公司回购字段

### 回购数据（`westock buyback`）

**港股字段**：
| 字段 | 说明 |
|------|------|
| `BuybackShares` | 回购股份(股) |
| `BuybackMoney` | 回购金额(港元) |
| `BuybackPrice` | 回购均价(港元) |
| `BuybackCumMoney` | 本轮回购累计金额(港元) |

**A股字段**（BuybackAttach 数组）：
| 字段 | 说明 |
|------|------|
| `BuybackFunds` | 本次回购资金(元) |
| `BuybackSum` | 本次回购数量(股) |
| `BuybackPrice` | 本次回购均价(元) |

> 回购数据按日期降序排列，仅返回有回购记录的交易日。

---

### 风险事件（`westock risk`）

#### 特别处理（ST）

| 字段 | 说明 |
|------|------|
| `type` | 特别处理类型（ST/\*ST/SST/撤销ST） |
| `explain` | 事项描述 |
| `date` | 信息发布日期 |
| `riskLevel` | 风险等级：high（高风险）、medium（中风险）、low（低风险） |

#### 股权质押

| 字段 | 说明 |
|------|------|
| `date` | 股权质押披露截止日期 |
| `floatPledgedVolume` | 无限售股份质押数量（万股） |
| `nonFloatPledgedVolume` | 有限售股份质押数量（万股） |
| `pledgeNum` | 质押笔数 |
| `pledgeRatio` | 质押比例 |
| `totalPledge` | 质押数量（万股） |
| `riskLevel` | 风险等级：high（质押比例≥50%）、medium（30%-50%）、low（<30%） |

#### 解禁信息

| 字段 | 说明 |
|------|------|
| `initialInfoPublDate` / `infoPublDate` | 解禁信息首次/最新发布日期 |
| `estimateActual` | 解禁日期类型 |
| `shareHolderName` | 解禁股东名 |
| `changeReason` | 解禁原因 |
| `restrictedCondition` | 限售条件说明 |
| `newAFloatListed` | 新增可售A股 |
| `actualFloatListedShares` | 实际上市流通数量 |
| `riskLevel` | 风险等级：high、medium、low |

#### 诉讼仲裁

| 字段 | 说明 |
|------|------|
| `date` | 诉讼仲裁最新公告日期 |
| `actionDesc` | 行为描述 |
| `subjectMatterStat` | 案由简称 |
| `latestSuitSum` | 涉诉金额（元） |
| `eventSubject` | 事件主体 |
| `eventSubjectRole` | 事件主体在诉讼中的角色 |
| `plaintiff` | 诉讼仲裁原告 |
| `defendant` | 诉讼仲裁被告 |
| `plaintiffAssociation` / `defendantAssociation` | 原/被告与上市公司关联关系 |
| `caseStatus` / `*InstanceStatus` / `sppStatus` / `adjudgementStatus` | 仲裁/一审/二审/最高院监督/判决执行 各阶段状态 |
| `riskLevel` | 风险等级：high（涉诉金额>1亿或作为被告）、medium（>1000万）、low |

#### 增发信息

| 字段 | 说明 |
|------|------|
| `issueType` / `eventProcedure` / `stockType` / `issuePurpose` / `issueObject` | 增发类别/进程/A股类型/目的/对象（字段名自解释） |
| `*Date`/`*PublDate` | 各阶段公告/生效日期（自解释） |
| `issuePrice` / `issuePriceCeiling` / `issuePriceFloor` | 发行价 及 上/下限（元） |
| `issueVol` | 发行量（万股） |
| `seoProceeds` / `seoNetProceeds` | 募集资金总额/净额（元） |

#### 高管变动（LeaderChange）

| 字段 | 说明 |
|------|------|
| `leaderName` | 高管姓名 |
| `leaderPosition` | 职位（如 副总裁/董事/总经理） |
| `leaderPositionType` | 职位类型（如 经营层/董事会） |
| `leaderStartDate` | 任职起始日期（已规范化为 YYYY-MM-DD） |
| `leaderChangeReason` | 变动原因（如 退休/辞职/换届） |

#### 高管增减持（ExecutiveTransferPlans）

| 字段 | 说明 |
|------|------|
| `managerName` | 高管姓名 |
| `managerSharesChange` | 股份变动数量（**负数表示减持，正数表示增持**） |
| `managerDealPrice` | 成交均价（元） |
| `managerHoldChangeDeclareDate` | 公告日期（已规范化为 YYYY-MM-DD） |

#### 评级信息（BondRatingInfo）

| 字段 | 说明 |
|------|------|
| `rating` | 评级（如 AAA/AA+/AA） |
| `ratingOutlook` | 评级展望（如 稳定/正面/负面） |
| `ratingChgDirection` | 变动方向（如 维持/上调/下调） |
| `ratingStandard` | 评级标准 |
| `ratingOrg` | 评级机构（如 中诚信国际/联合资信） |

> **注意**：风险事件只提供客观数据展示，不进行主观评分或风险等级判定。用户需根据实际情况自行判断风险程度。无效代码或无风险事件的股票会输出"暂无风险事件"，AI 应如实反馈不要编造风险信息。

---

### 事件总览（`westock events`，42 类标签）

> **与 risk 的差别**：`westock risk` 是 8 类风险事件**细查**（按个股取明细字段），`westock events` 是 42 类事件标签**速览**（按 `stock_event` 全市场清单一次拉取后客户端过滤）。`westock events` 仅展示挂在股票身上的事件 ID + 中文描述，覆盖中性+利好+风险全场景，不含明细字段。

**返回字段**：

| 字段 | 说明 |
|------|------|
| `date` | 查询日期（YYYY-MM-DD） |
| `stocks[].code` | 股票代码（如 sh600519） |
| `stocks[].name` | 股票名称（清单未返回时通过 `stock_quote_snapshot` 兜底补全） |
| `stocks[].tagIds` | 命中的事件 ID 数组（按 `--types` 过滤后） |
| `stocks[].tagDescs` | 事件 ID 对应中文描述（与 tagIds 顺序一致） |

**42 类事件 ID 映射（按大类分组）**：

| 大类 | 事件 ID → 说明 |
|------|----------------|
| 交易异动 | 1=大宗交易(1个月)、21=龙虎榜详情(2周)、22=龙虎榜统计(2周) |
| 股本变动 | 2=回购披露(1个月)、5=实施公告含权期、6=除权除息填权(3天)、7=分红预案、8=分红决案、17/18=定增上市后1/3月、19/20=定增上市前1月/1周 |
| 业绩披露 | 9=业绩快报、10=业绩预告、11=新增财报(7天)、12=即将发布财报 |
| 指数变动 | 13=刚加入重要指数(1周)、14=即将加入、15=刚被踢出(1周)、16=即将踢出 |
| 董监高 | 23=董监高变动、24=增减持披露、25/26=计划增持实施中/未实施、27/28=计划减持实施中/未实施 |
| 股权事件 | 29=股东大会(1月内)、30=吸收合并、31=资产重组、32/33=更名公告/观察期、38=要约收购 |
| 限售解禁 | 34=即将实际解禁、35=解禁上市观察(2周)、36=预计解禁(3月内) |
| 法律处罚 | 3=被处罚未生效、4=重大违规(1月内)、37=涉诉披露(1月) |
| 停复牌 | 39=预计复牌(3天)、40=已复牌(1周)、41=停牌中、42=停牌超30天 |

> 完整中文描述与最新分组见上表（与代码同源）。

**典型用法**：

```bash
westock events sh600519                  # 个股事件标签速览
westock events sh600519,sz000001         # 批量

```

**与 risk 的选择**：
- 想知道**有没有**某类事件 → `westock events`（轻量速览，1 次接口拉清单）
- 想拿到**明细字段**（如解禁数量、质押比例、诉讼金额、高管姓名） → `westock risk`

> **数据特性**：`westock events` 命中规则由 `stock_event` 清单维护方决定（如"过去 1 个月内"、"未来 3 天内"等窗口）；某些 ID（如停复牌系列）只在事件发生窗口内才会被打标。当某只股票 `westock events` 返回为空时，应明确告知用户"当前无事件命中"，**不应编造事件**。

---

## 五、分析模板

### 成交量分析

1. `westock kline <CODE> --period day --limit 20` → 从表格中提取 `volume` 列
2. 计算：平均值、最大/最小值、前10日均值 vs 后10日均值
3. 识别：放量日（>均值×1.5）、缩量日（<均值×0.5）

### 资金流向分析

**A股**：`westock fund flow <CODE>` → 提取 `MainNetFlow`/`JumboNetFlow`/`BlockNetFlow` → 转换单位（元→亿元）→ 统计净流入/流出天数

**港股资金**：`westock fund flow <CODE>` → 提取 `TotalNetFlow`/`MainNetFlow` → 分析主力趋势

**港股卖空**：`westock fund short <CODE>` → 提取 `ShortShares`/`ShortAmount`/`ShortRatio` → 卖空比率>15%需关注

**美股卖空**：`westock fund short <CODE>` → 提取 `ShortRatio`/`ShortShares`/`ShortRecoverDays` → `ShortRatio`>10%或`ShortRecoverDays`>5天需关注

**指数/板块**：`market <CODE>` → 提取 `mainNetFlow`/`jumboNetFlow`/`blockNetFlow` → 转换单位 → 判断主力方向

### 技术指标分析

**MACD**：DIF与DEA交叉（金叉=买信号/死叉=卖信号）、MACD柱正负变化、DIF/DEA相对0轴位置

**KDJ**：K与D交叉、J值>80超买/<20超卖

**RSI**：RSI_6>70超买/<30超卖，RSI_6与RSI_12背离

**均线**：多头排列（MA5>MA10>MA20>MA60）、MA60/120/250作为支撑/压力位

### 筹码趋势分析（历史区间）

- 盈利率上升 = 获利盘增加（股价上涨）
- 平均成本抬升 = 筹码成本中枢上移（主力可能建仓）
- 集中度下降 = 筹码趋于集中（主力吸筹控盘）
- 集中度上升 = 筹码趋于分散（可能派发）

### 机构评级分析（港股/美股）

1. 评级共识度：`(ratingBuyCnt + ratingIncCnt) / ratingCnt`
2. 目标均价 vs 当前价 → 上涨/下跌空间
3. 港股：`earningsForecast` EPS × 目标PE → 合理估值区间

### A股一致预期分析

1. 目标价 vs 当前价 → 上涨空间
2. 多年度EPS增速 → 盈利增长确定性
3. PE走势 → 估值是否逐年降低（估值消化）
4. `institutionCnt` → 共识覆盖度

### 宏观经济数据分析

**可用指标**（短名带 region 前缀，详见 [macro-fields.md](./macro-fields.md)）：

**PMI 分析**：PMI>50 扩张/<50 收缩；新订单-产成品库存差值=领先指标；连续 3 个月趋势 > 单月

**GDP 价格指标分析**：CPI 同比>3% 通胀/<0 通缩；PPI-CPI 剪刀差=上下游传导；核心 CPI=真实通胀

**货币指标分析**：M2>名义GDP=流动性宽裕；M1-M2 剪刀差收窄=经营活跃；社融同比=融资需求；LPR/MLF=政策信号

**国债收益率曲线分析**（`yield_curve`）：10Y-1Y 利差扩大=预期改善、倒挂=衰退；长端下行=避险/宽松；短端跟随政策利率

**MLF 公开市场操作分析**（`cn_mlf`）：净投放持续为正=主动宽松；操作利率下调→LPR 跟随（宽松信号）；月末余额=总量基调

**溢价率分析**（`cn_premium_value` / `cn_premium_curve`）：
1. **股债溢价率（EquityPremium）= E/P - 10Y国债收益率**：数值越高股票越便宜；`EprPct10Y`≥80% 历史高位（偏便宜）、<20% 历史低位（偏贵）
2. **红利溢价率（DividendPremium）= 股息率 - 10Y国债收益率**：高位 → 高股息策略胜率提升
3. `cn_premium_curve`（约 2400 条日频）看长期分位上下轨；`cn_premium_value`（1 条最新值+10 年分位）看当前快速判断

**期限利差分析**（`cn_term_spread`）：
1. **`TermSpread` = Yield10Y - Yield2Y（bps）**：利差扩大（变陡）→ 经济预期改善；倒挂 → 衰退预期
2. **`CurveForm*`**（牛陡/牛平/熊陡/熊平）：牛陡=短端下行更快（宽松/避险买短）、牛平=长端下行更快（衰退/避险买长）、熊陡=长端上行更快（通胀过热）、熊平=短端上行更快（央行紧缩）
3. **`LongDif*` vs `ShortDif*`** → 判断曲线驱动来自哪一端

### 板块成份股分析

> ⚠️ **概念股查询重点**：当用户问"XX概念有哪些股票"（如"华为概念股"、"AI概念股"、"新能源汽车概念"），必须使用统一 `westock search` 入口两步查询：
> 1. `westock search 华为 --type sector` — 搜索板块代码
> 2. `westock sector constituent <搜索到的代码>` — 查询成份股
>
> **不要用外部搜索工具**。

**板块代码格式**：

| 前缀 | 类型 | 示例 |
|------|------|------|
| `sw1_` | 申万一级行业 | `sw1_pt01801080`(电子) |
| `sw2_` | 申万二级行业 | `sw2_pt01801081`(半导体) |
| `sw3_` | 申万三级行业 | `sw3_pt01801081` |
| `area_` | 聚源地域概念 | `area_pt0001`(北京) |
| `style_` | 聚源产业概念 | `style_pt0001` |
| `indus_` | 聚源风格概念 | `indus_pt0001` |

> 指数成份股请使用 `westock index` 命令：`westock index constituent sh000300`（A 股）/ `westock index constituent hkHSI`（港股）

**返回字段（港股指数成份股）**：

| 字段 | 说明 |
|------|------|
| `code` | 成份股代码（如 hk00700） |
| `name` | 成份股名称（如 腾讯控股） |
| `chg` | 涨跌幅（%） |
| `turnover` | 成交额 |

> **注意**：港股指数 `BkComponentStocks` 仅返回涨跌幅前 20 只成份股（A 股返回全量）；如需恒指全部 80 只，建议通过 ETF 持仓间接获取。


---

## 六、格式化输出规范

- 金额超过亿元：使用"亿元"/"亿港元"/"亿美元"
- 成交量超过万手：使用"万手"
- 涨跌幅：保留2位小数，带 +/- 号
- 日期：YYYY-MM-DD 格式
- 数据为空时说明"暂无数据"，**不可伪造数据**
- 港股/美股财务数据必须标注货币单位
