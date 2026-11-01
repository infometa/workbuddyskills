---
name: domestic-invoice-verification
label: 国内发票验真
icon: ""
description: 在用户明确要求核验中国大陆发票真伪或官方验真时调用 SealAI 发票验真。普通票据字段读取和境外小票识别不使用本流程。
---

# 国内发票验真

## 连接器与 OAuth

关联 `sealai-finance` Connector。未连接时引导用户通过 SealAI OAuth 登录、选择企业并确认授权；不得要求用户在对话中提供访问令牌。SealAI 按用户当前权限决定是否允许验真。

1. 仅在用户明确要求发票验真时调用 `expense_form_invoice_verify`，传入本次会话中的发票文件。
2. 工具返回 `job_id` 后，使用同一 `job_id` 调用 `expense_form_receipt_status`，直到任务完成或失败。
3. 返回 `installation_required=true` 时展示安装绑定引导并停止，不降级为豆包自行验真。
4. 只展示 SealAI 返回的验真状态和证据。`unsupported` 或 `not_attempted` 只能说明未完成官方验真，不得宣称发票为真。
5. 超时、429 或任务失败时如实说明，不自动重复提交验真任务。
