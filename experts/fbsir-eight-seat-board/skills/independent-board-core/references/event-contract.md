# 协同事件与证据合同

包版本与工作区 release tuple 分离：当前包为 `26.8.10`，新案卷固定写入 exact `fbsir.board-workspace/v2 + fbsir.board-event/v2 + productVersion=26.8.10`。只读 allowlist 另含 exact `v2@26.8.1` predecessor 与 exact `v1@26.7.20` legacy；前者按冻结 v2 语义和 workspace scope 重验，后者按冻结 v1 语义重验。两者都不得补字段、改 marker 或晋升为可写。混合 schema/release、扩展 marker 或未知版本统一 unsupported，所有写入口在产生 lock、temp、目录或文件前失败关闭。

统一门禁对事件账本设置资源上限：单工作空间最多 1024 个账本、单账本最多 16 MiB 且最多 10000 条事件；超限按事件链无效失败关闭，避免状态探测或任一写入口被无界历史数据拖垮。

## 前序与 Legacy Resume Digest

`fbsir.predecessor-resume-digest/v2` 只接受 exact `fbsir.board-workspace/v2@26.8.1` 作为 source，并在 `source.workspaceRelease` 中同时绑定 workspace schema、event schema 与 product version；公开 receipt 固定为 `source + bindings + predecessorResumeDigest + accessMode + contentExported`。该 tuple 不是当前包的 `packageVersion`，不得只比较单个版本字符串。

`fbsir.legacy-resume-digest/v1` 只接受 exact `fbsir.board-workspace/v1@26.7.20` 作为 source。公开 receipt 固定为 `source + bindings + legacyResumeDigest + accessMode + contentExported`，不含 `generatedAt`、正文或绝对路径。`legacyResumeDigest` 使用域 `fbsir.legacy-resume-digest/v1` 加 NUL 分隔符，对 `{source, bindings, byteInventory}` 的 canonical JSON 做 SHA-256；隐藏 `byteInventory` 覆盖 marker、指定 run 的 plan/event/checkpoint/collection/delivery，以及按相对路径排序的 deliverables 文件长度与原始字节 SHA。deliverables 清单另用域 `fbsir.deliverable-inventory/v1` 计算摘要。

`fbsir.case-resume-card/v1` 是 content-free 的用户可见投影。current 卡要求调用方提供 `board-checkpoint.mjs` 签发的 exact `checkpointReceiptDigest`，先经过完整工作空间事件验证器，再重放当前 marker、事件链、最新 `checkpoint.created`，以及存在时的冻结计划绑定；只从事件链生成 `observedMilestoneIds`，checkpoint `state` 不构成业务完成证据，独立材料记录因未被该 digest 绑定而不投影。terminal run 固定不展示同 run 继续动作。predecessor/legacy 卡分别要求 exact `predecessorResumeDigest` / `legacyResumeDigest`，`observedMilestoneIds` 固定为空，只按实际存在组件生成各自前缀的 `evidenceBindingIds`。三类卡均固定 `contentIncluded=false`、`writesPerformed=false`，缺失、失配、不支持或漂移时不回显敏感来源；`--inspect-only` 只隐藏本次卡片 CTA，不撤销独立 action envelope，也不提升证据。非 terminal current 确认继续必须保持同一 run，predecessor/legacy 必须使用不同的新 26.8.10 run。

checkpoint 签发与事件追加共用同一 run lock。相同最新 `checkpoint.created`、state、event count 与 chain head 的首次并发或后续串行重试必须收敛到同一既有 canonical payload digest，且不改写 checkpoint bytes；已有 checkpoint 只有在其旧绑定仍可由历史链重验、同时当前链已有更新的合法 `checkpoint.created` 时才允许推进。该 digest 不是宿主签名，也不绑定独立材料记录或正文。

`inspect` 对 predecessor/legacy 源案卷零写；`record` 只允许把 exact receipt 写入独立 current `v2@26.8.10` 案卷的 `.fbsir-board/predecessors/<targetRunId>.json`。source/target 相同或互相嵌套、检查时可见的路径链接、硬链接、超限文件、同 target run 的不同摘要都失败关闭。脚本使用 bigint 文件身份、打开句柄前后状态与 exact captured bytes 校验来检测所观察到的并发变化，并以独占临时文件加硬链接完成合作式单写者发布；标准 Node 路径 API 不能证明多个 source 文件构成原子快照，也不能证明恶意同身份进程未在检查间隙替换父目录。需要抵御该类对抗性并发时，调用方必须额外提供受信 ACL/独占执行边界或原生 `openat`/`linkat` 辅助证明，否则不得提升此 receipt 的证据等级。该 receipt 只证明稳定句柄捕获且可复算的旧字节身份，不证明旧内容为真、真实宿主回执、新 run 已收齐、listed/production 或产品成效。

新续办 plan 使用 exact `fbsir.predecessor-run-ref/v2`，字段固定为 `schema + receiptRef + receiptPayloadHash + sourceRunIdHash + resumeDigestSchema + resumeDigest`；既有 `fbsir.predecessor-run-ref/v1` 只为已冻结 legacy 计划保留兼容读取。`receiptRef` 必须逐字等于 `.fbsir-board/predecessors/<当前runId>.json`；读取时 receipt 必须是无链接普通文件，原始字节必须等于规范化对象的 pretty JSON + LF，receipt schema、摘要与完整旧 release/只读字段均重验。fresh plan 只允许 `null` 且同 run 不得存在 predecessor receipt。resume record 与 plan record 共用 run 级 plan lock，避免 `null` plan 与并发 receipt 共存；plan 记录、`plan.frozen`、成员工件写入和 collection 均重复验证 receipt，漂移即失败关闭。

collection 不能只凭 task/result/SendMessage observation 文件进入 `ready_for_synthesis`；旧 task/result/event 即使被复制到新案卷也不能关闭新 run。当前 run 的完整事件链还必须精确绑定 `plan.frozen`、每席 task 的 `seat.dispatch_requested` 与 dispatch resolution、accepted result 的 `seat.result_received|seat.result_recovered` 或失败件的 `seat.result_failed`，并为每个议题存在同 revision 的 `round.independent_sealed`。seal 前的 `seat.selected` 集合必须精确等于 plan 选席，所有依赖事件 sequence 必须早于 seal；seal 后同议题/修订禁止再追加任何 `seat.*`，`result_recovered` 只可在 seal 前由相同 payload hash 的可信 `result_received` 升级。缺任一绑定的席位固定为 `awaiting_current_run_event`，不得计入 accepted 或 ready。该门证明当前 workspace/run 的结构与事件哈希绑定，不证明拥有写权限者未合成整套自洽文件，也不证明跨 workspace predecessor 一次性消费。

## 决定确认生产门

`fbsir.decision-record/v1` 的通用 package-local validator 只接受 `confirmation_pending`，`decisionOwner=user` 只表示预期归属，不证明真实用户身份或同意。`artifact.presented` 与未来 `user.confirmed` 都必须携带 exact payload hash；通用 `appendEvent` 禁止写 `user.confirmed` 并固定返回 `DECISION_DEDICATED_WRITER_REQUIRED`。当前 `contracts/decision-confirmation-gate.json` 明确 `productionEnabled=false`、`dedicatedWriterEnabled=false`，阻塞项为服务 repository 对 finalized exact retry 的拒绝，以及 verifier 对同事件同 ACK 先报 nonce replay。两项 P0、工作区外受信 verifier、same-binding nonce claim exact retry 均有目标回执前，任何请求必须在创建目录、锁、所有权记录、决定记录或事件前失败关闭。该门只证明包内 fail-closed 行为，不证明真实用户确认、跨 workspace 防重放、宿主执行或 production readiness。

## 直接事实原则

- `package_local_observation` 只证明包内脚本实际记录或校验的本地事实。
- `user_confirmation` 只证明当前用户对明确对象作出的确认。
- `board-event.mjs register-host-receipt` 只写同一 workspace 的 `rcpt_<32hex>` 未核验观察记录，并按 run、事件类型、metadata 和 payloadHash 绑定。它不是 `host_runtime_receipt` 的可信签发源；26.8.10 包内未接外部 verifier 时，任何此类观察用于宿主事件都必须以 `HOST_RECEIPT_EXTERNAL_VERIFIER_REQUIRED` 失败，不能推进成功状态、证明动作成功或形成产品信用。
- `fbsir.member-delivery-observation/v1` 是成员看到 `SendMessage` 工具成功后的本地观察，仅用于内容恢复；它既不是 `host_runtime_receipt`，也不证明召集人主会话已消费消息。
- `board-assets.mjs` 的目录、构建和验证回执属于 `package_local_observation`。`assetbundle:<sha256>` 只绑定某议题、席位、阶段、起手卡摘要和精选短卡，不证明成员采用了方法、宿主执行成功或业务结果改善。
- 工具可见、调用请求、accepted、完成、产物呈现和用户验收是不同事件，不得互相替代。

## 单写入

只有 `board-convener` 可以记录冻结计划、成员任务、失败信封，追加共享事件或建立检查点。成员可以在自己的确定性路径记录结果和投递观察，但不得读其他席位目录或写共享事件。只有具备真实宿主回执的结果才能由召集人记为 `seat.result_received`；案卷恢复内容必须记为 `seat.result_recovered`，保持在 `package_local_observation` 层。

## 隐私

事件元数据采用允许列表。正文、提示词、问题、答案、原始材料、附件、姓名、邮箱、电话、地址、IP、token、secret 和 password 不得进入事件日志。`eventId` 由包按 workspace 与规范化意图生成，调用方不得提交；`agendaItemId/roundId` 在事件 metadata 中只允许有界序号。用户确认回执写入事件前转成 workspace-bound opaque ref，宿主观察只允许已登记 `rcpt_`。需要关联内容时只写 SHA-256 或本地不透明索引。

## 关键事件顺序

```text
meeting.opened
→ agenda.registered
→ plan.frozen (user_confirmation, exact plan payloadHash)
→ team.create_requested
→ team.created (host_runtime_receipt)
→ seat.selected
→ seat.dispatch_requested (exact persisted task-file bytes SHA-256)
→ seat.dispatched (host_runtime_receipt, same task-file bytes SHA-256)
  or seat.dispatch_failed (same task-file bytes SHA-256)
→ seat.result_received (host_runtime_receipt, exact result payloadHash)
  or seat.result_recovered (package_local_observation, exact result payloadHash)
  or seat.result_failed (package_local_observation, exact failure payloadHash)
→ round.independent_sealed
→ challenge.* (optional)
→ collection.ready (exact collection payloadHash)
→ memo.compiled (exact artifact SHA-256)
→ artifact.presented
→ user.confirmed (optional)
```

失败、用户停止和检查点是独立事件。`team.created` 缺外部可信回执时只能记录 `team.create_failed` 的包本地失败观察或停在请求状态；调用方自报摘要与 `register-host-receipt` 生成的未核验记录都不能解锁成功状态。

起手卡先经 `board-assets.mjs decision-card hash` 得到 `decisionCardHash`，再进入计划信封。`board-envelope.mjs plan` 校验后，召集人必须用 `board-record.mjs plan --actor board-convener` 将计划写入 `.fbsir-board/plans/<runId>.json`；返回的 `payloadHash` 必须原样绑定到 `plan.frozen`，缺少或换用其他哈希时不得请求 `TeamCreate`。同一 `runId` 的冻结计划不可覆盖；用户改题或变更计划时必须新建运行。

每席任务必须先经 `board-envelope.mjs task` 校验，再由召集人用 `board-record.mjs task --actor board-convener` 写入 `tasks/<agenda>/<seat>.task.r<revision>.json`，成功后才允许派发。记录回执的 `taskPayloadHash` 是该耐久任务文件原始字节的 SHA-256；`seat.dispatch_requested` 与随后的 `seat.dispatched` 或 `seat.dispatch_failed` 必须原样绑定此哈希。任务、结果、投递观察和失败信封全部绑定同一修订号；派发后任何正文或格式字节变化都会改变哈希，旧修订文件不能关闭新修订缺口。

选择、调度、结果去重和独立轮次封存全部按 `agendaItemId + seatId + revision` 复合作用域判断；同一 run 的其他议题或其他修订既不能关闭当前缺口，也不能阻止已完成作用域封存。封存前，当前议题与修订的所有已选席位都必须有哈希绑定的 `seat.result_received`、`seat.result_recovered` 或 `seat.result_failed`。派发本身失败时，先以任务哈希记录 `seat.dispatch_failed`，再以失败信封哈希记录 `seat.result_failed`。其中恢复事件只能证明包内耐久结果及成员侧投递观察，不能证明宿主签名回执或主会话消费。

N/N 收齐器另行检查冻结计划、耐久任务及其原始字节 `taskPayloadHash`、每个议题与选定专业席的修订绑定、唯一资产包引用、资产文件身份/范围/新鲜度/哈希、结果哈希、投递观察或一次重试后的失败信封。收齐器通过可以允许内容汇编，但不能自动追加 `seat.result_received` 宿主事件；召集人必须按真实证据层追加 `seat.result_received`、`seat.result_recovered` 或 `seat.result_failed`，两套证据层不得合并。

首轮封存且收齐器返回 `readyForSynthesis=true` 后，召集人以精确 `collectionPayloadHash` 和计划修订追加 `collection.ready`。完成默认 Markdown 后，先以 `board-record.mjs claim-index` 对 fence/HTML 注释外的显式主张标签建立 digest-only 索引，再以文件内容 SHA-256 和同一修订追加 `memo.compiled`。`board-delivery.mjs` 必须复核同一 artifact SHA 的 claim index、`plan.frozen` 与 `collection.planPayloadHash`、任务字节哈希与完整派发链、每席结果/失败事件、逐议题封存、`collection.ready` 和 `memo.compiled` 的精确作用域及哈希绑定；任一缺失、错议题、错修订、错哈希、可见分类未降级或来源记录失配都不得呈现交付物。主张索引只覆盖显式标签，未标记语句的语义完整性仍需人工复核。

事件文件与命令中的 `runId` 通过 `runIdHash` 强绑定；任何跨 run 复制、顺序越级、终止后继续推进或未声明字段都必须失败关闭。任务/结果信封采用字段白名单，并从包内 manifest 动态读取专业席和流程支持席：秘书只能使用 `process_support`，不得通过信封伪装成专业审议意见。
