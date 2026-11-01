# 商品域 — 到店服务与预约模板写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-service.md`；现态读取（服务/模板列表与详情）先读 `store-service-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：store-service.create 创建到店服务 · store-service.update 编辑到店服务 · store-service.on-shelf 服务上架 · store-service.off-shelf 服务下架 · store-service.delete 删除服务 🔴 · appointment-template.create 创建预约模板 · appointment-template.update 编辑预约模板 · appointment-template.delete 删除预约模板 🔴

---

## ✅ 创建到店服务 — ops.product.store-service.create

- **语义**：创建到店服务，返回新服务 `id`（string）。`isDraft=false` 直接发布（此时 `templateId` 必填）；`isDraft=true` 存草稿。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 服务名称（≤100 字） |
| subtitle | String | — | 服务副标题（≤200 字） |
| images | List&lt;String&gt; | — | 服务图片 URL 列表 |
| serviceItems | List | — | 服务项目列表（结构见下） |
| templateId | String | — | 预约时间模板 ID（**发布时必填**，草稿可空；来自 appointment-template） |
| maxPerSlot | Integer | — | 每时段人数上限（≥1，默认 10） |
| confirmMode | String | — | 确认模式：`auto`（自动确认）/ `store_confirm`（门店确认），默认 auto |
| validStartDate | String | — | 预约有效期起（yyyy-MM-dd） |
| validEndDate | String | — | 预约有效期止（yyyy-MM-dd） |
| cancelRuleDesc | String | — | 取消规则说明（≤200 字） |
| storeScope | String | ✅ | 门店范围模式：`all` / `specified` |
| storeAssignments | List | — | 门店差异化模板分配（specified 时用；结构见下；替代已废弃的 storeIds） |
| detailImages | List&lt;String&gt; | — | 服务详情素材 URL 列表 |
| isDraft | Boolean | — | true=存草稿 / false=发布（默认 false） |

**serviceItems[] 子结构**：`name`（✅ ≤30 字）、`description`（≤100 字）、`sortOrder`（≥0）。

**storeAssignments[] 子结构**：`storeId`（✅）、`templateId`（该门店使用的差异化模板；两级回退——无分配时用服务级 templateId）。

### 调用示例

```json
{"capability":"ops.product.store-service.create","input":{"name":"营地讲解服务","storeScope":"all","serviceItems":[{"name":"全程讲解","sortOrder":0}],"maxPerSlot":10,"confirmMode":"auto","isDraft":false,"templateId":"2600012345678901234"},"summary":"创建并发布营地讲解服务"}
```

---

## ✅ 编辑到店服务 — ops.product.store-service.update

- **语义**：编辑到店服务；`serviceItems` 全量覆盖（更新项传原 `id`，新增项不传）。**返回超卖警告**：若被预约引用的时段因 `maxPerSlot` 下调而超卖，返回 `overBookedSlots` 列表（门店/日期/时段/当前预约数/新上限）——收到警告必须如实转告用户。

### 入参

与 create 同构（`name` 非必填），另需路径 `id`；`isDraft` 仅当前状态为 draft 时生效（true=保持草稿，false=发布，发布时 templateId 必填）。

### 出参

- `overBookedSlots[]`：超卖时段警告（空列表=无超卖）：`storeId`、`appointmentDate`（yyyy-MM-dd）、`startTime`、`currentCount`、`maxPerSlot`。

### 调用示例

```json
{"capability":"ops.product.store-service.update","input":{"id":"2500012345678901234","name":"营地讲解服务","maxPerSlot":8},"summary":"下调讲解服务每时段人数到8并检查超卖"}
```

---

## ✅ 到店服务上架 — ops.product.store-service.on-shelf

- **语义**：上架（online）；执行后回读核验。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 服务 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.store-service.on-shelf","input":{"id":"2500012345678901234"},"summary":"上架讲解服务"}
```

---

## ✅ 到店服务下架 — ops.product.store-service.off-shelf

- **语义**：下架（offline）；执行后回读核验。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 服务 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.store-service.off-shelf","input":{"id":"2500012345678901234"},"summary":"下架讲解服务"}
```

---

## ✅ 删除到店服务 — ops.product.store-service.delete

- 🔴 不可逆；执行前向用户确认服务名称；有预约引用的服务建议先下架评估影响。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 服务 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.store-service.delete","input":{"id":"2500012345678901234"},"summary":"删除已停用的旧讲解服务"}
```

---

## ✅ 创建预约模板 — ops.product.appointment-template.create

- **语义**：创建预约时间模板，返回新模板 `id`（string）。**模板名称租户内唯一**（重名拒绝）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 模板名称（≤30 字，租户内唯一） |
| startTime | String | ✅ | 营业开始时间（`HH:mm` 如 09:00） |
| endTime | String | ✅ | 营业结束时间（`HH:mm` 如 21:00） |
| slotDuration | Integer | ✅ | 时间粒度（分钟）：30 / 60 / 120 |
| applicableWeekdays | List&lt;Integer&gt; | ✅ | 适用星期（1~7，非空） |
| requireAdvanceBooking | Boolean | ✅ | 是否需提前预约 |
| advanceBookingValue | Integer | 条件 | 提前时长数值（requireAdvanceBooking=true 时必填，≥1） |
| advanceBookingUnit | String | — | 提前时长单位：`day` / `hour` |
| maxBookingDays | Integer | — | 最长预约天数（≥1，默认 7） |
| requiredFields | List&lt;String&gt; | — | 预约信息字段：`name` / `phone` |

### 调用示例

```json
{"capability":"ops.product.appointment-template.create","input":{"name":"标准营业时段","startTime":"09:00","endTime":"21:00","slotDuration":60,"applicableWeekdays":[1,2,3,4,5,6,7],"requireAdvanceBooking":true,"advanceBookingValue":1,"advanceBookingUnit":"day","maxBookingDays":7,"requiredFields":["name","phone"]},"summary":"创建标准营业时段模板"}
```

---

## ✅ 编辑预约模板 — ops.product.appointment-template.update

- **语义**：编辑模板（名称租户内唯一、排除自身）；入参与 create 同构，另需路径 `id`。⚠️ 模板被在架到店服务引用时，时段变更影响其可约时段——编辑前先确认引用方。

### 调用示例

```json
{"capability":"ops.product.appointment-template.update","input":{"id":"2600012345678901234","name":"标准营业时段","startTime":"09:00","endTime":"22:00","slotDuration":60,"applicableWeekdays":[1,2,3,4,5,6,7],"requireAdvanceBooking":true,"advanceBookingValue":1,"advanceBookingUnit":"day","maxBookingDays":7,"requiredFields":["name","phone"]},"summary":"把模板营业结束时间延长到22点"}
```

---

## ✅ 删除预约模板 — ops.product.appointment-template.delete

- 🔴 不可逆；**被到店服务引用的模板删除会被拒绝**——先解除引用（改服务模板或删服务）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.appointment-template.delete","input":{"id":"2600012345678901234"},"summary":"删除废弃的预约模板"}
```
