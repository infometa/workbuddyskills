# 会员子域 — 积分商城流程（商品维护/商城开关/兑换订单发货）

> 对应契约：`apis/member/points-goods-query.md` / `apis/member/points-goods-action.md`（积分商品）、`apis/member/points-mall-query.md` / `apis/member/points-mall-action.md`（商城配置）、`apis/member/points-exchange-order-query.md` / `apis/member/points-exchange-order-action.md`（兑换订单）；概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；写操作共同纪律（风险档位/超时不重试）见入口 Skill 护栏段。

## 积分商城运营

**场景**：积分商品的上架与维护、商城开关。

### 操作步骤

1. **看列表**：`ops.member.points-goods.search`（⚠️ 分页参数为 `pageNo`/`pageSize`，不是 pageNum）——按名称/编码/状态/门店筛选；返回含 isHidden（关联 SPU 派生）、库存与已兑
2. **看详情**：`points-goods.detail`（含 items 子项与 allowedLevels）
3. **创建** 🔴：`points-goods.create`
   - 实物商品：items[{itemType:1, spuId, skuId, itemName, redeemPoints, stock, storeId?}]——spuId/skuId 来自商品域
   - 优惠券商品：items[{itemType:2, couponTemplateId, itemName, redeemPoints, stock}]（券模板来自促销域）
   - ⚠️ 一次请求按门店+商品分组可能裂变多条积分商品，返回**首条** ID；用 search 按名称回查全部新建记录
   - **超时禁盲目重试**：先按 goodsName 用 search 回查是否已创建（可能已裂变多条），确认未创建再重试
   - redeemMode=2 时各 item redeemAmount 必填；validType=2 时 validStartTime/validEndTime 必填（ISO-8601，如 2026-10-01T00:00:00）
4. **编辑** 🔴：`points-goods.update`——先读 detail；**仅修改用户要求变更的字段**（积分价 redeemPoints/redeemAmount、库存、可兑等级 allowedLevels、有效期均须用户确认），其余字段以 detail 回读值原样回传（⚠️ `itemImage` 例外：detail 出参为 60 分钟时效签名 URL 而 update 落库不清洗，回传须剥离 `?` 后参数只留裸 URL）；同源 items 原地更新（匹配 skuId/couponTemplateId 或 spuId+storeId），异源 items 自动拆分建新商品（响应含 spawnedIds，如实转达"额外创建了 N 个新积分商品"）；**不允许清空全部同源 SKU**
5. **上下架**：`points-goods.on-shelf` / `off-shelf`（单条）；`batch-on-shelf` / `batch-off-shelf`（批量 ids）
6. **删除** 🔴：`points-goods.delete` / `batch-delete`（不可逆）；单 SKU 移除用 `delete-item`（末个 SKU 后端拒绝）
7. **商城开关**：`points-mall.config`（读）→ `points-mall.config-save`（enabled 0/1 + bgImageUrl 可空）

### 业务规则
- 同门店同商品（goodsCode）不允许重复上架。
- 商品域 SPU 隐藏会派生积分商品"已隐藏"状态（不落库实时查），如实向用户解释。
- allowedLevels 为等级编码（V0/V1...）列表，来自等级配置。

## 兑换订单发货

**场景**：实物兑换订单发货。

### 操作步骤

1. **找待发货订单**：`ops.member.points-exchange-order.search`（⚠️ 分页参数 `pageNo`；status=1 待发货）→ 取 `records[].id`
2. **看详情**：`points-exchange-order.detail`（收货人/地址/物流信息）
3. **发货** 🟡：`points-exchange-order.ship`——logisticsNo 必填、logisticsCompany 建议提供；物流单号必须由用户提供，禁止编造；不可逆（误发需人工客服补救，无系统撤回），但受状态机保护（仅待发货可发）且限单订单
4. **核验**：回读 detail（status=2 已发货 + 物流信息）

### 业务规则
- 仅待发货（status=1）可发货；发货不可逆。
- 订单状态：1 待发货 / 2 已发货 / 3 已完成 / 4 已取消。
