# 促销域 — 赠品库写操作契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-support.md`
> 移除前核对引用与关联影响；服务端不校验引用数，引用>0也会删除。计数0也不能排除暂停活动或草稿引用，不能据此保证安全。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：写 gift-pool.batch-add · gift-pool.remove 🔴 · gift-pool.remove-by-spu 🔴
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：移除前必查 `gift-pool-query.md` 的 reference-count（部分状态的关联商品行数，0不证明无引用；核对关联影响并按用户确认执行）。

---

## ✅ 批量添加赠品 — `ops.promotion.gift-pool.batch-add`

- 🟡 可逆写（可移除）
- **说明**：先经商品事实核对真实SKU及其SPU归属，服务端不替代这一步；items **只含 spuId + skuId**（库存取商品实物库存，不在此设置）；已存在的 SKU 跳过并计入失败明细。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | Array | ✅ | 1..100 项 |
| items[].spuId | String | ✅ | SPU ID |
| items[].skuId | String | ✅ | SKU ID |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| successCount / failureCount | 成功 / 失败数量 |
| failures | 失败明细数组（含原因） |

### 调用示例

```json
{"capability":"ops.promotion.gift-pool.batch-add","input":{"items":[{"spuId":"2058365707555589633","skuId":"2158365707555589633"}]},"summary":"把研学水杯SKU加入赠品库"}
```

---

## ✅ 移除赠品（单记录） — `ops.promotion.gift-pool.remove`

- 🔴 影响关联赠品活动
- **前置**：**服务端不校验引用数**——引用 >0（in_use）也会被直接删除（进行中的赠品活动将失去该赠品来源）。reference-count为0仍可能存在口径外引用；执行前查计数及相关活动，说明实际影响并与用户确认。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| giftPoolId | String | ✅ | 赠品池记录 ID（SKU 维度，来自列表/明细） |

### 调用示例

```json
{"capability":"ops.promotion.gift-pool.remove","input":{"giftPoolId":"5000000000000000001"},"summary":"移除单个赠品SKU记录"}
```

---

## ✅ 按 SPU 移除赠品 — `ops.promotion.gift-pool.remove-by-spu`

- 🔴 影响面更大（该 SPU 下全部 SKU 一次性移除；服务端同样不校验引用数）
- **前置**：先查引用数并与用户确认 SPU 名称与 SKU 数量。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU ID |

### 调用示例

```json
{"capability":"ops.promotion.gift-pool.remove-by-spu","input":{"spuId":"2058365707555589633"},"summary":"把该商品全部SKU移出赠品库"}
```
