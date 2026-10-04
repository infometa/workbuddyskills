# Keepa-亚马逊-商品详情 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/keepa/productRequest`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| asin | string | 是 | 亚马逊标准识别号(ASIN)，多个ASIN用英文逗号分隔，最多5个，最大长度300字符。示例：`B0088PUEPK` 或 `B0088PUEPK,B00U26V4VQ,B07M68S376` |
| domain | string | 是 | 亚马逊域名ID。可选值：`1`（美国）、`2`（英国）、`3`（德国）、`4`（法国）、`5`（日本）、`6`（加拿大）、`8`（意大利）、`9`（西班牙）、`10`（印度）、`11`（墨西哥）、`12`（巴西） |
| history | integer | 否 | 返回值是否包含历史数据、历史销量。`1` = 包含价格历史、销售排名、历史销量等时间序列数据（前几个月的销量），`0` = 仅返回基本商品信息。默认：`0` |

## 响应结构

### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总行数 |
| perPage | integer | 每页数量 |
| sourceType | string | 来源类型：keepa |
| columns | array | 渲染的列 |
| costToken | integer | 消耗token |
| totalCount | integer | 总数量 |
| currentPage | integer | 当前页码 |
| type | string | 渲染的样式 |
| products | array | 商品列表（详见下方） |

### 商品对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | ASIN |
| title | string | 商品标题 |
| brand | string | 品牌 |
| manufacturer | string | 制造商 |
| model | string | 型号 |
| color | string | 颜色 |
| material | string | 产品的材质，指其构造中使用的主要材料 |
| price | number | 当前价格（单位：元，如美元/欧元等） |
| primePrice | number | prime价格 |
| currency | string | 币种 |
| rating | number | 当前评分（0.0-5.0，如4.5星） |
| ratings | integer | 评分数量 |
| reviewCount | integer | 评论数量 |
| salesRank | integer | 销售排名 |
| salesRank30 | integer | 近30天平均销售排名 |
| salesRank90 | integer | 近90天平均销售排名 |
| salesRank180 | integer | 近180天平均销售排名 |
| monthlySalesUnits | integer | 月销量 |
| monthlySalesRevenue | number | 月销售额 |
| monthlySalesUnits1MonthAgo | integer | 1月前月销量 |
| monthlySalesUnits2MonthsAgo | integer | 2月前月销量 |
| monthlySalesUnits3MonthsAgo | integer | 3月前月销量 |
| monthlySalesUnits4MonthsAgo | integer | 4月前月销量 |
| monthlySalesUnits5MonthsAgo | integer | 5月前月销量 |
| monthlySalesUnits6MonthsAgo | integer | 6月前月销量 |
| monthlySalesUnits7MonthsAgo | integer | 7月前月销量 |
| monthlySalesUnits8MonthsAgo | integer | 8月前月销量 |
| monthlySalesUnits9MonthsAgo | integer | 9月前月销量 |
| monthlySalesUnits10MonthsAgo | integer | 10月前月销量 |
| monthlySalesUnits11MonthsAgo | integer | 11月前月销量 |
| monthlySalesUnits12MonthsAgo | integer | 12月前月销量 |
| availableDate | string | 上架时间（yyyy-MM-dd HH:mm:ss） |
| lastUpdate | string | 最后更新时间（yyyy-MM-dd HH:mm:ss） |
| imageUrl | string | 图片URL（请求地址） |
| productImageUrls | array | 商品图片列表 |
| asinUrl | string | 亚马逊asin的详情网址 |
| urlSlug | string | URL Slug |
| itemLength | integer | 商品长度，单位为毫米，不可用时为0或-1 |
| itemWidth | integer | 商品宽度，单位为毫米，不可用时为0或-1 |
| itemHeight | integer | 商品高度，单位为毫米，不可用时为0或-1 |
| dimension | string | 尺寸 |
| dimensionsType | string | 尺寸类型 |
| weight | string | 重量（克） |
| packageLength | integer | 包装长度（毫米） |
| packageWidth | integer | 包装宽度（毫米） |
| packageHeight | integer | 包装高度（毫米） |
| packageWeight | string | 包装重量（克） |
| packageDimensions | string | 包装尺寸 |
| packageQuantity | integer | 包装中商品的数量，不可用时为0或-1 |
| fulfillment | string | 配送方式(AMZ,FBA,FBM) |
| fbaFees | number | FBA配送费（单位：元） |
| referralFeePercentage | number | 推荐费百分比 |
| profit | number | 利润率（百分比，如25.5表示25.5%） |
| buyBoxSellerId | string | 购买按钮卖家ID |
| sellerNum | integer | 卖家数 |
| variationNum | integer | 变体数量 |
| parentAsin | string | 父ASIN |
| rootCategory | integer | 根类目ID |
| categoryTree | string | 类目树 |
| categoryTreeId | string | 类目树Id |
| subcategories | array | 子类目列表，每个元素包含 `code`（类目ID）、`rank`（排名）、`label`（类目名称） |
| isAdultProduct | boolean | 是否为成人产品 |
| isHazmat | boolean | 是否为危险品 |
| sourceType | string | 来源类型：keepa |
| sourceTool | string | 来源工具 |

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
curl -X POST https://tool-gateway.linkfox.com/keepa/productRequest \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B0088PUEPK", "domain": "1", "history": 1}'
```

### 批量查询示例

```bash
curl -X POST https://tool-gateway.linkfox.com/keepa/productRequest \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B0088PUEPK,B00U26V4VQ,B07M68S376", "domain": "1", "history": 0}'
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
