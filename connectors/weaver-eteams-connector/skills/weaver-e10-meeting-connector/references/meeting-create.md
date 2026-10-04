# 冲突检测与预约会议（prepare/apply 确认链）

## 何时使用

预约会议 / 建会；建会前的会议室 / 参会人 / 属性冲突核查。

## 输入要点

- 必填：`name`、`beginDatetime`、`endDatetime`（`yyyy-MM-dd HH:mm`）。
- `caller`/`contacter` 缺省当前登录用户（后端 contacter 无兜底，CLI 已显式默认）。
- 会议室 `address`、类型 `mtType`、参会人 `hrmMembers`/`orgMembers`（逗号分隔 id 字符串）。
- 周期会议：`repeatType`（1=每天 2=每周 4=每月 5=每年 6=自定义）+ `finishAt`（1=次数 2=日期，**禁止 0=永不**）+ `count`/`until`；`repeatDesc` 缺省按规则自动拼接（如 `每 1 周 周一 周三 周五 重复5次 非工作日正常召开`）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json meeting run meeting.conflict.room --input-json '{"address":"1297870848451641350","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00"}'
weaver-work-cli --profile eteams --json meeting run meeting.conflict.member --input-json '{"hrmids":"100,101","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00"}'
weaver-work-cli --profile eteams --json meeting run meeting.create.prepare --input-json '{"name":"周会","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00","address":"1297870848451641350","hrmMembers":"100,101"}'
# 用户确认后：
weaver-work-cli --profile eteams --json meeting run meeting.create.apply --input-json '{"confirm":true,"continuation":"<prepare返回的continuation>","name":"周会","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00","address":"1297870848451641350","hrmMembers":"100,101"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json meeting run meeting.conflict.room --input-json '{"address":"1297870848451641350","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00"}'
weaver-work-cli --profile eteams --json meeting run meeting.conflict.member --input-json '{"hrmids":"100,101","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00"}'
weaver-work-cli --profile eteams --json meeting run meeting.create.prepare --input-json '{"name":"周会","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00","address":"1297870848451641350","hrmMembers":"100,101"}'
# 用户确认后：
weaver-work-cli --profile eteams --json meeting run meeting.create.apply --input-json '{"confirm":true,"continuation":"<prepare返回的continuation>","name":"周会","beginDatetime":"2026-09-11 09:00","endDatetime":"2026-09-11 10:00","address":"1297870848451641350","hrmMembers":"100,101"}'
```

## 输出处理

- 冲突检测结果 `verdict`：`ok`（无冲突）/ `warn`（可提交但有冲突描述 → warnings 建议换时间/地点）/ `rejected`（`cansub=false`）/ `unknown`（接口未返回 cansub，人工复核）。
- `create.prepare` 返回 `AWAITING_CONFIRMATION` + `preview` + `continuation`（10 分钟有效）；向用户摘要后再 apply。
- `create.apply` 成功返回 `meetingId`；用 `meeting.list` 回读确认。

## 注意

- `prepare` 内部已强制执行冲突检测（接口失败视为冲突、`cansub=false` 直接拒绝），独立冲突 operation 用于"只查不建"场景。
- **命中任何冲突（含仅提醒）一律不得提示绕过冲突直接建会**；`cansub=false` 直接终止。
- `onlyFlowCreate=1` 或周期会议配置了工作流（`repeatWorkFlowBaseIds` 非空）时 `prepare` 主动拒绝（`conflict_rejected`），提示走流程建会。

## 失败处理

- `conflict_rejected` / `conflict_check_failed`：停止建会，不提供绕过选项。
- `target_changed` / `continuation_expired` / `continuation_invalid`：重新 prepare 并再次向用户确认。
- 写请求发出后网络中断 → `partial/write_uncertain`：禁止自动重试，先 `meeting.list` 回查是否已建会。
