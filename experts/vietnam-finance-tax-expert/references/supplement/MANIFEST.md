# 越南财税金融专家包 · 短板补强总清单 (MANIFEST)

> 生成时间：2026-07-24
> 目的：将"税务以外财务/金融数据储备量"补强成果集中归档，便于一键迁移/恢复。
> 配套：realtime_sources.json（18个实时权威源）、README.md（使用与恢复说明）

## 一、8 大板块覆盖状态（最终验收）

| 板块 | 状态 | 累计补强语料 | 说明 |
|---|---|---|---|
| ① 税务核心 | 🔵 原强项 | 1 | 新《税收管理法》108/2025（2026-07-01生效） |
| ② 银行·外汇·金融科技 | 🟢 已补强 | 5 | DICA外汇 + 贸易融资 + 信用证实操 + **Decree 52/2024 非现金支付/电子钱包(新)** |
| ③ 投资·ODI·FDI·PPP | 🟢 已补强 | 2 | **PPP法64/2020 + Decree 243/2025(新)** + DICA(FDI开户) |
| ④ 会计·审计 | 🟢 已补强 | 2 | Circular 99/2025（2026-01-01生效） + **FDI强制审计2026实务** |
| ⑤ 社保·劳工 | 🟢 已补强 | 1 | 社保法2024 + 21.5%/10.5%费率 + 外籍30% |
| ⑥ 证券 | 🟢 已补强 | 1 | 证券法修订56/2024（2025-01-01生效） |
| ⑦ 反洗钱 AML | 🟢 已补强 | 1 | SBV Circular 27/2025（2025-11-01生效） |
| ⑧ 保险 | 🟢 已补强 | 3 | 强制险框架 + 工程一切险CAR + 保险法2022 |

> 另：转让定价(TP) 5 篇、贸易融资/银团 6 篇，跨板块计入②③④。

## 二、补充语料完整索引（22 篇，corpus_supplement/）

### 第一批（税务 + 实时样例）
1. `vn_taxadmin_law_108_2025_chinatax.txt` — 新《税收管理法》108/2025（电商/数字平台代扣代缴）
2. `vcb_fx_sample_2026-07-24.txt` — Vietcombank 实时牌价样例（时点快照，佐证实时链路）

### 第二批（非税六大领域）
3. `vn_insurance_law_2022_luatduongtri.txt` — 保险法2022 + 强制险议定
4. `vn_social_insurance_law_2024_rates_lawma.txt` — 社保法2024 + 费率规则
5. `vn_accounting_circular99_2025_parkerrussell.txt` — 会计通函99/2025（取代200/2014）
6. `vn_securities_law_56_2024_ssc.txt` — 证券法修订56/2024
7. `vn_aml_circular27_2025_allenandgledhill.txt` — 反洗钱 Circular 27/2025
8. `vn_banking_dica_forex_indochinalink.txt` — DICA资本账户/外汇合规

### 第三批（贸易融资/银团/商业保险非寿险）
9. `vn_trade_finance_boc_vietnam.txt` — 中行越南贸易融资产品清单
10. `vn_trade_finance_lc_operations_dewintech.txt` — 信用证L/C实操（UCP600/UPAS）
11. `vn_syndicated_loan_circular42_2011_luatvietnam.txt` — 银团贷款 Circular 42/2011
12. `vn_syndicated_loan_transfer_vtnpartners.txt` — 银团贷款转让实务
13. `vn_mandatory_insurance_russinvecchi.txt` — 强制保险框架（最低保额）
14. `vn_car_insurance_tokiomarine.txt` — 工程一切险CAR产品

### 第四批（转让定价 TP）
15. `vn_tp_decree132_2025_grantthornton.txt` — TP法规 Decree 132/2020 + 20/2025澄清
16. `vn_tp_compliance_2026_acclime.txt` — TP合规2026（APA/豁免/安全港）
17. `vn_tp_audit_trends_2025_deloitte.txt` — 2025 TP稽查趋势数据
18. `vn_tp_industry_risk_kelmer.txt` — TP行业风险与争议解决
19. `vn_tp_china_vietnam_treaty_article9_fsou.txt` — 中越协定第九条（联属企业）

### 第五批（最终补强：金融科技/PPP/审计）
20. `vn_fintech_decree52_2024_noncash_vietnambusinesslaw.txt` — 非现金支付法令52/2024（电子钱包/支付牌照）
21. `vn_ppp_law64_2020_decree243_2025_investtovietnam.txt` — PPP法64/2020 + Decree 243/2025
22. `vn_fdi_audit_compliance_2026_vietnambriefing.txt` — FDI强制审计2026实务

## 三、实时数据源（realtime_sources.json，18 源）

税务/海关/法规类（13）：SBV参考价、Vietcombank牌价、gdt税务总局、税路通、vbpl法理库、Lawnet、LuatVietnam、tariff.customs.gov.vn、VCCI关税、FIA外资局、MoF财政部、SSC证券委、Winmart/海关工具
非税金融类（5）：sbv_policy_rate（政策利率）、vcb_rates（存贷款基准利率）、vss_portal（社保局费率）、hose_hnx（证交所行情）、mof_insurance（保险监管）

## 四、入库与索引状态

- 工作区补充目录：`vietnam-finance-supplement/` —— 持久、不被专家包升级覆盖
- 专家包语料目录：`.../vietnam-finance-tax-expert/references/corpus/vietnam-finance-tax-corpus/`
- 索引：`build_index.py --force` 重建后约 **80,210+ 块 / 672 文件**，全部补充语料可语义检索命中
- 恢复步骤（专家包升级后）：将 `corpus_supplement/*.txt` 复制进语料目录 → 在隔离 venv 跑 `build_index.py --force`

## 五、诚实的残余真空（如实说明）

- 贸易融资/银团贷款/商业保险的具体**产品费率数字**：各行保密且常变，宜用实时源或持牌机构，不应由静态语料承载
- 实时汇率/利率/股价/保费行情：用时即查（realtime_sources.json），不入库堆积
