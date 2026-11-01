---
name: audit-comment-writeback
label: 审核评论写回
icon: ""
description: 在 SealAI 飞书单据审核完成且用户已看到评论预览后，将审核结论写入飞书全文评论。没有当前会话明确确认时不得调用。
---

# 审核结论评论写回

## 连接器与 OAuth

关联 `sealai-finance` Connector。未连接时引导用户通过 SealAI OAuth 登录、选择企业并确认授权；不得要求用户在对话中提供访问令牌。调用时必须复用已完成飞书审核任务的 `job_id`，SealAI 按用户当前权限决定是否允许写回。

- 仅处理已完成的飞书单据审核；当前对话材料审核不支持写回。
- 先完整展示 `financial_audit_status` 返回的评论预览，并询问用户是否写回。
- 只有用户在当前会话明确同意后，才使用该审核任务的 `job_id` 调用 `financial_audit_comment_writeback`。
- 不接受用户另行提供的评论正文，不修改 SealAI 生成的结论，也不执行审批动作。
- 调用结果不确定或失败时如实说明，不自动重试，避免重复写入。
