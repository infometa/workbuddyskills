# 商品域 — 商品状态与门店分配写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-status.md`；检索与单笔事实读取（搜索/详情/SKU 行）先读 `spu-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：spu.on-shelf 上架 · spu.off-shelf 下架 · spu.hide 隐藏 · spu.unhide 取消隐藏 · spu.recommend 推荐开关 · spu.batch-on-shelf 批量上架 🔴 · spu.batch-off-shelf 批量下架 🔴 · spu.batch-hide 批量隐藏 🔴 · spu.batch-unhide 批量取消隐藏 🔴 · spu.batch-update 批量改价 🔴 · spu.delete 删除商品 ⛔已摘除（后端废弃，改用 hide/unhide） · spu.batch-delete 批量删除商品 🔴 · spu.assign-stores 分配门店 · spu.batch-assign-store 批量分配门店 · spu.store-stock 分门店库存

---

## ✅ 上架 — ops.product.spu.on-shelf

- **语义**：上架 = 活跃 SKU 全部置 ENABLED（可售）；SPU 可售性 = 任一活跃 SKU ENABLED
- **前置条件**（服务端强制）：非草稿；未隐藏（隐藏商品先 `unhide`，违反返回商品状态无效类业务错误）
- **流程纪律**：执行前读详情/SKU 行核对现态；执行后回读确认
- **注意**：上下架≠取消隐藏；上架 ≠ C 端可售（还需门店上架 + 库存）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |

### 出参（原始返回）

`data` 为 Void（null）。

### 调用示例

```json
{"capability":"ops.product.spu.on-shelf","input":{"spuId":"2058365707555589633"},"summary":"上架指定的研学商品"}
```

---

## ✅ 下架 — ops.product.spu.off-shelf

- **语义**：下架 = 活跃 SKU 全部置 DISABLED（禁售）
- **前置条件**（服务端强制）：非草稿；未隐藏
- **流程纪律**：执行前读详情/SKU 行核对现态；执行后回读确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |

### 出参（原始返回）

`data` 为 Void（null）。

### 调用示例

```json
{"capability":"ops.product.spu.off-shelf","input":{"spuId":"2058365707555589633"},"summary":"下架指定的研学商品"}
```

---

## ✅ 隐藏 — ops.product.spu.hide

- **语义**：隐藏 = C 端不展示但不删除。hide 前置（服务端强制）：非草稿，且**当前未隐藏**（对已隐藏商品重复 hide 会失败）
- **流程纪律**：执行前读详情核对现态（已是目标状态时无需执行）；执行后回读确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |

### 出参（原始返回）

`data` 为 Void（null）。

### 调用示例

```json
{"capability":"ops.product.spu.hide","input":{"spuId":"2058365707555589633"},"summary":"隐藏指定商品"}
```

---

## ✅ 取消隐藏 — ops.product.spu.unhide

- **语义**：恢复 C 端展示
- **流程纪律**：执行前读详情核对现态；执行后回读确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |

### 出参（原始返回）

`data` 为 Void（null）。

### 调用示例

```json
{"capability":"ops.product.spu.unhide","input":{"spuId":"2058365707555589633"},"summary":"取消隐藏指定商品"}
```

---

## ✅ 推荐开关（toggle） — ops.product.spu.recommend

- **语义**：**toggle**——每次调用在推荐/取消推荐之间切换。执行前先读现态（搜索结果 `isRecommended`），执行后回读确认目标状态；因 toggle 语义，超时后**禁止盲目重试**（可能反转结果）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |

### 出参（原始返回）

`data` 为 Void（null）。用 `ops.product.spu.search`（keyword=商品名）回读 `isRecommended` 确认。

### 调用示例

```json
{"capability":"ops.product.spu.recommend","input":{"spuId":"2058365707555589633"},"summary":"推荐指定商品"}
```

---

## ✅ 批量上架 — ops.product.spu.batch-on-shelf

- 🔴 商业影响档位；批量影响面大（≤200 条），执行前向用户复述对象清单
- **语义**：同单条上架；前置条件（非草稿、未隐藏等）由服务端逐条校验，**部分失败可能发生**——结果原样返回（`SpuBatchUpdateResultVO`，含成功/失败明细），逐条报告给用户

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | SPU 业务ID列表，≤200 项（十进制字符串） |

### 出参（原始返回）

`data` 为批量结果对象（成功数/失败明细），逐条核对并向用户报告，不把 HTTP 成功当全部业务成功。

### 调用示例

```json
{"capability":"ops.product.spu.batch-on-shelf","input":{"ids":["2058365707555589633","2058365707555589634"]},"summary":"批量上架两个研学商品"}
```

---

## ✅ 批量下架 — ops.product.spu.batch-off-shelf

- 🔴 商业影响档位；批量影响面大（≤200 条），执行前向用户复述对象清单
- **语义**：同单条下架；服务端逐条校验，部分失败可能发生，结果含 `failures[]` 逐条失败明细
- ⚠️ **字段名差异**：本能力用 **`spuIds`**（后端线协议命名；batch-on-shelf/batch-hide/batch-unhide 用 `ids`）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuIds | String[] | ✅ | SPU 业务ID列表，≤200 项（十进制字符串） |

### 出参（原始返回）

`data` 为批量结果对象（`SpuBatchUpdateResultVO`：成功/失败计数 + `failures[]` 逐条失败明细），逐条核对并向用户报告。

### 调用示例

```json
{"capability":"ops.product.spu.batch-off-shelf","input":{"spuIds":["2058365707555589633"]},"summary":"批量下架指定商品"}
```

---

## ✅ 批量隐藏 — ops.product.spu.batch-hide

- 🔴 商业影响档位；批量影响面大（≤200 条），执行前向用户复述对象清单
- **语义**：同单条隐藏；服务端逐条校验（非草稿且当前未隐藏），部分失败可能发生，结果含失败明细

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | SPU 业务ID列表，≤200 项（十进制字符串） |

### 出参（原始返回）

`data` 为批量结果对象（`SpuBatchUpdateResultVO`：成功/失败计数 + `failures[]` 逐条失败明细）。

### 调用示例

```json
{"capability":"ops.product.spu.batch-hide","input":{"ids":["2058365707555589633"]},"summary":"批量隐藏指定商品"}
```

---

## ✅ 批量取消隐藏 — ops.product.spu.batch-unhide

- 🔴 商业影响档位；批量影响面大（≤200 条），执行前向用户复述对象清单
- **语义**：同单条取消隐藏；服务端逐条校验，部分失败可能发生，结果含失败明细

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | SPU 业务ID列表，≤200 项（十进制字符串） |

### 出参（原始返回）

`data` 为批量结果对象（`SpuBatchUpdateResultVO`：成功/失败计数 + `failures[]` 逐条失败明细）。

### 调用示例

```json
{"capability":"ops.product.spu.batch-unhide","input":{"ids":["2058365707555589633"]},"summary":"批量取消隐藏指定商品"}
```

---

## ✅ 批量改价 — ops.product.spu.batch-update

- 🔴 商业影响档位；批量改价执行前必须用户确认价格与对象清单
- **⚠️ 抹平警示**：会把每个 SPU 的**全部活跃 SKU 统一改为该价格**并覆盖 SPU 顶层价格——多规格商品（各规格不同价）慎用，改前向用户确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | SPU 业务ID列表，≤200 项 |
| updates | Array | ✅ | 修改项列表：`{field, value}`；**field 仅允许 `price`**（元字符串如 "99.00"；状态批量操作请用 batch-on/off-shelf 等） |

### 出参（原始返回）

`data` 为批量结果对象（成功/失败明细）。

### 调用示例

```json
{"capability":"ops.product.spu.batch-update","input":{"ids":["2058365707555589633"],"updates":[{"field":"price","value":"99.00"}]},"summary":"批量调整商品价格为99元"}
```

---

## ⛔ 删除商品（单体）— ops.product.spu.delete（已摘除）

- **⛔ 已摘除（2026-09-17 后端废弃，TAPD-1170082580164030478）**：能力目录已移除该 capability，调用得到 CAPABILITY_NOT_FOUND，**不要尝试**。后端 `SpuController` 已 `@Deprecated`，`deleteSingle` 恒抛「商品删除功能已废弃，请使用隐藏/取消隐藏」——四类商品归档已统一收敛为 `spu.hide`/`spu.unhide`。需要"删除"效果时引导用户使用隐藏（hide），不要绕行
- 🔴 批量删除（`ops.product.spu.batch-delete`）**未废弃**，仍开放——见下一锚点

---

## ✅ 批量删除商品 — ops.product.spu.batch-delete

- 🔴 不可逆档位（逻辑删除不可恢复），执行前必须向用户确认完整对象清单（单条删除也用本能力传单元素）
- **前置（服务端强制）**：仅**草稿或已隐藏**状态可删除；在架商品需先下架并隐藏，否则逐条失败

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | SPU 业务ID列表，≤200 项 |

### 出参（原始返回）

`data` 为批量结果对象（`SpuBatchUpdateResultVO`：成功/失败计数 + `failures[]` 逐条失败明细）。

### 调用示例

```json
{"capability":"ops.product.spu.batch-delete","input":{"ids":["2058365707555589633"]},"summary":"批量删除已确认的商品"}
```

---

## ✅ 分配门店 — ops.product.spu.assign-stores

- **语义**：把 SPU 上架到指定门店（生成门店商品记录）；分配后门店级上下架状态由门店商品能力管理（`store-product-action.md`，已开放）。`source` 字段不开放（运营端不声明导购来源）
- 执行前确认目标门店清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |
| storeIds | String[] | ✅ | 目标门店ID列表，≤100 项 |

### 出参（原始返回）

`data` 为分配结果对象：`AssignStoresResultVO`（含逐门店结果）。

### 调用示例

```json
{"capability":"ops.product.spu.assign-stores","input":{"spuId":"2058365707555589633","storeIds":["6000012345678901234"]},"summary":"将商品上架到指定门店"}
```

---

## ✅ 批量分配门店 — ops.product.spu.batch-assign-store

- **语义**：多 SPU 批量分配到目标门店（传 SPU ID 列表；门店商品侧另有 `store-product.batch-assign-store` 传门店商品 ID，两者区分）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | SPU 业务ID列表，≤200 项 |
| storeIds | String[] | ✅ | 目标门店ID列表，≤100 项 |

### 出参（原始返回）

`data` 为 `SpuBatchUpdateResultVO`（计数 + `failures[]` 逐条失败明细）。

### 调用示例

```json
{"capability":"ops.product.spu.batch-assign-store","input":{"ids":["2058365707555589633"],"storeIds":["6000012345678901234"]},"summary":"批量分配商品到门店"}
```

---

## ✅ 分门店库存保存 — ops.product.spu.store-stock

- **语义**：按门店维度设置该 SPU 的库存分配（门店预留）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |
| storeStocks | Array | ✅ | `[{storeId: 门店ID, stock: 库存数量≥0}]` |

### 出参（原始返回）

`data` 为 Void（null）。

### 调用示例

```json
{"capability":"ops.product.spu.store-stock","input":{"spuId":"2058365707555589633","storeStocks":[{"storeId":"6000012345678901234","stock":100}]},"summary":"设置商品在指定门店的库存分配"}
```
