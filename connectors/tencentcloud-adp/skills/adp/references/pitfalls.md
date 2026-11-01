# Platform pitfalls

Symptom → cause → fix. Each one constrains an API this CLI already calls. Verify the
platform side with `adp docs search "<action>" --format json` when in doubt.

## Single-workflow `WorkflowId` must be written through the bind path

- **Symptom**: the workflow is deployed and enabled, but `adp app get` still shows an
  empty entry workflow and `adp deploy` fails with `450934 Single workflow is empty`.
- **Cause**: writing the id into `adp.jsonc` `mode.single_workflow` sends
  `ModifyApp` `Config.Mode.SingleWorkflowConfig`, but only when that path is in the
  update mask. A mask that omits it silently drops the binding.
- **Fix**: `adp workflow deploy` binds via `Config.Mode.SingleWorkflowConfig` for
  `app_mode=3`. To bind an existing id by hand, keep `mode.single_workflow` in
  `adp.jsonc` and `adp deploy`; the mask is derived from the config, so the object
  must be present.

## Enable before bind

- **Symptom**: binding fails with `450935 Specified workflow is invalid`, even though
  the workflow looks publishable.
- **Cause**: a workflow that has just been saved is not yet enabled. Publish status
  (`UNPUBLISHED` / `PUBLISHED`) is not the enable flag — `IsEnable` is, and it is a
  separate field.
- **Fix**: `adp workflow enable --app-id <id> --workflow-id <wf>` before any bind.
  `workflow deploy` does this in order (create → save → enable → bind) and waits
  ~2s before binding because the platform is eventually consistent here.

## `app_mode` cannot always change

- **Symptom**: a mode change is rejected with `450442 Application mode cannot be changed`.
- **Cause**: `1` / `2` / `3` can switch among themselves, but Claw (`4`) is isolated.
- **Fix**: treat Claw as create-time-only. If a mode change is rejected, create a new
  app rather than forcing it. Mode table: [app-modes.md](app-modes.md).

## Claw release needs a Claw-scene model

- **Symptom**: `adp deploy` on an `app_mode=4` app fails with
  `4600005 应用配置不完整，请检查后再发布`, although the agent has instructions and a model.
- **Cause**: Claw only accepts models listed under `DescribeModelList` `ModelScene=18`.
  `adp models` without `--scene` lists every model, so a general model such as
  `qwen3.8-flash` looks valid but is rejected at release.
- **Fix**: `adp models --scene 18 --space-id <id> --fields modelId --format json`, put one
  into `agent.model.model_id`, then `adp deploy`. `adp init --app-mode 4 --create-remote`
  without `--model-id` already picks the first one; `adp deploy` refuses the
  `placeholder-model` value before calling the API.

## `ModifyChannel` only changes a few fields

- **Symptom**: `adp channel update --name …` (older CLI) returned ok, but the name did not
  change and the description was wiped.
- **Cause**: the `ModifyChannel` update mask allows only `spec.description` and
  `spec.wecom_robot.callback.wecom_robot_id` (B-end), or `spec.description` and
  `spec.wecom_robot.websocket.bot_id` / `bot_secret` (C-end). Other paths are ignored.
  ADP also stores a per-type default `ChannelName` (10016 → 「飞书机器人」).
- **Fix**: the CLI exits 2 for any other path. Recreate the channel to change the name
  or other credentials.

## Most channel types check credentials with the provider

- **Symptom**: `adp channel create` with placeholder credentials fails with
  `4506004 确认填写认证的回调url地址` (10002, 10009), `4506003 渠道相关参数错误` (LINE),
  or a system / internal error (10004, Telegram, 10000).
- **Cause**: at create time ADP verifies the credentials or callback URL with WeCom,
  LINE, Telegram, or WeChat. Only 10013 DingTalk, 10014 WeCom robot WebSocket and
  10016 Lark are stored without a check. 10000 and 10015 authorize by QR code; their
  fields are filled in by ADP after the scan.
- **Fix**: use real credentials. For WeCom callback types, configure the receive-message
  URL, Token and EncodingAESKey in the WeCom admin console first. Read a block's fields
  with `adp docs get 132545 --section <Name>ChannelConfig --format json`.
- A second channel of the same type is allowed: a second 10016 Lark channel on the same app
  is created normally. `4506003-企微应用已经被绑定` means that credential is already bound to a
  channel. ADP says 企微应用 for every type (a Lark `AppId` gets the same text); the CLI message
  names the provider from the ChannelType instead (`these Lark robot credentials are already
  bound …`) and reports `ChannelAlreadyBound` (conflict, exit 5).
- The binding is not released right away when the channel is deleted: recreating a channel with
  the same Lark `AppId` right after `channel delete` has been measured to fail with the same
  4506003. Reuse the existing channel (`adp channel list --app-id <app>`), wait before
  recreating, or use another provider app; changing other fields will not help.

## Release completion is `status = 3`, nothing else

- **Symptom**: a release looks finished but the app still serves the old version.
- **Cause**: intermediate and terminal statuses are easy to confuse; substring matching
  on a status description reads in-flight states as done.
- **Fix**: `adp versions --fields releaseId,status --format json`. Status is a numeric
  enum: `1` pending, `2` publishing, **`3` published (the only completion signal)**,
  `4` failed, `5` reviewing, `6` review passed, `7` review failed, `8` callback
  running, `9` paused, `10`–`12` appeal states. Wait for `3`; treat `4` / `7` / `12`
  as failure and inspect before retrying — `adp deploy` is `non_idempotent`.

## Reading shared-KB bindings

`DescribeApp` can return an empty `SharedKbList` while the binding exists. `adp app get`
then reads `draft.sharedKbIds` from the app's referenced shared KBs (LKE
`ListReferShareKnowledge`). `adp kb create --shared-sub-type` is sent as `SharedSubType`,
but ADP currently ignores it: `kb get` reports 0 whatever you pass.

## `shared_kb_ids` is full-overwrite

- **Symptom**: after a push that adds one shared KB, every previously bound shared KB
  disappears.
- **Cause**: `ModifyApp` `SharedKbIdList` replaces the whole set. Any id missing from
  the pushed list is unbound, and a non-numeric id is dropped silently.
- **Fix**: read the current set with `adp app get --app-id <id> --format json` and push
  the full target list.
- **Tri-state in `adp.jsonc`**:
  | Config | Effect |
  | --- | --- |
  | key absent | bindings untouched (the path is not in the update mask) |
  | `"shared_kb_ids": ["<id>"]` | replace the whole set with that list |
  | `"shared_kb_ids": []` | unbind everything (explicit empty array) |
- Ids must be plain numeric strings (for example `"2019409536501314752"`), no `kb_`
  prefix. Confirm the result with `adp app get` after pushing.

## List `truncated` used to lie at 100 rows

- **Symptom** (historical): `--limit 200` returned 100 rows with `truncated: false`.
- **Cause**: Cloud `PageSize` max is 100. The CLI used to probe `items.length > limit` and dropped `TotalCount`.
- **Fix**: lists now auto-follow pages, return `total`, and set `truncated` from `items.length < total`. If truncated, re-run with `--limit` equal to `total`. Do not paginate with hand-signed Cloud API.
- With `--page`, one page is fetched and its size is capped at 100 (`pageSize` in the result shows the real size). `truncated` is true only when rows remain after this page; the last page and pages past the end report `false`, and `next_actions` points at `--page <n+1>`.
- 对话里的知识引用：只有直接命中问答对的回复带 `References`，内容都指向那条问答，所以几条引用一模一样是平台返回的；文档生成的回复不带 `References`（`result.references` 为空不代表没检索到文档）。Claw（app_mode 4）应用的知识库工具同样只返回问答引用，命中文档时没有引用（已两次实测确认），不要承诺能给出文档出处。`adp chat` 的引用在成功结果的 `result.references`（`index`、`name`、`type`，问答带 `qaId` / `kbId`，文档带 `docId`）；CLI 会收集 SSE 里任意位置的 `Reference` / `References`，平台以后若在别的帧里带上文档引用也能拿到。`adp tail` 读的 `DescribeMsgRecordList` 没有引用字段，看不到引用。`conversation messages` 只能读当前 CAM 可见的会话（访客 1、评测 2、工作流调试 10）；`adp chat` 建的是 API 会话（类型 5，要 AppKey），用 `conversation messages` / `get` / `delete` 都读不到也删不掉。要看文档出处，在知识库里用 `kb doc referrers` 反查。
- 应用长期记忆（`adp.jsonc` 的 `memory`）不保证下一轮一定召回：实测开了记忆、上一轮说过的信息，下一轮 `adp chat` 仍可能答不出。这是平台行为，CLI 没有召回开关；需要确定性时把关键信息放进同一轮消息，或用 `adp memory` 管理记忆库条目。
- `adp chat --app-id <id>` 直接对任意已发布应用对话（AppKey 的取法和项目默认应用相同，不打印），不需要 `adp.jsonc`；`--agent-id` 只在需要指定 Agent 时传。
- `adp var get` 默认 `--module-type -1`（任意模块），能找到 `var put` 写入的变量，不管平台把它存在哪个模块；`var update` / `var delete` 不传 `--module-type` 时先读出变量所在模块再写。内置变量（`VisitorBizId` 等，列表里 `moduleType` 为 0）`var get` 读不到（450010，CLI 报 `VarNotFound`），只能在 `var list` 里看。
