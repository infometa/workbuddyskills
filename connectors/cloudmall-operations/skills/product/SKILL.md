---
name: product
display_name: 云MALL商品
display_name_en: CloudMall Products
description: 云MALL商品域查询。当用户要求查商品、商品列表、在售/下架/隐藏商品、按类目或品牌筛选商品、查看商品详情、商品租户库存时使用。
description_zh: 查询当前授权租户的云MALL商品：商品列表、状态筛选、商品详情与租户聚合库存。
description_en: Query CloudMall products for the authorized tenant: product list, status filtering, details, and tenant-level stock.
allowed-tools: cloudmall_query
version: 0.1.0
author: 云MALL
---

# 云MALL商品域

以当前运营账号的实时接口权限与数据权限，查询云MALL商品（SPU）数据。第一期提供 SPU 分页查询与 SPU 详情两项能力，本 Skill 随域内能力扩展持续更新。

## 域内能力与参数

### ops.product.spu.search — SPU 分页查询

| 参数 | 必填 | 说明 |
|---|---|---|
| pageNum / pageSize | 是 | 分页参数；pageSize 上限 100，默认建议 20 |
| keyword | 否 | 商品关键词 |
| productType | 否 | 商品类型：PHYSICAL / SERVICE / STUDY_TOUR |
| categoryCodes | 否 | 类目编码数组（字符串，1~10 个） |
| brandId | 否 | 品牌 ID，十进制字符串 |
| statusTab | 否 | 状态页签：ALL / ON_SALE / OFF_SALE / HIDDEN。不存在 SOLD_OUT（MCP 层直接拒绝，不会静默按 ALL 处理） |
| auditStatus | 否 | 审核状态数组：NONE / REVIEWING / APPROVED / REJECTED |
| createSource | 否 | 创建来源：ADMIN / GUIDE_PUBLISH / SUPPLIER |
| storeId | 否 | 门店 ID，十进制字符串 |

### ops.product.spu.detail — SPU 详情

| 参数 | 必填 | 说明 |
|---|---|---|
| id | 是 | SPU ID，正数十进制字符串 |

## 调用流程（固定）

1. 查询意图不明确时先向用户追问（类目、状态、类型等）。
2. search → 唯一命中 → 用返回的 id 调 detail 补全；多命中 → 先向用户确认目标商品再继续。

## 调用示例

```json
{"capability": "ops.product.spu.search", "input": {"pageNum": 1, "pageSize": 20, "statusTab": "ON_SALE", "keyword": "研学"}, "summary": "查询在售的研学商品"}
```

```json
{"capability": "ops.product.spu.detail", "input": {"id": "2058365707555589633"}, "summary": "查询商品详情"}
```

## 输出

统一成功结构 `{ capability, data, traceId, truncated }`。search 的 data 为分页对象（records/total/pageNum/pageSize/totalPages/hasMore）；detail 为单个商品对象。字段以服务端 allowlist 为准：列表含 spuId/spuName/subtitle/productType/categoryName/brandName/price/minPrice/maxPrice/totalStock/remainStock/totalSales 等，详情含 id/spuId/spuName/auditStatus/priceDescription 等。

库存口径：仅 Java 返回的租户聚合库存（totalStock/remainStock）。不得向用户承诺门店可售库存；第一期不支持门店库存明细查询。

## 翻页与 truncated

truncated=true 表示响应预算触发精确重定位：MCP 已按原 offset 返回较小完整页。必须改用 truncation 中的 effectivePageNum/effectivePageSize/nextPageNum 继续翻页，不能沿用原 pageNum/pageSize。

## 错误恢复

- AUTH_REQUIRED：授权已失效，提示用户在 WorkBuddy 重新连接，不要求粘贴任何 Token。
- PERMISSION_DENIED：当前账号没有该接口权限，向用户说明后停止，不尝试其他权限码或接口。
- INPUT_INVALID：按参数表检查字段与枚举（例如 statusTab 没有 SOLD_OUT，正确值是 ALL/ON_SALE/OFF_SALE/HIDDEN），修正后重试。
- UPSTREAM_TIMEOUT：稍后重试，并缩小查询范围（增加 keyword 或减小 pageSize）。

## 禁止事项与边界

- 不得询问或传入租户、账号、Token、接口路径、权限码等身份/路由信息；身份由连接授权自动绑定。
- Snowflake ID（brandId/storeId/id）一律按十进制字符串处理，禁止转成数字。
- 第一期本域仅开放只读查询：门店库存明细、物流、售后、报表及任何写操作（上下架/编辑/审核/发布等）均不支持。用户提出时明确说明不支持，不得尝试绕过。
