---
name: erhao-hr-attendance
description: "二号人事部考勤域：月度考勤汇总与每日打卡状态、打卡/补卡/请假/外出/出差/加班明细、排班与假期类型/余额查询。"
description_zh: "考勤域技能：考勤汇总与明细、打卡与补卡、请假/外出/出差/加班记录、排班、假期类型与假期余额（仅当月及前 6 个月）；含假期类型、打卡来源、补卡数据来源、外出/出差/加班等词表口径。"
description_en: "Attendance domain: monthly summaries and daily card status, card/revamp/leave/outing/business-trip/overtime records, schedules, vacation types and vacation balances (current month plus the previous six months)."
version: 0.1.9
author: 二号人事部
---

# 二号人事部 · 考勤域

> 机制、返回形态与默认查询口径见共享技能 `erhao-hr`；本技能只讲「场景 → 工具 → 本域口径」。

## 场景 → 工具

| 场景 | 工具 | 本域口径 |
|---|---|---|
| 月度考勤汇总 | `attendance_month_result` | 按人按月的汇总结果；`one_codes` **必须非空**，否则上游报「参数异常」 |
| 月度汇总表头 | `attendance_month_result_headers` | 汇总列的中文含义 |
| 月视图每日打卡状态 | `attendance_month_card` | 月内每日状态（明细里的 `time` 为状态码） |
| 月视图表头 | `attendance_month_card_headers` | 列含义（字段中文名） |
| 打卡记录 | `attendance_card_record` | 原始打卡流水 |
| 补卡记录 | `attendance_revamp_record` | 补卡来源与审批信息 |
| 请假记录 | `attendance_leave_record` | 假期类型与请假时长 |
| 外出记录 | `attendance_outing` | 外勤（外出）明细 |
| 出差记录 | `attendance_business_trip` | 外勤（出差）明细 |
| 加班记录 | `attendance_overtime` | 加班时长与加班来源 |
| 排班 | `attendance_schedule` | 排班计划 |
| 假期类型清单 | `attendance_vacation_type_list` | 假期类型码值清单 |
| 假期余额表头 | `attendance_vacation_balance_headers` | 余额列含义 |
| 假期余额 | `attendance_vacation_balance` | **仅支持当月及前 6 个月** |

## 域特有口径

- 考勤状态码（明细表每日 `time` 的 0–16）**不在连接器字典中** —— 该枚举在机器源里没有常量。字典只收录**词表型枚举**（假期类型、打卡来源、补卡数据来源、外出/出差/加班 `source_type` 等），其码值见 `../erhao-hr/references/data-dictionary.md`。**不要**去字典查状态码，也不要凭记忆写码值。
- **请假**可按 `vacation_type` 的码值或名称匹配；假期类型码值以字典为准。
- **假期余额的时间窗**：仅支持**当月及前 6 个月**；超出该范围时改用请假记录（`attendance_leave_record`）统计。
- `attendance_month_result` 的 `one_codes` **必须非空**（传空上游会报「参数异常」）。
- **`source_type` 在不同接口上是不同枚举**（请假 / 外出 / 出差 / 加班），**禁止混用同一套取值**；
  字典收录了外出 / 出差 / 加班三套，请假接口的取值不在字典中——差异登记见
  `../erhao-hr/references/enum-conflicts.md`。
- **时长单位**：加班时长字段为系统定义的 `(分钟)`；外勤（外出 / 出差）时长为自定义的 `(小时)`，两者不可直接相加比较。

## 引用

返回形态、分页拉全量、默认查询口径与错误恢复见共享技能 `erhao-hr`。
