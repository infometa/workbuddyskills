---
name: approval-document-query
label: 单据查询
icon: ""
description: 按 SealAI 单据标识或来源系统与来源单据标识查询当前企业单据，用于核对字段、状态和模板关联。
---

# 单据查询

## 连接器与 OAuth

关联 `sealai-finance` Connector。未连接时引导用户通过 SealAI OAuth 登录、选择企业并确认授权；不得要求用户在对话中提供访问令牌。

- 已知 SealAI 单据 ID 时，用 `document_id` 调用 `approval_document_get`。
- 已知业务来源标识时，用 `source_system + source_document_id` 查询。
- 返回来源单号、状态、模板引用和字段值；敏感字段仅按工具实际返回展示。
- 查不到时明确说明所用查询条件，不自动创建单据或改用其他企业查询。
