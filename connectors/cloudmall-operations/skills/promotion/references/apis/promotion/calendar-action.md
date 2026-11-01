# 促销域 — 促销日历与主题写操作契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-support.md`
> 主题是活动分组容器，删除主题不删活动。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：写 theme.create · theme.update · theme.workcopy · theme.delete · theme.assign-activity · theme.unassign-activity
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：expectedRevision 从 `calendar-query.md` 的 theme.detail 取 revision 当前值；theme.create 固定传 0（新主题基线）。
> 创建/修改主题排期前读取 `form-validation.md` 的主题日期覆盖：周期须覆盖全部保留活动的生命周期（含预热），不得为保存而自动移出冲突成员。前端名称上限50字符，服务端64字符。
> 日期示例假设用户已确认 2026 年九月的起止时刻（Asia/Shanghai）；实际调用须使用用户确认的日期、时刻和时区重新计算，并核对成员生命周期覆盖，不照抄示例时间。

---

## ✅ 创建主题 — `ops.promotion.theme.create`

- 🟡 可逆写（可编辑/删除）
- **前置**：`expectedRevision` 固定传 **0**（新主题版本基线，非 0 报「新主题版本基线必须为0」——与其他写操作「取 theme.detail 当前值」不同）；`sourceThemeRevisions` 必传（纳入的活动均未归属任何主题时传空对象 `{}`；纳入已在其他主题的活动需带源主题 revision）。
- 服务内部名称校验可能报“主题周期不合法”，HTTP入口也可能先触发DTO参数校验；不要断言超长名称必返回某一文案。排障同时核对名称与周期。
- ALL_ELIGIBLE不是状态安全筛选：优先完整分页预览eligible-activities，按用户意图确定ID集合后用EXPLICIT；候选仍须核对状态，不能只取第一页当全部。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| expectedRevision | Integer | ✅ | 固定传 0（新主题版本基线） |
| sourceThemeRevisions | Object | ✅ | 源主题乐观锁：`{"<源主题ID>": <revision>}`（纳入未归属活动传 `{}`，≤500 项） |
| name | String | ✅ | 主题名称，≤64 字符（服务端 trim 首尾空格后校验非空） |
| startTime | String | ✅ | 主题开始（毫秒时间戳） |
| endTime | String | ✅ | 主题结束（毫秒时间戳） |
| selectionMode | String | ✅ | `EXPLICIT` 显式指定活动（配 promotionIds）/ `ALL_ELIGIBLE` 按生命周期时间覆盖自动纳入，当前不按状态/类型过滤，可能含已结束/终止活动（promotionIds传[]） |
| promotionIds | String[] | ✅ | 活动 ID 列表（**必填**，EXPLICIT 时逐个给出；ALL_ELIGIBLE 传 `[]`）。⚠️ **本字段无条数上限**（与 workcopy 的 `addedPromotionIds` 上限 500 不对称）——数量大时结果由服务端事务耗时决定，不是被上限拒绝 |

### 出参（原始数据）

- **关键字段来源**：`themeId`（→ 编辑/删除/归组）；`promotionIds`/`activityCount` 回显。

### 调用示例

```json
{"capability":"ops.promotion.theme.create","input":{"expectedRevision":0,"sourceThemeRevisions":{},"name":"2026年九月大促","startTime":"1788192000000","endTime":"1790783999999","selectionMode":"EXPLICIT","promotionIds":["4100000000000000001"]},"summary":"创建2026年九月大促主题并纳入指定活动（Asia/Shanghai）"}
```

---

## ✅ 编辑主题 — `ops.promotion.theme.update`

- 🟡 可逆写
- **语义**：全量覆盖 name/时间窗；`removedPromotionIds` **必填**（空数组=不移出任何活动；显式列出的活动被移出主题）。
- **前置**：`expectedRevision` 必填（主题乐观锁，从 `theme.detail` 取 `revision` 当前值；不匹配报「主题已被修改，请刷新后重试」）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| themeId | String | ✅ | 主题 ID |
| expectedRevision | Integer | ✅ | 主题乐观锁版本号（theme.detail 的 revision） |
| name | String | ✅ | 主题名称，≤64 字符（服务端 trim 首尾空格后校验非空） |
| startTime | String | ✅ | 主题开始（毫秒时间戳） |
| endTime | String | ✅ | 主题结束（毫秒时间戳） |
| removedPromotionIds | String[] | ✅ | 要移出的活动 ID 列表（空数组=不移出） |

### 出参（原始数据）

- 保存后的主题视图（`themeId`/`revision` 新版本号/`promotionIds`/`activityCount`）。

### 调用示例

```json
{"capability":"ops.promotion.theme.update","input":{"themeId":"5100000000000000001","expectedRevision":2,"name":"2026年九月大促","startTime":"1788192000000","endTime":"1790783999999","removedPromotionIds":[]},"summary":"调整2026年九月大促主题时间窗（Asia/Shanghai）"}
```

---

## ✅ 主题工作副本原子保存 — `ops.promotion.theme.workcopy`

- 🟡 可逆写（可再次 workcopy/update 修正）
- **语义**：名称、排期、成员增删在**同一事务内原子保存**（区别于 `theme.update` 只改名称/排期/移出——workcopy 可同时批量移入）。`addedPromotionIds` 与 `removedPromotionIds` 不得重叠；`removedPromotionIds` 必须全部是当前主题成员。
- **前置**：`expectedRevision` 目标主题乐观锁（theme.detail 取当前值）；`sourceThemeRevisions` 为**跨主题移入活动的源主题乐观锁**（`Map<源主题ID, 源主题revision>`，键是主题 ID 不是活动 ID；活动未归属/同主题内操作时传空对象 `{}`）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| themeId | String | ✅ | 主题 ID（路径参数） |
| expectedRevision | Integer | ✅ | 目标主题乐观锁版本号 |
| name | String | ✅ | 主题名称，≤64 字符（服务端 trim 首尾空格后校验非空） |
| startTime | String | ✅ | 主题开始（毫秒时间戳） |
| endTime | String | ✅ | 主题结束（毫秒时间戳） |
| removedPromotionIds | String[] | ✅ | 要移出的活动 ID 列表（空数组=不移出） |
| addedPromotionIds | String[] | ✅ | 要加入的活动 ID 列表（≤500，空数组=不加入） |
| sourceThemeRevisions | Object | ✅ | 源主题乐观锁：`{"<源主题ID>": <revision>}`（无跨主题移入传 `{}`，≤500 项） |

### 出参（原始数据）

- 保存后的主题视图（含新 `revision` 与 `promotionIds`）。

### 调用示例

```json
{"capability":"ops.promotion.theme.workcopy","input":{"themeId":"5100000000000000001","expectedRevision":3,"name":"2026年九月大促","startTime":"1788192000000","endTime":"1790783999999","removedPromotionIds":[],"addedPromotionIds":["4100000000000000002"],"sourceThemeRevisions":{"5100000000000000002":2}},"summary":"把活动从其他主题移入并保存2026年九月主题排期（Asia/Shanghai）"}
```

---

## ✅ 删除主题 — `ops.promotion.theme.delete`

- 🟡 可逆性弱（主题删除后活动转为未归属，需重新归组）
- **语义**：只删主题分组，**不删除活动本身**。
- **前置**：`expectedRevision` 服务层必填（缺失报「页面版本过旧，请刷新后重试」；从 theme.detail 取当前值）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| themeId | String | ✅ | 主题 ID |
| expectedRevision | Integer | ✅ | 主题乐观锁版本号（query 参数） |

### 调用示例

```json
{"capability":"ops.promotion.theme.delete","input":{"themeId":"5100000000000000001","expectedRevision":2},"summary":"删除该主题（活动转为未归属）"}
```

---

## ✅ 活动加入/移动主题 — `ops.promotion.theme.assign-activity`

- 🟡 可逆写（unassign 可移出）
- **语义**：加入目标主题；活动已在其他主题时**跨主题移动**（原子：源主题移出 + 目标主题加入）。
- **前置**：请求体**必填**（缺失报「页面版本过旧」）——`expectedRevision` 目标主题乐观锁 + `sourceThemeRevisions` 源主题乐观锁（`Map<源主题ID, 源主题revision>`；活动未归属时传空对象 `{}`）。建议先查 eligible-targets 确认 eligible=true（主题周期须覆盖活动周期）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| themeId | String | ✅ | 目标主题 ID（路径参数） |
| promotionId | String | ✅ | 活动 ID（路径参数） |
| expectedRevision | Integer | ✅ | 目标主题乐观锁版本号 |
| sourceThemeRevisions | Object | ✅ | 源主题乐观锁：`{"<源主题ID>": <revision>}`（活动未归属传 `{}`） |

### 出参（原始数据）

- `themeId`/`promotionId`/`assignedAt`（归组时间，**yyyy-MM-dd HH:mm:ss** 字符串——非毫秒时间戳）、`revision`（主题版本号，整数）。
  - ⚠️ `revision` 口径分两支：活动**首次归入**该主题时返回自增后的**新版本号**；活动**已在该主题**（重复归组）时返回自增**前**的旧值。不要假设「归组后 revision 必 +1」。

### 调用示例

```json
{"capability":"ops.promotion.theme.assign-activity","input":{"themeId":"5100000000000000001","promotionId":"4100000000000000001","expectedRevision":2,"sourceThemeRevisions":{}},"summary":"把活动加入九月大促主题"}
```

---

## ✅ 活动移出主题 — `ops.promotion.theme.unassign-activity`

- 🟡 可逆写（可再次 assign）
- **前置**：`expectedRevision` 服务层必填（缺失报「页面版本过旧」；从 theme.detail 取当前值）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| themeId | String | ✅ | 主题 ID（路径参数） |
| promotionId | String | ✅ | 活动 ID（路径参数） |
| expectedRevision | Integer | ✅ | 主题乐观锁版本号（query 参数） |

### 调用示例

```json
{"capability":"ops.promotion.theme.unassign-activity","input":{"themeId":"5100000000000000001","promotionId":"4100000000000000001","expectedRevision":2},"summary":"把活动移出主题"}
```
