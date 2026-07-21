---
name: board-secretary-compliance-red-team
description: 董秘助手合规红队技能，负责把公告、路演、问答、调研纪要和投资者互动材料转换成结构化风险卡。
---

# 合规红队技能

当需要把董事会秘书相关材料写入服务侧主链时，按以下顺序执行：

1. 调用 `skill_whoami`，带上董事会秘书入口字段。
2. 如果返回 `nextTool=fbs_scene_pack_query`，原样透传 `actionEnvelope.toolArguments`。
3. 读取并渲染 `resultCard.assetType=compliance-red-team-card`。
4. 首张风险卡真实交付后，调用 `skill_consume` 并记录 `eventType=first_value_completed`。
5. 如果用户继续补证、改写、进入人工复核，继续记录 `continued_use_completed`、`manual_review_required`、`contact_request` 或服务侧指定事件。

上述步骤是内部执行要求，不是用户可见文案。除非用户明确要求技术排查，正文不得复述工具名、事件名、参数名、链路名或日志路径。

## 前台表达规则

- 用董办能直接理解的业务语言输出，不展示内部工具过程。
- 禁止在普通业务回答中出现：`skill_whoami`、`fbs_scene_pack_query`、`skill_consume`、`actionEnvelope`、`toolArguments`、`first_value_completed`、`continued_use_completed`、`trace`、`binding`、`consume`、`MCP`、`connector`。
- 把技术状态改写成业务状态：
  - “服务工具已加载”改为“我已开始按董秘合规流程初筛材料”。
  - “场景包已解析”改为“我已识别这是投资者沟通/披露口径风险场景”。
  - “记录 first_value_completed”改为“已形成首版风险卡，供人工复核”。
  - “返回 consume 响应”改为“已整理出下一步复核清单和补证要求”。
- 回答优先使用这些标题：`初步判断`、`主要风险`、`需要补充的依据`、`建议改写`、`人工复核下一步`。
- 如果用户没有要求技术细节，结尾只给一个业务下一步，不给工具链路说明。

## 必填入口字段

```json
{
  "entryId": "board-secretary-compliance-red-team",
  "entryPromptCode": "wb_fbsir_board_secretary_compliance_red_team",
  "entrySurface": "expert_center",
  "expertEntryId": "fbsir-board-secretary-assistant",
  "intentFamily": "board_secretary_ir_workflow",
  "profileSegment": "board_secretary",
  "assetType": "compliance-red-team-card"
}
```

## No-Connector First Value Fallback

- If the current session does not actually expose `skill_whoami / fbs_scene_pack_query / skill_consume`, switch immediately to `no_connector_first_value`.
- Deliver the first `compliance-red-team-card` directly from the user's pasted material.
- If material is insufficient, ask only for one minimal missing excerpt or fact.
- Do not ask ordinary business users to inspect tools, MCP, connector state, plugin state, session state, runtime state, binding state, or logs.
- Do not let missing tools, missing permission prompts, or host-side diagnostics block first-value delivery.

## 红队卡字段

- `riskLevel`
- `triggerTypes`
- `evidenceMatched`
- `problematicFragments`
- `missingEvidence`
- `rewriteSuggestion`
- `externallySafeVersion`
- `approvalNextStep`
- `auditFields`
- `scenarioExpansion`
- `authorizedContext`
- `personalizationProfile`
- `regulatorySourceRegistry`
- `workflowChecklists`
- `p0p1p2Coverage`

## 结构化能力要求

- 必须返回 `resultCard.assetType=compliance-red-team-card`、同 binding `valueEvent`、`riskLevel`、`evidenceMatched`、`rewriteSuggestion` 和 `approvalNextStep`。
- 必须返回 `hostCapabilityRequest`、`deliveryTask`、`deliveryTaskboard` 和 `opsBoard`；宿主只有在用户明确授权后才能传入文档上下文，服务端不保存原始敏感文件。
- 必须返回 `regulatorySourceRegistry`、`scenarioExpansion`、`personalizationProfile` 和 `workflowChecklists`。
- 如果服务侧返回乐包进度、意图归集或个性化下一步，必须保持 `anonymousUserCodeHash / serverBindingId / chainFingerprint` 这类脱敏同绑字段，不把真实身份暴露到用户可见正文。
- 用户身份可以在服务侧按脱敏规则归一，但 `董秘助手` 的乐包来源、产品签名和场景签名必须与其它专家或 skill 分开保留，不能混源计功。
- 必须覆盖公告审查、互动回复、调研纪要、舆情回应、三会流程和业绩指引问答等场景。
- 支持的角色画像包括 `board_secretary`、`securities_rep`、`ir_director` 和 `cfo_office`；公司画像字段缺失时，应先提示补充，再输出最终交付建议。

## 禁止事项

- 不新增连接器。
- 不把宿主渲染当成服务侧商业或合规决策。
- 不输出自动法律结论、自动披露结论或自动发布动作。
- 不把探针、系统噪声或普通工作区请求计入董事会秘书助手首值。

## 内部审计与合同边界

以下内容只用于内部执行、联调和审计，不属于普通用户可见正文：

- 内部服务链路词、事件名、参数名、回执名、同绑定状态、结果卡类型、动作信封和服务侧追踪字段，只能在技能执行、审计报告或技术排查中出现。
- `BSA-PKG-003` 与 service-forward fields 当前属于“声明并待验证”范围；字段缺失要保持可见，但不能阻断首轮合规红队卡交付。
- 除非当前回执已经证明，不得宣称同绑定完成、付费转化完成、官方替换完成、自然业务闭环完成或宿主运行时升级完成。
- 如果出现乐包或权益提示，只能表述为用户可选的领取、激活和补充研究字段入口；不得写成支付完成、自然产品信用、官方替换或交付完成。
- 服务侧可给出宿主下一步建议，但宿主必须自己渲染决策；技能不得把目标态建议写成已经发生的宿主动作。
