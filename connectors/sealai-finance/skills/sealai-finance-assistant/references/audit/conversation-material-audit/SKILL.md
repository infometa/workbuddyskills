---
name: conversation-material-audit
label: 对话材料审核
icon: ""
description: 使用企业、跨行业通用、行业参考或临时规则审核当前对话中的文本、PDF、图片或其他材料，并展示 SealAI 逐条结果。按飞书单号取单和评论写回不使用本流程。
---

# 当前对话材料审核

## 连接器与 OAuth

关联 `sealai-finance` Connector。未连接时引导用户通过 SealAI OAuth 登录、选择企业并确认授权；不得要求用户在对话中提供访问令牌。SealAI 按用户当前权限决定是否允许审核。

已有材料审核 `job_id` 且用户只要继续查看结果时，直接复用该 `job_id` 调用 `financial_audit_status`，不执行下述新审核的 context、prepare 或 start 步骤，也不重新提交材料或写回评论。

1. 调用 `financial_audit_context_status`；未绑定时展示安装引导并停止，任何材料都不得游客审核。
2. 用户未指定规则来源时，调用 `financial_audit_prepare`；企业规则可用时采用返回版本，没有可用企业规则时让用户在跨行业通用、行业参考和本次临时规则之间选择。用户只说“通用规则”时，询问是跨行业通用还是行业参考规则。
3. 用户选择或已经指定行业参考规则时，调用 `financial_audit_industry_catalog` 确认行业，再调用 `financial_audit_industry_rule_prepare` 获取并逐条展示完整规则和固定参数。行业不明确时只询问一次。行业规则只读；用户要求修改时，将本次所选规则复制为完整临时规则，只修改用户明确指定的内容，并说明来源已变为“本次临时规则”。
4. 向用户展示本次实际使用的完整规则并取得明确确认，确认前不得调用 `financial_audit_start`。未修改的行业来源使用 `type=industry`、规则包 `reference` 和 `selected_rule_ids`；由行业规则转换出的临时规则使用 `type=custom` 和完整 `rules`，不得传行业覆盖字段。
5. 调用 `financial_audit_start`，只传 `material` 及规则来源，不传 `document_number` 或飞书查询参数。材料可包含粘贴文本和最多 10 个当前会话文件。
6. 取得 `job_id` 后，使用同一 `job_id` 调用 `financial_audit_status`，只展示 SealAI 返回的证据、逐条规则结果和结论。

工具不可达或任务失败时不降级为豆包自行解析或审核。材料审核不支持飞书评论写回。
