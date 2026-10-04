# 审批流程

`kiwi_accept_agreement` 和 `kiwi_handoff` 是两个不同的高风险 action，各自需要与当时条款绑定的
持久审批。WorkBuddy 的界面确认不能替代 Kiwi 的 `approval_id`。

1. 首次调用目标 action，不携带 `approval_id`。
2. 若返回 `approval_required`，读取 `approval_id` 和候选摘要。
3. 向用户展示商家、商品/数量、总价/币种、交期、MOQ、售后、有效期、缺失信息和风险。
4. 用户明确同意当前条款后，调用 `kiwi_approve`。
5. 携批准后的 `approval_id` 重试同一 action。
6. 用户拒绝、犹豫或要求修改时，调用 `kiwi_reject` 或回到磋商，不得批准。

如果条款、报价、商家或 action 改变，旧审批失效；重新生成候选并再次确认。遇到
`authorization_denied` 或 `approval_denied` 时停止，不自动重试。
