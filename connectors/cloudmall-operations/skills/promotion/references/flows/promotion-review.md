# 促销域 — 运营流程：审核链（本域核心流程）

> 创建/修改活动与券模板的唯一通道，新建与变更两条链路；活动与券模板创建均走本流程。
> 概念知识见 `references/domains/promotion-concepts.md`，状态与枚举见 `references/domains/promotion-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> 对应契约：`pending-action.md`（编辑/提审/审核/删除）、`pending-query.md`（草稿详情/审核历史）、`activity-action.md` 与 `coupon-template-action.md` 的 create/check。
>
> **能力标识约定**：本文为行文简洁使用模块短名（如 `pending.submit`），
> 实际调用 capability 必须使用全限定 id = `ops.promotion.` + 短名（即 `ops.promotion.pending.submit`），
> 禁止把短名直接作为 capability 传入。

---

## 促销审核链

### 创建、改期与提审前检查

先读取 `references/apis/promotion/form-validation.md`；特殊活动还读 `specialty.md`。编辑以 pending 完整快照为基线合并修改，按当前模式校验整组日期、SKU价格和范围：预售保留发货时刻时，活动/尾款截止必须在其之前；定金窗口同步活动起止。不得只把过期结束时间顺延、留下过去的开始/定金/尾款窗口。仅提审已有草稿也要先读快照检查；审批通过阶段的时间规则仍按下方审核链执行。

### 新建链路（草稿 → 提审 → 通过 → 落主表）

```
创建草稿（activity.create / coupon-template.create，返回 pendingId + 预分配 promotionId）
  → [可选] 编辑草稿（pending.update / coupon-template.update，必传 version）
  → 提审（pending.submit / coupon-template.submit；带内容=先存后审，不带=直接提审）
  → 审核通过（pending.approve / activity.check(approved=true) / coupon-template.check(approved=true)）→ 活动落主表（按审核时刻回算：开始时间已过→直接进行中；预热窗口内→预热；否则未开始；**结束时间已过无法通过审核**，报「活动已过期」需改期重提）
  或 审核驳回（pending.reject / activity.check(approved=false) / coupon-template.check(approved=false)，reason 必填）
  → 驳回后修改草稿（pending.update）→ 重新提审
待审核可撤回（pending.withdraw → 回草稿态）
草稿/驳回可删除（pending.delete，物理删除不可恢复）
```

### 变更重审链路（仅未开始的活动）

```
发起变更（pending.start-edit，仅主表 NOT_START；已有草稿/驳回 pending 时复用其 pendingId）
  → 编辑变更草稿（pending.update）→ 提审 → 通过（变更生效）/ 驳回（解锁主表，可改后重提）
```

- 变更提审后主表 `editing_locked=1`：期间禁止编辑/删除/停用/再次变更。
- 撤回/驳回/删除变更草稿均会解锁主表。

审核通过后 pending 会被删除：普通活动按已知 promotionId 查 activity.detail；券模板按 promotion-coupon.md 的参数来源链取得正式 templateId，再查询正式详情。用户未提供通过意见时不补写 reason，审核回执不含正式状态时不能宣称“已回读”。

### 审核历史

`ops.promotion.pending.check-logs`（按 promotionId 分页）；草稿快照用 `ops.promotion.pending.detail`（promotionDetail/couponDetail 字段为完整表单内容，编辑前必读）。

### 参数来源

| 参数 | 来源 |
|------|------|
| pendingId | 创建草稿响应 / 搜索 PENDING 行 / start-edit 响应 |
| version | pending 详情的 `version`（编辑/提审带内容时必传） |
| 审核结论与驳回原因 | 用户明确给出，禁止 AI 编造 |

### 异常处置
- `PROMOTION_OPTIMISTIC_LOCK_CONFLICT`（版本冲突）→ 重新读 pending 详情取新 version，与用户确认后重试。
- 非草稿/驳回状态提审/编辑 → 按状态机说明当前态。
- 提审校验失败（时间/规则/商品缺失）→ 读错误信息定位缺失项，补全后再提。

---

## 跨域引用

- 引用：商品域（spuId/skuId/类目/品牌）、数据标签域（人群标签值 ID、口令码人群包）、用户域（memberId）。
- 被引用：营销域、装修域、交易域（订单结算）。
- 需要跨域数据时先查对应域技能（商品/用户/交易），不要用促销接口猜测商品或会员信息。
