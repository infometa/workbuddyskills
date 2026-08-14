# 创建和管理定时任务

使用 `lovrabet schedule` 校验、创建、查看、立即运行和删除当前应用的定时任务。

## 准备定时任务

开始前确认：

- 当前 AccessKey 对目标应用有权限。
- `--app`、`--appcode` 或当前工作目录指向正确应用。
- 时间统一使用 UTC。
- prompt 是完整、可重复执行的任务说明，不依赖当前对话中的临时上下文。
- prompt 不包含 AccessKey、密码或其他明文凭证。

定时任务分为：

- `CRON`：按五段 UTC cron 表达式重复执行。
- `ONCE`：在一个 UTC 时间执行一次。

五段 cron 的顺序是：

```text
minute hour day-of-month month day-of-week
```

支持数字、`*`、范围、列表和 step。不要使用秒字段、月份英文名或星期英文名。

## 校验周期任务

先校验输入，不创建计划：

```bash
lovrabet schedule validate \
  --kind CRON \
  --cron '0 9 * * 1-5' \
  --title '工作日销售日报' \
  --prompt '汇总昨日销售数据并生成报告' \
  --channel auto
```

检查返回的 `kind`、`timezone`、`cron`、`title`、`prompt` 和 `channel`。

## 校验单次任务

`--scheduled-at` 使用 canonical UTC ISO datetime，至少晚于当前时间 60 秒，最多晚于当前时间 365 天：

```bash
lovrabet schedule validate \
  --kind ONCE \
  --scheduled-at '2026-08-01T01:30:00.000Z' \
  --title '发布前检查' \
  --prompt '检查当前应用的发布资料' \
  --channel premium
```

不要同时传 `--cron` 和 `--scheduled-at`。

## 创建定时任务

先预览：

```bash
lovrabet schedule create \
  --kind CRON \
  --cron '0 9 * * 1-5' \
  --title '工作日销售日报' \
  --prompt '汇总昨日销售数据并生成报告' \
  --channel auto \
  --dry-run
```

把以下信息交给用户确认：

- 应用
- UTC 时间或 cron
- 是否重复执行
- 标题
- 完整 prompt
- channel

用户明确确认后执行：

```bash
lovrabet schedule create \
  --kind CRON \
  --cron '0 9 * * 1-5' \
  --title '工作日销售日报' \
  --prompt '汇总昨日销售数据并生成报告' \
  --channel auto \
  --yes
```

只有返回 `scheduleId` 才表示计划创建成功。保存该值，用于详情、立即运行和删除。

## 查看定时任务

按服务端要求分别查看周期或单次计划。查看周期计划第一页：

```bash
lovrabet schedule list --kind CRON --limit 20
```

查看单次计划第一页：

```bash
lovrabet schedule list --kind ONCE --limit 20
```

返回 `nextCursor` 时，把它原样传给下一次查询：

```bash
lovrabet schedule list --kind CRON --limit 20 --cursor '<NEXT_CURSOR>'
```

翻页时必须保持 `--kind` 不变，不要解析、修改或拼接 cursor。

查看详情：

```bash
lovrabet schedule detail --schedule-id <SCHEDULE_ID>
```

list 和 detail 不返回完整 prompt。不要根据详情猜测或恢复创建时的 prompt。

当前没有 update、pause 或 resume 命令。需要修改时，先确认删除旧计划，再创建新计划。

## 立即运行一次

先查看详情并预览：

```bash
lovrabet schedule detail --schedule-id <SCHEDULE_ID>
lovrabet schedule run --schedule-id <SCHEDULE_ID> --dry-run
```

用户明确确认后执行：

```bash
lovrabet schedule run --schedule-id <SCHEDULE_ID> --yes
```

返回 `taskId` 和 `status=QUEUED` 只表示 Task 已接收，不表示已经完成。保留 `taskId`；
无法从当前 CLI 核对终态时，明确说明“已进入队列，执行结果尚未验证”，不要声称任务成功。

## 删除定时任务

先查看目标并预览：

```bash
lovrabet schedule detail --schedule-id <SCHEDULE_ID>
lovrabet schedule delete --schedule-id <SCHEDULE_ID> --dry-run
```

用户明确确认后执行：

```bash
lovrabet schedule delete --schedule-id <SCHEDULE_ID> --yes
```

删除只停止未来触发，不会取消已经创建的 Task。不要把“计划已删除”表述为“正在执行的
Task 已取消”。

## 处理失败

| `errorCode` | 处理 |
| --- | --- |
| `UNAUTHORIZED` | 重新确认 AccessKey |
| `ACCESS_KEY_SCOPE_MISMATCH` | 停止操作，确认目标应用权限 |
| `SCHEDULE_NOT_FOUND` | 刷新列表；ONCE 计划可能已经执行并消失 |
| `SCHEDULE_CONFLICT` | 重新读取列表和详情后再判断 |
| `SCHEDULE_INPUT_INVALID` | 修正 UTC 时间、cron 或字段组合 |
| `ACCESS_KEY_AUTH_UNAVAILABLE` | 保留输入，稍后重试 |
| `SCHEDULE_CONTROL_UNAVAILABLE` | 不伪造成功结果，稍后重试 |

## 检查完成结果

- create 返回真实 `scheduleId`。
- list 或 detail 能查到新计划。
- run 返回 `taskId` 时只报告已进入队列。
- delete 后列表不再包含该计划。
- 没有把删除计划误写成取消既有 Task。
