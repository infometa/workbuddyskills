# 会员域 — 积分商品写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points-mall.md`；积分商品现值读取（分页/详情/回填来源）先读 `points-goods-query.md`，商城开关见 `points-mall-action.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。⚠️ 本模块分页查询参数为 `pageNo`/`pageSize`（见 query 文件）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.points-goods.create 创建积分商品 🔴 · member.points-goods.update 编辑积分商品 🔴 · member.points-goods.on-shelf 上架 · member.points-goods.off-shelf 下架 · member.points-goods.batch-on-shelf 批量上架 🔴 · member.points-goods.batch-off-shelf 批量下架 🔴 · member.points-goods.delete 删除 🔴 · member.points-goods.batch-delete 批量删除 🔴 · member.points-goods.delete-item 删除单 SKU 子项

---

## ✅ 创建积分商品 — ops.member.points-goods.create

- 🔴 商业影响——按门店+商品分组可能**裂变创建多条**积分商品，返回**首条** ID——创建后用 search 按名称回查全部新建记录并如实告知用户；**超时禁盲目重试**（可能已裂变多条），先按 goodsName 回查确认未创建再重试；积分价/库存/可兑等级数值必须用户给值

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| goodsName | String | ✅ | 商品名称（实物类创建后会被 SPU 名称覆盖展示） |
| goodsType | Integer | ✅ | 1=实物 / 2=优惠券（**服务端不校验值域**——非 2 的任意值一律按实物分支处理，须严格传 1/2） |
| redeemMode | Integer | ✅ | 1=纯积分 / 2=积分+现金（2 时各 item redeemAmount 必填；值域同样无服务端校验） |
| redeemDesc | String | — | 兑换说明 |
| items | Array | ✅ | SKU 子项（1~200 个） |
| validType | Integer | ✅ | 1=长期 / 2=时间段（值域无服务端校验） |
| validStartTime / validEndTime | String | 条件 | validType=2 必填（**ISO-8601 含 T**，如 `2026-10-01T00:00:00`） |
| allowedLevels | String[] | ✅ | 可兑等级编码（非空，如 ["V0","V1"]，来自等级配置） |
| storeId | String | — | 关联门店（实物商品；item 级 storeId 优先） |

`items[]` 子结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| itemType | Integer | ✅ | 1=实物 SKU / 2=优惠券；⚠️ **create 时 items 类型须与顶层 goodsType 一致，不支持混排**（goodsType=1 时全部 item 都要求 spuId，含 itemType=2 的混排项会报「商品SPU不能为空」；item.itemType 仅在 update 拆分路径生效） |
| spuId | String | 条件 | 实物必填（商品域 SPU） |
| skuId | String | — | 实物规格（商品域 SKU） |
| couponTemplateId | String | 条件 | 优惠券必填（促销域券模板） |
| itemName / itemImage / itemSpec | String | — | 子项名称/图片/规格 |
| originalPrice | Number | — | 原价（元） |
| redeemPoints | Integer | ✅ | 兑换积分（>0） |
| redeemAmount | Number | 条件 | 加购现金（元）；redeemMode=2 必填 |
| purchaseLimit / redeemLimitPerPerson / redeemLimitPerDay | Integer | — | 限购/每人限兑/每日限兑 |
| stock | Integer | ✅ | 库存（**服务端不校验非负**，务必传 ≥0 的值） |
| storeId | String | — | 子项级门店（覆盖顶层） |

### 出参（原始返回）

`data` 为首条积分商品 ID（Long→string）。

### 调用示例

```json
{"capability":"ops.member.points-goods.create","input":{"goodsName":"积分兑换保温杯","goodsType":1,"redeemMode":1,"validType":1,"allowedLevels":["V0","V1"],"storeId":"6000012345678901234","items":[{"itemType":1,"spuId":"2058365707555589633","skuId":"9000012345678901234","itemName":"保温杯-蓝色","redeemPoints":500,"stock":100,"storeId":"6000012345678901234"}]},"summary":"创建500积分兑换保温杯"}
```

---

## ✅ 编辑积分商品 — ops.member.points-goods.update

- 🔴 商业影响——积分价（redeemPoints/redeemAmount）、库存、可兑等级（allowedLevels）、有效期均须用户确认，**仅修改用户要求变更的字段，其余以 detail 回读值原样回传**；⚠️ **图片字段例外**：detail 返回的 `items[].itemImage` 为 60 分钟时效的 COS 预签名 URL（`mainImage` 为其派生展示字段），而 update 落库**不做签名清洗**（与 points-mall config-save 不同）——原样回传会把带时效签名的 URL 写入 DB，签名过期后图片失效。回传 `itemImage` 时须**剥离 `?` 及之后的查询参数**只留裸 URL（或仅在用户明确换图时传新值）；同源/异源拆分语义：同源 items（同 skuId/couponTemplateId 或同 spuId+storeId）原地增删改；异源 items 自动**拆分创建新积分商品**（响应含 spawnedIds）；门店归属不可改（request.storeId 被忽略）

### 入参

同创建（`id` 必填；不传 spuId 的顶层字段）。编辑前先 `points-goods.detail` 读回 items 原样回传要保留的子项（保留其 skuId/couponTemplateId；`itemImage` 按上文剥离签名参数后回传），未回传的旧子项会被删除；**不允许清空全部同源 SKU**（末个保护，完全换品需删除重建）。

### 出参（原始返回）

对象：`updatedId`（原商品 ID）+ `spawnedIds[]`（拆分新建的商品 ID 列表，非空时向用户说明"额外创建了 N 个新积分商品"）。

### 调用示例

```json
{"capability":"ops.member.points-goods.update","input":{"id":"1100012345678901234","goodsName":"积分兑换保温杯","goodsType":1,"redeemMode":1,"validType":1,"allowedLevels":["V0","V1"],"items":[{"itemType":1,"spuId":"2058365707555589633","skuId":"9000012345678901234","itemName":"保温杯-蓝色","redeemPoints":600,"stock":100}]},"summary":"将保温杯兑换积分调整为600"}
```

---

## ✅ 上架 — ops.member.points-goods.on-shelf

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 积分商品 ID |

### 出参（原始返回）

`data` 为 `null`；回读 `points-goods.search` 核验 status=1。

### 调用示例

```json
{"capability":"ops.member.points-goods.on-shelf","input":{"id":"1100012345678901234"},"summary":"上架积分商品"}
```

---

## ✅ 下架 — ops.member.points-goods.off-shelf

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 积分商品 ID |

### 出参（原始返回）

`data` 为 `null`；回读核验 status=0。

### 调用示例

```json
{"capability":"ops.member.points-goods.off-shelf","input":{"id":"1100012345678901234"},"summary":"下架积分商品"}
```

---

## ✅ 批量上架 — ops.member.points-goods.batch-on-shelf

- 🔴 批量改变 C 端兑换入口可见性——ids 清单先向用户确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 积分商品 ID 列表（非空） |

### 出参（原始返回）

`data` 为 `null`；回读 `points-goods.search` 核验。

### 调用示例

```json
{"capability":"ops.member.points-goods.batch-on-shelf","input":{"ids":["1100012345678901234","1100012345678901235"]},"summary":"批量上架两个积分商品"}
```

---

## ✅ 批量下架 — ops.member.points-goods.batch-off-shelf

- 🔴 批量改变 C 端兑换入口可见性——ids 清单先向用户确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 积分商品 ID 列表 |

### 出参（原始返回）

`data` 为 `null`；回读核验。

### 调用示例

```json
{"capability":"ops.member.points-goods.batch-off-shelf","input":{"ids":["1100012345678901234","1100012345678901235"]},"summary":"批量下架两个积分商品"}
```

---

## ✅ 删除 — ops.member.points-goods.delete

- 🔴 逻辑删除不可恢复——执行前向用户复述对象清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 积分商品 ID |

### 出参（原始返回）

`data` 为 `null`；回读 `points-goods.search` 确认已移除。

### 调用示例

```json
{"capability":"ops.member.points-goods.delete","input":{"id":"1100012345678901234"},"summary":"删除一个积分商品"}
```

---

## ✅ 批量删除 — ops.member.points-goods.batch-delete

- 🔴 不可恢复——执行前向用户复述完整对象清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 积分商品 ID 列表 |

### 出参（原始返回）

`data` 为 `null`；回读确认。

### 调用示例

```json
{"capability":"ops.member.points-goods.batch-delete","input":{"ids":["1100012345678901234"]},"summary":"批量删除积分商品"}
```

---

## ✅ 删除单个 SKU 子项 — ops.member.points-goods.delete-item

- 末个 SKU 后端拒绝（保底保护，防清空商品）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| itemId | String | ✅ | 子项 ID（来自 `points-goods.detail` 的 `items[].id`） |

### 出参（原始返回）

`data` 为 `null`；回读 detail 核验。

### 调用示例

```json
{"capability":"ops.member.points-goods.delete-item","input":{"itemId":"1150012345678901234"},"summary":"删除积分商品的一个SKU子项"}
```
