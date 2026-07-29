---
name: linkfox-zhihuiya-bibliography
description: 通过专利ID或公开号查询智慧芽专利数据库中的专利著录（书目）信息。当用户提到专利著录信息查询、专利书目信息、专利申请人查询、专利发明人查询、专利分类号、专利摘要获取、专利引用分析、专利优先权主张、专利申请引用、专利审查员信息、patent bibliographic data, inventor lookup, applicant lookup, patent classification, patent metadata, PatSnap, patent citations时触发此技能。即使用户未明确提及"著录信息"，只要其需求涉及通过专利ID或公开号查询特定专利的详细元数据，也应触发此技能。
---

# 智慧芽-著录项目

## 基本信息

- **业务工具名**：`/zhihuiya/bibliography`
- **所属分组**：智慧芽 · 专利数据
- **功能说明**：工具中文名：智慧芽-著录项目
描述：可以通过输入专利ID或专利公开号查询具体某条专利的著录项目信息。
关键词：智慧芽,著录
- **关键词**：智慧芽,著录


## 何时使用

当用户意图与“智慧芽-著录项目”匹配，或需要以下能力时使用本工具：工具中文名：智慧芽-著录项目
描述：可以通过输入专利ID或专利公开号查询具体某条专利的著录项目信息。
关键词：智慧芽,著录

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `patentId` | `string` | 否 | 最长 60000 | 专利ID（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开，上限100条 |
| `patentNumber` | `string` | 否 | 最长 60000 | 公开公告号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开，上限100条 |


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
    "name": "/zhihuiya/bibliography",
    "arguments": {}
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 著录项目数据列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `pn` | `string` | 否 |  | 公开公告号 |
| `exdt` | `integer` | 否 |  | 智慧芽专利预估到期日 |
| `agency` | `array<object>` | 否 |  | 申请代理机构 |
| `agents` | `array<object>` | 否 |  | 专利申请人 |
| `patentId` | `string` | 否 |  | 专利ID |
| `abstracts` | `array<object>` | 否 |  | 专利摘要 |
| `assignees` | `array<object>` | 否 |  | 当前申请(专利权)人 |
| `examiners` | `array<object>` | 否 |  | 审查员信息 |
| `inventors` | `array<object>` | 否 |  | 发明人 |
| `applicants` | `array<object>` | 否 |  | 原始申请人 |
| `patentType` | `string` | 否 |  | 专利类型，其中APPLICATION：发明申请，PATENT：授权发明，UTILITY：实用新型，DESIGN：外观设计 |
| `inventionTitle` | `array<object>` | 否 |  | 专利标题语言和名称 |
| `priorityClaims` | `array<object>` | 否 |  | 优先权声明 |
| `classificationFi` | `array<any>` | 否 |  | FI分类号 |
| `relatedDocuments` | `array<object>` | 否 |  | 分案继续申请信息 |
| `classificationCpc` | `object` | 否 |  |  |
| `classificationGbc` | `object` | 否 |  |  |
| `classificationLoc` | `array<any>` | 否 |  | LOC分类号 |
| `classificationUpc` | `object` | 否 |  |  |
| `classificationIpcr` | `object` | 否 |  |  |
| `classificationFterm` | `array<any>` | 否 |  | F_term分类号 |
| `applicationReference` | `object` | 否 |  |  |
| `publicationReference` | `object` | 否 |  |  |
| `referenceCitedOthers` | `array<object>` | 否 |  | 引用非专利文献 |
| `referenceCitedPatents` | `array<object>` | 否 |  | 引用专利文献 |
| `pctOrRegionalFilingData` | `object` | 否 |  |  |
| `datesOfPublicAvailability` | `object` | 否 |  |  |
| `pctOrRegionalPublishingData` | `object` | 否 |  |  |

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
