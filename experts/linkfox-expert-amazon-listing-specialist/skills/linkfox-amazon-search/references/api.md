# 亚马逊前端搜索模拟 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/amazon/search`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词；请尽量翻译为对应国家的语言，比如美国用英语关键词，德国用德语关键词等等（最大长度1024） |
| amazonDomain | string | 否 | 亚马逊各个国家站点，默认 `amazon.com` |
| node | string | 否 | 亚马逊类目节点（最大长度1000） |
| language | string | 否 | 语言区域代码，如 en_US、de_DE、ja_JP、fr_FR（最大长度1000） |
| sort | string | 否 | 排序方式：`relevanceblender`（精选，默认）、`price-asc-rank`（价格从低到高）、`price-desc-rank`（价格从高到低）、`review-rank`（平均客户评价）、`date-desc-rank`（最新到货）、`exact-aware-popularity-rank`（畅销商品） |
| page | integer | 否 | 页码（从1开始，每页大概20条），默认 `1` |
| deliveryZip | string | 否 | 配送地邮编，用于模拟亚马逊前台地址，建议使用目标国家主要城市的常用邮编，如美国站常用纽约邮编 10001（最大长度1000） |
| device | string | 否 | 设备类型：`desktop`、`mobile`、`tablet`，默认 `desktop`（最大长度1000） |

### 支持的 amazonDomain 值

| 域名 | 国家 |
|------|------|
| amazon.com | 美国 |
| amazon.co.uk | 英国 |
| amazon.de | 德国 |
| amazon.fr | 法国 |
| amazon.it | 意大利 |
| amazon.es | 西班牙 |
| amazon.co.jp | 日本 |
| amazon.ca | 加拿大 |
| amazon.com.au | 澳大利亚 |
| amazon.com.br | 巴西 |
| amazon.in | 印度 |
| amazon.nl | 荷兰 |
| amazon.se | 瑞典 |
| amazon.pl | 波兰 |
| amazon.sg | 新加坡 |
| amazon.sa | 沙特阿拉伯 |
| amazon.ae | 阿联酋 |
| amazon.com.mx | 墨西哥 |
| amazon.com.tr | 土耳其 |
| amazon.com.be | 比利时 |
| amazon.cn | 中国 |
| amazon.eg | 埃及 |

### 常用 language 值

| 区域代码 | 说明 |
|----------|------|
| en_US | 美国站 英语 |
| en_GB | 英国站 英语 |
| de_DE | 德国站 德语 |
| fr_FR | 法国站 法语 |
| it_IT | 意大利站 意大利语 |
| es_ES | 西班牙站 西班牙语 |
| ja_JP | 日本站 日语 |
| en_CA | 加拿大站 英语 |
| fr_CA | 加拿大站 法语 |
| en_AU | 澳大利亚站 英语 |
| pt_BR | 巴西站 葡萄牙语 |
| en_IN | 印度站 英语 |
| hi_IN | 印度站 印地语 |
| nl_NL | 荷兰站 荷兰语 |
| sv_SE | 瑞典站 瑞典语 |
| pl_PL | 波兰站 波兰语 |
| en_SG | 新加坡站 英语 |
| ar_AE | 阿联酋/沙特阿拉伯/埃及站 阿拉伯语 |
| en_AE | 阿联酋/沙特阿拉伯/埃及站 英语 |
| tr_TR | 土耳其站 土耳其语 |
| nl_BE | 比利时站 荷兰语 |
| fr_BE | 比利时站 法语 |
| zh_CN | 中国站 中文 |
| pt_MX | 墨西哥站 西班牙语 |

### 常用 deliveryZip 值

| 国家 | 城市 | 邮编 |
|------|------|------|
| 美国 | 纽约 | 10001 |
| 英国 | 伦敦 | EC1A 1BB |
| 德国 | 柏林 | 10115 |
| 法国 | 巴黎 | 75001 |
| 意大利 | 罗马 | 00100 |
| 西班牙 | 马德里 | 28001 |
| 日本 | 东京 | 100-0001 |
| 加拿大 | 多伦多 | M5A 1A1 |
| 澳大利亚 | 悉尼 | 2000 |
| 巴西 | 圣保罗 | 01000-000 |
| 印度 | 新德里 | 110001 |
| 荷兰 | 阿姆斯特丹 | 1012 |
| 瑞典 | 斯德哥尔摩 | 111 22 |
| 波兰 | 华沙 | 00-001 |
| 新加坡 | 新加坡 | 018989 |
| 沙特阿拉伯 | 利雅得 | 11564 |
| 阿联酋 | 阿布扎比 | 00000 |
| 墨西哥 | 墨西哥城 | 01000 |
| 土耳其 | 伊斯坦布尔 | 34349 |
| 比利时 | 布鲁塞尔 | 1000 |
| 中国 | 北京 | 100000 |
| 埃及 | 开罗 | 11511 |

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总行数 |
| keyword | string | 搜索关键词 |
| type | string | 渲染的样式 |
| columns | array | 渲染的列定义 |
| costToken | integer | 消耗token |
| products | array | 搜索结果列表（详见下方） |

### products 商品对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| asin | string | ASIN |
| title | string | 标题 |
| brand | string | 品牌 |
| price | number | 价格 |
| extractedPrice | number | 解析后的价格 |
| oldPrice | number | 划线价格 |
| extractedOldPrice | number | 解析后的划线价格 |
| currency | string | 币种 |
| priceUnit | string | 价格单位 |
| extractedPriceUnit | number | 解析后的价格单位 |
| rating | number | 评分 |
| ratings | integer | 评分数 |
| position | integer | 位置 |
| sponsored | boolean | 是否赞助商 |
| imageUrl | string | 缩略图 |
| asinUrl | string | 链接 |
| delivery | string | 配送信息 |
| fulfillment | string | 配送信息（如 FBA） |
| availableDate | string (date) | 上架时间 |
| monthlySalesUnits | integer | 月销量 |
| monthlySalesRevenue | string | 月销售额 |
| sellerNation | string | 卖家国籍 |
| dimension | string | 尺寸 |
| weight | string | 重量 |
| options | string | 选项 |
| offers | string | 优惠信息 |
| badges | string | 亚马逊前台搜索标识 |
| tags | string | 标签 |
| snapEbtEligible | boolean | SNAP/EBT资格 |
| sourceType | string | 来源类型：amazon |
| sourceTool | string | 来源工具 |
| keyword | string | 关键词 |

## 错误码

正常情况下，接口的 HTTP 状态码均为 200，业务的成功与否通过响应体中的 `errcode` 字段区分（`errcode = 200` 表示成功，其他值表示业务错误）。当遇到未授权等情况时，HTTP 状态码为 401，且对应的 `errcode` 也是 401。

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
curl -X POST https://tool-gateway.linkfox.com/amazon/search \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "wireless earbuds", "amazonDomain": "amazon.com", "page": 1}'
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
