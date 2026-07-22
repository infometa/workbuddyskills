---
name: independent-board-core
description: |
  福帮手独董会的核心协同技能。用于决策起手卡后的场景路由、专用案卷工作空间初始化、席位认知资产选择与哈希绑定、成员任务/结果信封校验、追加式协同事件、检查点标记、长文档交付和证据边界控制。触发词：独董会、独立审议、组席、会议案卷、认知资产、审议备忘录、协同回执、检查点。
user-invocable: false
---

# Independent Board Core

## 使用边界

- 该 Skill 提供确定性协议、词典和本地脚本，不创建团队、不调度 Agent、不发送成员消息，也不证明宿主调用成功。
- `TeamCreate` 必须且只能由 `board-convener` 执行；成员由召集人通过 AgentTool（WorkBuddy 5.2.6 运行时函数名：`Agent`）调度，并经 `SendMessage` 回传。
- 决策起手卡本身可以只在对话中完成；用户确认开始本地独立审议后，必须在当前任务目录内初始化新的 `local_managed` 专用案卷，作为结果恢复与最终产物的边界。初始化失败时不得写入普通目录。
- 共享会议状态只能由 `board-convener` 写入。秘书和专业席只返回信封，由召集人校验并记录。
- 事件默认不存正文、提示词、原始材料或个人信息；只存运行元数据、摘要哈希和回执引用。

## 参考资料

- 事件与证据规则：@references/event-contract.md
- 专用工作空间与恢复：@references/workspace-policy.md
- 场景词典：@references/scene-lexicon.v1.json
- 认知资产目录：@references/cognitive-assets/manifest.v1.json
- 认知资产来源与权利边界：@references/cognitive-assets/source-ledger.v1.json
- 长文档与产物质量门：@references/document-delivery.md

## 命令

命令从专家包根目录执行。所有脚本只向 stdout 输出 JSON 回执；失败时非零退出。

```text
node skills/independent-board-core/scripts/board-workspace.mjs init --workspace <专用空目录> --workspace-id <随机ID>
node skills/independent-board-core/scripts/board-workspace.mjs status --workspace <目录>

node skills/independent-board-core/scripts/board-route.mjs < route-input.json
node skills/independent-board-core/scripts/board-assets.mjs catalog validate --as-of <运行日期>
node skills/independent-board-core/scripts/board-assets.mjs decision-card hash < decision-card-hash-request.json
node skills/independent-board-core/scripts/board-assets.mjs bundle build --workspace-root <目录> < asset-selection-request.json
node skills/independent-board-core/scripts/board-assets.mjs bundle verify --workspace-root <目录> < asset-bundle-verification-request.json
node skills/independent-board-core/scripts/board-envelope.mjs proposal < seat-proposal.json
node skills/independent-board-core/scripts/board-envelope.mjs plan < review-plan.json
node skills/independent-board-core/scripts/board-envelope.mjs task < member-task.json
node skills/independent-board-core/scripts/board-envelope.mjs result < member-result.json
node skills/independent-board-core/scripts/board-envelope.mjs delivery < member-delivery-observation.json
node skills/independent-board-core/scripts/board-envelope.mjs failure < member-failure-envelope.json

node skills/independent-board-core/scripts/board-record.mjs plan --workspace <目录> --input <计划草稿.json> --actor board-convener
node skills/independent-board-core/scripts/board-record.mjs task --workspace <目录> --input <任务草稿.json> --actor board-convener
node skills/independent-board-core/scripts/board-record.mjs result --workspace <目录> --input <结果草稿.json>
node skills/independent-board-core/scripts/board-record.mjs delivery --workspace <目录> --input <投递观察草稿.json>
node skills/independent-board-core/scripts/board-record.mjs failure --workspace <目录> --input <失败草稿.json> --actor board-convener
node skills/independent-board-core/scripts/board-collect.mjs --workspace <目录> --run <runId>
node skills/independent-board-core/scripts/board-delivery.mjs --workspace <目录> --run <runId> --artifact <deliverables内文件> --type <quick_review_card|review_memo|deep_review_preparation_card>

node skills/independent-board-core/scripts/board-event.mjs append --workspace <目录> --run <runId> < event-input.json
node skills/independent-board-core/scripts/board-event.mjs verify --workspace <目录> --run <runId>
node skills/independent-board-core/scripts/board-checkpoint.mjs --workspace <目录> --run <runId> --state <state> --actor board-convener
```

`route-input.json` 只在进程内用于词典匹配，不被脚本保存。任务与结果模板见 `templates/`。

## 推荐执行顺序

1. 召集人先在对话中形成决策起手卡候选；按改变结论的可能性对候选席排序，把建议模式、专业席和流程支持席送入 `board-envelope.mjs proposal`。只有回执 `ok=true` 时才展示其 `normalized` 选席：快审恰好 1 个专业席，标准/深度准备为 2—3 个专业席。该预检不写工作空间、不需要用户确认，也不证明建团或宿主动作；未获用户确认不得建团。
2. 需要场景提示时，将最小必要文本通过 stdin 送入 `board-route.mjs`；结果只是路由提示，必须由召集人确认。
3. 用户确认开始独立审议后，先初始化新的专用工作空间；对非空且未标记目录必须失败关闭。把绝对工作空间和 `board-record.mjs` 路径随任务信封下发。
4. 用户确认议案卡后，召集人先以 `package_local_observation` 追加 `meeting.opened`、`agenda.registered`，再把已确认起手卡送入 `decision-card hash`，只取 `decisionCardHash`；用计划模板冻结 1—5 个议题、审议模式、2—3 席或快审 1 席、可选流程支持席和该摘要。依次运行 `board-envelope.mjs plan` 与 `board-record.mjs plan --actor board-convener`，把返回的精确 `payloadHash` 作为 `user_confirmation` 写入 `plan.frozen`。只有该哈希绑定事件成功后才能请求 `TeamCreate`；计划、本地记录和事件都不证明宿主建团成功。
5. 同一 `runId` 的计划文件固定为 `.fbsir-board/plans/<runId>.json`，冻结后不可覆盖。用户改题或变更已确认计划时终止旧运行并使用新 `runId` 重建起手卡与计划，不得让旧任务、结果或意见晋级。
6. 以运行当日校验资产目录。为每个议题 × 专业席构建并验证 `phase1_independent` 包；秘书使用 `phase1_process_support`。首轮每包仅一张本席方法卡和一张清单。
7. 召集人用任务模板生成每席独立切片，写明确定性的结果/投递观察目标，并在 `evidenceRefs` 中放且只放一个已验证的本席 `assetbundle:<sha256>`。依次运行 `board-envelope.mjs task` 与 `board-record.mjs task --actor board-convener`，确认任务落在 `tasks/<agenda>/<seat>.task.r<revision>.json` 后，才可通过 AgentTool/Agent 派发。专业席使用 `professional_review`；秘书仅可使用 `process_support`，不得提交投票或专业结论。
8. 成员先复核自己的资产包，结果回显同一资产引用，再用 `board-record.mjs result` 耐久记录结果并调用真实 `SendMessage`；只有工具成功后才能用 `board-record.mjs delivery` 记录成员侧成功观察。两种文件都不能冒充宿主签名回执或主会话消费证明。
9. 每次成员消息或团队终态唤醒都运行 `board-collect.mjs`。收齐器会再次验证计划、任务、本席资产文件、结果引用和当前修订；只有 `readyForSynthesis=true` 才能汇编。缺口最多重试一次，仍失败由召集人写入当前修订的失败信封。系统终态通知和 UI 绿勾本身都不是收齐证明。
10. 由召集人按直接事实追加事件。只有真实宿主回执可写 `team.created`、`seat.dispatched`、`seat.result_received`；从案卷恢复的有效结果写 `seat.result_recovered` 并绑定精确 `resultPayloadHash`，一次重试后的失败写 `seat.result_failed` 并绑定精确 `failurePayloadHash`，两者都保持 `package_local_observation`，不得升级为宿主回执。
11. 所有选定席位有哈希绑定的结果或失败事件后封存首轮。收齐器返回 `readyForSynthesis=true` 后，以精确 `collectionPayloadHash` 追加 `collection.ready`；生成模式对应 Markdown 后，以文件内容 SHA-256 追加 `memo.compiled`，再运行 `board-delivery.mjs`。交付器必须同时复核结果/失败、收齐和产物四类事件绑定。
12. 首轮封存后才能用新修订号构建 `phase2_challenge` 反例/案例短包；不得覆盖首轮包。Phase 3 为召集人构建自己的汇编方法包，但不允许代写专业意见。
13. 每个关键阶段验证事件链并创建检查点标记。哈希链损坏时停止晋级，保留文件并由用户决定后续处理。
14. 按决策质量六链检查框架、替代、信息、取舍、推理和执行承诺，建立选择、指标、触发器、负责人和复审日期的决策日志。文件存在、`readyForSynthesis` 和 `ready_to_present` 都不等于用户验收。

## 失败降级

- Node 或 Bash 不可用：继续公开核心对话流程，但标记 `script_runtime_unavailable`，不声称有本地事件链或恢复能力。
- 工作空间未初始化：拒绝写入并建议用户选择专用空目录；不得改写其他目录。
- 宿主团队能力不可用：返回决策起手卡和恢复建议，不生成带席位归因的结论。
- 回执缺失：相应宿主事实不得进入事件链；本地“请求已记录”不能升级为宿主成功。成员侧成功观察可以恢复内容，但必须标注主会话消费未证明。
- 资产目录、构建或验证失败：停止受影响席位的派发或汇编；不得读取旧包、跨席包或绕过 `assetbundle` 绑定继续。
- 事件链损坏：停止晋级并保留原文件；哈希链只能发现未重算的意外改动，不是带外锚定或抗攻击证明，当前检查点也不自动恢复内容。
- 信封含未声明字段、席位类别不匹配或流程支持角色尝试提交专业意见：失败关闭，不透传未知字段。
