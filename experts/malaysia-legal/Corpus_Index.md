# 马来西亚法务法规专家 — 语料库索引

**生成时间**: 2026-07-06
**版本**: v1.0

## 目录结构

```
malaysia-legal/
├── Reference_Texts/         # 45 份法律/合规文献（纯文本，+3 新增/更新）
├── Databases/               # DuckDB 离线数据库（15 张表）
├── CSV_Datasets/            # 原始 CSV/JSON 数据
├── agents/                  # Agent MD 行为定义
├── skills/malaysia-legal/   # SKILL MD + 引擎脚本 + API 模块
└── .codebuddy-plugin/       # plugin.json 配置
```

## Reference_Texts 清单（45 份）

### 一、公司法与公司治理（3 份）

| 文件 | 说明 |
|------|------|
| `companies_act_2016.txt` | Companies Act 2016 (Act 777) 全文，577 页 |
| `mida_companies_act_2016_guide.txt` | MIDA 公司法改革要点指南 |
| `pwc_doing_business_2025.txt` | PwC 马来西亚营商环境指南 |

### 二、核心基础法条（6 份）

| 文件 | 说明 |
|------|------|
| `contracts_act_1950.txt` | Contracts Act 1950 (Act 136) — 合同法基础 |
| `evidence_act_1950.txt` | Evidence Act 1950 (Act 56) — 证据法 |
| `limitation_act_1953.txt` | Limitation Act 1953 (Act 254) — 诉讼时效 |
| `partnership_act_1961.txt` | Partnership Act 1961 (Act 135) — 合伙企业法 |
| `national_land_code_1965.txt` | National Land Code 1965 (Act 56) — 土地法 |
| `courts_of_judicature_act_1964.txt` | Courts of Judicature Act 1964 (Act 91) — 法院体系 |

### 三、仲裁与争议解决（1 份）

| 文件 | 说明 |
|------|------|
| `arbitration_act_2005.txt` | Arbitration Act 2005 (Act 646) — 仲裁法 |

### 四、数据保护与隐私（2 份）

| 文件 | 说明 |
|------|------|
| `pdpa_2010.txt` | Personal Data Protection Act 2010 (Act 709) |
| `pdpa_amendment_2024.txt` | **[新增]** PDPA 2024修正案（DPO/数据泄露通知/跨境传输/罚款上调） |

### 四B、医疗器械监管（1 份）**[新增]**

| 文件 | 说明 |
|------|------|
| `medical_device_act_2012.txt` | **[新增]** Medical Device Act 2012 (Act 737) — 4级分类/Establishment Licence/产品注册/CAB/GDPMD/罚款最高RM200k |

### 五、劳动法与雇佣法规（17 份）

| 文件 | 说明 |
|------|------|
| `employment_act_1955.txt` | Employment Act 1955 (Act 265) |
| `industrial_relations_act_1967.txt` | Industrial Relations Act 1967 |
| `osha_1994.txt` | Occupational Safety & Health Act 1994 |
| `trade_unions_act_1959.txt` | Trade Unions Act 1959 |
| `socso_act_1969.txt` | Employees' Social Security Act 1969 |
| `epf_act_1991.txt` | Employees Provident Fund Act 1991 |
| `eis_act_2017.txt` | Employment Insurance System Act 2017 |
| `anti_sexual_harassment_act_2022.txt` | Anti-Sexual Harassment Act 2022 |
| `children_young_persons_employment_act_1966.txt` | Children and Young Persons Employment Act |
| `minimum_retirement_age_act_2012.txt` | Minimum Retirement Age Act 2012 |
| `minimum_wages_order_2026.txt` | Minimum Wages Order 2026 |
| `workmen_compensation_act_1952.txt` | Workmen's Compensation Act 1952 |
| `private_employment_agencies_act_1981.txt` | Private Employment Agencies Act 1981 |
| `sabah_sarawak_labour_ordinance.txt` | Sabah & Sarawak Labour Ordinances |
| `hrdf_act_2001.txt` | HRDF Act 2001 |
| `act_446_workers_housing_1990.txt` | Workers' Minimum Standards Housing Act |
| `industrial_court_landmark_cases.txt` | 工业法庭重要判例 |

### 六、竞争法与合规（4 份）

| 文件 | 说明 |
|------|------|
| `unctad_model_law_competition.txt` | UNCTAD 竞争法范本 |
| `msci_esg_methodology.txt` | MSCI ESG 评级方法论 |
| `company_insurance_requirements_malaysia.txt` | 企业保险要求 |
| `business_premise_license_malaysia.txt` | 营业场所牌照要求 |

### 七、外劳与移民（2 份）

| 文件 | 说明 |
|------|------|
| `foreign_worker_levy_2026.txt` | 外劳人头税 2026 |
| `immigration_employment_pass_2026.txt` | 外籍员工工作准证 2026 **[含6月新规]** |

### 八、判例与司法实践（3 份）

| 文件 | 说明 |
|------|------|
| `industrial_court_landmark_cases.txt` | 工业法庭重要判例 |
| `hr_violations_cases.txt` | 劳动违规案例 |
| `domestic_inquiry_procedure.txt` | 内部调查程序 |

### 九、税务与财务合规（4 份）

| 文件 | 说明 |
|------|------|
| `lhdn_bik_public_ruling_2019.txt` | 雇员福利税务裁定 (BIK) |
| `mida_codb_2024.txt` | MIDA 建厂成本指南（含牌照费用） |
| `statutory_filing_calendar_malaysia.txt` | 法定申报日历 |
| `pcb_mtd_income_tax_2026.txt` | PCB/MTD 所得税指南 |

### 十、法律体系总览（1 份）

| 文件 | 说明 |
|------|------|
| `malaysia_legal_system_overview.txt` | 马来西亚法律体系总览（法院层级、双轨制、引用格式等） |

### 十一、人力资源实务（6 份）

| 文件 | 说明 |
|------|------|
| `employee_handbook_essentials.txt` | 员工手册必备条款 |
| `retrenchment_termination_guide.txt` | 裁员与解雇指南 |
| `office_leasing_guide_malaysia.txt` | 办公室租赁指南 |
| `attendance_leave_management_malaysia.txt` | 出勤与休假管理 |
| `performance_discipline_malaysia.txt` | 绩效与纪律管理 |
| `flexible_working_arrangements_guidelines.txt` | 弹性工作安排 |

### 十二、其他指南（8 份）

| 文件 | 说明 |
|------|------|
| `business_travel_expense_policy_malaysia.txt` | 商务差旅政策 |
| `payroll_compliance_checklist.txt` | 薪资合规清单 |
| `admin_procurement_sop_malaysia.txt` | 行政采购标准作业程序 |
| `malaysia_labor_market_intelligence.txt` | 马来西亚劳动力市场情报 |
| `malaysia_workforce_profile.txt` | 马来西亚劳动力概况 |
| `malaysia_workplace_culture_islamic.txt` | 马来西亚职场文化与伊斯兰原则 |
| `employee_benefits_benchmark_malaysia.txt` | 员工福利对标 |
| `malaysia_salary_guide_2026.txt` | 马来西亚薪资指南 2026 |

## DuckDB 数据库（15 张表）

| 表名 | 行数 | 说明 |
|------|------|------|
| `pharmaceutical_manufacturers` | 283 | 获批药品制造商 |
| `pharmaceutical_importers` | 461 | 获批药品进口商 |
| `pharmaceutical_wholesalers` | 974 | 获批药品批发商 |
| `pharmaceutical_products` | 28,097 | 获批药品清单 |
| `pharmaceutical_products_cancelled` | 1,587 | 被取消注册药品 |
| `cosmetics_manufacturers` | 617 | 获批化妆品制造商 |
| `cosmetic_notifications` | 240,854 | 已通报化妆品 |
| `cosmetic_notifications_cancelled` | 121 | 被取消通报化妆品 |
| `legal_advisory_services` | 250,000 | 法律咨询服务记录 |
| `legal_advisory_category` | 2,832 | 法律咨询分类统计 |
| `legal_advisory_subcategory` | 6,322 | 法律咨询子类统计 |
| `legal_advisory_branch` | 1,105 | 分支机构服务统计 |
| `crime_district` | 40,000 | 按地区犯罪数据 |
| `prisoners_state` | 234 | 各州囚犯数据 |
| `prisoners_prison` | 648 | 各监狱囚犯数据 |

**总计**: 574,135 行 / 18.5 MB

## API 模块

| 模块 | 说明 |
|------|------|
| `api_modules/ssm_einfo_module.md` | SSM 公司注册查询指南 |
| `api_modules/ekehakiman_module.md` | e-Kehakiman 诉讼查询指南 |
| `api_modules/myipo_scraper.py` | MyIPO 商标/专利查询脚本 |

## 数据源（site: 搜索目标）

| 数据源 | 站点 | 用途 |
|--------|------|------|
| SSM e-Info | site:ssm.com.my | 公司注册信息 |
| e-Kehakiman | site:ehakiman.kehakiman.gov.my | 诉讼/清盘查询 |
| MyIPO | site:myipo.gov.my | 商标/专利查询 |
| PDPA | site:pdp.gov.my | 数据保护合规 |
| LHDN | site:lhdn.gov.my | 税务合规 |
| MOF | site:mof.gov.my | 政府招标 |
| Customs | site:customs.gov.my | 海关/关税 |
| JAKIM Halal | site:halal.gov.my | 清真认证 |
| CIDB | site:cidb.gov.my | 建筑承包商 |
| MCMC | site:mcmc.gov.my | 通信牌照 |
| ST Energy | site:st.gov.my | 能源许可 |
