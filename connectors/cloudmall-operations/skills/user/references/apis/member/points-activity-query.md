# 会员域 — 积分活动查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points.md`；活动写操作（创建/编辑/启停/删除）见 `points-activity-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。活动启停影响 C 端发积分，属商业影响写。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.points-activity.search 积分活动分页 · member.points-activity.detail 积分活动详情

---

## ✅ 积分活动分页 — ops.member.points-activity.search

- 仅分页，无筛选字段

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页；pageSize ≤100 |

### 出参（原始返回）

分页对象。**关键字段**：`records[].id`（→ 详情/编辑/启停/删除路径参数）、`activityName`、`pointsPerYuan`；**枚举字段**：`status`（0=停用 1=启用）；**格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）。

### 调用示例

```json
{"capability":"ops.member.points-activity.search","input":{"pageNum":1,"pageSize":20},"summary":"查询积分活动列表"}
```

---

## ✅ 积分活动详情 — ops.member.points-activity.detail

- **编辑前必读**（全量覆盖回填来源）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 出参（原始返回）

活动详情对象。**关键字段**：`id`、`itemConfigType`（0/1/2）、`categoryItems[]`/`productItems[]`（可获积分范围）、`nonEarnableCategoryItems[]`/`nonEarnableProductItems[]`（不可获积分范围）、`limitPeriod`/`dailyPointsLimit`/`expiryMode`/`expiryYearOffset`/`expiryMonthDay`/`expiryDays`/`ruleContent`（编辑回填用）。`productItems[]`/`nonEarnableProductItems[]` 子项除 `skuId` 外还含**实时富化字段** `spuId`/`productName`/`skuName`/`skuCode`（详情时由商品中心实时补齐、不落库——编辑回传时无需也无法回传这些富化字段）。

### 调用示例

```json
{"capability":"ops.member.points-activity.detail","input":{"id":"1300012345678901234"},"summary":"查询积分活动详情"}
```
