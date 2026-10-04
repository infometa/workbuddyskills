---
name: kiwi-sourcing
display_name: Kiwi 采购询价
display_name_en: Kiwi Sourcing & Negotiation
description: Source products, request quotes, compare offers, and negotiate non-binding terms with suppliers.
description_zh: 查找供应商、跨商家询价、比价并协商非绑定采购条款。
description_en: Source products, request quotes, compare offers, and negotiate non-binding supplier terms.
allowed-tools: kiwi_search, kiwi_request_quotes, kiwi_get_task, kiwi_negotiate, kiwi_accept_agreement, kiwi_get_agreement, kiwi_handoff, kiwi_approve, kiwi_reject
version: 1.0.0
author: HarryLabs
user-invocable: true
---

# Kiwi 采购询价

当用户要找供应商、询价、比价、议价，或询问交期、起订量和售后时使用本技能。Kiwi 形成的
是非绑定商业协议：不创建订单、不支付、不锁库存，也不代表用户签署具有法律约束力的合同。

## 标准流程

1. 用 `kiwi_search` 发现候选供应商。把商品名称保持为短词，规格、预算、地区和时间要求另行整理。
2. 默认最多选择 3 家相关商家，调用 `kiwi_request_quotes`。每次写调用使用新的稳定幂等键。
3. 用 `kiwi_get_task` 查看结果。收到 `partial_success` 时保留成功报价，并明确列出失败商家。
4. 按总价、交期、MOQ、售后、币种和证据完整性比较，不只按单价排序。
5. 用户要求还价或澄清时调用 `kiwi_negotiate`，不要擅自改变预算、数量或交付底线。
6. 接受前调用 `kiwi_accept_agreement`。若返回 `approval_required`，先展示完整摘要，获得用户明确确认后调用 `kiwi_approve`，再携带返回的 `approval_id` 重试原 action。
7. 用 `kiwi_get_agreement` 核对协议、摘要和 digest。
8. 用户确实需要后续入口时再调用 `kiwi_handoff`。handoff 是单独 action，必须使用它自己的审批，不能复用接受协议的审批。

参数与隐私规则见 @references/commerce-intent.md，审批规则见 @references/approval-flow.md，
异常处理见 @references/error-recovery.md。

## 工具选择

| 工具                    | 用途                         | 约束                                |
| ----------------------- | ---------------------------- | ----------------------------------- |
| `kiwi_search`           | 发现供应商                   | 只读；先于询价                      |
| `kiwi_request_quotes`   | 向候选商家询价               | 最多 3 家；提供合法 intent 和幂等键 |
| `kiwi_get_task`         | 查看任务、报价与部分结果     | 超时后优先查询，不无限重试          |
| `kiwi_negotiate`        | 还价、澄清条款               | 不越过用户明确底线                  |
| `kiwi_accept_agreement` | 接受非绑定协议               | 需要对应 action 的审批              |
| `kiwi_get_agreement`    | 读取协议与审计摘要           | handoff 前核对                      |
| `kiwi_handoff`          | 生成 checkout、PO 或联系入口 | 不等于完成下单或支付                |
| `kiwi_approve`          | 批准待审批 action            | 只有用户明确确认后调用              |
| `kiwi_reject`           | 拒绝待审批 action            | 用户拒绝或条款不清时调用            |

## 必须向用户呈现的信息

在任何批准前，至少展示商家、商品与数量、总价及币种、交期、MOQ、售后/退换条件、报价
有效期、缺失信息和风险。不得只说“是否确认”。批准后也要说明结果仍是非绑定协议或后续入口。

## 禁止事项

- 未获得当前对话中的明确确认时，不调用 `kiwi_approve`；
- 不把同一 `approval_id` 用于不同 action、不同报价或已变化的条款；
- 不把聊天记录、联系人、地址、组织目录或 WorkBuddy 记忆整体放进采购意图；
- 不承诺 Kiwi 已下单、已付款、已锁库存或已签署合同；
- 不因某一家超时而丢弃其他商家的有效报价；
- 不自动无限重试写操作。
