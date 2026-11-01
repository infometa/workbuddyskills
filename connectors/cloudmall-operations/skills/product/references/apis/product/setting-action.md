# 商品域 — 商品通用配置写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-gift-setting.md`；现态读取（可能为 null=未配置）先读 `setting-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：setting.general-save 通用配置保存

---

## ✅ 通用配置保存 — ops.product.setting.general-save

- **语义**：保存商品通用配置（upsert）；`filterOutOfStockProduct` 不传时保留现有值。⚠️ 与评价设置（review.setting-save）**同表同源**——两处保存会互相改写审核时效字段，向用户说明影响面。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reviewTimeout | Long | — | 人工审核时效（秒），1~31622400（约 365 天） |
| defaultPraiseTime | Long | — | 默认好评时间（秒），1~31622400 |
| filterOutOfStockProduct | Boolean | — | 商品列表是否过滤缺货商品（不传保留现有值） |

### 调用示例

```json
{"capability":"ops.product.setting.general-save","input":{"reviewTimeout":86400,"defaultPraiseTime":604800,"filterOutOfStockProduct":true},"summary":"设置人工审核时效1天并过滤缺货商品"}
```
