# 运营数据、用量、审计与模型目录

都是只读命令，唯一的例外是 `corp assistant set`。时间窗口用 `--from` / `--to`，可以写 `YYYY-MM-DD`（按北京时间）、ISO 时间或 Unix 秒；不传就是最近 7 天。

```bash
adp metrics overview --space-id <id> --format json      # 工作台活跃人数、会话数、运行时长，以及环比
adp metrics trend --space-id <id> --from 2026-10-01      # 每天的运行时长
adp metrics top-users --space-id <id> --limit 10         # 按任务数排行的用户；超过 --limit 时 truncated=true
adp metrics detail --space-id <id> [--pu]                # 每个用户的统计；加 --pu 看每次运行的 PU 和 token
adp metrics app --app-id <id> --space-id <id>            # 单个应用的调用量、成功率、耗时、回复类型分布
adp metrics export --space-id <id> --yes                 # 只提交导出；文件发到控制台通知，没有可轮询的任务

adp billing resources --space-id <id>                    # 套餐和增值包的总量与已用量
adp billing summary|detail|consumption|concurrency --space-id <id> [--app-id <id>]

adp audit meta                                            # --action / --biz 可取的值
adp audit list --space-id <id> --action delete --limit 20 # 最新的在前；游标分页：truncated=true 时按 next_actions 带 --cursor 续翻，传 --page 报 UsageError
adp account list --space-id <id>

adp corp assistant get --space-id <id>                    # 工作台设置：长期记忆、自定义指令、默认模型
adp portal get                                            # 企业门户的状态和子域名

adp models --space-id <id> [--scene 18] --fields modelId,name   # 空间可用模型列表；--scene 18 只列 Claw 模式可用的
adp models get --model-id TCADP/glm-5.1                   # 完整模型卡片
adp models developers --space-id <id> [--limit 10 --page 0]   # 列表 envelope：items / truncated / total；--page 从 0 开始
adp models mappings --model TCADP/glm-5.1                 # 已下线的模型名现在会路由到哪个模型

adp workspace credential --workspace-id <id> [--reveal]   # 会话沙箱的存储凭证，默认打码
adp workspace download-url --workspace-id <id> --path /workdir/x.md [--reveal]
```

- `billing summary|detail|consumption|concurrency` 和 `account list` 需要企业管理员授予报表权限，否则返回 `PermissionDenied`。这时告诉用户去找管理员，不要换账号重试。
- PU 消耗有两个来源：工作台按次运行的 PU 用 `metrics detail --pu`；整个空间或单个应用的资源消耗（含 PU）用 `billing consumption`（需要报表权限）。`metrics overview`、`trend`、`top-users` 只统计工作台的任务和会话，不含 PU。
- `--action` / `--biz` 必须是 `adp audit meta` 里的 key（如 `modify`、`app`），写中文名或拼错会直接报参数错误。
- `usage` 和 `billing … --app-id` 遇到 450002 时，CLI 会先查应用：应用不存在报 `AppNotFound`，存在才是 `PermissionDenied`。
- 不存在的资源统一报 not_found（退出码 3）并带专门的 code：应用 450011「应用不存在」→ `AppNotFound`，插件 460010「插件不存在」→ `PluginNotFound`，技能 450002「技能不存在」→ `SkillNotFound`；next_actions 指向对应的 list 命令。460010 也用于「会话不存在或没有操作权限」，报 `ConversationNotFound` / not_found。其他映射：450403「ErrAppNotFound」、460004「机器人不存在」→ `AppNotFound`；450151「标签标准词不存在」→ `KbLabelNotFound`；450013「QA不存在」→ `KbQaNotFound`；471044「ErrConflictQuestionNotFound」→ `KbQaConflictNotFound`；440014「生成任务不存在」→ `GuidelineTaskNotFound`；450160「QA无法编辑」→ `KbQaNotEditable`（conflict，可重试，问答还在审核/学习中）。CLI 改写过的错误（如 `TimerTaskNotFound`、`CredentialNotFound`）在 message 末尾括号里保留平台原始码。
- 删除不存在的 ID 时，平台的删除接口常常照样返回成功，所以 CLI 先只读地查一遍：`kb doc/file/qa/label delete`、`channel delete`、`synonym delete`、`agent delete` 有任何一个 ID 不存在（`--dry-run` 也先查）就报对应的 `KbDocNotFound` / `KbQaNotFound` / `KbLabelNotFound` / `ChannelNotFound` / `SynonymNotFound` / `AgentNotFound`（退出码 3），一条都不删。`plugin delete` 对不存在的插件平台报 460001 FailedOperation，带 `--space-id`（或 adp.jsonc 有空间）时 CLI 用 DescribePlugin 确认后报 `PluginNotFound`。`guideline delete` 同样先逐个查：任何一个 ID 不存在就报 `GuidelineNotFound`（退出码 3），一条都不删；ID 都存在但平台仍拒绝时才是 `GuidelineBatchFailed`。
- 数字 ID 在本地统一校验，所有命令（含 `--dry-run`）都一样：`--app-id`、`--kb-id`、`--channel-id`、`--release-id`，以及 `adp kb` 下的 `--qa-id`、`--doc-id`、`--label-id`。传名称或 `doc-1` 这类值报 `InvalidIdFormat`（退出码 2），不发请求，next_actions 指向能查到数字 ID 的列表命令。逗号分隔或重复传的每一项都要是数字。
- 只接受一个 ID 的参数（`--agent-id`、`--plugin-id`、`--app-id` 等）传了逗号或重复传，本地报 `UsageError`（退出码 2），不会拼成一个错误的 ID；要处理多个就逐个执行。`kb doc delete` / `kb file delete` 的 `--doc-id` 可以重复传或逗号分隔，删除是全有或全无。
- 删除后再读：`kb doc get` / `kb file get` 对已删除的文档平台仍返回成功但内容为空，CLI 报 `KbDocNotFound`（退出码 3）；`kb doc retry` 遇到已删除文档（450202）同样报 `KbDocNotFound`，next_action 是 `adp kb doc list --kb-id <id>`。`agent get` 对已删除的智能体平台报 `550005 数据不存在`，CLI 报 `AgentNotFound`（退出码 3）。
- not_found 错误的 message 会去掉平台附带的「请重试」（例如「插件不存在，请重试」），重试找不回已删除的资源。
- 失败时的 next_actions：「without --yes」类用法错误给出加上 `--yes` 的原命令（会真的写入）；`PermissionDenied`（450002）给出 `adp whoami --format json`，请空间管理员授权；可重试错误（如 450003）第一条一定是原命令（带上从 adp.jsonc 解析出的 `--app-id`），后面可能再附一条查 ID 的命令；只有参数/用法错误才回退到 `adp schema`。缺少 `--space-id` / `--app-id` 又没有 adp.jsonc 时，给出能查到这个 ID 的命令（`--all-spaces`、`adp space list`、`adp app list --all-spaces`）。
- 写命令 `--dry-run` 成功且没有别的建议时，next_action 是去掉 `--dry-run` 的同一条命令（需要确认的加 `--yes`）。
- `kb search` 结果带 `truncated`，没有 `total`（命中数等于 `--limit` / `--recall-count` 时 truncated=true；接口不能分页，不接受 `--page`，续查是加大 `--limit`）；`skill refs` 带 `total` / `truncated`；`metrics top-users` 是 `items` + `total` / `truncated` / `page` / `pageSize`，续查保留 `--limit`、`--page` 加一（排名一次取回，本地切页）。`agent list` 每行都有 `name`。`agent changed --since 0` 表示从头算。`--variable-id` 只接受一个 ID。
- 缺 `--space-id` / `--app-id` 的用法错误，next_action 是 `adp space list` / `adp app list --all-spaces`，不是 schema。`conversation messages` 对 `adp chat` 的会话（type 5）报 `ConversationNotFound`，next_action 指向 `adp tail`。
- `app key list`、`agent changed`、`models developers` 返回标准列表 envelope，支持 `--limit` / `--page`；列表续取的 next_action 保留原命令的全部参数（含 `--fields`、`--env`、`--profile`、`--config`）。
- `channel get` 的报错按哪个 id 不对而不同（实测）：应用 id 不存在时平台返回 450003「无坐席权限」，CLI 报 `PermissionDenied`，和真正缺席位同一个码，先用 `app get` 确认应用存在再找管理员；应用存在而渠道 id 不存在时是 4506001「渠道不存在」→ `ChannelNotFound`（next_actions 指向 `channel list`）；`--channel-id 0` 是 450057「参数错误」；非数字 id 报 `InvalidIdFormat`。
- `next_actions[].command` 都可以原样执行：不含 `<占位符>` 和说明文字，会带上你传过或从 adp.jsonc 解析出的 `--space-id` / `--app-id` / `--agent-id` / `--kb-id`。需要你补的值写在 `reason` 里。
- `channel list|create` 偶尔返回 450003（无席位权限）后重试又成功：CLI 报 `PermissionDenied`，`retryable: true`，提示可能是瞬时的。重试一次；持续出现才找空间管理员分配席位。
- 只读命令加 `--dry-run` 无论成功还是失败都会带 `DryRunIgnored` warning（例如没有报表权限的 `billing summary`）。
- `docs list` 一次拿到整个目录，结果带 `total`，`truncated` 按 `items.length < total` 计算。
- `trigger get|list` 的 `status` 是数字；`agent limits` 的字段是 camelCase（如 `agentToolLimit`）。
- 列表的续页 next_actions（`--limit` / `--page`）会带上你传过的范围参数（`--space-id`、`--app-id`、`--kb-id`、`--query` 等），直接照抄执行即可。
- `corp assistant set` 会改动该空间所有成员的工作台。执行前先 `get` 一次，把要改的字段告诉用户，得到同意后再加 `--yes`。
- `workspaceId` 来自 `adp conversation get` 的返回结果，只有带沙箱的会话才有。`workspace credential` 对不存在的工作区、或 `--type` / `--app-id` 与会话不符时报 `WorkspaceNotFound`。凭证和下载链接默认打码；只有用户需要把它们交给别的工具时才加 `--reveal`，而且不要在对话里转述明文。
- 席位分配、资源包明细、已消耗模型这几项，目前平台后端还没开放，CLI 也没有对应命令。开通门户在控制台完成。
