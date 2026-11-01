---
name: aike-product
display_name: 商品查询
display_name_en: Products
description: 查询企业内部商品库：按名称/内部编号/品牌/规格型号关键词检索自家商品档案，支持标签、分类与上架状态过滤，返回品牌、规格型号、分类路径、起订量、折扣说明、标签等档案字段。当用户说"查一下 LED 产品资料""我有哪些太阳能产品""这个产品参数多少""看下在售的商品"时触发。
description_zh: 按关键词/标签/分类/上架状态检索企业内部商品库，返回商品档案字段。
description_en: Search the in-house product catalog by keyword, tags, category or on-shelf status.
category: sales-commerce
version: 1.3.0
author: AI销客
---

# 商品查询

当用户需要查询商品（找产品、看参数、查在售款式、推荐产品）时，按以下步骤执行：

## 执行步骤

1. **确认工具可用**：本技能依赖 gsales 连接器提供的 `search_products` 工具。当前环境没有该工具时，引导用户先安装并连接「外贸销客」连接器，连接后再继续；**不要在无工具环境编造商品数据**。
2. **明确检索词**：从用户话里取关键词（匹配 商品名称 / 内部编号 / 品牌 / 规格型号）。用户没给任何检索词时，先问一句"想查哪个产品或品牌？"再查；用户说"在售 / 已上架"时加 `status: "1"`。
3. **调用 `search_products`**：默认用 `keyword` 起步；仅在用户明确给出标签名或分类 id 时才附加 `tags` / `categoryId`。默认每页 10 条，不够时翻页。
4. **呈现结果**：列表卡逐项给出商品档案——商品名 + 品牌 / 规格型号 / 分类路径 + `price` 与 `currencyLabel` 字段（**原样引用，不要拆分、计算或换算**）+ 起订量（`moq`）+ 折扣说明 + 标签 + 上架状态。
5. **衔接后续**：用户想记录意向商品，可衔接「新增客户」技能把商品名写进客户 `product_tags`（产品偏好标签）。

## 结果为空或异常时

- **空结果**：先放宽条件重试一次（去掉 `tags` / `categoryId` 只留 `keyword`）；仍为空则如实告知"商品库没有匹配的商品"，建议换关键词再试，**不要编造商品**。
- **401**（授权无效/过期/已断开）：引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）。
- **403**（无权限）：多为用户角色未配置 `pc:products` 权限码，联系管理员开通。

## 工具参考：`search_products`

- **用途**：检索企业内部商品库（查商品档案、核对在售款式）
- **入参**：
  - `keyword`（string，可选）：关键词，模糊匹配 商品名称 / 内部编号 / 品牌 / 规格型号
  - `tags`（string[]，可选）：标签筛选（匹配任一标签）
  - `categoryId`（string uuid，可选）：分类 ID，传一级分类 id 会包含其下所有二级分类的商品
  - `status`（string，可选）：上架状态，`"1"`=已上架 / `"0"`=下架（**字符串枚举**，不要传数字或布尔；不传返回全部）
  - `page`（int，默认 1）/ `pageSize`（int，默认 10，上限 50）/ `full`（boolean，默认 `false`，true 返回后端全量字段）
- **返回**：`{ total, page, pageSize, items[] }`，`items` 每项：
  - `id` / `name`（商品名）/ `productCode`（内部编号）/ `brand`（品牌）
  - `categoryName`（分类名）/ `categoryPath`（完整分类路径，如 `太阳能/组件`）/ `specs`（规格型号）
  - `price`（文本格式字段，由维护人员自由填写，可能含区间/单位/币种）/ `currencyLabel`（币种标签，如 美元 USD）
  - `moq`（起订量）/ `discountNote`（折扣说明）/ `tags`（标签）/ `status`（`"1"` 上架 / `"0"` 下架）/ `updatedAt`

## 字段口径说明

- `price` 与 `currencyLabel` 是商品档案里维护人员填写的文本字段，向用户展示时**原样引用**即可，不要自行拆分、计算或换算币种。
- 更细的档案字段（成本备注 / 参数组 / 落地页等）传 `full: true` 获取，默认精简口径已覆盖日常查询所需。
