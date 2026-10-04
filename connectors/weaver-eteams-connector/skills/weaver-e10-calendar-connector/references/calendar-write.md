# 创建 / 更新 / 删除日程（写操作）

## 何时使用

创建日程、修改日程、删除日程时使用。全部为**高风险写操作**，必须走 prepare→apply 确认协议。

## operation 清单

| 用途 | prepare | apply |
| --- | --- | --- |
| 创建日程 | `calendar.create.prepare` | `calendar.create.apply` |
| 更新日程（全量覆盖） | `calendar.update.prepare` | `calendar.update.apply` |
| 删除日程（不可逆） | `calendar.delete.prepare` | `calendar.delete.apply` |

## 写操作确认协议

1. `prepare` 只归一化输入、补默认值、查当前数据（更新/删除时）、生成预览和 continuation，**不写入**。
2. 向用户摘要目标、差异、风险和确认条件。
3. 用户明确确认后调用 `apply`，必须带 `confirm=true` 和 prepare 返回的 continuation。
4. `apply` 校验 session、目标 ID 和字段指纹未变化；网络中断返回 `partial/write_uncertain`，**禁止自动重试**，先做只读回查。

continuation 绑定当前登录环境与操作人，10 分钟有效。租户或账号变化触发 `context_mismatch`，字段与 prepare 快照不一致触发 `target_changed`，均需重新 `prepare`。

## 创建日程

必填 `agn_name`、`start_time`、`agn_type`、`priority`；`end_time` 缺省自动 `start_time + 1 小时`；`participants` 缺省自动带当前操作人。

第一步 prepare（Windows PowerShell）：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.create.prepare --input-json '{"agn_name":"项目周会","start_time":"2026-08-15 09:00","agn_type":"1147539906291523593","priority":"1147539666016624641"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"agn_name":"项目周会","start_time":"2026-08-15 09:00","agn_type":"1147539906291523593","priority":"1147539666016624641"}' | weaver-work-cli --profile eteams --json calendar run calendar.create.prepare --input -
```

第二步 apply（把 `--input-json` 换成 prepare 返回的 continuation，并加 `confirm`）：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.create.apply --input-json '{"agn_name":"项目周会","start_time":"2026-08-15 09:00","agn_type":"1147539906291523593","priority":"1147539666016624641","confirm":true,"continuation":"<prepare返回的token>"}'
```

## 更新日程（全量覆盖）

`calendar.update.prepare` 先查当前详情再合并用户修改。只传 `id` 加要改的字段即可，未传字段保留原值。

第一步 prepare：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.update.prepare --input-json '{"id":"1304552516098269190","place":"B栋5楼会议室","start_time":"2026-08-15 14:00"}'
```

第二步 apply：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.update.apply --input-json '{"id":"1304552516098269190","place":"B栋5楼会议室","start_time":"2026-08-15 14:00","confirm":true,"continuation":"<prepare返回的token>"}'
```

## 删除日程（不可逆）

第一步 prepare：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.delete.prepare --input-json '{"id":"1304552516098269190"}'
```

第二步 apply：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.delete.apply --input-json '{"id":"1304552516098269190","confirm":true,"continuation":"<prepare返回的token>"}'
```

## 字段说明（创建/更新 mainTable）

- `agn_name`（String，必填）：日程名称。
- `start_time`/`end_time`（Date，`yyyy-MM-dd HH:mm`）：起止时间。
- `participants`（人员 ID 字符串，多个逗号分隔）：参与人。
- `agn_type`/`priority`（选项 ID）：日程类型/紧急程度，先查字典。
- Switch 字段 `all_day`/`remind`/`part_receipt`：数字 `0`/`1`，禁止布尔值。
- 提醒：`start_reminder`/`end_reminder`（`NOW`/`M5`/`M15`/`H1`/`D1`/`CUSTOM`）、`remind_type`（`system`/`message`/`email`）。
- 重复：`repeat_type`（`NONE`/`D1`/`W1`/`W2`/`M1`/`CUSTOM`）、`repeat_custom_type`（`D`/`W`/`M`）、`repeat_custom_cycle`、`repeat_week_unit`（`MO`~`SU`）、`repeat_month_unit`（`1`~`31`）、`repeat_end_type`（`0`/`1`/`2`）、`repeat_end_date`、`repeat_end_num`。

## 注意

- 写操作请求带 `Content-Type: application/json; charset=utf-8`，中文字段（`agn_name`/`agn_desc`/`place`）按 UTF-8 写入，由 CLI 自动处理。
- 参与人姓名 → 人员 ID 交 weaver-e10-hrm-connector 解析；类型/紧急程度名称 → 选项 ID 先查字典。
- 删除不可逆，务必先 prepare 展示日程详情并获得用户明确确认。

## 失败处理

- `confirmation.required`：`apply` 未带 `confirm=true`。
- `continuation_invalid` / `continuation_expired` / `continuation_mismatch`：continuation 无效/过期/不匹配，重新 prepare。
- `target_changed`：字段与 prepare 快照不一致，重新 prepare。
- `partial/write_uncertain`：请求已发送但结果不确定，禁止自动重试，用 `calendar.get`/`calendar.list` 回查。
