# 促销域 — 活动库存写操作契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-support.md`
> 仅支持**正增量**增加，不支持扣减或设置绝对值。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：写 stock.increase 🔴（幂等 batchOperationId）
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：增库存前用 `stock-query.md` 的 stock.items 确认当前库存项与余量。

---

## ✅ 增加活动库存 — `ops.promotion.stock.increase`

- 🔴 商业影响（改变可售名额）
- **前置**：活动进行中、促销类型支持增库存、有限库存池（LIMITED）；不限量活动不支持。
- **幂等纪律**：`batchOperationId`（≤64字符）在租户内唯一，指纹由promotionId和按SKU排序的sku:delta构成，items顺序不影响指纹；跨活动不能复用批次号——**超时/结果不确定时用同一批次号和相同参数重试是安全的**；同批次号换参数会报 `STOCK_INCREASE_IDEMPOTENCY_CONFLICT`，禁止靠换新批次号掩盖未知执行结果。
- **原子性**：整批事务执行，任一明细失败全部回滚；数据库提交后缓存介质同步可能异步进行，稍后复查库存结果。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionId | String | ✅ | 活动 ID |
| batchOperationId | String | ✅ | 幂等批次号，≤64 字符，调用方生成（重试保持原值） |
| items | Array | ✅ | 1..200 项，**不允许重复 SKU** |
| items[].skuId | String | ✅ | SKU ID（必须属于当前活动） |
| items[].delta | Integer | ✅ | 正整数增量（**不是** increaseCount；不支持扣减/设绝对值） |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| success | 是否成功——**恒为 true**（失败路径全部经统一错误信封抛出，不存在 success=false 的返回形态） |
| errorCode | ⚠️ **恒为 null**——全中心对该字段无任何赋值点，失败错误码只出现在统一错误信封里，不要在本出参读它 |
| batchOperationId | 回显批次号 |
| idempotent | 是否幂等重放命中 |
| items | 每项：`skuId`/`delta`/`totalCount`/`availableCount`（totalCount为DB总量，availableCount查询降级可为空，也可能被底层编码成0） |

- 返回余量来自提交后查询，任务允许时可作回读，不能称为另一次独立stock.items查询。availableCount为0可能是真实售罄，也可能是Redis缺值/异常降级，非空不保证已取得真实余量；缺失/null补查stock.items。同源复查仍0且无健康信号时如实说明无法区分，不断言售罄或增库失败，不换批次再次增库。任务明确要求独立查询时仍执行。
- 出参**没有** successCount/failCount（整批原子，要么全成要么全败）。
- 常见业务错误：`STOCK_INCREASE_NOT_ALLOWED`（活动/类型不允许）、`STOCK_INCREASE_ITEM_INVALID`（明细无效）、`STOCK_INCREASE_IDEMPOTENCY_CONFLICT`（幂等冲突）。

### 调用示例

```json
{"capability":"ops.promotion.stock.increase","input":{"promotionId":"4100000000000000001","batchOperationId":"stock-inc-20260909-0001","items":[{"skuId":"2158365707555589633","delta":50}]},"summary":"给周期购活动的该SKU增加50个名额"}
```

幂等重放先于活动状态校验，活动结束后原批次同参重放也可能返回成功；这不证明活动仍进行中。重放totalCount为当前DB值，不是首次操作时的数量。
