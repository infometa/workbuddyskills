# 独董会输出结构示例

以下只示范结构，不提供可套用的行业事实、阈值或结论。

## 能力发现卡

只用于问候、能力询问和无有效议案的试探；不生成伪议案，不建团，不写案卷或事件。

```text
【定位】独董会是一支 AI 经营决策独立审议专家团；不是法定董事会，也不替代法定独立董事意见。

【四个可复制入口】
1. 投资并购｜“我们是否应该收购这家上游企业？请先帮我形成决策起手卡。”
2. 增长 / 第二曲线｜“增长停滞，我该深挖主业、变革渠道还是小试第二曲线？”
3. 经营 / 组织取舍｜“这项降本、扩产或组织调整该不该做，最关键的取舍是什么？”
4. 合规风险 / 数智化重大项目｜“这个合规风险或数智化重大项目是否值得推进，最低安全门槛是什么？”

【交付】先给一张决策起手卡；你确认后，再交付带证据、异议、成立条件和行动的审议结果。

【唯一主动作】粘贴你正在犹豫的一项决策
```

## 决策起手卡

受测输入只用于把 expected route 与静态输出 fixture 绑定；入口校验器验证模型构造的 envelope 形状，不读取或分类 `userInput`：

```json
{
  "userInput": "我们是否应该在现金压力下收购一家上游企业？",
  "entryIntent": {
    "schema": "fbsir.entry-intent/v1",
    "route": "decision_intake",
    "confidenceBand": "high",
    "signals": {
      "hasDecisionQuestion": true,
      "hasUserMaterial": false,
      "hasResumeReference": false,
      "isCapabilityQuestion": false,
      "isOutOfScope": false
    },
    "firstValueType": "decision_start_card",
    "teamCreationAllowed": false,
    "workspaceWriteAllowed": false,
    "evidenceBoundary": "model_classification_validated_by_package_shape_only"
  }
}
```

```text
【你真正要决定的事】是否在不突破现金安全边界的前提下，对候选项目进行可逆的小规模试点？
【可选路径与本次不讨论什么】不做 / 小试 / 直接投入；本次不讨论已排除项目，也不替代法定审批。
【当前已知 / 关键假设 / 最小补材】已知事实：仅列用户确认口径；待验证假设：市场、成本和执行前提；证据缺口与最小补材：只补会改变合法性、选项或承受力的数据。
【建议审议方式与会改变结论的席位】standard_review；战略、资本财务、法务风控，均说明其会改变哪项判断。
【当前最稳妥的可逆动作】在不对外承诺的前提下冻结小试边界、现金上限和退出门。

【主动作】1 按建议开始独立审议（用户明确回复主动作后才视为确认）
【次级分支】2 补充关键事实
【次级分支】3 切换审议模式
```

## 动作展示合同

以下 JSON 是包内 normal/debug 双模式 golden，不是普通用户正文。普通模式的 `visibleBody` 只有自然语言数字选择；完整 action envelope 位于宿主元数据。只有显式请求 debug 时，才可把同一 envelope 放入独立 debug block。两种模式都不证明宿主执行。

```json
{
  "schema": "fbsir.action-presentation-contract/v1",
  "catalogRef": "contracts/no-connector-action-contract.json",
  "constraints": {
    "primaryActionCount": 1,
    "secondaryBranchCount": 2,
    "normalEnvelopeLocation": "host_metadata",
    "debugEnvelopeLocation": "explicit_debug_block",
    "debugRequiresExplicitRequest": true,
    "bodyContainsEnvelope": false,
    "fallbackWhenMetadataUnavailable": "keep_internal_fail_closed_never_print_in_user_body",
    "forbiddenEnvelopeKeys": [
      "prompt",
      "token",
      "rawMaterial",
      "personalInformation",
      "pii",
      "email",
      "phone",
      "userInput"
    ],
    "visibleActions": [
      {
        "role": "primary",
        "ordinal": 1,
        "actionId": "confirm_review",
        "labelZh": "按建议开始独立审议"
      },
      {
        "role": "secondary",
        "ordinal": 2,
        "actionId": "add_facts",
        "labelZh": "补充关键事实"
      },
      {
        "role": "secondary",
        "ordinal": 3,
        "actionId": "change_mode",
        "labelZh": "切换审议模式"
      }
    ],
    "metadataBindsPrimaryAction": true,
    "debugMatchesMetadataEnvelope": true,
    "debugBlockExactKeys": true,
    "evidenceBoundary": "package_proposed_action_only_not_host_execution_or_product_credit",
    "presentationValidationProvesHostExecution": false
  },
  "normalGolden": {
    "presentationMode": "normal_user",
    "visibleBody": [
      "【主动作】1 按建议开始独立审议",
      "【次级分支】2 补充关键事实",
      "【次级分支】3 切换审议模式"
    ],
    "primaryActionIds": ["confirm_review"],
    "secondaryActionIds": ["add_facts", "change_mode"],
    "envelopeLocation": "host_metadata",
    "bodyContainsEnvelope": false,
    "debugRequested": false,
    "hostMetadata": {
      "actionEnvelope": {
        "schema": "fbsir.host-action-envelope/v1",
        "actionId": "confirm_review",
        "actionInstanceId": "act_confirm_review_001",
        "product": {
          "packageId": "fbsir-eight-seat-board",
          "productVersion": "26.8.19"
        },
        "arguments": {
          "reviewMode": "standard_review",
          "decisionCardHash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        "sideEffectClass": "state_write",
        "approvalState": "required",
        "idempotent": true,
        "stopCondition": "plan_v2_frozen_with_exact_action_digest",
        "doneState": "review_plan_confirmed",
        "successorAction": "request_team_create",
        "routeSignature": "fbsir-eight-seat-board:confirm_review:v1",
        "evidenceBoundary": "package_proposed_action_only_not_host_execution_or_product_credit"
      }
    },
    "debugBlock": null
  },
  "explicitDebugGolden": {
    "presentationMode": "explicit_debug",
    "visibleBody": [
      "【主动作】1 按建议开始独立审议",
      "【次级分支】2 补充关键事实",
      "【次级分支】3 切换审议模式"
    ],
    "primaryActionIds": ["confirm_review"],
    "secondaryActionIds": ["add_facts", "change_mode"],
    "envelopeLocation": "explicit_debug_block",
    "bodyContainsEnvelope": false,
    "debugRequested": true,
    "hostMetadata": null,
    "debugBlock": {
      "actionEnvelope": {
        "schema": "fbsir.host-action-envelope/v1",
        "actionId": "confirm_review",
        "actionInstanceId": "act_confirm_review_001",
        "product": {
          "packageId": "fbsir-eight-seat-board",
          "productVersion": "26.8.19"
        },
        "arguments": {
          "reviewMode": "standard_review",
          "decisionCardHash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        "sideEffectClass": "state_write",
        "approvalState": "required",
        "idempotent": true,
        "stopCondition": "plan_v2_frozen_with_exact_action_digest",
        "doneState": "review_plan_confirmed",
        "successorAction": "request_team_create",
        "routeSignature": "fbsir-eight-seat-board:confirm_review:v1",
        "evidenceBoundary": "package_proposed_action_only_not_host_execution_or_product_credit"
      },
      "evidenceBoundary": "package_proposed_action_only_not_host_execution_or_product_credit",
      "provesHostExecution": false
    }
  }
}
```

## 当前续办卡

```text
【证据状态】verified_current_checkpoint；必须与调用方已有 checkpointReceiptDigest 精确一致
【案卷状态】当前
【已观察里程碑】只列 checkpoint 所绑定 current event chain 可复算的枚举节点；不复述 checkpoint.state，不把事件写入等同于真实业务完成
【证据绑定】current_checkpoint_bound；不展示路径、runId、正文、文件名或成员意见
【仍开关卡】材料状态未被 checkpoint 绑定、人工复核，以及非 terminal run 的显式继续确认；terminal run 另显示 run_terminal_no_same_run_resume
【下一项主动作】非 terminal 时为 resume_case，且 current_checkpoint 只能继续 sourceRunIdHash 对应的同一 current run；terminal 时不展示继续动作
【负责人 / 期限 / 复审日期】本版 checkpoint 不含这些字段，固定显示“回执未提供 / null / null”
【恢复边界】只恢复 checkpoint 绑定的本地操作链；不证明正文、语义完成、宿主签名执行或用户确认
```

## 前序只读续办卡

```text
【证据状态】verified_predecessor_resume_digest；必须与调用方已有 predecessorResumeDigest 精确一致
【案卷状态】前序只读（exact fbsir.board-workspace/v2@26.8.1）
【已观察里程碑】无；predecessor digest 只绑定字节，不把旧事件、checkpoint、collection 或 delivery 解释成真实完成
【证据绑定】只列 predecessor_workspace/plan/event_chain 及实际存在的 checkpoint/collection/delivery/deliverable_inventory 的 `*_bound` 枚举
【仍开关卡】显式继续确认、新 run 绑定、人工复核和旧内容真实性未核验
【下一项主动作】resume_case；predecessor_read_only 必须选择与旧 run 不同的新 26.8.19 run，并在确认后走 exact predecessorRunRef v2
【负责人 / 期限 / 复审日期】predecessor digest 不含这些字段，固定显示“回执未提供 / null / null”
【恢复边界】旧意见仅作历史材料；绝不改写前序案卷，也不用旧结果关闭新 run
```

## 历史只读续办卡

```text
【证据状态】verified_legacy_resume_digest；必须与调用方已有 legacyResumeDigest 精确一致
【案卷状态】历史只读
【已观察里程碑】无；legacy digest 只绑定字节，不把旧事件、checkpoint、collection 或 delivery 解释成真实完成
【证据绑定】只列 legacy_workspace/plan/event_chain 及实际存在的 checkpoint/collection/delivery/deliverable_inventory 的 `*_bound` 枚举
【仍开关卡】显式继续确认、新 run 绑定、人工复核和旧内容真实性未核验
【下一项主动作】resume_case；legacy_read_only 必须选择与旧 run 不同的新 26.8.19 run，并在确认后走 exact predecessorRunRef v2
【负责人 / 期限 / 复审日期】legacy digest 不含这些字段，固定显示“回执未提供 / null / null”
【恢复边界】旧意见仅作历史材料；绝不改写旧案卷，也不用旧结果关闭新 run
```

## 恢复证据不足卡

```text
【案卷状态】未验证
【证据状态】missing / unsupported / receipt_mismatch / source_changed
【已观察里程碑】无
【仍开关卡】source_receipt_required 或 source_unsupported_or_changed
【唯一下一步】重新选择原案卷并执行只读检查，或重新粘贴继续决策所需的关键事实
```

运行时只允许通过以下只读命令构造卡片；缺少 `--receipt-digest` 时只返回恢复证据不足卡：

```powershell
node skills/independent-board-core/scripts/board-resume.mjs card --workspace <案卷> --run <runId> --receipt-digest <既有回执摘要>
```

`checkpoint.create` 会正式返回 `checkpointReceiptDigest`。相同 current run 续办时，`resume_case.targetRunId` 的 SHA-256 必须等于卡片 `source.runIdHash`；legacy 续办则必须不同，并在确认后使用既有 predecessor receipt/plan v2 路径。`card ... --inspect-only` 是只读展示模式：current/legacy 证据卡仍可生成，但本次返回的 `nextAction.actionId=null` 且出现 `resume_action_not_presented`。它不持久化撤销状态，也不能阻止调用方脱离该卡片独立构造 action envelope；宿主不得从 inspect-only 卡片生成 CTA 或动作。

## 友好转向卡

```text
【边界说明】独董会聚焦实体企业需要权衡选项、风险和行动门槛的重大经营决策；当前请求不会被强行改造成议案。
【一个可重写问题】如果你真正要决定的是一项经营取舍，能否补充“要选什么、为什么现在决定、哪条边界不能突破”？
【副作用】本卡不写案卷或事件，不建团，也不生成席位意见。
```

## 确认后的会议计划

用户明确选择 `confirm_review` 且 action envelope 校验回执为 `ok=true` 后，召集人在建团前形成计划信封；`confirmationAction.actionEnvelopeDigest` 必须取该 exact normalized action envelope 的 canonical digest：

```json
{
  "schema": "fbsir.review-plan/v2",
  "runId": "run_example",
  "revision": 1,
  "reviewMode": "standard_review",
  "agendaItems": [
    {
      "agendaItemId": "agenda_1",
      "decisionQuestion": "在既定约束下应优先验证哪个可逆方案？"
    }
  ],
  "specialistSeatIds": ["growth-partner", "operations-partner"],
  "supportSeatIds": ["board-secretary"],
  "decisionCardHash": "0000000000000000000000000000000000000000000000000000000000000000",
  "userConfirmed": true,
  "confirmationReceiptId": "user_confirmation_example",
  "confirmationAction": {
    "actionId": "confirm_review",
    "actionInstanceId": "act_plan_example",
    "actionEnvelopeDigest": "304ea93b468f3e51354cba855d9a96c32c4351d4cc2976d5d0e0cdd20bc88ae4"
  },
  "predecessorRunRef": null,
  "singleNextAction": "request_team_create"
}
```

新议案的 `predecessorRunRef` 必须为 `null` 且同 run 不得已有 predecessor receipt；只读续办必须使用 exact `fbsir.predecessor-run-ref/v2` 六字段对象，绑定 `.fbsir-board/predecessors/<新run>.json`、canonical receipt payload hash、旧 run hash、摘要 schema 与摘要。旧 `fbsir.predecessor-run-ref/v1` 只为既有 26.7.20 legacy 计划保留只读兼容。计划先在共享 run lock 内复核并耐久记录，`plan.frozen` 再绑定记录回执返回的精确 canonical `payloadHash`；任一 receipt、摘要、修订或哈希不一致都不得请求建团。旧 task/result/event 不导入新作用域；collection 还必须看到当前 run 的 plan/task/result-or-failure/round-seal 事件绑定才可 ready。该信封和冻结事件不能作为团队已经创建、成员已经调度、跨 workspace 一次性消费或旧内容真实的证明。

## 专业席回传

```text
seatId=strategy-partner | stance=有条件赞成 | confidence=中 | conclusionReady=true | receiptId=<宿主真实回执>

一、独立性、关联与证据偏差
二、本席核心判断
三、支撑事实、推断与假设
四、立场及成立条件
五、最大风险和失效条件
六、最小补数或人工复核要求
七、对其他席位的质询
```

## 快速审议卡

```text
# 独董会快速审议卡
一、一句话判断
二、事实 / 估计 / 假设 / 判断 / 未知与最强反证
三、专业席立场及成立条件
四、最大风险与失效条件
五、决策质量最弱链
六、唯一下一步、触发器、负责人、复审日期与人工关卡
```

快审只使用上述六节；不得为追求篇幅或形式完整而升级为标准/深度十节，也不得省略人工关卡。

## 审议备忘录

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

## 深度审议准备卡

```text
# 独董会深度审议准备卡
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

深度准备与标准审议只改变规范标题和内容深度，不增加、删除或重排十节。附录只在议案需要时追加，不能冒充第十一节，也不能把未验证材料写成事实。

第六节逐项覆盖问题框架、可行替代、可靠信息、价值与取舍、推理、执行承诺，并展示最弱链、缺口、状态和关闭责任人。第七节必须保留最终选择、未选方案、可解析时的关键概率与截止日、领先指标、触发器、负责人、复审日期；不可解析时不制造概率，但其他日志字段仍须保留。

## 审议后的决定、行动与复查用户卡

审议产物交付后，只把 AI 的审议建议与用户自己的决定并列展示，不把前者改写成后者。以下三张卡消费 `fbsir.decision-record/v1` 的待确认视图；包内视图始终保持 `confirmation_pending + confirmation=null + not_recorded`。它只证明卡片形状和分栏边界，不证明用户确认、决定持久化、宿主执行或行动完成。

```text
# 用户决定卡
【AI 审议建议】建议、成立条件和失效条件；明确标为 AI 建议
【用户自己的决定】approved / approved_with_conditions / rejected / deferred / revision_requested / no_decision；只回显用户已给出的选择
【决定状态】confirmation_pending；持久化状态 not_recorded
【可选确认动作】仅在用户已经给出决定时展示；当前 apply 状态 blocked_external，仍不是 user_confirmed
【边界】AI 不得替用户决定，也不得形成法定投票、董事会决议或法定独立董事意见
```

```text
# 用户行动卡
【行动】actionItemId；不从 AI 建议另造行动正文
【负责人】ownerRef；null 显示“待用户指定”
【截止时间】dueAt；null 显示“待用户指定”
【触发器】triggerId / condition / response；缺失显示“待用户指定”
【行动状态】open / in_progress / blocked / done / cancelled；不得从建议或时间经过推断完成
【复查状态】not_scheduled / scheduled / due_for_user_review；仅为展示态
```

```text
# 用户复查卡
【复查日期】reviewAt；null 显示“尚未安排”
【领先指标】indicatorId / metric / target / reviewTriggerId
【触发条件与响应】只回显决定记录中的 exact trigger
【复查状态】没有日期为 not_scheduled；有日期为 scheduled；只有可信 as-of 才能显示 due_for_user_review
【关闭条件】仍需用户明确确认；卡片、日期经过或 AI 判断都不能关闭复查
```

缺失的 `ownerRef`、`dueAt`、触发器或 `reviewAt` 必须显式保留为待用户指定/尚未安排，不能由秘书、召集人或宿主猜测。用户尚未决定时只显示 `no_decision`，不展示确认动作，不用追问或倒计时强迫确认。任何卡片都不得改称法定投票、董事会决议或法定独立董事意见。

```json
{
  "schema": "fbsir.followup-card-set/v1",
  "sourceSchema": "fbsir.decision-record/v1",
  "evidenceBoundary": "package_local_pending_presentation_only_not_user_confirmation_persistence_host_execution_statutory_vote_or_legal_opinion",
  "constraints": {
    "decisionOwner": "user",
    "aiRecommendationLabel": "AI 审议建议",
    "userDecisionLabel": "用户自己的决定",
    "pendingStatus": "confirmation_pending",
    "persistenceState": "not_recorded",
    "confirmationActionRequiresUserDecision": true,
    "confirmationActionWhenNoDecision": false,
    "confirmationActionApplyStateUntilGateEnabled": "blocked_external",
    "missingOwnerDisplay": "待用户指定",
    "missingDueAtDisplay": "待用户指定",
    "missingTriggerDisplay": "待用户指定",
    "reviewStateValues": ["not_scheduled", "scheduled", "due_for_user_review"],
    "dueForReviewRequiresTrustedAsOf": true,
    "reviewStateIsPresentationOnly": true,
    "closureRequiresUserConfirmation": true
  },
  "goldens": {
    "confirm": {
      "intent": "confirm",
      "decisionCard": {
        "aiRecommendation": {
          "label": "AI 审议建议",
          "statement": "建议先进行有退出门的小范围试点。"
        },
        "userDecision": {
          "label": "用户自己的决定",
          "decisionCode": "approved_with_conditions",
          "statement": "选择小范围试点；复查门未通过则停止扩大。",
          "status": "confirmation_pending",
          "confirmation": null,
          "persistenceState": "not_recorded"
        },
        "confirmationActionPresented": true,
        "confirmationActionState": "blocked_external"
      },
      "actionCard": {
        "items": [
          {
            "actionItemId": "action_pilot",
            "ownerRef": "owner_operations",
            "dueAt": "2026-09-01T00:00:00.000Z",
            "status": "open"
          }
        ],
        "triggers": [
          {
            "triggerId": "trigger_stop",
            "condition": "关键指标未达门槛",
            "response": "停止扩大并进入用户复查"
          }
        ],
        "reviewState": "scheduled"
      },
      "reviewCard": {
        "reviewAt": "2026-09-08T00:00:00.000Z",
        "reviewState": "scheduled",
        "leadingIndicators": [
          {
            "indicatorId": "indicator_pilot_retention",
            "metric": "试点留存率",
            "target": ">=0.80",
            "reviewTriggerId": "trigger_stop"
          }
        ],
        "triggers": [
          {
            "triggerId": "trigger_stop",
            "condition": "关键指标未达门槛",
            "response": "停止扩大并进入用户复查"
          }
        ],
        "closureRequiresUserConfirmation": true
      }
    },
    "decline": {
      "intent": "decline",
      "decisionCard": {
        "aiRecommendation": {
          "label": "AI 审议建议",
          "statement": "在当前证据和承受力约束下不建议推进原方案。"
        },
        "userDecision": {
          "label": "用户自己的决定",
          "decisionCode": "rejected",
          "statement": "不推进原方案。",
          "status": "confirmation_pending",
          "confirmation": null,
          "persistenceState": "not_recorded"
        },
        "confirmationActionPresented": true,
        "confirmationActionState": "blocked_external"
      },
      "actionCard": {
        "items": [],
        "triggers": [],
        "reviewState": "not_scheduled"
      },
      "reviewCard": {
        "reviewAt": null,
        "reviewState": "not_scheduled",
        "leadingIndicators": [],
        "triggers": [],
        "closureRequiresUserConfirmation": true
      }
    },
    "defer": {
      "intent": "defer",
      "decisionCard": {
        "aiRecommendation": {
          "label": "AI 审议建议",
          "statement": "先补齐会改变结论的关键证据，再决定是否推进。"
        },
        "userDecision": {
          "label": "用户自己的决定",
          "decisionCode": "deferred",
          "statement": "暂缓决定，先补齐现金承受力证据。",
          "status": "confirmation_pending",
          "confirmation": null,
          "persistenceState": "not_recorded"
        },
        "confirmationActionPresented": true,
        "confirmationActionState": "blocked_external"
      },
      "actionCard": {
        "items": [
          {
            "actionItemId": "action_collect_cash_evidence",
            "ownerRef": null,
            "dueAt": null,
            "status": "open"
          }
        ],
        "triggers": [
          {
            "triggerId": "trigger_cash_evidence_ready",
            "condition": "现金承受力证据已由有权责任人复核",
            "response": "由用户重新打开决定与复查"
          }
        ],
        "reviewState": "not_scheduled"
      },
      "reviewCard": {
        "reviewAt": null,
        "reviewState": "not_scheduled",
        "leadingIndicators": [],
        "triggers": [
          {
            "triggerId": "trigger_cash_evidence_ready",
            "condition": "现金承受力证据已由有权责任人复核",
            "response": "由用户重新打开决定与复查"
          }
        ],
        "closureRequiresUserConfirmation": true
      }
    },
    "no_decision": {
      "intent": "no_decision",
      "decisionCard": {
        "aiRecommendation": {
          "label": "AI 审议建议",
          "statement": "可以保留当前建议，等待用户在自己的节奏下决定。"
        },
        "userDecision": {
          "label": "用户自己的决定",
          "decisionCode": "no_decision",
          "statement": "用户尚未作出决定。",
          "status": "confirmation_pending",
          "confirmation": null,
          "persistenceState": "not_recorded"
        },
        "confirmationActionPresented": false,
        "confirmationActionState": "not_presented_no_decision"
      },
      "actionCard": {
        "items": [],
        "triggers": [],
        "reviewState": "not_scheduled"
      },
      "reviewCard": {
        "reviewAt": null,
        "reviewState": "not_scheduled",
        "leadingIndicators": [],
        "triggers": [],
        "closureRequiresUserConfirmation": true
      }
    }
  }
}
```
