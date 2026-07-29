---
name: linkfox-ruiguan-detection-patent-design
description: 基于睿观的外观专利侵权检测，支持25+国家/地区的图片专利检索。当用户提到外观专利检测、专利侵权检查、专利风险分析、TRO案件查询、外观设计专利搜索、设计专利相似度、产品专利排查、design patent detection, patent infringement, design patent, TRO cases, patent risk, patent search, Ruiguan时触发此技能。即使用户未明确提及"外观专利"，只要其需求涉及检查产品图片是否可能侵犯已有的外观设计专利，或提到侵权、专利、TRO、外观专利等关键词，也应触发此技能。
---

# 睿观-外观专利检测

## 基本信息

- **业务工具名**：`/ruiguan/detectionPatentDesign`
- **所属分组**：睿观 · 合规检测
- **功能说明**：支持按产品标题、图片URL、专利国家来进行专利检测
- **关键词**：侵权、睿观、外观专利 、专利、案件


## 何时使用

当用户意图与“睿观-外观专利检测”匹配，或需要以下能力时使用本工具：支持按产品标题、图片URL、专利国家来进行专利检测

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `topLoc` | `string` | 否 | 格式 `^(0[1-9]\|1[0-9]\|2[0-9]\|3[0-2]\|ALL)(,(0[1-9]\|1[0-9]\|2[0-9]\|3[0-2]\|ALL))*$`；示例：`01`, `02`, `03`, `04`, `05`, `06`, `07`, `08` | 指定检索的一级LOC范围, 不指定时代表使用模型LOC预测服务的结果, 可多选, 多选时多个编码用逗号隔开，如 01,02 |
| `regions` | `string` | 否 | 默认 `"US"`；格式 `^(SE\|EU\|CH\|IE\|BR\|MX\|US\|WO\|GB\|IL\|JP\|IN\|DK\|DE\|AU\|IT\|NZ\|AT\|CA\|BX\|FI\|FR\|CN\|KR\|TH)(,(SE\|EU\|CH\|IE\|BR\|MX\|US\|WO\|GB\|IL\|JP\|IN\|DK\|DE\|AU\|IT\|NZ\|AT\|CA\|BX\|FI\|FR\|CN\|KR\|TH))*$`；示例：`SE`, `EU`, `CH`, `IE`, `BR`, `MX`, `US`, `WO` | 商品所售卖国家/地区代码, 可多选, 多选时多个编码用逗号隔开，如： US,CH,IE |
| `imageUrl` | `string` | 是 | 最长 1000 | 产品图片文件URL |
| `queryMode` | `string` | 是 | 默认 `"hybrid"`；格式 `physical\|line\|hybrid`；示例：`physical`, `line`, `hybrid` | 检索模式 |
| `topNumber` | `integer` | 是 | 默认 `100`；最大 100 | 召回专利数量 |
| `enableRadar` | `boolean` | 否 | 默认 `true` | 是否启用雷达图 |
| `patentStatus` | `string` | 否 | 默认 `"1"`；最长 1000；示例：`1`, `0` | 专利有效性, 可多选, 多选时多个状态用逗号隔开，如 1,0 |
| `productTitle` | `string` | 否 | 最长 1000 | 产品标题 |
| `sourceLanguage` | `string` | 否 | 最长 1000 | 原语言，需要标记，以便统一翻译成英文，文本为英语时传空即可.例如：zh-CN |
| `productDescription` | `string` | 否 | 最长 1000 | 产品描述 |


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
    "name": "/ruiguan/detectionPatentDesign",
    "arguments": {
      "imageUrl": "https://example.com/item",
      "topNumber": 100,
      "queryMode": "hybrid"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 专利列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `images` | `array<any>` | 否 |  | 专利图片列表 |
| `troCase` | `boolean` | 否 |  | 是否有TRO维权史 |
| `abstracts` | `string` | 否 |  | 专利摘要 |
| `grantDate` | `string` | 否 |  | 专利授权日 |
| `inventors` | `array<any>` | 否 |  | 发明人 |
| `patentLoc` | `string` | 否 |  | 该专利的loc分类，多个loc英文逗号隔开 |
| `troHolder` | `boolean` | 否 |  | 是否是TRO权利人的专利 |
| `applicants` | `array<any>` | 否 |  | 申请人 |
| `locOneInfo` | `string` | 否 |  | loc一级详情 |
| `locTwoInfo` | `string` | 否 |  | loc二级详情 |
| `patentProd` | `string` | 否 |  | 专利标题 |
| `similarity` | `string` | 否 |  | 专利与产品相似度 |
| `radarResult` | `object` | 否 |  |  |
| `isSketchText` | `string` | 否 |  | 是否线稿图 |
| `patentFamily` | `array<object>` | 否 |  | 同族专利 |
| `patentProdCn` | `string` | 否 |  | 专利标题中文 |
| `globalImageId` | `string` | 否 |  | 专利图片的ID |
| `specification` | `string` | 否 |  | 专利说明书 |
| `globalPatentId` | `string` | 否 |  | 全球专利ID |
| `patentImageUrl` | `string` | 否 |  | 与产品图片相似度最高的专利附图 |
| `patentValidity` | `string` | 否 |  | 专利有效性 |
| `applicationDate` | `string` | 否 |  | 专利申请日 |
| `publicationDate` | `string` | 否 |  | 专利公开日 |
| `estimatedDueDate` | `string` | 否 |  | 预估到期日 |
| `applicationNumber` | `string` | 否 |  | 专利申请号 |
| `publicationNumber` | `string` | 否 |  | 专利公开号 |
| `applicantAddresses` | `array<any>` | 否 |  | 申请人地址 |
| `registrationOfficeCode` | `string` | 否 |  | 专利注册受理局 |

### 嵌套输出结构：`data.radarResult`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `exp` | `string` | 否 |  | 预期描述 |
| `same` | `boolean` | 否 |  | 是否疑似侵权 |

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
