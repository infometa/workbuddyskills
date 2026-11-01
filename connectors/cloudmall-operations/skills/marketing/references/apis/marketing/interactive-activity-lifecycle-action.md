# 营销域 — 互动活动生命周期写操作契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/interactive-activity-flow.md`
> formal 副本运行态操作（发布快照/暂停/恢复/结束）与复制、删除——发布后 C 端立即可见，结束/删除为终态；编辑配置见 `interactive-activity-action.md`、奖品履约见 `interactive-activity-prize-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：状态前置与现态核验读 `interactive-activity-query.md`（search/detail/stats）；发布前确认 draft 完整性。
> 能力索引（前缀 `ops.marketing.`）：interactive-activity.publish 发布互动活动 🔴 · interactive-activity.end 结束互动活动 🔴 · interactive-activity.pause 暂停互动活动 🟡 · interactive-activity.resume 恢复互动活动 🟡 · interactive-activity.copy 复制互动活动 🟢 · interactive-activity.delete 删除互动活动 🔴

---

## ✅ 发布活动 — `ops.marketing.interactive-activity.publish`

- **风险**：🔴 生效动作（draft 快照落 formal，C 端立即可见）
- **前置**：draft 存在且 configInfo 校验通过。发布时按开始时间自动判定 formal 初始状态（未到 → NOT_STARTED，已到 → RUNNING）。重复发布 = 覆盖 formal（再次快照）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.publish","input":{"activityId":"1942000000000000001"},"summary":"发布国庆到店兑换礼活动"}
```

---

## ✅ 结束活动 — `ops.marketing.interactive-activity.end`

- **风险**：🔴 不可逆（手动结束终态）
- **前置**：formal 处于 RUNNING / NOT_STARTED / PAUSED。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.end","input":{"activityId":"1942000000000000001"},"summary":"提前结束该互动活动"}
```

---

## ✅ 暂停活动 — `ops.marketing.interactive-activity.pause`

- **风险**：🟡 可逆（可恢复）
- **前置**：formal 处于 RUNNING / NOT_STARTED。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.pause","input":{"activityId":"1942000000000000001"},"summary":"暂停进行中的活动"}
```

---

## ✅ 恢复活动 — `ops.marketing.interactive-activity.resume`

- **风险**：🟡 可逆
- **前置**：仅 PAUSED；恢复后按开始时间回落 NOT_STARTED 或 RUNNING。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.resume","input":{"activityId":"1942000000000000001"},"summary":"恢复已暂停的活动"}
```

---

## ✅ 复制活动 — `ops.marketing.interactive-activity.copy`

- **风险**：🟡 可逆写（生成新草稿）
- **说明**：FORMAL 优先复制（未发布则复制 draft）；新活动名称追加"(副本)"，状态 UNPUBLISHED，页面配置随同复制。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 源活动业务 ID |

### 出参（原始数据）

- **关键字段来源**：返回对象含 `activityId`（新活动业务 ID）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.copy","input":{"activityId":"1942000000000000001"},"summary":"复制该活动为新一轮草稿"}
```

---

## ✅ 删除活动 — `ops.marketing.interactive-activity.delete`

- **风险**：🔴 不可逆（draft + formal 及库存/限流数据一并删除）
- **前置**：仅未发布（无 formal）或 formal 已结束（TERMINATED）/已过期（EXPIRED）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.delete","input":{"activityId":"1942000000000000001"},"summary":"删除已结束的互动活动"}
```

---
