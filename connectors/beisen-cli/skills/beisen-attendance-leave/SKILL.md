---
name: beisen-attendance-leave
version: 1.1.0
description: "北森考勤休假查询。本 Skill 用于查询假期余额、考勤记录、排班信息、加班、公出、出差、休假记录、调休假余额。所有查询通过 beisen-data-query 通用数据查询流水线执行。当用户询问考勤、打卡、排班、加班、公出、出差、休假、请假、调休、假期余额等考勤休假相关问题时触发。"
category: 人力资源/考勤休假
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 考勤休假

**CRITICAL — 开始前 MUST 读取：**
1. **[../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)** — 认证、安全规则、门禁协议
2. **[../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)** — 通用数据查询流水线（本 Skill 所有场景均走此流水线）

## 路由优先级

本 Skill 处理：考勤与休假数据的查询（只读）

不归本 Skill 处理：
- 业务操作意图（"我要请假""我要出差""我要休假""申请加班""帮我请个假"等，即用户要**执行某项操作**而非查询数据）→ [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 员工个人档案信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
- 考勤制度/政策查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)

## 场景清单

以下场景统一使用 [beisen-data-query](../beisen-data-query/SKILL.md) 的 SceneTool → SceneToolMessage → SearchFormTool → BusinessDataTool → 生成回答 → 展示关联菜单 6 步流水线：

### 考勤类

| 场景 | 对应北森查询场景 | 敏感等级 |
|------|---------------|:------:|
| 查询考勤记录 | 租户配置的"考勤记录"场景 | L1（本人）/ L2（他人） |
| 查询考勤排班信息 | 租户配置的"排班信息"场景 | L1 |
| 查询加班信息 | 租户配置的"加班信息"场景 | L1（本人）/ L2（他人） |
| 查询公出信息 | 租户配置的"公出信息"场景 | L1 |
| 查询出差信息 | 租户配置的"出差信息"场景 | L1 |

### 假期类

| 场景 | 对应北森查询场景 | 敏感等级 |
|------|---------------|:------:|
| 查询假期余额 | 租户配置的"假期余额"场景 | L1 |
| 查询休假记录 | 租户配置的"休假记录"场景 | L1 |
| 查询调休假余额 | 租户配置的"调休余额"场景 | L1 |

> 实际查询场景名称由租户在后台配置决定，Agent 必须通过 `SceneTool` 动态获取，不可硬编码。

## 执行原则

- 所有查询走 beisen-data-query 流水线，Agent 按 6 步流程执行
- 默认查询当前用户自己的数据（员工字段 value=`"当前用户"`）
- 查询团队成员考勤时，员工字段 value 不传（走团队查询）
- 时间参数按 beisen-data-query 的日期转换规则处理
- 考勤记录建议初始范围不超过 30 天，范围过大时提示用户缩小范围
- 查询他人考勤记录（L2 敏感数据）时，仅展示摘要，不回显原始 JSON
- 考勤数据中的异常记录重点展示，正常记录一笔带过

## 参数提取要点

- 员工字段：查自己 → `"当前用户"`；查他人 → 具体人名；查团队 → 不传
- 日期字段：用户提及时间时按规则转换（如"本月" → `2026/08/01-2026/08/31`），未提及时不传
- 选项字段：如假期类型（年假/事假/病假等），从 `dataSourceItems` 匹配，value 填 id
- 详细提取规则见 [../beisen-data-query/references/business-rules.md](../beisen-data-query/references/business-rules.md)

## Playbook 案例

### 案例 1：查询本人假期余额

用户问："我还有多少年假？"

执行步骤：
1. 前置检查
2. 按 beisen-data-query 6 步流水线执行
3. SceneTool 匹配"假期余额"场景
4. SearchFormTool 获取字段，员工字段 value=`"当前用户"`，假期类型匹配"年假"
5. BusinessDataTool 查询数据
6. 生成回答："你当前年假余额为X天"

### 案例 2：查询下属考勤异常

用户问："李白本月有没有考勤异常？"

执行步骤：
1. 前置检查
2. 按 6 步流水线执行，员工字段 value=`"李白"`，日期字段 value=`"2026/08/01-2026/08/31"`
3. 查询结果为 L2 敏感数据（他人考勤），展示摘要
4. 如有异常，重点展示异常日期和原因

### 案例 3：查询团队工时

用户问："我的团队本月工时情况"

执行步骤：
1. 按 6 步流水线执行，员工字段不传（团队查询）
2. 逐人展示工时，不做求和汇总
3. 展示关联菜单

## 详细参考

- [references/attendance.md](references/attendance.md)：考勤类场景说明
- [references/leave.md](references/leave.md)：假期类场景说明
- [../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)：通用查询流水线完整步骤
- [../beisen-data-query/references/business-rules.md](../beisen-data-query/references/business-rules.md)：参数提取规则与输出格式要求

## 不在本 Skill 范围

- 业务操作意图（请假、出差、休假、加班、公出等申请/提交类操作）→ [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 考勤制度/政策查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)
- 员工个人档案信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
