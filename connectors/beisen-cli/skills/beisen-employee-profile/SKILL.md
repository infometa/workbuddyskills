---
name: beisen-employee-profile
version: 1.0.9
description: "北森员工档案查询。本 Skill 用于查询员工基本信息、任职信息、语言能力、教育背景、考核结果、证书执照、项目经历、专业技能、工作履历、表彰奖励、晋升结果。所有查询通过 beisen-data-query 通用数据查询流水线执行。当用户询问个人信息、任职、学历、绩效、证书、项目、技能、履历、奖项、晋升等员工档案相关问题时触发。"
category: 人力资源/员工档案
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 员工档案

**CRITICAL — 开始前 MUST 读取：**
1. **[../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)** — 认证、安全规则、门禁协议
2. **[../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)** — 通用数据查询流水线（本 Skill 所有场景均走此流水线）

## 路由优先级

本 Skill 处理：员工个人档案的查询（基础信息 + 扩展属性）

不归本 Skill 处理：
- 考勤/休假数据 → [../beisen-attendance-leave/SKILL.md](../beisen-attendance-leave/SKILL.md)
- 组织层面的信息 → [../beisen-organization/SKILL.md](../beisen-organization/SKILL.md)
- 考核/晋升的操作流程（审批） → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)

## 场景清单

以下场景统一使用 [beisen-data-query](../beisen-data-query/SKILL.md) 的 SceneTool → SceneToolMessage → SearchFormTool → BusinessDataTool → 生成回答 → 展示关联菜单 6 步流水线：

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

> 实际查询场景名称由租户在后台配置决定，Agent 必须通过 `SceneTool` 动态获取，不可硬编码。

## 执行原则

- 所有查询走 beisen-data-query 流水线，Agent 按 6 步流程执行
- 默认查询当前用户自己的信息（员工字段 value=`"当前用户"`）
- 查询他人信息时，员工字段 value 填具体人名；查询团队时 value 不传
- 考核结果、晋升结果属于 L2 敏感数据：
  - 查自己 → 完整展示
  - 查他人 → 仅展示摘要，不回显原始 JSON
- dataList 中的员工字段值已含消歧信息（如"姓名(部门)"），直接使用
- 多轮对话时，结合上下文将代词替换为前文已出现的具体人名

## 参数提取要点

- 员工字段：查自己 → `"当前用户"`；查他人 → 具体人名；查团队 → 不传
- 日期字段：用户未提及日期时不传该字段
- 选项字段：从 `dataSourceItems` 匹配用户表达，value 填匹配项的 id
- 详细提取规则见 [../beisen-data-query/references/business-rules.md](../beisen-data-query/references/business-rules.md)

## Playbook 案例

### 案例 1：查询自己的基本信息

用户问："我的任职信息是什么？"

执行步骤：
1. 前置检查
2. 按 beisen-data-query 6 步流水线执行
3. SceneTool 匹配"员工档案"/"任职信息"场景
4. SearchFormTool 获取字段，员工字段 value=`"当前用户"`
5. BusinessDataTool 查询数据
6. 生成回答，展示关联菜单

### 案例 2：查询他人考核结果（L2 敏感）

用户问："李白最近的考核结果怎么样？"

执行步骤：
1. 前置检查
2. 按 6 步流水线执行，员工字段 value=`"李白"`
3. 查询结果为 L2 敏感数据，仅展示摘要
4. 不回显原始 JSON

## 详细参考

- [references/basic-info.md](references/basic-info.md)：基础信息场景说明
- [references/education-skills.md](references/education-skills.md)：教育技能类场景说明
- [references/performance-promotion.md](references/performance-promotion.md)：绩效晋升类场景说明（含 L2 敏感数据处理规则）
- [../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)：通用查询流水线完整步骤
- [../beisen-data-query/references/business-rules.md](../beisen-data-query/references/business-rules.md)：参数提取规则与输出格式要求
