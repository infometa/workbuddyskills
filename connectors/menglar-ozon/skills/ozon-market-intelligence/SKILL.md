---
name: ozon-market-intelligence
description: 使用 menglar-ozon MCP 分析 OZON 类目、商品、店铺、品牌、关键词和大盘趋势。适用于市场规模评估、类目选品、竞品研究、热销榜与中国专区分析、店铺/品牌诊断以及关键词趋势分析。
description_zh: 使用 menglar-ozon MCP 分析 OZON 类目、商品、店铺、品牌、关键词和大盘趋势。
description_en: Analyze OZON categories, products, shops, brands, keywords, and market trends using menglar-ozon MCP.
version: "1.0.0"
---

# OZON Market Intelligence

通过 `menglar-ozon` 提供的只读工具完成 OZON 市场数据查询和分析。

## 核心规则

1. **先查 ID，再做深度分析。** 类目分析先获取 `categoryId`；三级类目还必须保留并传递 `typeId`。商品、店铺、关键词等先通过列表或榜单获取对应 ID。
2. **三级类目必须带 typeId。** 三级类目可能存在多个类型；详情、榜单、趋势等后续查询需同时传 `categoryId` 与 `typeId`。
3. **尊重数据账期。** 用户未指定且工具允许默认时，使用最近可用账期，并在结论中注明实际账期；不把当前自然日假设为已有完整数据。
4. **账期格式。**

   - 近 7 天 / 近 28 天：`yyyy-MM-dd`

   - 自然月：`yyyy-MM`

   - 季度：`yyyy-Qn`

   - 年度：`yyyy`

   - 关键词周榜：`yyyy-MM-dd`（表示该日起近 7 天搜索汇总）
5. **只使用工具支持的周期。** 大盘趋势仅支持日（`DAY`）和自然月；店铺详情与店铺趋势默认近 28 天，趋势范围最多约 90 天；品牌商品固定近 28 天。
6. **控制范围。** 分页从 `pageNo: 1`、`pageSize: 15` 开始；批量查询商品 / 品牌 / 店铺 / 关键词单次最多 10 个；先小范围验证条件再扩大。
7. **榜单默认 DESC。** 按用户关注指标选择 `GMV`、`SALES`、`PRICE` 等；关键词可按搜索指数、订单金额、已订购商品数等排序。
8. **类目语言。** 支持 `CH` / `RU` / `EN`，默认 `CH`。
9. **不编造数据。** 只根据 MCP 实际返回总结；调用失败、无权限、无数据时明确说明。
10. **默认只读。** 本插件仅用于查询与分析，不声称能够修改 OZON 店铺、商品或广告设置。
11. **保护凭据。** 不在回复中打印、复述或记录访问令牌。
12. **工具名大小写。** 若客户端将工具名改为全小写，按工具含义和参数结构匹配。

## 推荐工作流

### 1. 大盘与类目选品

1. 用 `queryLevel1Categories` 获取一级类目。
2. 按需用 `queryLevel2Categories`、`queryLevel3Categories` 逐级定位；保留三级返回的 `typeId`。
3. 使用 `queryHotCategoryRankings` 或 `queryCategoryDetail` 分析类目表现。
4. 使用 `queryCategoryTrendSnapshots`、`queryMarketTrendSnapshots` 分析趋势和大盘。
5. 进一步用商品、店铺、品牌、关键词工具验证竞争度和需求。

不要只凭类目名称猜测 `categoryId` 或 `typeId`。

### 2. 商品与榜单分析

- 使用 `queryHotProductRankings` 查询全站热销商品。

- 使用 `queryCnZoneProductRankings` 查询中国专区商品。

- 获得商品 ID 后，使用 `queryProductDetails` 批量查询详情。

- 使用 `queryProductTrendSnapshots` 分析销售趋势。

- 使用 `queryProductInfoTracks` 追踪价格、评分、评论、跟卖等（默认近 30 天，最多约 90 天）。

- 使用 `queryProductTrafficKeywords` 分析自然流量词、主题标签和广告流量词。

对“爆品”“潜力品”等判断，应说明使用的指标、账期、类目和筛选条件。

### 3. 关键词分析

- 使用 `queryHotKeywordRankings` 获取热搜词及榜单。

- 使用 `queryKeywordDetails` 查询词详情（关键词 ID，最多 10 个）。

- 使用 `queryKeywordTrendSnapshots` 分析趋势（周榜最多约 90 天）。

- 使用 `queryKeywordRelatedProducts` 查看关联商品。

区分搜索指数、曝光、转化、供需比、订单金额等指标，不把相关性表述成因果关系。

### 4. 品牌分析

- 优先使用 `queryHotSaleBrandRankings` 查找热销品牌（按所选类目下品牌销售；不传类目则查全部）。

- 使用 `queryBrandDetails` 获取详情（品牌名称，最多 10 个）。

- 使用 `queryBrandProducts` 分析关联商品（近 28 天）。

- `queryTopBrandRankings` 已废弃，勿主动使用。

使用接口返回的规范品牌名，避免自行改写。

### 5. 店铺分析

- 使用 `queryHotShopRankings` 找到目标店铺（可筛级别、跨境/本土、开店周期、动销率等）。

- 使用 `queryShopDetails` 获取详情（店铺 ID，最多 10 个）。

- 使用 `queryShopTrendSnapshots` 查询趋势。

- 使用 `queryShopItemDetails` 分析店铺商品。

## 工具目录

### 类目与大盘

- `queryLevel1Categories`：查询一级类目

- `queryLevel2Categories`：查询二级类目

- `queryLevel3Categories`：查询三级类目（含 `typeId`）

- `queryHotCategoryRankings`：查询类目热销榜

- `queryCategoryDetail`：查询类目详情

- `queryCategoryTrendSnapshots`：查询类目趋势快照

- `queryMarketTrendSnapshots`：查询大盘趋势快照

### 商品

- `queryHotProductRankings`：查询热销商品榜

- `queryCnZoneProductRankings`：查询中国专区商品榜

- `queryProductDetails`：批量获取商品详情

- `queryProductTrendSnapshots`：查询商品趋势快照

- `queryProductInfoTracks`：查询商品信息追踪

- `queryProductTrafficKeywords`：查询商品流量词

### 关键词

- `queryHotKeywordRankings`：查询热搜词榜

- `queryKeywordDetails`：批量获取关键词详情

- `queryKeywordTrendSnapshots`：查询关键词趋势快照

- `queryKeywordRelatedProducts`：查询关键词关联商品

### 品牌

- `queryHotSaleBrandRankings`：查询品牌热销榜（推荐）

- `queryBrandDetails`：批量获取品牌详情

- `queryBrandProducts`：查询品牌关联商品

- `queryTopBrandRankings`：已废弃，请改用热销榜

### 店铺

- `queryHotShopRankings`：查询店铺热销榜

- `queryShopDetails`：批量获取店铺详情

- `queryShopTrendSnapshots`：查询店铺趋势快照

- `queryShopItemDetails`：查询店铺商品明细

## 限制与数据解释

- 列表工具通常每页最多 15 条。

- 销售额默认按俄罗斯卢布理解，除非返回结果另有说明。

- 百分比保持工具返回形式，不擅自转换为小数比例。

- 趋势比较必须使用相同统计口径的账期。

- 必须区分“无数据”与数值为零。

## 认证、计费与充值提示

- Connector 授权后，远程 MCP 请求头注入 `${ACCESS_TOKEN}`；不要让用户在聊天中发送令牌。

- `initialize` / `initialized` / `tools/list` 不扣费；`tools/call` 按次扣除 `API_CALL` 额度。

- HTTP `401` / `403` 属于认证或权限问题，不得误报为余额不足。

- HTTP `402` 且 JSON-RPC `code: -32002` 判定为额度不足：立即停止自动重试，不改用其他工具规避计费。

提示用户：

> 萌啦 OZON API 调用额度已用完，需要充值或补充额度后才能继续查询。

## 输出规范

- 开头注明：数据周期、实际账期、类目（含层级与 `typeId`）、筛选条件和排序依据。

- 排名结果优先用表格展示，并保留接口返回的单位和币种。

- 趋势结论至少给出起止值或变化幅度；不能从单点数据推导趋势。

- 结论与事实分开：先列数据，再写洞察和建议。

- 若结果分页，注明当前页、页大小以及是否已覆盖全部结果。

- 保留后续下钻所需的类目、商品、关键词、品牌或店铺 ID。

- 若数据为空，先检查类目 ID/`typeId`、账期、周期类型和筛选条件，再解释无法得出结论。

