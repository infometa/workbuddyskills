---
name: erhao-hr-employee
description: "二号人事部人事域：花名册高级搜索、异动记录、合同状态与 15 个多列表域（教育/经历/技能/联系人等）的查询与表头解读。"
description_zh: "人事域技能：花名册复合筛选、异动类型/原因、合同签订与未签名单，以及 15 个多列表域（每个域含列表 + 表头工具）；按主题挑域，含在职三态与离职口径。"
description_en: "Employee domain: roster high-level search, transfer records, contract status and 15 multi-list domains (education, work experience, skills, contacts, etc.) with per-domain headers for field semantics."
version: 0.1.9
author: 二号人事部
---

# 二号人事部 · 人事域

> 机制、返回形态与默认查询口径见共享技能 `erhao-hr`；本技能只讲「场景 → 工具 → 本域口径」。

## 场景 → 工具

| 场景 | 工具 | 本域口径 |
|---|---|---|
| 花名册复合查询（核心） | `employee_high_level_search` | 批量人员筛选与统计的主入口；条件字段可透视 |
| 花名册字段中文含义 / 参数类型 | `employee_high_level_search_headers` | 字段含义不明时先取表头再解读 |
| 异动记录 | `employee_transfer_record` | 入职/转正/调岗等异动明细 |
| 异动表头 | `employee_transfer_record_headers` | 异动字段含义 |
| 异动类型枚举 | `employee_transfer_type` | 取异动类型的合法取值 |
| 异动原因枚举 | `employee_transfer_reason` | 取异动原因的合法取值 |
| 合同签订情况（按部门统计） | `employee_contract_status` | 各部门签订/未签数量 |
| 合同签订记录 | `employee_contract_record` | 逐条签订记录 |
| 未签订合同名单 | `employee_unsign_contract` | 待签订人员名单 |

## 15 个多列表域（列表 + 表头）

**按主题只挑相关域，切勿一次拉全部**。每个域一对工具：列表取数、表头解释字段。

| 域 | 列表工具 | 表头工具 |
|---|---|---|
| 教育 | `employee_education` | `employee_education_headers` |
| 工作经历 | `employee_work_experience` | `employee_work_experience_headers` |
| 技能 | `employee_skill` | `employee_skill_headers` |
| 紧急联系人 | `employee_emergency_contact` | `employee_emergency_contact_headers` |
| 家庭成员 | `employee_family_member` | `employee_family_member_headers` |
| 职称 | `employee_professional_title` | `employee_professional_title_headers` |
| 工作技能 | `employee_work_skill` | `employee_work_skill_headers` |
| 语言 | `employee_language` | `employee_language_headers` |
| 履历 | `employee_career` | `employee_career_headers` |
| 会话 | `employee_conversation` | `employee_conversation_headers` |
| 培训 | `employee_training` | `employee_training_headers` |
| 奖励惩罚 | `employee_award` | `employee_award_headers` |
| 实习生 | `employee_intern` | `employee_intern_headers` |
| 考察 | `employee_investigation` | `employee_investigation_headers` |
| 入职意向 | `employee_intent_employee` | `employee_intent_employee_headers` |

## 表头的用法

表头工具返回字段的中文含义与搜索参数类型；**列表工具返回的字段含义不明时，先取该域表头再解读**，
不要凭字段英文名猜含义，也不要把某个域的字段含义套用到另一个域。

## 口径应用

- 在职一律用**三态** `1、2、3`（试用 / 正式 / 待离职），详见共享技能 `erhao-hr`；聚合值 `6` 不使用。
- 主题为「离职」时改用已离职（`work_status=[4]`）。
- 需要 `dep_id` 等 ID 时先经组织域工具解析（见 `erhao-hr-org`）。

## 引用

返回形态、分页拉全量、默认查询口径与错误恢复见共享技能 `erhao-hr`。
