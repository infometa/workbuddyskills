---
name: beisen-organization
version: 1.0.9
description: "北森组织架构查询。本 Skill 用于查询组织/部门信息（负责人、BP、分管领导、行政助理）和编制信息。所有查询通过 beisen-data-query 通用数据查询流水线执行，需管理者视角。当用户询问组织、部门、负责人、BP、编制、分管领导、行政助理等组织架构相关问题时触发。"
category: 人力资源/组织架构
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 组织架构

**CRITICAL — 开始前 MUST 读取：**
1. **[../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)** — 认证、安全规则、门禁协议
2. **[../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)** — 通用数据查询流水线（本 Skill 所有场景均走此流水线）

## 路由优先级

本 Skill 处理：组织层面的信息查询（组织架构、负责人、编制）

不归本 Skill 处理：
- 员工个人信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
- 考勤数据 → [../beisen-attendance-leave/SKILL.md](../beisen-attendance-leave/SKILL.md)
- 企业知识制度查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)

## 场景清单

以下场景统一使用 [beisen-data-query](../beisen-data-query/SKILL.md) 的 SceneTool → SceneToolMessage → SearchFormTool → BusinessDataTool → 生成回答 → 展示关联菜单 6 步流水线：

| 场景 | 对应北森查询场景 | 敏感等级 |
|------|---------------|:------:|
| 查询组织信息 | 租户配置的"组织信息"场景 | L0 |
| 查询编制信息 | 租户配置的"编制信息"场景 | L1 |

> 实际查询场景名称由租户在后台配置决定，Agent 必须通过 `SceneTool` 动态获取，不可硬编码。

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

- 所有查询走 beisen-data-query 流水线，Agent 按 6 步流程执行
- 组织信息查询需要 `beisen:org:read` scope，缺少时按 beisen-shared 的权限不足流程处理
- 返回的 ID（负责人、BP、分管领导等）已由后端完成消歧，直接使用
- 组织架构数据属于 L0 公开信息，正常完整展示
- 编制信息属于 L1 内部数据，批量查询时使用摘要模式
- 多轮对话时，结合上下文理解用户查询的组织范围

## 参数提取要点

- 组织字段：用户提及部门名称时，从 `dataSourceItems` 匹配，value 填对应 id
- 日期字段：组织信息通常不涉及日期筛选，用户未提及时不传
- 员工字段：通常不涉及，除非查询特定负责人的组织信息
- 详细提取规则见 [../beisen-data-query/references/business-rules.md](../beisen-data-query/references/business-rules.md)

## Playbook 案例

### 案例 1：查询部门负责人

用户问："技术部的负责人是谁？"

执行步骤：
1. 前置检查
2. 按 beisen-data-query 6 步流水线执行
3. SceneTool 匹配"组织信息"场景
4. SearchFormTool 获取字段，组织字段匹配"技术部"
5. BusinessDataTool 查询数据
6. 生成回答，展示负责人信息

### 案例 2：查询编制情况

用户问："我们部门还有多少空编？"

执行步骤：
1. 按 6 步流水线执行
2. SceneTool 匹配"编制信息"场景
3. 查询当前用户所在部门的编制数据
4. 展示编制数量、在岗人数、空缺数

## 详细参考

- [references/org-info.md](references/org-info.md)：组织信息场景说明
- [references/headcount.md](references/headcount.md)：编制信息场景说明
- [../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)：通用查询流水线完整步骤
- [../beisen-data-query/references/business-rules.md](../beisen-data-query/references/business-rules.md)：参数提取规则与输出格式要求

## 不在本 Skill 范围

- 企业知识制度查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)
- 办事入口 → [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 员工个人信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
