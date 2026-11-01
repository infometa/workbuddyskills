# 促销域 — 运营总览契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-activity.md`
> 首页汇总与拼团统计两组只读汇总能力。状态标记：✅ 已开放；⛔ 未开放。
> 能力索引（前缀 `ops.promotion.`）：查询 home.summary · groupon.stats · groupon.stats-batch
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。

---

## ✅ 首页营销活动汇总 — `ops.promotion.home.summary`

- 无入参

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| mjCouponActiveCount / discountCouponActiveCount / shippingCouponActiveCount | 进行中的满减券 / 折扣券 / 运费券数 |
| discountActiveCount / discountRateActiveCount / nItemPriceActiveCount / giftActivityActiveCount | 进行中的满减 / 满折 / N件Y元 / 赠品活动数 |
| flashSaleActiveCount / directDownActiveCount / presellActiveCount | 进行中的秒杀 / 直降 / 预售数 |

- 全部为整数计数；只统计 IN_PROGRESS 状态。
- 这些字段是进行中活动数量，不是促销工具启用/停用开关，也不是账号创建权限。数量为0或大于0均不能证明工具是否启用；用户问开关/创建权限时说明当前索引未提供对应查询，不用本能力代答。

首页券项不含兑换券DH_COUPON，三个券计数之和不是所有券总数。discountActiveCount为MYJ/MJJ/DNJ，discountRateActiveCount为MYZ/MJZ/DNZ，giftActivityActiveCount为MYG/MJG/MG；分组缺少某subCode补0是group by无记录语义，不等同于查询失败或统计缺失。

### 调用示例

```json
{"capability":"ops.promotion.home.summary","input":{},"summary":"查看当前进行中的各类营销活动数量"}
```

---

## ✅ 拼团活动统计 — `ops.promotion.groupon.stats`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionId | String | ✅ | 拼团活动 ID |

### 出参（原始数据）

> ⚠️ 该能力在后端挂了**两条等价路径**（`/{promotionId}/stats` 与 `/{promotionId}/statistics`），同一个处理逻辑，能力登记的 `stats` 即 statistics，无需区分。

| 字段 | 说明 |
|------|------|
| promotionId | 拼团活动 ID |
| formalGroupCount | 正式团总数 |
| groupingCount | 进行中的团数 |
| successGroupCount | 成团数 |
| failedGroupCount | 失败关闭的团数 |
| historicallyConfirmedMemberCount | 历史支付确认的团员人次 |

### 调用示例

```json
{"capability":"ops.promotion.groupon.stats","input":{"promotionId":"4100000000000000001"},"summary":"查看拼团活动的成团情况"}
```

---

## ✅ 拼团统计批量 — `ops.promotion.groupon.stats-batch`

- 列表页批量刷新

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionIds | String[] | ✅ | 拼团活动 ID 列表 |

### 出参（数组，原始数据）

- 每项结构同单活动统计。

### 调用示例

```json
{"capability":"ops.promotion.groupon.stats-batch","input":{"promotionIds":["4100000000000000001","4100000000000000002"]},"summary":"批量查看拼团活动成团情况"}
```

---

## ⛔ 未开放（本模块）

| 能力 | 原因 |
|------|------|
| 促销工具启用/停用开关及创建权限查询 | 当前能力索引未提供对应读取能力；活动数量不替代配置或权限证据 |
| 拼团事件重放（outbox replay）/ 发件箱健康检查 | 消息运维面操作，不属运营开放能力 |
