# Create an ADP app and agent (`adp`)

This topic is loaded from the **`adp`** companion skill. Discover flags with `adp schema`. Mode table: [../references/app-modes.md](../references/app-modes.md). Platform API names: `adp docs search "<action>" --format json` then `adp docs get <id>`.

## Pick a mode (do not skip)

Infer from the user’s goal; ask only if it is ambiguous. Do not mention the integer in user-facing chat unless they asked.

| Goal | `--app-mode` |
| --- | ---: |
| FAQ / 知识问答 / 客服，不要工具 | 1 Standard |
| 多个 Agent 分工、转交 | 2 Multi-Agent (CLI default) |
| 固定流水线、不需要 Agent 规划 | 3 Single workflow |
| 自主规划、写代码、挂 Skill | 4 Claw |

Claw cannot be switched to/from the other three later. Standard and Multi-Agent **cannot** mount Skills.

## Prerequisites

先检查已有 profile。公有云使用 CAM；独立站使用 OneID。鉴权失败时读取
[../references/auth.md](../references/auth.md)，不要预设所有站点都要求 AKID。然后：

```bash
adp auth status --format json
adp space list --format json --fields spaceId,name
adp models --format json --fields modelId,name --limit 20
adp models --scene 18 --space-id "<space_id>" --format json --fields modelId,name   # Claw (app_mode 4)
```

需要 `space_id` 和 `model_id`。Claw 应用只能用 `--scene 18` 列出的模型，否则发布报 `4600005-应用配置不完整`；不传 `--model-id` 时 `init --create-remote` 自动取该列表第一项，目前通常是 `Auto/auto`（平台自动选模型，可以正常发布）；要固定模型就显式传 `--model-id`。不带 `--create-remote` 时写入占位值 `placeholder-model`，`adp deploy` 会拒绝，需先改成 scene 18 列表里的模型。非 Claw 模式不传 `--model-id` 时（含 `--create-remote`）同样写占位值，`init` 结果带 warning：多 Agent 要先换成 `adp models` 里的真实模型；1/3 模式没有智能体，不会发送这个值。`--model-id` 只写入 `agent.model.model_id`，通过 `ModifyAgent` 生效：标准模式（`1`）和单工作流（`3`）没有智能体，传了也不会改应用的生成模型（控制台仍显示 Auto），`init` 结果里会带 `warnings` 提示；这两种模式的模型请在控制台选择。`init --dry-run` 的 next_action 是去掉 `--dry-run` 的同一条 `adp init`（带 `--create-remote` 时附 `--yes`，会真的建应用）。不要在回复中回显明文 SecretKey；agent 不等待 TTY 交互输入。

## Create (one shot)

Write a real `instructions.md` (role, can/cannot, language). Then:

```bash
adp init --name "<name>" --space-id "<space_id>" --model-id "<model_id>" \
  --app-mode <1|2|3|4> --create-remote --dry-run --format json
```

`--dry-run` does not write `adp.jsonc` and does not call `CreateApp`. `adp init` never overwrites an existing `instructions.md` (the result says `instructionsKept: true`); write it first and init uses it. After the user confirms:

```bash
adp init --name "<name>" --space-id "<space_id>" --model-id "<model_id>" \
  --app-mode <1|2|3|4> --create-remote --format json
```

`--create-remote` calls `CreateApp`. **Claw (`4`)** then `CreateAgent` for the main agent (`Role=0`) and writes `agent_id`. A Claw app has **1 main agent (`Role=0`) and up to 19 sub-agents (`Role=1`)**, 20 agents in total. Creating a second main agent fails with `AgentAlreadyExists` (ADP returns the existing id); edit that agent with `adp agent update`. Add a sub-agent with `adp agent create --role 1` (see [Agents after init](#agents-after-init)). Standard (`1`) / single-workflow (`3`) have no agent (`CreateAgent` is rejected). Multi-Agent (`2`) binds the first listed agent if the platform created one; a fresh Multi-Agent app usually has none, so `agent_id` stays empty and that is expected. Then `ModifyApp` (and `ModifyAgent` only when `agent_id` is set). For Standard, put the role in `role_description`, not only `instructions.md`: `adp init --app-mode 1` (and `3`) copies the instructions (an existing `instructions.md` included) into top-level `role_description`; edit that key afterwards. Creation consumes quota and is not easily undone from this CLI without `adp delete --yes`.

Then publish only if they asked to 上线 / 发布:

```bash
adp deploy --dry-run --format json
adp deploy --format json
```

Chat talks to the **published** app (C-end SSE + AppKey). After `adp deploy`:

```bash
adp chat --message "你好" --dry-run --format json
adp chat --message "你好" --format json
adp chat --conversation-id <id-from-result> --message "继续" --format json
adp tail --app-id <app_id> --format json   # question/answer records of recent chats (each row's recordId + conversationId go to conversation record get --record-id --conversation-id; not for adp chat rows)
```

`adp chat` is a C-end (AppKey) session: it does not show up in `adp conversation list` (empty), and `adp conversation messages` / `get` / `delete` cannot reach it with any `--type` (460010 for 1/2, type 5 needs the AppKey the CLI does not send). It cannot be deleted from the CLI. Keep the `conversationId` from the chat result to continue, and read the exchange back with `adp tail --app-id`. `adp tail --app-id` reads `DescribeMsgRecordList` (all channels, newest first, no time window) for the released app; records land asynchronously, so a `tail` right after `chat` can be empty for up to about a minute. Retry instead of concluding the chat was lost.

Knowledge citations are in `result.references` (`index`, `name`, `type` 1 = QA with `qaId` / `kbId`, docs with `docId`). `adp tail` records have no citation field (`DescribeMsgRecordList` does not return one).

Right after `adp deploy` the first call of a tool can fail on the runtime side (`mcp__…KnowledgeRetrievalAnswer not found`); the CLI reports retryable `ChatToolNotReady`. Wait about a minute after a release, then retry the same chat. A plain `Timeout` (also retryable) means the reply was still streaming at the deadline.

`--image-url` / `--file-url` accept public or ADP COS URLs. Timeout can be minutes when a plugin (for example 腾讯医典) runs.

## Knowledge-base documents

Default KB id equals `app_id`. Same profile keys on the public cloud and the independent site; no extra COS or AppKey. Read it with `adp kb get --kb-id "<app_id>" --space-id "<space_id>"` (the platform's `DescribeKB` only serves shared KBs, so the CLI reads the default KB from the space's KB list and needs the space).

```bash
adp kb doc import --file ./faq.md --format json --cwd "<project>"
adp kb doc list --format json --cwd "<project>"
adp chat --message "根据知识库回答：…" --format json --cwd "<project>"
```

`--wait` is the default (poll until parse finishes). Create a shared KB with `adp kb create`; bind it with `shared_kb_ids` in `adp.jsonc`. QA / labels / FileId documents: `adp schema --command kb --compact --format json`. Local `--file` stays on `adp kb doc import`; ADP `FileId` import is `adp kb file import`. A `FileId` must already exist in ADP file management (uploaded in the console); it is not a local path and not a `docId` from `kb doc list`. If every FileId is rejected the command fails with `DocImportFailed` (exit 1); otherwise check each item's `succeeded`. When the user only has a local file, use `adp kb doc import --file`. `kb doc list` and `kb file list` read the same documents (both call `DescribeDocSummaryList` on the KB): a file imported with `kb doc import` shows up in `kb file list` with the same numeric `docId`, so `kb file get|modify|delete` accept it too. Only the import paths differ (local file vs existing `FileId`).

`adp kb search --kb-id <id> --question "…"` is a recall test (same as the console's 召回测试) and returns `docName` / `content` per hit. `adp kb doc retry` only works on failed documents; a finished one reports `DocAlreadyImported`. `adp kb qa export` only starts a task and returns `exportTaskId`; the file is downloaded from the console. `adp kb qa conflict list` shows `pending` groups by default (`--status resolved|all`); resolved groups drop out of the default list.

### Claw (mode 4) answers without the knowledge base

A Claw agent only searches knowledge through the `KnowledgeRetrievalAnswer` tool. Wire it in this order:

1. `adp init --app-mode 4` already writes this tool into `agent.tools`; for an older project add it to `agent.tools` in `adp.jsonc` (`kb doc import` and `deploy` in a Claw project without it return a `needs_edit adp.jsonc` next action): `{"plugin_id":"3ad93aae-587e-4bcc-ae07-ad13bfb1aaca","tool_id":"0ca8d482-1e77-462b-bc21-807c8f052f69"}`. On deploy the CLI adds its plugin to the `PluginList` it sends (without it ADP answers 560001); it does not write that ID back into your local `plugin_ids`, so `adp.jsonc` keeps only what you wrote. Leave its inputs alone: the platform fills `KnowledgeScope` with all bound KBs.
2. Default KB: import docs or QA (`adp kb doc import`, `adp kb qa create`). QA with an effective domain must be enabled to be cited. A new QA goes 4 (审核中) / 6 (学习中) → 8 (导入完成) in about 15-30 s; `kb qa update` during that window fails with `KbQaNotEditable` (platform `450160 QA无法编辑`, retryable). `kb qa create` returns a `kb qa get` next action to watch the status. Adding a QA is not a release change (`deploy` reports nothing to release); the released Claw agent answers from it once the tool from step 1 is released (measured).
3. Shared KB: list it in `shared_kb_ids`, run `adp dev`, then **`adp deploy`**. Chat only sees a newly bound shared KB after a release; the default KB works from the draft.
4. Check with `adp app get` (`draft.sharedKbIds`) and an `adp chat` question only the KB can answer (after `adp deploy`; `adp chat` talks to the released app).

## Agents after init

`adp agent create` is **Claw-only** (`app_mode 4`). A Claw app has **1 main agent (`Role=0`)** and up to **19 sub-agents (`Role=1`)** (20 agents total). `adp.jsonc` `agent` is the main agent. `adp dev` / `adp deploy` call `ModifyAgent` only for that `agent_id`; they do not overwrite sub-agents.

`CreateAgent` with `Role=0` is idempotent once a main agent exists: a second `adp agent create` without `--role 1` returns `AgentAlreadyExists` (including `--dry-run`). The error `next_actions` include a runnable `adp agent create --role 1` preview. Edit the main agent with `adp agent update`.

Add a sub-agent (this is how to handle “给这个应用添加子 agent，名字叫 …”):

```bash
adp schema --command "agent create" --format json
adp agent create --app-id "<claw_app_id>" --role 1 --name "<name>" \
  --description "<when the main agent should delegate>" \
  --instructions "<how this sub-agent works>" \
  [--model-id "<model_id>"] --dry-run --format json
adp agent create --app-id "<claw_app_id>" --role 1 --name "<name>" \
  --description "<when the main agent should delegate>" \
  --instructions "<how this sub-agent works>" \
  [--model-id "<model_id>"] --format json
```

`--sub-agent` is the same as `--role 1`. `--description` is the routing text the main agent uses to decide when to delegate. `--name` is required for a sub-agent (do not reuse the main agent's name from `adp.jsonc`). The same flags work with no `adp.jsonc` as long as `--app-id` is set. With `--role 1`, the CLI does **not** copy the main agent's `instructions.md`, `skill_ids`, or `plugin_ids`. Pass `--instructions` or `--instructions-file` for the sub-agent prompt; if you pass neither, the prompt is a short default from the name. Pass `--skill-id` only for skills this sub-agent should mount (default: none). Omit `--model-id` to inherit a real `adp.jsonc` model, else the main agent's model, else the first `ModelScene=18` model, else `Auto/auto`.

Change a sub-agent without rewriting `adp.jsonc` by passing only the fields that change. The CLI reads the current agent and keeps the rest (including `Role`):

```bash
adp agent update --app-id "<claw_app_id>" --agent-id "<sub_agent_id>" \
  --name "<name>" --description "<when to delegate>" --dry-run --format json
```

With no field flags, `adp agent update` still syncs `adp.jsonc` plus `instructions.md` onto `--agent-id`.

Claw multi-agent collaboration (doc 134193) has two mechanisms:

1. **单向委派 (default).** The main agent routes work to sub-agents from each sub-agent's `name` and `description`. Each sub-agent runs with its own `instructions`, model, skills, and tools.
2. **团队协作 (optional).** Set `mode.claw.team_enabled` and `mode.claw.team_prompt` in `adp.jsonc` (`ClawAgentConfig.AgentTeamConfig`). Teammates can report back and talk to each other according to `team_prompt`. That is app config, not a substitute for creating the sub-agent.

On Standard (`1`), Multi-Agent (`2`) or single-workflow (`3`) apps the CLI reads the app mode first and refuses with a usage error, also under `--dry-run` (upstream would answer `560001`). Edit an existing agent with `adp agent update`; for another Claw agent, create a Claw app with `adp init --app-mode 4`. Re-create a missing main agent (role 0) only when `adp agent list` shows no role 0 agent:

```bash
adp agent create --app-id "<claw_app_id>" --dry-run --format json
```

This CLI does **not** generate canvas JSON — copy a template from
[../references/workflows.md](../references/workflows.md), export one, or pull one from an existing app. It can bind an existing id in `adp.jsonc`
(`mode.single_workflow`) and set Multi-Agent collaboration
(`mode.multi_agent.collaboration_mode`). Do not invent `adp workflow` flags: check
`adp schema --command "workflow" --compact --format json`.

## Workflows

`adp workflow` uses the same profile keys as every other command (it calls LKE canvas
actions). Public cloud sends them to `lke.tencentcloudapi.com`; an independent or custom profile sends them to its ADP host.

```bash
adp workflow list --app-id "<app_id>" --format json --fields workflowId,name,status,isEnable
adp workflow get --app-id "<app_id>" --workflow-id "<wf_id>" --format json
adp workflow deploy --app-id "<app_id>" --canvas-file ./canvas.json --dry-run --format json
adp workflow deploy --app-id "<app_id>" --canvas-file ./canvas.json --yes --format json
adp workflow enable --app-id "<app_id>" --workflow-id "<wf_id>" --format json
adp workflow export --app-id "<app_id>" --workflow-id "<wf_id>" --output ./wf.zip --format json
# Same-name workflow in the target app → WorkflowImportDuplicate
adp workflow import --app-id "<app_id>" --file ./wf.zip --enable --format json
# Whole app (released apps only; run adp deploy first). Default scope is app settings plus
# every workflow, connector, knowledge base, agent, and skill. --include workflow,kb narrows it.
# A pipe, CI, agent, or --yes does not prompt. A selected workflow keeps referenced connectors and knowledge bases.
adp app export --app-id "<app_id>" --output ./app.zip --format json
# Import that ZIP as a new unreleased app (copy; name gets 的副本NN)
adp app import --space-id "<space_id>" --file ./app.zip --format json
# A full package already contains workflows (app/workflow/workflow_<id>.json inside app.zip)
# and knowledge bases (knowledge_bases.zip and metadata.json Components.KnowledgeBases).
# A settings-only package does not. A mode 3 copy of a settings-only package is NOT runnable until you
# copy the entry workflow (500304 otherwise); import prints a warning plus these next_actions,
# with the source app ID (from the package) and entry workflow ID (from the source draft) filled
# in when the CLI can read them; otherwise it adds app list / app get lookups first:
adp workflow export --app-id "<source_app_id>" --workflow-id "<entry_wf_id>" --output ./wf.zip --format json
adp workflow import --app-id "<copy_app_id>" --file ./wf.zip --enable --format json
adp workflow list --app-id "<copy_app_id>" --fields workflowId,name --format json   # the new workflow ID
unzip wf.zip   # holds <entry_wf_id>_workflow.json, the canvas
adp workflow deploy --app-id "<copy_app_id>" --workflow-id "<imported_wf_id>" --canvas-file ./<entry_wf_id>_workflow.json --bind --yes --format json
# Preview / manage package tasks (download after --no-wait, retry failed, delete)
adp app package summary --app-id "<app_id>" --format json
adp app package download --app-id "<app_id>" --task-id "<task_id>" --output ./app.zip --format json
```

### From a template

```bash
adp app template list --space-id "<space_id>" --query 客服 --format json --fields templateId,name,appMode
adp app template get --space-id "<space_id>" --template-id "<tpl_id>" --format json   # read devNotes first
adp app template use --space-id "<space_id>" --template-id "<tpl_id>" --name MyBot --format json
```

The new app is an unreleased draft; its `appMode` comes from the template. Configure what `devNotes` asks for, then `adp deploy`.

### Async workflow runs

Needs `app_mode: 3` with a bound entry workflow (`mode.single_workflow.workflow_id`), synced with `adp dev` (test) or `adp deploy` (prod). Other modes answer `WorkflowRunUnsupported` (500331). `async_workflow: true` was not required in live tests.

```bash
adp workflow run start --app-id "<app_id>" --query "<input>" --var name=value --format json
adp workflow run get --app-id "<app_id>" --run-id "<wfr_id>" --format json
adp workflow run node --app-id "<app_id>" --node-run-id "<nr_id>" --format json   # input/output/log
adp workflow run stop --app-id "<app_id>" --run-id "<wfr_id>" --format json
```

- `list` / `get` / `deploy` / `enable` / `disable` / `export` / `import` / `remove` / `run` all exist.
- `workflow run start` exits 0 even when the workflow fails: read `state` (2 ok, 3 failed, 4 cancelled) and the failing node in `nodeRuns`, then `workflow run node` for its log.
- `state: 5` (`stateLabel: "waiting_input"`) means a node such as OPTION_CARD waits for the user: `start` returns at once with `status: "waiting_input"`; answer with `adp workflow run resume --run-id <wfr_id> --query "<answer>"`, which waits for the next terminal or waiting state (`--no-wait` to return immediately). After an OPTION_CARD, `SYS.UserQuery` is the clicked button's text; keep the original question by referencing an earlier node's output (an LLM or PARAMETER_EXTRACTOR before the card).
- `status` in `list` is the **release** state; `isEnable` is the enable flag. They are
  different fields — `isEnable` is what `workflow enable` changes.
- `deploy` checks the canvas locally (also with `--dry-run`), derives `Edge` from
  `NextNodeIDs`, then runs create → validate → enable → bind. It stops on a validation
  failure without persisting the canvas. A same-name workflow with a non-empty canvas is
  refused; update it in place with `--workflow-id <wf_id>`.
- `--canvas-file` takes a canvas JSON object. The CLI stamps the real `WorkflowID` into
  it before saving.
- `deploy` binds as the entry workflow only when `app_mode` is `3`; `--no-bind`
  disables that.
- `export` returns a short-lived download URL. Treat it as a credential: do not log it.
- Canvas authoring: start from the templates and rules in
  [../references/workflows.md](../references/workflows.md) (fast path, node types,
  nested WORKFLOW_REF / deep research, and how modes 1/3/4 reach a workflow). See
  [../references/pitfalls.md](../references/pitfalls.md) for the bind-order and
  release-status traps.
