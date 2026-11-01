# 字段清单与枚举速查（yj-fin-data）

> 本文件是**活的**：首次实跑后把真实返回的字段名回写进来。
> 科目与列的**一手来源**是本服务提供的列目录（`field_list` 可填写的英文字段名），本文件只做高频子集速查。

---

## 1. 枚举闭集（写错就查不到，绝不报错）

| 参数 | 取值 | 备注 |
|---|---|---|
| 财务 `period` | `q1` / `interim` / `q3` / `annual` / `latest` | 一季报 / 中报 / 三季报 / 年报 / 最新一期（默认） |
| 财务 `report_type` | `consolidated` / `consolidated_restated` / `standalone` / `standalone_restated` | 默认 `consolidated`（合并报表） |
| 财务 `period_type` | `accumulated` / `quarterly` | 港股/美股**只有** `accumulated` |
| 财务 `market` | `a` / `hk` / `us` | 默认 `a` |
| 主营 `breakdown` | `product` / `industry` / `region` | 不传 = 三种全并发 |
| 主营 `period` | `interim` / `annual` | 只有中报和年报有披露 |
| 股东 `holder_type` | `top10` / `top10_float` | 十大股东 / 十大流通股东 |
| 估值 `indicator` | `pe_ttm` / `ps_ttm` / `pb_mrq` / `peg` / `pcf_ttm` / `em` | `em` = 企业倍数 |
| 线索 `query_mode` | `by_security` / `by_industry` | — |
| 线索 `source_list` | `research_report` / `conference` / `announcement` / `view` | — |
| 热点 `category_list` | `morning_briefing` / `noon_briefing` / `afternoon_flash` / `evening_briefing` | — |
| 主题跟踪 `type` | `morning` / `night` | — |
| 知识库 `resource_types` | `研究报告`/`外资研报`/`内部报告`/`AI云盘`/`首席观点`/`公司公告`/`产业公众号`/`会议纪要`/`调研纪要`/`网络纪要` | — |
| 全市场关键字 | `a_shares` / `hk_stocks` / `us_stocks` | **不是 `all`**，必须单独传 |

**报告期入参形态**——`period` 取英文闭集，直接给下列取值即可，没有 `Q1~Q4/Q0` 这类季度缩写：

```
q1（一季报）   interim（中报）   q3（三季报）   annual（年报）   latest（最新一期，默认）
```

---

## 2. 行情字段

### 日 K

```json
["security_code","trade_date","open","high","low","close","pre_close","change","pct_change","volume","amount"]
```

### 分钟 K

```json
["security_code","trade_time","open","high","low","close","change","pct_change","volume","amount"]
```

> 日期列是 `trade_time` 不是 `trade_date`。

### 实时快照

```json
["security_code","exchange","trade_date","trade_time","trade_status","latest_price",
 "open","high","low","pre_close","change","pct_change","volume","amount","amplitude"]
```

> **不返回**换手率与量比，改为返回 `trade_status`。需要换手率走 EDE。

### 资金流向

```json
["security_code","trade_date",
 "small_inflow","small_outflow","small_net_inflow",
 "medium_inflow","medium_outflow","medium_net_inflow",
 "large_inflow","large_outflow","large_net_inflow",
 "xlarge_inflow","xlarge_outflow","xlarge_net_inflow",
 "main_inflow","main_outflow","main_net_inflow",
 "total_inflow","total_outflow","total_net_inflow"]
```

### 单位（错一次全篇错）

| 字段 | 单位 |
|---|---|
| `volume` | **股**（不是手） |
| `amount` | 元 |
| `pct_change` | %（已乘 100，不是小数） |
| 市值 | 行情列目录**不提供**市值列；如需市值见 `yj-fin-comparable` 技能说明 |

---

## 3. 财务科目：常用英文名 → 中文名

`field_list` 只认**英文名（即下列 canonical，非 camelCase）**。以下为高频子集，完整列以本服务提供的列目录为准。

### 利润表

| 英文名 | 中文名 |
|---|---|
| `total_op_rev` | 营业总收入 |
| `op_rev` | 营业收入 |
| `tot_op_cost` / `total_op_cost` | 营业总成本 |
| `op_cost` | 营业成本 |
| `net_profit` | 净利润 |
| `net_profit_attr_parent` | 归属于母公司所有者的净利润 |
| `net_profit_attr_noncontrol` | 少数股东损益 |
| `total_profit` | 利润总额 |
| `op_profit` | 营业利润 |
| `sales_exp` / `admin_exp` / `rd_exp` / `fin_exp` | 销售 / 管理 / 研发 / 财务费用 |
| `basic_eps` | 基本每股收益 |
| `diluted_eps` | 稀释每股收益 |

### 资产负债表（FDD 常用）

| 英文名 | 中文名 |
|---|---|
| `total_assets` | 资产总计 |
| `total_liab` | 负债合计 |
| `total_equity` | 所有者权益合计 |
| `total_parent_eq` | 归属母公司所有者权益合计 |
| `cash` / `monetary_assets` | 货币资金 |
| `accounts_receivable` | 应收账款 |
| `inventory` | 存货 |
| `goodwill` | 商誉 |
| `total_ppe` / `ppe` | 固定资产 |
| `total_cip` / `cip` | 在建工程 |
| `st_borrowings` | 短期借款 |
| `lt_borrowings` | 长期借款 |
| `contract_liab` | 合同负债 |
| `accounts_payable` | 应付账款 |

### 现金流量表

| 英文名 | 中文名 |
|---|---|
| `net_op_cash_flows` | 经营活动产生的现金流量净额 |
| `net_inv_cash_flows` | 投资活动产生的现金流量净额 |
| `net_fin_cash_flows` | 筹资活动产生的现金流量净额 |
| `cash_from_sales` | 销售商品、提供劳务收到的现金 |
| `cash_paid_acq_construct_assets` | 购建固定资产等支付的现金 |
| `dep_amort_fixed_assets` | 固定资产折旧/摊销 |
| `cash_paid_dividends_interest` | 分配股利、利润或偿付利息支付的现金 |

### 身份与时点列

| 字段 | 说明 |
|---|---|
| `security_code` / `security_name` | 证券代码 / 证券名称 |
| `date` | 财报截止日期 |
| `earliest_annc_date` | **最早公告日期**——时点对齐必须用这个（目录无独立的公告日期字段） |
| `report_period` | 报告期中文（如"2025年三季报"） |

---

## 4. 估值分析

```json
{ "field_list": ["value","percentile_rank"] }
```

- `value`：指标值
- `percentile_rank`：在 N 年中所处分位（N=1，即近一年）
- 六个指标要**分别调用** `valuation_analysis`，可并发（扇出 5）

**本工具不暴露 `skipNull`**——它与 `field_list` 组合会把正常数据静默过滤成 0 行。

---

## 5. EDB（行业/宏观/产品指标）

- 频率后缀：`daily` / `weekly` / `monthly` / `quarterly` / `halfyearly` / `yearly`
- 单次批量上限 **10 个指标**
- `limit`（search）1–200，**默认 100**（不传即 100）

**检索措辞**：

| 场景 | 正确写法 | 错误写法 |
|---|---|---|
| 中国宏观 | `CPI`、`GDP` | `中国 CPI`（中国指标名不含"中国"） |
| 商品价格 | `黄金现货价`、`原油结算价` | `黄金价格` |
| 产品销量 | `新能源汽车销量`、`空调销量` | `比亚迪销量`（分品牌查不到，要逐品牌查） |

---

## 6. EDE（公司指标）

- `calendar_type`：**不传时接口默认 `ND` 不是 `TD`**。报告期类指标传错会整片返 `null` **且不报错**。
- `currency` 默认 `DFT`；`scale` 默认 `"0"`
- 单次 **3 万单元格**上限
- 季度日期：`03-31` / `06-30` / `09-30` / `12-31`
- 目前**仅 A 股**

参数覆盖写法：

```json
{ "indicator_param_list": [
    {"indicator_code":"qte_high","param":{"adjustType":"3"}},
    {"indicator_code":"qte_close","param":{"adjustType":"2"}}
]}
```

语义：**多指标 × 单证券** 或 **单指标 × 多证券**（谁少谁拆）。

---

## 7. 题材与板块

| 步骤 | 工具 | 返回 |
|---|---|---|
| 题材名 → concept_id | `concept_search` | `{concept_id, concept_name}` |
| 题材档案 | `concept_info` | **Markdown 文本**（定义/投资逻辑/行业空间/竞争格局） |
| 题材成分股 | `concept_securities` | `{summary, rows:[{group_name, security_code, security_name}]}` |
| 板块名 → sector_id | `sector_search` | `{sector_id, sector_name}` |
| 板块成分股 | `sector_constituents` | `{security_code, security_name}` |

`concept_info` 是数据技能里**唯一返回文本**的工具，可直接引用进报告。
题材与板块是两套 ID 体系，`concept_id` 与 `sector_id` **不能混用**。
