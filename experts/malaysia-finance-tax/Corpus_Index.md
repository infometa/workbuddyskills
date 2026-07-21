# Malaysia Finance & Tax Expert — 语料库索引 (Corpus Index)

> 最后更新: 2026-07-08 (v2.0 — 大规模扩充)
> 总规模: **36份 Reference_Texts** (~2.6 MB) + 12份 CSV (~0.9 MB) + 1个 DuckDB (12 MB, 33张表, 28,295行)

---

## 一、Reference_Texts

### A. 税务 (Taxation)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 1 | `income_tax_guide.txt` | 5.8 KB | 5,920 | 企业所得税(15-24%)、个人所得税(0-30%)、预扣税 | LHDN, PwC |
| 2 | `sst_act_2018_guide.txt` | 5.9 KB | 6,015 | 销售与服务税(SST)税率、注册门槛、申报 | Royal Customs, LHDN |
| 3 | `customs_tariff_guide.txt` | 5.9 KB | 6,039 | 海关关税、HS编码、进出口税费 | JKDM/RMCD |
| 4 | `mida_incentives_guide.txt` | 4.1 KB | 4,213 | MIDA投资激励 (PS/ITA/RA/GITA) | MIDA |
| 5 | `regional_incentives_guide.txt` | 2.4 KB | 2,478 | 区域投资激励(Iskandar/ECER/Sabah/Sarawak) | MIDA, IRDA, ECERDC |
| 6 | `transfer_pricing_guide.txt` | 6.3 KB | 6,399 | ✅ 转让定价规则、文档要求、APA、惩罚条款 | LHDN, OECD |
| 7 | `einvoice_guide.txt` | 5.9 KB | 6,013 | ✅ 电子发票分阶段实施、MyInvois、技术规范 | LHDN |
| 8 | `rpgt_guide.txt` | 5.6 KB | 5,680 | ✅ 房产盈利税税率、豁免、计算方法 | LHDN |
| 9 | `digital_tax_ssm_guide.txt` | 10.0 KB | 10,262 | ✅ 数字经济税(FDRSP) + SSM公司注册流程 | LHDN, SSM, Customs |

### B. 银行与外汇 (Banking & Forex)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 10 | `bnm_fep_guide.txt` | 4.5 KB | 4,570 | BNM外汇政策(FEP)、非居民/居民规则 | BNM |
| 11 | `banking_system_guide.txt` | 9.5 KB | ~9,500 | ✅ [扩充] 银行体系、支付系统、利率、数字银行、Basel III | BNM |

### C. 合规与会计 (Compliance & Accounting)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 12 | `companies_act_compliance.txt` | 4.2 KB | 4,287 | 公司合规、审计要求、年报截止日 | SSM |
| 13 | `accounting_mfrs_guide.txt` | 4.1 KB | 4,148 | MFRS/MPERS会计准则、审计要求 | MASB |
| 14 | `aml_compliance_guide.txt` | 2.8 KB | 2,889 | 反洗钱合规、CDD/EDD、STR | BNM |

### D. 资本市场 (Capital Markets)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 15 | `sc_capital_markets_guide.txt` | 5.5 KB | 5,590 | 证券委员会监管、资本市场法规 | SC |
| 16 | `bursa_listing_rules_guide.txt` | 5.7 KB | 5,818 | 交易所上市规则、IPO流程与披露要求 | Bursa Malaysia |

### E. 保险 (Insurance)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 17 | `insurance_guide.txt` | 6.2 KB | 6,319 | 保险与伊斯兰保险(Takaful)监管体系 | BNM, PIAM, PIDM |
| 18 | `islamic_finance_products_guide.txt` | 2.9 KB | 2,985 | 伊斯兰金融产品 | ISRA, BNM, SC |

### F. 社保 (Social Security)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 19 | `epf_socso_guide.txt` | 7.8 KB | ~7,800 | ✅ [扩充] EPF/SOCSO/EIS/HRDF/PCB/外劳税 — 完全重写 | EPF, SOCSO, HRD Corp, LHDN |

### G. 贸易促进 (Trade Promotion)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 20 | `matrade_trade_guide.txt` | 2.0 KB | 2,023 | MATRADE出口促进政策 | MATRADE |

### H. 上市公司与产业财税 (Listed Companies & Industry Tax)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 21 | `bursa_listed_companies_guide.txt` | 9.4 KB | 9,572 | ✅ Bursa上市公司、板块财务特征 | Bursa, SC |
| 22 | `state_tax_incentives_guide.txt` | 10.5 KB | 10,762 | ✅ 各州税收激励、经济走廊政策 | MIDA, IRDA |
| 23 | `oil_gas_palm_oil_guide.txt` | 8.8 KB | 9,026 | ✅ 石油/天然气/棕油产业财税 | PITA, MPOB |

### I. 大报告（权威数据源）

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 24 | `bnm_annual_report_2025.txt` | 501 KB | 513,366 | ⭐ BNM年报 — 货币政策、金融稳定、宏观展望 | BNM |
| 25 | `bnm_emr_2025.txt` | 261 KB | 266,953 | ⭐ BNM经济货币评论 — 行业增长、通胀、外部部门 | BNM |
| 26 | `mof_economic_2026.txt` | 702 KB | 718,825 | ⭐ MOF经济报告 — 2026预算案、财政政策 | MOF |
| 27 | `pwc_doing_business_2025.txt` | 150 KB | 153,845 | ⭐ PwC营商指南 | PwC |
| 28 | `ifsb_corporate_governance_2024.txt` | 234 KB | 239,962 | ⭐ IFSB伊斯兰金融治理 | IFSB |

### J. 新增补充 (New Supplements — v2.0, 2026-07-08)

| # | 文件 | 大小 | 字符数 | 主题 | 来源 |
|---|------|------|--------|------|------|
| 29 | `esg_sustainability_guide.txt` | ~9.0 KB | ~9,000 | ✅ ESG/可持续发展/绿色金融 — NSRF、Bursa ESG报告、SEDG、GTFS、碳税 | SC, Bursa, BNM, CMM |
| 30 | `sme_financing_grants_guide.txt` | ~10 KB | ~10,000 | ✅ 中小企业融资与政府补贴 — Budget 2026、GGSM2、CGC、TEKUN、数字转型、出口融资 | MOF, SME Corp, CGC, TEKUN, MATRADE |
| 31 | `fintech_digital_banking_guide.txt` | ~10 KB | ~10,000 | ✅ 金融科技与数字银行 — 数字银行监管、P2P、众筹、电子货币、数字资产、DITO | BNM, SC, PDPA |
| 32 | `cross_border_tax_guide.txt` | ~9.0 KB | ~9,000 | ✅ 跨境税务与国际税务 — DTA、BEPS、Pillar Two (QDMTT/IIR/UTPR)、CbCR、FTC、CFC | LHDN, OECD, KPMG |
| 33 | `real_estate_finance_tax_guide.txt` | ~8.5 KB | ~8,500 | ✅ 不动产与房地产金融 — RPGT详解、印花税、REITs、MFRS 15、发展商合规 | LHDN, SC, KPKT, JPPH |
| 34 | `manufacturing_tax_guide.txt` | ~9.5 KB | ~9,500 | ✅ 制造业财税激励 — NIF框架、NIA Scorecard、PS/ITA/RA、E&E、EV、航空医疗 | MIDA, MITI, PIA 1986 |
| 35 | `tech_digital_tax_guide.txt` | ~8.0 KB | ~8,000 | ✅ 科技/IT服务业财税 — MD Status、SaaS税、R&D双倍扣除、IP收益 | MDEC, MIDA, SC |
| 36 | `epf_socso_guide.txt` | 7.8 KB | ~7,800 | ✅ [扩充重写] 见F节 | EPF, SOCSO, HRD Corp |

### K. 新增补充 — 按领域划分的触发矩阵

| 触发主题 | 必须读取的文件 | 示例问题 |
|---------|--------------|---------|
| ESG/可持续发展 | `esg_sustainability_guide.txt` | NSRF何时全面合规？Bursa ESG报告2026年要求？ |
| 中小企业融资 | `sme_financing_grants_guide.txt` | CGC担保额度？TEKUN贷款上限？ |
| 金融科技/数字银行 | `fintech_digital_banking_guide.txt` | 数字银行牌照要求？P2P借贷投资上限？ |
| 跨境税务 | `cross_border_tax_guide.txt` | 马中DTA预扣税率？Pillar Two适用门槛？ |
| 房地产税务 | `real_estate_finance_tax_guide.txt` | REIT派息税务处理？RPGT第6年后税率？ |
| 制造业激励 | `manufacturing_tax_guide.txt` | NIF申请要求？E&E行业PS优惠？ |
| 科技/数字税收 | `tech_digital_tax_guide.txt` | MD Status申请流程？SaaS服务税税率？ |
| EPF/SOCSO | `epf_socso_guide.txt` | 外劳EPF费率？PCB截止日？ |

---

## 二、CSV_Datasets

| # | 文件 | 行数 | 大小 | 说明 |
|---|------|------|------|------|
| 1 | `bnm_opr_history.csv` | 12 | 271 B | BNM OPR历史(2023-2026) |
| 2 | `forex_rates_myr.csv` | 5 | 125 B | 5个主要币种汇率(当前) |
| 3 | `sst_rates.csv` | 11 | 293 B | SST税率分类 |
| 4 | `tax_rates.csv` | 15 | 581 B | 企业所得税/个人所得税率 |
| 5 | `historical_exchange_rates.csv` | 1,755 | 339 KB | MYR月度汇率(27种货币，多年度) |
| 6 | `historical_interest_rates.csv` | 5,712 | 229 KB | 商业银行/伊斯兰银行利率(多期限) |
| 7 | `gdp_annual.csv` | 157 | 6.9 KB | 年度名义GDP+GNI+人均(1947起) |
| 8 | `cpi_headline.csv` | 7,798 | 148 KB | 整体CPI月度指数(1980起) |
| 9 | `trade_headline.csv` | 743 | 56 KB | 贸易总量与余额 |
| 10 | `federal_finance_annual.csv` | 594 | 22 KB | 年度联邦财政收支(1970起) |
| 11 | `fuel_price_historical.csv` | 933 | 50 KB | 周度RON95/97/Diesel价格(2017起) |
| 12 | `monetary_aggregates.csv` | 1,896 | 75 KB | M1/M2/M3货币供应量 |

**CSV_Datasets 总计: 12个文件, ~19,633 行, ~928 KB**

---

## 三、DuckDB — malaysia_finance_tax.duckdb

数据库路径: `Databases/malaysia_finance_tax.duckdb`
大小: **12 MB** (从5.3MB导入宏观数据后)
引擎: DuckDB
数据来源: Risa (malaysia-company-search) DuckDB 桥接导入

### 表清单

#### A. 财税核心表 (10张, 120行)

| # | 表名 | 行数 | 主题 |
|---|------|------|------|
| 1 | `tax_rates` | 23 | 企业所得税/个人所得税率 |
| 2 | `sst_rates` | 15 | SST税率 |
| 3 | `bnm_opr_history` | 15 | OPR利率历史 |
| 4 | `forex_rates` | 10 | 当前汇率 |
| 5 | `tax_incentives` | 12 | 税务激励 |
| 6 | `withholding_tax` | 5 | 预扣税 |
| 7 | `compliance_deadlines` | 12 | 合规截止日 |
| 8 | `company_types` | 7 | 公司类型 |
| 9 | `personal_tax_reliefs` | 15 | 个人税务减免 |
| 10 | `bond_yields` | 6 | 债券收益率 |

#### B. 宏观经济表 (23张, 28,175行)

| # | 表名 | 行数 | 数据范围 | 说明 |
|---|------|------|---------|------|
| 11 | `macro_gdp_annual` | 157 | 1947-2026 | 年度名义GDP+GNI+人均 |
| 12 | `macro_gdp_annual_real` | 111 | 1970-2026 | 年度实际GDP+GNI+人均 |
| 13 | `macro_gdp_qtr` | 45 | 季度 | 实际GDP(季节调整) |
| 14 | `macro_gdp_state` | 1,904 | 州级 | 各州实际GDP(生产法) |
| 15 | `macro_cpi_headline` | 7,798 | 1980-2026 | 整体CPI月度指数 |
| 16 | `macro_cpi_core` | 1,414 | 2018-2026 | 核心CPI |
| 17 | `macro_cpi_annual` | 542 | 1960-2026 | 年度CPI |
| 18 | `macro_trade_headline` | 743 | 月度 | 贸易总量与余额 |
| 19 | `macro_interest_rates` | 5,712 | 月度 | 商业银行存款利率 |
| 20 | `macro_exchange_rates` | 1,755 | 月度 | MYR对27种货币汇率 |
| 21 | `macro_monetary_aggregates` | 1,896 | 月度 | M1/M2/M3货币供应 |
| 22 | `macro_federal_finance_qtr` | 1,243 | 季度 | 联邦财政收支明细 |
| 23 | `macro_federal_finance_year` | 594 | 1970-2026 | 联邦财政年度 |
| 24 | `macro_fuel_price` | 933 | 2017-2026 | 周度燃油价格 |
| 25 | `macro_economic_indicators` | 423 | 月度 | 经济先行/同步/滞后指标 |
| 26 | `macro_epf_dividend` | 74 | 1952-2026 | EPF公积金分红率 |
| 27 | `macro_fdi_flows` | 71 | 年度 | FDI流入/流出 |
| 28 | `macro_bop_balance` | 325 | 季度 | 国际收支平衡表 |
| 29 | `macro_ppi` | 575 | 月度 | PPI生产者价格指数 |
| 30 | `macro_iowrt` | 287 | 月度 | 批发零售销售指数 |
| 31 | `macro_payment_channels` | 430 | 月度 | 支付渠道交易 |
| 32 | `macro_currency_circulation` | 969 | 年度 | 流通货币(按面值) |
| 33 | `macro_state_gdp_lookup` | 174 | — | GDP编码对照表 |

---

## 四、数据覆盖缺口（v2.0 已全部修复）

所有此前识别的内容缺口已于 **2026-07-08 (v2.0)** 完成补充，新增8份参考文本：

| # | 主题 | 状态 | 文件 |
|---|------|------|------|
| 1 | ESG/可持续发展/绿色金融 | ✅ 已补 | `esg_sustainability_guide.txt` (~9KB) |
| 2 | 中小企业融资与政府补贴 | ✅ 已补 | `sme_financing_grants_guide.txt` (~10KB) |
| 3 | 金融科技与数字银行 | ✅ 已补 | `fintech_digital_banking_guide.txt` (~10KB) |
| 4 | 跨境税务与国际税务(DTA/Pillar Two) | ✅ 已补 | `cross_border_tax_guide.txt` (~9KB) |
| 5 | 不动产与房地产金融 | ✅ 已补 | `real_estate_finance_tax_guide.txt` (~8.5KB) |
| 6 | 制造业与NIF激励 | ✅ 已补 | `manufacturing_tax_guide.txt` (~9.5KB) |
| 7 | 科技/IT服务业税务(MD Status) | ✅ 已补 | `tech_digital_tax_guide.txt` (~8KB) |
| 8 | EPF/SOCSO/HRDF/PCB 重写扩充 | ✅ 已补 | `epf_socso_guide.txt` 重写为7.8KB |
| 9 | 银行体系指南扩充 | ✅ 已补 | `banking_system_guide.txt` 扩充为9.5KB |

### 数据时效性状态 (v2.0)

| 数据源 | 最新数据 | 频率 | 状态 |
|-------|---------|------|------|
| CPI (headline/core) | 2026年5月 | 月度 | ✅ |
| 汇率 (MYR) | 2026年3月 | 月度 | ✅ |
| 利率 | 2026年2月 | 月度 | ✅ |
| 燃油价格 | 2026年6月 | 周度 | ✅ 最新 |
| 贸易数据 | 2026年4月 | 月度 | ✅ |
| GDP (季度) | 2026 Q1 | 季度 | ✅ |
| FDI | 2025年7月 | 月度 | ⬜ 1年滞后 |
| 联邦财政 (季度) | 2024 Q1 | 季度 | ⬜ 待更新 |
| 州级GDP | 2023 | 年度 | ⬜ 2年滞后 |
| Reference_Texts | 2026 | 按需 | ✅ 已查新 |

---

## 五、数据源映射

| 官方机构 | 覆盖领域 | URL | 本地语料 |
|---------|---------|-----|---------|
| LHDN | 税务 | lhdn.gov.my | income_tax, sst_act, transfer_pricing, einvoice, rpgt, digital_tax |
| BNM | 银行/外汇/保险 | bnm.gov.my | bnm_fep, banking_system, insurance, bnm_annual, bnm_emr |
| MOF | 财政/预算 | treasury.gov.my | mof_economic |
| SSM | 公司注册 | ssm.com.my | companies_act, digital_tax (Part 2) |
| MIDA | 投资激励 | mida.gov.my | mida_incentives, regional_incentives, state_tax |
| SC | 证券监管 | sc.com.my | sc_capital_markets |
| Customs | 关税 | customs.gov.my | customs_tariff |
| Bursa | 上市规则 | bursamalaysia.com | bursa_listing_rules, bursa_listed_companies |
| MATRADE | 贸易促进 | matrade.gov.my | matrade_trade |
| EPF | 公积金 | epf.gov.my | epf_socso |
| SOCSO | 社保 | perkeso.gov.my | epf_socso |
| MASB | 会计准则 | masb.org.my | accounting_mfrs |
| PITA | 石油税 | — | oil_gas_palm_oil (Part 1) |
| MPOB | 棕油 | mpob.gov.my | oil_gas_palm_oil (Part 2) |
| IRDA/ECERDC/RECODA | 区域发展 | 各走廊机构 | state_tax_incentives |
| DOSM | 统计数据 | dosm.gov.my | 宏观DuckDB表 (桥接Risa) |
| data.gov.my | 开放数据 | data.gov.my | 宏观DuckDB表 (桥接Risa) |
