---
name: erhao-hr-org
description: "二号人事部组织域：组织架构部门树与 8 个组织维度清单查询，用于组织盘点、部门维度分布与 ID 解析。"
description_zh: "组织域技能：查询组织架构部门树、工作地点、职务、岗位、合同公司、工作城市、岗位类别树、职等、职级；含职级/职等语义区分与 count/full_count 口径。"
description_en: "Organization domain: department tree plus work place, job position, job title, contract company, work city, job title group, job grade and job level lookups, with level/grade semantics and count/full_count conventions."
version: 0.1.9
author: 二号人事部
---

# 二号人事部 · 组织域

> 机制、返回形态与默认查询口径见共享技能 `erhao-hr`；本技能只讲「场景 → 工具 → 本域口径」。

## 核心概念

- `job_level_name` = **职级**（如 P1 / P2 / M1 / M2）；`job_grade_name` = **职等**（如 1 / 2 / 3）。
  用户说「职级分布」时一律按**职级**（`job_level_name`）处理，不要拿职等凑数，两者不可互换。
- **岗位** = `job_title`（岗位清单）；**职务** = `job_position`（职务清单）。两者是不同维度，不可混用。
- 基础维度清单**不分页**，用于把用户的自然语言名称解析成 ID。

## 场景 → 工具

| 场景 | 工具 | 本域口径 |
|---|---|---|
| 组织架构查询 | `orgs_department_tree` | 部门树，节点含 `id` / `name` / `level` / `count` / `full_count` / `children` |
| 组织盘点 / 部门规模 | `orgs_department_tree` | `count` = **直属**人数；`full_count` = **含子级**总人数。汇报组织概况优先用 `full_count` |
| 工作地点清单（取 ID） | `orgs_work_place` | 名称 → ID 解析 |
| 职务清单（取 ID） | `orgs_job_position` | 职务维度 |
| 岗位清单（取 ID） | `orgs_job_title` | 岗位维度 |
| 合同公司清单（取 ID） | `orgs_contract_company` | 合同主体维度 |
| 工作城市清单（取 ID） | `orgs_work_city` | 城市维度 |
| 岗位类别树 | `orgs_job_title_group` | 树形，可按类别统计 |
| 职等清单（取 ID） | `orgs_job_grade` | 职等 = `job_grade_name`（1 / 2 / 3） |
| 职级清单（取 ID） | `orgs_job_level` | 职级 = `job_level_name`（P1 / P2 / M1 / M2） |

## 与其他域的衔接

组织维度的**人数分布**（部门 × 性别 / 学历 / 职级 …）在本域只负责拿**维度名与 ID**，
分组统计一律回花名册域 `employee_high_level_search` 执行（见 `erhao-hr-employee`）。

## ID 唯一性铁律

凡需要 `dep_id` / `job_title_id` 等 ID 的工具，**必须先经本域工具（或花名册搜索）拿到真实 ID**，
禁止把中文名称直接当 ID 传入；也不要用近似名称猜 ID。

## 引用

返回形态、分页拉全量、默认查询口径与错误恢复见共享技能 `erhao-hr`。
