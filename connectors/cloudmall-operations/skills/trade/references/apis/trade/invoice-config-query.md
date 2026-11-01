# 交易域 — 发票配置契约（查询侧）

> 概念知识：`references/domains/trade-concepts.md`；平台启停/销方/税收写操作见 `invoice-config-action.md`；运营流程：`references/flows/trade-finance.md`
> 本页是租户级开票基础配置的读取面：平台、销方、税收分类编码、商品类目-税收映射、全局默认税率。所有 ID 为十进制字符串。
> ⛔ **平台创建与凭据配置（`platform/save`，含 appKey/appSecret）不在开放范围**——敏感凭据面，走管理后台；开放面是列表读取、启停与默认切换（见 action 文件）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 invoice.platform.list · invoice.seller.list · invoice.tax-category.list · invoice.goods-tax.list · invoice.goods-tax.default-rate.get

---

## ✅ 开票平台列表 — ops.trade.invoice.platform.list

用途：查询开票平台配置列表（🟢）。

入参：无，传 `{}`。结果来源 `InvoicePlatformConfigVO` 数组：`id`、`platformCode` / `platformName`、`appKey`、`appSecret`（**脱敏：仅前 4 位+****，不能作为写参数回传**）、`merchantNo`（商户号）、`apiBaseUrl` / `tokenUrl` / `callbackUrl`、`extraConfig`（**平台扩展配置 JSON 文本**：可能为空；运行时按键消费，如百望的 `username`/`password`/`userSalt`、沙箱调试 `accessToken`、开票人 `drawer`、诺诺 `invoiceLine`——**可能含凭据原文，不得向用户复述其内容，也不得作为任何写操作入参**）、`status`（`1` 启用 / `0` 禁用）、`isDefault`（`1` 默认）、`createdTime` / `updatedTime`（`yyyy-MM-dd HH:mm:ss`）。

```json
{
  "capability": "ops.trade.invoice.platform.list",
  "input": {},
  "summary": "查询开票平台配置"
}
```

---

## ✅ 销方列表 — ops.trade.invoice.seller.list

用途：查询销方（开票方）信息列表（🟢），含默认销方标记。

入参：无，传 `{}`。结果来源 `InvoiceSellerVO` 数组：`id`、`sellerName`、`taxpayerNo`（纳税人识别号）、`taxpayerType`、`address` / `phone` / `bankName` / `bankAccount`、`status`、`isDefault`、`createdTime` / `updatedTime`。

```json
{
  "capability": "ops.trade.invoice.seller.list",
  "input": {},
  "summary": "查询销方信息"
}
```

---

## ✅ 税收分类编码树 — ops.trade.invoice.tax-category.list

用途：查询税收分类编码（商品和服务税收分类）树（🟢）。

入参：无，传 `{}`。结果来源 `InvoiceTaxCategoryVO` 列表（树形）：`id`、`taxCategoryCode`（编码）、`taxCategoryName`、`parentCode`、`level`、`taxRate`（小数，如 `0.13`）、`preferredPolicy`（优惠政策）、`description`、`status`、`children[]`（子分类递归嵌套）。编码是商品税收映射的 `taxCategoryCode` 取值来源。

```json
{
  "capability": "ops.trade.invoice.tax-category.list",
  "input": {},
  "summary": "查询税收分类编码"
}
```

---

## ✅ 商品税收映射列表 — ops.trade.invoice.goods-tax.list

用途：查询商品类目与税收分类的映射（🟢，开票时按商品类目自动匹配税收编码与税率）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| keyword | 字符串 | 否 | 类目名称/编码模糊筛选 |

结果来源 `InvoiceGoodsTaxMappingVO` 数组：`id`、`goodsCategoryId` / `goodsCategoryName` / `goodsCategoryPath`、`taxCategoryCode` / `taxCategoryName`、`taxRate`、`preferredPolicy` / `preferredPolicyFlag`、`zeroTaxFlag`（零税率标记）、`invoiceItemName`（票面商品名）、`priority`（匹配优先级）、`status`、`createdTime` / `updatedTime`。

`goodsCategoryId` 来源于商品域类目（跨域能力：商品类目查询），不自造。

```json
{
  "capability": "ops.trade.invoice.goods-tax.list",
  "input": {},
  "summary": "查询商品税收映射"
}
```

---

## ✅ 全局默认税率查询 — ops.trade.invoice.goods-tax.default-rate.get

用途：查询全局默认税率（无类目映射时开票使用的兜底税率）。

入参：无，传 `{}`。结果来源 `BigDecimal`（小数税率，如 `0.13`）。

```json
{
  "capability": "ops.trade.invoice.goods-tax.default-rate.get",
  "input": {},
  "summary": "查询默认税率"
}
```
