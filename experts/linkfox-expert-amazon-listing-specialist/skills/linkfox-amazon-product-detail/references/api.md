# 亚马逊前端-商品详情 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/amazon/product/detail`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| asins | string | 是 | ASIN列表，支持批量查询，最多40个ASIN。格式：`^[A-Z0-9]+(,[A-Z0-9]+){0,39}$`。示例：`B072MQ5BRX,B08N5WRWNW` |
| amazonDomain | string | 否 | 亚马逊各个国家站点，默认 `amazon.com`。可选值：`amazon.com`、`amazon.co.uk`、`amazon.de`、`amazon.fr`、`amazon.it`、`amazon.es`、`amazon.co.jp`、`amazon.ca`、`amazon.com.au`、`amazon.com.br`、`amazon.in`、`amazon.nl`、`amazon.se`、`amazon.pl`、`amazon.sg`、`amazon.sa`、`amazon.ae`、`amazon.com.tr`、`amazon.com.mx`、`amazon.eg`、`amazon.cn`、`amazon.com.be` |
| language | string | 否 | 语言。示例：`en_US`、`de_DE`、`fr_FR`、`ja_JP`、`it_IT`、`es_ES`、`pt_BR`、`en_GB`、`zh_CN` |
| deliveryZip | string | 否 | 配送邮编，用于获取配送相关定价。示例：`10001`（美国纽约）、`10115`（德国柏林）、`EC1A 1BB`（英国伦敦） |
| device | string | 否 | 设备类型：`desktop`（默认）、`mobile`、`tablet` |
| returnBoughtTogether | boolean | 否 | 是否返回经常一起购买的商品（boughtTogether），默认 `false` |
| returnRelatedProducts | boolean | 否 | 是否返回相关商品列表（relatedProducts），默认 `false` |
| returnAuthorsReviews | boolean | 否 | 是否返回作者评论列表（authorsReviews），默认 `false` |

## 响应结构

顶层字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总行数 |
| columns | array | 渲染的列 |
| type | string | 渲染的样式 |
| costToken | integer | 消耗token |
| products | array | 产品列表（详见下方） |

### 产品对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | ASIN编码 |
| title | string | 商品标题 |
| brand | string | 品牌 |
| price | number | 价格 |
| extractedPrice | number | 提取的价格 |
| oldPrice | number | 原价 |
| extractedOldPrice | number | 提取的原价 |
| currency | string | 币种 |
| discount | string | 折扣 |
| saveWithCoupon | string | 优惠券节省金额 |
| rating | number | 评分 |
| ratings | integer | 评论数 |
| prime | boolean | 是否Prime商品 |
| stock | string | 库存状态 |
| delivery | string | 配送信息 |
| link | string | 商品链接 |
| linkClean | string | 纯净链接 |
| asinUrl | string | 链接 |
| imageUrl | string | 缩略图 |
| thumbnail | string | 缩略图 |
| productImageUrls | array | 商品图片链接列表 |
| aboutItem | array | 五点描述 |
| productDescription | string | 商品描述列表 |
| description | string | 商品描述 |
| dimension | string | 商品尺寸 |
| weight | string | 重量 |
| tags | string | 标签列表 |
| badges | string | 徽章列表 |
| climatePledgeFriendly | boolean | 是否气候友好 |
| snapEbtEligible | boolean | 是否支持SNAP EBT |
| boughtLastMonth | string | 上月购买数（字符串） |
| boughtLastMonthCount | integer | 上月购买数（数字） |
| reviewsSummary | string | 评论摘要 |
| reviewsImages | array | 评论图片列表 |
| sourceTool | string | 来源工具 |
| sourceType | string | 来源类型：amazon |
| pageFileUrl | string | 完整页面文件url |

### 嵌套对象

**productDetails** -- 商品详细规格信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | ASIN编码 |
| manufacturer | string | 制造商 |
| productDimensions | string | 商品尺寸 |
| upc | string | UPC编码 |
| units | string | 单位 |
| rating | number | 评分 |
| review | integer | 评论数 |

**customerReviews** -- 星级评分分布：

| 字段 | 类型 | 说明 |
|------|------|------|
| fiveStar | integer | 五星评论数 |
| fourStar | integer | 四星评论数 |
| threeStar | integer | 三星评论数 |
| twoStar | integer | 二星评论数 |
| oneStar | integer | 一星评论数 |

**variants** -- 商品变体列表（数组）：

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 变体标题（如颜色、尺寸） |
| items | array | 变体项列表，每项包含 `name`（名称）、`asin`（ASIN编码）、`position`（位置）、`selected`（是否已选择） |

**itemSpecifications** -- 商品规格（动态键值）。

**itemIngredients** -- 商品成分列表（数组）。

**reviewsImages** -- 评论图片列表（数组）。

### 可选嵌套数组（按需返回）

**boughtTogether**（当 `returnBoughtTogether: true` 时返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | ASIN编码 |
| title | string | 标题 |
| price | string | 价格 |
| extractedPrice | number | 提取的价格 |
| priceUnit | string | 单价 |
| extractedPriceUnit | number | 提取的单价 |
| thumbnail | string | 缩略图 |
| link | string | 链接 |
| linkClean | string | 纯净链接 |
| stock | string | 库存状态 |
| delivery | array | 配送信息 |
| position | integer | 位置 |

**relatedProducts**（当 `returnRelatedProducts: true` 时返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | ASIN编码 |
| title | string | 标题 |
| price | string | 价格 |
| extractedPrice | number | 提取的价格 |
| oldPrice | string | 原价 |
| extractedOldPrice | number | 提取的原价 |
| priceUnit | string | 单价 |
| extractedPriceUnit | number | 提取的单价 |
| rating | number | 评分 |
| reviews | integer | 评论数 |
| thumbnail | string | 缩略图 |
| link | string | 链接 |
| linkClean | string | 纯净链接 |
| prime | boolean | 是否Prime商品 |
| sponsored | boolean | 是否赞助商品 |
| climatePledgeFriendly | boolean | 是否气候友好 |
| discount | string | 折扣 |
| badges | array | 徽章列表 |
| position | integer | 位置 |

**authorsReviews**（当 `returnAuthorsReviews: true` 时返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 标题 |
| text | string | 评论内容 |
| author | string | 作者 |
| authorImage | string | 作者头像 |
| authorLink | string | 作者链接 |
| rating | integer | 评分 |
| date | string | 日期 |
| verifiedPurchase | boolean | 是否已验证购买 |
| helpfulVotes | string | 有用投票数 |
| productSize | string | 商品尺寸 |
| productFlavorName | string | 商品口味名称 |
| position | integer | 位置 |

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
curl -X POST https://tool-gateway.linkfox.com/amazon/product/detail \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"asins": "B072MQ5BRX,B08N5WRWNW", "amazonDomain": "amazon.com"}'
```

### 包含可选参数

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/product/detail \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "asins": "B072MQ5BRX",
    "amazonDomain": "amazon.de",
    "language": "de_DE",
    "deliveryZip": "10115",
    "returnBoughtTogether": true,
    "returnAuthorsReviews": true
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
