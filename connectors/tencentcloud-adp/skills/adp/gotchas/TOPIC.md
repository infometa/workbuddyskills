# ADP gotchas (CLI)

If this file disagrees with `adp docs get`, trust the official markdown.

## Draft vs release

Platform has two domains: **draft** (owner only) and **release** (end users). `ModifyAgent` / `ModifyApp` touch draft. `CreateRelease` (`adp deploy`) promotes to release.

| Surface | After an edit |
| --- | --- |
| `adp deploy` | draft then `CreateRelease` |
| `adp deploy --dry-run` | preview only: `preview` / `previewTotal` are the remote draft's pending changes (same list as `adp release preview`); local `adp.jsonc` edits are pushed only by the real deploy |
| `adp dev` | draft only; does not chat |
| `adp chat` | published app (AppKey). Deploy at least once. |
| `adp chat --dry-run` | validates `app_id` in `adp.jsonc`; does not call C-end SSE |

## `app_mode`

| Value | Mode | Agent `skill_ids` |
| ---: | --- | --- |
| 1 | Standard | ignored / rejected |
| 2 | Multi-Agent (`adp init` default) | rejected |
| 3 | Single workflow | ignored / rejected |
| 4 | Claw | supported |

Claw cannot switch to or from 1/2/3 on the same app. Create a new app.

`CreateAgent` is **Claw-only**. Standard (`1`) and single-workflow (`3`) have no agent. Multi-Agent (`2`) may bind an existing agent from `DescribeAgentSummaryList`. Standard instructions live in `role_description`, not only `instructions.md`.

`app_mode` is not Multi-Agent **collaboration**. That is `mode.multi_agent.collaboration_mode` (1 free-handoff / 2 workflow / 3 Plan-and-Execute).

Full table: [../references/app-modes.md](../references/app-modes.md).

## Catalog vs mounts

- `adp plugin` / `adp skill` are **space catalog** CRUD. `adp skill create` takes `--file` (local zip) or `--file-url` (existing COS path), not both. `--name` is a lowercase identifier; Chinese is `--display-name`. The zip needs a root `SKILL.md` with YAML front matter `name` and `description` (else 450020). After create, a ~2 minute security scan makes `skill release` answer 450028 and `skill delete` answer 450063: wait and retry, see [../references/platform-skills.md](../references/platform-skills.md).
- `adp plugin create` has two paths: MCP (`--mcp-url --icon-url --name`) or API (`--from-config plugin.jsonc`).
  - MCP: the platform connects to `--mcp-url` at create time, so it must be a real, reachable SSE or Streamable HTTP endpoint (`--mcp-transport 1`). A placeholder such as `https://example.com/sse` fails with `460030` (HTTP 404). Ask the user for their server URL.
  - API: `CreatePlugin` takes nested `Profile` / `Config` / `ToolList`. `Profile.IconUrl` is required. `cdn.xiaowei.qq.com` icons always work; publicly readable COS image URLs were also accepted in live tests. If ADP answers `460007`, switch to a `cdn.xiaowei.qq.com` icon.
  - `plugin.jsonc` keys are snake_case and strict; an unknown key is a `UsageError`, never silently dropped. Top level: `name`, `description`, `author`, `icon_url`, `plugin_class`, `auth`, `tools`. Each tool: `name`, `description`, `method`, `url`, `query` / `header` / `body` (request parameters — there is no `inputs`), `outputs`, `example`, `access_mode`. Each parameter: `name`, `type` (`string`, `int`, `float`, `bool`, `object`, `array<string>` …), `description`, `required`, `default`, `sub_params`.
  - API-key auth: `"auth": { "location": "header" | "query", "param_name": "X-Api-Key", "param_value": "${MY_KEY}" }`. Keep the secret in an env var. `plugin.jsonc` cannot declare OAuth 2.0; create OAuth plugins in the console, then authorize with `adp credential authorize` (see references/credentials.md).
  - `adp plugin update` needs the space (`--space-id` or `adp.jsonc`) because it reads the plugin first: `--name` / `--description` alone keep the icon and other profile fields, and `PluginVersion` becomes current+1.
  - `adp plugin update --from-config` carries `ToolId` over by tool name; a tool without its id is recreated and silently unbinds agents.
- `adp trigger create` needs a published app (`adp deploy`) plus `--cron` and `--prompt` for the scheduled+instruction path.
- `adp trigger update` needs the app id (`--app-id` or `adp.jsonc`) and at least one field; only the fields you pass are changed.
- `adp channel create` needs the credential block for its `--channel-type` in `--spec-json`, e.g. 10016 `{"Lark":{"AppId":"cli_xxx","AppSecret":"xxx"}}`, 10014 `{"WecomRobot":{"Websocket":{"BotId":"...","BotSecret":"..."}}}`. 10015 is C-end only (`--scene 1`) and needs both `--user-id` (any non-empty owner id) and `--agent-id` (the published Claw app's `agent_id` from `adp.jsonc`); pass `--spec-json '{"WechatClawBot":{}}'` and scan the returned `qrcodeUrl` within 120 s. C-end channels are not listed until the QR code is scanned, and `channel get` on an unscanned one returns `pendingAuthorization: true` (ADP answers `ChannelId 0` with only the QR session). ADP keeps returning that session even after `channel delete`, so `channel get` proves neither existence nor deletion; keep the create result and trust `channel list --scene 1`. ADP stores a per-type default name (10016 → 「飞书机器人」). The `--spec-json` help lists every type.
- Only 10013 DingTalk, 10014 WeCom robot WebSocket and 10016 Lark accept credentials without a provider check. 10002/10009 need the callback URL verified in the WeCom admin console first (`4506004`); LINE, Telegram and WeChat customer service validate real credentials; a rejected credential comes back from ADP as `InternalError`, which the CLI reports as `ChannelCredentialRejected` (validation, not retryable). Do not create those with placeholder values or retry them. 10000 `Wechat` and 10015 `WechatClawBot` authorize by QR code (fields are filled in after the scan; the result carries `qrcodeUrl`): read `adp docs get 132545 --section WechatChannelConfig` before trying.
- `adp channel update` can only change the description and the WeCom robot ids; recreate the channel for anything else.
- `adp trigger get` returns `cron`, `timezone`, `prompt`, `workflowId`; read it back after `trigger update` to confirm.
- `adp trigger` is an app trigger (needs a published app); `adp timer` is a workbench timer task in a space (prompt + model, per user). Pick by what the user names.
- Guideline and synonym edits (`adp guideline`, `adp synonym`) reach end users only after `adp deploy`; check `adp guideline changes` first. Only pass `adp feedback create --accept-terms` when the user agreed to the platform terms.
- Enabling a tool on the current agent is `agent.tools` in `adp.jsonc`. With `agent_id` set, `adp dev` / `adp deploy` replace the whole tool list, platform default tools included. `adp agent tool bind|unbind` only changes the draft until the next sync; use it for quick trials or apps without `adp.jsonc`, and tell the user to add lasting tools to `agent.tools`.
- Before `adp deploy`, `adp app check` lists blocking problems (unconfigured workflow nodes, broken KB or agent settings), and `adp release preview` lists the app-level config items the release changes; `--scope` shows who can call the app afterwards. A failed release (status 4 / 7 / 12) can be retried with `adp release retry --release-id <id> --yes`; anything else, including `--dry-run` on a published release, fails with `ReleaseNotRetryable`. `adp rollback --release-id <id> --yes` restores that release into the draft and publishes it as a new release (the live version only changes after that publish); `--draft-only` stops after the restore. If the restored draft equals the live release (for example only guidelines or synonyms changed, which RollbackRelease does not restore), the publish step answers 450027 NothingToRelease; rollback still succeeds with `nothingToRelease: true` and a `note`, and next_actions point to `adp guideline list` / `adp synonym list` to fix those by hand. A rollback can leave a guideline disabled (observed again in a live run); rollback therefore snapshots guideline status before and after and reports any change as `guidelineChanges` (`before` / `after`), or `guidelineWarning` when the snapshot fails. When a guideline went from enabled to something else, the first next_action is the exact `adp guideline enable --app-id … --guideline-id … --format json` for those ids. Knowledge-base QA and documents are **not** rolled back either: KB content is live, not versioned by release, so a QA edited after the target release stays as it is now. `deploy` and `rollback` print one envelope and wait for status `3`; when another release of the app is still publishing (`4506011-正在发布中`) they wait for it and submit once more. If that release already shipped the same draft, `deploy` reports it with `joinedInFlight: true` (exit 0). If the app stays busy you get `ReleaseInProgress` with `retryable: true`: watch `adp versions`, then rerun. Do not run two deploys of one app in parallel. Do not follow a draft-only rollback with `adp deploy`: it pushes local `adp.jsonc` / `instructions.md` over the restored draft.
- `adp app copy --target-space-id <id> --yes` copies an app; the copy is named "<name>的副本NN", so rename it with `adp app update` if the user cares.
- Check what is bound with `adp agent resources --agent-id <id> [--type skills]`; quotas with `adp agent limits`.
- Skill **mounts** are Claw-only (`agent.skill_ids`).
- Child agents are agents, never tools. Do not put an `agent_id` in a plugin list.

## Knowledge

An ID flag fed a name or non-numeric string fails with `InvalidIdFormat` (exit 2; the platform only says `invalid character … looking for beginning of value`). Use the numeric ID from the matching `list` command.

Default KB id = `app_id`; read it with `adp kb get --kb-id <app_id> --space-id <space_id>`. `adp kb doc import` uses the same CAM keys; no extra COS or AppKey. Shared KBs, categories, labels, and QA are managed with `adp kb create`, `adp kb category`, `adp kb label`, and `adp kb qa`; check `adp schema --command kb --compact --format json` for flags. Bind a shared KB to an app with `shared_kb_ids` in `adp.jsonc`. To use a KB from another space, the owner runs `adp kb share set --space-id <owner_space> --kb-id <kb_id> --scope spaces --space <target> --yes`; read the current scope with `adp kb share get --space-id <owner_space> --kb-id <kb_id>` and check the target side with `adp kb share inbound --space-id <target>`. Both `kb share get` and `kb share set` need the owning space (`--space-id` or `adp.jsonc`). `kb share set` replaces the whole scope and is visible to everyone in the target spaces, so confirm the targets with the user; add `--request-approval --remark` only when the user wants admin approval.

Pagination: `--page` (0-based) works on page-numbered lists. Cursor lists do not take it: `adp audit list` refuses `--page` with a UsageError and continues with the `--cursor` value from its next action; `conversation messages` continues with `--record-id`. `adp docs search` continues with `--page` over the same ranked pool (`total` appears when the portal returned every hit).

## Conversation list is not usage

`adp conversation list` returns sessions the current CAM key can see. It is not application-wide C-end volume. The result field `scope` is `owner`; there is no `--scope` flag. Without `adp.jsonc`, pass `--app-id` after `space list` and `app list --space-id`. Do not run `adp init` to list sessions. `adp conversation messages` reads one of those sessions. A `tool_call` row is the tool span: `trace.toolName`, `trace.traceId`, `title` (call), and content `text` (result). There is no separate thought document. `--type 0`, `5`, and `20` are refused; pass the `type` from the `conversation list` row. `adp conversation create|get|rename|reset|delete` default to `--type 2` (evaluation); pass `--type 1` for visitor sessions or you get `ConversationNotFound`. After `delete`, `get` answers `ConversationNotFound`; `reset` clears context but keeps history, and is a write: it needs `--yes` (without it the CLI refuses and the next action is the same command with `--yes`). `get` / `messages` / `reset` / `delete` accept `--app-id` (validated and echoed, not sent: these APIs take only the conversation ID). `adp chat` sessions are type 5 (API) and cannot be read back with `conversation messages`; next actions suggest `adp chat` only for type 1 conversations. `adp conversation record get --record-id` takes the question record ID from `conversation messages`, or the reply `recordId` from `adp tail` together with that row's `--conversation-id`. Rows from `adp chat` (API conversations) cannot be resolved that way. `adp app token sse|ws` print a masked token; add `--reveal` only when the caller must hand it to a channel client. `adp usage` is one app's model KPIs for the last 7 days and needs `--app-id` or `adp.jsonc`. It may fail with 450002 (no metric permission); then use `adp app list --fields appId,name,status,updateTime`.

## 工作流边界

`adp workflow` 已支持 list/get/deploy/enable/disable/export/import/remove/run，与其他命令共用 CAM 密钥，仅支持公有云站点。
`workflow import` 遇到目标应用里有同名工作流会报 `WorkflowImportDuplicate`，缺变量报 `WorkflowImportMissingVariables`；启用后要发布应用才在生产生效。

## 应用包导入导出

- `adp app export` 只能导出**已发布**的应用（未发布报 `AppNotReleased`，先 `adp deploy`）；导出的是最新发布版本，`--release-id` 可指定版本。
- `adp workflow run` 只适用于绑定了入口工作流的单工作流模式应用（`app_mode: 3`；实测 `async_workflow` 为 false 也能跑），其他模式报 `WorkflowRunUnsupported`（平台 500331）。工作流跑失败时命令仍成功返回，要看 `state`。运行停在需要用户回答的节点（选项卡 OPTION_CARD、参数提取追问等）时状态为 5（`stateLabel: "waiting_input"`，公开文档未列出），`run start` 立即返回 `status: "waiting_input"` 而不是等到超时，结果里的 `question` 是节点的追问（例如「请提供要查询的日期」）；把用户的回答接在 `adp workflow run resume --run-id … --query` 后面继续，resume 默认会等到下一个终态或等待态（`--no-wait` 立即返回），追问没答全会再次返回 `waiting_input` 和新的 `question`；已结束的运行不能 resume。参数提取的 `IncorrectExamples` 执行得很严：用户的写法和错误示例一样（实测「10月20日」）时节点会再追问，即使用户已经给了日期。意图识别节点把最后一个意图当兜底（输出 `IntentName: "Other"`，不交给模型判断），所以最后一个意图必须是显式的「其他」。对话里的选项卡同理：平台不展示最后一个选项（兜底分支），所以选项卡的最后一项也要是「其他」。`adp chat`（`adp deploy` 之后，对话打到已发布版本）把展示的选项放进 `result.optionCards`，并在 `reply` 末尾附上编号列表。排查 token 消耗用 `workflow run node --stats`。
- `adp.jsonc` 的 `memory` 只是应用自带长期记忆的开关；独立的记忆库、条目和绑定用 `adp memory`（见 references/memory.md）。
- `adp app template` 的所有子命令都需要空间（`--space-id` 或 `adp.jsonc`），模板库按空间可见。`use` 新建的应用默认与模板同名，用 `--name` 改名。
- `adp app package retry` 只对失败的任务有效；`canRetry` 为 true 不代表能重试（报 `AppPackageTaskNotFailed`）。
- `adp app import --space-id … --file …` 总是新建一个应用，状态为未上线，不会覆盖已有应用。发布副本用 `adp deploy --app-id <副本 appId> --yes`：带 `--app-id` 时只把该应用的远端草稿原样发布，不读 adp.jsonc、不推本地文件；import 的最后一条 next_action 就是这条命令。新应用的名称不保证带「的副本NN」：实测副本可能与源应用同名，按 `appId` 区分，不要按名称找。空间应用数已满时平台报 4900001（CLI 报 `AppQuotaExceeded`，`retryable: true`，next_action 是原命令）；`--no-wait` 的 next_action 是 `app list --space-id …`，新应用先以 status 4（导入中）出现。应用包只含应用配置，不含工作流和知识库文档/问答：标准/多 Agent 等模式的副本会收到 warning；能列出源应用工作流时，next_actions 对每个工作流给出具体的 `workflow export --app-id 源 --workflow-id … --output ./<名称>-<id>.zip` 和 `workflow import --app-id 新 --file 同一个 zip --enable`，列不出时给出源应用的 `workflow list`；最后是源应用的 `kb doc list`，文档要用 `kb doc import --kb-id 新应用 --file 原文件` 逐个重新导入。导入并启用的工作流随下一次 `adp deploy` 一起发布。单工作流（app_mode 3）副本的入口工作流不存在，运行报 500304。import 会给出 warning 和 next_actions：从源应用 `workflow export`，`workflow import --enable` 到副本，`workflow list` 查到新 id，再用 `workflow export` 结果里 `canvasFiles` 指向的 `<id>_workflow.json`（导出时已从 ZIP 解到同目录）执行 `workflow deploy --workflow-id 新id --canvas-file … --bind`。源应用 id 取自包里的 `base_config.json`，入口工作流 id 取自源应用草稿（导出包会把它置空）；读不到的 id 前面会多一步 `app list` / `app get`。
- `workflow import --enable` 导入的工作流不需要再 `workflow deploy`：下一次 `adp deploy` 发布应用时会一并发布它们（实测）。`adp deploy` 发布后仍会检查已启用但仍是 `UNPUBLISHED` 的工作流，这种情况很少见；出现时给出 warning（`unpublishedWorkflows`）和 next_action：先 `workflow export --output` 拿到 `<id>_workflow.json`，再 `workflow deploy --workflow-id … --yes`，然后重新 `adp deploy`。
- 两个 export 命令不带 `--output` 时返回约 30 分钟有效的 `downloadUrl`，视同凭证，不要写进日志或回复里。
读取 [../create/TOPIC.md](../create/TOPIC.md) 的 Workflows 部分和目标命令的 schema。
工作流画布通过本地 JSON 与 `adp workflow deploy` 管理。
