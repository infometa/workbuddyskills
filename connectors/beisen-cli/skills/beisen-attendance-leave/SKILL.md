---
name: beisen-attendance-leave
version: 3.2.1
description: "北森考勤休假查询。本 Skill 用于查询数据，包含：假期余额、考勤记录、排班信息、加班、公出、出差、休假记录、调休假余额。所有查询通过 beisen-data-query 通用数据查询流水线执行。当用户询问考勤、打卡、排班、加班、公出、出差、休假、请假、调休、假期余额等考勤休假相关记录时触发。"
author: beisen
display_name: "北森考勤休假"
display_name_en: "Beisen Attendance & Leave"
description_zh: "北森考勤休假查询。本 Skill 用于查询数据，包含：假期余额、考勤记录、排班信息、加班、公出、出差、休假记录、调休假余额。所有查询通过 beisen-data-query 通用数据查询流水线执行。当用户询问考勤、打卡、排班、加班、公出、出差、休假、请假、调休、假期余额等考勤休假相关记录时触发。"
description_en: "Beisen attendance & leave query. This Skill queries data including leave balances, attendance records, shift schedules, overtime, official outings, business trips, leave records, and compensatory-leave balances. All queries run through the beisen-data-query universal data-query pipeline. Trigger when the user asks about attendance, clock-in/out, shifts, overtime, outings, business trips, leave, time off, compensatory leave, leave balances, or other attendance-and-leave records."
category: productivity
requires-skills:
  - beisen-shared
  - beisen-data-query
---

# 考勤休假

**CRITICAL — 开始前 MUST 读取：**
1. **[references/beisen-shared.md](references/beisen-shared.md)** — 连接器与授权、安全规则、写操作门禁
2. **[references/beisen-data-query.md](references/beisen-data-query.md)** — 通用数据查询流水线（本 Skill 所有场景均走此流水线）

## 路由优先级

本 Skill 处理：考勤与休假数据的查询（只读）

不归本 Skill 处理：
- 业务操作意图（"我要请假""我要出差""我要休假""申请加班""帮我请个假"等，即用户要**执行某项操作**而非查询数据）→ [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 员工个人档案信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
- 考勤制度/政策查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)

## 场景清单

以下场景统一按 [beisen-data-query](references/beisen-data-query.md) 的 6 步流水线执行：场景发现 → 场景说明（输出要求与关联菜单）→ 场景字段 → 数据查询 → 生成回答 → 展示关联菜单。

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

> 实际查询场景名称由租户在后台配置决定，Agent 必须通过场景发现工具动态获取，不可硬编码。

## 执行原则

- 所有查询走 beisen-data-query 流水线，Agent 按 6 步流程执行；工具选择与参数格式以连接器工具清单和各工具 inputSchema 为准
- 默认查询当前用户自己的数据；查询团队成员时按流水线的"查询主体与组织范围判定"处理（第一人称+范围词 = 本人权限范围）
- 时间条件仅在用户原文明确提及时间时传入；用户未提及时不传，由后端默认范围决定
- 考勤记录建议初始查询范围不超过 30 天，范围过大时提示用户缩小范围
- 查询他人考勤记录（L2 敏感数据）时，仅展示摘要，不回显原始返回
- 考勤数据中的异常记录重点展示，正常记录一笔带过（异常判断型展示策略见流水线输出规则）

## Playbook 案例

### 案例 1：查询本人假期余额

用户问："我还有多少年假？"

执行步骤：
1. 按 beisen-data-query 6 步流水线执行
2. 场景发现匹配"假期余额"场景
3. 场景字段返回员工、假期类型等筛选字段 → 提取：主体=本人、假期类型=年假（取值按字段说明）
4. 数据查询 → 生成回答："你当前年假余额为X天" → 展示关联菜单

### 案例 2：查询下属考勤异常

用户问："李白本月有没有考勤异常？"

执行步骤：
1. 按 6 步流水线执行：主体=指定人"李白"、时间=本月（起止日期按 schema 格式）
2. 查询结果为 L2 敏感数据（他人考勤），展示摘要
3. 如有异常，重点展示异常日期和原因；无异常直接给结论，不铺全部记录

### 案例 3：查询团队工时

用户问："我的团队本月工时情况"

执行步骤：
1. 按 6 步流水线执行：第一人称+范围词 → 本人权限范围（团队查询）
2. 逐人展示工时，不做求和汇总
3. 展示关联菜单

## 不在本 Skill 范围

- 业务操作意图（请假、出差、休假、加班、公出等申请/提交类操作）→ [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 考勤制度/政策查询 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)
- 员工个人档案信息 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
