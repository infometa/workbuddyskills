# 睿观-外观专利检测 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/ruiguan/detectionPatentDesign`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY`（或 `LINKFOXAGENT_API_KEY`）读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| imageUrl | string | 是 | - | 产品图片文件URL，用于与专利数据库进行比对（最大1000字符） |
| queryMode | string | 是 | hybrid | 检索模式：`physical`（实物图检索）、`line`（线条图检索）、`hybrid`（混合检索）。最大1000字符 |
| topNumber | integer | 是 | 100 | 召回专利数量（最大100） |
| regions | string | 否 | US | 商品所售卖国家/地区代码，多选时用逗号隔开（如 `US,EU,CN`）。支持：US、EU、CN、JP、KR、DE、GB、FR、IT、AU、CA、BR、MX、IN、TH、SE、CH、IE、IL、DK、NZ、AT、BX、FI、WO。最大1000字符 |
| productTitle | string | 否 | - | 产品标题，用于补充检索上下文（最大1000字符） |
| productDescription | string | 否 | - | 产品描述，用于补充检索上下文（最大1000字符） |
| patentStatus | string | 否 | 1 | 专利有效性筛选：`1`（有效专利）、`0`（失效专利）、`1,0`（全部）。最大1000字符 |
| enableRadar | boolean | 否 | true | 是否启用雷达图（AI侵权判定分析） |
| topLoc | string | 否 | - | 指定检索的一级LOC范围（如 `06,07`）。格式：`^(0[1-9]\|1[0-9]\|2[0-9]\|3[0-2]\|ALL)(,(0[1-9]\|1[0-9]\|2[0-9]\|3[0-2]\|ALL))*$`。不指定时使用模型LOC预测服务的结果 |
| sourceLanguage | string | 否 | - | 原语言代码，需要标记以便统一翻译成英文（如 `zh-CN`）。文本为英语时传空即可。最大1000字符 |


## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 返回的专利记录总数 |
| data | array | 专利列表（详见下方专利对象） |
| columns | array | 渲染的列定义 |
| costToken | integer | 消耗token |
| type | string | 渲染的样式 |

### 专利对象（`data` 数组中的每个元素）

| 字段 | 类型 | 说明 |
|------|------|------|
| applicationNumber | string | 专利申请号 |
| publicationNumber | string | 专利公开号 |
| patentProd | string | 专利标题（英文） |
| patentProdCn | string | 专利标题（中文） |
| similarity | string | 专利与产品图片的相似度（0-1） |
| patentImageUrl | string | 与产品图片相似度最高的专利附图URL |
| images | array | 专利图片列表 |
| abstracts | string | 专利摘要 |
| specification | string | 专利说明书 |
| inventors | array | 发明人列表 |
| applicants | array | 申请人列表 |
| applicantAddresses | array | 申请人地址 |
| troCase | boolean | 是否有TRO维权史 |
| troHolder | boolean | 是否是TRO权利人的专利 |
| radarResult | object | AI雷达分析结果 |
| radarResult.same | boolean | 是否疑似侵权 |
| radarResult.exp | string | 预期描述（雷达判定说明） |
| patentLoc | string | 该专利的LOC分类（多个用逗号隔开） |
| locOneInfo | string | LOC一级详情 |
| locTwoInfo | string | LOC二级详情 |
| patentValidity | string | 专利有效性 |
| applicationDate | string | 专利申请日 |
| publicationDate | string | 专利公开日 |
| grantDate | string | 专利授权日 |
| estimatedDueDate | string | 预估到期日 |
| registrationOfficeCode | string | 专利注册受理局 |
| patentFamily | array | 同族专利列表 |
| globalPatentId | string | 全球专利ID |
| globalImageId | string | 专利图片的ID |
| isSketchText | string | 是否线稿图 |

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
curl -X POST https://tool-gateway.linkfox.com/ruiguan/detectionPatentDesign \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://example.com/product.jpg",
    "queryMode": "hybrid",
    "topNumber": 50,
    "regions": "US",
    "enableRadar": true
  }'
```

## 多地区检索示例

```bash
curl -X POST https://tool-gateway.linkfox.com/ruiguan/detectionPatentDesign \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://example.com/product.jpg",
    "queryMode": "physical",
    "topNumber": 100,
    "regions": "US,EU,CN",
    "productTitle": "便携式无线充电支架",
    "productDescription": "一款可折叠的智能手机无线充电支架",
    "patentStatus": "1",
    "enableRadar": true
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
