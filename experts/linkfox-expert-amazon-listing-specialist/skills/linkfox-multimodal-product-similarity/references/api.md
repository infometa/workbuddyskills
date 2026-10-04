# 商品主图相似度分组 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/multimodal/analyzeProductSimilarity`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| similarityThreshold | integer | 否 | 相似度阈值（0-100的整数，表示相似度百分比），默认 `60`。值越高要求视觉匹配越接近 |
| includeSingleBrandGroups | boolean | 否 | 是否展示只有单一品牌的分组，默认 `true`（展示），`false` 则不展示品牌数量为1的分组 |
| refResultData | string | 否 | 前序工具返回的结果数据（JSON字符串），必须包含 `products` 数组。最大长度 2,024,000 字符 |
| userInput | string | 否 | 用户输入信息。最大长度 10,000,000 字符 |

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| groups | array | 相似商品分组列表（见下方分组对象） |
| analysisInfo | object | 分析摘要信息（见下方分析信息对象） |
| tables | array | 查询结果数据列表数组，每个元素包含 `data`（查询结果数据列表）、`columns`（渲染的列）、`name`（sheet的名称） |
| total | integer | 结果总数 |
| title | string | 标题 |
| type | string | 渲染的样式 |
| costToken | integer | 调用LLM消耗的总token数（输入token + 输出token） |

### 分组对象（groups 数组元素）

| 字段 | 类型 | 说明 |
|------|------|------|
| groupNumber | integer | 分组序号 |
| reason | string | 这些商品分在一组的理由 |
| brandCount | integer | 该组商品中不同品牌的数量 |
| asins | array | 该组内的商品列表（见下方商品对象） |

### 商品对象（asins 数组元素）

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | 商品ASIN编号 |
| productId | string | 商品ID |
| brand | string | 品牌名称 |
| price | number | 价格 |
| rating | number | 评分 |
| ratings | integer | 评分数 |
| monthlySalesUnits | integer | 月销量 |
| monthlySalesRevenue | number | 月销售额 |
| monthlySalesUnitsGrowthRate | number | 月销量增长率 |
| imageUrl | string | 商品主图地址 |
| productImageUrls | array | 商品图片列表 |
| imagePrompt | string | 图片提示词 |
| asinUrl | string | 商品详情页地址 |
| availableDate | string | 上架日期 |
| color | string | 颜色 |
| material | string | 材质 |
| sourceTool | string | 来源工具 |
| sourceType | string | 来源类型 |

### 分析信息对象（analysisInfo）

| 字段 | 类型 | 说明 |
|------|------|------|
| totalProductsAnalyzed | integer | 分析的商品总数 |
| totalGroupsFound | integer | 发现的分组总数 |
| similarityThreshold | number | 相似度阈值（0-1之间的小数） |
| analysisTimestamp | string | 分析时间戳 |

## 错误码

正常情况下，接口的 HTTP 状态码均为 200，业务的成功与否通过响应体中的 errorCode 字段区分（errorCode = 200 表示成功，其他值表示业务错误）。当遇到未授权等情况时，HTTP 状态码为 401，且对应的 errorCode 也是 401。

| errcode | 含义 | 处理建议 |
|---------|------|----------|
| 200 | 成功 | 正常解析业务字段 |
| 401 | 认证失败 | HTTP 401 或 authorized error：按 SKILL.md 的 **## 解决认证和积分问题** 处理。 |
| 402 | 积分或余额不足 | HTTP 402：按 SKILL.md 的 **## 解决认证和积分问题** 处理。 |
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
curl -X POST https://tool-gateway.linkfox.com/multimodal/analyzeProductSimilarity \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "similarityThreshold": 60,
    "includeSingleBrandGroups": true,
    "refResultData": "{\"products\":[{\"asin\":\"B0XXXXXXXX\",\"imageUrl\":\"https://example.com/img1.jpg\",\"brand\":\"BrandA\",\"price\":29.99},{\"asin\":\"B0YYYYYYYY\",\"imageUrl\":\"https://example.com/img2.jpg\",\"brand\":\"BrandB\",\"price\":31.99}]}",
    "userInput": "按视觉相似度对这些商品进行分组"
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
