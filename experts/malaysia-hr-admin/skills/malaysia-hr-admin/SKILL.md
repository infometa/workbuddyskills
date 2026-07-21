---
name: malaysia-hr-admin
description: 马来西亚人力行政语料库引擎 — 52 份 Reference_Texts + 77 张 DuckDB HR 子集表 + 7 数据源定向触发矩阵
agent_created: false
---

# Malaysia HR & Admin Corpus Engine

## 🔧 环境依赖 (Environment Setup)

**Python 依赖**：`duckdb` —— 脚本首次运行时会自动检测并安装（通过 `pip install duckdb`），无需手动操作。

如果自动安装失败（网络问题/权限不足），手动执行：
```bash
pip install -r requirements.txt
```

## 📁 目录结构与路径解析 (Directory Structure & Path Resolution)

安装后的标准目录结构：
```
malaysia-hr-admin/                 ← 插件根目录（任何位置均可）
├── .codebuddy-plugin/plugin.json
├── agents/malaysia-hr-admin.md
├── skills/malaysia-hr-admin/SKILL.md   ← 本文件
├── Reference_Texts/              ← 52 份 .txt 语料（~3.8MB）
│   ├── employment_act_1955.txt
│   ├── companies_act_2016.txt
│   └── ... (共 52 份)
├── Databases/
│   └── hr.duckdb                ← DuckDB 数据库（77 表，~24MB）
├── scripts/
│   ├── duckdb_query.py          ← SQL 查询引擎
│   ├── ref_text_search.py       ← 语料全文检索
│   ├── data_verifier.py         ← 数据完整性验证
│   └── pressure_test.py         ← 压力测试
├── avatars/expert.png
└── requirements.txt             ← pip 依赖（仅 duckdb>=0.9.0）
```

### 路径解析机制

所有 Python 脚本使用**相对于脚本位置的路径解析**，自动定位插件根目录：

```python
# scripts/duckdb_query.py 中的核心逻辑
PLUGIN_ROOT = Path(__file__).resolve().parent.parent  # scripts/ → 插件根目录
DB_PATH = PLUGIN_ROOT / "Databases" / "hr.duckdb"
CORPUS_PATH = PLUGIN_ROOT / "Reference_Texts"
```

**关键保证**：只要 `Databases/`、`Reference_Texts/`、`scripts/` 三个目录的相对位置不变，插件在任何路径下均可正常运行——无论是默认插件目录还是用户自定义位置。

### 运行前提清单

- [x] Python 3.8+ 已安装（脚本会自动检测）
- [x] `duckdb` 包可安装（自动 pip install，失败时需手动 `pip install -r requirements.txt`）
- [x] `Databases/hr.duckdb` 文件存在且完整（24MB，首次解压时确认）
- [x] `Reference_Texts/` 目录下有 .txt 文件（至少 40+ 份）
- [ ] 无需网络即可运行核心功能（语料库 + DuckDB 均为离线数据）

---

## 📊 语料库统计 (验证时间: 2026-07-02)

### Reference_Texts — 52 份，3,800+ KB，3,600,000+ 字符

| 文件 | 字符数 | 行数 | 用途 |
|------|--------|------|------|
| companies_act_2016.txt | 976,215 | 20,857 | 公司法全文 |
| mof_economic_2026.txt | 706,337 | 10,736 | 2026 财政预算案 |
| bnm_annual_report_2025.txt | 501,774 | 8,934 | 央行经济与货币政策年报 |
| kri_state_of_households_2024.txt | 430,042 | 7,914 | 家庭收入/不平等/消费 |
| employment_act_1955.txt | 187,903 | 4,377 | 劳动法全文 |
| pwc_doing_business_2025.txt | 150,533 | 2,640 | 营商环境与公司设立 |
| pdpa_2010.txt | 149,841 | 3,326 | 个人数据保护法 |
| msci_esg_methodology.txt | 117,227 | 2,025 | ESG 评级方法论 |
| mida_codb_2024.txt | 107,476 | 2,368 | 经商成本与人工标准 |
| mida_companies_act_2016_guide.txt | 16,413 | 271 | 公司法官方指南 |
| hiring_budget_planner_2026.txt | ~8,000 | ~200 | 招聘预算与人才成本规划 |
| hr_violations_cases.txt | ~8,000 | ~200 | HR 合规违规案例集 |
| industrial_relations_act_1967.txt | 7,870 | 175 | 劳资关系法 |
| domestic_inquiry_procedure.txt | 7,439 | 166 | 国内调查操作手册 |
| trade_unions_act_1959.txt | 7,071 | 157 | 工会法 |
| hr_practice_templates.txt | ~6,500 | ~180 | 合同/信函/Onboarding 模板 |
| retrenchment_termination_guide.txt | 6,248 | 148 | 裁员与解雇指南 |
| flexible_working_arrangements_guidelines.txt | 5,594 | 128 | 弹性工作制指南 |
| industrial_court_landmark_cases.txt | 5,547 | 106 | 劳工法庭判例汇编 |
| osha_1994.txt | 5,323 | 118 | 职业安全与健康法 |
| lhdn_bik_public_ruling_2019.txt | 5,028 | 120 | BIK 税务裁定 |
| children_young_persons_employment_act_1966.txt | 4,994 | 106 | 童工与青年工法 |
| act_446_workers_housing_1990.txt | 4,983 | 130 | 外劳宿舍标准法 |
| employee_handbook_essentials.txt | 4,971 | 146 | 员工手册要素 |
| immigration_employment_pass_2026.txt | 4,968 | 116 | 工作准证与移民 |
| hrdf_act_2001.txt | 4,945 | 118 | 人力资源发展基金 |
| socso_act_1969.txt | 4,893 | 102 | 社险法 |
| eis_act_2017.txt | 4,660 | 120 | 就业保险法 |
| pcb_mtd_income_tax_2026.txt | 4,653 | 106 | PCB/MTD 薪资扣税 |
| private_employment_agencies_act_1981.txt | 4,754 | 111 | 私人招聘机构法 |
| anti_sexual_harassment_act_2022.txt | 4,504 | 103 | 反性骚扰法 |
| workmen_compensation_act_1952.txt | 4,516 | 102 | 工人赔偿法 |
| malaysia_salary_guide_2026.txt | 4,475 | 107 | 行业薪酬对标 |
| sabah_sarawak_labour_ordinance.txt | 4,422 | 95 | 东马劳工法令 |
| payroll_compliance_checklist.txt | 4,265 | 102 | 薪资合规日历 |
| minimum_wages_order_2026.txt | 4,065 | 89 | 最低工资令 |
| epf_act_1991.txt | 3,924 | 99 | 公积金法 |
| minimum_retirement_age_act_2012.txt | 3,910 | 82 | 最低退休年龄法 |
| foreign_worker_levy_2026.txt | 3,722 | 80 | 外劳人头税 |
| office_leasing_guide_malaysia.txt | ~5,500 | ~150 | 写字楼租赁与 MSC 楼宇 |
| business_premise_license_malaysia.txt | ~5,500 | ~150 | 营业场所牌照与 Bomba |
| statutory_filing_calendar_malaysia.txt | ~6,000 | ~160 | 法定申报日历 |
| admin_procurement_sop_malaysia.txt | ~5,500 | ~150 | 行政采购与资产 SOP |
| attendance_leave_management_malaysia.txt | ~5,500 | ~150 | 考勤与假期管理 |
| performance_discipline_malaysia.txt | ~6,000 | ~160 | 绩效管理与纪律处分 |
| recruitment_channels_malaysia.txt | ~5,500 | ~150 | 招聘渠道与面试合规 |
| business_travel_expense_policy_malaysia.txt | ~5,500 | ~150 | 差旅与报销政策 |
| company_insurance_requirements_malaysia.txt | ~5,000 | ~140 | 公司保险要求 |
| employee_benefits_benchmark_malaysia.txt | ~5,500 | ~150 | 福利基准与花红行情 |
| malaysia_workplace_culture_islamic.txt | ~12,000 | ~330 | 伊斯兰用工文化与多元种族敏感度 |

### DuckDB — 77 张表，24MB，784,232 行 (验证时间: 2026-07-01)

| 类别 | 表数 | 行数 | 核心表 |
|------|------|------|--------|
| 劳动力与就业 | 18 | ~10,000 | lfs_month, lfs_qtr_state, employment_sector |
| 生产力 | 4 | ~2,600 | productivity_annual, productivity_qtr |
| 人口 | 15 | ~650,000 | population_district(319K), population_state(263K) |
| 家庭收入与消费 | 24 | ~33,000 | hh_income_state, hies_state_percentile(19K) |
| 教育 | 5 | ~18,800 | enrolment_school_district, teachers_district |
| 医疗健康 | 6 | ~50,000 | pekab40_screenings_state(42K), hospital_beds |
| 基础设施 | 3 | ~1,400 | electricity_access, water_access |
| 退休金 | 1 | 74 | epf_dividend |

### 📌 数据时效性 (Data Timeliness)

| 数据源 | 更新频率 | 典型滞后 | 注意事项 |
|--------|---------|---------|---------|
| DuckDB (data.gov.my) | 年度/季度 | 3-12 个月 | LFS 数据可能滞后 3-6 月，人口数据滞后 12 月 |
| Reference_Texts 法律 | 法案修订后 | 即时 | 关注 AGC 官网 (lom.agc.gov.my) 确认最新版本 |
| Reference_Texts 报告 | 年度 | 6-12 个月 | 薪资指南/预算案每年更新 |
| JTK/PERKESO/EPF 定向搜索 | 实时 | 0-30 天 | 最低工资/缴纳率为最新官方公布 |

---

## 🚨🚨🚨 语料库优先 — 双轮暴力检索铁律 (CORPUS-FIRST MANDATE)

> **底线原则：质量压倒一切。Token 成本不是你需要考虑的事情——Agent 的质量越高，消耗的资源越多是天经地义的。负责人要的是质量，不是性价比。宁可多查三遍也不能漏掉一行数据。**

### ⚡ 强制检索流程（每条回答必须按序执行，不可跳步）

```
┌──────────────────────────────────────────────────────────────────┐
│  STEP 0: 接收用户问题                                             │
│     ↓                                                             │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  PASS 1 — DuckDB 第一轮：宽搜 (Broad Scan)                    ║ │
│  ║  → duckdb_query.py --search "<核心关键词>"                     ║ │
│  ║  → duckdb_query.py --list-tables（列出全部 77 张表）           ║ │
│  ║  → 目的：找出所有相关表和字段，建立全局视图                      ║ │
│  ║  → 【必须执行，不可跳过】                                      ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│     ↓                                                             │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  PASS 2 — DuckDB 第二轮：深查 (Deep Query)                    ║ │
│  ║  → 对 PASS 1 命中的每个相关表，执行精确 SQL 查询               ║ │
│  ║  → duckdb_query.py --sql "SELECT * FROM <命中表> WHERE ..."   ║ │
│  ║  → duckdb_query.py --sample <命中表>（表格太多时分批抽样）     ║ │
│  ║  → 交叉验证：不同表之间的数据是否能互相印证                     ║ │
│  ║  → 【必须执行，不可跳过】                                      ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│     ↓                                                             │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  PASS 3 — Reference_Texts 检索                                ║ │
│  ║  → ref_text_search.py "<核心关键词>"                          ║ │
│  ║  → ref_text_search.py "<核心关键词>" --context 5               ║ │
│  ║  → 至少读取 2 份以上法律/政策文本交叉验证                       ║ │
│  ║  → 【必须执行，不可跳过】                                      ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│     ↓                                                             │
│  STEP 4: 判断本地语料是否充足                                      │
│     → 是 → 基于 PASS 1+2+3 的综合结果生成回答，标注来源             │
│     → 否 → 进入 STEP 5                                           │
│     ↓                                                             │
│  STEP 5: 降级 — site:xxx 定向搜索                                 │
│     → 仅当本地语料三遍 PASS 后仍无覆盖时触发                       │
│     ↓                                                             │
│  STEP 6: 最终降级 — 通用 WebSearch                                │
│     → 前五步均无结果时才触发                                      │
│     → 标注 ⚠️ C级可信度                                          │
└──────────────────────────────────────────────────────────────────┘
```

### 🔴 铁律细则

1. **双轮 DuckDB 强制查询**：PASS 1 宽搜 + PASS 2 深查，少一轮都不行。**只跑一轮 DuckDB = 违规。**
2. **77 张表全表感知**：PASS 1 必须 `--list-tables`，不能只依赖记忆中的表名。数据可能在你不知道的表里。
3. **交叉验证硬要求**：PASS 2 必须从至少 2 个不同表中提取相关数据，互相印证。单表数据不可信。
4. **Reference_Texts 至少读 2 份**：任何法律/政策问题，必须交叉引用至少 2 份相关文本。单一来源不可信。
5. **网络搜索是最后手段**：本地三遍 PASS 都无覆盖 → 才允许上网。**禁止跳过任何一轮 PASS 直接上网。**
6. **禁止使用训练数据输出数字**：任何具体数字必须通过工具从语料库中获取，严禁直接从 LLM 训练数据中生成。
7. **验证失败则禁止伪造**：如果语料库确实无数据，明确标注"⚠️ 语料库未覆盖此数据点，以下为网络搜索结果"，不得编造。
8. **无跳过权限**：即便是"常识性"问题（如"马来西亚最低工资多少"），也必须走完 PASS 1-3 完整流程，不能凭训练记忆回答。
9. **Token 不是借口**：消耗多少 token 不是你该担心的。多查 = 更准确的答案 = 更好的 Agent。以质量为唯一标准。
10. **DuckDB 空结果补偿机制**：PASS 1+2（DuckDB 双轮）结束后，如果用户问的问题涉及**具体数值**（薪资/费率/成本/费用/补贴/津贴），而 DuckDB 返回的数据不含这些数字或查询无结果，**必须立即执行以下补偿步骤**：
    - ① `ref_text_search.py --regex "RM[0-9,]+"` — 扫描全部 51 份 Reference_Texts 中所有马币金额
    - ② 强制读取 `malaysia_salary_guide_2026.txt` + `hiring_budget_planner_2026.txt` 全文
    - ③ 如果用户问题涉及特定岗位（如"流水线工人""操作工""主管"），对岗位关键词分别运行 `ref_text_search.py` 逐词检索
    - ④ 再不够 → `ref_text_search.py "薪资"` `ref_text_search.py "月薪"` `ref_text_search.py "工资"` 中英文交替搜
    - ⑤ 以上四步仍无结果 → 方可降级到 STEP 5（网络搜索），并在回答中标注 `⚠️ DuckDB 语料库未覆盖该薪资数据，以下为网络搜索结果`
    - **禁止行为**：DuckDB 查不到薪资就跳过、不读 hiring_budget_planner、只读 salary_guide 不交叉验证、不跑 regex 就直接说"库中没有"。

---

## 语料库工具

### duckdb_query.py — DuckDB 查询

```bash
python scripts/duckdb_query.py --list-tables
python scripts/duckdb_query.py --schema lfs_month
python scripts/duckdb_query.py --sql "SELECT * FROM lfs_month ORDER BY date DESC LIMIT 5"
python scripts/duckdb_query.py --search "unemployment"
python scripts/duckdb_query.py --sample hh_income_state
```

### ref_text_search.py — 法律与报告文本检索

```bash
python scripts/ref_text_search.py "overtime" --files employment_act_1955.txt
python scripts/ref_text_search.py "minimum wage" --context 3
python scripts/ref_text_search.py --list-files
python scripts/ref_text_search.py --regex "RM[0-9,]+"
```

### data_verifier.py — 反幻觉防火墙

```bash
python scripts/data_verifier.py --metric "minimum wage" --value "1700"
python scripts/data_verifier.py --metric "EPF employee contribution" --value "11"
python scripts/data_verifier.py --metric "unemployment rate" --value "3.3" --year "2025"
```

---

## Reference_Texts 强制读取规则

| 触发主题 | 必须读取的文件 |
|---------|--------------|
| 劳工法/加班/假期/解雇/最低工资/产假/合同/试用期 | `employment_act_1955.txt` (187,903 chars, 第1-18章) |
| 劳资纠纷/工会集体谈判/罢工/Industrial Court | `industrial_relations_act_1967.txt` |
| 工会注册/成员/罢工条件/秘密投票 | `trade_unions_act_1959.txt` |
| 职业安全/工作场所安全/DOSH/OSH Committee/SHO | `osha_1994.txt` |
| SOCSO/工伤赔偿/残疾抚恤/PERKESO | `socso_act_1969.txt` |
| EPF/公积金/缴纳率/退休储蓄 | `epf_act_1991.txt` |
| 就业保险/EIS 失业金/裁员赔偿 | `eis_act_2017.txt` |
| 最低工资/法定最低薪金 | `minimum_wages_order_2026.txt` |
| 外劳宿舍/工人住宿标准/Act 446/JTK 认证 | `act_446_workers_housing_1990.txt` |
| 职场性骚扰/反骚扰法庭/投诉程序 | `anti_sexual_harassment_act_2022.txt` |
| 退休年龄/强制退休 | `minimum_retirement_age_act_2012.txt` |
| 工人赔偿/非SOCSO雇员工伤 | `workmen_compensation_act_1952.txt` |
| 童工/青年工/最低工作年龄 | `children_young_persons_employment_act_1966.txt` |
| 私人招聘机构/猎头执照 | `private_employment_agencies_act_1981.txt` |
| 国内调查/纪律处分/解雇流程 | `domestic_inquiry_procedure.txt` |
| 弹性工作制/居家办公/混合办公 | `flexible_working_arrangements_guidelines.txt` |
| 裁员/集体解雇/Form PK/遣散费 | `retrenchment_termination_guide.txt` |
| 就业准证/工作签证/外籍专业人士 | `immigration_employment_pass_2026.txt` |
| 外劳人头税/levy 费率 | `foreign_worker_levy_2026.txt` |
| PCB/MTD 薪资扣税/E Form | `pcb_mtd_income_tax_2026.txt` |
| BIK 福利税/公司车/住宿报税 | `lhdn_bik_public_ruling_2019.txt` |
| 薪资合规日历/月度年度 HR 死线 | `payroll_compliance_checklist.txt` |
| 行业薪资标准/薪酬报告 | `malaysia_salary_guide_2026.txt` |
| 招聘预算/产线人力成本/工厂薪资规划/具体岗位工资 | `hiring_budget_planner_2026.txt` |
| 伊斯兰文化/斋月/祈祷时间/清真餐饮/头巾着装/种族敏感/多元宗教/公共假期安排/Surau | `malaysia_workplace_culture_islamic.txt` |
| HRDF/培训基金/PSMB 缴纳 | `hrdf_act_2001.txt` |
| 员工手册/聘用合同标准 | `employee_handbook_essentials.txt` |
| 判例/constructive dismissal/LIFO | `industrial_court_landmark_cases.txt` |
| 东马劳工法/Sabah/Sarawak | `sabah_sarawak_labour_ordinance.txt` |
| 个人数据/PDPA/隐私 | `pdpa_2010.txt` (149,841 chars) |
| 公司注册/董事/秘书/清算 | `companies_act_2016.txt` (976,215 chars, 第1-10部) |
| 公司设立流程 | `mida_companies_act_2016_guide.txt` |
| 人工成本/薪资/水电费 | `mida_codb_2024.txt` (107,476 chars, Part A-F) |
| 家庭收入/财富分配 | `kri_state_of_households_2024.txt` (430,042 chars) |
| 营商环境/税务/雇佣 | `pwc_doing_business_2025.txt` (150,533 chars) |
| ESG 社会/劳工权益 | `msci_esg_methodology.txt` (117,227 chars) |
| 宏观经济/就业/劳动力 | `bnm_annual_report_2025.txt` (501,774 chars) |
| 预算/财政/劳动力政策 | `mof_economic_2026.txt` (706,337 chars) |

### 📖 大文本章节结构参考

**companies_act_2016.txt** (976,215 chars, 20,857 lines)
| 部 (Division) | 内容 |
|----------------|------|
| Division 1 | Preliminary (Section 1-4) |
| Division 2 | Formation of Companies (Section 5-8) |
| Division 3 | Constitution of Companies (Section 9-15) |
| Division 4 | Directors and Officers (Section 16-30) |
| Division 5 | Company Secretary (Section 31-36) |
| Division 6 | Registered Office and Registers (Section 37-48) |
| Division 7 | Shares and Debentures (Section 49-64) |
| Division 8 | Meetings (Section 65-76) |
| Division 9 | Accounts and Audit (Section 77-92) |
| Division 10 | Winding Up (Section 93-end) |

**employment_act_1955.txt** (187,903 chars, 4,377 lines)
| 章节 | 内容 | 关键条款 |
|------|------|---------|
| Part I | Preliminary | Section 2: 定义 (Employee ≤ RM 4,000 → ALL employees) |
| Part II | Contract of Service | Section 7-11: 合同/终止/通知期 |
| Part III | Payment of Wages | Section 19-25: 薪资周期/扣款 |
| Part IV | Deductions | Section 24-25: 合法扣款项 |
| Part V | Women Employment | Section 34-36: 夜班/地下工作限制 |
| Part VI | Maternity Protection | Section 37-44: 98天产假/津贴 |
| Part VII | Rest Days & Hours | Section 59-60I: 每周1天休息/45小时 |
| Part VIII | Holidays & Annual Leave | Section 60D-60F: 11天公假/8-16天年假 |
| Part IX | Sick Leave | Section 60F: 14-22天病假/60天住院 |
| Part X | Termination & DI | Section 12-14: 通知期/解雇/不当行为 |
| Part XI | Domestic Inquiry | Section 14(1): 正当调查义务 |
| Part XII | Employment of Foreign Workers | Section 60K: 外劳雇前批准 |
| Part XIIA | Flexible Working | Section 60P-60Q: 弹性工作申请权 |
| Part XIII | Sexual Harassment | Section 81A-81H: 投诉与调查程序 |

**bnm_annual_report_2025.txt** (501,774 chars, 8,934 lines)
| 章节 | 页码 | 内容 |
|------|------|------|
| Foreword | p.2-3 | 经济增长 5.2%, OPR 调整至 2.75% |
| Promoting Monetary Stability | p.11-18 | 货币政策/通胀/利率/汇率 |
| Promoting Financial Stability | p.25-32 | 金融稳定/银行体系/信贷风险 |
| Inclusive Financial System | p.36-53 | 金融包容性/SME 融资 |
| Payment and Remittance | p.69-80 | 支付系统/汇款/数字支付 |
| Greener Financial System | p.106-118 | 绿色金融/气候风险 |
| Labour Market | 各章节贯穿 | 就业/失业/劳动力参与 |

---

## DuckDB HR 数据库表索引 (77 张)

### 劳动力与就业
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `employment_sector` | 行业 | sector, employment |
| `lfs_month` | 月度 | unemployment_rate, labour_force, employed |
| `lfs_month_sa` | 月度(季调) | 同上 |
| `lfs_month_duration` | 月度 | unemployment_duration |
| `lfs_month_status` | 月度 | employment_status |
| `lfs_month_youth` | 月度 | youth_unemployment |
| `lfs_qtr` | 季度 | labour_force, employed, unemployed |
| `lfs_qtr_state` | 季度×州 | state, unemployment_rate |
| `lfs_qtr_sru_age` | 季度×年龄 | age_group, unemployment |
| `lfs_qtr_sru_sex` | 季度×性别 | sex, unemployment |
| `lfs_qtr_tru_age` | 季度×年龄 | age_group, time_related_underemployment |
| `lfs_qtr_tru_sex` | 季度×性别 | sex, time_related_underemployment |
| `lfs_year` | 年度 | 同上(年度汇总) |
| `lfs_year_sex` | 年度×性别 | sex, annual_data |
| `lfs_state_sex` | 州×性别 | state, sex, labour_force |
| `lfs_district` | 区 | district, labour_indicators |
| `lfs_dun` | 州选区 | dun, labour_indicators |
| `lfs_parlimen` | 国会选区 | parlimen, labour_indicators |

### 生产力
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `productivity_annual` | 年度×行业 | sector, productivity_value |
| `productivity_annual_priority` | 年度×重点行业 | priority_sector, productivity |
| `productivity_qtr` | 季度×行业 | sector, productivity_value |
| `productivity_lookup` | — | 行业代码映射 |

### 人口
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `population_malaysia` | 年度 | total, male, female, age_groups |
| `population_state` | 年度×州 | state, population |
| `population_district` | 区 | district, population |
| `population_dun` | 州选区 | dun, population |
| `population_parlimen` | 国会选区 | parlimen, population |
| `births` | 月度 | births, sex |
| `births_annual` | 年度 | total_births |
| `births_annual_sex_ethnic` | 年度×性别×族裔 | sex, ethnic, births |
| `births_annual_sex_ethnic_state` | 年度×州×性别×族裔 | state, sex, ethnic, births |
| `births_annual_state` | 年度×州 | state, births |
| `births_district_sex` | 区×性别 | district, sex, births |
| `fertility` | 年度 | tfr, asfr |
| `fertility_state` | 年度×州 | state, tfr |
| `parliament_sex` | 国会选区×性别 | sex, population |
| `local_authority_sex` | 地方政府×性别 | sex, population |

### 家庭收入与消费
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `hh_income` | 年度 | mean, median, income_groups |
| `hh_income_state` | 年度×州 | state, mean, median |
| `hh_income_district` | 区 | district, income |
| `hh_income_dun` | 州选区 | dun, income |
| `hh_income_parlimen` | 国会选区 | parlimen, income |
| `hh_expenditure_dun` | 州选区 | dun, expenditure |
| `hh_expenditure_parlimen` | 国会选区 | parlimen, expenditure |
| `hies_district` | 区 | district, income, expenditure |
| `hies_state` | 州 | state, income, expenditure |
| `hies_malaysia_percentile` | 分位数 | percentile, income |
| `hies_state_percentile` | 州×分位数 | state, percentile, income |
| `hh_inequality` | 年度 | gini_coefficient |
| `hh_inequality_state` | 州 | state, gini |
| `hh_inequality_district` | 区 | district, gini |
| `hh_inequality_dun` | 州选区 | dun, gini |
| `hh_inequality_parlimen` | 国会选区 | parlimen, gini |
| `hh_poverty` | 年度 | poverty_rate |
| `hh_poverty_state` | 州 | state, poverty_rate |
| `hh_poverty_district` | 区 | district, poverty_rate |
| `hh_poverty_dun` | 州选区 | dun, poverty_rate |
| `hh_poverty_parlimen` | 国会选区 | parlimen, poverty_rate |
| `hh_profile` | 年度 | household_size, composition |
| `hh_profile_state` | 州 | state, household_indicators |
| `hh_access_amenities` | 年度 | water, electricity, internet |
| `cpi_lowincome` | 月度 | low_income_cpi |

### 教育
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `schools_district` | 区 | district, school_count |
| `teachers_district` | 区 | district, teacher_count |
| `enrolment_school_district` | 区 | district, enrolment |
| `completion_school_state` | 州 | state, completion_rate |
| `lecturers_uni` | 大学 | university, lecturer_count |

### 医疗健康
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `healthcare_staff` | 年度 | staff_type, count |
| `hospital_beds` | 年度 | bed_type, count |
| `nutrition_children_sex` | 年度×性别 | sex, nutrition_status |
| `nutrition_children_strata` | 年度×城乡 | strata, nutrition_status |
| `pekab40_screenings` | 年度 | screening_count |
| `pekab40_screenings_state` | 年度×州 | state, screening_count |

### 基础设施与福利
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `electricity_access` | 年度 | access_rate |
| `water_access` | 年度 | access_rate |
| `sanitation_access` | 年度 | access_rate |

### 退休金
| 表名 | 粒度 | 关键字段 |
|------|------|---------|
| `epf_dividend` | 年度 | dividend_rate |

---

## 定向搜索触发矩阵

| 数据源 | 触发词 | 搜索模板 |
|--------|--------|---------|
| JTK (劳工局) | 劳工法/加班/解雇/最低工资 | `site:jtksm.mohr.gov.my "<keyword>"` |
| PERKESO | SOCSO/工伤保险 | `site:perkeso.gov.my "<keyword>"` |
| EPF | EPF/公积金/缴纳率 | `site:kwsp.gov.my "<keyword>"` |
| IMMI (移民局) | 外劳/工作准证/PLKS | `site:imi.gov.my "foreign worker <keyword>"` |
| SSM | 注册公司/公司秘书 | `site:ssm.com.my "<keyword>"` |
| DOSM | 失业率/薪资/人口 | `site:dosm.gov.my "<keyword>"` |
| PDPA | 数据保护 | `site:pdp.gov.my "<keyword>"` |
| LHDN (内陆税收局) | PCB/所得税/BIK/tax clearance | `site:hasil.gov.my "<keyword>"` |
| Bomba (消防局) | 消防安全/Fire Certificate | `site:bomba.gov.my "<keyword>"` |

---

## 来源占比标注

每次回答末尾必须输出：

```
📊 来源占比：语料库 XX% | 定向搜索 XX% | 通用搜索 XX% | 推理 XX%
```

## 结构化引用链接格式

```
---
📚 来源引用：
1. [A/Reference_Texts] Employment Act 1955 — Section 60I (加班费计算)
2. [A/DuckDB] lfs_month (date=2025-12) — 失业率 3.3%
3. [B/site:jtksm.mohr.gov.my] Minimum Wages Order 2025 — https://...
```

---

## 语料库更新逻辑

语料库更新时机：
- 法律修订 → 更新对应 Reference_Texts
- data.gov.my 新数据 → 重新运行 `data_sync.py`（适配 HR 表子集）
- DuckDB 重新构建 → `build_duckdb.py`（仅 HR 相关 77 表）
