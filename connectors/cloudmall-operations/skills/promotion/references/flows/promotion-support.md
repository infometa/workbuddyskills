# 促销域 — 运营流程：活动配套资源（赠品库 / 促销日历 / 活动库存）

> 赠品 SKU 池维护、促销日历与主题分组、活动库存正增量。
> 概念知识见 `references/domains/promotion-concepts.md`，状态与枚举见 `references/domains/promotion-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> 对应契约：`gift-pool-query.md` / `gift-pool-action.md`、`calendar-query.md` / `calendar-action.md`、`stock-query.md` / `stock-action.md`。
>
> **能力标识约定**：本文为行文简洁使用模块短名（如 `gift-pool.batch-add`），
> 实际调用 capability 必须使用全限定 id = `ops.promotion.` + 短名（即 `ops.promotion.gift-pool.batch-add`），
> 禁止把短名直接作为 capability 传入。

---

## 赠品库管理

**场景**：维护赠品 SKU 池（满元赠/满件赠/买赠活动的赠品来源）。

1. 查询 `gift-pool.search`（keyword 精确匹配 SPU/SKU ID）；SPU 展开 `gift-pool.sku-details`（逐 SKU 移除用 skuDetails[].giftPoolId——列表行 giftPoolId 仅对应第一条 SKU）。
2. 添加 `gift-pool.batch-add`（≤100 项，items 只含 spuId+skuId；已存在的跳过计入失败明细）。
3. 移除前查引用：`gift-pool.reference-count`（spuIds 或 skuIds 至少传其一，均不传返回空 Map；返回计数是部分状态下的关联商品行数，0不能排除暂停活动或草稿引用；结合活动查询核对影响——**服务端不校验引用数**）。
4. 移除：单 SKU 记录 `gift-pool.remove`（giftPoolId）/ 按 SPU 整组 `gift-pool.remove-by-spu`。

### 异常处置
- in_use（有关联活动）→ 引用数 > 0，向用户说明关联商品行计数与覆盖范围，不冒充去重活动数，**确认后才执行**（服务端不会拦截，删除后进行中赠品活动将失去该赠品来源）。

---

## 促销日历

**场景**：按时间轴总览活动与主题分组。

1. 查日历 `calendar.view`（rangeStart/rangeEnd 毫秒时间戳必填；返回活动、主题、未归属活动、时间冲突、汇总）。
2. 主题管理：create（selectionMode=EXPLICIT 时必传 promotionIds，=ALL_ELIGIBLE传[]按时间覆盖纳入、不筛状态/类型；优先完整预览后用EXPLICIT）/ update（removedPromotionIds 必填空数组=不移出）/ workcopy（**原子保存**名称/排期/成员增删同事务，added 与 removed 不得重叠）/ delete。
3. 活动归组：assign-activity（加入或跨主题移动）/ unassign-activity；放置前可用 `theme.eligible-targets` 查可放置性与原因码、`theme.eligible-activities` 查周期内候选活动。
4. **主题写操作先读 `theme.detail`** 取当前 revision 与完整成员（含窗口外成员及空主题——calendar 视图仅含窗口内活动，编辑回填以 detail 为准）；assign/workcopy 携带 sourceThemeRevisions（源主题乐观锁，未归属传 `{}`）。**create 例外**：expectedRevision 固定传 0、无源主题时 sourceThemeRevisions 传 `{}`，无需先读 detail。

### 参数来源

| 参数 | 来源 |
|------|------|
| themeId | 日历 themes[].themeId / 创建主题响应 |
| expectedRevision / sourceThemeRevisions | `theme.detail` 的 revision（每次写操作后版本号变化，需重新读取） |
| promotionId | 活动查询 |
| 时间范围 | 毫秒时间戳，用户提供或按自然周期换算 |

---

## 活动库存

**场景**：单品层限量活动（周期购等）的运行态库存。

1. 查询 `stock.items`（分页；goodsId 可选，同时匹配活动 SPU/SKU ID）。
2. 增库存 `stock.increase`：batchOperationId（幂等批次号 ≤64 字符）+ items 1..200 项（skuId + delta 正整数）；仅进行中、支持增库存、有限库存池的活动可操作。
3. 整批原子提交，任一明细失败全回滚；**超时结果不确定时用同一 batchOperationId + 相同参数重试**（幂等），不可换批次号掩盖未知结果。

### 异常处置
- 不限量活动（UNLIMITED）不支持增库存。
- `STOCK_INCREASE_IDEMPOTENCY_CONFLICT`：同批次号参数不一致，先查库存项确认上次结果。

库存回读中的0可能是Redis查询降级，不能据此断言售罄或增库失败；空/null补查，同源反复0仍未知时按stock-action如实说明，保持原幂等批次。
