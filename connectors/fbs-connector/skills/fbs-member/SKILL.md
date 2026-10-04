---
name: fbs-member
description: 说明福帮手会员权益、积分与回执的能力边界；当前默认资源仅提供指引，不执行收费。
metadata:
  ai.workbuddy.description_zh: 仅说明会员权益、积分与回执的接入条件；未开放时不代查或扣费。
  ai.workbuddy.description_en: Explain membership, credit and receipt prerequisites; unavailable tools remain guidance only and never trigger billing.
  ai.workbuddy.version: 2026.9.25-r7
  ai.workbuddy.author: FBSir
---
# 会员与服务回执

会员权益、积分与收费工具在当前连接器Gateway仍为support_readiness=guidance_only；管理系统存在这些业务不等于该资源已暴露MCP工具。先遵守[公共路由](../fbs-connector/SKILL.md)。例外是已审查OAuth Gateway的member_whoami：通过能力门后可查最小账号主体/状态，但不返回会员权益、余额或实名证明。

按[权益与账务规则](references/entitlement-and-billing.md)区分账号与权益：member_check_entitlement、member_credit_status、member_service_receipt尚未在新Gateway开放，不调用或借其它后台代查。member_whoami仅在实际开放的OAuth资源按account:read调用；输出必要状态，不倾倒账号信息。

`member_settle_service` 会扣分，当前读取试点不开放。旧 `skill_whoami/skill_consume/lebao_status` 保持旧 API2 的身份场景、进度和奖励合同；禁止用会员系统的同名别名替换。查询、首值完成或积分充足均不代表已批准购买。

无会员/无画像同意按产品原权益与降级规则处理，不自动充值、购买或取消已有权益。未知或丢响应先查原回执，不换业务号结算。
