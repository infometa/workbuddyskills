---
name: approval-document-template-management
label: 单据模板管理
icon: ""
description: 将用户确认的业务字段定义幂等写入 SealAI 单据模板，并按模板标识查询核对。未确认字段定义时不得写入。
---

# 单据模板管理

## 连接器与 OAuth

关联 `sealai-finance` Connector。未连接时引导用户通过 SealAI OAuth 登录、选择企业并确认授权；不得要求用户在对话中提供访问令牌。

- 写入前确认 `source`、`source_template_id`、`version`、模板名称和完整字段定义。
- 每个字段必须包含稳定 `key`、展示 `label`、合法 `type` 和 `required`。
- 同一来源、外部模板 ID 和版本重复调用 `approval_document_template_write` 会更新同一模板。
- 写入后返回 SealAI `id`，后续单据写入必须使用该模板 ID。
- 需要核对已保存模板时调用 `approval_document_template_get`，不得用猜测补齐字段。
