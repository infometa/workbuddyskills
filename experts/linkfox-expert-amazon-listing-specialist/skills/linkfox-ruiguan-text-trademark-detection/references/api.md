# 睿观-文本商标检测 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/ruiguan/textTrademarkDetection`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productTitle | string | 是 | 产品标题，用于商标检测（最大1000字符） |
| regions | string | 否 | 国家/地区代码，多个用逗号分隔。支持值：US、EM、GB、DE、FR、IT、ES、AU、CA、MX、JP、CN、WO、TR、BX |
| limit | integer | 是 | 返回结果数量限制（默认100，最大500） |
| productText | string | 否 | 产品的其他文本信息，如五点描述或产品描述（最大1000字符） |


## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 匹配到的商标记录数 |
| data | array | 商标列表（扁平化），每个元素包含以下字段 |
| detectId | string | 接口调用 ID |
| columns | array | 渲染的列定义 |
| blacklistTrademarks | array | 文本中检测到的黑名单商标 |
| whitelistTrademarks | array | 文本中检测到的白名单（安全）商标 |
| textTrademarkRadar | string | 产品风险等级："0" = 低风险，"1" = 待人工核查，"2" = 高风险 |
| costToken | integer | 消耗token |
| type | string | 渲染的样式 |

### data[] 元素字段

| 字段 | 类型 | 说明 |
|------|------|------|
| trademarkName | string | 商标词 |
| region | string | 国家/地区代码 |
| score | integer | 风险分数 |
| highestModeScore | integer | 最高风险分数（范围0-5） |
| trademarksStatus | string | 最高分商标词状态 |
| regionStatus | string | 商标在匹配地区的状态 |
| holder | string | 权利人 |
| applicationNumber | string | 申请号 |
| registrationNumber | string | 注册号 |
| isFamous | boolean | 是否著名商标 |
| isAmazonBrand | boolean | 是否亚马逊热搜品牌 |
| isActiveHolder | boolean | 是否活跃维权人 |
| isCompatibility | boolean | 是否兼容性 |
| isCommonSense | boolean | 是否常用词 |
| niceClass | array | 尼斯分类 |
| originalTextMatches | array | 触发匹配的原词 |

### blacklistTrademarks[] 和 whitelistTrademarks[] 元素字段

| 字段 | 类型 | 说明 |
|------|------|------|
| trademark | string | 商标名称 |
| region | string | 国家/地区代码 |
| note | string | 备注 |

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
curl -X POST https://tool-gateway.linkfox.com/ruiguan/textTrademarkDetection \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "productTitle": "Wireless Bluetooth Headphones Noise Cancelling Over Ear",
    "regions": "US",
    "limit": 100
  }'
```

### 附带产品文本的示例

```bash
curl -X POST https://tool-gateway.linkfox.com/ruiguan/textTrademarkDetection \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "productTitle": "Portable USB-C Charger Fast Charging Power Bank",
    "productText": "Compatible with iPhone, Samsung Galaxy, supports QC 3.0",
    "regions": "US,EM,GB",
    "limit": 200
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
