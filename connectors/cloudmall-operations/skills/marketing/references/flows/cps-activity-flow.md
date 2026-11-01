# 营销域 — 运营流程：CPS 活动奖励与活动推广

> 概念知识见 `references/domains/cps-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`cps-activity-query.md` / `cps-activity-action.md`（活动奖励/分销规则）
> ⚠️ 下图为对象**生命周期参考**，不是单次执行清单：用户没说「发布」就不要调 publish——创建后停在 draft 汇报并询问。
> ⚠️ 按名称找活动时「找不到 ≠ 不存在」：CPS 活动奖励 / 互动活动 / 活动推广 / 促销活动四域都可能同名，一个域搜不到须把其余域都查一遍再下结论。、`cps-promotion-query.md` / `cps-promotion-action.md`（活动推广）、`cps-goods-promotion-query.md`（选品）。

---

## CPS 活动奖励管理

**场景**：创建/发布/终止 CPS 分销活动奖励，查询结算状态。

```
创建草稿（cps-activity.save，activityId 不传）→ [可选] 冲突校验（cps-activity.overlap-check）
  → 编辑（cps-activity.save，传 activityId，仅 draft 可改）
  → 发布（cps-activity.publish，draft → init）→ 按时间自动流转 init → warmup → running → terminated
  → [可选] 手动终止（cps-activity.terminate，init/warmup/running → terminated，立即流转结算状态）
  → 查结算明细（cps-settle.search）
草稿可删除（cps-activity.delete）；任意状态可复制为草稿（cps-activity.copy，名称追加「（复制）」，时间原样复制——副本预热时间可能已过期，需编辑后才能发布）
```

1. 保存前服务端逐条校验：预热时间 > 当前时间、开始 > 预热、结束 > 开始、名称 2-30 字、说明 2-500 字；任一失败整体拒绝。
2. 冲突校验口径：四维度（商品/门店/用户/分销员）**全部重叠**才算冲突；任一方四维度全不限则与所有活动冲突；信息不完整时保守不判冲突。
3. 终止为资损敏感操作：已产生订单 → unsettled（待结算），无订单 → settled（已结算），事务保障不可逆。

### 参数来源

| 参数 | 来源 |
|------|------|
| activityId | 列表/详情/保存/复制响应的 `activityId`（16 位业务 ID 字符串） |
| 奖励金额与阶梯 | 用户明确给出（元，两位小数），禁止 AI 编造 |
| 人群标签值 ID / 门店分组 ID / 分销员分组 ID | 数据标签域 / 商户域 / 分销员分组查询 |
| goodsList spuId | 商品推广选择器 `cps-goods-promotion.selector` |

### 异常处置
- 已发布活动更新被拒 → 仅 draft 可改；需要变更先用复制建新草稿。
- 发布报"只有未发布状态的活动才能发布" → 重查详情确认现态。
- 时间校验失败 → 按规则调整时间顺序后重试。

---

## CPS 活动推广管理

**场景**：维护 C 端推广落地页活动（爆品推广/平台活动）。

```
新建（cps-promotion.create，初始未发布 0）→ 配置商品编排（cps-promotion.update 的 selectGoods）
  → 发布（cps-promotion.publish，按时间窗口落 未开始 1 / 进行中 2）
  → [可选] 取消发布（cps-promotion.unpublish，1/2/3 → 0，可再编辑发布）
  → [可选] 提前结束（cps-promotion.terminate，1/2 → 3，不可再发布）
  → 效果报表（cps-stats.promotion-report）
```

- **更新为整体覆盖式**：未传字段会被置空——更新前先查明细，原值回传只改需要改的字段；服务端不校验当前状态，对已发布活动修改直接影响 C 端。
- 发布前置：活动名称已配置、商品编排结构完整（不完整报"商品配置不完整或格式不合法"）。
- **删除（cps-promotion.delete）不做任何状态校验**——进行中的活动也能直接物理删除，等于强制下线，务必先与用户确认。
- 列表 activityStatus 筛选传**中文描述**（未发布/未开始/进行中/已结束）且为当前页内存过滤——total 不变、翻页可能不连续，精确筛选用 id。

### 参数来源

| 参数 | 来源 |
|------|------|
| id（活动推广） | 列表/创建/复制响应的 `id`（十进制字符串） |
| selectGoods spuId | `cps-goods-promotion.selector` / 商品推广分页 |

---
