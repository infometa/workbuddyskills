# 商品域 — 搭配查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-collocation.md`；写操作（创建/编辑/上下线/删除/海报/图片/投放重试）见 `collocation-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> 搭配 = 单店维度的商品组合营销实体（如"研学装备搭配"）：归属门店 + 搭配商品列表（含主图锚点），支持上/下线；图片上传、海报配置、投放物料均已开放（写侧见 `collocation-action.md`）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：collocation.search 搭配分页 · collocation.dashboard 搭配看板 · collocation.detail 搭配详情 · collocation.poster-config-get 海报文案查询 · collocation.launch-material 投放物料查询

---

## ✅ 搭配分页 — ops.product.collocation.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页 |
| keyword | String | — | 搭配名称关键词 |
| spuId | String | — | 包含该 SPU 的搭配 |
| publishMethod | String | — | 发布方式：`manual` / `auto`（小写） |
| status | String | — | 搭配状态筛选（**小写** `online`/`offline`） |

### 出参（原始返回）

`data.records[]` 为搭配视图；**关键字段来源**：`records[].id`（→ 各写能力的 `id`）、`records[].collocationId`（业务标识，原样透出）、`name`、`status`、`storeId`。

> **collocationId → 内部 id 解析配方**（用户只给 collocationId 时必读）：search 入参**不支持**按 collocationId 筛选。定位路径：`{"pageNum":1,"pageSize":50}` 起翻页遍历 `records[]`，按 `records[].collocationId` 精确匹配（搭配总量有限，通常 1-2 页内定位），取该条的 `records[].id` 作为后续 detail/写能力的 `id`。**不要**把 collocationId 直接传给 detail/写能力（报「搭配不存在」），也**不要**因「search 没有 collocationId 入参」而停滞——翻页遍历就是官方路径。

### 调用示例

```json
{"capability":"ops.product.collocation.search","input":{"pageNum":1,"pageSize":20,"keyword":"研学"},"summary":"查询研学相关搭配"}
```

---

## ✅ 搭配看板 — ops.product.collocation.dashboard

- **语义**：看板指标 + 环比值

**出参字段**：实时指标 `onlineCount`（已上线搭配数）、`manualPublishCount`（手动发布数）、`autoPublishCount`（自动发布数）；区间指标 `exposurePv`/`exposureUv`（曝光）、`activeCollocationCount`（动销搭配数）、`orderAmount`（成交金额，元）、`orderCount`（订单量）及各自 `*Ratio` 环比（如 `exposurePvRatio`）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timeRange | String | ✅ | 时间范围：`LAST_7_DAYS` / `LAST_30_DAYS` |

### 调用示例

```json
{"capability":"ops.product.collocation.dashboard","input":{"timeRange":"LAST_7_DAYS"},"summary":"查看近7天搭配数据看板"}
```

---

## ✅ 搭配详情 — ops.product.collocation.detail

- **语义**：编辑前先读详情（编辑为全量覆盖语义）
- **ID 口径**：入参 `id` 是**内部主键**（来自 collocation.search 的 `records[].id`，短数字如 `"69"`）；用户语境的「搭配（套餐）ID」是业务标识 `collocationId`（长雪花 ID，如 `"2108105925562068994"`）——**两者不同**。用户给搭配 ID 时先用 `collocation.search` 换取内部 `id` 再查/改（换法见 collocation.search 的「collocationId → 内部 id 解析配方」），直接用 collocationId 会报「搭配不存在」。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配内部ID（来自 collocation.search 的 `records[].id`；不是 collocationId） |

### 出参（原始返回）

- **路径参数来源**：`id`（→ 各写能力）；基础字段：`collocationId`、`storeId`、`storeName`、`name`、`recommendation`、`hasMainImage`、`mainImageUrl`、`showRecommendInDetail`、`productCount`
- `previewQrcodeUrl`：小程序预览二维码 URL（异步生成，可能为空）
- `products[]` 子结构（编辑回填锚点，含实时 SPU 信息）：`spuId`、`productName`、`productImage`、`productPrice`（string，元）、`spuStatus`（实时在售状态）、`sortOrder`、`anchorX`/`anchorY`（0.00~100.00 百分比坐标）、`anchorLabel`、`anchorDirection`（right/down/left/up）

### 调用示例

```json
{"capability":"ops.product.collocation.detail","input":{"id":"3300012345678901234"},"summary":"查看搭配详情"}
```

---

## ✅ 海报文案配置查询 — ops.product.collocation.poster-config-get

- **语义**：获取搭配的分享海报文案配置（主标题/副标题/投放文案/主图）；无配置时返回空骨架。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配 ID（路径参数） |

### 出参（原始数据）

- `collocationId`、`mainTitle`、`subTitle`、`promotionCopy`、`mainImageUrl`
- **格式敏感字段**：`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.product.collocation.poster-config-get","input":{"id":"3300012345678901234"},"summary":"查看该搭配的海报文案配置"}
```

---

## ✅ 投放物料查询 — ops.product.collocation.launch-material

- **语义**：聚合获取该搭配指定小程序环境的投放物料（微信太阳码 + URL Link / release 短链）。物料异步生成，首次调用可返回 `GENERATING` 状态——稍后重查即可。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配 ID（路径参数） |
| envVersion | String | ✅ | 环境版本（如 `release`） |

### 出参（原始数据）

- `collocationId`、`envVersion`、`pagePath`（小程序页面路径）、`generatedAt`（yyyy-MM-dd HH:mm:ss）
- `qrcode` / `shortLink` / `urlLink`：物料对象，结构 `{capability, status, value, failureReason, expiresAt}`——`status` 为物料状态（`READY` / `GENERATING` / `FAILED`，仅此三值），`value` 为物料值（太阳码/链接 URL），`failureReason` 仅 FAILED 有值，`expiresAt` 为物料时效（链接类有值）

### 调用示例

```json
{"capability":"ops.product.collocation.launch-material","input":{"id":"3300012345678901234","envVersion":"release"},"summary":"获取搭配正式环境的投放物料"}
```
