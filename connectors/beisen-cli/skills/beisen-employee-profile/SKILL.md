---
name: beisen-employee-profile
version: 3.2.1
description: "北森员工档案查询。本 Skill 用于查询员工基本信息、任职信息、语言能力、教育背景、考核结果、证书执照、项目经历、专业技能、工作履历、表彰奖励、晋升结果。所有查询通过 beisen-data-query 通用数据查询流水线执行。当用户询问个人信息、任职、学历、绩效、证书、项目、技能、履历、奖项、晋升等员工档案相关问题时触发。"
author: beisen
display_name: "北森员工档案"
display_name_en: "Beisen Employee Profile"
description_zh: "北森员工档案查询。本 Skill 用于查询员工基本信息、任职信息、语言能力、教育背景、考核结果、证书执照、项目经历、专业技能、工作履历、表彰奖励、晋升结果。所有查询通过 beisen-data-query 通用数据查询流水线执行。当用户询问个人信息、任职、学历、绩效、证书、项目、技能、履历、奖项、晋升等员工档案相关问题时触发。"
description_en: "Beisen employee-profile query. This Skill queries an employee's basic information, employment information, language ability, education background, performance-review results, certificates and licenses, project experience, professional skills, work history, awards and recognitions, and promotion results. All queries run through the beisen-data-query universal data-query pipeline. Trigger when the user asks employee-profile questions about personal info, employment, education, performance, certificates, projects, skills, work history, awards, or promotions."
category: productivity
requires-skills:
  - beisen-shared
  - beisen-data-query
---

# 员工档案

**CRITICAL — 开始前 MUST 读取：**
1. **[references/beisen-shared.md](references/beisen-shared.md)** — 连接器与授权、安全规则、写操作门禁
2. **[references/beisen-data-query.md](references/beisen-data-query.md)** — 通用数据查询流水线（本 Skill 所有场景均走此流水线）

## 路由优先级

本 Skill 处理：员工个人档案的查询（基础信息 + 扩展属性）

不归本 Skill 处理：
- 考勤/休假数据 → [../beisen-attendance-leave/SKILL.md](../beisen-attendance-leave/SKILL.md)
- 组织层面的信息 → [../beisen-organization/SKILL.md](../beisen-organization/SKILL.md)
- 考核/晋升的操作流程（审批） → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)

## 场景清单

以下场景统一按 [beisen-data-query](references/beisen-data-query.md) 的 6 步流水线执行：场景发现 → 场景说明（输出要求与关联菜单）→ 场景字段 → 数据查询 → 生成回答 → 展示关联菜单。

### 基础信息类

| 场景 | 对应北森查询场景 | 敏感等级 |
|------|---------------|:------:|
| 查询员工基本信息、任职信息 | 租户配置的"员工档案"/"任职信息"场景 | L1 |
| 查询员工语言能力 | 租户配置的"语言能力"场景 | L1 |
| 查询教育背景 | 租户配置的"教育背景"场景 | L1 |

### 教育技能类

| 场景 | 对应北森查询场景 | 敏感等级 |
|------|---------------|:------:|
| 查询证书执照 | 租户配置的"证书执照"场景 | L1 |
| 查询专业技能 | 租户配置的"专业技能"场景 | L1 |
| 查询项目经历 | 租户配置的"项目经历"场景 | L1 |
| 查询工作履历 | 租户配置的"工作履历"场景 | L1 |

### 绩效晋升类（L2 敏感）

| 场景 | 对应北森查询场景 | 敏感等级 |
|------|---------------|:------:|
| 查询考核结果 | 租户配置的"考核结果"场景 | L2 |
| 查询表彰与奖励 | 租户配置的"表彰与奖励"场景 | L1 |
| 查询晋升结果 | 租户配置的"晋升结果"场景 | L2 |

> 实际查询场景名称由租户在后台配置决定，Agent 必须通过场景发现工具动态获取，不可硬编码。

## 执行原则

- 所有查询走 beisen-data-query 流水线，Agent 按 6 步流程执行；工具选择与参数格式以连接器工具清单和各工具 inputSchema 为准
- 默认查询当前用户自己的信息；查询他人时主体为具体人名（原文透传）；查询团队时按流水线的组织范围判定处理
- 考核结果、晋升结果属于 L2 敏感数据：
  - 查自己 → 完整展示
  - 查他人 → 仅展示摘要，不回显原始返回
- 返回记录中的员工姓名通常已含消歧信息（如"姓名(部门)"），直接使用
- 用户未提及日期时不传时间条件
- 多轮对话时，结合上下文将代词替换为前文已出现的具体人名

## Playbook 案例

### 案例 1：查询自己的基本信息

用户问："我的任职信息是什么？"

执行步骤：
1. 按 beisen-data-query 6 步流水线执行
2. 场景发现匹配"员工档案"/"任职信息"场景
3. 场景字段返回筛选字段 → 提取：主体=本人
4. 数据查询 → 生成回答 → 展示关联菜单

### 案例 2：查询他人考核结果（L2 敏感）

用户问："李白最近的考核结果怎么样？"

执行步骤：
1. 按 6 步流水线执行：主体=指定人"李白"
2. 查询结果为 L2 敏感数据，仅展示摘要
3. 不回显原始返回

## 不在本 Skill 范围

- 考勤/休假数据 → [../beisen-attendance-leave/SKILL.md](../beisen-attendance-leave/SKILL.md)
- 组织层面信息 → [../beisen-organization/SKILL.md](../beisen-organization/SKILL.md)
- 企业知识制度查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)
