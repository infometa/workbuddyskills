---
name: linkfox-ruiguan-utility-patent-detection
description: 基于产品信息检测和搜索相似的实用新型/发明专利。当用户提到实用新型专利检测、专利侵权风险、专利相似度搜索、专利排查、发明专利查询、专利风险评估、TRO（临时限制令）风险分析、utility patent, invention patent detection, patent infringement risk, patent search, TRO risk, Ruiguan时触发此技能。即使用户未明确说"实用新型专利"，只要其需求涉及在目标市场销售前检查产品是否可能侵犯已有的实用新型/发明专利，也应触发此技能。
---

# 睿观-发明专利检测

## 基本信息

- **业务工具名**：`/ruiguan/utilityPatentDetection`
- **所属分组**：睿观 · 合规检测
- **功能说明**：工具中文名：睿观-发明专利检测
工具说明：支持按产品标题、产品描述、售卖国家/地区搜寻相似的发明专利


## 何时使用

当用户意图与“睿观-发明专利检测”匹配，或需要以下能力时使用本工具：工具中文名：睿观-发明专利检测
工具说明：支持按产品标题、产品描述、售卖国家/地区搜寻相似的发明专利

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `region` | `string` | 是 | 默认 `"US"`；最长 1000；示例：`US` | 商品想要售卖的国家/地区代码，多个用逗号分隔，当前支持 US |
| `topNumber` | `integer` | 是 | 默认 `100`；最小 10；最大 200 | 召回数量，最大200 |
| `productTitle` | `string` | 是 | 最长 1000 | 产品标题 |
| `productDescription` | `string` | 是 | 最长 1000 | 产品描述 |


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
    "name": "/ruiguan/utilityPatentDetection",
    "arguments": {
      "productTitle": "example",
      "productDescription": "example",
      "region": "US",
      "topNumber": 100
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
| `detectId` | `string` | 否 |  | 检测id |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `title` | `string` | 否 |  | 发明专利标题 |
| `claims` | `string` | 否 |  | 权利要求 |
| `images` | `array<any>` | 否 |  | 专利附图 |
| `region` | `string` | 否 |  | 受理局 |
| `titleCn` | `string` | 否 |  | 发明专利标题(中文) |
| `troCase` | `boolean` | 否 |  | 是否有TRO维权史 |
| `claimsCn` | `string` | 否 |  | 权利要求(中文) |
| `inventors` | `array<any>` | 否 |  | 发明家 和 国家拼接 数组格式 |
| `troHolder` | `boolean` | 否 |  | 是否是TRO权利人的专利 |
| `applicants` | `array<any>` | 否 |  | 申请人 和 国家 拼接 数组格式 |
| `cpcKindRaw` | `array<object>` | 否 |  | cpc分类（原始 JSONArray） |
| `similarity` | `number` | 否 |  | 相似度 |
| `classNumList` | `array<any>` | 否 |  | 类别号路径列表，格式 classNum1 > classNum2 > classNum3，由 cpcKind 结构生成 |
| `specification` | `string` | 否 |  | 说明书 |
| `patentAbstract` | `string` | 否 |  | 摘要 |
| `patentImageUrl` | `string` | 否 |  | 专利封面图 |
| `patentValidity` | `string` | 否 |  | 专利有效性 Active/Invalid |
| `priorityNumber` | `array<any>` | 否 |  | 优先权号 数组 |
| `applicationDate` | `string` | 否 |  | 申请日 yyyy-MM-dd |
| `globalUtilityId` | `string` | 否 |  | 专利id |
| `publicationDate` | `string` | 否 |  | 公开日 yyyy-MM-dd |
| `specificationCn` | `string` | 否 |  | 说明书(中文) |
| `estimatedDueDate` | `string` | 否 |  | 预估到期日 yyyy-MM-dd |
| `patentAbstractCn` | `string` | 否 |  | 摘要（中文） |
| `applicationNumber` | `string` | 否 |  | 申请号 |
| `inventorAddresses` | `array<any>` | 否 |  | 发明人地址 数组格式 |
| `publicationNumber` | `string` | 否 |  | 公开号 |
| `applicantAddresses` | `array<any>` | 否 |  | 权利人地址 数组格式 |
| `relatedPublicationDate` | `array<any>` | 否 |  | 首次公开日 数组 yyyy-MM-dd |

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
