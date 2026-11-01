---
name: overseas-receipt-inspection
label: 境外小票识别
icon: ""
description: 识别境外消费小票并返回 SealAI 结构化结果。中国大陆发票官方验真、普通 OCR 和整单财务审核不使用本流程。
---

# 境外小票识别

## 连接器与 OAuth

关联 `sealai-finance` Connector。未连接时引导用户通过 SealAI OAuth 登录、选择企业并确认授权；不得要求用户在对话中提供访问令牌。SealAI 按用户当前权限决定是否允许识别。

1. 用户明确提供境外小票并要求识别时，调用 `expense_form_overseas_receipt_inspect`。
2. 工具返回 `job_id` 后，使用同一 `job_id` 调用 `expense_form_receipt_status`，直到任务完成或失败。
3. 返回 `installation_required=true` 时展示安装绑定引导并停止，不使用普通 OCR 冒充 SealAI 境外小票结果。
4. 只展示 SealAI 返回的字段、处理状态和错误，不补造缺失信息。
5. 超时、429 或任务失败时如实说明，不自动重复提交识别任务。
