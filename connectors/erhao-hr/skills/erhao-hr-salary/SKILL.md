---
name: erhao-hr-salary
description: "二号人事部薪酬域：工资核算明细与月薪汇总、薪资档案、银行发放模板、业务提报、公司成本与员工成本分摊、个税记录。"
description_zh: "薪酬域技能：核算明细/月薪汇总/薪资档案、银行模板、提报计划与数据、成本汇总与员工分摊、个税；含租户动态项目 code 与表头先行口径。"
description_en: "Payroll domain: calculation details, monthly totals, salary archive, bank templates, business reporting, company and per-employee cost allocation, and tax records; salary item codes are tenant-dynamic and require fetching headers first."
version: 0.1.9
author: 二号人事部
---

# 二号人事部 · 薪酬域

> 机制、返回形态与默认查询口径见共享技能 `erhao-hr`；本技能只讲「场景 → 工具 → 本域口径」。

## 场景 → 工具

| 场景 | 工具 | 本域口径 |
|---|---|---|
| 工资核算明细 | `smart_salary_calc_detail` | 按人按项目的核算明细 |
| 核算明细表头 | `smart_salary_calc_detail_headers` | **先取表头**确定项目 code 与含义 |
| 月薪汇总 | `smart_salary_month_total` | 按期间汇总额 |
| 月薪汇总表头 | `smart_salary_month_total_headers` | 汇总列含义 |
| 薪资档案 | `smart_salary_archive` | 员工薪资档案项 |
| 薪资档案表头 | `smart_salary_archive_headers` | 档案列含义 |
| 银行发放模板 | `smart_salary_bank_template` | 发放模板（不含金额口径判断） |
| 业务提报计划 | `smart_salary_report_plan` | 提报计划与状态 |
| 业务提报表头 | `smart_salary_report_headers` | 提报列含义 |
| 业务提报数据 | `smart_salary_report_data` | 提报明细数据 |
| 公司成本汇总 | `smart_salary_cost_result_data` | 公司维度成本结果 |
| 成本汇总表头 | `smart_salary_cost_result_headers` | 成本列含义 |
| 员工成本分摊 | `smart_salary_emp_cost` | 员工维度分摊额 |
| 员工分摊表头 | `smart_salary_emp_cost_headers` | 分摊列含义 |
| 个税记录 | `smart_salary_tax` | 个税明细 |
| 个税表头 | `smart_salary_tax_headers` | 个税列含义 |

## 域特有口径

- **薪酬项目 code 为租户动态**（形如 `ITEM…`，每个企业不同）：**必须先取表头**确定项目 code 与含义，
  再按 code 取数；**不存在通用项目映射表**，不要凭经验拼项目 code，也不要把 A 企业的 code 套用到 B 企业。
- 表头工具返回的 `value_type` 用于判定列是数值还是文本；**聚合前必须筛掉非数值列**（否则会得到字符串拼接或空值）。
- **环比 / 同比**一律用相邻期数据计算，不得跨期混算；期间口径不一致时先对齐期间再比。
- 员工成本分摊接口（`smart_salary_emp_cost`）的 `totalpage` **可能恒为 0**：
  按「返回为空」终止翻页，不要依赖 `totalpage` 判定结束。
- 金额/个税类数据的口径差异（如是否含税、是否含年终奖）以表头与项目含义为准，不臆测。

## 引用

返回形态、分页拉全量、默认查询口径与错误恢复见共享技能 `erhao-hr`。
