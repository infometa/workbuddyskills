# 亚马逊-以图搜图 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/amazon/searchByImage`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY`（或 `LINKFOXAGENT_API_KEY`）读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| imageUrl | string | 是 | 图片URL地址，请确保图片URL地址有效。最大长度：1000 |
| amazonDomain | string | 是 | 亚马逊站点，仅支持以下站点：美国(`amazon.com`)、英国(`amazon.co.uk`)、德国(`amazon.de`)、法国(`amazon.fr`)、意大利(`amazon.it`)、西班牙(`amazon.es`)、日本(`amazon.co.jp`)、印度(`amazon.in`)。默认 `amazon.com` |
| sort | string | 否 | 排序，支持价格、评分、评论数排序。可选值：`default`（默认）、`price-asc-rank`（价格从低到高）、`price-desc-rank`（价格从高到低）、`rating-asc-rank`（评分从低到高）、`rating-desc-rank`（评分从高到低）、`ratings-asc-rank`（评论数从低到高）、`ratings-desc-rank`（评论数从高到低） |
| deliveryZip | string | 否 | 站内收货地址邮编或城市，如果用户未指定，则取站点（国家）的默认邮编。最大长度：1000。各站点默认邮编：美国=10001、英国=EC1A 1BB、德国=10115、法国=75001、意大利=00100、西班牙=28001、日本=100-0001、印度=110034 |
| countryOrAreaCode | string | 否 | 站外收货的国家代码（如 CN、JP、KR、TW、HK、MO、SG、TH、VN、PH、MY）。站内邮编地址和站外国家地区代码不能同时指定。注意：印度站不支持设置站外国家或地区收货。最大长度：1000 |
| aggregateByKeepaData | boolean | 否 | 是否聚合Keepa数据（销售排名、月销量、FBA费用、尺寸等） |


## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总行数 |
| totalCount | integer | 总数量 |
| perPage | integer | 每页数量 |
| currentPage | integer | 当前页码 |
| type | string | 渲染的样式 |
| sourceType | string | 来源类型 |
| columns | array | 渲染的列 |
| costToken | integer | 消耗token |
| products | array | 商品列表（详见下方商品字段） |

### 商品字段

每个商品返回的核心字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | ASIN |
| title | string | 商品标题 |
| imageUrl | string | 图片URL（请求地址） |
| asinUrl | string | 亚马逊ASIN的详情网址 |
| price | number | 当前价格（单位：元，如美元/欧元等） |
| oldPrice | number | 划线价格 |
| currency | string | 币种 |
| rating | number | 当前评分（0.0-5.0，如4.5星） |
| ratings | integer | 评分数量 |
| brand | string | 品牌 |
| sourceTool | string | 来源工具 |
| sourceType | string | 来源类型 |

Keepa 聚合字段（当 `aggregateByKeepaData` 为 true 时返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| salesRank | integer | 销售排名(keepa) |
| salesRank30 | integer | 近30天平均销售排名(keepa) |
| salesRank90 | integer | 近90天平均销售排名(keepa) |
| salesRank180 | integer | 近180天平均销售排名(keepa) |
| monthlySalesUnits | integer | 月销量(keepa) |
| monthlySalesRevenue | number | 月销售额(keepa) |
| monthlySalesUnits1MonthAgo ~ monthlySalesUnits12MonthsAgo | integer | 1~12月前月销量(keepa) |
| reviewCount | integer | 评论数量(keepa) |
| fbaFees | number | FBA配送费(keepa)（单位：元） |
| profit | number | 利润率(keepa)（利润率百分比，如25.5表示25.5%） |
| referralFeePercentage | number | 推荐费百分比(keepa) |
| fulfillment | string | 配送方式(AMZ, FBA, FBM)(keepa) |
| primePrice | number | Prime价格(keepa) |
| buyBoxSellerId | string | 购买按钮卖家ID(keepa) |
| sellerNum | integer | 卖家数(keepa) |
| variationNum | integer | 变体数量(keepa) |
| parentAsin | string | 父ASIN(keepa) |
| availableDate | string | 上架时间(keepa)（yyyy-MM-dd HH:mm:ss） |
| lastUpdate | string | 最后更新时间(keepa)（yyyy-MM-dd HH:mm:ss） |
| manufacturer | string | 制造商(keepa) |
| model | string | 型号(keepa) |
| color | string | 颜色(keepa) |
| material | string | 产品的材质(keepa)，指其构造中使用的主要材料 |
| weight | string | 重量（克）(keepa) |
| dimension | string | 尺寸(keepa) |
| itemLength | integer | 商品长度(keepa)，单位为毫米，不可用时为0或-1 |
| itemWidth | integer | 商品宽度(keepa)，单位为毫米，不可用时为0或-1 |
| itemHeight | integer | 商品高度(keepa)，单位为毫米，不可用时为0或-1 |
| packageLength | integer | 包装长度（毫米）(keepa) |
| packageWidth | integer | 包装宽度（毫米）(keepa) |
| packageHeight | integer | 包装高度（毫米）(keepa) |
| packageWeight | string | 包装重量（克）(keepa) |
| packageDimensions | string | 包装尺寸(keepa) |
| packageQuantity | integer | 包装中商品的数量(keepa)，不可用时为0或-1 |
| dimensionsType | string | 尺寸类型(keepa) |
| categoryTree | string | 类目树(keepa) |
| categoryTreeId | string | 类目树ID(keepa) |
| rootCategory | integer | 根类目ID(keepa) |
| isAdultProduct | boolean | 是否为成人产品(keepa) |
| isHazmat | boolean | 是否为危险品(keepa) |
| urlSlug | string | URL Slug(keepa) |
| productImageUrls | array | 商品图片列表(keepa) |

## 错误码

正常情况下，接口的 HTTP 状态码均为 200，业务的成功与否通过响应体中的 errorCode 字段区分（errorCode = 200 表示成功，其他值表示业务错误）。当遇到未授权等情况时，HTTP 状态码为 401，且对应的 errorCode 也是 401。

| errcode | 含义 | 处理建议 |
|---------|------|----------|
| 200 | 成功 | 正常解析业务字段 |
| 401 | 认证失败 | HTTP 401 或 authorized error：按 SKILL.md 的 **## 解决认证和积分问题** 处理。|
| 402 | 积分不足 | HTTP 402：按 SKILL.md 的 **## 解决认证和积分问题** 处理。|
| 其他非200值 | 业务异常 | 参考 `errmsg` 字段获取具体错误原因 |

错误响应示例：

```json
{
    "errcode": 401,
    "errmsg": "authorized error"
}
```

## curl 示例

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/searchByImage \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://m.media-amazon.com/images/I/61pAlIX8SZL._AC_SY575_.jpg",
    "amazonDomain": "amazon.com",
    "sort": "default"
  }'
```

### 聚合 Keepa 数据示例

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/searchByImage \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://m.media-amazon.com/images/I/61pAlIX8SZL._AC_SY575_.jpg",
    "amazonDomain": "amazon.com",
    "sort": "price-asc-rank",
    "aggregateByKeepaData": true
  }'
```

### 站外收货示例

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/searchByImage \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://m.media-amazon.com/images/I/61pAlIX8SZL._AC_SY575_.jpg",
    "amazonDomain": "amazon.co.jp",
    "countryOrAreaCode": "CN"
  }'
```

---

## Feedback API

> This endpoint is **separate** from the tool API above. Do not mix the two base URLs.

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-xxx-xxx",
  "sentiment": "POSITIVE",
  "category": "OTHER",
  "content": "Results were accurate, user was satisfied."
}
```

**Field rules:**
- `skillName`: Use this skill's `name` from the YAML frontmatter
- `sentiment`: Choose ONE — `POSITIVE` (praise), `NEUTRAL` (suggestion without emotion), `NEGATIVE` (complaint or error)
- `category`: Choose ONE — `BUG` (malfunction or wrong data), `COMPLAINT` (user dissatisfaction), `SUGGESTION` (improvement idea), `OTHER`
- `content`: Include what the user said or intended, what actually happened, and why it is a problem or praise
