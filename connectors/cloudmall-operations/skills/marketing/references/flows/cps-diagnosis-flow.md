# 营销域 — 运营流程：CPS 分销佣金缺失排查（客诉诊断）

> 概念知识见 `references/domains/cps-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：交易域订单查询（跨域）+ `cps-distributor-query.md` / `cps-bind-relation`（绑定关系）/ `cps-rule.get` / `cps-goods-promotion-query.md` / `cps-activity-query.md` / `cps-settle-query.md` / `cps-settle-action.md`（manual-settle）/ `cps-commission-action.md`（trigger-replay）。

---

## CPS 分销佣金缺失排查（客诉诊断）

**场景**：分销员反馈「已绑定用户通过我的推广链接下单，但没算佣金 / 分销后台查不到这笔订单」类客诉。典型输入三要素：**订单号 + 分销员手机号 + 下单用户手机号**（均由用户提供，缺一项先索取）。全流程默认**只读排查**，先定位断点环节，再决定处置；唯一可能用到的写操作是 manual-settle（见处置分支）。

> 跨域能力（交易域/会员域）使用全限定 id 调用，并遵守对应域技能纪律（订单搜索不得向用户复述手机号等个人信息）。

### 诊断决策树

```
① 定位订单（ops.trade.order.detail，orderNo）
   → 取 items[].spuId、下单时间、支付状态；存在 subOrders 时先定位实际子单再取商品行
② 分销归属判定（ops.trade.order.search，noKeyword=订单号 + cpsOnly=true）
   ├─ 未命中 → 订单未被 CPS 归因（与"分销后台查不到"互证）→ 转 ③④⑤ 找归因失败原因
   └─ 命中（再用 cpsUid=分销员 uid 复核归属人）→ 归因成功，问题在结算侧 → 转 ⑥
③ 分佣主体核验（cps-distributor.search，phone=分销员手机号）
   → status=1（禁用）或员工类型 employeeStatus=1 → 分佣资格已停，即为根因
④ 绑定关系核验（cps-bind-relation.search，phone=下单用户手机号）
   → 无记录 → 该账号未与任何分销员绑定，即为根因
   → valid=false 或 expireTime 早于下单时间 → 绑定已失效/过期（动态绑定受跟随有效期约束），即为根因
   → 记录的 cpsUid/分销员 ≠ 被反馈的分销员 → 用户实际绑定的是其他分销员，即为根因
⑤ 规则与适用范围核验（逐项排除）
   a. cps-rule.get → followUpValiditySeconds（动态绑定跟随有效期，0=永不过期；未保存过返回 null）；
      selfPurchaseCommission（分销员自购）/ employeeOrderCommission（员工下单）——下单人即分销员本人/员工时核对开关
   b. cps-goods-promotion.detail（spuId 来自①）→ promotionStatus=1（已停止）→ 商品不在分销推广范围，即为根因
   c. cps-activity.search（status=running，时间窗覆盖下单时刻）→ detail 核对 configInfo 四维度
      （商品/门店/用户/分销员适用范围）是否覆盖这笔订单；无 running 活动 → 无生效活动即为根因
⑥ 结算与流水核验（归因成功路径）
   a. cps-settle.search（activityId + cpsUid）或 cps-settle.global-search（phone=分销员手机号）
   b. cps-distributor.deal-records → 流水凭证号 voucherNum 即订单号，逐页核对
   → 有归因、无预估结算、无流水 → 结算数据异常，走处置分支一
```

### 处置分支

- **分支一（归因成功但预估结算缺失）**：确认覆盖该订单的活动 activityId 后，向用户复述「活动名 + 订单号」取得确认 → `cps-settle.manual-settle`（🔴 资金面运维动作）→ 用 `cps-settle.search` 复查该分销员结算明细。**注意 manual-settle 对不存在的订单静默返回成功——调用成功不能作为修复证据，必须以复查结果为准**。若预估结算存在但**分佣计算/流水缺失**（⑥ b 无流水），可改走 `cps.order.trigger-replay`（🔴 按订单当前状态触发分佣计算/结算确认的补偿重放，返回订单状态/执行动作/是否成功），执行后仍以 `cps-distributor.deal-records` 复查流水为准。
- **分支二（未归因，②未命中）**：订单维度的归因明细（推广链接点击链路、chanId 落库记录）**后端无查询端点**，无法直接查证归因失败根因；可用订单详情的 `chanId` 是否为空做间接推断（chanId 为空 → 推广链接渠道参数未携带/丢失）。超出能力范围的部分如实告知用户需人工核查 C 端推广链路，不编造结论。
- **分支三（规则性根因：绑定过期/商品停止推广/活动未覆盖/分销员禁用）**：只读排查结论向用户说明即可；**不得顺手执行任何修复写操作**（重新启用商品推广、调整活动范围等），用户明确要求时按对应流程另行确认执行。

### 参数来源

| 参数 | 来源 |
|------|------|
| orderNo / 分销员手机号 / 下单用户手机号 | 用户提供（缺一项先索取，禁止猜测） |
| cpsUid（分销员） | cps-distributor.search 出参 `uid` |
| spuId | 订单详情 `items[].spuId` |
| activityId | cps-activity.search 出参（16 位业务 ID） |
| chanId | 订单详情/列表出参（推广渠道追踪标识，间接证据） |

### 纪律与陷阱

- 三套结算状态不可混用：订单侧 `cpsSettleStatus`、CPS 活动侧字符串（'0'/unsettled/settled）、明细侧整数（0/1）。
- cps-bind-relation 出参 `expireTime` 为 null 表示永不过期，不是"缺失数据"。
- cps-settle 出参 `phone` 为未脱敏明文——展示时自行打码；订单/会员查询同样不得向用户复述手机号。
- ① 中订单未支付/已关闭 → 佣金本就不应产生，直接说明，无需继续排查。

---
