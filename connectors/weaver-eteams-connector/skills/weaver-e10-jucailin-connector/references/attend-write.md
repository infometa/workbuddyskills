# 出勤写操作

## 何时使用

PC 端考勤打卡、创建考勤申诉、处理申诉、触发出勤报表重算时使用。这四类操作会写入业务数据，必须使用 `prepare -> apply` 确认链。

可用 operation：

| 用途 | prepare | apply |
| --- | --- | --- |
| PC 端打卡 | `ehr.attend.card.check.prepare` | `ehr.attend.card.check.apply` |
| 创建申诉 | `ehr.attend.appeal.save.prepare` | `ehr.attend.appeal.save.apply` |
| 处理申诉 | `ehr.attend.appeal.result.prepare` | `ehr.attend.appeal.result.apply` |
| 报表重算 | `ehr.attend.report.recalc.prepare` | `ehr.attend.report.recalc.apply` |

## 输入要点

- **PC 端打卡**：`type` 必填，取值 `CHECKIN`（上班签到）、`CHECKOUT`（下班签退）、`LEAVE`（外出）、`RETURN`（返回）、`CHECKIN_AND_RETURN`、`CHECKOUT_AND_LEAVE`。
- **创建申诉**：`attendDay`（格式 `yyyyMMdd`，注意不是 `yyyy-MM-dd`）、`periodId`、`attendInfoKey`、`appeals` 必填。创建前必须先调 `ehr.attend.appeal.formid` 确认 `stillShowAppeal=true`；`prepare` 传入 `userId` 时会自动完成这层校验。
- **处理申诉**：`id` 与 `handleResult` 必填，`handleResult` 取值 `APPROVE`、`REJECT`、`INVALID`。`suggestion` 最长 500 字。
- **报表重算**：`beginDate`、`endDate` 必填；`onlyEmpIds` 不传表示重算全部人员。

## 命令

第一步，只预览，不写入：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.attend.card.check.prepare --input-json '{"type":"CHECKIN"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"type":"CHECKIN"}' | weaver-work-cli --profile eteams --json ehr run ehr.attend.card.check.prepare --input -
```

第二步，用户确认后才提交：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.attend.card.check.apply --input-json '{"type":"CHECKIN","continuation":"<prepare 返回的 token>","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"type":"CHECKIN","continuation":"<prepare 返回的 token>","confirm":true}' | weaver-work-cli --profile eteams --json ehr run ehr.attend.card.check.apply --input -
```

## 确认链要求

1. `prepare` 只预览和生成 continuation，**不会发送任何写请求**。
2. 向用户摘要目标、影响范围、风险和 continuation 绑定含义（continuation 与当前租户与登录账号绑定，10 分钟有效）。
3. 用户**明确确认**后才调用 `apply`，并传入 `confirm=true` 与 `prepare` 返回的 continuation。
4. `apply` 不可盲目重试。遇到不确定结果先停止，再做一次只读回查。

## 输出处理

- `prepare` 返回 `status=AWAITING_CONFIRMATION`，`preview` 是待确认内容，`continuation` 是提交凭证。
- `apply` 返回 `status=COMPLETE`。报表重算额外返回 `async=true`。
- 回查方式：打卡用 `ehr.attend.card.status` 或 `ehr.attend.signrecord.list`；申诉用 `ehr.attend.appeal.list`；重算用 `ehr.attend.report.get`。

## 注意

- **`card.status` 的语义**：`timecardStatus` 表示**下一次应打的卡**（`CHECKIN` 待打上班卡 / `CHECKOUT` 待打下班卡）。2026-09-04 实测：打卡成功后立即回查，该字段仍返回 `CHECKIN`（服务端存在缓存滞后），**不能用它判断是否已打卡成功**。判断是否成功请回到 `apply` 返回的 `message`（如「签到成功:2026-09-04 14:00:40」），或用 `ehr.attend.signrecord.list` 查当日记录（记录含 `addTime`、`isInRange`、`isInTime`、`sourceType`、`ip` 等字段）。
- **PC 端打卡的前提**：只有当考勤打卡方式开启了「允许 PC 电脑端打卡」时才能成功。若设置为只允许移动端打卡并开启了地图定位校验、WiFi 校验等，智能工具无法获取当前定位位置信息，无法完成打卡——此时必须明确告知用户改用 IM APP 移动端、移动端企业微信等完成打卡，**不要伪造定位、WiFi 或设备凭证重试**。
- 打卡凭证 `sign` 由 CLI 按当前登录态的 `empId`、`ETEAMSID`、`tenantKey` 在 `apply` 阶段实时构造，continuation 中不携带可复用的签名材料。
- 创建申诉会生成审批流程；处理申诉不可逆转。这两类操作必须让用户看清楚对象再确认。
- 报表重算是异步任务，提交成功不代表计算完成；同一时刻仅允许一个重算任务。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户**明确确认**后才继续。

## 失败处理

- `confirmation/required`：缺少 `confirm=true`，必须回到确认链第 2 步。
- `target_changed`：提交参数与 `prepare` 快照不一致，必须重新执行 `prepare`。
- `context_mismatch`：租户或登录账号在 prepare 之后发生变化，必须重新执行 `prepare`。
- `continuation_expired`：continuation 超过 10 分钟，重新执行 `prepare`。
- `appeal_not_allowed`：`stillShowAppeal=false`，当前不可申诉，不要继续提交。
- `partial/write_uncertain`：请求已发出但结果不确定。立即停止，禁止自动重试，先做只读回查再向用户报告。
