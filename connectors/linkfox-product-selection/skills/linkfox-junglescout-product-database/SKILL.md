---
name: linkfox-junglescout-product-database
description: Jungle Scout产品数据库多条件筛选，支持按品类、价格、销量、收入、评论、评分、重量、BSR排名、LQS、卖家类型等维度筛选亚马逊商品，覆盖10个站点。当用户提到亚马逊选品、产品数据库筛选、BSR排名筛选、品类选品、高评分低竞争选品、FBA选品、亚马逊商品搜索、产品筛选、Amazon product database, product research, product filtering, BSR rank filter, category product search, niche product finder, FBA product search, Amazon product discovery, low competition products, Jungle Scout product database时触发此技能。即使用户未明确提及"Jungle Scout"或"产品数据库"，只要其需求涉及按多条件筛选亚马逊商品或发现潜力产品，也应触发此技能。
---

# 产品基本信息查询

## 基本信息

- **业务工具名**：`/tool-jungle-scout/product-database/query`
- **所属分组**：Jungle Scout · 亚马逊关键词与销量
- **功能说明**：产品基本信息查询：POST product_database_query，支持多条件筛选与内部自动分页


## 何时使用

当用户意图与“产品基本信息查询”匹配，或需要以下能力时使用本工具：产品基本信息查询：POST product_database_query，支持多条件筛选与内部自动分页

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `sort` | `string` | 否 | 最长 1000；示例：`name`, `-name`, `category`, `-category`, `revenue`, `-revenue`, `sales`, `-sales` | 排序字段。可选值: name, -name, category, -category, revenue, -revenue, sales, -sales, price, -price, rank, -rank, reviews, -reviews, lqs, -lqs, sellers, -sellers。默认: name |
| `maxLqs` | `integer` | 否 |  | 最高列表质量分 LQS(1-10) |
| `maxNet` | `number` | 否 |  | 最高净利润(价减FBA费等) |
| `minLqs` | `integer` | 否 |  | 最低列表质量分 LQS(1-10) |
| `minNet` | `number` | 否 |  | 最低净利润(价减FBA费等) |
| `maxRank` | `integer` | 否 |  | 最高 BSR 排名 |
| `minRank` | `integer` | 否 |  | 最低 BSR 排名 |
| `maxPrice` | `number` | 否 |  | 最高价格 |
| `maxSales` | `integer` | 否 |  | 最高月销量估算 |
| `minPrice` | `number` | 否 |  | 最低价格 |
| `minSales` | `integer` | 否 |  | 最低月销量估算 |
| `maxRating` | `number` | 否 |  | 最高星级评分(1.0-5.0) |
| `maxWeight` | `number` | 否 |  | 最大重量(磅) |
| `minRating` | `number` | 否 |  | 最低星级评分(1.0-5.0) |
| `minWeight` | `number` | 否 |  | 最小重量(磅) |
| `needCount` | `integer` | 否 |  | 需要返回的总条数(系统内部自动分页拉取) |
| `categories` | `string` | 否 | 最长 1000；示例：`Electronics`, `Baby,Toys & Games` | 主类目筛选，多值逗号分隔；为空表示不限。须与所选 marketplace 下官方类目名称完全一致。 us marketplace: Appliances,Arts, Crafts & Sewing,Automotive,Baby,Beauty & Personal Care,Camera & Photo,Cell Phones & Accessories,Clothing, Shoes & Jewelry,Computers & Accessories,Electronics,Grocery & Gourmet Food,Health & Household,Home & Kitchen,Industrial & Scientific,Kitchen & Dining,Musical Instruments,Office Products,Patio, Lawn & Garden,Pet Supplies,Software,Sports & Outdoors,Tools & Home Improvement,Toys & Games,Video Games uk marketplace: Automotive,Baby Products,Beauty,Business, Industry & Science,Fashion,Computers & Accessories,DIY & Tools,Electronics & Photo,Garden,Grocery,Health & Personal Care,Home & Kitchen,Jewellery,Large Appliances,Lighting,Luggage,Musical Instruments & DJ,PC & Video Games,Pet Supplies,Shoes & Bags,Sports & Outdoors,Stationery & Office Supplies,Toys & Games,Watches ca marketplace: Automotive,Baby,Beauty & Personal Care,Clothing & Accessories,Electronics,Grocery & Gourmet Food,Health & Personal Care,Industrial & Scientific,Jewelry,Luggage & Bags,Musical Instruments, Stage & Studio,Office Products,Patio, Lawn & Garden,Pet Supplies,Shoes & Handbags,Sports & Outdoors,Tools & Home Improvement,Toys & Games,Watches de marketplace: Auto & Motorrad,Baby,Baumarkt,Beauty,Bekleidung,Beleuchtung,Bücher,Bürobedarf & Schreibwaren,Computer & Zubehör,DVD & Blu-ray,Drogerie & Körperpflege,Elektro-Großgeräte,Elektronik & Foto,Fremdsprachige Bücher,Games,Garten,Gewerbe, Industrie & Wissenschaft,Haustier,Kamera & Foto,Koffer, Rucksäcke & Taschen,Küche, Haushalt & Wohnen,Lebensmittel & Getränke,Musikinstrumente & DJ-Equipment,Schmuck,Schuhe & Handtaschen,Software,Spielzeug,Sport & Freizeit,Uhren fr marketplace: Animalerie,Auto & Moto,Bagages,Beauté & Parfum,Bijoux,Bricolage,Bébé et Puériculture,Chaussures & Sacs,Commerce, Industrie & Science,Cuisine & Maison,DVD & Blu-ray,Epicerie,Fournitures de bureau,Gros électroménager,High-tech,Hygiène & Santé,Informatique,Instruments de musique & Sono,Jardin,Jeux & Jouets,Jeux vidéo,Livres,Livres anglais & étrangers,Logiciels,Luminaires & Eclairage,Montres,Sports & Loisirs,Vêtements in marketplace: Baby,Baby Products,Bags, Wallets & Luggage,Beauty,Books,Car & Motorbike,Clothing & Accessories,Electronics,Gift Cards,Grocery & Gourmet Foods,Health & Personal Care,Home & Kitchen,Industrial & Scientific,Jewellery,Movies & TV Shows,Music,Musical Instruments,Office Products,Pet Supplies,Shoes & Handbags,Software,Sports, Fitness & Outdoors,Toys & Games,Video Games,Watches it marketplace: Abbigliamento,Alimentari e cura della casa,Auto e Moto,Bellezza,Buoni regalo,CD e Vinili,Casa e cucina,Commercio, Industria e Scienza,Elettronica,Fai da te,Film e TV,Giardino e giardinaggio,Giochi e giocattoli,Gioielli,Illuminazione,Informatica,Kindle Store,Libri,Libri in altre lingue,Orologi,Prima infanzia,Salute e cura della persona,Scarpe e borse,Software,Sport e tempo libero,Valigeria,Videogiochi es marketplace: Apps y Juegos,Bebé,Belleza,Bricolaje y herramientas,Coche y moto,Deportes y aire libre,Electrónica,Equipaje,Hogar y cocina,Iluminación,Industria, empresas y ciencia,Informática,Instrumentos musicales,Jardín,Joyería,Juguetes y juegos,Libros,Oficina y papelería,Películas y TV,Relojes,Ropa,Salud y cuidado personal,Software,Tienda Kindle,Videojuegos,Zapatos y complementos mx marketplace: Bebé,Deportes y Aire Libre,Electrónicos,Herramientas y Mejoras del Hogar,Hogar y Cocina,Industria, Empresas y Ciencia,Instrumentos Musicales,Juguetes y Juegos,Libros,Música,Oficina y papelería,Ropa, Zapatos y Accesorios,Salud, Belleza y Cuidado Personal,Software,Tienda Kindle,Videojuegos jp marketplace: DIY・工具・ガーデン,おもちゃ,シューズ&バッグ,ジュエリー,スポーツ&アウトドア,ドラッグストア,ビューティー,ベビー&マタニティ,ペット用品,ホビー,ホーム&キッチン,大型家電,家電&カメラ,文房具・オフィス用品,服&ファッション小物,産業・研究開発用品,腕時計,車&バイク,食品・飲料・お酒 |
| `maxRevenue` | `number` | 否 |  | 最高月收入估算 |
| `maxReviews` | `integer` | 否 |  | 最多评论数 |
| `maxSellers` | `integer` | 否 |  | 最多卖家数 |
| `minRevenue` | `number` | 否 |  | 最低月收入估算 |
| `minReviews` | `integer` | 否 |  | 最少评论数 |
| `minSellers` | `integer` | 否 |  | 最少卖家数(FBA+FBM+AMZ合计) |
| `marketplace` | `string` | 是 | 最长 1000；示例：`us`, `uk`, `de`, `in`, `ca`, `fr`, `it`, `es` | 目标市场代码 |
| `sellerTypes` | `string` | 否 | 最长 1000；示例：`fba,fbm` | 卖家履约类型，多值逗号分隔；可选 amz(亚马逊), fba, fbm |
| `maxUpdatedAt` | `string` | 否 | 最长 1000；示例：`2020-09-29` | 产品最晚更新日期(YYYY-MM-DD) |
| `minUpdatedAt` | `string` | 否 | 最长 1000；示例：`2020-09-28` | 产品最早更新日期(YYYY-MM-DD) |
| `productTiers` | `string` | 否 | 最长 1000；示例：`standard`, `oversize,standard` | 产品规格层级，多值逗号分隔；可选 oversize, standard |
| `excludeKeywords` | `string` | 否 | 最长 1000；示例：`sushi,ramen` | 标题排除的关键词或ASIN，多值逗号分隔(单条最长50字符，最多100项) |
| `includeKeywords` | `string` | 否 | 最长 1000；示例：`pasta,spaghetti` | 标题包含的关键词或ASIN，多值逗号分隔(单条最长50字符，最多100项) |
| `excludeTopBrands` | `boolean` | 否 | 示例：`false`, `true` | 是否排除头部品牌 |
| `excludeUnavailableProducts` | `boolean` | 否 | 示例：`false`, `true` | 是否排除缺货/不可售产品 |


## MCP 调用示例

向以下地址发起 HTTP `POST`：

```text
https://mcp-tool-gateway.linkfox.com/mcp/any-tool
```

请求体：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "/tool-jungle-scout/product-database/query",
    "arguments": {
      "marketplace": "us"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `costToken` | `integer` | 否 |  | 消耗token |
| `productDatabaseList` | `array<object>` | 否 |  | 产品库查询结果列表 |

### 嵌套输出结构：`productDatabaseList`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `id` | `string` | 否 |  | 产品唯一标识(市场/ASIN) |
| `type` | `string` | 否 |  | 响应资源类型(固定 product_database_result) |
| `brand` | `string` | 否 |  | 品牌名称 |
| `price` | `number` | 否 |  | 当前售价 |
| `title` | `string` | 否 |  | 产品完整标题 |
| `rating` | `number` | 否 |  | 平均评分(1-5星) |
| `eanList` | `array<any>` | 否 |  | EAN 列表 |
| `reviews` | `integer` | 否 |  | 评论总数 |
| `upcList` | `array<any>` | 否 |  | UPC 列表 |
| `category` | `string` | 否 |  | 产品主要类别 |
| `gtinList` | `array<any>` | 否 |  | GTIN 列表 |
| `imageUrl` | `string` | 否 |  | 产品主图链接 |
| `isParent` | `boolean` | 否 |  | 是否父ASIN |
| `isbnList` | `array<any>` | 否 |  | ISBN 列表 |
| `variants` | `object` | 否 |  |  |
| `isVariant` | `boolean` | 否 |  | 是否变体ASIN |
| `updatedAt` | `string` | 否 |  | 数据最后更新时间 |
| `parentAsin` | `string` | 否 |  | 父产品ASIN |
| `sellerType` | `string` | 否 |  | 卖家履约类型(FBA/FBM/AMZ) |
| `weightUnit` | `string` | 否 |  | 重量单位 |
| `widthValue` | `number` | 否 |  | 包装宽度 |
| `buyBoxOwner` | `string` | 否 |  | 购物车(Buy Box)拥有者 |
| `heightValue` | `number` | 否 |  | 包装高度 |
| `isAvailable` | `boolean` | 否 |  | 是否有库存/可购买 |
| `lengthValue` | `number` | 否 |  | 包装长度 |
| `productRank` | `integer` | 否 |  | 类别内销售排名(BSR) |
| `weightValue` | `number` | 否 |  | 重量数值 |
| `feeBreakdown` | `object` | 否 |  |  |
| `isStandalone` | `boolean` | 否 |  | 是否独立ASIN |
| `breadcrumbPath` | `string` | 否 |  | 分类面包屑路径 |
| `dimensionsUnit` | `string` | 否 |  | 尺寸单位 |
| `variantReviews` | `integer` | 否 |  | 变体评论数(仅变体时有值) |
| `numberOfSellers` | `integer` | 否 |  | 卖家数量 |
| `subcategoryRanks` | `array<object>` | 否 |  | 子类目排名列表 |
| `dateFirstAvailable` | `string` | 否 |  | 首次上架日期(YYYY-MM-DD) |
| `buyBoxOwnerSellerId` | `string` | 否 |  | 购物车卖家ID |
| `listingQualityScore` | `integer` | 否 |  | 列表质量评分(LQS) |
| `approximate30DayRevenue` | `number` | 否 |  | 近30天收入估算(USD) |
| `approximate30DayUnitsSold` | `integer` | 否 |  | 近30天销量估算 |
| `dateFirstAvailableIsEstimated` | `boolean` | 否 |  | 首次上架日期是否为估算值 |

### 嵌套输出结构：`productDatabaseList.feeBreakdown`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `fbaFee` | `number` | 否 |  | FBA 费用 |
| `totalFees` | `number` | 否 |  | 费用合计 |
| `referralFee` | `number` | 否 |  | 推荐费 |
| `variableClosingFee` | `number` | 否 |  | 变动结算费 |

### 嵌套输出结构：`productDatabaseList.subcategoryRanks`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `id` | `string` | 否 |  | 子类目节点ID |
| `rank` | `number` | 否 |  | 在该子类目中的排名 |
| `subcategory` | `string` | 否 |  | 子类目名称 |

## 响应处理建议

1. 先检查 JSON-RPC 外层是否包含 `error`。
2. 成功时读取 `result`，并继续解析其中的 `content`、`data`、`products`、`items` 或其他业务字段。
3. 如果响应为 `text/event-stream`，按 SSE 事件读取 `data:` 内容，再解析 JSON。
4. 保留分页字段、总数、失败明细及 `costToken`。
5. 向用户输出分析结论，不要直接倾倒大段原始 JSON。

## 原始 Schema

原始的Input Schema 和 Output Schema 参考 references/schema.md

## 解决认证和积分问题

异常情况：未配置 `LINKFOX_AGENT_API_KEY` 和 `LINKFOXAGENT_API_KEY`；响应 401 或 402；消息含"积分余额不足/quota exceeded/insufficient balance/套餐到期/需充值"等。

措施：优先用 skill 内 onboarding.md 引导；找不到则加载 /linkfox-onboarding skill。 根据它的指引操作。

**注意**：你是workbuddy，并且渠道是workbuddy，使用linkfox-onboarding登录注册时**必须**传递channel为 workbuddy。这非常重要！
