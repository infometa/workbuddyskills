# 商品域 — 赠品配置与商品通用设置流程

> 对应契约：`apis/product/gift-setting-query.md`（送礼配置查询/白名单校验）、`apis/product/gift-setting-action.md`（送礼配置保存）、`apis/product/setting-query.md` 与 `apis/product/setting-action.md`（商品通用配置读写）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 送礼玩法配置

1. **读现态**：`ops.product.gift-setting.get`（开关/金额区间/排除类目/白名单/素材）
2. **圈品**：候选 SKU 先 `gift-setting.validate-skus` 校验资格（selectable=false 的带原因剔除）→ 通过者填入 whitelistSkuIds
3. **保存**：`gift-setting.save`（金额区间与分享素材向用户确认后提交）

## 商品通用配置

1. **读现态**：`ops.product.setting.general-get`（可能为 null=未配置）
2. **保存**：`setting.general-save`（人工审核时效/默认好评时间单位秒；缺货过滤不传保留现有值）
- ⚠️ 与评价设置（review.setting-save）同表同源，保存会互相改写审核时效——向用户说明影响面（见 `product-review.md` 评价设置维护）。
