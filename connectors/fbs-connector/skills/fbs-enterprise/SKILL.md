---
name: fbs-enterprise
description: 说明福帮手企业服务的范围与授权条件；当前默认资源仅提供指引，企业和个人权限账务分开。
metadata:
  ai.workbuddy.description_zh: 仅说明企业服务与事项的授权条件；工具未开放时不代查、预占或扣费。
  ai.workbuddy.description_en: Explain enterprise scope and approval prerequisites; unavailable tools do not query cases, reserve services or charge accounts.
  ai.workbuddy.version: 2026.9.25-r7
  ai.workbuddy.author: FBSir
---
# 企业服务与事项

本资源企业工具仍为support_readiness=guidance_only，当前OAuth Gateway未暴露；管理系统企业网页/API已有实现不构成MCP调用授权。组织画像也未实现，不能把企业context降级为PERSONAL。遵守[公共路由](../fbs-connector/SKILL.md)，仅后续独立审定并真实开放后使用以下工具。

先完整读[组织与服务状态机](references/organization-and-service-lifecycle.md)。组织须用户明确选择、服务端核验当前成员权限；不猜组织编号，管理员身份不等于能读全员私有内容。

未来 `member_enterprise_prepare` 仅建立待确认入口；网页批准组织、范围和费用后才可 start；真实交付后 complete，取消未结算操作用 cancel，结果核对用 receipt。每项都使用原服务上下文，不另造编号。

企业事项 list/get 只读本人；create/link/artifact_save 只保存明确选择的最小信息，不上传正文或路径。企业额度不足不改扣个人；没有网页批准、不明状态或能力缺失时不预占、不执行收费服务。
