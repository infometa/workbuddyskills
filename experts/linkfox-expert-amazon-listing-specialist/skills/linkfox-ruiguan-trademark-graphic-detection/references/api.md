# 睿观-图形商标检测 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/ruiguan/trademarkGraphicDetection`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| imageUrl | string | 是 | 产品图片URL或base64编码的图片数据（最大1000字符） |
| topNumber | integer | 是 | 返回YOLO坐标的最大数量，默认 `5`，最大 `100`。实际返回数量可能少于传参数量 |
| productTitle | string | 否 | 产品标题，用于上下文感知检测（最大1000字符） |
| trademarkName | string | 否 | 可能的图形logo名称，用于缩小检索范围（最大1000字符） |
| regions | string | 否 | 需要检测的国家/地区代码，多个时使用逗号隔开，不传默认全部国家。可选值：US（美国）、WO（世界知识产权）、ES（西班牙）、GB（英国）、DE（德国）、IT（意大利）、CA（加拿大）、MX（墨西哥）、EM（欧盟）、AU（澳大利亚）、FR（法国）、JP（日本）、TR（土耳其）、BX（玻利维亚）、CN（中国） |
| enableLocalizing | boolean | 否 | 是否开启切图，默认 `false` |
| enableRadar | boolean | 否 | 是否开启雷达监测，默认 `true` |


## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| boundingBoxCount | integer | 检测结果数量 |
| radarResult | string | 雷达检测结果 |
| total | integer | 记录数 |
| data | array | 检测结果列表（详见下方） |
| detectId | string | 检测ID |
| columns | array | 渲染的列定义 |
| costToken | integer | 消耗token |
| type | string | 渲染的样式 |

### data 数组项字段

`data` 数组中每个对象包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| image | string | 匹配的商标图片地址 |
| boundingBox | string | YOLO坐标（逗号隔开） |
| subRadarResult | string | 子雷达检测结果 |
| applicationNumber | string | 申请号 |
| niceClassName | string | 尼斯分类名称（逗号隔开） |
| applicantName | string | 权利人（逗号隔开） |
| tradeMarkStatus | string | 商标状态，枚举值：`"DEL"`、`"ended"`、`"registered"`、`"act"`、`"pend"`、`"filed"`、`""` |
| niceClass | array | 尼斯分类详情 |
| similarity | number | 相似度（0到1，值越高越相似） |
| registrationNumber | string | 注册号 |
| registrationOfficeCode | string | 商标受理局 |
| registrationDate | string | 注册日期 |
| bid | string | logo标识 |
| trademarkName | string | 图片中的文字商标名称 |
| applicationDate | string | 申请日期 |

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
curl -X POST https://tool-gateway.linkfox.com/ruiguan/trademarkGraphicDetection \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"imageUrl": "https://example.com/product-image.jpg", "topNumber": 5, "productTitle": "无线蓝牙耳机", "regions": "US,EM"}'
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
