# 商品域 — 评价查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-review.md`；写操作（回复/审核/关键词/模板/设置）见 `review-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。未列出的展示型字段以后端实际返回为准，透传给用户即可；⚠️ **身份类字段（昵称等）不属展示型字段，禁止转述给终端用户**（手机号服务端已脱敏）。
> 评价管理主线：`review.search`/`tab-count` 找到待处理评价 → `review.detail` 看全文 → 回复（`review-action.md` 的 `reply`）或审核（`audit`/`batch-audit`/`append-audit`）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：review.search 评价分页 · review.tab-count 状态Tab计数 · review.detail 评价详情 · review.reply-templates 回复模板列表 · review.stats-overview 统计总览 · review.stats-trend 统计趋势 · review.stats-star-distribution 星级分布 · review.stats-word-cloud 评价词云 · review.stats-product-ranking 商品评价排行 · review.keyword-candidates 关键词候选池 · review.keywords-enabled 已启用关键词 · review.setting-get 评价设置查询 · review.export 评价导出（URL型）

---

## ✅ 评价分页 — ops.product.review.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页 |
| auditStatus | String | — | 审核状态：`PENDING_AUDIT`（待审）/ `APPROVED` / `AUTO_APPROVED` / `TIMEOUT_APPROVED` / `REJECTED` / `RISK_CONTROLLING` / `RISK_APPROVED` / `RISK_REJECTED`。⚠️ PENDING_AUDIT/REJECTED 为**追评合并口径**（待审 Tab = 主评待审或追评待审；其余状态排除有追评待审/驳回的记录），非单值精确匹配 |
| starLevel | Integer | — | 星级 1~5 |
| reviewType | String | — | **内容形态**：`WITH_TEXT`（有文字）/ `WITH_IMAGE`（有图）/ `STAR_ONLY`（仅星级）——不是首评/追评维度（追评用详情的 hasAppendReview 判断） |
| keyword | String | — | 评价内容关键词 |
| productName | String | — | 商品名称 |
| spuId / skuId | String | — | 商品维度过滤 |
| orderNo | String | — | 订单号 |
| startTime / endTime | String | — | 时间范围（`YYYY-MM-DD HH:mm:ss`，空格分隔） |

### 出参（原始返回）

`data.records[]` 为评价视图；**关键字段来源**：`records[].id`（→ 详情/审核/回复的 `id`/`reviewId`）、`starLevel`、`auditStatus`、`content`。

### 调用示例

```json
{"capability":"ops.product.review.search","input":{"pageNum":1,"pageSize":20,"auditStatus":"PENDING_AUDIT"},"summary":"查询待审核评价"}
```

---

## ✅ 评价 Tab 计数 — ops.product.review.tab-count

- **语义**：工作台 Tab 计数总览（5 桶：pendingAudit/approved/rejected/riskControlling/timeoutApproved），用于向用户汇报待办

### 入参

无（传空对象 `{}`）。

### 调用示例

```json
{"capability":"ops.product.review.tab-count","input":{},"summary":"查看各状态评价数量"}
```

---

## ✅ 评价详情 — ops.product.review.detail

- **语义**：审核/回复前先看全文（含图片、追评）
- ⚠️ **PII 红线**：详情中 `userPhone` 服务端**已脱敏**（掩码展示）；`userNickname` 等身份信息仍为原始值——身份类字段一律**禁止转述/复述给终端用户**，只可用于运营内部核对；向用户汇报时只用评价内容、星级、时间等业务字段

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 评价ID（来自 review.search 的 `records[].id`） |

### 出参（原始数据，结构化字段）

- `images[]`：string[]（评价图片 URL）
- `dimensionRatings[]`：维度评分 `{name（维度名）, score（1~5）}`
- `appendReviews[]`：追评列表——`id`（**追评自身 ID，→ append-audit / 回复追评的 appendReviewId**，勿与主评价 ID 混淆）、`content`、`images[]`、`auditStatus`、`rejectReason`、`createdTime`、`replies[]`
- `replies[]`：商家回复列表——`id`、`content`、`replierName`、`createdTime`
- `attributes[]`：商品描述属性回显 `{name, value, sortOrder}`；`aiKeywords[]`：AI 提取关键词

### 调用示例

```json
{"capability":"ops.product.review.detail","input":{"id":"5000012345678901234"},"summary":"查看评价详情"}
```

---

## ✅ 回复模板列表 — ops.product.review.reply-templates

- **语义**：全量非分页；回复时可引用模板内容（回复时仍需把最终文案作为 `content` 传入，而非模板ID）

### 入参

无（传空对象 `{}`）。

### 出参（原始返回）

`data[]` 为模板列表（含默认模板标记）。

### 调用示例

```json
{"capability":"ops.product.review.reply-templates","input":{},"summary":"查看评价回复模板"}
```

---

## ✅ 评价统计总览 — ops.product.review.stats-overview

- **语义**：运营看板数据，只读

### 入参

无（传空对象 `{}`）。

### 调用示例

```json
{"capability":"ops.product.review.stats-overview","input":{},"summary":"查看评价总览"}
```

---

## ✅ 评价趋势 — ops.product.review.stats-trend

- **语义**：运营看板数据，只读

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| granularity | String | ✅ | **小写** `day`/`week`/`month`（大写会静默回落 day） |
| startDate | String | ✅ | 起始日期（`YYYY-MM-DD`） |
| endDate | String | ✅ | 结束日期（`YYYY-MM-DD`） |

### 调用示例

```json
{"capability":"ops.product.review.stats-trend","input":{"granularity":"day","startDate":"2026-09-01","endDate":"2026-09-09"},"summary":"查看近9日评价趋势"}
```

---

## ✅ 星级分布 — ops.product.review.stats-star-distribution

- **语义**：运营看板数据，只读

### 入参

无（传空对象 `{}`）。

### 调用示例

```json
{"capability":"ops.product.review.stats-star-distribution","input":{},"summary":"查看星级分布"}
```

---

## ✅ 评价词云 — ops.product.review.stats-word-cloud

- **语义**：运营看板数据，只读

### 入参

无（传空对象 `{}`）。

### 调用示例

```json
{"capability":"ops.product.review.stats-word-cloud","input":{},"summary":"查看评价词云"}
```

---

## ✅ 商品评价排行 — ops.product.review.stats-product-ranking

- **语义**：运营看板数据，只读

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productName | String | — | 商品名过滤 |
| sortBy | String | — | `reviewCount` 评价数 / `positiveRate` 好评率（非这两个值会静默按 reviewCount 排序） |
| limit | Integer | — | 默认 5 |

### 调用示例

```json
{"capability":"ops.product.review.stats-product-ranking","input":{"sortBy":"reviewCount","limit":10},"summary":"查看商品评价排行前十"}
```

---

## ✅ 评价关键词候选池 — ops.product.review.keyword-candidates

- **语义**：关键词从评价中聚合产生：候选池待启用，启用后作为评价筛选词

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页 |
| spuId | String | — | 商品维度过滤 |
| keyword | String | — | 关键词（模糊） |

### 出参（原始返回）

`data.records[]`；**关键字段来源**：`records[].id`（→ 批量启用的 `ids`）、关键词、出现次数。

### 调用示例

```json
{"capability":"ops.product.review.keyword-candidates","input":{"pageNum":1,"pageSize":20},"summary":"查看评价关键词候选池"}
```

---

## ✅ 已启用评价关键词 — ops.product.review.keywords-enabled

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页 |
| spuId | String | — | 商品维度过滤 |
| keyword | String | — | 关键词（模糊） |

### 出参（原始返回）

`data.records[]`；**关键字段来源**：`records[].id`（→ 单条操作的 `id`）、关键词。

### 调用示例

```json
{"capability":"ops.product.review.keywords-enabled","input":{"pageNum":1,"pageSize":20},"summary":"查看已启用的评价关键词"}
```

---

## ✅ 评价设置查询 — ops.product.review.setting-get

- **语义**：查询租户评价全局设置（审核时效、默认好评、追评窗口、评分维度）。

### 入参

无（空对象 `{}`）。

### 出参（原始数据）

- `reviewTimeout`（审核时效，秒）、`defaultReviewEnabled`（默认好评开关）、`defaultReviewTimeout`（默认好评时间，秒）、`appendReviewWindow`（追评窗口，天）
- `scoreDimensions[]`：`key`（维度标识，如 product_description）、`name`、`fixed`（固定维度不可删除）、`sortOrder`。

### 调用示例

```json
{"capability":"ops.product.review.setting-get","input":{},"summary":"查看当前评价设置"}
```

---

## ✅ 评价导出（URL 型） — ops.product.review.export

- **语义**：按筛选条件导出评价。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| auditStatus | String | — | 审核状态筛选 |
| starLevel | Integer | — | 星级（1~5） |
| reviewType | String | — | 评价类型 |
| keyword | String | — | 关键词 |
| startTime | String | — | 开始时间（yyyy-MM-dd HH:mm:ss） |
| endTime | String | — | 结束时间（yyyy-MM-dd HH:mm:ss） |
| productName | String | — | 商品名称 |

### 出参

- 预期 `mode`/`downloadUrl`/`taskId`（URL 型导出契约）。

### 调用示例

```json
{"capability":"ops.product.review.export","input":{"auditStatus":"APPROVED","starLevel":5},"summary":"导出已通过的5星评价"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 评价 ES 重建 / 统计手动刷新 | 运维/调试面（统计聚合为定时任务，每 5 分钟自动执行） |
| 风控回调 | 外部风控系统机器回调入口（HMAC 验签），非运营操作 |
