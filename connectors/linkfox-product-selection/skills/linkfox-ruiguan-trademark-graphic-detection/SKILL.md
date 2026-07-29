---
name: linkfox-ruiguan-trademark-graphic-detection
description: 产品图片的图形商标检测与相似度搜索。当用户提到商标检测、图形商标搜索、Logo侵权检查、商标相似度分析、图片商标风险评估、产品图片商标筛查、graphic trademark detection, logo infringement, trademark similarity, trademark risk, image trademark screening, Ruiguan时触发此技能。即使用户未明确说"商标检测"，只要其需求涉及将产品图片与已注册的图形商标进行比对或评估商标侵权风险，也应触发此技能。
---

# 睿观-图形商标检测

## 基本信息

- **业务工具名**：`/ruiguan/trademarkGraphicDetection`
- **所属分组**：睿观 · 合规检测
- **功能说明**：支持按产品标题、图片URL、国家来进行图形商标检测


## 何时使用

当用户意图与“睿观-图形商标检测”匹配，或需要以下能力时使用本工具：支持按产品标题、图片URL、国家来进行图形商标检测

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `regions` | `string` | 否 | 格式 `^(US\|WO\|ES\|GB\|DE\|IT\|CA\|MX\|EM\|AU\|FR\|JP\|TR\|BX\|CN)(,(US\|WO\|ES\|GB\|DE\|IT\|CA\|MX\|EM\|AU\|FR\|JP\|TR\|BX\|CN))*$`；示例：`US`, `WO`, `ES`, `GB`, `DE`, `IT`, `CA`, `MX` | 需要检测的国家/地区，不传默认全部国家, 选择多个时，使用逗号隔开，如：US,WO,ES |
| `imageUrl` | `string` | 是 | 最长 1000 | 产品图片base64文件 |
| `topNumber` | `integer` | 是 | 默认 `5`；最大 100 | 返回yolo坐标的最大数量（有可能返回数量少于传参数量） |
| `enableRadar` | `boolean` | 否 | 默认 `true` | 是否雷达监测 |
| `productTitle` | `string` | 否 | 最长 1000 | 产品标题 |
| `trademarkName` | `string` | 否 | 最长 1000 | 可能的图形logo名称 |
| `enableLocalizing` | `boolean` | 否 | 默认 `false` | 是否开切图,不传默认不开启 |


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
    "name": "/ruiguan/trademarkGraphicDetection",
    "arguments": {
      "topNumber": 5,
      "imageUrl": "https://example.com/item"
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 检测结果列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `detectId` | `string` | 否 |  | 检测id |
| `costToken` | `integer` | 否 |  | 消耗token |
| `radarResult` | `string` | 否 |  | 雷达检测结果 |
| `boundingBoxCount` | `integer` | 否 |  | 检测结果数量 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `bid` | `string` | 否 |  | logo标识 |
| `image` | `string` | 否 |  | 图片地址 |
| `niceClass` | `array<object>` | 否 |  | 尼斯分类名称 |
| `similarity` | `number` | 否 |  | 相似度 |
| `boundingBox` | `string` | 否 |  | yolo坐标（逗号隔开） |
| `applicantName` | `string` | 否 |  | 权利人（逗号隔开） |
| `niceClassName` | `string` | 否 |  | 尼斯分类名称（逗号隔开） |
| `trademarkName` | `string` | 否 |  | 图片中的文字商标名称 |
| `subRadarResult` | `string` | 否 |  | 子雷达检测结果 |
| `applicationDate` | `string` | 否 |  | 申请日期 |
| `tradeMarkStatus` | `string` | 否 |  | 商标状态，枚举："DEL","ended"，"registered","act","pend","filed","" |
| `registrationDate` | `string` | 否 |  | 注册日期 |
| `applicationNumber` | `string` | 否 |  | 申请号 |
| `registrationNumber` | `string` | 否 |  | 注册号 |
| `registrationOfficeCode` | `string` | 否 |  | 商标受理局 |

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
