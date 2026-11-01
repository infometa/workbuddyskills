# 促销域 — 促销审核链查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-review.md`
> 审核链是活动与券模板创建/修改的唯一通道。pending.detail 返回编辑/提审必传的乐观锁 `version` 与完整表单快照。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：查询 pending.detail · pending.check-logs
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 审核链写操作（编辑/提审/撤回/审核/删除/变更重审）见 `pending-action.md`。

---

## ✅ 审核草稿详情 — `ops.promotion.pending.detail`

- 编辑前必读（取 version + 完整表单快照）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核草稿 ID（本文各能力中的 pendingId 均为此义） |

### 出参（原始数据）

- **关键字段来源**：`pendingId`（→ 编辑/提审/撤回/审核/删除）、`promotionId`（→ 审核历史；变更重审场景为真实主表ID，可用于查看线上配置；新建场景为预分配ID，**新建活动审核通过前不可用于正式活动详情/状态操作**；草稿操作始终用pendingId）、`version`（→ 编辑/提审必传的乐观锁）、`templateId`（券模板pending的模板ID，新建预分配值不代表正式模板已存在）
- **枚举字段**：`checkStatus`（0 草稿 / 1 待审核 / 3 已驳回）、`sourceType`（0 新建 / 1 变更重审）、`bizType`（PROMOTION/COUPON_TEMPLATE）
- **格式敏感字段**：`checkTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `promotionDetail` / `couponDetail` 为**创建请求形态的表单快照**（字段名与 `activity.create` / `coupon-template.create` 入参一致——rules/goodsList/productScopeType/audienceType 等，可直接作为编辑基线）：
  - 快照形态即**创建请求体**（券场景为该请求体的券模板变体，字段一致）。
  - ⚠️ **券场景下 `couponDetail` 与 `promotionDetail` 内容完全一致**（同一份快照的两个出口）——不要当成两份互补数据去分别读取。
  - `rules` 是**从规则 JSON 反解回填**的，规则 JSON 为空时不回填；`goodsList` 为快照原文（变更重审场景由主表商品列表覆盖）；`extJson` 原文回显但会剔除两个口令内部键。
  - ⚠️ **口令码未脱敏，是明文**：`passcode` 原样回显，且当顶层为空时会从扩展配置里提升上来。属业务资产，只在用户要求核对时转述。
  - 编辑时以其为基线保留未改动字段。

### 调用示例

```json
{"capability":"ops.promotion.pending.detail","input":{"pendingId":"4200000000000000001"},"summary":"读取审核草稿详情与乐观锁版本"}
```

---

## ✅ 审核历史 — `ops.promotion.pending.check-logs`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionId | String | ✅ | 活动 ID（不是 pendingId） |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **枚举字段**：`action`（**1 提交 / 2 通过 / 3 驳回 / 4 撤回**）、`sourceType`（0/1）、`bizType`
- **关键字段来源**：`promotionId`；`reason` 为审核意见；`operatorName` 为操作人姓名（**Feign 翻译降级时恒为 null**，此时回退 `operator`；`operatorId` 为操作人 ID，十进制字符串）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）；`versionNo` 对齐 `pending.submit_count`
- ⚠️ **审核历史没有 `templateId` 字段**（已移除，底层数据列仅留作审计追溯）——不要从审核历史取券模板 ID。

### 调用示例

```json
{"capability":"ops.promotion.pending.check-logs","input":{"promotionId":"4100000000000000001","pageNum":1,"pageSize":20},"summary":"查看活动的审核历史"}
```

---
