---
name: linkfox-aba-intelligent-query
description: 亚马逊ABA（品牌分析）搜索词数据的查询与分析，涵盖15个站点近3年的周维度数据。当用户提到ABA数据、亚马逊搜索词分析、关键词挖掘、搜索排名趋势、市场机会分析、季节性关键词、高点击低转化分析、蓝海词发现、竞品关键词分析、ABA data, search term report, keyword mining, search ranking trends, blue ocean keywords, click share, conversion share, seasonal keywords, market opportunity analysis, competitor keywords时触发此技能。即使用户未明确提及"ABA"，只要其需求涉及亚马逊搜索词数据和排名分析，也应触发此技能。
---

# ABA-数据挖掘

## 基本信息

- **业务工具名**：`/aba/intelligentQuery`
- **所属分组**：ABA · 亚马逊数据挖掘
- **功能说明**：支持亚马逊多站点的ABA进行SQL统计和数据发现，返回值的rank越小则表示排名越好。
- **关键词**：亚马逊ABA，STR数据分析，关键词挖掘，市场垄断分析，低效词诊断


## 何时使用

当用户意图与“ABA-数据挖掘”匹配，或需要以下能力时使用本工具：支持亚马逊多站点的ABA进行SQL统计和数据发现，返回值的rank越小则表示排名越好。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `uid` | `string` | 否 | 最长 1000 | 用户ID |
| `chatId` | `string` | 否 | 最长 1000 | 对话ID |
| `region` | `string` | 否 | 默认 `"US"`；格式 `DE\|BR\|US\|CA\|AU\|JP\|AE\|ES\|FR\|IT\|SA\|TR\|MX\|SE\|NL`；示例：`DE`, `BR`, `US`, `CA`, `AU`, `JP`, `AE`, `ES` | 亚马逊市场（站点） |
| `stepId` | `string` | 否 | 最长 1000 | 调用顺序 |
| `memberId` | `string` | 否 | 最长 1000 | 成员ID |
| `messageId` | `string` | 否 | 最长 1000 | 消息ID |
| `createDownloadUrl` | `boolean` | 否 | 默认 `false`；示例：`true`, `false` | 是否生成下载链接。当用户要求下载、导出、或生成下载链接时，设置为true。 |
| `analysisDescription` | `string` | 是 | 最长 1000；示例：`筛选美国站，关键词“gift”在过去12周的搜索热度排名。`, `筛选美国站，关键词包含“gift”，2025年Q1和全年的平均搜索排名都大于50万，但最新排名冲进5万-10万的搜索词。`, `筛选美国站，最新排名在20万以内，且4周前的排名比8周前提升30%，本周的排名比4周前提升30%的搜索词。`, `筛选美国站，筛选当前搜索排名在20000以内，近三个月点击占比Top 1的Asin的转化率占比低于5%的搜索词。相同搜索词相同Asin值保留最新的一个。`, `筛选美国站，包含“cup”的关键词中，去年（2024年）1-9月份排名未进入50万，10-11月份连续进入20万的词。`, `筛选筛选美国站关键词包含“hat”的，最新搜索排名在5万-20万之间，且近3个月来点击占比大于20%，转化占比小于10%的ASIN。相同搜索词和ASIN仅保留点击占比和转化占比的比例最小数据。`, `筛选美国站，关键词包含“charger”的，当前排名在20万开外的，近2个月的平均转化占比大于平均转化占比1.5倍的关键词，以及相应的ASIN。`, `找到美国站“charger”的长尾词中，近一个月才进入排名榜单，且当前排名在50万以内的所有词。` | 需要查询或分析的具体内容。应客观反映用户意图，不能曲解用户需求。 |


## MCP 调用示例

向以下地址发起 HTTP `POST`：

```text
https://mcp-tool-gateway.linkfox.com/mcp/any-tool
```

请求体：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "/aba/intelligentQuery",
    "arguments": {
      "analysisDescription": "筛选美国站，关键词“gift”在过去12周的搜索热度排名。"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `msg` | `string` | 否 |  | 消息 |
| `code` | `string` | 否 |  | 返回码 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `title` | `string` | 否 |  | 标题 |
| `total` | `integer` | 否 |  | 结果总数 |
| `tables` | `array<object>` | 否 |  | 查询结果数据列表数组 |
| `success` | `boolean` | 否 |  | 本次数据挖掘是否最终成功执行 |
| `costTime` | `integer` | 否 |  | 耗时 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `downloadUrl` | `string` | 否 |  | CSV 文件下载 URL，当 createDownloadUrl 为 true 时返回 |
| `downloadNote` | `string` | 否 |  | 文件下载提示。提醒用户下载文件，或通过下载文件查看完整数据。 |

### 嵌套输出结构：`tables`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 查询结果数据列表 |
| `name` | `string` | 否 |  | sheet的名称 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `userExplanation` | `string` | 否 |  | 用户的分析意图 |
| `analysisStatement` | `string` | 否 |  | LLM生成的SLS分析语句 |

## 响应处理建议

1. 先检查 JSON-RPC 外层是否包含 `error`。
2. 成功时读取 `result`，并继续解析其中的 `content`、`data`、`products`、`items` 或其他业务字段。
3. 如果响应为 `text/event-stream`，按 SSE 事件读取 `data:` 内容，再解析 JSON。
4. 保留分页字段、总数、失败明细及 `costToken`。
5. 向用户输出分析结论，不要直接倾倒大段原始 JSON。

## 原始 Schema

原始的Input Schema 和 Output Schema 参考 references/schema.md

## 解决认证和积分问题

异常情况：未配置 `LINKFOX_AGENT_API_KEY` 和 `LINKFOXAGENT_API_KEY`；响应 401 或 402；消息含"积分余额不足/quota exceeded/insufficient balance/套餐到期/需充值"等。

措施：优先用 skill 内 onboarding.md 引导；找不到则加载 /linkfox-onboarding skill。 根据它的指引操作。

**注意**：你是workbuddy，并且渠道是workbuddy，使用linkfox-onboarding登录注册时**必须**传递channel为 workbuddy。这非常重要！
