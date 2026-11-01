# 工作台定时任务（`adp timer`）

智能工作台里的定时任务：按调度把 prompt 发给模型执行。任务属于空间，并且只对创建者可见。它和应用上的触发器（`adp trigger`）不是一回事：用户说「给应用加定时触发」时用 trigger，说「工作台定时任务」时用 timer。

## 创建

```bash
adp timer create --space-id <sp> --name 日报 --prompt "总结今天的行业新闻" --daily 09:30 --format json
adp timer create --space-id <sp> --name 周报 --prompt-file prompt.md --weekly 1@09:00 --weekly 5@17:00
adp timer create --space-id <sp> --name 巡检 --prompt "检查…" --every 2h --start-at 2026-12-01T08:00:00+08:00
adp timer create --space-id <sp> --name 一次性 --prompt "…" --once 2026-12-01T09:00:00+08:00
adp timer create --space-id <sp> --name 工作日 --prompt "…" --cron "0 9 * * 1-5"
adp timer create --space-id <sp> --name 试跑 --prompt "…" --manual
```

- 调度只能选一种。`--weekly` 的格式是 `<1-7>@HH:MM`，1 是周一，可以重复传，最多 7 条。
- `--every` 只接受 `h`（小时）和 `d`（天），并且必须带 `--start-at`。
- 时间写成带时区偏移的 RFC 3339 格式。`--timezone` 默认是 `Asia/Shanghai`。
- `--model` 不传时用平台默认模型，可以先用 `adp models --space-id <sp>` 查可选模型。
- 返回结果里的 `policy` 是平台生成的中文描述，比如「每周一、五 09:30」。

## 管理与运行

以下命令都需要 `--space-id`（不传时读 `adp.jsonc`；没有项目文件时必须显式传）。

```bash
adp timer list --space-id <sp>
adp timer get --space-id <sp> --timer-id <id> --format json
adp timer update --space-id <sp> --timer-id <id> --cron "0 9 * * 1-5"    # 只改传入的字段；--timezone 必须和一个调度参数一起传
adp timer pause|resume --space-id <sp> --timer-id <id>                   # 暂停只停调度
adp timer run --space-id <sp> --timer-id <id> --wait --format json       # 立即执行一次
adp timer runs --space-id <sp> --timer-id <id> [--unread]
adp timer mark-read --space-id <sp> --timer-id <id> [--run-id <id> ...]
adp timer delete --space-id <sp> --timer-id <id> --yes
```

- 应用触发器的运行记录：`adp tail --app-id <id> --trigger-id <id>`（必须带 `--app-id`），单次详情 `adp trigger instance get --instance-id <id>`，返回的 `conversationId` 可以接着用 `adp conversation messages --type 1` 查看。
- 运行日志里 `statusLabel` 的取值有 `pending`、`running`、`succeeded`（`status` 4，`resultCode` 为 `SUCCESS`）、`failed`（5）；没见过的状态码显示成 `status_<n>`，不要自行解读。`triggerLabel` 是 `scheduled` 或 `manual`。
- `resultSummary` 只保留模型的最终回答，前面的思考过程（`</think>` 之前的内容）已去掉。
- 运行失败时，`resultSummary` 里有模型或工具的错误信息，`sessionId` 可以在工作台打开对应会话。
- 报 `TimerTaskNotFound`，说明这个任务不存在、已被删除，或者不是你创建的。
- 结果推送渠道（企微等）目前只能在控制台配置。
