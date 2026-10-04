# 亚马逊商品评论 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/amazon/reviews/list`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明                                                                                                                             |
|------|------|------|--------------------------------------------------------------------------------------------------------------------------------|
| asin | string | 是 | 亚马逊商品ASIN                                                                                                                      |
| domainCode | string | 否 | 亚马逊域名代码，默认 `com`。可选值：`com`、`ca`、`co.uk`、`in`、`de`、`fr`、`it`、`es`、`co.jp`、`com.au`、`com.br`、`nl`、`se`、`com.mx`、`ae`。美国站使用 `com` |
| star1Num | integer | 否 | 1星评论数量，默认获取10条，最多100条                                                                                                          |
| star2Num | integer | 否 | 2星评论数量，默认获取10条，最多100条                                                                                                          |
| star3Num | integer | 否 | 3星评论数量，默认获取10条，最多100条                                                                                                          |
| star4Num | integer | 否 | 4星评论数量，默认获取10条，最多100条                                                                                                          |
| star5Num | integer | 否 | 5星评论数量，默认获取10条，最多100条                                                                                                          |
| filterByKeyword | string | 否 | 按关键词筛选评论，最大长度1000字符                                                                                                            |
| sortBy | string | 否 | 评论排序方式：`recent`（最新评论）或 `helpful`（最有用评论），默认 `recent`                                                                            |
| reviewerType | string | 否 | 评论者类型：`all_reviews`（所有评论）或 `avp_only_reviews`（仅认证购买），默认 `all_reviews`                                                          |
| mediaType | string | 否 | 媒体类型：`all_contents`（所有内容）或 `media_reviews_only`（仅包含媒体的评论），默认 `all_contents`                                                    |
| formatType | string | 否 | 格式类型：`all_formats`（所有格式）或 `current_format`（当前格式），默认 `all_formats`                                                           |

说明：若 `star1Num` ~ `star5Num` 均未传，则 1~5 星默认各抓取 `10` 条；若已传任意一个星级数量，则其它未传星级默认 `0`。

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总评论数 |
| data | array | 评论列表（详见下方评论对象） |
| columns | array | 渲染的列 |
| costToken | integer | 总Token消耗 |
| type | string | 渲染的样式 |

### 评论对象

| 字段 | 类型 | 说明 |
|------|------|------|
| reviewId | string | 评论ID |
| asin | string | 产品ASIN |
| title | string | 评论标题 |
| text | string | 评论内容 |
| rating | string | 评分 |
| date | string | 评论日期 |
| userName | string | 评论者名称 |
| verified | boolean | 是否已验证购买 |
| vine | boolean | 是否Vine Voice评论 |
| numberOfHelpful | integer | 有用数量 |
| imageUrlList | array | 评论图片列表 |
| videoUrlList | array | 评论视频列表 |
| domainCode | string | 国家代码 |
| productTitle | string | 产品标题 |
| productRating | string | 产品评分 |
| countRatings | integer | 产品评分数量 |
| countReviews | integer | 产品评论数量 |
| variationId | string | 变体ID |
| variationList | array | 变体列表 |
| profilePath | string | 评论者个人资料路径 |
| currentPage | integer | 当前页码 |
| sortStrategy | string | 排序策略 |
| statusCode | integer | 状态码 |
| statusMessage | string | 状态消息 |
| locale | object | 区域信息 |
| reviewSummary | object | 评论摘要数据 |
| filters | object | 已应用的筛选条件 |

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

## curl 示例（美国站）

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/reviews/list \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "B08N5WRWNW",
    "domainCode": "com",
    "star1Num": 10,
    "star2Num": 10,
    "star3Num": 0,
    "star4Num": 0,
    "star5Num": 0,
    "sortBy": "recent",
    "reviewerType": "all_reviews"
  }'
```

---

## Feedback API

> This endpoint is **separate** from the tool API above. Do not mix the two base URLs.

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-amazon-reviews",
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
