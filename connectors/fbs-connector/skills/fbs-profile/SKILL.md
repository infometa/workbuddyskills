---
name: fbs-profile
description: 通过当前福帮手OAuth能力核对本人画像用途、读取已确认事实或提出待确认草案；用途、来源与事实确认分别校验。
metadata:
  ai.workbuddy.description_zh: 按本人已同意用途使用画像；事实提案仍需本人确认。
  ai.workbuddy.description_en: Use confirmed profile facts for an approved purpose, or propose one fact for separate owner confirmation.
  ai.workbuddy.version: 2026.9.25-r7
  ai.workbuddy.author: FBSir
---
# 本人画像

个人工作偏好的用途入口固定填写 **`contextType="PERSONAL"`、`contextId="personal"`、`purposeCode="expert-personalization"`**。`personal` 不是新建编号，不得替换为测试标签、任务名、时间戳或操作号。需要幂等编号时只单独填写 `operationId`，不能拿它作 `contextId`。

CASE 只用 **`contextType="CASE"`、本人已经存在且有权限的 `case-` 编号、`purposeCode="decision-support"`**；编号来自本人既有事项，不能猜测或临时新建。没有真实既有事项时先停在查询/说明，不调用用途写入口。

入口顺序：当前账号 `member_whoami` 与能力 `fbs_capabilities` → `profile_status` → 用户选择的用途/事实操作。三个读取都带已知专家的实际四字段。不要先走旧 `skill_whoami`；匿名业务绑定不用于核对 OAuth 登录账号。服务返回 `accountName` 时可核对登录名，但不把用户输入名称作为认证或查询他人的依据。

默认 canonical 资源已有受 OAuth 保护的画像工具面；本技能按[当前能力门](../fbs-connector/references/capability-routing.md)条件执行，不能统一视为 guidance_only，也不因目录可见就直接读取。先核对本次账号、工具/schema、真实专家四字段及当前服务准入。未知或被拒绝的后继版本保持原值并停止依赖画像的操作。

只在本次任务需要、用户选择相应用途时使用[画像用途与提案](references/profile-purpose-and-provenance.md)：

- profile_status：account:read，可选 contextRef；查看授权与用途状态，不返回事实。
- profile_manage_entry：profile:manage；operationId、contextType、contextId、purposeCode，生成待同意上下文及本人页面。这有元数据写入，需要用户本次意愿。
- profile_read：profile:read；contextRef，可选 fieldKeys（1–5 个唯一字段）、afterFactId；每页最多两项。只读本用途最少已确认事实。用途字段只用于本地匹配，不作为工具参数发送。
- profile_propose：profile:propose；operationId、contextRef、fieldKey、value、evidence、claimKind；每次一项待确认草案，value/evidence 各最多 256 字符。
- profile_operation_receipt：profile:manage；原 operationId；仅查询当前 client/grant 的 MCP 操作或读取审计。

`PROFILE_CONTEXT_UNSUPPORTED` 表示应核对以上组合及服务的 `supportedContexts`，`nextAction="review_context_contract"` 不授权自动改参或再次写入；不能猜成“临时产品未开放”。保留真实错误和原 `operationId`，不另生新号。结果未知时先查原号；`PROFILE_NOT_FOUND` 也不能证明原操作从未存在或没有副作用。核对参数/账号授权边界并得到明确后继安排后再执行新的写动作。UUID由调用端在用户明确选择操作后生成，不要求用户输入；可选纯本地校验器见[画像请求规划器](scripts/profile-request-plan.mjs)，它不联网、不代替服务判权。

上述五工具都要求真实 productId、packageName、expertEntryId、packageVersion。只传当前 schema 接受的顶层参数，不添加 intentSignal、flowRef、interopReceipt、userId、callerOperationId、expectedVersion、amend 或自造 purpose。

先由本人在网页同意用途，再逐项确认事实；OAuth 和 scope 不能替代这两步。claimKind 区分用户陈述、获准材料观察与专家推断，确认不会把声明来源升级为客观验证。无有效同意或工具时继续原产品允许的工作，不猜替代接口。

每个新任务及纠正/撤回后重新读取；不把 value/evidence 写入长期记忆。可选 interopReceipt 只辅助技术对账，不是业务回执或画像确认，详见[回执边界](../fbs-connector/references/interop-reconciliation.md)。当前删除/导出未开放，撤回不称已擦除。

当前读取须同时通过用途/时效和本轮实际工具 schema 校验，使用 scripts/profile-request-plan.mjs 的 planProfileReadRequest。只选本次任务必要字段；schema未观察或发生不支持的变化时停止，不猜别名后试写。账号连接有效不等于画像用途有效；未知回执不能改写成没有事实。
