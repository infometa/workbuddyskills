---
name: new-customer-finance-setup
label: 新客财务初始化
icon: ""
description: 用户明确要求新客初始化时，幂等创建默认模板；仅在企业规则与版本均不存在时初始化规则。可另行确认导入固定演示草稿和演示审核，不补齐或覆盖已有配置。
---

# 新客财务初始化

## 适用范围与连接器

关联 `sealai-finance` Connector。只承接新客默认配置初始化，以及该流程中的可选演示数据导入和演示审核；不因用户首次报销、缺少模板或询问审核情况就自动初始化。

日常真实报销交给“报销草稿提交”；已有企业规则的创建、修改或删除交给“企业规则维护”。本流程中的模板、初始规则、演示草稿和演示审核由本流程统一编排，不同时启动其他流程重复执行这些操作。

模板阶段要求 `FORMS_MANAGE`；初始规则 preview、publish 和 activate 要求 `AUDIT_MANAGE`；演示草稿导入要求 `FORMS_USE`。各阶段权限由真实 Tool 校验，不因用户已连接或已确认就视为授权。遇到权限拒绝时停止初始化，保留已完成结果，不降级权限、切换身份或绕过限制。

## 固定数据与独立确认

固定输入位于 `references/new-customer-finance-presets.json`。先完整读取文件；只能按其中的模板、顺序和字段调用 Tool，不临时生成、补齐或改写案例。

模板初始化、初始规则发布、演示草稿导入、演示审核分别取得用户确认。确认只适用于已经展示的本阶段内容；“开始初始化”不代替后续确认，导入确认也不代替演示审核确认。尚未取得对应确认时，不执行该阶段的写操作。

## 执行步骤

### 1. 连接企业

未连接时，引导用户通过 SealAI OAuth 登录、创建或选择企业并确认授权，不要求用户提供令牌。

### 2. 确认并初始化两个模板

展示差旅和宴请模板的名称、版本、完整字段定义及说明，明确它们是 SealAI 默认模板，不代表客户制度。

取得具备 `FORMS_MANAGE` 权限的用户确认后，分别以两个 `templates[].input` 的原始内容调用 `approval_document_template_write`，固定传 `mode=create_if_missing`。逐个记录返回的模板 ID，并保留其与预置模板的对应关系。模板已存在时保留客户模板，不用 upsert 覆盖；某个模板失败时，不猜测它的 ID，也不把另一个模板成功表述为两个模板都已就绪。

### 3. 只在规则和版本都不存在时准备初始规则

调用 `financial_audit_rule_update(action=list)`，读取数据库规则 UUID、完整正文和 `latestVersion`。

只要已有任一规则或版本，就说明“已保留现有企业规则，跳过初始规则创建”，继续到演示草稿步骤；不修改、补齐或重新发布客户规则。查询失败或结果无法确认时，不把它当作规则为空。

仅当规则与版本均不存在时，调用 `finance_public_general_rules`。将返回的每条通用规则按现有 changes 结构映射为只含 `description`、`scope`、`strictness` 的 create change，再调用 `financial_audit_rule_update(action=preview)`。完整展示规则来源、免责声明、changes 和发布基线，不写死规则数量，不改写 preview，不把预览说成已发布。

演示预期比较必须另行核对规则基线，不把 fixture 自述当作当次 Tool 已验证的事实：

- 读取 `manifest.rule_baseline` 的 `reference`、`version`、`rules`、`digest_algorithm` 和 `digest`。其规范算法 `sha256-json-stringify-rules-v1` 为：按规则数组原序，每项固定键序 `id`、`description`、`scope`、`strictness`，取 `JSON.stringify` 无缩进输出的 UTF-8 字节做 SHA-256；不 trim、改写正文、重排规则或丢弃属性。该算法供既有离线校验重算，不是 Tool 提供的哈希能力。
- 将本次 `finance_public_general_rules` 返回的来源、版本和完整规则数组与上述快照逐项、逐字段严格比对，数量与顺序也须一致。只有一致时才可引用 fixture 摘要，并注明“实际 Tool 正文已比对，摘要来自已校验的预置快照”；不得声称 Tool 返回了摘要或在没有计算能力时声称已现场重算。快照、算法或正文缺失、不一致时标记预期不可比较。
- 发布并激活后再次 `list`，按 `description`、`scope`、`strictness` 完全相同且唯一的一一对应关系，记录每个 `general-*` 到实际企业规则 UUID 的映射、实际完整正文与版本证据。不得按数组位置或编号猜测 UUID；不得把企业 UUID 与公共 ID 直接比较。全部规则须对应且无新增、缺失、修改或重复歧义。
- 数据库 UUID 不等于实际审核命中 ID；企业审核会使用规则 code 或快照中的规则 ID。审核后从本次实际持久规则快照按同样的完整正文三元组唯一匹配，补全 `general-* / 企业数据库 UUID / 本次快照 rule.id` 三列映射，再用快照 ID 比较 `hitRules[].id`。不能用 list 的数组位置推断 `rule-N`，也不能直接拿 UUID 比命中 ID。
- 已有客户规则时仍保留并跳过创建；若用户要比较演示预期，使用只读 Tool 对现有规则做同样的完整核对与映射，不为匹配 fixture 修改客户规则。提交前再次核对版本和正文，审核后以实际持久审核的规则快照与三列映射验证本次生效基线。仅有当前 list、无法取得本次快照或实际命中 ID 无法映射时，也不能判定预期匹配。

导入摘要和演示审核展示分别记录公共规则基线、实际企业规则版本/映射以及 `manifest.synthesised_policy_digest`；制度摘要不能代替规则摘要。任一核对失败只说明基线差异或证据缺口，并将预期比较标为不可比较，不判成预期通过或失败，不改写 fixture。初始化仍按当前实际 Tool 规则及独立确认继续，不把演示基线当作覆盖客户规则的理由。

### 4. 确认预览后发布，区分发布与激活

取得具备 `AUDIT_MANAGE` 权限的用户对本次 preview 的明确确认后，调用 `financial_audit_rule_update(action=publish)`。以下值必须原样映射，不能重新拼装 changes、替换指纹或省略发布基线：

| publish 参数 | 本次 preview 返回值 |
| --- | --- |
| `changes` | `preview.changes` |
| `expected_changes_fingerprint` | `preview.expectedChangesFingerprint` |
| `expected_rules_fingerprint` | `preview.expectedRulesFingerprint` |
| `expected_published_version_id` | `preview.expectedPublishedVersionId` |

基线、目标或指纹发生变化，或出现并发冲突时，停止发布并重新执行步骤 3 的 list 检查。仍满足空规则、空版本条件时，重新 preview 并重新取得确认；若已出现规则或版本，则按步骤 3 跳过，不自动覆盖。

返回 `activationStatus=published_not_activated` 时，版本已经发布但尚未激活；不得再次 publish，只能调用 `financial_audit_rule_update(action=activate, version_id=<返回的 versionId>)` 重试 Agent 激活。`status=PUBLISHED_WITH_QUOTA_SYNC_FAILURE` 表示版本已发布但配额同步失败；不得再次 publish，配额同步留给系统补偿，只有同时返回未激活时才重试 activate。激活仍失败时保留已发布结果并说明限制，不宣称规则已全部生效。

发布调用失败或返回不确定时，保留错误与已取得的版本证据，不自动重复 publish，也不凭缺少响应宣称未发布。

### 5. 另行确认后导入 40 条固定演示草稿

演示数据只允许导入用户明确确认为“独立测试租户/演示环境”的企业，导入前先执行“数据口径与禁止操作”下“演示数据隔离边界”一节的租户确认。

询问具备 `FORMS_USE` 权限的用户是否导入 40 条固定演示草稿，说明导入只创建草稿，不提交、不审核。未明确同意时不导入；用户仅表达“初始化”“开始用”而未明确要演示数据时，不把它当作导入授权。

用户同意后，按 `demo_drafts` 的预置顺序，逐条调用 `approval_document_write`。每条只允许以下映射：

| Tool 参数 | 取值 |
| --- | --- |
| `mode` | `create_if_missing` |
| `source_system` | `finance_skill` |
| `source_document_id` | `draft.client_draft_id` |
| `template_id` | 步骤 2 返回的对应模板 ID |
| `source_document_sn` | `draft.source_document_sn` |
| `fields` | `draft.fields` |
| `source_document_url` | 仅预置中实际存在时，传 `draft.source_document_url` |
| `source_start_time` | 仅预置中实际存在时，传 `draft.source_start_time` |
| `source_end_time` | 仅预置中实际存在时，传 `draft.source_end_time` |

必须保留以下精确白名单映射：`source_document_id=draft.client_draft_id`、`source_document_sn=draft.source_document_sn`、`fields=draft.fields`。

通过案例的 `template_key` 对应预置模板的 `key`，再使用步骤 2 的真实模板 ID。缺少对应模板 ID 时说明依赖未满足，不猜 ID。不得传 `draft.template_ref`，不得将 `client_draft_id` 作为同名 Tool 参数传入，不得展开整个 `draft`，也不把案例说明或 `acceptance_expectation` 加入请求。

v4 的 `draft.fields` 包含可传输的合成证据：两类单据的 `applicant_grade` 和 `policy_basis`（完整合成制度 JSON 文本），以及宴请的 `preapproval_evidence`（逐单合成事前审批 JSON 文本）。这些字段须原样随 `fields` 写入，不能只在对话展示或留在顶层 manifest。审批证据须关联当前单号、申请人、业务日期和事由，包含审批时间、结果和适用范围；普通事前审批不等于超标特批，`special_exception=false` 不得解释为豁免人均或住宿标准。若已存在模板或草稿缺少这些字段，不覆盖、不补写旧版本，只披露该条证据不完整、不可按 v4 预期验收。

逐条记录 `document_id`、`revision`、新建或已存在的实际结果以及失败证据。普通单条失败时保留证据并继续后续条目；权限拒绝按前文要求停止。重复执行仍使用相同稳定 ID 和 `create_if_missing`，不得覆盖已有单据。

导入结束后先展示新建、已存在、失败和未执行的实际数量及逐项结果，并明确输出“风险验收未完成”。不得把草稿导入描述为已经提交、已经 AI 审核、已命中规则或已完成风险统计验收。

### 6. 导入结果展示后，另行确认演示审核

只有用户看过导入结果，并再次明确确认“演示审核”后，才逐条调用 `expense_form_submit`。这次确认对应已展示的待提交单据与 revision，不使用模板确认、规则确认或导入确认代替，也不默认启动 40 次 AI 审核。

提交固定使用 `document_id=approval_document_write 返回的 document.id`、`confirmed_revision=approval_document_write 返回的 revision`，不得改成其他参数名。没有取得真实 `document.id` 和 `revision` 的条目不提交；单据或 revision 与确认内容不一致时，停止该条提交，重新展示并重新取得用户确认，不悄悄替换已确认版本。

随后使用 `expense_form_progress` 收集实际 job、持久审核记录以及完成或失败证据。失败或结果不确定时，不自动重复提交。队列 `completed` 不等于审核通过，审核结论只能来自真实持久审核记录；没有结论的条目保留为尚未取得结果，不用验收预期补齐。

### 7. 按阶段汇总实际结果

分别说明模板、企业规则、演示草稿和可选演示审核完成了什么、跳过了什么，以及失败或尚未完成的部分。保留已成功结果与逐项证据，不把部分执行描述为完整初始化或完整验收。

## 数据口径与禁止操作

### 演示数据隔离边界

- 演示草稿（`demo_data=true`）仅可导入用户明确确认为独立测试租户或演示环境的企业；无法从当前环境确认为测试租户时，必须先显式向用户询问并披露下述统计影响，不得把本流程 的任何文案当作服务端已经隔离演示数据。
- 导入前必须向用户披露：演示数据 `demo_data=true` 会进入按业务日期统计的企业口径——`financial_audit_reimbursement_overview` 按租户加业务日期（单据 `source_start_time`）查询，不自动排除演示数据；若导入非测试租户，会污染该月份的企业报销统计。用户尚未确认租户性质前，中止导入并先确认。
- 让后台统计过滤 `demo_data` 属于生产行为变化，不在本流程 权限内；用户提出该需求时，说明当前限制并另行请求授权，不在本流程内承诺或实现。

### 预期证据前提与数据口径

40 条案例固定为 20 条差旅、20 条宴请，业务日期范围为 `2026-08-01T00:00:00+08:00`（含）至 `2026-09-01T00:00:00+08:00`（不含），时区为 `Asia/Shanghai`。这是 2026-09-28 口径的“上个月”，重复导入不移动日期。

演示案例保留 `demo_data=true`。以后用这些模板创建普通报销单时，必须传 `demo_data=false`。每条 `acceptance_expectation` 只是基于案例字段与初始通用规则设计的预期，`evidence_status=pending_real_audit`；20 条预期通过、20 条预期拒绝不是实测分布。

预期结论的规则前提必须随展示说明：fixture 的 `acceptance_expectation` 基于其公开规则快照与 `policy_basis` 中的合成制度，以及单据中可传输的职级和逐单审批证据。其中 `general-010`（职级/城市住宿标准）、`general-040`（招待人均标准）、`general-043`（招待事前审批）按该合成证据口径设计；制度全文、数值和适用范围以预置文件为准，不代表真实企业参数。审批编号本身不是充分证据。预期标签、说明和摘要等验收元数据仍不得混入业务字段或附件。

附件 URL 指向 SealAI 托管的合成测试 PDF（按预置附件清单逐条传入，数量以预置为准），带 `SYNTHETIC TEST FIXTURE` 标记，不是真实发票或经认证的凭证；只供测试环境验证审核流程，不得向用户宣称其具备真实报销效力。除预置 URL 外不补入其他附件或个人信息。附件不可访问时保留失败证据，不用预期代替审核。只有实际提交并取得持久 AI 审核结果后，才可验证演示范围的统计；真实执行过的演示审核仍属合成业务，不能冒充真实企业风险、费用分布或异常率。发现预期与实际不一致时报告差异，不修改 fixture。

不创建或修改审批流，不执行同意、驳回、退回、付款或评论写回，不增加自动通知。不将持久化规则修改降为本次临时规则。不调用 Shell、脚本或伪造的 MCP 结果代替真实 Tool 调用。
