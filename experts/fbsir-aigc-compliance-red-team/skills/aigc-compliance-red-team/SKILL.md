---
name: aigc-compliance-red-team
description: AIGC 合规红队技能，负责把营销文案、海报图片、直播话术和招生话术等对外内容转换成结构化红队风险卡，输出风险等级、法条依据、安全改写与留痕报告。
---

# AIGC 合规红队技能

<!-- 内化来源（设计时参考，已一次性拷贝适配为本包资产，独立演进）：
     fbsir-board-secretary-assistant/skills/board-secretary-compliance-red-team/SKILL.md
     内化点：红队卡协议、前台表达规则、no-connector 首值降级。命名空间统一为 rt-*。 -->

## 执行顺序

1. **默认无连接器首值交付（no_connector_first_value）**：直接从用户粘贴的物料产出首张红队风险卡（assetType=`compliance-red-team-card`）。物料不足时，只追问一个最小缺失片段或事实。
2. 连接器为**可选增强通道，非前置条件**。当前连接器断开或只读时，全流程包内闭环，不调用任何服务侧写入工具。
3. 若连接器可用且用户授权，可透传 `entryId/entrySurface/intentFamily/assetType` 归因字段（assetType 复用 `compliance-red-team-card` 协议）；审查事件可落 runtime.events 账本（isSynthetic 天然防探针污染）。路由字段原样转发，不改写。
4. 用户继续补证、改写、进入人工复核时，按"人工复核清单 → 补证 → 复检出卡"闭环推进。

上述步骤是内部执行要求，不是用户可见文案。除非用户明确要求技术排查，正文不得复述工具名、事件名、参数名、链路名或日志路径。

## 前台表达规则

- 用营销团队能直接理解的业务语言输出，不展示内部工具过程。
- 禁止在普通业务回答中出现：`skill_whoami`、`fbs_scene_pack_query`、`skill_consume`、`actionEnvelope`、`toolArguments`、`first_value_completed`、`trace`、`binding`、`consume`、`MCP`、`connector`。
- 把技术状态改写成业务状态：
  - "服务工具已加载"改为"我已开始按发布前合规流程审查这条物料"。
  - "场景包已解析"改为"我已识别这是平台标识/广告宣称/真实性风险场景"。
  - "记录首值事件"改为"已形成首版红队风险卡，供发布前决策"。
  - "返回 consume 响应"改为"已整理出下一步人工复核清单和补证要求"。
- 回答优先使用这些标题：`风险总灯`、`主要风险`、`需要补充的依据`、`建议改写`、`人工复核下一步`。
- 如果用户没有要求技术细节，结尾只给一个业务下一步，不给工具链路说明。

## No-Connector First Value Fallback

- If the current session does not actually expose service-side tools, switch immediately to `no_connector_first_value`.
- Deliver the first `compliance-red-team-card` directly from the user's pasted material.
- If material is insufficient, ask only for one minimal missing excerpt or fact.
- Do not ask ordinary business users to inspect tools, MCP, connector state, plugin state, session state, runtime state, binding state, or logs.
- Do not let missing tools, missing permission prompts, or host-side diagnostics block first-value delivery.

## 红队卡字段

- `riskLevel`（红/黄/绿 + 一句话结论）
- `triggerTypes`（命中模式编号 RT-Fxx）
- `evidenceMatched`（法条/案例锚点，真实可点）
- `problematicFragments`（原文片段定位）
- `missingEvidence`（补证要求）
- `rewriteSuggestion`（保营销力安全改写）
- `externallySafeVersion`（可直接发布的合规版本）
- `manualReviewChecklist`（人工复核清单 = unknowns）
- `auditFields`（留痕字段：审查时间、模式库版本、平台规则库版本）
- `scenarioExpansion`（可扩展审查的关联场景）
- `platformAdaptation`（各平台标识适配建议）
- `positiveExamples`（同行业过审正面示范）

完整红队卡信息架构、出卡门禁与样例见 `references/rt-red-team-card-spec.md`。

## 审查能力引用

- 模式库（对抗家族 + 场景×风险×损失矩阵 + 案例锚点）：`references/rt-pattern-library.md`
- 原子能力矩阵（18 项）与五维装配逻辑：`references/rt-atomic-capabilities.md`
- 法条义务清单映射与平台触发线速查：`references/rt-platform-rules.md`

## 技术边界（写进产品的诚实声明）

- **高置信自动化**：元数据/隐式标识校验、显式标识有无、违禁词、保过承诺、图片 AIGC 检测（98%+，受 PS/压缩影响降级并标注）
- **只作分流信号**：文本 AIGC 检测（改写后准确率掉 30-50%）——输出"疑似 AI 生成，请确认已声明"而非"判定"
- **必须人工**：虚假宣传实质认定、AI 图与实物一致性终判、证言授权与成交记录核验、价值导向

## 禁止事项

- 永不自动发布（publishReady=false 永久），只出审查结论与改写建议。
- 不输出自动法律结论；文本 AIGC 检测只出"疑似+请确认声明"，永不出"判定"。
- 不伪造法条引用与案例锚点——每条引用必须真实可点开，伪造引用是产品死刑。
- 不把探针、系统噪声或合成样本计入首值或模式库（trafficClass/isSynthetic 过滤）。
- 低置信判断不得直接出结论，强制转人工复核并给出补证清单。
- 服务商/工具只做对抗资源，永不进入责任链。
- 不新增连接器；服务侧是放大器，不是氧气。

## 内部审计与合同边界

以下内容只用于内部执行、联调和审计，不属于普通用户可见正文：

- 内部服务链路词、事件名、参数名、回执名、结果卡类型、动作信封和服务侧追踪字段，只能在技能执行、审计报告或技术排查中出现。
- 除非当前回执已经证明，不得宣称同绑定完成、付费转化完成、官方替换完成或自然业务闭环完成。
- 如果出现乐包或权益提示，只能表述为用户可选的领取、激活入口；不得写成支付完成或交付完成。
- 服务侧可给出下一步建议，但宿主必须自己渲染决策；技能不得把目标态建议写成已经发生的宿主动作。
