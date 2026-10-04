# 宏观经济指标字段说明

本文档列出 `westock macro` 命令的指标清单（短名表）与字段命名规律。

> 数据来源：腾讯自选股宏观经济数据接口

## 子命令总览

```bash
westock macro list [--region cn|us|hk|jp|eu|global]    # 列出指标
westock macro indicator <短名[,短名...]> [...]          # 查主题型指标
westock macro indicator --region <r> [--date D]         # 一键拉某 region 全套
westock macro expect list                               # 列 36 个地区
westock macro expect --area <iso3> [--year Y | --start --end]  # 海外预期日历

```

每个 entry 在注册表里声明 `region` + `mode`：
- `mode=date` → 用 `--date`（默认今天），底层 `query_list_data_by_date(实际日期)`
- `mode=year` → 用 `--year`/`--start --end`，底层 `query_list_data_by_date(YYYY-01-01)`

## 指标清单（短名表）

### 中国 (cn) — 按年查询指标（22 个）

| 短名 | 完整代码 | 名称 | 分类 |
| --- | --- | --- | --- |
| `cn_gdp` | `macro_gdp` | GDP数量指标 | GDP |
| `cn_cpi_ppi` | `macro_cpi_ppi` | GDP价格指标(CPI/PPI) | GDP |
| `cn_pmi` | `macro_pmi` | GDP供给指标(PMI) | GDP |
| `cn_profit` | `macro_profit` | GDP供给指标(工业企业利润) | GDP |
| `cn_valueadded` | `macro_valueadded` | GDP供给指标(工业增加值) | GDP |
| `cn_consumption` | `macro_consumption` | GDP需求指标(消费) | GDP |
| `cn_investment` | `macro_investment` | GDP需求指标(投资) | GDP |
| `cn_export` | `macro_export` | GDP需求指标(进出口) | GDP |
| `cn_export_value` | `macro_export_value` | GDP需求指标(出口交货值) | GDP |
| `cn_prosperity` | `macro_prosperity` | GDP供给指标(企业景气指数) | GDP |
| `cn_fiscal` | `macro_fiscal` | GDP财政指标 | GDP |
| `cn_power_consumption` | `macro_power_consumption` | GDP供给指标(用电量) | GDP |
| `cn_disposable_income` | `macro_disposable_income` | GDP需求指标(可支配收入) | GDP |
| `cn_capacity_utilization` | `macro_capacity_utilization` | GDP供给指标(产能利用率) | GDP |
| `cn_product_output` | `macro_product_output` | GDP供给指标(宏观产量) | GDP |
| `cn_financing` | `macro_financing` | 货币需求指标(社融) | 货币 |
| `cn_fundquantity` | `macro_fundquantity` | 货币供给指标(数量) | 货币 |
| `cn_fundcost` | `macro_fundcost` | 货币供给指标(利率) | 货币 |
| `cn_yield_curve` | `macro_yield_curve` | 货币供给指标(国债收益率曲线) | 货币 |
| `cn_mlf` | `macro_mlf` | 货币供给指标(公开市场操作/MLF) | 货币 |
| `cn_forecast` | `macro_forecast` | 宏观预测 | 综合 |
| `cn_calendar_hist` | `macro_calendar_hist` | 宏观日历历史 | 综合 |

### 中国 (cn) — 按日期查询指标（11 个）

| 短名 | 完整代码 | 名称 | 分类 |
| --- | --- | --- | --- |
| `cn_core` | `macro_core_indicators_cur_p1/p2` | 最新核心宏观指标（聚合短名，一键拉 p1+p2） | 综合 |
| `cn_core_p1` | `macro_core_indicators_cur_p1` | 最新核心宏观指标(1) | 综合 |
| `cn_core_p2` | `macro_core_indicators_cur_p2` | 最新核心宏观指标(2) | 综合 |
| `cn_employment` | `macro_employment` | 就业情况 | 综合 |
| `cn_calendar_future` | `macro_calendar_future` | 宏观日历未来 | 综合 |
| `cn_premium_curve` | `macro_premium_curve` | 溢价率曲线(红利/股债) | 估值 |
| `cn_premium_value` | `macro_premium_value` | 溢价率水平(含10年分位) | 估值 |
| `cn_term_spread` | `macro_term_spread` | 期限利差与曲线形态 | 估值 |
| `cn_lpr` | `macro_lpr` | 贷款市场报价利率(LPR) | 中国专项 |
| `cn_caixin_pmi` | `macro_caixin_pmi` | 财新PMI | 中国专项 |
| `cn_installed_capacity` | `macro_installed_capacity` | 发电装机容量 | 中国专项 |

### 美股 (us) — 按日期主题指标（24 个）

| 短名 | 完整代码 | 名称 |
| --- | --- | --- |
| `us_employment` | `macro_us_employment` | 美股宏观(就业) |
| `us_eco_growth` | `macro_us_eco_growth` | 美股宏观(经济增长) |
| `us_inflation` | `macro_us_inflation` | 美股宏观(通胀) |
| `us_confidence` | `macro_us_confidence` | 美股宏观(景气指数) |
| `us_monetary` | `macro_us_monetary` | 美股宏观(货币政策) |
| `us_fiscal` | `macro_us_fiscal` | 美股宏观(财政政策) |
| `us_energy` | `macro_us_energy` | 美股宏观(能源板块) |
| `us_realestate` | `macro_us_realestate` | 美股宏观(地产板块) |
| `us_consumption` | `macro_us_consumption` | 美股宏观(消费) |
| `us_manufacturing` | `macro_us_manufacturing` | 美股宏观(工业生产) |
| `us_trade` | `macro_us_trade` | 美股宏观(对外贸易) |
| `us_treasury_holders` | `macro_us_treasury_holders` | 美股宏观(国债持有分布) |
| `us_fiscal_p2` | `macro_us_fiscal_p2` | 美股宏观(财政政策P2) |
| `us_monetary_p2` | `macro_us_monetary_p2` | 美股宏观(货币政策P2) |
| `us_fed_asset` | `macro_us_fed_asset` | 美股宏观(美联储资产结构) |
| `us_fed_liability` | `macro_us_fed_liability` | 美股宏观(美联储负债结构) |
| `us_fed_netliquidity` | `macro_us_fed_netliquidity` | 美股宏观(美联储净流动性) |
| `us_fed_qe_qt_status` | `macro_us_fed_qe_qt_status` | 美股宏观(美联储QE/QT状态) |
| `us_vix` | `macro_us_vix` | 美股宏观(VIX) |
| `us_usd_index` | `macro_us_usd_index` | 美股宏观(美元指数) |
| `us_key_index` | `macro_us_key_index` | 美股宏观(三大股指) |
| `us_debt_size` | `macro_us_debt_size` | 美股宏观(债务规模) |
| `us_term_spread_10y2y` | `macro_us_term_spread_10y2y` | 美股宏观(期限利差-10y2y) |
| `us_term_spread_10y3m` | `macro_us_term_spread_10y3m` | 美股宏观(期限利差-10y3m) |

### 美股 (us) — 按年主题指标（5 个）

| 短名 | 完整代码 | 名称 |
| --- | --- | --- |
| `us_yield_curve` | `macro_us_yield_curve` | 美股宏观(国债收益率曲线) |
| `us_policy_rate_anchor` | `macro_us_policy_rate_anchor` | 美股宏观(政策利率锚) |
| `us_sofr_real_rate` | `macro_us_sofr_real_rate` | 美股宏观(SOFR实际利率) |
| `us_sofr_exp_rate` | `macro_us_sofr_exp_rate` | 美股宏观(SOFR市场预期利率) |
| `us_broad_rate` | `macro_us_broad_rate` | 美股宏观(广义短端与长端利率) |

### 港股 / 日本 / 欧元区 — 按日期主题指标

| 区域 | 数量 | 短名 |
| --- | --- | --- |
| 港股 (hk) | 4 个 | `hk_eco_growth` / `hk_export_reserve` / `hk_monetary` / `hk_others` |
| 日本 (jp) | 6 个 | `jp_eco_growth` / `jp_inflation` / `jp_employment` / `jp_confidence` / `jp_monetary` / `jp_export_reserve` |
| 欧元区 (eu) | 6 个 | `eu_eco_growth` / `eu_inflation` / `eu_monetary` / `eu_confidence` / `eu_export_reserve` / `eu_employment` |

> 这些主题指标返回**事件日历型数据**：每条记录对应一次具体的指标发布（如"美国 5 月 ISM 制造业 PMI"）。统一 schema：`IndicatorName / OccurDate / OccurTime / ActualValue / ForecastValue / FormerValue`。

### 海外预期日历 (global) — 按年（按地区 iso3）

通过 `westock macro expect --area <iso3>` 查询。短名形如 `expect_<iso3>`，共 36 个地区：

| iso3 | 国家/地区 | iso3 | 国家/地区 | iso3 | 国家/地区 |
| --- | --- | --- | --- | --- | --- |
| `chn` | 中国 | `usa` | 美国 | `jpn` | 日本 |
| `hk` | 中国香港 | `twn` | 中国台湾 | `kor` | 韩国 |
| `sgp` | 新加坡 | `aus` | 澳大利亚 | `nzl` | 新西兰 |
| `ind` | 印度 | `idn` | 印度尼西亚 | `mys` | 马来西亚 |
| `tha` | 泰国 | `phl` | 菲律宾 | `vnm` | 越南 |
| `eu` | 欧洲联盟 | `euz` | 欧元区 | `efta` | 欧英EFTA |
| `uk` | 英国 | `fra` | 法国 | `deu` | 德国 |
| `ita` | 意大利 | `esp` | 西班牙 | `grc` | 希腊 |
| `che` | 瑞士 | `swe` | 瑞典 | `nor` | 挪威 |
| `rus` | 俄罗斯 | `ukr` | 乌克兰 | `tur` | 土耳其 |
| `can` | 加拿大 | `mex` | 墨西哥 | `bra` | 巴西 |
| `chl` | 智利 | `zaf` | 南非 | `glo` | 全球 |

---

## 字段命名规律

主题型指标（cn_*）字段名 = `指标_子项_口径`，多段用 `_` 连接，如 `CPI_YOY_FOOD` = CPI·同比·食品类。看懂规律后，绝大多数字段无需逐条查表。

### 口径后缀（通用）

| 后缀 | 含义 | 示例 |
| --- | --- | --- |
| `_YOY` | 同比(%) | `CPI_YOY` = CPI 同比 |
| `_MOM` | 环比(%) | `CPI_MOM` = CPI 环比 |
| `_CUM` | 累计值 | `ENTERPRISE_PROFIT_CUM` = 工业企业利润累计 |
| `_CUR` | 当期值 | `CONSUMP_CUR` = 社零当期值 |
| `_YTD` | 年初至今累计 | `FISCAL_PUB_REV_YTD` = 一般公共预算收入累计 |
| `_Q` | 季度 | `CAPU_CAPU_Q` = 产能利用率(季) |
| `_Y` | 年度 | `PROD_OUT_COAL_Y` = 原煤产量(年) |
| `_CHG` | 同比增减量 | `CAPU_CAPU_CHG` = 产能利用率同比增减 |

### 拼音缩写对照（CPI 分类子项，无法从字段名推断）

| 缩写 | 含义 |
| --- | --- |
| `JTTX` | 交通和通信 |
| `JYWY` | 教育文化和娱乐 |
| `JZ` | 居住 |
| `SHYP` | 生活用品及服务 |
| `SPYJ` | 食品烟酒 |
| `YLBJ` | 医疗保健 |
| `YZ` | 衣着 |

### 易混淆的截断英文缩写（可支配收入/消费支出子项）

| 缩写 | 含义 |
| --- | --- |
| `WAGE` | 工资性收入 |
| `BIZ` | 经营净收入 |
| `PROP` | 财产净收入 |
| `TRSF` | 转移净收入 |
| `CLTH` | 衣着(clothing) |
| `HOUS` | 居住(housing) |
| `HH` | 生活用品及服务(household) |
| `COMM` | 交通通信(communication) |
| `EDUC` | 教育文化娱乐(education) |
| `HLTH` | 医疗保健(health) |
| `OTHR` | 其他用品和服务(other) |

> 其余子项为完整英文单词（`FOOD`/`CAR`/`COAL`/`CHEMICAL`/`ELECTRIC`/`MINING`/`TEXTILE`/`MEDICINE`/`OIL`/`PLASTIC`/`METAL`/`AGRICULTURE`/`NONFERROUS_METAL` 等），可直接从字段名推断中文含义，不再逐条列出。

## 特殊 schema

### 事件日历型（主题型 us_/hk_/jp_/eu_ + 海外预期 expect 共用）

| 字段 | 说明 |
| --- | --- |
| `IndicatorName` | 指标名（中文，如"美国 5 月非农就业"） |
| `OccurDate` | 数据发生/发布日期（YYYYMMDD） |
| `OccurTime` | 发布时间（HH:MM） |
| `ActualValue` | 实际值（已发布） |
| `ForecastValue` | 市场预测值 |
| `FormerValue` | 前值 |
| `Importance` | 重要程度（仅海外预期，1=低 / 2=中 / 3=高） |

### cn_core（聚合）

`cn_core` = `cn_core_p1` + `cn_core_p2`，一次拉取最新核心宏观指标（PMI/CPI/PPI/SHIBOR/10Y国债/工业企业利润/工业增加值/社零/固投/社融/M1/M2/出口/外汇储备/汇率/失业率等）。字段名带 `CORE_P1_`/`CORE_P2_` 前缀，其中 `SM_` 开头为"现值"字段，均可从字段名直接推断含义。

### 估值 / 期限类（cn_premium_* / cn_term_spread）

| 字段 | 说明 |
| --- | --- |
| `DividendPremium` | 红利溢价率(%) |
| `EquityPremium` | 股债溢价率(%) |
| `DprPct10Y` | 红利溢价率 10 年百分位(%) |
| `EprPct10Y` | 股债溢价率 10 年百分位(%) |
| `Yield10Y` / `Yield2Y` | 10 年 / 2 年国债收益率(%) |
| `TermSpread` | 期限利差(bps) |
| `CurveFormD/W/M/Q/Y` | 日/周/月/季/年形态（牛陡/牛平/熊陡/熊平） |
| `LongDif*` / `ShortDif*` | 长端 / 短端收益率变化(%) |
