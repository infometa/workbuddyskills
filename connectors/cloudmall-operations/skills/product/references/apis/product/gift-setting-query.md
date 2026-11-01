# 商品域 — 赠品（送礼玩法）查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-gift-setting.md`；写操作（配置保存）见 `gift-setting-action.md`；商品通用配置见 `setting-query.md` / `setting-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：gift-setting.get 送礼配置查询 · gift-setting.validate-skus 白名单资格校验

---

## ✅ 送礼配置查询 — ops.product.gift-setting.get

- **语义**：获取租户送礼玩法配置（开关/金额区间/排除类目/白名单商品/祝福语/分享素材），含排除类目与白名单商品的富化回显（名称等信息）。

### 入参

无（空对象 `{}`）。

### 出参（原始数据）

- `enabled`（送礼玩法开关）、`minAmount`/`maxAmount`（可送礼商品金额区间，元）、`excludedCategoryCodes`（排除类目编码集合）、`whitelistSkuIds`（白名单 SKU ID 集合）
- 富化回显：`excludedCategories[]`（排除类目信息）、`whitelistProducts[]`（白名单商品信息）
- `defaultBlessing`（默认祝福语 ≤100 字）、`shareTitle`（分享文案 ≤20 字）、`shareImageUrl`/`posterImageUrl`/`receiveSuccessImageUrl`/`receiveFailureImageUrl`（分享/海报/领取结果素材 URL）。

### 调用示例

```json
{"capability":"ops.product.gift-setting.get","input":{},"summary":"查看送礼玩法当前配置"}
```

---

## ✅ 白名单资格校验 — ops.product.gift-setting.validate-skus

- **语义**：批量校验候选 SKU 是否可选为送礼白名单商品（纯校验无副作用），返回 `selectable` 与不可选原因——配置白名单前用来过滤不合规商品。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuIds | List&lt;String&gt; | ✅ | 候选 SKU ID 列表（来自 spu.skus / sku.search） |

### 出参（数组，原始数据）

- 每项：`skuId`、`selectable`（是否可选）、`reason`（不可选原因；selectable=true 时为 null）。

### 调用示例

```json
{"capability":"ops.product.gift-setting.validate-skus","input":{"skuIds":["9000012345678901234","9000012345678901235"]},"summary":"校验两个候选商品能否加入送礼白名单"}
```
