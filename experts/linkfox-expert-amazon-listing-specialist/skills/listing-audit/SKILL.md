---
name: listing-audit
description: Amazon Listing 深度诊断与诊断后优化交接。用于已上架、已提供或刚生成 Listing 的全面体检、链接诊断、为什么没流量或不转化，以及 AI 导购、VOC、移动端、漏斗和架构根因，复用 listing-quality-scorer 统一分数。只要数字分走 scorer；已明确直接改写走 listing-core rewrite；“诊断并优化”时输出 auditHandoff 并连续交给 Core。本 Skill 只诊断不改写；无后台报表时漏斗为 N/A。即使证据不全也应审计可用部分。
---

# Listing Audit

本 Skill 负责“为什么”和“下一步改什么”，不维护第二套评分、不写 Listing。基础 `scorePanel` 必须由 `listing-quality-scorer` 产生；Audit 只增加不重复计权的诊断视角和 `auditHandoff`。

## 输入与复用

- `target`：ASIN、Listing 字段，或 Core 的 `run-manifest.json`。
- 可选：`seller_reports`、`backend_attributes`、`competitor_asins`、`audit_depth=fast|standard`。
- 有 Core manifest 时复用 facts、Product Detail、SIF、评论、检查报告和 AI readiness，不重复取数。
- ASIN 入口只补缺失证据；相同参数复用 24h 缓存。

开始取数前读取 [evidence-routing.md](references/evidence-routing.md)。只有存在卖家报表时读取 [funnel-diagnosis.md](references/funnel-diagnosis.md)。组装产物和交给 rewrite 前读取 [audit-output-contract.md](references/audit-output-contract.md) 与 [audit-rewrite-handoff.md](../listing-core/references/audit-rewrite-handoff.md)。

## 执行

1. 外部 ASIN / 粘贴文案先跑一次 `scripts/run_preflight.py`，在一个本地进程中完成字段归一化、合规词库和原始字段 QA；以它的 `listing` / `field_provenance` / `field_metrics` 及检查产物为唯一来源，不得手工拆分标题补齐 Highlights。
2. 复用 preflight 的本地字段检查与合规结果；已有 Core 产物时直接复用，Alexa 问答实测(计费)仍需用户同意。
3. 以 `listing-quality-scorer` 作为本轮唯一语义评估步骤：同一响应形成 canonical 8 维扣分证据、诊断 findings，以及 rewrite 可直接复用的四柱洞察、买家问题和关键词计划；再由确定性脚本计算分数，Audit 不另起一轮重算。
4. 从同一批 findings 输出额外诊断视角：
   - AI 导购理解：实体关系、问题覆盖、事实边界；
   - 移动端/视觉：标题首屏、前两点、图片/A+；
   - VOC：赞点、槽点、顾虑和未满足问题；
   - 漏斗：仅在真实报表存在时归因；
   - 架构：类目节点、属性和变体。
5. 将发现拆成 `field_actions` 与 `operational_actions`，生成 `auditHandoff`。语义结果不得直接作为最终产物；必须先运行 `scripts/normalize_audit_report.py`，把 handoff 规范化并校验本地证据路径。校验失败时停止，不得展示“直接改写”或降级成普通 rewrite。
6. 独立 audit 请求只交付报告；若上层场景是“诊断并优化”、带 `[deliveryContract:listing-final]` 或已明确 rewrite，本报告只是中间产物：必须把 handoff 交回上层并继续 `listing-core mode=rewrite`，不得向用户结束任务。

## 性能约束

- 审计刚生成的 Core 产物时，默认零新增 Product Detail/SIF 调用。
- Product Detail 评论摘要正常时不拉评论明细；升级条件和费用沿用 [Core 评论策略](../listing-core/references/review-depth-policy.md)。
- 补充后台报表后只更新漏斗视角与 handoff，不重跑评分、VOC、视觉或架构。
- Audit 最多一次语义评估；canonical 扣分项和诊断视角在同一响应产生，评分脚本不调用模型。
- normalize、合规词库和字段 QA 必须走一次 preflight，不拆成多条命令；其输出自带毫秒耗时。
- 输出 Markdown/JSON，不调用专用渲染器。

## 输出

- `auditReport`：证据化诊断视角，不生成第二个 overall。
- `scorePanel`：原样引用 scorer 结果。
- `aiReadiness`：原样引用 scorer 派生面板，可追加 Alexa 问答实测(计费)结果但不得改基础分。
- `auditHandoff`：Core rewrite 的唯一结构化入口；“诊断并优化”时须在 `evidence_paths` 带同轮生成的 `keywords`、`buyer_questions`、`insight`，使 Core 免做重复 S3。
- `next_actions`：按报告改写、补报表、补评论、调整图片/价格/广告或暂不处理。

## Guardrails

- 只诊断不改写；用户已明确要求“诊断并优化”时可连续编排 Audit → Core，无需再次确认写作。
- 不负责店铺授权或拉取报表；漏斗分析仅消费用户或宿主提供的数据。
- 没有可比周期或基线时，不得断言 CTR/CVR“低”；只描述观察值和证据缺口。
- 文案不能解决的主图、价格、评分、广告、库存、变体问题必须进入 `operational_actions`，禁止伪装成文案修复。
- 不承诺 A10/COSMO/Alexa/Rufus 收录、回答或推荐结果；审计仅做内容结构判断。真实外部抽样只支持 Alexa 且须走 `listing-ai-readiness` 的 `alexa_live` 确认门禁；Rufus 不提供在线探测。
- 用户可见报告不暴露脚本名、内部 key 或实现兼容来源。
- 报告语言默认中文：`observation`、`impact`、`action`、`next_actions` 和对话摘要一律中文；引用的 Listing 原文、关键词和字段名保留原文。目标站点是英文站不构成改用英文出报告的理由，只有用户明确要求时才切换。

## 产物与落盘

本 skill 的 `run_preflight.py` 只保存确定性准备产物。最终报告由调用方保存为 UTF-8 JSON
或 Markdown，不依赖专用 HTML、上传或平台会话协议。载荷带
`kind=listingAuditReport`、`schema_version=2`，形状见
[audit-output-contract.md](references/audit-output-contract.md)。

`auditHandoff` 是 `listing-core mode=rewrite` 的唯一结构化入口，必须包含在同一份产物里，不要另落一份。最终报告必须带 `rewrite_ready=true`；该字段只能由 `normalize_audit_report.py` 写入，禁止模型自行声称就绪。
