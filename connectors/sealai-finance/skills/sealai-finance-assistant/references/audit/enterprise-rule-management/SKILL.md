---
name: enterprise-rule-management
label: 企业规则维护
icon: ""
description: 用户明确要求持久创建、修改或删除企业规则时，先预览变化，经确认后发布新版本。不承接新客空配置初始化或本次临时规则选择，不启动审核。
---

# 企业规则持久维护

## 适用范围与连接器

关联 `sealai-finance` Connector。只处理需要跨会话保存的企业规则创建、修改和删除。“这次审核采用哪些规则”使用“财务规则选择”，不在两个流程间复用确认；该流程不可用时说明能力边界，不改成持久发布。新客默认配置初始化使用“新客财务初始化”。用户只问风险或审核进度时，不据此发起规则变更。

未连接时，引导用户通过 SealAI OAuth 登录、选择企业并确认授权。规则 preview、publish 和 activate 遵守既有 `AUDIT_MANAGE` 权限要求；其他操作仍以现有 Tool 权限校验为准，不因只读或已连接就绕过校验。权限拒绝时停止，保留已完成结果。

## 执行步骤

1. **读取真实规则和当前基线。** 调用 `financial_audit_rule_update(action=list)`，取得当前企业规则的数据库 UUID、完整正文、严格度、状态和 `latestVersion`，完整展示相关规则。修改和删除只使用本次 list 返回的 ID，不根据描述、编号或旧会话记忆猜目标。查询失败时停止，不把失败当作规则为空。

2. **明确本次持久变化。** 仅收集用户明确要求的 create、update 或 delete 变化，不顺带调整其他规则。目标不唯一，或临时选择与持久修改意图不清时，先澄清再预览。规则严格度只能是 `MUST_FOLLOW`、`SHOULD_FOLLOW` 或 `SUGGESTION`。

3. **预览，不写入。** 调用 `financial_audit_rule_update(action=preview)`，完整展示新增、修改、删除、当前发布版本和预期指纹，说明这是待确认的预览，尚未写入或发布。保留这次 preview 的原始返回值，后续发布不得按文字摘要重新生成请求。

4. **确认本次预览后发布。** 只有用户明确确认这一次 preview 后，才调用 `financial_audit_rule_update(action=publish)`，原样映射以下参数：

   | publish 参数 | 本次 preview 返回值 |
   | --- | --- |
   | `changes` | `preview.changes` |
   | `expected_changes_fingerprint` | `preview.expectedChangesFingerprint` |
   | `expected_rules_fingerprint` | `preview.expectedRulesFingerprint` |
   | `expected_published_version_id` | `preview.expectedPublishedVersionId` |

   用户改变目标或变更内容、基线变化或指纹冲突时，停止发布，重新 list、preview 并重新取得确认，不自动覆盖。此前的变更意向或其他流程的确认，不代替对本次预览的确认。

5. **区分发布成功、激活和部分成功。** 按 Tool 实际返回的发布、激活状态反馈，不把一次 publish 调用完成笼统表述为规则已经全部生效。`activationStatus=published_not_activated` 表示版本已发布但未激活；不得重新 publish，只能调用 `financial_audit_rule_update(action=activate, version_id=<返回的 versionId>)` 重试 Agent 激活。`status=PUBLISHED_WITH_QUOTA_SYNC_FAILURE` 表示版本已发布但配额同步失败；不得重新 publish，配额同步留给系统补偿，只有同时返回未激活时才重试 activate。激活失败时保留已发布结果，说明仍未完成的部分。

## 异常与边界

preview 失败或用户尚未确认时，不发布。发布调用失败或返回不确定时，保留错误及已有版本证据，不自动重发 publish；无法确认的状态如实说明，不宣称未发布或全部成功。

发布的新企业规则供后续财务审核使用，不代表已经重新审核历史单据。本流程不调用 `financial_audit_start`，不执行人工审批、付款或通知，不修改只读行业规则包，不把持久化变更降为本次临时规则。
