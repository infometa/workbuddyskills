# SIF-ASIN的关键词 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/sif/asinKeywords`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| asin | string | 是 | ASIN码，最大长度1000字符。本工具一次只能查询一个ASIN |
| country | string | 否 | 国家站点，默认 `US`。可选值（共 13 个）：`US`、`UK`、`DE`、`CA`、`JP`、`FR`、`ES`、`IT`、`MX`、`AU`、`AE`、`BR`、`SA` |
| keyword | string | 否 | 关键词，最大长度1000。尽量翻译成对应国家站点的语言 |
| timePieceType | string | 否 | 时间片段类型，默认 `latelyDay`。可选值：`latelyDay`（最近N天）、`month`（某月）、`week`（某周） |
| timePieceValue | string | 否 | 时间片段值，默认 `7`，最大长度1000。`latelyDay` 时仅支持 `7` 或 `30`；`month` 时为 `YYYY-MM`（如 `2026-04`）；`week` 时为周开始日期 `YYYY-MM-DD`（如 `2026-04-13`） |
| conditions | string | 否 | 条件筛选，多个以英文逗号隔开。可选值：<br>**标志类**：`nfPosition`（自然流量词）、`isSpAd`（SP广告词）、`isBrandAd`（品牌广告词）、`isVedioAd`（视频广告词）、`isAC`（AC推荐词）、`isAccurateKw`（精准流量词）、`isAccurateTailKw`（精准长尾词）、`isPurchaseKw`（出单词）、`isQualityKw`（转化优质词）、`isStableKw`（转化平稳词）、`isLossKw`（转化流失词）、`isInvalidKw`（无效曝光词）、`isMultiVariantKw`（多变体自然位词）、`isSearchVolUpKw`（搜索量同比增长词）、`isSearchVolDownKw`（搜索量同比下降词）<br>**周期计数类（`.total` 全量 / `.in` 新进）**：`totalPeriod.in`、`nfKeywordCnt.total`、`nfKeywordCnt.in`、`adKeywordCnt.total`、`adKeywordCnt.in`、`allSpKeywordCnt.total`、`allSpKeywordCnt.in`、`spKeywordCnt.total`、`spKeywordCnt.in`、`recSpKeywordCnt.total`、`recSpKeywordCnt.in`、`allSbKeywordCnt.total`、`allSbKeywordCnt.in`、`sbKeywordCnt.total`、`sbKeywordCnt.in`、`sbvKeywordCnt.total`、`sbvKeywordCnt.in` |
| sortBy | string | 否 | 排序字段。可选值：`lastRank`（自然排名）、`adLastRank`（广告排名）、`updateTime`（关键词抓取时间）、`searchesRank`（搜索排名）、`estSearchesNum`（月搜索量）。空字符串为默认系统排序 |
| desc | boolean | 否 | 是否降序，默认 `true` |
| pageNum | integer | 否 | 页码，默认 `1` |
| pageSize | integer | 否 | 每页数量，最小10，最大100，默认 `100` |


## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | SIF 业务返回码，`"1"` 表示成功 |
| msg | string | 消息 |
| total | integer | 本次实际返回的数据数量 |
| data | array | 返回数据数组（详见下方） |
| columns | array | 渲染的列 |
| type | string | 渲染的样式 |
| title | string | 标题 |
| isParentAsin | boolean | 是否是父体（pasin） |
| hasVaiants | boolean | 是否有变体 |
| abaCreateDateWeek | string | 最新周 ABA 数据对应的周时间 |
| costTime | integer | 耗时（ms） |
| costToken | integer | 消耗token |

### data 数组元素字段

| 字段 | 类型 | 说明 |
|------|------|------|
| keyword | string | 关键词 |
| translateKeyword | string | 关键词翻译，站点本地化译文 |
| asin | string | 商品ASIN |
| productNaturalRank | integer | 商品自然搜索排名。该商品在此关键词下的自然搜索结果中的位置排名，如1表示排在搜索结果第1位（首位） |
| naturalRankDisplay | string | 自然排名显示文本。自然搜索排名的字符串表示形式 |
| productAdRank | integer | 商品SP广告排名。该商品在此关键词下的Sponsored Products广告位中的排名位置，如3表示排在广告位第3位 |
| adRankDisplay | string | 广告排名显示文本。SP广告排名的字符串表示形式 |
| weeklySearchVolume | integer | 周搜索量。该关键词在亚马逊平台每周的预估搜索次数 |
| keywordPopularityRank | integer | 关键词搜索热度排名。该关键词的月搜索量在亚马逊所有关键词中的排名，数值越小表示搜索量越大 |
| totalSearchResultProductCount | integer | 该关键词下搜索结果商品总数（在售产品数） |
| trafficShare | number | 流量占比。该关键词为商品带来的流量占所有关键词总流量的比例，其中1表示100% |
| naturalTrafficShare | number | 自然流量得分占比。自然搜索流量得分 / 总得分 |
| paidTrafficShare | number | 付费广告流量得分占比。广告流量得分 / 总得分；广告合计 = sp + sb + sbv + recAd |
| naturalTrafficScore | number | 自然流量得分。该关键词为该 ASIN 带来的自然搜索曝光得分，0 = 无自然流量曝光 |
| sponsoredProductsScore | number | SP 广告常规得分。Sponsored Products 常规位的流量得分（不含 SP 推荐位） |
| brandAdScore | number | SB 品牌广告得分。Sponsored Brands 品牌广告的流量得分（常规 + 视频，总和） |
| videoAdScore | number | SBV 视频广告得分。Sponsored Brands Video 视频广告的流量得分 |
| sponsoredRecommendationScore | number | SP 推荐位得分。Trending now / Seen on social media / Customers frequently viewed / 4 stars and above 等合计得分 |
| sponsoredRecommendationBreakdown | array | SP 推荐位得分明细。每项 `{title, score, scoreRatio}` |
| clickConcentrationShare | number | ABA TOP3 点击集中度。衡量点击是否集中在头部 ASIN；注意**不是转化率** |
| clickToPurchaseConversionRate | number | 点击到购买的转化率（purchaseQty / clickQty） |
| displayPositionTypes | array | 商品展示位置类型数组。可能包含以下值：natural=自然搜索结果位；ac=Amazon's Choice推荐位；sp=Sponsored Products赞助商品广告位；top=页面顶部品牌广告位；bottom=页面底部品牌广告位；er=Editorial Recommendations编辑推荐位；vedio=视频广告位；tr=Top Rated高评分推荐位；trfob=Top Rated Frequently Bought高频购买推荐位 |
| trafficCharacteristicMarkers | array | 关键词流量特征标记数组。可能包含以下值：isMainKw=主要流量词；isAccurateKw=精准流量词；isAccurateAboveKw=精准大词；isAccurateTailKw=精准长尾词 |
| conversionPerformanceMarkers | array | 转化效果标记数组。可能包含以下值：isPurchaseKw=出单词；isQualityKw=转化优质词；isStableKw=转化平稳词；isLossKw=转化流失词；isInvalidKw=无效曝光词 |
| lastNaturalRankTime | string | 最近有效自然排名的时间 |
| lastAdRankTime | string | 最近有效SP广告排名的时间 |
| periodEndDate | string | 本周期（周粒度）结束日期 = 开始周 + 7 天（站点时间） |
| updateTime | string | 关键词数据更新时间 |

## 错误码

接口包含两层状态码：网关调用状态通过 `errcode` 字段区分，`errcode = 200` 表示网关调用成功；SIF 业务成功通过响应体中的 `code` 字段区分，`code = "1"` 表示成功。当遇到未授权等网关错误时，HTTP 状态码和 `errcode` 为对应的错误码。

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
curl -X POST https://tool-gateway.linkfox.com/sif/asinKeywords \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B0XXXXXXXX", "country": "US", "pageSize": 100, "sortBy": "estSearchesNum", "desc": true}'
```

### 带关键词筛选和条件的示例

```bash
curl -X POST https://tool-gateway.linkfox.com/sif/asinKeywords \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B0XXXXXXXX", "country": "US", "keyword": "charger", "conditions": "nfPosition,isPurchaseKw", "sortBy": "lastRank", "desc": false, "pageNum": 1, "pageSize": 50}'
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
