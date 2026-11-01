# 会员域 — 积分商品查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points-mall.md`；积分商品写操作（创建/编辑/上下架/删除）见 `points-goods-action.md`，商城配置见 `points-mall-query.md` / `points-mall-action.md`，兑换订单见 `points-exchange-order-query.md` / `points-exchange-order-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。⚠️ 本模块分页参数为 **`pageNo` / `pageSize`**（不是 pageNum）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.points-goods.search 积分商品分页 · member.points-goods.detail 积分商品详情

---

## ✅ 积分商品分页 — ops.member.points-goods.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNo / pageSize | Integer | — | 分页（⚠️ 参数名是 pageNo，默认 1 / 10） |
| name | String | — | 商品名称（模糊） |
| code | String | — | 商品编码（模糊；后端按门店+SPU 生成） |
| status | Integer | — | 0=下架 / 1=上架 |
| storeId | String | — | 门店 ID 筛选 |
| isHidden | Boolean | — | 关联 SPU 派生的隐藏态筛选（跨服务实时判定） |

### 出参（原始返回）

分页对象。**关键字段**：`records[].id`（→ 详情/编辑/上下架/删除路径参数）、`storeId`、`goodsCode`（检索锚点，按门店+SPU 生成）、`totalStock`/`remainingStock`/`totalRedeemed`（items 级明细如单 SKU 已兑计数 redeemedCount 不在列表——以 `detail` 的 `items[]` 为准）；**枚举字段**：`goodsType`（1=实物 2=优惠券）、`redeemMode`（1=纯积分 2=积分+现金）、`status`（0/1）、`isHidden`（Boolean，任一关联 SPU 隐藏即 true，跨服务判定失败时为 null）、`source`（ADMIN/GUIDE_PUBLISH）、`deliveryMethodList[]`（String 数组，关联 SPU 的配送方式标签）；**格式敏感字段**：`validStartTime`/`validEndTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）。

### 调用示例

```json
{"capability":"ops.member.points-goods.search","input":{"pageNo":1,"pageSize":20,"status":1},"summary":"查询上架中的积分商品"}
```

---

## ✅ 积分商品详情 — ops.member.points-goods.detail

- 编辑前必读

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 积分商品 ID |

### 出参（原始返回）

商品详情对象（含 `redeemDesc`、`allowedLevels[]`（等级编码 V0/V1...）、`items[]` 子项）。**关键字段**：`items[].id`（→ `delete-item` 路径参数）、`items[].skuId`/`couponTemplateId`（编辑同源判定锚点）、`items[].externalSkuId`（商家 SKU 编码）、`items[].redeemPoints`/`redeemAmount`/`stock`/`redeemedCount`。⚠️ **列表有值、详情恒 null 的派生字段**：`isHidden`/`source`/`deliveryMethodList`（detail 转换器不回填）——判断隐藏态/来源以 `search` 列表为准，勿以 detail 为据。

### 调用示例

```json
{"capability":"ops.member.points-goods.detail","input":{"id":"1100012345678901234"},"summary":"查询积分商品详情"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 优惠券选项列表（coupon-options） | 后端首期返回空列表，开放无意义；券模板请从促销域获取 |
| 批量移除 ES 积分商城标记（ops/remove-tags） | 运维清理面，不属运营开放能力 |
