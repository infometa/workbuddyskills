# 商品域 — 到店服务与预约模板查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-service.md`；写操作（服务增改/上下架/删除、模板增改删）见 `store-service-action.md`。
> 跨域依赖：trade 域预约规则/预约记录运行时经内部 Feign 回查本域预约模板（内部面，不开放）；本域只管「服务与模板定义」。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：store-service.search 到店服务分页 · store-service.detail 到店服务详情 · appointment-template.search 预约模板分页 · appointment-template.options 预约模板选项 · appointment-template.detail 预约模板详情

---

## ✅ 到店服务分页 — ops.product.store-service.search

- **语义**：到店履约预约类服务（如讲解服务）的分页列表。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数（≤100） |
| name | String | — | 服务名称模糊搜索（≤50 字） |
| status | String | — | 状态：`draft` / `online` / `offline`（小写） |
| storeScope | String | — | 门店范围：`all` / `specified`（小写） |

### 出参（`PageResult`，原始数据）

- **路径参数来源**：`records[].id`（→ detail/update/on-shelf/off-shelf/delete）
- **枚举字段**：`status`（draft/online/offline）、`confirmMode`（auto/store_confirm）、`storeScope`

### 调用示例

```json
{"capability":"ops.product.store-service.search","input":{"pageNum":1,"pageSize":20,"status":"online"},"summary":"查看已上架的到店服务"}
```

---

## ✅ 到店服务详情 — ops.product.store-service.detail

- **语义**：单个到店服务详情（服务项目、预约模板、门店分配），编辑前读现态。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 服务 ID（路径参数） |

### 出参（原始数据）

- `name`、`subtitle`、`images[]`（string[]，首张已预签名）、`serviceItems[]`、`templateId`（预约模板）、`maxPerSlot`、`confirmMode`（auto/store_confirm）、`validStartDate/validEndDate`（yyyy-MM-dd）、`storeScope`、`detailImages[]`、`status`（draft/online/offline）
- `serviceItems[]` 子结构（编辑回填锚点）：`id`（已有项目 ID——update 全量覆盖时传原 id 保留，新增不传）、`name`、`description`、`sortOrder`
- `stores[]` 子结构（storeScope=specified 时的关联门店；all 时为空数组）：`storeId`（→ update storeAssignments[].storeId）、`storeName`、`storeAddress`、`templateId`（该门店差异化模板，null=用服务级默认模板——**编辑回填 storeAssignments 时从这两字段构造**）

### 调用示例

```json
{"capability":"ops.product.store-service.detail","input":{"id":"2500012345678901234"},"summary":"查看讲解服务详情确认现态"}
```

---

## ✅ 预约模板分页 — ops.product.appointment-template.search

- **语义**：预约时间模板分页列表（营业时段/粒度/提前预约规则）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数（≤100） |

### 出参（`PageResult`，原始数据）

- **路径参数来源**：`records[].id`（→ detail/update/delete、store-service 的 templateId）

### 调用示例

```json
{"capability":"ops.product.appointment-template.search","input":{"pageNum":1,"pageSize":20},"summary":"查看预约时间模板列表"}
```

---

## ✅ 预约模板选项 — ops.product.appointment-template.options

- **语义**：全量模板选项列表（下拉选择用，创建到店服务时取 `id` 作 templateId）。

### 入参

无（空对象 `{}`）。

### 出参（数组，原始数据）

- **关键字段来源**：`id`（→ store-service 的 templateId / storeAssignments[].templateId）、`name`。

### 调用示例

```json
{"capability":"ops.product.appointment-template.options","input":{},"summary":"获取预约模板选项"}
```

---

## ✅ 预约模板详情 — ops.product.appointment-template.detail

- **语义**：单个模板详情（编辑前读现态）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板 ID（路径参数） |

### 出参（原始数据）

- `name`（≤30 字）、`startTime`/`endTime`（HH:mm）、`slotDuration`（分钟 30/60/120）、`applicableWeekdays[]`（1~7）、`requireAdvanceBooking`、`advanceBookingValue`、`advanceBookingUnit`（day/hour）、`maxBookingDays`、`requiredFields[]`（`name`/`phone`）。

### 调用示例

```json
{"capability":"ops.product.appointment-template.detail","input":{"id":"2600012345678901234"},"summary":"查看标准营业时段模板详情"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 内部查询面（store-service/template 的 internal 端点） | 服务间内部 Feign 面，供 trade 域预约运行时回查，非运营面 |
