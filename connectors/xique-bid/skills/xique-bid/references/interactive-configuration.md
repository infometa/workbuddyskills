# WorkBuddy interactive configuration

Use the named MCP App tools for standard stages: `xique_prepare_source`, `xique_bid_configuration`,
`xique_outline_start`, `xique_special_project_selection`,
`xique_outline_confirmation`, and `xique_outline_update_confirmation`. Keep
`xique_select_option` only for targeted edits of one ordinary field. For a new
bid, call `xique_prepare_source` once and poll the same run. When parsing is
ready, `xique_generation_status` returns `awaiting_input/bid-config`. Immediately
call the explicit `xique_bid_configuration(runId)` stage tool; the status tool
only reports state and does not open the card itself. The explicit stage tool
declares the MCP App UI metadata that WorkBuddy needs to render the selector.
Do not ask the user to type the whole configuration.

## Permanent WorkBuddy UI constraint

- WorkBuddy v5.3.11 validates `AskUserQuestion.options` with `max(4)`.
- Its UI always adds a free-text `Other`/`其他补充` entry; a Skill cannot disable
  or remove that entry.
- Therefore never use `AskUserQuestion` for any Xique enum or confirmation.
- WorkBuddy v5.3.11's ordinary plugin MCP client returns JSON-RPC
  `Method not found` for `elicitation/create`, even when the host process
  advertises `elicitation.form`. Do not treat that environment marker as proof
  of native form support.
- The named stage tools and `xique_select_option` may still use a native MCP form on future compatible
  clients. On WorkBuddy v5.3.11 it returns
  `interactionMode=mcp-app`. The tool definition links
  `ui://xique-bid/selection.html`, so WorkBuddy automatically renders the
  standard MCP App in its dedicated panel. End the turn and wait for the
  click-generated user message; do not call `read_me` or `show_widget`.
- Keep `workbuddy.ui.launchSurface=panel` for WorkBuddy v5.3.11. Its inline
  renderer can create a live sandbox App without attaching the App to a visible
  tool-call anchor, especially when process messages are collapsed. A hidden
  sandbox target is not proof that the user can see or click the selector.
- The MCP App uses standard `ui/message`, has no automatic `其他补充`, and must
  show every legal value in the same component, including all seven page
  scopes and the five export-template cards; template 5 is enabled in the
  post-generation visual export settings card.
- WorkBuddy v5.3.11's legacy `show_widget` renderer omits the
  `WidgetRenderer.hostConfig` callback. A `sendPrompt()` click reaches
  `widget:sendMessage`, but the host discards it because `onSendMessage` is
  undefined. A button can therefore change color or become disabled without
  producing a new user message. Do not route Xique selection through that
  renderer; the standard MCP App `ui/message` path is required.
- Never expose the native MCP error, print a numbered text fallback, call
  `xique_choices` to reconstruct the question, or ask the user to type the
  whole configuration. If the MCP App resource does not render, report a
  WorkBuddy compatibility error and stop.
- Each rendered MCP App card is single-submit. Lock it before sending the first
  `ui/message` and persist the lock for reopened cards. A timeout or uncertain
  transport result must not re-enable the same card; query the current workflow
  state instead of allowing a second selection that could duplicate a request.

## Interaction constraints

- Resolve and pre-parse the source file first, then use the one-page configuration form for all
  common settings. Individual field calls below are compatibility and targeted
  edit paths only; do not run them sequentially for a new bid.
- Treat click messages beginning with `【喜鹊标书配置批量选择】`,
  `【喜鹊标书配置选择】`, or
  `【喜鹊标书确认】` as explicit user selections. Preserve earlier selections and
  proceed to only the next missing field.
- Show all supported values in the same selection component, even when there are more
  than four. Do not use range/category questions or `更多` navigation.
- Use single-select questions unless a step explicitly says multi-select.
- Allow free text only where this document explicitly requests a local path.
  Multi-bid identifiers/types and EPC values must come from the parsed backend
  response and must never be typed or invented by the user.
- 计划模式可在快速 / 规划间选择，并将用户选择原样提交；只有消息没有该字段时才默认
  快速（`--plan-mode 0`）。Do not silently force quick mode when the user selected
  planning, and do not hide the 计划模式 question.

### 2b. Plan mode

Call `xique_select_option(field=planMode)`:

- Header `计划模式`
- Question `请选择计划模式。`
- Options `快速`、`规划`

Pass the selected value as-is. Do not silently force quick mode.

## Preferred one-page flow

`xique_bid_configuration(runId)` renders parsed multi-bid/EPC choices first when present, then:
篇幅、写作质量、计划模式、正文风格、表格、图片设置、暗标设置、输出路径；表格样式、表格颜色、流程图样式、
导出模板、导出布局、自动编号、修改标记、四个页边距字段和四个图片尺寸字段（cm）统一位于默认收起的
“导出格式设置”中。Custom output path appears as a dependent text input on the same page. When 模板5 is selected, it shows the complete
visual numbering fields for title levels 1-5, body levels 1-4, fonts, sizes, alignment,
bold, page/line breaks and the starting index. There is no advanced style JSON input
and no manually entered multi-bid/EPC section. WorkBuddy must not ask users for style JSON.
The tool checks the current gallery while building
the page. After submission, map every line in the
`【喜鹊标书配置批量选择】` message, including `sourceRunId`, and call
`xique_prepare_bid` directly. Do not ask the same settings again or upload the file again.

The WorkBuddy card visibly preselects 标准、快速、基础配图、丰富表格、按通用方式生成暗标、纯净版、蓝色、
仅流程图、灰色流程图、模板1、常规、自动编号开启、修改标记关闭 and 默认输出路径.
篇幅 remains empty, so the user must choose it. 响应依据不在首次配置页展示，必须等待后端候选。Prefill is only UI state:
do not treat it as submitted configuration until the user clicks `提交全部配置`.

## Generation questions

### 1. Page scope

Call `xique_select_option(field=pageScope)`. Its single selection component must display
all seven presets:

- Header `篇幅`
- Question `请选择标书篇幅。`
- Options: `极短篇（50–100页）`、`超短篇（100–200页）`、
  `短篇（200–350页）`、`中篇（350–500页）`、`中长篇（500–800页）`、
  `长篇（800–1200页）`、`超长篇（1200–1500页）`.

Use these complete strings as the visible card labels. Do not display only the
preset names. The page range is required user-facing information, while only
the preset name or numeric code is passed to `xique_prepare_bid`.

Pass only the preset name before the parentheses to `xique_prepare_bid`.

### 2. Writing, style, tables, and response basis

If 篇幅 is `极短篇` or `超短篇`, set 写作质量 to `标准写作` and explain that the
frontend disables 专家智笔和旗舰智笔 for these two presets. Otherwise ask:

- Tool field `writingQuality`; header `写作质量`
- Question `请选择写作质量。`
- Options `标准写作`、`专家智笔`、`旗舰智笔`

Call `xique_select_option(field=themeStyle)`:

- Header `正文风格`
- Options `增强图文`、`全表格式`、`丰富图文`、`基础配图`、`纯文字`.

Then call `xique_select_option` separately for:

- Header `表格`; question `请选择正文中的表格数量。`; options
  `无（不插入表格）`、`少量（约每4页1表）`、`丰富（约每2页1表）`.
Pass only `无`、`少量` or `丰富` before the parentheses to MCP.

### 3. Table appearance

表格样式和表格颜色位于默认收起的“导出格式设置”中；展开后分别选择
`纯净版`、`表头强化`、`斑马条纹`、`全底色白框`，以及 `黑色`、`蓝色`、`红色`、
`绿色`、`紫色`、`青色`、`橙色`。

### 4. Images

Call `xique_gallery_status` immediately before this question. The frontend
queries `/image/library/query` with `pageSize=1` and `pageNum=1`; “我的图库” is
available only when `totalRecords > 0`. Treat a query error as unavailable.

Call `xique_select_option(field=imageTypes)` after the gallery status query. It
uses one multi-select that mirrors the frontend and always displays all five
entries:

- Header `图片设置`
- Question `请选择需要的图片类型。`
- Options:
  - When available: `我的图库（可用，共N张）` -> `knowledgeImg=1`
  - When unavailable: `我的图库（暂无图片，不可选）` -> keep
    `knowledgeImg=0`; description `请先在喜鹊前端“我的图库”上传图片`
  - `实拍风格图` -> `sceneImg=1` and `onlineImg=1`
  - `PPT式插图` -> `infoImg=1`
  - `流程图` -> `mermaidImg=1`
  - `无配图` -> all five image fields are `0`

Set unselected image fields to `0`. Do not show a separate `联网搜图` choice;
the frontend combines it with `实拍风格图`. `无配图` is mutually exclusive;
if it is selected with another entry, repeat the question.

WorkBuddy may not support a visually disabled card. If the unavailable gallery
entry can still be clicked, reject that selection, explain that the gallery is
empty, keep `knowledgeImg=0`, and repeat the same five-entry question. Never
hide “我的图库”. If the user says images were just uploaded, call
`xique_gallery_status` again before accepting the selection.

If `流程图` is selected, call `xique_select_option(field=mermaidStyle)` and show
all styles in one field: `灰色`、`紫色`、
`蓝色`、`绿色`、`橙色`、`红色`.

### 5. Multi-bid and EPC

`xique_prepare_source` returns a durable run while `xq-cli init --wait` parses
`isMultiBid`, `multiBiddingList`, and `epcEngineer_judgement`. After parsing,
the unified configuration card shows the actual packages and frontend EPC
values `全部编写`、`只写施工`、`只写设计`、`这不是EPC项目` at the top.
The server derives `multiBidType` from the parsed package and later reuses the
same `cid/uuid`; never ask the user to type it or open a second special card.
`awaiting_input/special-config` is compatibility-only for old unfinished runs.

### 6. Bidder role selection

解析完成后，如果 `xique_generation_status` 返回
`awaiting_input/bidder-role`，调用一次 `xique_bidder_role_selection(runId)`。
卡片只展示“我们自己生产”和“我们采购供应”两个真实选项；用户选择后只调用一次
`xique_apply_bidder_role_selection`，传入同一 `runId` 和卡片返回的 `bidderRole`，继续原任务。
不得重新上传源文件或调用 `xique_generate_bid` 创建第二个任务。旧版本已标记为 `blocked`、
错误指向 `bidderIdentity_judgement` 的任务也按此卡片恢复。

### 7. Reference basis selection

响应依据不是首次配置参数。等待 `xique_generation_status` 返回
`awaiting_input/reference-selection` 后，调用一次 `xique_reference_basis_selection(runId)`。卡片以“融合响应”、
“仅格式要求”、“仅评分要求”三个页签展示后端返回的完整真实候选目录树。
切换页签只供预览，不得视为提交或用户确认。用户点击“按当前思路生成大纲”后，
才只调用一次 `xique_apply_reference_basis_selection`，传入同一 `runId` 和 `referenceType`；重复点击只查询
当前任务，不得重新调用 `xique_generate_bid`、重新上传或再次提交不同依据。

## Export questions

Call `xique_select_option(field=exportTemplate)` and keep all complete visible
labels returned by `xique_choices`:

- `模板1｜章节目次（第一章→第一节→一、）` — traditional formal Chinese bid style;
  full sequence: `第一章 → 第一节 → 一、→（一）→ 1 → 1.1`.
- `模板2｜中文层级（一、→（一）→1）` — compact Chinese clause style; full
  sequence: `一、→（一）→ 1 → 1.1 → (1) → 1)`.
- `模板3｜全数字分级（1→1.1→1.1.1）` — numeric technical-specification
  style; full sequence: `1 → 1.1 → 1.1.1 → 1.1.1.1 → (1) → 1)`.
- `模板4｜章节+数字（第一章→1→1.1）` — hybrid formal/numeric style; full
  sequence: `第一章 → 1 → 1.1 → 1.1.1 → (1) → 1)`.
- `模板5｜自定义编号（可视化设置）` — selecting it in the one-page configuration
  card reveals the `模板5自定义编号` fields inside the collapsed `导出格式设置` group, with title/body numbering, font,
  alignment, page/line breaks and start index fields. The same fields are available
  again in the post-generation export settings card for a second download. WorkBuddy
  must not ask users for style JSON.

Do not shorten the visible labels to only `模板1` through `模板5`. Pass only the
canonical template name or numeric value to MCP. WorkBuddy can submit 模板1-5; 模板5 uses the structured values from the export card.

For a completed task, call `xique_export_configuration(cid)` to show one export
settings card. It includes all remaining export settings plus four page-margin
fields and four image-size fields (cm). Submitting the card internally prepares
`xique_prepare_export` with structured numbering data; show its summary and wait
for a fresh explicit confirmation before calling `xique_export_bid`.

For the initial one-page generation configuration, the batch card also includes the
remaining export settings. The page-margin and image-size groups are collapsed by
default because their frontend defaults are already valid; users can expand them when
they need custom layout values. Do not ask the user to repeat these values in chat:

- Header `导出布局`; options `常规`、`全表`、`精排`.
- Header `自动编号`; options `开启`、`关闭`.
- Header `修改标记`; options `关闭`、`开启`.
- Header `输出路径`; options `默认`、`指定路径`.

If `指定路径` is selected, request an absolute local path in a follow-up text
question. A path is intentional free text after selecting `指定路径`; it is not
an enum fallback. Never invent it.

## Confirmation

After `xique_prepare_bid` returns, show its final configuration summary before
execution. Call
`xique_outline_start(context=完整配置摘要,
confirmationId=xique_prepare_bid返回值)` with:

- `确认开始` — call `xique_generate_bid` exactly once and pass this exact label
  as `confirmationText`.
- `返回修改` — ask only for the fields the user wants to change, prepare again,
  and show a new summary.
- `取消` — do not generate.

This interactive selection is the explicit post-summary user confirmation. If
it is returned as a Widget, show the Widget, end the turn, and treat its
click-generated confirmation message as the new explicit reply. Never replace
it with a numbered text list or silently fall back to defaults.

## Outline review and modification

When `xique_generation_status` returns `awaiting_confirmation`, show every row
from `outlineDetail.outLine`, including title, theme, importance, and id. Do not
show only a count or abbreviated preview. Render one clearly separated block
per row, then verify the number of displayed blocks equals the structured array
length. Do not merge consecutive ids or skip chapters between the first and
last row. Prefer the MCP tool's complete outline text verbatim.

Call `xique_prepare_outline_continue` once before calling
`xique_outline_confirmation(context=完整大纲和继续摘要, runId=返回值,
confirmationId=返回值)`. Repeated preparation for the same unchanged outline
must return the same confirmation ID rather than create another card:

- Header `大纲确认`
- Question: include the complete outline and the returned continue summary.
- Options:
  - `确认大纲并生成正文`
  - `修改大纲`
  - `暂不继续`

Pass the first label exactly as `confirmationText`, together with the exact
`runId` and `confirmationId` carried by the clicked card, to
`xique_continue_bid`.
`暂不继续` leaves the durable run at `awaiting_confirmation`.

If the user selects `修改大纲`, ask for the requested changes. Construct a
complete updated `outLine` array from the latest structured outline. Preserve
all unchanged rows and ids. A missing existing row means deletion, so never omit
one unless the user explicitly requests deletion. New rows must omit `id`.

Call `xique_prepare_outline_update`, then show every diff item and call
`xique_outline_update_confirmation(context=完整差异摘要, runId=当前runId,
confirmationId=xique_prepare_outline_update返回值)`:

- Header `保存大纲`
- Options `确认保存修改`、`返回调整`、`取消`

Only `确认保存修改` authorizes `xique_apply_outline_update`. After saving, show
the complete returned outline and say `修改已保存，但正文尚未开始，仍需确认最终大纲`.
Immediately prepare a new outline-continue confirmation for the same `runId`.
Do not say the outline is already confirmed.

If the model accidentally sends an older confirmation ID, do not reopen this
question. Pass the card's `runId`; `xique_continue_bid` must verify that the run
is still at `awaiting_confirmation/outline-review`, verify that the current
outline signature matches, and atomically consume the matching live record.
One user click must never require a second outline-confirmation click. Never
return to generation configuration, call `xique_prepare_bid`, or create a
replacement run unless the user explicitly requests regeneration.
