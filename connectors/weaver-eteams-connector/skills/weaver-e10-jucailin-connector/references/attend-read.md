# 出勤查询

## 何时使用

查询出勤统计、异常考勤、出勤报表、工作时长、原始打卡记录、外勤轨迹、假期统计，以及为申诉准备参数时使用。全部为只读操作。

## 输入要点

除 `ehr.attend.appeal.formid` 与 `ehr.attend.appeal.calendar` 外，所有列表接口都必须提供 `beginDate` 与 `endDate`，格式 `YYYY-MM-DD`。

| operation | 必填 | 说明 |
| --- | --- | --- |
| `ehr.attend.summary.get` | `beginDate`,`endDate` | 出勤统计、出勤汇总、请假、外勤、假期余额 |
| `ehr.attend.abnormal.list` | `beginDate`,`endDate` | 迟到、早退、缺卡、缺勤、失联明细 |
| `ehr.attend.report.get` | `beginDate`,`endDate` | 出勤汇总报表，返回 `recalcPermission` |
| `ehr.attend.worktime.list` | `beginDate`,`endDate` | 应出勤天数、实际工作时长、加班时长 |
| `ehr.attend.signrecord.list` | `beginDate`,`endDate` | 原始打卡记录，含打卡方式与地点 |
| `ehr.attend.orbit.list` | `beginDate`,`endDate` | 外勤轨迹记录 |
| `ehr.attend.leave.report` | `beginDate`,`endDate` | 假期使用量与剩余额度 |
| `ehr.attend.appeal.formid` | `userId` | 申诉表单 ID 与可申诉状态 |
| `ehr.attend.appeal.calendar` | `date` | 某天考勤日历详情，取 `periodId`/`timecardId` |
| `ehr.attend.appeal.list` | `beginDate`,`endDate` | 申诉记录列表，取申诉 ID |
| `ehr.attend.card.status` | 无 | 当前打卡按钮状态 |

`ehr.attend.abnormal.list` 的 `attendStatus` 取值：`SIGN_IN_LATE`、`SIGN_OUT_EARLY`、`SIGN_IN_ABSENTEEISM`、`SIGN_OUT_ABSENTEEISM`、`ABSENTEEISM`、`LOST`。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.attend.summary.get --input-json '{"beginDate":"2026-03-01","endDate":"2026-03-31"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"beginDate":"2026-03-01","endDate":"2026-03-31"}' | weaver-work-cli --profile eteams --json ehr run ehr.attend.summary.get --input -
```

查询某天的考勤日历详情（为申诉取参数）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.attend.appeal.calendar --input-json '{"date":"2026-03-05"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"date":"2026-03-05"}' | weaver-work-cli --profile eteams --json ehr run ehr.attend.appeal.calendar --input -
```

## 输出处理

- 分页信息在 `meta.page`，含 `pageNo`、`pageSize`、`totalCount`。
- `ehr.attend.summary.get` **不返回 page 对象**，它是对时间范围的聚合统计，不是分页列表。
- 出勤类响应的成功判定走 `success` 布尔；列表数据在 `data.data`。

## 注意

- 日期格式必须是 `YYYY-MM-DD`。`2026-3-1` 这类非补零格式会被 CLI 拒绝。
- `beginDate` 不得晚于 `endDate`，两者必须成对提供。
- 打卡记录与外勤轨迹包含位置信息，属于个人行踪数据。回复用户时只给结论和必要字段，不要原样粘贴完整轨迹 JSON。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户**明确确认**后才继续。

## 失败处理

- `date_range_required`：缺少 `beginDate` 或 `endDate`。
- `date_range_invalid`：日期格式非法，或开始日期晚于结束日期。
- `user_id_invalid`：`appeal.formid` 的 `userId` 不是人员 ID。
- 权限不足时返回业务失败，不要重试；先确认当前账号是否有对应报表的查看权限。
