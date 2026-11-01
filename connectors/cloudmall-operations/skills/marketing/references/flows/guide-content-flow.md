# 营销域 — 运营流程：导购推广任务/话术/素材

> 概念知识见 `references/domains/guide-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`guide-task-query.md` / `guide-task-action.md`、`guide-speech-query.md` / `guide-speech-action.md`、`guide-material-query.md` / `guide-material-action.md`（业务素材/内容素材/素材分组）。

---

## 导购推广任务

**场景**：创建/下发/跟进导购推广任务（新品/活动/日常）。

```
创建草稿（guide-task.create，isDraft=true，仅标题/类型必填）
  或 直接创建并下发（isDraft=false，🔴 三段必填：targetCustomer/relatedContent/dispatch，创建即 active 并异步生成执行记录）
  → [草稿路径] 下发（guide-task.dispatch，🔴 draft/active 均可下发；active 重复下发会按当前范围再次生成执行记录，可能重复）
  → 查执行记录（guide-task.executions，异步生成略有延迟；executionStatus/keyword 筛选）
  → [可选] 催办（guide-task.urge，🟡 ≤10 条 executionIds 同步催办，缺省/超限则异步催办全部 pending/received）
  → [可选] 结束（guide-task.end，🔴 终态：pending/received 执行记录批量置 expired）
```

- 任务类型决定关联内容可选项：新品→product；活动→promotion/coupon；日常→content/page。
- goodsList 的 SKU 引用字段是 `skuList[].skuId`（不是 skuIds）；SPU 级选择不传 skuList（后端圈全部 SKU）。
- 更新 `update`：draft/active 可改（已结束不可），仅非空字段生效、嵌套结构整体替换。

---

## 话术管理

**场景**：维护导购工作台话术库（内容块 + 分组 + 置顶）。

1. 查询 `guide-speech.search`（**groupId 精确且不含子分组**——与内容素材"含子分组"不同）/ `guide-speech.detail`（contentBlocks 按序）。
2. 创建 `create`（内容块 1..9 条）→ 更新 `update`（**contentBlocks 一旦传入即全量替换**——只改标题时不要带）/ 删除 `delete`（🔴 物理删除含内容块）。
3. 批量：`batch-update-group`（action 固定 `move_group` 占位）/ `batch-delete`（action 固定 `delete`）；返回 successCount（不存在的 ID 跳过）。
4. 置顶 `toggle-top`（再调一次反转）；分享计数 `share`（缓存计数器 +1）。

---

## 推广素材管理
**场景**：业务素材（引用既有业务对象）/ 内容素材（原创内容）/ 素材分组三类对象维护。

### 业务素材
- 查询 `guide-material.business-search`（materialType/displayStatus/keyword；优惠券/促销标题实时回源可能变化）。
- 添加 `business-batch-add`（materialType + items[{sourceId, title?}]，同类型同 sourceId 自动跳过）→ 显示切换 `business-toggle-display`（🟡）→ 置顶 `business-toggle-top`（🟡）→ 批量移除 `business-batch-remove`（🔴 物理删除，不存在 ID 不报错）。

### 内容素材（发布生命周期）
```
创建草稿（content-create，🟡）→ [可选] 更新（content-update，任何发布状态都可改——已发布时改动立即生效，先确认影响）
  → 发布（content-publish，🔴 导购端立即可见；前置 draft/unpublished）
  → [可选] 取消发布（content-unpublish，🔴 导购端立即不可见；可再发布）
  → 删除（content-delete，🔴 物理删除；前置非 published）
```
- 附件 attachment 按类型只填对应子结构（images ≤9 张 / posters / videos 一段 / links）；图片/视频地址需用户提供已上传的云MALL 可访问地址。
- 统计：`content-stats` 全生命周期汇总 / `stats-trend` 按日趋势 / `stats-store` 门店明细。

### 素材分组
- `guide-material-group.tree`（**bizType 必传**：content_material / speech 两套独立树）→ `create`（最多两级；同父级子分组 ≤10；一级创建可带 children 批量建二级）→ `update`（仅改名/排序，不能移动层级）→ `delete`（🔴 三重校验：无子分组 + 无内容素材 + 无话术）。

---
