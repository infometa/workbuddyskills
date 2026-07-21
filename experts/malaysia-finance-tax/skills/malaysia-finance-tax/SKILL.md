---
name: malaysia-finance-tax
description: Malaysia Finance & Tax intelligence skill — covering taxation, banking, financing, forex, auditing, subsidies, insurance and financial compliance data retrieval and analysis for businesses in Malaysia.
agent_created: true
---

# Malaysia Finance & Tax Skill



## 📊 语料库统计

### Reference_Texts — 56 份，~17 MB，~16.8M 字符（v2.1 新增20份法律全文+激励指南）

| 文件 | 字符数 | 大小 | 用途 |
|------|--------|------|------|
| `income_tax_guide.txt` | 5,920 | 5.8 KB | 企业所得税/个人所得税税率、优惠、预扣税 |
| `income_tax_act_1967.txt` | 1,095,103 | 1,069 KB | ⭐ Income Tax Act 1967 (Act 53) 全文 — 企业所得税/预扣税/资本津贴/税收优惠 |
| `sst_act_2018_guide.txt` | 6,015 | 5.9 KB | 销售与服务税(SST)税率、注册门槛、申报 |
| `sales_tax_act_2018.txt` | 141,725 | 138 KB | ⭐ Sales Tax Act 2018 (Act 806) 全文 — SST销售税体系/纳税义务/免税 |
| `service_tax_act_2018.txt` | 117,886 | 115 KB | ⭐ Service Tax Act 2018 (Act 807) 全文 — SST服务税/数字服务税/申报 |
| `bnm_fep_guide.txt` | 4,570 | 4.5 KB | BNM 外汇政策(FEP)、非居民/居民规则 |
| `mida_incentives_guide.txt` | 4,213 | 4.1 KB | MIDA 投资激励 (PS/ITA/RA) |
| `mida_codb_2024.txt` | 107,476 | 105 KB | ⭐ MIDA经商成本2024 — 人工/水电/工业用地/租金/激励总览 |
| `miti_services_incentives.txt` | 14,204 | 14 KB | ⭐ MITI服务业激励 — 教育/医疗/物流/ICT的PS/ITA/RA |
| `companies_act_compliance.txt` | 4,287 | 4.2 KB | 公司合规、审计要求、年报截止日 |
| `companies_act_2016.txt` | 976,215 | 953 KB | ⭐ Companies Act 2016 (Act 777) 全文 — 公司注册/董事/股东/分红/清算 |
| `accounting_mfrs_guide.txt` | 4,148 | 4.1 KB | MFRS/MPERS会计准则、审计要求 |
| `aml_compliance_guide.txt` | 2,889 | 2.8 KB | 反洗钱合规、CDD/EDD、STR |
| `amlatfpuaa_2001.txt` | 244,871 | 239 KB | ⭐ AMLATFPUAA 2001 (Act 613) 全文 — 反洗钱/反恐融资/STR/CDD |
| `macc_act_2009.txt` | 122,164 | 119 KB | ⭐ MACC Act 2009 (Act 694) 全文 — 反贿赂/反腐败委员会/企业合规 |
| `banking_system_guide.txt` | ~9,500 | 9.5 KB | ✅ [扩充] 银行体系、支付系统、利率、数字银行、Basel III |
| `epf_socso_guide.txt` | ~7,800 | 7.8 KB | ✅ [扩充] EPF/SOCSO/EIS/HRDF/PCB/外劳税 |
| `employment_act_1955.txt` | 173,006 | 169 KB | ⭐ Employment Act 1955 (Act 265) 全文 — 雇佣/工资/加班/解雇/外劳 |
| `customs_tariff_guide.txt` | 6,039 | 5.9 KB | 海关关税、HS编码、进出口税费 |
| `sc_capital_markets_guide.txt` | 5,590 | 5.5 KB | 证券委员会监管、资本市场法规 |
| `bursa_listing_rules_guide.txt` | 5,818 | 5.7 KB | 交易所上市规则、IPO流程与披露要求 |
| `capital_markets_services_act_2007.txt` | 914,715 | 893 KB | ⭐ CMSA 2007 (Act 671) 全文 — 证券/期货/基金/上市规则/SC监管 |
| `insurance_guide.txt` | 6,319 | 6.2 KB | 保险与伊斯兰保险(Takaful)监管体系 |
| `pidm_act_2011.txt` | 389,413 | 380 KB | ⭐ PIDM Act 2011 (Act 735) 全文 — 存款保险/RM250K保障/Takaful保障基金 |
| `matrade_trade_guide.txt` | 2,023 | 2.0 KB | 对外贸易发展局与出口促进政策 |
| `regional_incentives_guide.txt` | 2,478 | 2.4 KB | 区域投资激励(Iskandar/ECER/Sabah/Sarawak) |
| `islamic_finance_products_guide.txt` | 2,985 | 2.9 KB | 伊斯兰金融产品(Murabahah/Musharakah/Ijarah等) |
| `islamic_financial_services_act_2013.txt` | 492,053 | 480 KB | ⭐ IFSA 2013 (Act 759) 全文 — 伊斯兰银行/Takaful/Shariah治理 |
| `transfer_pricing_guide.txt` | 6,399 | 6.3 KB | 转让定价(TP)规则、文档要求、APA |
| `einvoice_guide.txt` | 6,013 | 5.9 KB | LHDN电子发票(e-Invoice)分阶段实施 |
| `rpgt_guide.txt` | 5,680 | 5.6 KB | 房产盈利税(RPGT)税率、豁免、计算 |
| `rpgt_act_1976.txt` | 142,731 | 139 KB | ⭐ RPGT Act 1976 (Act 169) 全文 — 房产盈利税征收/处置定义/税率阶梯/豁免 |
| `stamp_act_1949.txt` | 148,901 | 145 KB | ⭐ Stamp Act 1949 (Act 378) 全文 — 印花税征收/税率结构/股份转让/豁免 |
| `digital_tax_ssm_guide.txt` | 10,262 | 10.0 KB | 数字经济税(SST) + SSM公司注册流程 |
| `bursa_listed_companies_guide.txt` | 9,572 | 9.4 KB | Bursa上市公司数据、财务指标、板块分析 |
| `state_tax_incentives_guide.txt` | 10,762 | 10.5 KB | 各州差异化税收与区域发展走廊激励 |
| `mida_jssez_snapshot.txt` | 10,019 | 10 KB | ⭐ JS-SEZ激励概览 — 柔佛-新加坡经济特区税收优惠/行业重点 |
| `oil_gas_palm_oil_guide.txt` | 9,026 | 8.8 KB | 石油/天然气/棕油产业财税全指南 |
| `bnm_annual_report_2025.txt` | 513,366 | 501 KB | ⭐ BNM年报 — 货币政策、金融稳定、宏观展望 |
| `bnm_emr_2025.txt` | 266,953 | 261 KB | ⭐ BNM经济货币评论 — 行业增长、通胀、外部部门 |
| `mof_economic_2026.txt` | 718,825 | 702 KB | ⭐ MOF经济报告 — 2026预算案、财政政策、行业预期 |
| `pwc_doing_business_2025.txt` | 153,845 | 150 KB | ⭐ PwC营商指南 — 税务体系、外资准入、公司设立总览 |
| `ifsb_corporate_governance_2024.txt` | 239,962 | 234 KB | ⭐ IFSB伊斯兰金融治理 — Shariah合规框架 |
| `esg_sustainability_guide.txt` | ~9,000 | ~9 KB | ✅ ESG/可持续/绿色金融 — NSRF、Bursa ESG、碳税 |
| `mida_green_tech_incentive_2024.txt` | 19,030 | 19 KB | ⭐ MIDA绿色科技激励(GTI)2024 — 绿色资产/可再生能源税收优惠 |
| `mida_diaf_esg_guideline.txt` | 16,065 | 16 KB | ⭐ DIAF-ESG基金指南 — ESG转型补贴/国内投资加速/合格项目 |
| `exchange_control_act_1953.txt` | 166,034 | 162 KB | ⭐ Exchange Control Act 1953 (Act 17) 全文 — 外汇管制框架[已废止2013] |
| `financial_services_act_2013.txt` | 463,073 | 452 KB | ⭐ FSA 2013 (Act 758) 全文 — 银行/保险/支付系统/BNM监管 |
| `sme_financing_grants_guide.txt` | ~10,000 | ~10 KB | ✅ 中小企业融资 — Budget 2026、CGC、TEKUN |
| `fintech_digital_banking_guide.txt` | ~10,000 | ~10 KB | ✅ 金融科技/数字银行 — 数字银行监管、P2P |
| `cross_border_tax_guide.txt` | ~9,000 | ~9 KB | ✅ 跨境税务 — DTA、Pillar Two、BEPS |
| `real_estate_finance_tax_guide.txt` | ~8,500 | ~8.5 KB | ✅ 不动产/金融 — RPGT、REIT、MFRS 15 |
| `manufacturing_tax_guide.txt` | ~9,500 | ~9.5 KB | ✅ 制造业激励 — NIF、PS/ITA/RA、E&E |
| `mida_pipc_manufacturing.txt` | 21,191 | 21 KB | ⭐ PIPC制造业激励指南 — 高价值产品/PS/ITA/NIMP 2030配套 |
| `tech_digital_tax_guide.txt` | ~8,000 | ~8 KB | ✅ 科技/IT业 — MD Status、SaaS、R&D |

### DuckDB — 33 张表，28,295 行，12 MB

| 表名 | 行数 | 内容 |
|------|------|------|
| `tax_rates` | 23 | 企业所得税(15-24%)、个人所得税(0-30%)、CGT/RPGT |
| `sst_rates` | 15 | 销售税(0/5/10%)、服务税(6/8%)、SToDS |
| `bnm_opr_history` | 15 | BNM OPR 历史(2023-2026) |
| `forex_rates` | 10 | MYR 对 USD/EUR/SGD/CNY 等汇率 |
| `tax_incentives` | 12 | Pioneer Status、ITA、RA、GITA、BioNexus 等 |
| `withholding_tax` | 5 | 利息/特许权/技术费预扣税(5-15%) |
| `compliance_deadlines` | 12 | SSM/LHDN/EPF/SOCSO 截止日及罚则 |
| `company_types` | 7 | Sdn Bhd、Bhd、LLP、Branch 等 |
| `personal_tax_reliefs` | 15 | 个人减免(RM1k-RM10k)、EPF、保险等 |
| `bond_yields` | 6 | MGS 3yr-20yr 收益率、OPR |
| `macro_gdp_annual` | 157 | 年度名义GDP+GNI+人均 (1947起) |
| `macro_gdp_annual_real` | 111 | 年度实际GDP+GNI+人均 |
| `macro_gdp_qtr` | 45 | 季度实际GDP(季节调整) |
| `macro_gdp_state` | 1,904 | 州级实际GDP(生产法) |
| `macro_cpi_headline` | 7,798 | 整体CPI月度指数(1980起) |
| `macro_cpi_core` | 1,414 | 核心CPI(2018起) |
| `macro_cpi_annual` | 542 | 年度CPI(1960起) |
| `macro_trade_headline` | 743 | 贸易总量与余额 |
| `macro_interest_rates` | 5,712 | 商业银行/伊斯兰银行存款利率 |
| `macro_exchange_rates` | 1,755 | MYR月度汇率(27种货币) |
| `macro_monetary_aggregates` | 1,896 | M1/M2/M3货币供应量 |
| `macro_federal_finance_qtr` | 1,243 | 季度联邦财政收支 |
| `macro_federal_finance_year` | 594 | 年度联邦财政收支(1970起) |
| `macro_fuel_price` | 933 | 周度RON95/97/Diesel价格 |
| `macro_economic_indicators` | 423 | 先行/同步/滞后经济指标 |
| `macro_epf_dividend` | 74 | 公积金dividend(1952起) |
| `macro_fdi_flows` | 71 | FDI流入/流出量 |
| `macro_bop_balance` | 325 | 国际收支平衡表 |
| `macro_ppi` | 575 | PPI生产者价格指数 |
| `macro_iowrt` | 287 | 批发零售月度销售指数 |
| `macro_payment_channels` | 430 | 支付渠道交易数据 |
| `macro_currency_circulation` | 969 | 流通货币(年度，按面值) |
| `macro_state_gdp_lookup` | 174 | GDP编码对照表 |

### 数据时效性

| 数据源 | 更新频率 | 典型滞后 | 注意事项 |
|--------|---------|---------|---------|
| DuckDB | 季度/年度 | 3-12 个月 | 参考各表注释 |
| Reference_Texts 税务 | 年度 | 0-6 个月 | Budget 发布后更新 |
| Reference_Texts 政策 | 发布后 | 0-3 个月 | 关注 LHDN/BNM/MIDA 官网 |
| Reference_Texts 新增(v2.0) | 2026-07 | 0-3 个月 | ESG/SME/FinTech以Budget 2026为准 |
| site 定向搜索 | 按需 | 实时 | 首选出处 |

---

## 🚨 语料库优先原则

任何回答必须优先从本地语料库提取信息。优先级：
1. Reference_Texts (.txt)
2. DuckDB (.duckdb)
3. CSV_Datasets (.csv)
4. 官方 API (data.gov.my)
5. site:xxx 定向搜索
6. **fetch_with_fallback 在线抓取** — 四层降级兜底（直连→Google缓存→CORS网关→免费代理），当 site:xxx 和通用搜索均无法获取目标页面内容时触发
7. 通用 WebSearch

## 触发主题 — 强制读取表

| 触发主题 | 必须读取的文件 | 必须查询的库表 | 示例问题 |
|---------|--------------|---------------|---------|
| 企业所得税 | `income_tax_guide.txt` | `tax_rates` | 马来西亚Sdn Bhd所得税税率？ |
| SST 税率 | `sst_act_2018_guide.txt` | `sst_rates` | 服务税有哪些类别？ |
| 关税/进出口 | `customs_tariff_guide.txt` | — | 电子产品进口关税税率？ |
| 外汇管制 | `bnm_fep_guide.txt` | — | 外资汇出利润的限制？ |
| 公司合规 | `companies_act_compliance.txt` | `compliance_deadlines` | SSM年报提交截止日期？ |
| 投资激励 | `mida_incentives_guide.txt` | `tax_incentives` | Pioneer Status申请条件？ |
| 区域投资激励 | `regional_incentives_guide.txt` | — | ECER区域有哪些税收优惠？ |
| 会计准则 | `accounting_mfrs_guide.txt` | — | MFRS 9 核心要求？ |
| 银行利率 | `banking_system_guide.txt` | `bnm_opr_history`, `bond_yields` | 当前OPR是多少？ |
| 个人税收 | `income_tax_guide.txt` | `personal_tax_reliefs` | 个人所得税减免项目？ |
| 社会保险 | `epf_socso_guide.txt` | — | EPF缴纳比例？ |
| 反洗钱 | `aml_compliance_guide.txt` | — | AML报告义务？ |
| 资本市场 | `sc_capital_markets_guide.txt` | — | CMSA对基金管理人的要求？ |
| 上市规则 | `bursa_listing_rules_guide.txt` | — | 创业板转主板的条件？ |
| 保险/Takaful | `insurance_guide.txt` | — | 外资保险公司的设立要求？ |
| 贸易促进/出口 | `matrade_trade_guide.txt` | — | MATRADE为出口商提供什么支持？ |
| 伊斯兰金融 | `ifsb_corporate_governance_2024.txt`, `islamic_finance_products_guide.txt` | — | 伊斯兰金融的Shariah治理要求？ |
| 转让定价 | `transfer_pricing_guide.txt` | — | 关联交易转让定价文档要求？ |
| 电子发票 | `einvoice_guide.txt` | — | 电子发票分阶段实施时间表？ |
| RPGT/房产盈利税 | `rpgt_guide.txt` | — | 外国人出售马来西亚房产的RPGT？ |
| 数字经济税 | `digital_tax_ssm_guide.txt` | — | 外国数字服务提供商SST注册要求？ |
| SSM公司注册 | `digital_tax_ssm_guide.txt` | `company_types` | 外资在马来西亚设立Sdn Bhd的流程和成本？ |
| Bursa上市公司 | `bursa_listed_companies_guide.txt` | — | KLCI成分股有哪些？金融板块平均PE？ |
| 各州税收激励 | `state_tax_incentives_guide.txt` | — | JS-SEZ有什么税收优惠？ |
| 油气财税 | `oil_gas_palm_oil_guide.txt` | — | PITA税率多少？PSC成本油上限？ |
| 棕油产业税 | `oil_gas_palm_oil_guide.txt` | — | CPO暴利税什么时候触发？ |
| 汇率 | — | `forex_rates` | 马币兑美元汇率？ |
| 货币政策/金融稳定 | `bnm_annual_report_2025.txt` | `bnm_opr_history` | BNM 2025年货币政策走向？ |
| 宏观经济展望 | `bnm_emr_2025.txt`, `mof_economic_2026.txt` | — | 2026年马来西亚GDP增长预测？ |
| 财政预算/财政政策 | `mof_economic_2026.txt` | — | 2026年财政赤字目标？ |
| 营商体系/外资准入 | `pwc_doing_business_2025.txt` | `company_types` | 外资在马来西亚设立公司的形式？ |
| ESG/可持续发展 | `esg_sustainability_guide.txt` | — | NSRF 2026年合规要求？Bursa ESG报告期限？ |
| 中小企业融资 | `sme_financing_grants_guide.txt` | — | CGC担保额度上限？Budget 2026 SME补贴？ |
| 数字银行/金融科技 | `fintech_digital_banking_guide.txt` | — | 数字银行牌照申请条件？P2P借贷上限？ |
| 跨境税务/DTA | `cross_border_tax_guide.txt` | — | 马中DTA股息预扣税率？Pillar Two门槛？ |
| 不动产/房地产税务 | `real_estate_finance_tax_guide.txt` | — | REIT派息税务处理？RPGT第6年后税率？ |
| 制造业激励/NIF | `manufacturing_tax_guide.txt` | `tax_incentives` | NIF申请流程？E&E行业激励措施？ |
| 科技/IT税务 | `tech_digital_tax_guide.txt` | — | MD Status申请条件？SaaS服务税税率？ |
| 所得税法全文 | `income_tax_act_1967.txt` | `tax_rates` | Income Tax Act 1967对企业所得税第7条的具体规定？ |
| Sales Tax / Service Tax 全文 | `sales_tax_act_2018.txt`, `service_tax_act_2018.txt` | `sst_rates` | Sales Tax Act 2018对进口商品销售税的规定？ |
| FSA 银行/保险监管 | `financial_services_act_2013.txt` | — | FSA 2013对银行牌照和BNM监管权力的规定？ |
| IFSA 伊斯兰金融监管 | `islamic_financial_services_act_2013.txt` | — | IFSA 2013对伊斯兰银行Shariah治理的要求？ |
| CMSA 资本市场法 | `capital_markets_services_act_2007.txt` | — | CMSA 2007对证券经纪商牌照管理的条款？ |
| AMLATFPUAA 反洗钱法 | `amlatfpuaa_2001.txt` | — | AMLATFPUAA对洗钱罪处罚金额和刑期的规定？ |
| 外汇管制法 | `exchange_control_act_1953.txt` | — | Exchange Control Act 1953是否仍然有效（已废止）？ |
| Companies Act 2016 公司法全文 | `companies_act_2016.txt` | `compliance_deadlines` | Companies Act 2016对公司分红和减资的条款？ |
| Employment Act 1955 劳动法全文 | `employment_act_1955.txt` | — | Employment Act 1955对加班费和离职补偿的规定？ |
| MACC Act 2009 反贿赂法 | `macc_act_2009.txt` | — | MACC Act 2009对商业行贿的处罚规定？ |
| Stamp Act 1949 印花税法 | `stamp_act_1949.txt` | — | Stamp Act 1949对股份转让的印花税率？ |
| RPGT Act 1976 房产盈利税法 | `rpgt_act_1976.txt` | — | RPGT Act 1976对第5年内处置房产的税率？ |
| MIDA经商成本 | `mida_codb_2024.txt` | — | 马来西亚制造业工人最低工资和加班费率？ |
| 服务业激励 | `miti_services_incentives.txt` | — | MITI服务业有哪些PS/ITA激励？ |
| 绿色科技激励 | `mida_green_tech_incentive_2024.txt` | — | GTI绿色科技激励申请条件？ |
| JS-SEZ特区激励 | `mida_jssez_snapshot.txt` | — | 柔佛-新加坡经济特区企业所得税优惠？ |
| PIPC制造业激励 | `mida_pipc_manufacturing.txt` | — | PIPC制造业激励中PS和ITA选择条件？ |
| DIAF-ESG转型基金 | `mida_diaf_esg_guideline.txt` | — | 企业ESG转型补贴申请条件？ |
| PIDM存款保险 | `pidm_act_2011.txt` | — | PIDM存款保障额度是多少？银行倒闭如何赔付？ |

## 数据源定向触发矩阵

| 查询类型 | 优先数据源 | 搜索指令 | 备用数据源 |
|---------|----------|---------|----------|
| 税务税率 | LHDN | site:lhdn.gov.my | MOF, PwC Tax Summaries |
| 外汇政策 | BNM | site:bnm.gov.my | RHB/银行汇率 |
| 公司注册 | SSM | site:ssm.com.my | data.gov.my |
| 投资激励 | MIDA | site:mida.gov.my | LHDN, MATRADE |
| 证券法规 | SC | site:sc.com.my | Bursa Malaysia |
| 关税查询 | Customs | site:customs.gov.my | MITI |
| 财政预算 | MOF | site:treasury.gov.my | BNM, DOSM |
| 上市规则 | Bursa | site:bursamalaysia.com | SC |
| 统计数据 | data.gov.my | site:data.gov.my | DOSM, BNM |
| 银行利率 | BNM | site:bnm.gov.my | 各商业银行官网 |
| AML法规 | BNM | site:amlcft.bnm.gov.my | FATF |
| 会计准则 | MASB | site:masb.org.my | IFRS Foundation |
| 贸易促进 | MATRADE | site:matrade.gov.my | MITI |
| 保险监管 | BNM | site:bnm.gov.my (Insurance & Takaful) | PIDM, PIAM |
| ESG/可持续 | Bursa | site:bursamalaysia.com (Sustainability) | SC, CMM |
| 碳税/绿色 | MGTC | site:mgtc.gov.my | BNM, SC |
| 数字银行 | BNM | site:bnm.gov.my | SC Digital |
| 科技/数字 | MDEC | site:mdec.my | MIDA, SC |
| SME融资 | SME Corp | site:smecorp.gov.my | CGC, TEKUN |

## 脚本工具

skill 脚本位于 `scripts/`：
- `duckdb_query.py` — DuckDB SQL 查询引擎 (--list-tables, --schema, --sql, --search, --sample)
- `ref_text_search.py` — Reference_Texts 关键词/正则搜索 (--keyword, --regex, --list-files)
- `data_verifier.py` — 反幻觉防火墙，验证数据点是否存在于语料库

---

## 结构化引用格式

```
---
📚 来源引用：
1. [A/Reference_Texts] {file} — {section}
2. [B/site:{site}] {fact} — {url}

📊 来源占比：语料库 XX% | 定向搜索 XX% | 通用搜索 XX% | 推理 XX%
```

## 输出模式

- `详细模式` / `verbose` → 展开完整分析
- `简洁模式` / `concise` → 3-5 条核心结论
- `语料库测试` / `corpus test` → 每条数据标注来源

## 不确定性

- 非官方/单一来源必须标注 `⚠️ 不确定性`
- 禁止绝对化表述