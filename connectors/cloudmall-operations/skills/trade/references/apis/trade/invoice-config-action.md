# 交易域 — 发票配置契约（写操作）

> 概念知识：`references/domains/trade-concepts.md`；运营流程：`references/flows/trade-finance.md`
> **先读现值**：全部写入先用 `invoice-config-query.md` 的对应 list 读取现值；销方/购方信息是发票票面法定要素，必须来自用户提供的真实工商信息，不猜测。税率统一为小数（`0.13` 表示 13%），不是百分数。
> 平台凭据（appKey/appSecret）的创建与变更不在开放范围；列表返回的脱敏 appSecret 不能作为任何写操作入参。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 invoice.platform.toggle 🔴 · invoice.platform.set-default 🔴 · invoice.seller.save 🟡 · invoice.seller.delete 🔴 · invoice.seller.set-default 🟡 · invoice.tax-category.save 🟡 · invoice.tax-category.delete 🔴 · invoice.goods-tax.save 🟡 · invoice.goods-tax.delete 🔴 · invoice.goods-tax.toggle 🟡 · invoice.goods-tax.default-rate.save 🔴

---

## ✅ 开票平台启停 — ops.trade.invoice.platform.toggle

用途：启用或禁用一个开票平台（🔴）。**同一时间仅可启用一个平台**——启用新平台会改变全部开票链路的目标。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，非 null | platform.list 返回的平台 ID |
| status | 整数 | 是，非 null | `1` 启用、`0` 禁用 |

来源：`TogglePlatformRequest`。执行前复述平台名、当前状态与目标影响（禁用后开票全部暂停）；执行后 platform.list 回读。

```json
{
  "capability": "ops.trade.invoice.platform.toggle",
  "input": { "id": "8600000000000000001", "status": 1 },
  "summary": "启用开票平台"
}
```

---

## ✅ 切换默认平台 — ops.trade.invoice.platform.set-default

用途：切换默认开票平台（🔴）。影响新开票请求路由的目标平台。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是（body 字段 `id`，服务端校验非空） | platform.list 返回的平台 ID |

```json
{
  "capability": "ops.trade.invoice.platform.set-default",
  "input": { "id": "8600000000000000001" },
  "summary": "设置默认开票平台"
}
```

---

## ✅ 保存销方 — ops.trade.invoice.seller.save

用途：新增或编辑销方信息（🟡）。`id` 有值为编辑（全量覆盖）、无值为新增。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 否 | 编辑时必填（seller.list 取得） |
| sellerName | 字符串 | 百望场景外必填 | 公司名称（百望由平台税号自动关联，可空） |
| taxpayerNo | 字符串 | 是，正则 `^[0-9A-Z]{15}$` 或 `{18}` 或 `{20}` | 纳税人识别号（15/18/20 位数字或大写字母） |
| address / phone | 字符串 | 否 | 注册地址 / 注册电话 |
| bankName / bankAccount | 字符串 | 否 | 开户银行 / 银行账号 |

来源：`SaveSellerRequest`。销方信息来自用户提供的真实工商信息，不猜测；保存后 seller.list 回读。

```json
{
  "capability": "ops.trade.invoice.seller.save",
  "input": {
    "taxpayerNo": "91330100MA27XW888X",
    "sellerName": "杭州示例科技有限公司",
    "address": "杭州市西湖区文三路100号",
    "phone": "0571-88888888",
    "bankName": "杭州银行科技支行",
    "bankAccount": "888888888888"
  },
  "summary": "保存销方信息"
}
```

---

## ✅ 删除销方 — ops.trade.invoice.seller.delete

用途：删除销方（🔴）。**默认销方不允许删除**（服务端校验）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是（body 字段） | seller.list 返回的销方 ID |

```json
{
  "capability": "ops.trade.invoice.seller.delete",
  "input": { "id": "8700000000000000001" },
  "summary": "删除销方"
}
```

---

## ✅ 设默认销方 — ops.trade.invoice.seller.set-default

用途：设为默认销方（🟡）。后续开票默认使用该销方。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是（body 字段） | seller.list 返回的销方 ID |

```json
{
  "capability": "ops.trade.invoice.seller.set-default",
  "input": { "id": "8700000000000000001" },
  "summary": "设置默认销方"
}
```

---

## ✅ 保存税收分类 — ops.trade.invoice.tax-category.save

用途：新增或编辑税收分类编码（🟡）。`id` 有值为编辑、无值为新增。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 否 | 编辑时必填 |
| taxCategoryCode | 字符串 | 是，非空 | 税收分类编码（以税务机关编码为准，不自造） |
| taxCategoryName | 字符串 | 是，非空 | 分类名称 |
| parentCode | 字符串 | 否 | 父分类编码 |
| level | 整数 | 是 | 层级 |
| taxRate | 数字 | 否 | 税率（小数如 0.13） |
| preferredPolicy / description | 字符串 | 否 | 优惠政策 / 说明 |

```json
{
  "capability": "ops.trade.invoice.tax-category.save",
  "input": { "taxCategoryCode": "1070201000000000000", "taxCategoryName": "日用杂货", "level": 1, "taxRate": 0.13 },
  "summary": "保存税收分类编码"
}
```

---

## ✅ 删除税收分类 — ops.trade.invoice.tax-category.delete

用途：删除税收分类编码（🔴）。被商品税收映射引用的分类服务端拒绝删除。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是（body 字段） | tax-category.list 返回的分类 ID |

```json
{
  "capability": "ops.trade.invoice.tax-category.delete",
  "input": { "id": "8800000000000000001" },
  "summary": "删除税收分类编码"
}
```

---

## ✅ 保存商品税收映射 — ops.trade.invoice.goods-tax.save

用途：新增或编辑商品类目-税收映射（🟡）。影响该类目商品的开票税收编码与税率。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 否 | 编辑时必填 |
| goodsCategoryId | ID字符串 | 是 | 商品类目 ID（goods-tax.list 或商品域类目查询取得） |
| goodsCategoryName / goodsCategoryPath | 字符串 | 否 | 类目名称/路径（快照） |
| taxCategoryCode | 字符串 | 是，非空 | 税收分类编码（tax-category.list 取真实值） |
| taxCategoryName | 字符串 | 否 | 分类名称快照 |
| taxRate | 数字 | 是 | 税率（小数如 0.13） |
| preferredPolicy / preferredPolicyFlag / zeroTaxFlag | 字符串/整数 | 否 | 优惠政策 / 政策标记 / 零税率标记 |
| invoiceItemName | 字符串 | 否 | 票面商品名 |
| priority | 整数 | 否 | 匹配优先级 |

```json
{
  "capability": "ops.trade.invoice.goods-tax.save",
  "input": {
    "goodsCategoryId": "3000000000000000001",
    "goodsCategoryName": "服饰",
    "taxCategoryCode": "1070201000000000000",
    "taxCategoryName": "日用杂货",
    "taxRate": 0.13
  },
  "summary": "保存商品税收映射"
}
```

---

## ✅ 删除商品税收映射 — ops.trade.invoice.goods-tax.delete

用途：删除商品类目-税收映射（🔴）。删除后该类目商品开票回退全局默认税率。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是（body 字段） | goods-tax.list 返回的映射 ID |

**默认通配映射（`goodsCategoryId=0`）服务端拒绝删除**（`InvoiceTaxConfigServiceImpl` 校验）——它是所有无映射类目的兜底，删除即断兜底链路。

```json
{
  "capability": "ops.trade.invoice.goods-tax.delete",
  "input": { "id": "8900000000000000001" },
  "summary": "删除商品税收映射"
}
```

---

## ✅ 启停商品税收映射 — ops.trade.invoice.goods-tax.toggle

用途：启用或停用商品类目映射（🟡）。停用后该类目不参与开票匹配。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是（body 字段） | goods-tax.list 返回的映射 ID |
| status | 整数 | 是 | `1` 启用、`0` 停用 |

**默认通配映射（`goodsCategoryId=0`）不允许停用**（服务端校验「默认通配映射不允许禁用」）。`status` 服务端不做 0/1 范围校验（任意整数直接入库），Agent 只传 `0` 或 `1`。

```json
{
  "capability": "ops.trade.invoice.goods-tax.toggle",
  "input": { "id": "8900000000000000001", "status": 0 },
  "summary": "停用商品税收映射"
}
```

---

## ✅ 设置全局默认税率 — ops.trade.invoice.goods-tax.default-rate.save

用途：设置全局默认税率（🔴）。影响全部无映射类目商品的开票税率。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| taxRate | 数字 | 是（body 字段，服务端校验非空） | 全局默认税率（小数如 0.13） |

来源：`InvoiceTaxConfigController.setDefaultRate`。**前置：租户必须已配置默认销方**（该值实际写入默认销方的 `defaultTaxRate`；无默认销方时报错「请先配置默认销方信息」，先走 seller.save + seller.set-default）。执行前复述当前值与目标值；执行后 default-rate.get 回读。

```json
{
  "capability": "ops.trade.invoice.goods-tax.default-rate.save",
  "input": { "taxRate": 0.13 },
  "summary": "设置默认税率"
}
```
