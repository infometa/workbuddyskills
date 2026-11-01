---
name: approval-document-write
label: 单据写入
icon: ""
description: 使用已保存的 SealAI 模板幂等写入业务单据。只保存单据数据，不发起审核、审批或付款动作。
---

# 单据写入

## 连接器与 OAuth

关联 `sealai-finance` Connector。未连接时引导用户通过 SealAI OAuth 登录、选择企业并确认授权；不得要求用户在对话中提供访问令牌。

- 必须取得已保存模板的 SealAI `template_id`；只有外部模板标识时，先完成模板管理。
- 调用 `approval_document_write` 时提供稳定的 `source_system`、`source_document_id`、展示单号和字段数组。
- 字段类型和值必须匹配模板定义；缺少必填值时先让用户补充，不编造默认值。
- 相同租户、来源系统和来源单据 ID 重复写入会更新同一单据。
- 返回实际保存的 SealAI 单据 ID 和模板引用，明确说明本操作没有发起审批。
