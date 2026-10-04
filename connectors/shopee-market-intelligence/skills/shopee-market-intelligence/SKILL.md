---
name: shopee-market-intelligence
description: 使用 Shopee MCP 分析站点、类目、商品、店铺、品牌、趋势和热搜词。适用于市场规模评估、类目选品、竞品研究、榜单分析、店铺/品牌诊断以及关键词趋势分析。
---

# Shopee Market Intelligence

通过 `shopee-mcp` 提供的只读工具完成 Shopee 市场数据查询和分析。

## 核心规则

1. **先确认站点。** 支持的常用站点代码包括：`tw`、`my`、`id`、`th`、`ph`、`sg`、`vn`、`br`。用户只给出国家或地区名称时，先转换为对应站点代码；无法确定时再询问。
2. **先查 ID，再做深度分析。** 类目分析先获取 `categoryId` 和 `level`；商品、店铺、热搜词等对象分析先通过列表或榜单获取对应 ID。
3. **尊重数据时间。** 数据通常为 T+1；优先使用接口可用的最新数据日期，不把当前自然日假设为已经有完整数据。
4. **日期格式。** `date`、`startDate`、`endDate`、`timest` 通常使用 `yyyy-MM-dd`。若接口 schema 或错误信息给出更具体格式，以工具声明为准。
5. **控制范围。** 趋势查询使用满足问题所需的最短合理时间范围；列表和榜单使用分页，先取小页验证条件，再按需扩大。
6. **不编造数据。** 只根据 MCP 实际返回进行总结；调用失败、无权限、无数据或字段含义不清楚时，明确说明。
7. **默认只读。** 本插件仅用于查询与分析，不声称能够修改 Shopee 店铺、商品或广告设置。
8. **保护凭据。** 不在回复中打印、复述或记录用户的 API Key。

## 推荐工作流

### 1. 站点概览

- 使用 `queryShopeeSiteDate` 查询站点一段时间内的基础数据。
- 对返回的销售额、销量、商品量、店铺量等指标做同比/环比时，先确认接口是否提供可比周期。
- 如果用户要求“最新”，先从接口返回中识别最新可用日期，并在结论中注明该日期。

### 2. 类目选品分析

1. 用 `queryShopeeLevel1Categories` 获取一级类目。
2. 按需用 `queryShopeeLevel2Categories`、`queryShopeeLevel3Categories` 逐级定位类目 ID。
3. 使用 `queryShopeeCatData` 或 `queryShopeeSubCatData` 补充类目列表。
4. 使用 `queryShopeeCatRanking`、`queryShopeeCatTrend`、`queryShopeeCatPriceDistribute` 分析排名、趋势和价格带。
5. 进一步使用商品、店铺、品牌、热搜词工具验证竞争度和需求。

不要只凭类目名称猜测 `categoryId` 或 `level`。

### 3. 商品与榜单分析

- 使用 `queryShopeeItemData` 筛选商品列表。
- 使用 `queryShopeeItemRanking` 查询指定日期、周期和类目的商品榜单。
- 获得商品 ID 后，使用 `queryShopeeItemDetailBatch` 批量查询详情。
- 使用 `queryShopeeItemTrend` 或 `queryShopeeItemTrendDetail` 分析时间趋势。
- 使用 `queryShopeeItemHotWord` 分析商品关联热搜词。

对“爆品”“潜力品”等判断，应说明使用的指标、日期、站点、类目和筛选条件。

### 4. 店铺分析

- 使用 `queryShopeeShopData` 或 `queryShopeeShopRanking` 找到目标店铺。
- 使用 `queryShopeeShopDetailBatch` 获取详情。
- 使用 `queryShopeeShopTrend` 或 `queryShopeeShopTrendDetail` 查询趋势。
- 使用 `queryShopeeShopItemList`、`queryShopeeShopItemPriceDistribute` 分析商品和价格结构。
- 使用 `queryShopeeShopCatDistribute`、`queryShopeeShopBrandAnalysis` 分析类目和品牌构成。

### 5. 品牌分析

- 使用 `queryShopeeBrandData` 或 `queryShopeeBrandRanking` 找到品牌。
- 使用 `queryShopeeBrandDetailBatch` 获取详情。
- 使用 `queryShopeeBrandTrend` 或 `queryShopeeBrandTrendDetail` 查询趋势。
- 使用 `queryShopeeBrandItemList`、`queryShopeeBrandShopList` 分析商品与店铺。
- 使用 `queryShopeeBrandCategoryDistribute`、`queryShopeeBrandSiteDistribute`、`queryShopeeBrandPriceDistribute` 分析类目、站点和价格分布。

品牌工具通常以 `brandName` 作为标识；使用接口返回的规范品牌名，避免自行改写。

### 6. 热搜词分析

- 使用 `queryShopeeWordData` 或 `queryShopeeWordRanking` 获取热搜词及榜单。
- 使用 `queryShopeeWordDetailBatch` 查询词详情。
- 使用 `queryShopeeWordTrend` 分析趋势。
- 使用 `queryShopeeWordItemList` 查看热搜词关联商品。

区分搜索热度、商品数、销量和推荐价格等不同指标，不把相关性表述成因果关系。

## 工具目录

### 站点与类目

- `queryShopeeSiteDate`：查询站点基础数据
- `queryShopeeLevel1Categories`：查询一级类目
- `queryShopeeLevel2Categories`：查询二级类目
- `queryShopeeLevel3Categories`：查询三级类目
- `queryShopeeCatData`：查询站点类目列表
- `queryShopeeSubCatData`：查询子类目列表
- `queryShopeeCatRanking`：查询类目榜单
- `queryShopeeCatTrend`：查询类目趋势快照
- `queryShopeeCatPriceDistribute`：查询类目价格分布
- `queryShopeeCategoryTrendOverview`：查询类目趋势概览

### 商品

- `queryShopeeItemData`：查询商品列表
- `queryShopeeItemRanking`：查询商品榜单
- `queryShopeeItemDetailBatch`：批量获取商品详情
- `queryShopeeItemTrend`：查询商品趋势快照
- `queryShopeeItemTrendDetail`：查询商品趋势
- `queryShopeeItemHotWord`：商品热搜词分析

### 店铺

- `queryShopeeShopData`：查询店铺列表
- `queryShopeeShopRanking`：查询店铺榜单
- `queryShopeeShopDetailBatch`：批量获取店铺详情
- `queryShopeeShopTrend`：查询店铺趋势快照
- `queryShopeeShopTrendDetail`：查询店铺趋势
- `queryShopeeShopItemList`：查询店铺产品列表
- `queryShopeeShopItemPriceDistribute`：查询店铺销量价格分布
- `queryShopeeShopCatDistribute`：查询店铺类目分布
- `queryShopeeShopBrandAnalysis`：查询店铺品牌分析

### 品牌

- `queryShopeeBrandData`：查询品牌列表
- `queryShopeeBrandRanking`：查询品牌榜单
- `queryShopeeBrandDetailBatch`：批量获取品牌详情
- `queryShopeeBrandTrend`：查询品牌趋势快照
- `queryShopeeBrandTrendDetail`：查询品牌趋势
- `queryShopeeBrandItemList`：查询品牌产品列表
- `queryShopeeBrandShopList`：查询品牌店铺列表
- `queryShopeeBrandCategoryDistribute`：查询品牌类目分布
- `queryShopeeBrandSiteDistribute`：查询品牌站点分布
- `queryShopeeBrandPriceDistribute`：查询品牌价格分布

### 热搜词

- `queryShopeeWordData`：查询热搜词列表
- `queryShopeeWordRanking`：查询热搜词榜单
- `queryShopeeWordDetailBatch`：批量获取热搜词详情
- `queryShopeeWordTrend`：热搜词趋势快照
- `queryShopeeWordItemList`：查询热搜词关联商品

## 输出规范

- 开头注明：站点、数据日期或时间范围、类目及层级、筛选条件。
- 排名结果优先用表格展示，并保留接口返回的单位和币种。
- 趋势结论至少给出起止值或变化幅度；不能从单点数据推导趋势。
- 结论与事实分开：先列数据，再写洞察和建议。
- 若结果分页，注明当前页、页大小以及是否已覆盖全部结果。
- 若数据为空，先检查站点、日期、类目层级和 ID 是否匹配，再解释无法得出结论。

## 示例请求

- “分析马来西亚站最近 30 天女装一级类目的市场趋势。”
- “查询泰国站某三级类目本周商品销量榜，并总结前 20 名价格带。”
- “对比新加坡站两个店铺近 90 天的销量和 GMV 趋势。”
- “查找菲律宾站某品牌的热销商品、核心店铺和价格分布。”
- “分析越南站某类目的热搜词趋势及关联商品。”
