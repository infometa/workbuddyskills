---
name: fbs-lebao
description: 福帮手乐包状态查询、领取与凭证兑换。奖励只在已有绑定和价值证据后处理；服务端掉落工具由包侧禁用，不向模型开放。
metadata:
  ai.workbuddy.description_zh: 查询、领取和兑换福帮手奖励凭证，保留原奖励合同。
  ai.workbuddy.description_en: Query, claim and redeem FBSir reward vouchers under the existing reward contract.
  ai.workbuddy.version: 2026.9.25-r7
  ai.workbuddy.author: FBSir
---
# 福帮手乐包后续

执行本技能时遵守[公共路由](../fbs-connector/SKILL.md)，完整读取 [lebao-lifecycle](references/lebao-lifecycle.md) 后组织参数。乐包凭证不等于会员钱包；不得把本工具族改为会员积分结算。

本页流程保留 canonical 旧乐包合同，仅在本轮实际开放时使用。历史独立 OAuth 预览不开放lebao_status/lebao_claim/lebao_redeem；不因旧工具名存在文档就尝试，也不改用会员积分工具或另一个后台代调。

## 固定顺序

1. 用户明确询问奖励状态时先调用 `lebao_status`。
2. 只有服务端已把用户推进到领取阶段且会话身份可验证时，才调用 `lebao_claim`。
3. 只有用户已有完整、可信的乐包凭证载荷时，才调用 `lebao_redeem`。
4. `lebao_drop` 是服务端管理工具，当前 plugin 包在 `.codebuddy-plugin/plugin.json` 的 `extensions.ai.workbuddy.policy.mcpServers.fbs-connector.disabledTools` 禁用；不得尝试调用或规避黑名单。服务端原始 `tools/list` 列出它，不等于宿主模型工具面允许它。

## 边界

- 奖励后续永远不抢在身份确认和价值交付之前。
- 领取或兑换明确失败时不自动重复写操作；丢响应或连接中断保持未决，先用当前 `tools/list` 实际提供的只读状态能力核对，不猜测恢复工具或生成新凭证。
- 签名、nonce、编码载荷和匿名绑定材料不得自行构造、补全或展示。
- 没有工具回执时，不声称奖励已领取、已兑换、已到账或权益已解锁。
