# 协同事件与证据合同

## 直接事实原则

- `package_local_observation` 只证明包内脚本实际记录或校验的本地事实。
- `user_confirmation` 只证明当前用户对明确对象作出的确认。
- `host_runtime_receipt` 必须带真实 `receiptRef`，只证明回执直接覆盖的宿主动作。
- `fbsir.member-delivery-observation/v1` 是成员看到 `SendMessage` 工具成功后的本地观察，仅用于内容恢复；它既不是 `host_runtime_receipt`，也不证明召集人主会话已消费消息。
- `board-assets.mjs` 的目录、构建和验证回执属于 `package_local_observation`。`assetbundle:<sha256>` 只绑定某议题、席位、阶段、起手卡摘要和精选短卡，不证明成员采用了方法、宿主执行成功或业务结果改善。
- 工具可见、调用请求、accepted、完成、产物呈现和用户验收是不同事件，不得互相替代。

## 单写入

只有 `board-convener` 可以记录冻结计划、成员任务、失败信封，追加共享事件或建立检查点。成员可以在自己的确定性路径记录结果和投递观察，但不得读其他席位目录或写共享事件。只有具备真实宿主回执的结果才能由召集人记为 `seat.result_received`；案卷恢复内容必须记为 `seat.result_recovered`，保持在 `package_local_observation` 层。

## 隐私

事件元数据采用允许列表。正文、提示词、问题、答案、原始材料、附件、姓名、邮箱、电话、地址、IP、token、secret 和 password 不得进入事件日志。需要关联内容时只写 SHA-256 或本地不透明索引。

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

失败、用户停止和检查点是独立事件。`team.created` 缺回执时只能记录 `team.create_failed` 或停在请求状态。

起手卡先经 `board-assets.mjs decision-card hash` 得到 `decisionCardHash`，再进入计划信封。`board-envelope.mjs plan` 校验后，召集人必须用 `board-record.mjs plan --actor board-convener` 将计划写入 `.fbsir-board/plans/<runId>.json`；返回的 `payloadHash` 必须原样绑定到 `plan.frozen`，缺少或换用其他哈希时不得请求 `TeamCreate`。同一 `runId` 的冻结计划不可覆盖；用户改题或变更计划时必须新建运行。

每席任务必须先经 `board-envelope.mjs task` 校验，再由召集人用 `board-record.mjs task --actor board-convener` 写入 `tasks/<agenda>/<seat>.task.r<revision>.json`，成功后才允许派发。记录回执的 `taskPayloadHash` 是该耐久任务文件原始字节的 SHA-256；`seat.dispatch_requested` 与随后的 `seat.dispatched` 或 `seat.dispatch_failed` 必须原样绑定此哈希。任务、结果、投递观察和失败信封全部绑定同一修订号；派发后任何正文或格式字节变化都会改变哈希，旧修订文件不能关闭新修订缺口。

选择、调度、结果去重和独立轮次封存全部按 `agendaItemId + seatId + revision` 复合作用域判断；同一 run 的其他议题或其他修订既不能关闭当前缺口，也不能阻止已完成作用域封存。封存前，当前议题与修订的所有已选席位都必须有哈希绑定的 `seat.result_received`、`seat.result_recovered` 或 `seat.result_failed`。派发本身失败时，先以任务哈希记录 `seat.dispatch_failed`，再以失败信封哈希记录 `seat.result_failed`。其中恢复事件只能证明包内耐久结果及成员侧投递观察，不能证明宿主签名回执或主会话消费。

N/N 收齐器另行检查冻结计划、耐久任务及其原始字节 `taskPayloadHash`、每个议题与选定专业席的修订绑定、唯一资产包引用、资产文件身份/范围/新鲜度/哈希、结果哈希、投递观察或一次重试后的失败信封。收齐器通过可以允许内容汇编，但不能自动追加 `seat.result_received` 宿主事件；召集人必须按真实证据层追加 `seat.result_received`、`seat.result_recovered` 或 `seat.result_failed`，两套证据层不得合并。

首轮封存且收齐器返回 `readyForSynthesis=true` 后，召集人以精确 `collectionPayloadHash` 和计划修订追加 `collection.ready`。完成默认 Markdown 后，以文件内容 SHA-256 和同一修订追加 `memo.compiled`。`board-delivery.mjs` 必须复核 `plan.frozen` 与 `collection.planPayloadHash`、任务字节哈希与完整派发链、每席结果/失败事件、逐议题封存、`collection.ready` 和 `memo.compiled` 的精确作用域及哈希绑定；任一缺失、错议题、错修订或错哈希都不得呈现交付物。

事件文件与命令中的 `runId` 通过 `runIdHash` 强绑定；任何跨 run 复制、顺序越级、终止后继续推进或未声明字段都必须失败关闭。任务/结果信封采用字段白名单，并从包内 manifest 动态读取专业席和流程支持席：秘书只能使用 `process_support`，不得通过信封伪装成专业审议意见。
