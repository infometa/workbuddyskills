# 创建和管理定时任务

使用 `lovrabet schedule` 校验、创建、查看、立即运行和删除当前应用的定时任务。定时任务到点无人值守自动执行，创建前必须先通过「检查任务能否无人值守完整执行」。

## 准备定时任务

开始前确认：

- 当前 AccessKey 对目标应用有权限。
- `--app`、`--appcode` 或当前工作目录指向正确应用。
- 时间统一使用 UTC。
- 使用 `--model` 选择执行模型；默认 `deepseek-v4-flash-0731`，也可显式选择 `kimi/k3` 或 `deepseek-v4-pro-0813`。
- prompt 是完整、可重复执行的任务说明，不依赖当前对话中的临时上下文。
- prompt 不包含 AccessKey、密码或其他明文凭证。
- 任务的完整执行流程已通过「检查任务能否无人值守完整执行」，所需能力全部在 `{read}` 集合内。

定时任务分为：

- `CRON`：按五段 UTC cron 表达式重复执行。
- `ONCE`：在一个 UTC 时间执行一次。

五段 cron 的顺序是：

```text
minute hour day-of-month month day-of-week
```

支持数字、`*`、范围、列表和 step。不要使用秒字段、月份英文名或星期英文名。

## 检查任务能否无人值守完整执行

定时任务到点自动执行，没有用户在场确认、审批或补充信息；流程走到需要人工的步骤时无法继续，整次执行会失败。创建前必须确认：任务的完整执行流程可以由当前 CLI 标记为 `risk: "read"` 的能力完成。下文把 `lovrabet schema` 中 `risk == "read"` 的完整命令集合称为 `{read}` 能力集合。

`schedule validate` 只校验字段、时间、模型和 prompt 格式，不检查任务的能力依赖，不能替代本检查。

### 获取 `{read}` 能力集合

```bash
lovrabet schema --format compress --jq '[.data.services[] as $s | $s.commands[] | select(.risk == "read") | {service: $s.service, command}]'
```

- 同时记录同一输出中的 `cli.version` 和 `schemaVersion`，作为本次判断的依据。不同环境安装的 CLI 版本可能不同；不沿用其他环境的结论，不把某个版本的命令数量或清单当成固定事实。
- 过滤结果是完整可选范围，由任务需求选择必要子集；不要求任务用上全部命令，也不得自行缩小成“查询类命令”或固定的小清单。
- 按 `risk` 标签判断，不按命令名或副作用直觉判断：`skill install`、`skill create`、`file upload`、`sql exec`、`bff exec` 当前都标记为 `read`，不会因为会安装文件、执行脚本或产生业务产物而被排除；`schedule delete` 是 `high-risk-write`，不会因为用途是清理而被当作 `read`。
- 命令缺失 `risk`、值未知，或 schema 无法读取时，该命令按不可用处理，不猜为 `read`；未完成本检查前不进入创建。
- 需要某个命令的参数、认证或适用范围时，读取完整 schema 输出和该命令的 `--help`，不凭记忆推断。
- `{read}` 标签只界定无人值守任务的可选工具集合，不替代身份、RBAC、应用权限、业务授权和可信契约验证；`sql exec`、`bff exec` 等仍须遵循 SKILL.md 的标识来源与契约要求。

### 审查完整任务流程

对照 prompt 审查任务的完整执行流程，覆盖所有条件分支、异常与降级处理、到期或超时处理、通知、清理和自停步骤；不能只审查正常分支，也不能只看任务标题。仅某个条件分支需要的能力不合格时，同样判为不能创建。

任务流程不得依赖：

- `write` 或 `high-risk-write` 命令，例如 `schedule delete`、`schedule run`、`data delete`、重新创建计划或其他带 `--yes` 的管理执行。
- 人工确认、人工审批或在场用户补充数据。
- 创建时对话中的临时上下文。

不满足时，创建前向用户指出具体能力缺口——哪个步骤需要什么能力、为什么当前 `{read}` 集合没有——并停止创建。不接受“创建时用户确认过一次，未来自动执行均已授权”的推断，也不通过删除约束、省略用户要求或换一种描述，把不能完整执行的任务包装成可创建。

### 创建行为与自动执行行为

创建 schedule 本身是需要用户确认的 `high-risk-write` 管理操作，沿用本工作流的 dry-run 与确认流程；这不禁止用户正常创建合格的 `{read}` 任务。本节约束的是计划将来自动运行的任务内容，不是创建动作本身。

### 计划生命周期需求

用户要求“条件满足后自动停止”“到期自动清理”“自动删除本计划”这类行为时，先核对当前 CLI 是否提供可用的计划生命周期能力。当前 schedule 只有 validate/create/list/detail/run/delete，没有条件停用、到期清理或自动停用命令。

没有可用能力时，如实说明该完整需求当前不支持，并提出需要用户确认的替代方案，例如：计划持续运行并按周期报告结果，由用户确认后删除计划；或改用单次 `ONCE` 任务表达一次性检查。不要把删除或重建计划等管理动作写进运行 prompt，交给执行中的任务自行处理。

### 检查的边界

本检查是创建前的决策指引，不是运行时强制；不要向用户声称本工作流能在技术上保证自动执行时永远不会调用非 `read` 命令。执行结果仍按「检查完成结果」回读与披露。

## 校验周期任务

先校验输入，不创建计划：

```bash
lovrabet schedule validate \
  --kind CRON \
  --cron '0 9 * * 1-5' \
  --title '工作日销售日报' \
  --prompt '汇总昨日销售数据并生成报告' \
  --model deepseek-v4-flash-0731
```

检查返回的 `kind`、`timezone`、`cron`、`title`、`prompt` 和 `model`。

## 校验单次任务

`--scheduled-at` 使用 canonical UTC ISO datetime，至少晚于当前时间 60 秒，最多晚于当前时间 365 天：

```bash
lovrabet schedule validate \
  --kind ONCE \
  --scheduled-at '2026-08-01T01:30:00.000Z' \
  --title '发布前检查' \
  --prompt '检查当前应用的发布资料' \
  --model kimi/k3
```

不要同时传 `--cron` 和 `--scheduled-at`。

## 创建定时任务

只有「检查任务能否无人值守完整执行」通过后才进入本节。

先预览：

```bash
lovrabet schedule create \
  --kind CRON \
  --cron '0 9 * * 1-5' \
  --title '工作日销售日报' \
  --prompt '汇总昨日销售数据并生成报告' \
  --model deepseek-v4-flash-0731 \
  --dry-run
```

把以下信息交给用户确认：

- 应用
- UTC 时间或 cron
- 是否重复执行
- 标题
- 完整 prompt
- model

用户明确确认后执行：

```bash
lovrabet schedule create \
  --kind CRON \
  --cron '0 9 * * 1-5' \
  --title '工作日销售日报' \
  --prompt '汇总昨日销售数据并生成报告' \
  --model deepseek-v4-flash-0731 \
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

- 创建前已记录能力检查结论：使用的 `cli.version`、`schemaVersion` 和判断结果。
- create 返回真实 `scheduleId`。
- list 或 detail 能查到新计划。
- run 返回 `taskId` 时只报告已进入队列。
- delete 后列表不再包含该计划。
- 没有把删除计划误写成取消既有 Task。
