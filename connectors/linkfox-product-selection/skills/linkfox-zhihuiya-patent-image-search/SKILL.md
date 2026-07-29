---
name: linkfox-zhihuiya-patent-image-search
description: 基于智慧芽的专利图片相似度搜索，支持通过图片URL检索外观设计专利。当用户提到专利图片搜索、外观设计专利侵权检查、外观专利搜索、视觉专利查询、以图搜专利、专利相似度检测、专利图片匹配、洛迦诺分类搜索、检查产品设计是否侵犯已有专利、patent image search, design patent search, patent reverse image search, design patent lookup, PatSnap, patent similarity时触发此技能。即使用户未明确提及"智慧芽"或"专利图片"，只要其需求涉及通过图片查找相似专利或排查外观设计专利风险，也应触发此技能。
---

# 智慧芽-专利图像检索

## 基本信息

- **业务工具名**：`/zhihuiya/patentImageSearch`
- **所属分组**：智慧芽 · 专利数据
- **功能说明**：支持按图片URL、专利国家来进行专利检测（包括外观专利和实用新型专利）


## 何时使用

当用户意图与“智慧芽-专利图像检索”匹配，或需要以下能力时使用本工具：支持按图片URL、专利国家来进行专利检测（包括外观专利和实用新型专利）

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `loc` | `string` | 否 | 最长 1000 | LOC分类(洛迦诺分类号)，多个分类号可以用逻辑符AND/OR/NOT连接 |
| `url` | `string` | 是 | 最长 1000 | 图像的URL |
| `lang` | `string` | 否 | 默认 `"original"`；最长 1000；示例：`original`, `cn`, `en` | 设置标题的语言优先选择，可以选cn、en、original |
| `field` | `string` | 否 | 默认 `"SCORE"`；最长 1000；示例：`SCORE`, `APD`, `PBD`, `ISD` | 返回结果排序field支持SCORE,APD,PBD,ISD |
| `limit` | `integer` | 否 | 默认 `10`；最大 100 | 返回专利条数, 1 <= limit <= 100，默认为10 |
| `model` | `integer` | 是 | 示例：`1`, `2`, `3`, `4` | 选择图像检索模型，外观专利：1-智能联想，2-搜索此图；实用新型专利：3-匹配形状，4-匹配形状/图案/色彩 |
| `order` | `string` | 否 | 默认 `"desc"`；最长 1000；示例：`desc`, `asc` | 当field选择APD,PBD,ISD时有效，order支持desc,asc |
| `offset` | `integer` | 否 | 默认 `0`；最小 0；最大 1000 | 偏移量，0 <= offset <= 1000，默认为0 |
| `country` | `string` | 否 | 最长 1000；示例：`WO`, `EP`, `CN`, `US`, `JP`, `KR`, `DE`, `FR` | 专利受理局（国家/组织/地区代码），多个用英文逗号隔开，不传时代表查询全部专利受理局的数据 |
| `isHttps` | `integer` | 否 | 默认 `0` | 选择是否返回https域名图片，1：返回https，0：返回http |
| `stemming` | `integer` | 否 | 默认 `0`；示例：`1`, `0` | 是否开启截词功能，1：开启；0：关闭 |
| `assignees` | `string` | 否 | 最长 1000 | 申请（专利权）人 |
| `mainField` | `string` | 否 | 最长 1000 | 专利主要字段，包括标题、摘要、权利要求、说明书、公开号、申请号、申请人、发明人和IPC/UPC/LOC分类号 |
| `preFilter` | `integer` | 否 | 默认 `1`；示例：`1`, `0` | 是否开启前置国家/LOC过滤，1：开启；0：关闭 |
| `patentType` | `string` | 是 | 默认 `"D"`；格式 `D\|U`；示例：`D`, `U` | 选择检索外观专利或实用新型专利：D-外观专利，U-实用新型专利 |
| `legalStatus` | `string` | 否 | 最长 1000；示例：`1`, `2`, `3`, `8`, `11`, `12`, `17`, `18` | 专利的法律状态，多个用英文逗号隔开 |
| `returnImgId` | `boolean` | 否 | 默认 `false` | 是否返回img_id |
| `applyEndTime` | `string` | 否 | 最长 1000 | 专利申请截止时间，格式:yyyyMMdd |
| `publicEndTime` | `string` | 否 | 最长 1000 | 专利公开截止时间，格式:yyyyMMdd |
| `applyStartTime` | `string` | 否 | 最长 1000 | 专利申请起始时间，格式:yyyyMMdd |
| `scoreExpansion` | `boolean` | 否 |  | 分数拓展 |
| `publicStartTime` | `string` | 否 | 最长 1000 | 专利公开起始时间，格式:yyyyMMdd |
| `simpleLegalStatus` | `string` | 否 | 最长 1000；示例：`0`, `1`, `2`, `220`, `221`, `999` | 专利的简单法律状态，多个用英文逗号隔开 |
| `includeMachineTranslation` | `boolean` | 否 |  | 搜索包含机器翻译数据 |


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
    "name": "/zhihuiya/patentImageSearch",
    "arguments": {
      "model": "1",
      "patentType": "D",
      "url": "https://example.com/item"
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
| `allRecordsCount` | `integer` | 否 |  | 总记录数 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `loc` | `array<any>` | 否 |  | LOC分类 |
| `url` | `string` | 否 |  | 相似的专利附图 |
| `apdt` | `integer` | 否 |  | 申请日 |
| `apno` | `string` | 否 |  | 申请号 |
| `pbdt` | `integer` | 否 |  | 公开日 |
| `imgId` | `string` | 否 |  | 相似的专利附图img_id |
| `score` | `number` | 否 |  | 相似度分数（仅当按照相似度排序时有效，即请求参数field为SCORE） |
| `title` | `string` | 否 |  | 专利名称 |
| `inventor` | `string` | 否 |  | 发明人 |
| `locMatch` | `integer` | 否 |  | 是否命中高权重LOC，1为命中，0为未命中（仅当model=1且field=SCORE时有效） |
| `patentId` | `string` | 否 |  | 相似专利ID |
| `patentPn` | `string` | 否 |  | 相似专利号 |
| `authority` | `string` | 否 |  | 受理局 |
| `currentAssignee` | `string` | 否 |  | 当前申请人 |
| `originalAssignee` | `string` | 否 |  | 原始申请人 |

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
