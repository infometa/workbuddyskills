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
- 包版本与工作区 release tuple 分开判断：当前包为 `26.8.19`，新案卷只写 exact `fbsir.board-workspace/v2 + fbsir.board-event/v2 + productVersion=26.8.19`；exact `v2@26.8.1` 是 `predecessor_read_only`，exact `v1@26.7.20` 是 `legacy_read_only`。混合、扩展或未知 tuple 均为 `unsupported`，不得按 semver 范围晋升。
- 续办只读案卷时，先以 `node skills/independent-board-core/scripts/board-resume.mjs inspect --source-workspace <旧案卷> --source-run <旧run>` 重算摘要。exact `v2@26.8.1` 生成 `fbsir.predecessor-resume-digest/v2`，exact `v1@26.7.20` 继续生成 `fbsir.legacy-resume-digest/v1`。结果只绑定 marker、plan、事件链、checkpoint、collection、delivery 与 deliverables 的字节身份，不证明正文事实、宿主回执或新 run 已完成；不得改写源案卷。
- 展示续办状态时，调用方必须提供签发时得到的 exact digest：current 使用 `board-checkpoint.mjs` 返回的 `checkpointReceiptDigest`，predecessor/legacy 使用 `inspect` 返回的相应 resume digest。运行 `board-resume.mjs card --workspace <案卷> --run <runId> --receipt-digest <hex>` 只读生成 exact `fbsir.case-resume-card/v1`；缺少、失配、不支持或源漂移均输出证据不足卡且不回显正文、路径、runId 或文件名。`--inspect-only` 仅在本次卡片展示中隐藏继续动作，不构成对独立 action envelope 的全局撤销。
- current 卡先通过完整工作空间事件验证器，里程碑只来自重放后的事件链，绝不解释 checkpoint 自由文本 `state`，也不读取 digest 未绑定的独立材料记录；terminal run 不展示继续动作，其他 current run 确认后只能续同一 run。predecessor/legacy 卡不声称任何已观察完成节点，只展示实际存在的各自 `*_bound` 字节绑定；确认后必须使用与旧 run 不同的新 26.8.19 run。三类回执都没有负责人、期限或复审日期时固定标注 `not_present_in_receipt`，不得发明责任状态。
- 用户明确确认继续后，先初始化独立的新 26.8.19 workspace，再以 `node skills/independent-board-core/scripts/board-resume.mjs record --source-workspace <旧案卷> --source-run <旧run> --workspace <新案卷> --run <新run>` 把 exact digest 写入新案卷 `.fbsir-board/predecessors/<新run>.json`。新续办 plan 的 `predecessorRunRef` 必须是 exact `fbsir.predecessor-run-ref/v2` 六字段对象并绑定 receipt schema 与摘要；既有 `v1` 引用只保留兼容读取。fresh plan 必须为 `null` 且同 run 不得已有 receipt。旧 task/result/event 只能作历史材料，不能关闭新 run。
- 共享会议状态只能由 `board-convener` 写入。秘书和专业席只返回信封，由召集人校验并记录。
- 事件默认不存正文、提示词、原始材料或个人信息；只存运行元数据、摘要哈希和回执引用。
- `known_relative_paths_no_directory_exploration`：首次响应直接使用本 Skill 已列出的固定相对路径。确需确认字段时，只可直接读取 `templates/entry-intent-envelope.json`、`templates/material-card-draft.json`、`templates/seat-proposal-envelope.json`，不得扫描目录、Grep 核心源码或重新发现契约结构，也不把探查声明交付给用户；仍不能构造预检输入时进入安全 fallback。
- `entry_retry_budget_one`：`entry` 首次失败后只允许修正 envelope 并重跑 1 次；运行时不可用或第二次仍失败时立即安全降级，不再探查或循环重试，也不声称 `normalized.route` 或确定性回执。
- `material_card_retry_budget_zero`：每个首次响应最多调用 1 次 `material-card`；首个对应回执具有终结吸收性，任意 `ok !== true` 都立即短路剩余预检并进入安全 fallback。不得改 draft 重跑，不得在失败后继续 `proposal`，不得让后续成功覆盖首个失败。`impact` 只允许 `may_change_framing / may_change_option / may_change_option_or_reversibility / may_change_risk_or_legality / may_change_timing_or_accountability`；`blockingFor` 只允许 `conditional_conclusion / definitive_conclusion / irreversible_recommendation`，不得自造近义词。
- `proposal_retry_budget_one`：`proposal` 首次失败后只允许重排候选席并重跑 1 次；第二次仍失败时立即安全降级，不再重排或循环，也不声称选席校验通过。
- `preflight_before_user_visible_plan`：`entry` 及决策入口上的 `material-card → proposal` 是只读预检，预检完成前不输出用户可见计划，预检过程不构成首值。
- `silent_preflight_tool_sequence`：从收到用户输入到完整终态卡组装完成，工具调用前、工具调用之间、工具结果后均禁止生成 `role=assistant` 的 message / `output_text`，无论是否被宿主标为 `status=completed`；直接调用工具，只允许 function call / function result 先于终态卡。若模型或宿主不能保持静默，跳过预检并把完整安全 fallback 作为唯一 assistant message，禁止先发前导、进度或过渡播报。
- `preflight_receipt_non_disclosure`：`entry / material-card / proposal` 的调用、顺序、次数、通过或失败、`ok`、错误码、重试和回执都只供内部判定；首轮唯一终态不得提及或汇总这些状态。终态直接从 `【你真正要决定的事】` 开始，不加标题或前言；最后三个非空行必须逐字为 `【主动作】1 按建议开始独立审议`、`【次级分支】2 补充关键事实`、`【次级分支】3 切换审议模式`，第三行后不得再有文字。
- `decision_intake_single_turn_terminal_gate`：`decision_intake / material_review_intake` 的首个 completed 回复必须同轮交付五段起手卡、材料卡、最多 2 个决定性问题和恰好一主两支；缺任一项时继续本轮，不能停在计划或占位内容。
- `decision_question_mark_budget`：首个终态全文的半角 `?` 与全角 `？` 合计最多 2 个；追问只允许独立物理行 `1. …？` 和可选的 `2. …？`，每行恰好 1 个问号。禁止 `Q1`、项目符号、Markdown 加粗编号、续行、跳号或在规范问题行之外放问号；其余缺口以陈述句折叠进“最小补材”，输出前按字符和行格式复核。
- `safe_decision_start_card_fallback`：Node 不可用、`entry` 在唯一修复后仍失败、`material-card` 失败，或 `proposal` 在唯一重排修复后仍失败时，仍交付不声称 normalized route 或确定性回执的安全起手卡；材料卡保留六个固定栏目但只写未校验边界，保持零案卷、零事件、零建团。

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
node skills/independent-board-core/scripts/board-envelope.mjs entry < entry-intent.json
node skills/independent-board-core/scripts/board-envelope.mjs material-card < material-card-draft.json
node skills/independent-board-core/scripts/board-envelope.mjs material-inspect < material-sufficiency.json
node skills/independent-board-core/scripts/board-envelope.mjs proposal < seat-proposal.json
node skills/independent-board-core/scripts/board-envelope.mjs action < host-action.json
node skills/independent-board-core/scripts/board-envelope.mjs plan < review-plan.json
node skills/independent-board-core/scripts/board-envelope.mjs task < member-task.json
node skills/independent-board-core/scripts/board-envelope.mjs result < member-result.json
node skills/independent-board-core/scripts/board-envelope.mjs support-handoff < process-support-handoff.json
node skills/independent-board-core/scripts/board-envelope.mjs delivery < member-delivery-observation.json
node skills/independent-board-core/scripts/board-envelope.mjs failure < member-failure-envelope.json

node skills/independent-board-core/scripts/board-record.mjs plan --workspace <目录> --input <计划草稿.json> --actor board-convener
node skills/independent-board-core/scripts/board-record.mjs task --workspace <目录> --input <任务草稿.json> --actor board-convener
node skills/independent-board-core/scripts/board-record.mjs result --workspace <目录> --input <结果草稿.json>
node skills/independent-board-core/scripts/board-record.mjs delivery --workspace <目录> --input <投递观察草稿.json>
node skills/independent-board-core/scripts/board-record.mjs failure --workspace <目录> --input <失败草稿.json> --actor board-convener
node skills/independent-board-core/scripts/board-record.mjs material-card --workspace <目录> --run <runId> --input <无引用材料草稿.json> --actor board-convener
node skills/independent-board-core/scripts/board-record.mjs public-source --workspace <目录> --run <runId> --input <仅sourceDigest.json> --actor board-convener
node skills/independent-board-core/scripts/board-record.mjs claim-index --workspace <目录> --run <runId> --artifact <deliverables内文件> --input <ordinal与evidenceRefs.json> --actor board-convener
node skills/independent-board-core/scripts/board-collect.mjs --workspace <目录> --run <runId>
node skills/independent-board-core/scripts/board-delivery.mjs --workspace <目录> --run <runId> --artifact <deliverables内文件> --type <quick_review_card|review_memo|deep_review_preparation_card>

node skills/independent-board-core/scripts/board-event.mjs append --workspace <目录> --run <runId> < event-input.json
node skills/independent-board-core/scripts/board-event.mjs register-host-receipt --workspace <目录> --run <runId> < host-receipt-observation.json
node skills/independent-board-core/scripts/board-event.mjs verify --workspace <目录> --run <runId>
node skills/independent-board-core/scripts/board-checkpoint.mjs --workspace <目录> --run <runId> --state <state> --actor board-convener
node skills/independent-board-core/scripts/board-resume.mjs card --workspace <目录> --run <runId> --receipt-digest <hex> [--inspect-only]
node skills/independent-board-core/scripts/board-resume.mjs inspect --source-workspace <旧案卷> --source-run <旧run>
node skills/independent-board-core/scripts/board-resume.mjs record --source-workspace <旧案卷> --source-run <旧run> --workspace <新案卷> --run <新run>
```

`route-input.json` 只在进程内用于词典匹配，不被脚本保存。任务与结果模板见 `templates/`。`board-record.mjs plan` 会自动以 `actionInstanceId` 为键原子占用工作空间内的确认动作，并写入 `receipts/action-confirmations/<actionInstanceId>.json`；受支持流程不得跳过命令而手写、复制或重算该记录。

## 推荐执行顺序

首轮执行以下第 1 步时必须保持 `silent_preflight_tool_sequence`：不要在工具调用前说“现在让我查看”，不要在工具调用之间报告“我将按顺序执行”，也不要在工具结果后说“入口校验通过，现在继续”。直接连续调用已知命令，所有用户可见文字合并到唯一终态卡；无法保持静默时不调用工具，直接交付完整安全 fallback。

1. 首次响应直接从专家包根目录的已知相对路径运行 `board-envelope.mjs entry`，不扫描目录；只有 exact `fbsir.entry-intent/v1` 回执 `ok=true` 才按 normalized route 继续。首次失败只允许修正 envelope 并重跑 1 次；运行时不可用或第二次仍失败时立即进入不声称 normalized route 或确定性回执的安全 fallback。`decision_intake` 与 `material_review_intake` 随后构造不含任何引用的 exact `fbsir.material-card-draft/v1`；`impact / blockingFor` 逐字使用 `material_card_retry_budget_zero` 列出的枚举，且每轮只运行 1 次 `board-envelope.mjs material-card`。只有该原子命令可以生成首轮材料卡引用：核心在同一进程内 CSPRNG mint `mat_/gap_/ref_`、复算三态并返回 `normalized + slotBindings`；首轮 status 只能是 `received_unverified / received_conflicted`，无 workspace-bound verifier 时自报 `received_verified` 必须失败关闭；调用方自带引用、state、policy、nextAction 或 pending 列表也必须失败关闭。首个材料回执 `ok !== true` 时立即停止，不调用 `proposal`、不修改 draft、不第二次调用 `material-card`，直接交付安全 fallback；直接 `board-envelope.mjs material` 已硬禁用，`material-inspect` 也不能用于修复或证明首轮 builder provenance。只有首个材料回执 `ok=true`，才按改变结论的可能性对候选席排序，把建议模式、专业席和流程支持席送入 `board-envelope.mjs proposal`。只有回执 `ok=true` 时才展示其 `normalized` 选席：快审恰好 1 个专业席，标准/深度准备为 2—3 个专业席；首次失败只允许重排候选席并重跑 1 次，第二次仍失败时立即安全 fallback。三项预检都不写工作空间、不需要用户确认，也不证明材料真实、建团或宿主动作；所有预检状态遵守 `preflight_receipt_non_disclosure`，未获用户确认不得建团。首个 completed 回复必须通过上述 `decision_intake_single_turn_terminal_gate`；脚本不可用或失败时按 `safe_decision_start_card_fallback` 交付保守卡，不得把脚本故障作为首值阻断。
2. 需要场景提示时，将最小必要文本通过 stdin 送入 `board-route.mjs`；结果只是路由提示，必须由召集人确认。
3. 用户明确选择 `confirm_review` 后，把确认版本起手卡送入 `decision-card hash`，构造与该卡片哈希、审议模式绑定的 exact `fbsir.host-action-envelope/v1`，运行 `board-envelope.mjs action`。只有回执 `ok=true` 才继续；动作文字或失败回执均不得当作确认。随后初始化新的专用工作空间；对非空且未标记目录必须失败关闭。把绝对工作空间和 `board-record.mjs` 路径随任务信封下发。
4. 构造 exact `fbsir.review-plan/v2`：1—5 个议题、审议模式、2—3 席或快审 1 席、可选流程支持席、同一卡片哈希，`confirmationAction` 必须绑定上一步的 `actionId + actionInstanceId + actionEnvelopeDigest`；fresh run 的 `predecessorRunRef` 为 `null`，只读续办则必须精确绑定同 run predecessor receipt 的路径、canonical payload hash、旧 run hash、摘要 schema 与摘要。先运行 `board-envelope.mjs plan`；回执 `ok=true` 后以 `package_local_observation` 追加 `meeting.opened`、`agenda.registered`，再运行 `board-record.mjs plan --actor board-convener`。resume receipt 与 plan 共用 run 级 plan lock；记录命令会原子复核 predecessor 并建立同工作空间内的动作所有权。缺失、漂移、失配或已被另一计划占用时必须停止，禁止另造摘要旁路。
5. 把记录命令返回的精确 `payloadHash` 和计划中的 `confirmationReceiptId` 以 `user_confirmation` 写入 `plan.frozen`。冻结和后续账本复核都会重验动作所有权记录；只有全部成功后才能请求 `TeamCreate`。同一 `runId` 的计划不可覆盖，同一 `actionInstanceId` 在同一工作空间内只能归属一个精确运行、修订、回执和计划哈希；相同绑定可幂等重试。确认记录已发布但 plan 尚未落盘时，同 run 只允许原动作和原计划精确续写；`PLAN_CONFIRMATION_RUN_REPLAY` 表示调用方试图给该 run 换动作，必须停止。用户改题或变更已确认计划时终止旧运行，获取新的明确确认与新 `actionInstanceId`，再以新 `runId` 重建，不得沿用旧任务、结果或意见。
6. 以运行当日校验资产目录。为每个议题 × 专业席构建并验证 `phase1_independent` 包；秘书使用 `phase1_process_support`。首轮每包仅一张本席方法卡和一张清单。
7. 召集人用任务模板生成每席独立切片，写明确定性的结果/投递观察目标，并在 `evidenceRefs` 中放且只放一个已验证的本席 `assetbundle:<sha256>`。依次运行 `board-envelope.mjs task` 与 `board-record.mjs task --actor board-convener`，确认任务落在 `tasks/<agenda>/<seat>.task.r<revision>.json` 后，才可通过 AgentTool/Agent 派发。专业席使用 `professional_review`；秘书仅可使用 `process_support`，不得提交投票或专业结论。26.8.19 的秘书新结果必须是 `fbsir.process-support-result/v1`，固定 `receiptId=unavailable`、`deliveryStatus.receiptObserved=false`、唯一任务 `assetbundle` 和 `sourceLedger={entries:[],pendingVerification:[],mutationAllowed:false}`，且不得自报 `tool_success_observed`；新材料一律退回召集人重建材料卡。旧 `fbsir.member-result/v1 + process_support` 仅兼容只读解析/展示；`board-record.mjs result` 和公开 `board-envelope.mjs result` 必须拒绝新写/新验，收齐器也不得将其计为新运行的 accepted/resolved。记录器在写前绑定任务完整 `evidenceRefs` 并原子返回 exact target/hash handoff；秘书不得自行构造，只能经 `board-envelope.mjs support-handoff` 重验，`SendMessage` 只发送 normalized handoff，不得添加自由文本。
8. 成员先复核自己的资产包，结果回显同一资产引用，再用 `board-record.mjs result` 耐久记录结果并调用真实 `SendMessage`；只有工具成功后才能用 `board-record.mjs delivery` 记录成员侧成功观察。两种文件都不能冒充宿主签名回执或主会话消费证明。
9. 每次成员消息或团队终态唤醒都运行 `board-collect.mjs`。收齐器会再次验证计划、任务、本席资产文件、结果引用和当前修订；只有 `readyForSynthesis=true` 才能汇编。缺口最多重试一次，仍失败由召集人写入当前修订的失败信封。系统终态通知和 UI 绿勾本身都不是收齐证明。
10. 由召集人按直接事实追加事件。`board-event.mjs register-host-receipt` 只能登记未核验宿主摘要，返回的 `rcpt_` 不得用于推进宿主成功事件；当前尝试会固定失败 `HOST_RECEIPT_EXTERNAL_VERIFIER_REQUIRED`。只有服务/连接器侧外部可信 verifier 门真正闭合后，才可引入独立的 verified receipt 写入路径并把对应宿主动作解释为已证明成功；从案卷恢复的有效结果写 `seat.result_recovered` 并绑定精确 `resultPayloadHash`，一次重试后的失败写 `seat.result_failed` 并绑定精确 `failurePayloadHash`，两者都保持 `package_local_observation`。
11. 所有选定席位有哈希绑定的结果或失败事件后封存首轮。收齐器返回 `readyForSynthesis=true` 后，以精确 `collectionPayloadHash` 追加 `collection.ready`；生成模式对应 Markdown 后，先把需审计主张写成显式可见分类标签。未核验、冲突或缺失的事实标签必须在正文显示“按假设/未知处理”。运行 `board-record.mjs claim-index` 建立同一 artifact SHA 的 digest-only 索引，再追加 `memo.compiled` 并运行 `board-delivery.mjs`。交付器必须同时复核主张索引、结果/失败、收齐和产物事件绑定；显式标签门不证明未标记语句完整性或事实真实性。
12. 首轮封存后才能用新修订号构建 `phase2_challenge` 反例/案例短包；不得覆盖首轮包。Phase 3 为召集人构建自己的汇编方法包，但不允许代写专业意见。
13. 每个关键阶段验证事件链并创建检查点标记，保存命令返回的 `checkpointReceiptDigest`，后续续办卡必须由调用方重新提供该 exact digest。checkpoint 签发与事件追加共用 run lock；相同最新 `checkpoint.created` 绑定的并发/串行重试返回同一既有 payload digest 且不改写文件，只有新的合法 checkpoint 事件才能推进绑定。该摘要只绑定 canonical checkpoint payload 与已重放事件链，不证明 checkpoint `state` 的业务语义、正文真实性、宿主签名或用户确认。哈希链损坏时停止晋级，保留文件并由用户决定后续处理。
14. 按决策质量六链检查框架、替代、信息、取舍、推理和执行承诺，先构造 exact `fbsir.decision-record/v1` pending 对象并运行 `board-envelope.mjs decision`；通用 validator 只接受 `confirmation_pending`，成功仅返回摘要，不回显正文。`contracts/decision-confirmation-gate.json` 为 `productionEnabled=false` 或 dedicated writer 未启用时，必须停在 pending，通用 `appendEvent(user.confirmed)` 固定失败 `DECISION_DEDICATED_WRITER_REQUIRED`。`artifact.presented` 必须先绑定 exact artifact payload hash；服务侧 finalized exact retry、nonce replay、受信外部 verifier 与 same-binding claim 全部闭环前，不得写 confirmed record、追加确认事件或宣称用户验收。文件存在、`readyForSynthesis` 和 `ready_to_present` 都不等于用户验收。

动作所有权记录只证明受支持 CLI 路径在同一主机、同一 PID namespace 的本工作空间内完成包本地耐久占用与精确计划绑定，不证明真实用户点击、宿主执行、连接器/服务 ACK、跨工作空间全局防重放、正式上架或自然流量，也不证明网络共享目录上的跨主机互斥。本地可写工作空间不属于防篡改信任根，包无法鉴别拥有文件写权限者构造的完整自洽手写记录；记录或 plan 被删除时必须保留至少一份耐久归属证据，不能把本地文件当作权威确认凭证。

## 失败降级

- Node 或 Bash 不可用：继续公开核心对话流程，但标记 `script_runtime_unavailable`，不声称有本地事件链或恢复能力。
- 工作空间未初始化：拒绝写入并建议用户选择专用空目录；不得改写其他目录。
- 宿主团队能力不可用：返回决策起手卡和恢复建议，不生成带席位归因的结论。
- 回执缺失：相应宿主事实不得进入事件链；本地“请求已记录”不能升级为宿主成功。成员侧成功观察可以恢复内容，但必须标注主会话消费未证明。
- 资产目录、构建或验证失败：停止受影响席位的派发或汇编；不得读取旧包、跨席包或绕过 `assetbundle` 绑定继续。
- 事件链损坏：停止晋级并保留原文件；哈希链只能发现未重算的意外改动，不是带外锚定或抗攻击证明，当前检查点也不自动恢复内容。
- 信封含未声明字段、席位类别不匹配或流程支持角色尝试提交专业意见：失败关闭，不透传未知字段。
