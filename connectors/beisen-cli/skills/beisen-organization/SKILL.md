---
name: beisen-organization
version: 3.2.1
description: "北森组织架构查询。本 Skill 用于查询组织/部门信息（负责人、BP、分管领导、行政助理）和编制信息。所有查询通过 beisen-data-query 通用数据查询流水线执行；查询结果受当前授权账号的组织管理权限范围影响。当用户询问组织、部门、负责人、BP、编制、分管领导、行政助理等组织架构相关问题时触发。"
author: beisen
display_name: "北森组织架构"
display_name_en: "Beisen Organization Structure"
description_zh: "北森组织架构查询。本 Skill 用于查询组织/部门信息（负责人、BP、分管领导、行政助理）和编制信息。所有查询通过 beisen-data-query 通用数据查询流水线执行；查询结果受当前授权账号的组织管理权限范围影响。当用户询问组织、部门、负责人、BP、编制、分管领导、行政助理等组织架构相关问题时触发。"
description_en: "Beisen organizational-structure query. This Skill queries organization/department information (person in charge, HRBP, supervising leader, administrative assistant) and headcount information. All queries run through the beisen-data-query universal data-query pipeline; results are scoped by the current authorized account's organization-management permissions. Trigger when the user asks organizational-structure questions about organizations, departments, the person in charge, HRBP, headcount, supervising leader, or administrative assistant."
category: productivity
requires-skills:
  - beisen-shared
  - beisen-data-query
---

# 组织架构

**CRITICAL — 开始前 MUST 读取：**
1. **[references/beisen-shared.md](references/beisen-shared.md)** — 连接器与授权、安全规则、写操作门禁
2. **[references/beisen-data-query.md](references/beisen-data-query.md)** — 通用数据查询流水线（本 Skill 所有场景均走此流水线）

## 路由优先级

本 Skill 处理：组织层面的信息查询（组织架构、负责人、编制）

不归本 Skill 处理：
- 员工个人信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
- 考勤数据 → [../beisen-attendance-leave/SKILL.md](../beisen-attendance-leave/SKILL.md)
- 企业知识制度查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)

## 场景清单

以下场景统一按 [beisen-data-query](references/beisen-data-query.md) 的 6 步流水线执行：场景发现 → 场景说明（输出要求与关联菜单）→ 场景字段 → 数据查询 → 生成回答 → 展示关联菜单。

| 场景 | 对应北森查询场景 | 敏感等级 |
|------|---------------|:------:|
| 查询组织信息 | 租户配置的"组织信息"场景 | L0 |
| 查询编制信息 | 租户配置的"编制信息"场景 | L1 |

> 实际查询场景名称由租户在后台配置决定，Agent 必须通过场景发现工具动态获取，不可硬编码。

### 组织信息场景

返回部门信息，包括：
- 部门名称、部门编码
- 负责人、BP、分管领导、行政助理
- 上级部门、下属部门

### 编制信息场景

返回各组织的编制数据，包括：
- 编制数量、在岗人数、空缺数
- 编制类型（正式编制、合同制等）

## 执行原则

- 所有查询走 beisen-data-query 流水线，Agent 按 6 步流程执行；工具选择与参数格式以连接器工具清单和各工具 inputSchema 为准
- 查询结果受当前授权账号的组织管理权限范围影响；权限不足时按 beisen-shared 的权限不足流程处理（如实转述、引导联系管理员、不反复重试）
- 返回中的人员/组织标识已由后端完成消歧，直接使用
- 组织架构数据属于 L0 公开信息，正常完整展示
- 编制信息属于 L1 内部数据，批量查询时使用摘要模式
- 部门名按流水线的部门名提取规则原文透传（剥离查询词和虚词、以部门后缀结尾），模糊匹配由后端负责
- 组织信息通常不涉及日期筛选；多轮对话时，结合上下文理解用户查询的组织范围

## Playbook 案例

### 案例 1：查询部门负责人

用户问："技术部的负责人是谁？"

执行步骤：
1. 按 beisen-data-query 6 步流水线执行
2. 场景发现匹配"组织信息"场景
3. 场景字段返回筛选字段 → 提取：部门="技术部"（原文透传）
4. 数据查询 → 生成回答，展示负责人信息

### 案例 2：查询编制情况

用户问："我们部门还有多少空编？"

执行步骤：
1. 按 6 步流水线执行
2. 场景发现匹配"编制信息"场景
3. 查询当前用户所在部门的编制数据
4. 展示编制数量、在岗人数、空缺数（数字逐字取自返回记录，不做计算）

## 不在本 Skill 范围

- 企业知识制度查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)
- 办事入口 → [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 员工个人信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
