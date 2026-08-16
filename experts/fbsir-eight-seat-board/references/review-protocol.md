# 独董会审议协议

## 1. 状态机

```text
intake
  -> decision_start_card
  -> mode_selected
  -> team_created
  -> independent_review
  -> challenge_optional
  -> memo_compiled
  -> delivered

任一阶段可进入：
  not_ready_for_conclusion
  orchestration_unavailable
  user_changed_proposal
  user_stopped
```

状态不能靠文案猜测。`team_created`、`independent_review` 和成员回传必须由宿主实际回执支持。

## 2. 决策起手卡

```text
【真议案】
【决策选项】
【Non-goals】
【已知事实】
【待验证假设】
【关键缺口】
【建议模式】quick_review / standard_review / deep_review
【建议席位及理由】
【唯一下一步】
```

首次响应最多提出 3 个真正会改变决策的关键问题。非关键缺口进入假设台账，不阻断首值。

一次运行最多处理 5 个议题。超过时按依赖、风险和决策时点建立分批计划，不静默超限。26.7.20 公开核心的快审为 1 个专业席，标准审议为 2—3 个专业席，深度审议先交付 2—3 席的准备卡；召集人与秘书都不计专业席。

起手卡展示前，召集人必须先按改变结论的可能性对候选池排序，并把建议模式、专业席和可选流程支持席送入 `fbsir.review-seat-proposal/v1` 校验。只有 `board-envelope.mjs proposal` 返回 `ok=true` 时，才可展示其 `normalized` 选席；该预检不写专用案卷、不需要用户确认，也不证明建团或宿主成功。

用户确认起手卡后，召集人必须先校验本次计划信封：1—5 个议题、审议模式、当前 manifest 中的专业席、可选流程支持席、确认回执和唯一下一步。计划信封通过只证明输入形状符合公开核心边界，不能替代 `TeamCreate` 回执。

## 3. 团队与工具回执

- `TeamCreate` 必须且只能由召集人执行。
- 规范 2.3 的调度语义名为 `AgentTool`；WorkBuddy 5.2.6 实际函数名为 `Agent`。`name` 和 `subagent_type` 都使用成员 Agent ID。
- 成员必须经 `SendMessage` 回到 `board-convener`，不得互相直连或 spawn 召集人。
- 脚本事件、工具可见性、`TaskList` 和文案都不能替代真实宿主回执。
- 本地建团前初始化专用案卷。每席先记录结构化结果，再调用 `SendMessage`，工具成功后记录与结果哈希绑定的成员侧投递观察；该观察只用于漏唤醒恢复，不是宿主签名回执或主会话消费证明。
- 召集人每次被成员消息或团队终态唤醒都运行 N/N 收齐器。只有所有选定专业席及显式选中的流程支持席均为“有效结果 + 成功观察”或“一次重试后明确失败”，且至少保留一个有效专业结果，才能汇编。
- 秘书只做流程支持和能力编排，不投票、不新增专业结论；一旦被计划选中，其任务、结果、失败和事件也必须进入同一案卷与收齐门，不能成为不可追溯旁路。

### 3.1 续办卡只读门

- current checkpoint 创建回执必须返回 `checkpointReceiptDigest`；生成 `fbsir.case-resume-card/v1` 时由调用方重新提供该 exact digest，并经过完整工作空间事件验证器后重放 marker、计划、事件链及最新 checkpoint 绑定。卡片只展示事件链可复算的操作里程碑，不解释 checkpoint 自由文本 `state`，也不投影该 digest 未绑定的材料记录；材料门固定显示未被 checkpoint 绑定。terminal run 不展示同 run 继续动作，其他 current run 确认后也只能继续同一 run。
- predecessor 续办卡必须把调用方提供的 `predecessorResumeDigest` 与 exact `v2@26.8.1` 只读重算结果精确比较；legacy 续办卡同样精确比较 exact `v1@26.7.20` 的 `legacyResumeDigest`。两类卡都不展示已观察完成节点，只列实际存在组件的各自 `*_bound` 字节绑定。确认后必须进入与旧 run 不同的新 26.8.19 run，并经 exact predecessor receipt/plan v2 绑定。
- digest 缺失、失配、版本不支持或源变化均失败关闭，不回显正文、路径、runId、文件名或成员意见；回执没有负责人、期限和复审日期时固定标明未提供。`--inspect-only` 只在本次返回卡中不展示 `resume_case`；它不写撤销状态，也不让 action validator 获得全局禁用能力。卡片不证明正文真实性、语义完成、宿主执行、用户确认或产品信用。

## 4. 认知资产与阶段隔离

- 运行当日先校验认知资产目录，再对已确认的决策起手卡做瞬时规范化哈希；脚本只返回摘要和字符数，不保存起手卡正文。
- Phase 1 为每个“议题 × 席位”生成独立短包。专业席使用 `phase1_independent`，秘书使用 `phase1_process_support`；每包只能包含本席一张方法卡和一张清单。
- 任务和结果 `evidenceRefs` 必须且只能含同一个 `assetbundle:<sha256>`。成员分析前验证，收齐器汇编前再次验证文件身份、阶段、席位、日期、新鲜度、内容哈希和预算。
- 首轮包不得包含案例、反例、其他席位资产或结果导向内容。只有首轮封存后，Phase 2 才可用新修订号向相关席位追加最多一张反例或案例卡。
- Phase 3 由召集人加载自己的汇编方法包；它只约束程序和质量门，不能替代专业席意见。
- 资产包证明精选、范围和哈希绑定，不证明方法实际被采用、结论正确、宿主动作成功或业务效果。

### 4.1 主张—证据与可见降级

- 用户确认后，召集人以无引用 `material-card-draft/v1` 运行 `board-record.mjs material-card --workspace <目录> --run <runId> --actor board-convener`。writer 在同一工作空间重新 mint 引用并写入 digest-only 材料记录；首轮只可能是 `received_unverified/received_conflicted`，不得从历史 material JSON 或形似 `mat_<32hex>` 的字符串自报 provenance。
- `board-event.mjs register-host-receipt` 只能建立与 workspace、run、事件类型、metadata 和 payloadHash 精确绑定的 `rcpt_<32hex>` 未核验观察记录。它只证明包记录了调用方提交的摘要，不是宿主签名或真实性证明；26.8.19 包内没有外部可信 verifier，因此该记录既不能把正文升级为事实，也不能作为 `host_runtime_receipt` 推进 `team.created/seat.dispatched/seat.result_received` 等状态，尝试时固定失败 `HOST_RECEIPT_EXTERNAL_VERIFIER_REQUIRED`。
- 明确公共来源可用 `board-record.mjs public-source` 只登记 `sourceDigest`，得到 workspace-bound `src_<32hex>`；26.8.19 没有外部可信 verifier 时固定为 `registered_unverified`，不计入事实绑定率。
- 正式 Markdown 中需审计的主张必须逐行使用 `【关键事实】/【事实】/【估计】/【假设】/【判断】/【未知】`。缺证、未核验或冲突的事实必须在用户可见正文改写为 `【关键事实（未核验，按假设处理）】`、`【事实（证据冲突，按未知处理）】` 或对应缺失标签；隐藏索引降级但正文仍写“事实”会失败关闭。
- `board-record.mjs claim-index --artifact <deliverables内文件>` 从 fence 与 HTML 注释之外的显式标签直接计算 statementDigest 和 package-owned claimId；调用方只提供 ordinal 与 evidenceRefs，不得提交正文、claimId 或 digest。索引只保存摘要和不透明引用，不保存正文或文件名。
- `board-delivery.mjs` 必须反查同一 workspace、run 与 artifact SHA 的 claim index，重算可见标签、分类、来源作用域和摘要；缺索引、换文件、篡改或来源记录丢失均不得进入 `ready_to_present`。该门只证明显式声明标签的完整覆盖，不证明未标记语句没有事实性含义，也不证明材料真实性或结论正确，S/P/C/B/G 与人工事实复核仍是必需门。

## 5. 专业席与流程支持席回传信封

### 5.1 专业席

每席先返回一行元数据，再返回正文：

```text
seatId=<id> | stance=<赞成/有条件赞成/反对/不具备表态条件> | confidence=<高/中/低> | conclusionReady=<true/false> | receiptId=<真实回执或 unavailable>
```

正文统一回答：

1. 独立性、关联与证据偏差；
2. 本席核心判断；
3. 支撑事实、估计、假设、判断与未知，并给置信度和最强反证；
4. 明确立场及成立条件；
5. 最大风险和失效条件；
6. 最小补数或人工复核要求；
7. 对其他席位的质询。

快审正文不超过 1000 个中文字符；标准/深度审议不超过 1600 个中文字符。法条、估值和测算证据附录不计入正文上限，但不得重复正文。

### 5.2 流程支持席

秘书只有在用户明确确认、exact plan 已冻结且被显式选为 `process_support` 后才能接收任务。acceptance 中的 `expectedAgent=board-secretary` 单独出现时只表示 routing candidate，不构成调度授权；缺少任一前置条件都必须保持 `dispatchAllowed=false`。26.8.19 新回传使用 `fbsir.process-support-result/v1`，必须固定为 `seatId=board-secretary`、`taskClass=process_support`、`stance=not_applicable`、`confidence=not_applicable`、`conclusionReady=false`；不得套用专业席正文模板。既有 `fbsir.member-result/v1 + process_support` 只允许历史只读解析/展示，不允许新写，也不得计入新运行的 accepted/resolved/收齐；专业席继续使用 `fbsir.member-result/v1`。

`sections` 只能包含以下四个 exact 机械对象，任何自由文本 section、额外字段或嵌套的 judgement / summary / recommendation / approval / legalOpinion 均由核心校验器失败关闭：

```text
deliveryStatus={state:<completed|partial|blocked>,receiptObserved:false}
sourceLedger={entries:[],pendingVerification:[],mutationAllowed:false}
artifactChecklist={requiredCount,readyCount,pendingCount,humanAcceptanceRequired:true}
capabilityStatus={state:<available|unavailable|not_authorized|accepted_without_result>,materialStateEffect:"none",externalFactProven:false,manualVerificationRequired:<boolean>}
```

MAT-002 只封闭首轮展示与秘书边界，不假装已经具备耐久来源账本：流程支持结果中的 `entries`、`pendingVerification` 必须为空，`mutationAllowed` 必须为 `false`。秘书在呈现层只能回显召集人已构建卡的材料/来源/版本状态；任何新材料、版本冲突或工具结果都退回召集人重新运行无引用 draft 的 `material-card` 构建，不得自行生成或持久化 `materialRef/version`。能力状态与材料状态正交，不能借 `capabilityStatus` 增删材料缺口、证明外部事实或形成专业结论。耐久来源账本必须等 workspace-bound 合同实现后再启用；哈希、自报回执或格式正确的 32hex 都不是 provenance。

当前流程支持结果还必须固定 `receiptId=unavailable`、`deliveryStatus.receiptObserved=false`，`evidenceRefs` 只能是任务下发的唯一 `assetbundle:<sha256>`；记录器在写前、收齐器在接受前都复核任务与结果的完整 `evidenceRefs` 全等。`board-record.mjs result` 写入成功后原子返回 exact `fbsir.process-support-handoff/v1`（耐久 `resultTarget + resultPayloadHash` 及身份字段）；秘书不得自行构造或修改，只可原样经 `board-envelope.mjs support-handoff` 重验并发送，不得附加自由文本、材料、路径、PII 或建议。真实发送成功仅由后置 delivery observation 表达，不能在 result 或 handoff 中自报。

## 6. 质询协议

- 只选择 2—4 个真正影响结论的冲突点。
- 只向相关席位传递结构化观点摘要、证据索引和待回答问题。
- 仅在首轮封存后按冲突点加载 `phase2_challenge` 反例/案例短包；使用新修订号，不覆盖首轮资产和回执。
- 回应必须标记“坚持 / 修正 / 让步”，并说明新证据或推理。
- 不得改写首轮意见；保留修订轨迹。
- 26.7.20 公开核心最多 1 轮。未解决的分歧进入保留意见，不循环追问；未来完整深度会只有在宿主资源和已验证权益允许时才能增加轮次。

## 7. 最终交付

最终交付不是只在聊天中显示完成状态。快审、标准审议和深度准备分别默认生成 `独董会快速审议卡.md`、`独董会审议备忘录.md` 和 `独董会深度审议准备卡.md`，并通过交付脚本校验收齐状态、规范标题与文件哈希后再向用户展示链接。系统终态通知、成员绿勾或文件存在均不等于用户验收。

### 快速审议卡

```text
# 独董会快速审议卡
一、一句话判断
二、事实 / 估计 / 假设 / 判断 / 未知与最强反证
三、专业席立场及成立条件
四、最大风险与失效条件
五、决策质量最弱链
六、唯一下一步、触发器、负责人、复审日期与人工关卡
```

快审严格保持六节；不得因为深度不足而静默升级为标准/深度十节。需要升级时必须回到用户动作与模式确认。

### 标准/深度十节合同

```text
# 独董会审议备忘录
【表态统计】赞成 X / 有条件赞成 Y / 反对 Z / 不具备表态条件 W
【一句话建议】……

一、议案、选项与 Non-goals
二、证据、假设与关键缺口
三、各席核心判断
四、质询、修正与保留异议
五、建议、成立条件与失效条件
六、决策质量六链门禁（最弱链 / 缺口 / 状态）
七、决策日志（选择 / 指标 / 触发器 / 负责人 / 复审日期）
八、7/30/90 天行动（责任方向 / 人工关卡 / 验收标准）
九、证据台账、席位回执与资产包索引
十、专业边界与需人工复核事项
```

`standard_review` 使用上述规范标题；`deep_review` 只把首行替换为 `# 独董会深度审议准备卡`，其余使用同一十节标题与顺序。表态统计与一句话建议是十节前置摘要，不占用编号，也不能替代任一节。

六链不得缩写为一个泛化分数，必须逐项覆盖问题框架、可行替代、可靠信息、价值与取舍、推理、执行承诺，并明确最弱链、缺口、状态和关闭责任人。决策日志必须保留最终选择、未选方案、可解析时的关键概率与截止日、领先指标、触发器、负责人、复审日期；不可解析的问题不强行赋概率，但不能因此删除其他日志字段。

只有议案需要时才附加详细测算、法条、变量观察台或自动化建议。六链门禁不使用平均分掩盖关键短板；不可解析的问题不强行赋概率。高质量程序不等于保证正确结果。
