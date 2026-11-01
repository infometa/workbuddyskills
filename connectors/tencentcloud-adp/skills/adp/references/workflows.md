# Workflow canvases and mounting

## Fast path

1. Copy a template from [canvas/](canvas/), set `WorkflowName` (unique per app) and
   `WorkflowDesc`, and edit node data only.
2. Write only `Nodes` with their `NextNodeIDs`. Leave out `Edge` and `NodeUI`: the CLI
   derives the connections from `NextNodeIDs` and lays the nodes out.
3. `adp workflow deploy --app-id <app> --canvas-file wf.json --dry-run --format json`.
   It checks the canvas locally (unknown node types, duplicate names, unconnected nodes,
   dead ends) and lists `canvasFixes`. Fix every reported problem, then run it with `--yes`.
4. To change a deployed workflow, deploy again **into the same id**:
   `adp workflow deploy --app-id <app> --workflow-id <wf> --canvas-file wf.json --yes`.
   Do not create renamed copies. The result says `bound: false` because the entry binding
   is left as it was, not removed. This saves the draft only: `--env test` sees it at once,
   but `--env prod` and `adp chat` keep the old version until `adp deploy` releases the app.
5. Draft check in mode 3: `adp workflow run start --app-id <app> --query "<q>" --env test`
   and read `answer`. Publish with `adp deploy`, then `adp chat`.

Inside a project directory every `adp workflow …` command defaults `--app-id` to
`app_id` in `adp.jsonc`.

| Template | Shape | Reply |
|---|---|---|
| [canvas/single.json](canvas/single.json) | START → CODE_EXECUTOR → ANSWER → END | `WF-OK:<user query>` |
| [canvas/llm.json](canvas/llm.json) | START → LLM → ANSWER (`Output.Content`) → END | model reply |
| [canvas/branch.json](canvas/branch.json) | START → LOGIC_EVALUATOR → 2 × ANSWER → END | `BR-YES` / `BR-NO` |
| [canvas/intent.json](canvas/intent.json) | START → INTENT_RECOGNITION → (计算: CODE_EXECUTOR → ANSWER, failure → ANSWER) / (闲聊: ANSWER) / (其他, fallback: ANSWER) → END | `CALC-OK:<query>` / `CALC-FAILED` / `CHAT` / `OTHER` |
| [canvas/option.json](canvas/option.json) | START → OPTION_CARD (基础版 / 专业版) → 2 × ANSWER → END | run pauses (`waiting_input`); `run resume --query 专业版` → `PLAN=PRO` |
| [canvas/dynamic-option.json](canvas/dynamic-option.json) | START → CODE → LOGIC (AND: `GE`, `NOT_CONTAINS`) → dynamic OPTION_CARD → LOGIC (`IN`) → ANSWER → END | query `many` pauses with `options` 北京/上海/广州; resume 北京 → `IN-OK`, 广州 → `NOT-IN`, 火星 → `ELSE`; query `one` → `FEW` |
| [canvas/extract.json](canvas/extract.json) | START → PARAMETER_EXTRACTOR (`date`) → ANSWER (`Output.date`) → END | `DATE=2026-11-03` for 「评审定在2026年11月3日」 |
| [canvas/sub.json](canvas/sub.json) | START(input `topic`) → CODE_EXECUTOR → END(output `result`) | none (child) |
| [canvas/main.json](canvas/main.json) | START → WORKFLOW_REF → ANSWER → END | `MAIN:<child result>` |
| [canvas/deep-research.json](canvas/deep-research.json) | START → 3 × WORKFLOW_REF (plan → research → summarize) → ANSWER → END | `MAIN:<summarize result>` |

## Canvas rules

- One `START`, one `END`. END does not reply: the user sees the **`ANSWER`** node
  (`AnswerNodeData.Answer`, `{{var}}` declared in `Inputs`). There is no `REPLY` type.
- Every node except END lists its successors in `NextNodeIDs`, and every node must be
  reachable from START. Branch nodes put each branch target in its own entry:
  `LogicEvaluatorNodeData.Group[i].NextNodeIDs` (at least 2 groups; the last group without
  `Logical` is else), `OptionCardNodeData.Options[i].NextNodeIDs`,
  `IntentRecognitionNodeData.Intents[i].NextNodeIDs`; the node's own `NextNodeIDs` stays
  empty. The CLI generates the branch edges and handles. See `branch.json`.
- INTENT_RECOGNITION (see `intent.json`): `IntentRecognitionNodeData.{ModelName,
  ModelParams{Temperature,TopP,MaxTokens}, Prompt, Intents[]}`; each intent has `Name`,
  `Desc`, `Example` (one string; an `Examples` array is dropped on save) and its own
  `NextNodeIDs`. The node's own `NextNodeIDs` is `[]`, and the query reaches `Prompt`
  through an `Inputs` entry (`{{q}}`).
- The platform treats the **last** entry of `Intents` as the fallback: it is not offered to
  the model, and every query that matches no other intent goes there. The node output then
  reads `{"IntentIndex": <N>, "IntentName": "Other"}` (`IntentIndex` is 1-based, N = number
  of intents), whatever that intent is called. So always end `Intents` with an explicit
  fallback such as `其他`; a real intent placed last (for example 闲聊) would never be
  recognised and would swallow unrelated queries.
- OPTION_CARD (see `option.json`): `OptionCardNodeData.{Question, Options[], CardFrom}`;
  `Question` is the prompt shown above the buttons, each option is `{Content, NextNodeIDs}`
  (`Content` is the button text; there is no id field), `CardFrom: "INPUT"` for static
  options. The node's own `NextNodeIDs` and `Inputs` stay empty. Downstream nodes read
  `REFERENCE_OUTPUT` `Output.OptionContent` / `Output.OptionIndex`. A run pauses at the
  card (`waiting_input`); answer with one option's `Content`.
- OPTION_CARD dynamic options (console 「动态拉取变量值」, see `dynamic-option.json`, verified on
  the platform): `CardFrom: "DYNAMIC"`, `Options: []`, and `DynamicOptionsRefInputName` names an
  `ARRAY_STRING` entry of the card's own `Inputs` (usually a `REFERENCE_OUTPUT` to an upstream
  list). The options form **one** branch:
  ```json
  "OptionCardNodeData": {
    "Question": "请选择城市：", "Options": [], "CardFrom": "DYNAMIC",
    "DynamicOptionsRefInputName": "cities",
    "DynamicOptionsRefNextNodeIDs": ["route"],
    "DynamicOptionsElseNextNodeIDs": ["fallback"],
    "SystemPrompt": "", "ModelName": "Hunyuan/hy3"
  },
  "Inputs": [{ "Name": "cities", "Type": "ARRAY_STRING",
    "Input": { "InputType": "REFERENCE_OUTPUT", "Reference": { "NodeID": "code1", "JsonPath": "Output.cities" } } }]
  ```
  `DynamicOptionsRefNextNodeIDs` is taken for any listed option, `DynamicOptionsElseNextNodeIDs`
  for a free-text answer that matches none; route on `Output.OptionContent` after it (for example
  LOGIC_EVALUATOR `IN`). The CLI derives both edges and checks the input name and type. A
  dynamic card lists **every** option in the waiting run's `options`.
- Every static OPTION_CARD has a system 「其它」 option as its last choice: a free-text answer that
  matches no option goes there. Like the intent fallback, it is not listed: the waiting run's
  `options` (and `adp chat` `optionCards`) leave the last option out.
- PARAMETER_EXTRACTOR (see `extract.json`): `SaveWorkflow` stores only
  `Parameters[i].{RefParameterID, Required, SubParams}`; a `Name` / `Type` / `Desc` written
  into the node is dropped and the run fails with `NodeErr.RuntimeError`. Declare each
  parameter inline as `{Name, Type (STRING|INT|FLOAT|BOOL), Desc, Required,
  CorrectExamples[], IncorrectExamples[]}`: `adp workflow deploy` registers it for that node
  (LKE `CreateParameter`, not in the public action list), replaces it with the returned
  `RefParameterID`, and lists the ids in `result.parameters`. An entry that already has a
  `RefParameterID` is kept as is. Examples are strings; empty strings are dropped (the
  platform answers `8000999`). Downstream nodes read `Output.<Name>`.
  Redeploying with `--workflow-id` reuses the ids the node already has: the platform rejects a
  second `CreateParameter` with the same name on the node (`500334 参数名称重复`), so deploy
  reads the stored canvas, looks the names up (LKE `GetParameterList`), rewrites those
  definitions in place (LKE `UpdateParameter`) and only creates new names.
- `CorrectExamples` / `IncorrectExamples` steer extraction hard: a value written the way an
  incorrect example is (measured: `10月20日` listed as incorrect) makes the node ask again even
  though the user gave the date. List only formats you really want to refuse.
- PARAMETER_EXTRACTOR input rule: the node reads the user query from the dialog itself, so
  leave `Inputs` empty. A `SYSTEM_VARIABLE` input (for example `SYS.UserQuery`) is rejected by
  the platform (「参数提取节点中不允许引用系统变量」) and by the CLI before anything is sent. To
  feed it preprocessed text, use a `REFERENCE_OUTPUT` input from an upstream node.
  `UserConstraint` is the follow-up dialogue style (language, tone), not the parameter list.
  When a required parameter is missing, the run pauses (`waiting_input`) for the follow-up answer.
- Failure branch on a node (CODE_EXECUTOR in `intent.json`): `ExceptionHandling` with
  `Switch: "ON"`, `HandleMethod: "EXCEPTION_EXECUTE"`, `NextNodeIDs: [<failure node>]` and
  `AbnormalRetrySwitch: "ABNORMAL_RETRY_OFF"`; the success path stays in the node's
  `NextNodeIDs`. A handled failure does not fail the run: the run ends in `state: 2` and the
  failed node's run carries `failCode` (for example `NodeErr.ExecuteCodeFailed`), so read
  `nodeRuns[].failCode` or the reply to tell the branches apart.
- `WorkflowDesc` is plain text: the platform drops `<...>`, so the CLI rewrites it as `{...}`.
- LOGIC_EVALUATOR `CONTAINS` / `EQ` with `MatchType: PRECISE` are case-sensitive (`YES` does
  not contain `yes`); normalise case in a CODE_EXECUTOR first if needed.
- LOGIC_EVALUATOR `Comparison.Operator` (all verified in runs): `EQ` 等于, `NE` 不等于, `GT` 大于,
  `GE` 大于等于, `LT` 小于, `LE` 小于等于 (`LeftType` `INT` or `FLOAT`; the right value is a number
  string such as `"2"`), `CONTAINS` 包含 / `NOT_CONTAINS` 不包含 (`STRING` or `ARRAY_STRING`),
  `IN` 属于 / `NOT_IN` 不属于 (left value against the right `Values[]` list), `IS_SET` 已填充 /
  `NOT_SET` 未填充 (no right value needed). `NEQ` and `UNSPECIFIED` fail the run
  (`NodeErr.ExistUnsupportedOperator`); the CLI rejects them, and numeric operators on a non-number
  `LeftType`, before anything is sent. `LeftType` uses the output types (`STRING`, `INT`, `FLOAT`,
  `BOOL`, `OBJECT`, `ARRAY_STRING`, …).
- Several conditions in one group: `{"LogicalOperator": "AND" | "OR", "Compound": [<single
  conditions>]}` with **no** `Comparison` beside `Compound` (a leftover `Comparison: {}` is read as
  `UNSPECIFIED`; the CLI removes it). A single condition is `LogicalOperator: "UNSPECIFIED"`,
  `Compound: []` and the `Comparison`. See `dynamic-option.json`.
- Node data key is `<Type>NodeData`: `StartNodeData`, `CodeExecutorNodeData`,
  `AnswerNodeData`, `LLMNodeData`, `WorkflowRefNodeData`.
- `NodeID` matches `^[a-zA-Z_][a-zA-Z0-9_]*$`; `NodeName` is unique in the canvas.
- Input sources (`Input.InputType`): `USER_INPUT`, `REFERENCE_OUTPUT`
  (`Reference: {NodeID, JsonPath: "Output.<field>"}`), `SYSTEM_VARIABLE`
  (`SystemVariable: {Name: "SYS.UserQuery"}`), `CUSTOM_VARIABLE`, `NODE_INPUT_PARAM`,
  `ENV_VARIABLE`, `APP_VARIABLE`, `WORKFLOW_VARIABLE`. `CONSTANT`/`TEXT` do not exist.
- CODE_EXECUTOR: `def main(params: dict) -> dict`; returned keys equal
  `Outputs[0].Properties[*].Title`. Types: `STRING`, `INT`, `FLOAT`, `BOOL`, `OBJECT`,
  `ARRAY_*` (no `NUMBER`).
- LLM nodes (see `llm.json`): `LLMNodeData.{ModelName, ModelParams{Temperature,TopP,MaxTokens},
  SystemPrompt, Prompt}`, no `0` params; the next node reads `Output.Content`. Not every
  `adp models` entry works in workflows: an unusable one fails deploy with
  `获取模型信息为空`. `Hunyuan/hy3` works; otherwise pick from the node type's scene:
  `adp models --scene 20` (LLM), 22 (PARAMETER_EXTRACTOR), 23 (LLM_KNOWLEDGE_QA),
  24 (TAG_EXTRACTOR), 25 (INTENT_RECOGNITION), 26 (OPTION_CARD), 27 (LOGIC_EVALUATOR).
  The deploy error's next_action is that scene's list for the failing node (scene 18 is
  Claw apps, not workflows).
- Local check (also `--dry-run`, nothing sent): cycles (`cycle a -> b -> a`, with the edge to
  remove), a `Reference.NodeID` that names no node, and an `Output.<field>` that the source
  node does not declare when it declares outputs (PARAMETER_EXTRACTOR inline parameter
  `Name`s, CODE_EXECUTOR `Outputs[0].Properties[*].Title`). Renaming an extractor parameter
  without updating the readers is caught here, with node id and the declared names. Every
  reference in the node is checked, not just `Inputs`: LOGIC_EVALUATOR `Comparison.Left` /
  `Right`, OPTION_CARD dynamic options, LLM / INTENT prompt variables and END outputs.
- `workflow deploy --dry-run` also checks each LLM / extractor / intent / option card node's
  `ModelName` against `adp models --scene <n>` (read-only): a model the scene does not list fails
  with `WorkflowModelInvalid` and a `models --scene` next action; when the model list cannot be
  read the preview only warns (`WorkflowModelCheckSkipped`).
- Follow-ups after a failed deploy (`WorkflowCanvasInvalid`, `WorkflowModelInvalid`,
  `WorkflowValidationError`) are your own command with every flag kept (`--no-bind`, `--name`,
  `--workflow-id`, `--env`, …); only `--dry-run` / `--yes` change. After a successful deploy in a
  Standard (1) or workflow (3) app the next actions preview another `--no-bind` deploy and
  `adp deploy --dry-run`. `adp deploy --dry-run` warns when workflows will be published even though
  `previewTotal` is 0.
- `workflow deploy --workflow-id … --dry-run` reads the stored canvas and
  `GetParameterList` (read-only) and plans `UpdateParameter` for parameters the node already
  registered, `CreateParameter` only for new ones — the same as the real deploy.
- When the platform rejects a canvas that passed the local check
  (`WorkflowValidationError`), the next_action is the same `workflow deploy` with `--yes`
  instead of `--dry-run` (it writes): edit the node the message names first; re-running
  `--dry-run` proves nothing. That action, and the local re-check after `WorkflowCanvasInvalid`,
  carry `needs_edit: {"file": "<canvas file>"}`: edit that file before running them; running
  them unchanged fails the same way.
- Workflows brought in with `workflow import --enable` need no `workflow deploy`: the next
  `adp deploy` (app release) publishes them along with the app. In the rare case an enabled
  workflow is still `UNPUBLISHED` after a release, `adp deploy` warns
  (`unpublishedWorkflows`) and its next_action re-saves it with `workflow deploy --workflow-id`.

## Nested workflows (WORKFLOW_REF)

1. Children: copy `sub.json` per step (change `WorkflowName` and the code), deploy each with
   `--no-bind`, and note the returned `workflowId`.
   - Child START declares parameters in `StartNodeData.Inputs`; child nodes read them
     with `REFERENCE_OUTPUT` on the START node (`JsonPath` = parameter name).
   - Child END exposes `Outputs[0].Properties[*]` with
     `Value: {InputType: "REFERENCE_OUTPUT", Reference: {NodeID, JsonPath: "Output.result"}}`.
2. Parent: put each child id in `WorkflowRefNodeData.WorkflowID` (in `deep-research.json`,
   replace `<PLAN_WORKFLOW_ID>`, `<RESEARCH_WORKFLOW_ID>`, `<SUMMARIZE_WORKFLOW_ID>`).
   `RefInputs` match the child inputs by `Name` and `Type`; a later step reads the previous
   one with `REFERENCE_OUTPUT` `Output.result`.
   - An `OBJECT` or `ARRAY_*` input also needs `RefInputs[i].SubInputs` listing every child
     field, each with its own `Input.Reference.JsonPath` (for `cfg` read from `Output.cfg`:
     `{Name: "topic", Type: "STRING", Input: {InputType: "REFERENCE_OUTPUT", Reference:
     {NodeID: "code0", JsonPath: "Output.cfg.topic"}}}`). Matching `Name` and `Type` alone
     fails deploy with `<ref NodeID>: 输入参数不匹配`.
3. Deploy the parent last. In a run, `adp workflow run get --sub-workflow-path <ref NodeID>`
   shows a child run, but its `output` can be `{}`; read a child's result with
   `adp workflow run node --node-run-id <id>` on the WORKFLOW_REF node run.

Verified: children returning `PLAN:`, `RESEARCH:`, `SUM:` prefixes reply
`MAIN:SUM:RESEARCH:PLAN:<query>`.

## How each app mode runs a workflow

| app_mode | How the workflow is reached | Steps |
|---|---|---|
| 3 single workflow | Every message runs the entry workflow | `workflow deploy` (binds entry) → `adp deploy` → `adp chat` |
| 1 standard | Routed by `WorkflowDesc` among enabled workflows | `workflow deploy` with a specific `WorkflowDesc` → `adp deploy` → `adp chat` with a query matching the description |
| 4 Claw | The agent calls it as a tool | `workflow deploy --no-bind` → `adp deploy` → `adp agent tool bind --agent-id <id> --plugin-id <wf> --tool-id <wf> --workflow` → add the tool to `agent.tools` in `adp.jsonc` (`tool_source: 1`) → `adp deploy` → `adp chat` |
| 2 Multi-Agent | Tool of an agent, or the collaboration workflow | same as Claw for tools |

- Claw/Multi-Agent: `adp deploy` writes `agent.tools` from `adp.jsonc` as a whole list. A
  tool bound only with `agent tool bind` is removed by the next deploy unless it is also
  in `agent.tools`. Check with `adp agent resources --env prod`.
- A workflow used as an agent tool must not pause for input (no OPTION_CARD,
  TEXT_COLLECTION, FILE_COLLECTION, PARAMETER_EXTRACTOR).
- `adp chat` only talks to the **released** app; before `adp deploy` it fails with
  `AppNotReleased` (platform `460048 应用未发布`, exit 5) and next action `adp deploy`.
- `workflow run start` / `get` return `answer` (the ANSWER node text) when the run-level
  `output` is empty. Only queued, running or waiting runs can be stopped.
- A run that reaches a node waiting for the user (OPTION_CARD, TEXT_COLLECTION,
  PARAMETER_EXTRACTOR follow-up, …) reports `state: 5`, `stateLabel: "waiting_input"`
  (state 5 is not in the public enum). `run start` stops waiting at once and returns
  `status: "waiting_input"` and `question` (the node's latest message, e.g. the
  PARAMETER_EXTRACTOR follow-up 「请提供要查询的日期」, read from ADP `DescribeWorkflowRun`
  `WorkflowRunOutput.LatestMessage`). When that message is an option card
  (`OptionCardList`), `options` lists the choices and the first next action is
  `adp workflow run resume … --query <first option>` (change `--query` to pick another).
  Otherwise (a free-text question such as a PARAMETER_EXTRACTOR follow-up) `options` is `[]`
  and the first next action is `adp workflow run resume --app-id … --run-id … --format json`
  with `needs_input: {"flag": "query", "question": "…"}`: append `--query '<the user's answer>'`
  before running it. A `needs_input` command lacks exactly that one flag (here the required
  `--query`) by design; append it, never a placeholder. The second next action is `adp workflow run get …` (it repeats
  `question`). `adp chat` does the same when the app's reply asks the user something (a
  PARAMETER_EXTRACTOR follow-up such as 「请问要查询哪个城市？」): the next action is
  `adp chat --conversation-id … --format json` with `needs_input: {"flag": "message", "question": "…"}`,
  not a canned `--message "继续"` (the extractor would take 继续 as the value). Run results (start / resume / get) always carry `question` and `options` (`null` when the run is not waiting), so `--fields question,options` works on finished runs too. A terminal `adp chat` reply (no option card, no question) gets no next action: a generic follow-up would only re-enter the workflow. A renamed or removed extractor parameter leaves its old registration on the platform (no public delete API); only the in-place `workflow deploy --workflow-id` that drops it from the canvas lists it under `staleParameters` (the CLI finds registered parameters through the stored canvas's `RefParameterID`s, so once a deploy has saved a canvas without it, later deploys no longer see or list it). Note the `parameterId`s from that deploy if you need them. After an OPTION_CARD, `SYS.UserQuery` in later nodes is the clicked button's text, not the user's original message: to keep the original text, read it from a node that ran before the card (an LLM or PARAMETER_EXTRACTOR output) instead of `SYS.UserQuery`. The `planned` ModifyApp line says when the deploy rebinds the mode 3 entry workflow. `run resume` then waits like `start` for the next terminal
  or waiting state (`--no-wait` returns `status: "resumed"` at once). After a resume the run
  can drop out of state 5 and back within one poll on the same node run (a follow-up asked
  again), so resume counts a state 5 seen 6 s after the resume as the new pause. Answer an
  option card with one option's text exactly as listed in `options`. `run resume` has no
  run-environment flag: the run id already fixes test/prod (`--env` on resume is only the
  global `adp.env.<name>.jsonc` overlay).
