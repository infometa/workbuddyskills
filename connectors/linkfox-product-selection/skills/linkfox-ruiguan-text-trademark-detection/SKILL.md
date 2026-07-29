---
name: linkfox-ruiguan-text-trademark-detection
description: 面向电商产品Listing的文字商标检测与侵权风险分析。当用户提到商标检测、商标风险检查、品牌侵权筛查、产品标题商标扫描、文字商标查询、Listing合规检查、知识产权风险评估、text trademark detection, trademark infringement, brand infringement screening, listing compliance, intellectual property risk, Ruiguan时触发此技能。即使用户未明确说"商标"，只要其需求涉及检查产品文本（标题、描述、五点描述）中是否包含可能侵权的商标，也应触发此技能。
---

# 睿观-文本商标检测

## 基本信息

- **业务工具名**：`/ruiguan/textTrademarkDetection`
- **所属分组**：睿观 · 合规检测
- **功能说明**：工具中文名：睿观-文本商标检测
工具说明：支持按产品标题、产品的其他文本信息、国家来进行商标检测


## 何时使用

当用户意图与“睿观-文本商标检测”匹配，或需要以下能力时使用本工具：工具中文名：睿观-文本商标检测
工具说明：支持按产品标题、产品的其他文本信息、国家来进行商标检测

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `limit` | `integer` | 是 | 默认 `100`；最大 500 | 返回结果数量限制 |
| `regions` | `string` | 否 | 最长 1000；示例：`US`, `EM`, `GB`, `DE`, `FR`, `IT`, `ES`, `AU` | 国家/地区代码，多个用逗号分隔，支持 AU,BX,CA,DE,EM,ES,FR,GB,IT,JP,MX,TR,US,WO,CN |
| `productText` | `string` | 否 | 最长 1000 | 产品的其他文本信息 |
| `productTitle` | `string` | 是 | 最长 1000 | 产品标题 |


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
    "name": "/ruiguan/textTrademarkDetection",
    "arguments": {
      "productTitle": "example",
      "limit": 100
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 商标列表（扁平化） |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `detectId` | `string` | 否 |  | 接口调用 id |
| `costToken` | `integer` | 否 |  | 消耗token |
| `textTrademarkRadar` | `string` | 否 |  | 产品风险等级：0低风险, 1待人工核查, 2高风险 |
| `blacklistTrademarks` | `array<object>` | 否 |  | 黑名单 |
| `whitelistTrademarks` | `array<object>` | 否 |  | 白名单 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `score` | `integer` | 否 |  | 风险分数 |
| `holder` | `string` | 否 |  | 权利人 |
| `region` | `string` | 否 |  | 国家/地区代码 |
| `isFamous` | `boolean` | 否 |  | 是否著名商标 |
| `niceClass` | `array<object>` | 否 |  | 尼斯分类 |
| `regionStatus` | `string` | 否 |  | 状态 |
| `isAmazonBrand` | `boolean` | 否 |  | 是否亚马逊热搜品牌 |
| `isCommonSense` | `boolean` | 否 |  | 是否常用词 |
| `trademarkName` | `string` | 否 |  | 商标词 |
| `isActiveHolder` | `boolean` | 否 |  | 是否活跃维权人 |
| `isCompatibility` | `boolean` | 否 |  | 是否兼容性 |
| `highestModeScore` | `integer` | 否 |  | 最高风险分数（范围0-5） |
| `trademarksStatus` | `string` | 否 |  | 最高分商标词状态 |
| `applicationNumber` | `string` | 否 |  | 申请号 |
| `registrationNumber` | `string` | 否 |  | 注册号 |
| `originalTextMatches` | `array<any>` | 否 |  | 原词 |

### 嵌套输出结构：`blacklistTrademarks`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `note` | `string` | 否 |  | 备注 |
| `region` | `string` | 否 |  | 国家 |
| `trademark` | `string` | 否 |  | 商标 |

### 嵌套输出结构：`whitelistTrademarks`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `note` | `string` | 否 |  | 备注 |
| `region` | `string` | 否 |  | 国家 |
| `trademark` | `string` | 否 |  | 商标 |

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
