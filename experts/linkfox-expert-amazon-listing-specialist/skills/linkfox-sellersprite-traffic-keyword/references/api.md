# 卖家精灵-流量词反查 API 参考

本文档与工具 `_sellersprite_traffic_keyword` 的 `inputSchema` / `outputSchema`（见 `temp/tools20260430.txt`）对齐。

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/sellersprite/traffic/keyword`
- **请求方式**：POST，`Content-Type: application/json`
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| marketplace | string | 是 | 见下表 | 市场站点，默认 `US` |
| asin | string | 是 | maxLength 1000 | 要反查的商品 ASIN |
| month | string | 否 | 正则 `^(19|20)\d{2}(0[1-9]|1[0-2])$` | 历史月份，格式 `yyyyMM`；不传默认最近 30 天 |
| page | integer | 否 | 默认 1 | 当前页 |
| size | integer | 否 | 默认 50，最小 1，最大 100；最多查 2000 条 | 每页条数 |
| keyword | string | 否 | maxLength 1000 | 关键词筛选 |
| badges | string | 否 | maxLength 1000，多值英文逗号分隔 | 流量词类型（曝光位置），见 [badges 枚举](#badges-枚举) |
| trafficKeywordTypes | string | 否 | maxLength 1000，多值英文逗号分隔 | 流量占比类型，见 [trafficKeywordTypes 枚举](#traffickeywordtypes-枚举) |
| conversionKeywordTypes | string | 否 | maxLength 1000，多值英文逗号分隔 | 流量转化类型，见 [conversionKeywordTypes 枚举](#conversionkeywordtypes-枚举) |
| orderField | string | 否 | maxLength 1000，默认 `rankPosition` | 排序字段，见 [orderField 可选值](#orderfield-可选值) |
| orderDesc | boolean | 否 | 默认 `false` | 排序是否倒序 |

### marketplace 可选值

| 取值 | 含义 |
|------|------|
| US | 美国站 USD($) |
| JP | 日本站 JPY(￥) |
| UK | 英国站 GBP(£) |
| DE | 德国站 EUR(€) |
| FR | 法国站 EUR(€) |
| IT | 意大利站 EUR(€) |
| ES | 西班牙站 EUR(€) |
| CA | 加拿大站 C$($) |
| IN | 印度站 INR(₹) |

### badges 枚举

多个值用英文逗号分隔。

| 取值 | 含义 |
|------|------|
| naturalSearching | 自然搜索词 |
| amazonChoice | AC 推荐词 |
| editorialRecommendations | ER 推荐词 |
| fourStar | 四星推荐词 |
| highlyRated | HR 推荐词 |
| sponsorBrand | 品牌推荐词 |
| sponsorVideo | 视频推荐词 |
| ads | SP 广告词 |

### trafficKeywordTypes 枚举

多个值用英文逗号分隔（与工具 schema 文案一致）。

| 取值 | 含义 |
|------|------|
| primary | 主要流量词 |
| precise | 精准流量词 |
| preciseLongTail | 转化流失词 |

### conversionKeywordTypes 枚举

多个值用英文逗号分隔。

| 取值 | 含义 |
|------|------|
| excellent | 转化优质词 |
| stable | 转化平稳词 |
| lost | 转化流失词 |
| invalid | 无效曝光词 |

### orderField 可选值

| 取值 | 含义 |
|------|------|
| rankPosition | 自然排名（默认） |
| adPosition | 广告排名 |
| createdTime | 创建时间 |
| searchesRank | 搜索量周排名 |
| searches | 月搜索量 |
| purchases | 月购买量 |
| purchaseRate | 购买率 |
| products | 商品数 |
| supplyDemandRatio | 供需比 |
| latest1daysAds | 广告竞品数 |
| bid | PPC 竞价 |
| trafficPercentage | 流量占比 |

## 响应结构

### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总条数 |
| marketplace | string | 市场编码 |
| asin | string | 查询的 ASIN |
| data | array | 流量词列表（对应第三方 `data.items`） |
| summaryList | array | 高频词总结列表 |
| columns | array | 列定义 |
| costToken | integer | 消耗 token |
| type | string | 渲染的样式 |

### summaryList 元素

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总次数 |
| keywords | string | 词 |

### data[] 元素（单条流量词）

| 字段 | 类型 | 说明 |
|------|------|------|
| keyword | string | 关键词 |
| keywordCn | string | 关键词中文翻译 |
| trafficKeywordType | string | 流量占比类型 |
| conversionKeywordType | string | 流量转化类型 |
| badges | array | 曝光位置（流量词类型） |
| rankPosition | object | 自然排名位次信息，结构见 [排名对象](#排名对象-rankposition--adposition) |
| adPosition | object | 广告排名位次信息，结构同 [排名对象](#排名对象-rankposition--adposition) |
| searches | integer | 月搜索量 |
| searchesRank | integer | 周搜索量排名 |
| searchesRankTimeFrom | integer | 周搜索量排名时间范围起 |
| searchesRankTimeTo | integer | 周搜索量排名时间范围止 |
| purchases | integer | 月购买量 |
| purchaseRate | number | 购买率 |
| products | integer | 商品数 |
| supplyDemandRatio | number | 供需比 |
| trafficPercentage | number | 流量占比 |
| naturalRatio | number | 流量分布-自然占比 |
| adRatio | number | 流量分布-广告占比 |
| calculatedWeeklySearches | number | 预估周曝光量 |
| impressions | integer | 展示量 |
| clicks | integer | 点击量 |
| bid | number | PPC 竞价 |
| bidMin | number | PPC 竞价下限 |
| bidMax | number | PPC 竞价上限 |
| latest1daysAds | integer | 最近 1 天广告竞品数 |
| latest7daysAds | integer | 最近 7 天广告竞品数 |
| latest30daysAds | integer | 最近 30 天广告竞品数 |
| sprt | number | SP 相关比率 |
| monopolyClickRate | number | 垄断点击率 |
| top3ClickingRate | number | Top3 点击率 |
| top3ConversionRate | number | Top3 转化率 |
| titleDensity | number | 标题密度 |
| stats | array | 高频词，元素见下表 |
| updatedTime | integer | 更新时间 |

### stats[] 元素（高频词子项）

| 字段 | 类型 | 说明 |
|------|------|------|
| keywords | string | 词 |
| total | integer | 总条数 |
| rankPosition | object | 自然排名位次，结构见下 |
| adPosition | object | 广告排名位次，结构见下 |

### 排名对象（rankPosition / adPosition）

| 字段 | 类型 | 说明 |
|------|------|------|
| updatedTime | integer | 排名时间 |
| pageSize | integer | 每页多少条数据 |
| index | integer | 当前页排第几 |
| page | integer | 第几页 |
| position | integer | 总结果中排第几 |

## curl 示例

```bash
curl -X POST https://tool-gateway.linkfox.com/sellersprite/traffic/keyword   -H "Authorization: $LINKFOXAGENT_API_KEY"   -H "Content-Type: application/json"   -d '{
    "marketplace": "US",
    "asin": "B0XXXXXXXXX",
    "page": 1,
    "size": 50
  }'
```

---

## Feedback API

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-sellersprite-traffic-keyword",
  "sentiment": "POSITIVE",
  "category": "OTHER",
  "content": "Results were accurate, user was satisfied."
}
```
