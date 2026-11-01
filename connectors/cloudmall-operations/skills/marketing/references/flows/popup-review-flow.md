# 营销域 — 运营流程：首页弹窗审核链

> 概念知识见 `references/domains/marketing-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`popup-query.md` / `popup-action.md`。

---

## 弹窗审核链

**场景**：首页弹窗创建→提审→审核→投放→暂停/恢复/下线全链路，及全局策略与效果统计。

```
创建（popup.create，isDraft=true 宽松保存 / false 强校验；创建后恒为 DRAFT）
  → [可选] 编辑（popup.update，仅 DRAFT/REJECTED；popupId 与 id 两个 ID 字段必须同值传入；以详情回显为基线保留未改字段）
  → 提审（popup.submit，仅 DRAFT/REJECTED；四要素强校验：名称/模板类型/开始时间/优先级/投放规则）
  → [建议] 冲突检测（popup.conflict，提审后执行并向用户转述冲突项）
  → 审核（popup.review，仅 PENDING_REVIEW，🔴 审核结论必须来自用户明确指示）
      ├─ APPROVE：开始时间已过 → 直接 ACTIVE；未到 → APPROVED（到点自动上线）
      ├─ EDIT_APPROVE：先应用 popupData 修改再通过
      └─ REJECT：→ REJECTED（reason 必填 ≥10 字，禁止编造）
  → 投放中（ACTIVE）：暂停（pause）/ 恢复（resume，仅 PAUSED 且未过期）/ 下线（offline，🔴 ENDED 终态）
  → 效果统计（popup-stats.summary / trend / store；global-summary 全租户汇总）
```

- 全局策略：`popup.global-strategy` → `update-global-strategy`（🔴 全租户生效，四字段全部必填整包覆盖）。
- 批量下线 `batch-offline` / 批量删除 `batch-delete`：逐条执行、失败跳过（部分成功，无逐项回执）——**执行后必须回读列表/状态计数核验**。
- 删除 `popup.delete`：投放中（ACTIVE）不可删，需先下线。

### 参数来源

| 参数 | 来源 |
|------|------|
| 弹窗 id | 列表/创建响应 |
| tagIds（人群标签） | 数据标签域标签查询 |
| storeIds | 商户域门店列表 |
| couponTemplateIds（COUPON 模板） | 促销域券模板 |
| targetId（跳转目标） | 商品 SPU ID / 促销活动 ID / 装修页 ID（按 linkType） |
| 审核结论与驳回原因 | 用户明确给出，禁止 AI 编造 |

### 异常处置
- 提审校验失败 → 读错误信息定位缺失项（具体缺失项会逐项列出）。
- 状态前置不符（如编辑非草稿）→ 重查详情按状态机说明当前态。
- 统计字段注意：clickRate 为百分数不要再乘 100；conversionRate 与 timePoint 当前实现未赋值，不要引用。

---
