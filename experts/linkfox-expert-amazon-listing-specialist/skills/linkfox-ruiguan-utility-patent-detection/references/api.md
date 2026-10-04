# 睿观-发明专利检测 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/ruiguan/utilityPatentDetection`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productTitle | string | 是 | 产品标题，最大1000字符 |
| productDescription | string | 是 | 产品描述，最大1000字符 |
| region | string | 是 | 商品想要售卖的国家/地区代码，多个用逗号分隔，当前支持 US。默认 `US` |
| topNumber | integer | 是 | 召回数量，范围：10--200，默认 `100` |


## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 记录数 |
| detectId | string | 检测ID |
| costToken | integer | 消耗token |
| type | string | 渲染的样式 |
| columns | array | 渲染的列定义 |
| data | array | 专利列表（详见下方） |

### 专利对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| globalUtilityId | string | 专利ID |
| title | string | 发明专利标题 |
| titleCn | string | 发明专利标题（中文） |
| similarity | number | 产品与该专利的相似度（0--1） |
| patentValidity | string | 专利有效性：`Active`（有效）或 `Invalid`（无效） |
| applicationNumber | string | 申请号 |
| applicationDate | string | 申请日（yyyy-MM-dd） |
| publicationNumber | string | 公开号 |
| publicationDate | string | 公开日（yyyy-MM-dd） |
| estimatedDueDate | string | 预估到期日（yyyy-MM-dd） |
| region | string | 受理局 |
| patentAbstract | string | 摘要 |
| patentAbstractCn | string | 摘要（中文） |
| claims | string | 权利要求 |
| claimsCn | string | 权利要求（中文） |
| specification | string | 说明书 |
| specificationCn | string | 说明书（中文） |
| inventors | array | 发明家和国家拼接，数组格式 |
| inventorAddresses | array | 发明人地址，数组格式 |
| applicants | array | 申请人和国家拼接，数组格式 |
| applicantAddresses | array | 权利人地址，数组格式 |
| priorityNumber | array | 优先权号，数组格式 |
| relatedPublicationDate | array | 首次公开日（yyyy-MM-dd），数组格式 |
| patentImageUrl | string | 专利封面图 |
| images | array | 专利附图 |
| classNumList | array | 类别号路径列表，格式：classNum1 > classNum2 > classNum3 |
| cpcKindRaw | array | CPC分类（原始 JSONArray） |
| troCase | boolean | 是否有TRO维权史 |
| troHolder | boolean | 是否是TRO权利人的专利 |

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
curl -X POST https://tool-gateway.linkfox.com/ruiguan/utilityPatentDetection \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"productTitle": "便携式USB-C 65W氮化镓快充充电器", "productDescription": "一款紧凑型65W氮化镓USB-C快充充电器，配备可折叠插脚，支持PD3.0和QC4.0协议，双USB-C端口和一个USB-A端口，适用于笔记本电脑、手机和平板电脑。", "region": "US", "topNumber": 100}'
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
