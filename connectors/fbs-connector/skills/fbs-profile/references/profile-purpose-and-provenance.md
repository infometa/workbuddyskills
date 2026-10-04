# 画像用途、提案和来源

先通过[capability-routing](../../fbs-connector/references/capability-routing.md)。本文输入形状与机器合同 sourceSnapshot 绑定的 R15 canonical 七工具源码及实际编译定义核对；运行时工具/schema、准入、账号政策和用途授权仍逐项确认。历史 172a425 预览留在机器合同 historicalPreviewGateway，不能用它的合成账号/三产品限制替代当前资源。当前机器边界见[身份合同](../../fbs-mainline/references/identity-contract.json)的 resourceProfiles.canonicalProfileGateway。

账户来自本资源有效 OAuth，主体在同一 issuer 内不随客户端或组织改变；不在参数补 subject_id/userId/grant，不以匿名 binding、产品ID或昵称选择他人。contextRef只能由服务签发，绑定账号、当前client/grant、精确上下文和用途。不同grant各自网页同意后才共享本人同范围事实；新grant不能复用旧ref。共享连接器的productId仅为声明来源，不能实现按专家保密。

当前仅支持以下范围，不自动将事项事实提升为个人偏好，也不跨事项复制：

| contextType / contextId / purposeCode | 合法fieldKey |
|---|---|
| PERSONAL / personal / expert-personalization | work_role、industry、experience、goals、constraints、decision_style、preferred_language、output_preference、delivery_preference、collaboration_preference |
| CASE / 本人已有个人case-ID / decision-support | objective、constraint、decision、success_criteria、deadline |

`PERSONAL` 的 `contextId` 只能是字面值 `personal`，不因每次任务或测试而变化；它与新写动作的 `operationId` 是两个字段。`CASE` 编号必须来自本人已有事项且以 `case-` 开头，服务仍独立检查存在性和归属。当前 `profile_status.purposes` 会给出 PERSONAL 的 `contextId=personal/contextIdSource=fixed`，以及 CASE 的 `contextIdSource=existing_personal_case/contextIdPrefix=case-/contextIdMustExist=true`；以本轮实际返回核对，不能把提示值扩展成新建事项能力。

组织画像、企业事项编号和organizationId覆盖明确拒绝，不能降级成个人。事项由本人门户已有流程选择/创建；本资源没有member_case_create等事项工具。只提出用户明确选择的最少短值，不上传聊天全文、原稿、媒体、文件路径、证件或凭据，不推断无关敏感标签。会员/账务信息不是可编辑画像字段。

`profile_manage_entry` 用完整四字段及operationId、contextType、contextId、purposeCode建立PENDING上下文并给manageUrl。用户在本人网页登录状态下明确同意用途后，才可读取/提案。当前用途有效期24小时；context.status为ACTIVE还须未过期且授权仍有效，不能仅凭状态字符串放行。

`profile_read` 除四字段外仅接收contextRef、可选fieldKeys和afterFactId。fieldKeys显式提供时为1–5个唯一合法字段；省略表示本用途范围，但任务辅助应主动选最少字段。每页最多2项，返回facts/count/hasMore/nextAfterFactId、consentVersion和auditOperationId；没有pageSize或通用cursor参数。每页检查当时当前版本，paginationConsistency=CURRENT_VERSIONS_PER_REQUEST，不承诺跨页快照。profile_status只列当前grant最多10个上下文，可传已知contextRef精确查询；不要自造分页参数或猜ref枚举。

事实条目含factId、fieldKey、value、evidence、source、revision、confirmedAt、confirmation、userCorrected。claimKind位于source内；没有每条事实expiresAt字段。到期与撤权看当前用途/授权，时间字段为Unix秒。仅返回最新ACTIVE且已经本人确认的事实，待审提案不当作事实。

`profile_propose` 必填operationId、contextRef、fieldKey、value、evidence、claimKind，每次一项。value/evidence各最多256个UTF-16字符单位；claimKind只能明确取user_statement（用户已陈述）、artifact_observation（本轮获准材料观察）、expert_inference（专家推断），缺失不得猜测或代填。sourceEvidenceTrust固定client_declared_unverified；本人确认或纠正后仍保留原kind/evidence，不因此证明观察客观正确。

operationId在用户明确选择某项写操作后由调用端本地分配并保留，同号同载荷返回原回执，异归属/载荷/产品版本冲突则停止。优先使用安全随机UUID；不要向用户索要内部操作号，也不要把个人信息放进编号。可选本地请求规划器见[profile-request-plan.mjs](../scripts/profile-request-plan.mjs)，纯本地验证不联网，不能代替实时schema或服务判权。MCP新增提案不接收callerOperationId、expectedVersion、amend或独立purpose参数。丢响应先按原operationId查profile_operation_receipt；同账号不同grant不能跨读该回执，需本人网页核对，不能另造新号。

任务追踪中`episodeId`只作本地任务分组，`attemptId`每次调用重新生成；二者不进入闭合工具schema。工具回执里的JSON-RPC `requestId`、写操作`operationId`和服务`requestRef`分别保存，不能用其中一个替代另一个。没有同一实际响应中的requestRef时标记`not_observed`，不按时间拼接用户或操作。

`PROFILE_CONTEXT_UNSUPPORTED` 的安全下一步是 `review_context_contract`：核对 `supportedContexts` 中的精确组合及既有事项来源，保留错误与原操作号，不自动替换contextId或再次调用写入口。即使本次返回 `serviceRequestAccepted=false`，也不能由此断言此前同号操作从未存在；`PROFILE_NOT_FOUND` 同样只说明当前查询没有返回该回执。用户和主任务确认后继方案前不改变载荷/版本或新造操作号重写。此错误不是OAuth失效、scope不足、用途同意缺失或“平台未开放”的通用别名。

提案不是确认。网页写操作使用本人Cookie、固定同源、X-Fbs-Profile:1及expectedVersion；这些由本人页面处理，模型不能手工搬运Cookie、伪造批准或向MCP塞accepted=true。当前没有另行暴露的一次性挑战参数。

| 本人网页动作 | expectedVersion对应对象 |
|---|---|
| CONSENT、WITHDRAW_PURPOSE | context.version |
| CONFIRM | proposal.version，且原consentVersion仍匹配 |
| CORRECT、WITHDRAW_FACT | fact.revision |

网页实际回执为operationId/action/status=COMPLETED/result/replayed/completedAt；网页操作通过本人网页核对，不是当前grant的MCP回执。确认是逐项动作，不能把用途同意当成全部草案确认。同字段已有有效事实时，新草案确认冲突，改走本人纠正。

单项撤回追加tombstone；用途撤回使该账号同上下文/用途的所有客户端同意失效，终止待确认草案并撤回对应事实。重新同意不自动复活旧值。解绑只撤销对应客户端；其他有有效同意的客户端仍可用。本人Cookie管理不因某个grant失效而失去纠正/撤回权限。当前是版本化撤回，不是hard-delete；删除和导出尚未实现，不承诺入口或已擦除。

每个新任务及纠正/撤回后重新读取，不用旧值补回。value/evidence不得进入长期记忆、日报、索引或案卷缓存；仅在用户已允许的持久记录内保留contextRef、purposeCode、consentVersion、factId/revision、operationId/auditOperationId等无值引用。新授权和引用都不隐含额外写权限。

每次成功读取（含空结果）产生新的READ_AUDIT技术观察：auditOperationId由服务生成，readOnlyHint=true表示不改画像正文/不扣费，idempotentHint=false反映每次审计号不同。回执记录读取者来源和准备返回的factId/revision，不存正文；deliveryStage=SERVICE_RESULT_PREPARED不是宿主收到、完整阅读、模型采用或成交证明。撤权后的失败读取不会生成成功读回执。

confirmation=ACCOUNT_OWNER只表明本人网页确认。当前产品/参与者仍是client_declared，hostExecutionProven、自然和产品信用标志保持false；没有宿主签名不妨碍本人已同意的画像闭环，但不授予专家保密权限或可信逐成员执行结论。
