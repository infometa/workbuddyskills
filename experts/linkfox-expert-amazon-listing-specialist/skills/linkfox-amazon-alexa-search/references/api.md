# 亚马逊 Alexa 购物助手 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/amazon/alexaSearch`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompts | string[] | 是 | 长度在255个字符以内。对话提示词数组，仅支持 **1 条**。每次调用只能传入 1 个问题。如需追问，agent 须自行总结上一轮回答的关键信息（推荐商品、ASIN、关键结论等），拼接新问题后作为新的 `prompts[0]` 发起新请求。每次调用是独立的新会话，不保留跨次调用的历史上下文 |
| format | string | 否 | 响应格式，`markdown`（默认）返回可读报告；`json` 返回结构化数据数组 |
| url | string | 否 | 联动页面 URL，用于补充 Alexa 当前答复的页面上下文。仅在用户提供了**具体页面**（分类页 / 搜索结果页 / 商品详情页等）时才传入；亚马逊首页（如 `https://www.amazon.com/`）**无需传**该参数 |

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| stdout | string | Markdown 格式问答报告，包含每一轮的用户问题、Alexa 回答、推荐商品、可继续追问的问题；仅 `format=markdown` 时返回 |
| data | array | 结构化对话结果数组；仅 `format=json` 时返回 |
| resultsNum | integer | Alexa 实际答复的对话轮次数量；为 0 表示未产生有效回答 |
| code | string | 业务状态码，成功为 `"200"`（同 `errcode` 数值版） |
| errcode | integer | 业务状态码（HTTP 层一般为 200，业务成功与否以此字段为准） |
| msg / errmsg | string | 响应消息，成功为 `ok` |
| costTime | integer | 接口耗时，单位毫秒 |
| costToken | integer | 本次调用消耗 Token 数；上游成功才计费 |
| taskId | string | 上游返回的本次任务标识 |
| type | string | 渲染样式：`stdoutWorkbenches`（markdown）或 `json` |

### `data[*]` 结构（`format=json`）

| 字段 | 类型 | 说明 |
|------|------|------|
| prompt | string | 当前轮次发送给 Alexa 的提示词 |
| content | string | Alexa 本轮回答的文本内容 |
| screenshot | string | 本轮对话截图链接 |
| followUpQuestions | string[] | Alexa 推荐继续追问的问题列表 |
| products | array | 推荐商品分组列表，每个分组包含 `title` 和 `items` |
| products[].title | string | 推荐分组标题 |
| products[].items[].asin | string | 商品 ASIN |
| products[].items[].title | string | 商品标题 |
| products[].items[].url | string | 商品详情页 URL |
| products[].items[].cover | string | 商品封面图 URL |
| products[].items[].price | string | 现价（带币种） |
| products[].items[].originalPrice | string | 原价或划线价 |
| products[].items[].score | string | 评分 |
| products[].items[].ratingsCount | string | 评价数量 |
| products[].items[].describe | string | 商品简介 |

## 错误码

正常情况下，接口的 HTTP 状态码均为 200，业务的成功与否通过响应体中的 `errcode` / `code` 字段区分（`200` 表示成功，其他值表示业务错误）。当遇到未授权等情况时，HTTP 状态码为 401，且对应的 `errcode` 也是 401。

| errcode | 含义 | 处理建议 |
|---------|------|----------|
| 200 | 成功 | 正常解析 `stdout` 或 `data` 字段 |
| 401 | 认证失败 | HTTP 401 或 authorized error：按 SKILL.md 的 **## 解决认证和积分问题** 处理。 |
| 402 | 计费/积分不足 | HTTP 402：按 SKILL.md 的 **## 解决认证和积分问题** 处理。 |
| 其他非 200 值 | 业务异常 | 参考 `errmsg` / `msg` 字段获取具体错误原因 |

错误响应示例：

```json
{
    "errcode": 401,
    "errmsg": "authorized error"
}
```

## curl 示例

**Markdown 格式（默认）：**

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/alexaSearch \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "prompts": ["best wireless earbuds for running"]
      }'
```

**JSON 格式：**

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/alexaSearch \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "prompts": ["best electric kettle on Amazon US"],
        "format": "json"
      }'
```

成功响应（节选）：

```json
{
  "msg": "ok",
  "errcode": 200,
  "code": "200",
  "stdout": "# 亚马逊 Alexa 购物助手\n\n## 问题 1：best wireless earbuds for running\n\n### Alexa 回答\n- ...\n\n### 推荐商品\n- ...\n\n### 可继续追问的问题\n- ...\n",
  "resultsNum": 1,
  "costTime": 12000,
  "costToken": 1500,
  "type": "stdoutWorkbenches",
  "taskId": "1779367311421-d728ce53704fc86e"
}
```

---

## Feedback API

> This endpoint is **separate** from the tool API above. Do not mix the two base URLs.

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-amazon-alexa-for-shopping",
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
