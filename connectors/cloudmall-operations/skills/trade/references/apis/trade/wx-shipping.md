# 交易域 — 微信发货管理契约

> 概念知识：`references/domains/trade-concepts.md`；运营流程：`references/flows/trade-finance.md`
> 微信发货信息管理是微信小程序交易的合规要求：实物订单发货后需向微信上报发货信息。渠道自动回传开关（channel-config.wx-shipping-switch）见 `payment-action.md`。
> 所有 ID 均为十进制字符串。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 payment.wx-shipping.report 🔴

---

## ✅ 微信发货补报 — ops.trade.payment.wx-shipping.report

用途：手动向微信上报单笔支付单的发货信息（🔴）。后端获取 access_token 后调用微信发货信息管理接口上报，token 过期自动刷新重试。仅用于自动回传失败/关闭时的补报；成功不返回业务详情。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | 支付单检索/详情的支付单 ID（注意是雪花 ID，不是 payOrderNo 业务单号） |

前置与边界：

- **失败前置**：小程序未配置（获取 access_token 失败）时服务端返回 400「请检查小程序配置」——先解决小程序配置，不能重试绕过，不是网络问题。
- 该能力是**补报**通道：正常链路由渠道的微信发货回传开关自动上报（`channel-config.wx-shipping-switch` 控制）；仅在自动上报失败或需要手动补报时使用。
- 无业务详情返回：成功即受理，上报结果以微信侧为准；失败时错误信息在响应中，向用户如实转述，不盲目重试。

```json
{
  "capability": "ops.trade.payment.wx-shipping.report",
  "input": { "id": "8500000000000000001" },
  "summary": "手动补报微信发货信息"
}
```

---

## 标识边界

`id` 是支付单雪花 ID（`pay-order.detail` 的 `id` 字段），不是 `payOrderNo` 字符串业务单号——两者不能互换。补报前先读取支付单详情确认已发货事实；未发货订单没有可上报的物流信息。
