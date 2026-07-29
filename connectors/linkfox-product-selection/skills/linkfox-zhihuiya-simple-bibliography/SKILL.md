---
name: linkfox-zhihuiya-simple-bibliography
description: 从智慧芽专利数据库查询专利简要著录（书目）数据。当用户提到专利著录信息查询、专利基本信息获取、专利书目数据、专利公开详情、按专利号查询发明人、专利申请人信息、专利摘要获取、专利分类号（IPC/CPC）、专利引用查询或任何通过专利ID、公开号检索结构化元数据的请求、patent brief bibliography, patent basic info, patent number lookup, patent abstract, PatSnap, patent metadata时触发此技能。即使用户未明确提及"智慧芽"或"著录信息"，只要其需求涉及查询特定专利的核心著录字段，也应触发此技能。
---

# 智慧芽-简单著录项

## 基本信息

- **业务工具名**：`/zhihuiya/simpleBibliography`
- **所属分组**：智慧芽 · 专利数据
- **功能说明**：支持根据专利ID、专利公告号查询专利的简单著录项目信息


## 何时使用

当用户意图与“智慧芽-简单著录项”匹配，或需要以下能力时使用本工具：支持根据专利ID、专利公告号查询专利的简单著录项目信息

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `patentId` | `string` | 否 | 最长 60000 | 专利ID（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个专利ID相互之间用英文[,]隔开，最大支持100个 |
| `patentNumber` | `string` | 否 | 最长 60000 | 公开公告号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个公开公告号相互之间用英文[,]隔开，最大支持100个 |


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
    "name": "/zhihuiya/simpleBibliography",
    "arguments": {}
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 著录项列表 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `allRecordsCount` | `integer` | 否 |  | 总记录数 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `pn` | `string` | 否 |  | 公开公告号 |
| `gbc` | `array<any>` | 否 |  | GBC分类号列表 |
| `loc` | `array<any>` | 否 |  | LOC分类号列表 |
| `kind` | `string` | 否 |  | 专利类型代码 |
| `title` | `string` | 否 |  | 专利标题 |
| `country` | `string` | 否 |  | 国家代码 |
| `cpcMain` | `string` | 否 |  | CPC主分类号 |
| `ipcMain` | `string` | 否 |  | IPC主分类号 |
| `patentId` | `string` | 否 |  | 专利ID |
| `assignees` | `array<any>` | 否 |  | 专利权人列表 |
| `inventors` | `array<any>` | 否 |  | 发明人列表 |
| `applicants` | `array<any>` | 否 |  | 申请人列表 |
| `cpcFurther` | `array<any>` | 否 |  | CPC副分类号列表 |
| `ipcFurther` | `array<any>` | 否 |  | IPC副分类号列表 |
| `patentType` | `string` | 否 |  | 专利类型 |
| `citedPatents` | `array<any>` | 否 |  | 引用专利列表 |
| `pctEntryDate` | `string` | 否 |  | PCT进入日期 |
| `applicationNo` | `string` | 否 |  | 申请号 |
| `pctFilingDate` | `string` | 否 |  | PCT申请日期 |
| `priorityClaims` | `array<any>` | 否 |  | 优先权声明列表 |
| `abstractContent` | `string` | 否 |  | 专利摘要 |
| `applicationDate` | `string` | 否 |  | 申请日期 |
| `citedNonPatents` | `array<any>` | 否 |  | 引用非专利文献列表 |
| `publicationDate` | `string` | 否 |  | 公开日期 |
| `publicationKind` | `string` | 否 |  | 公开类型代码 |
| `pctApplicationNo` | `string` | 否 |  | PCT申请号 |
| `assigneeAddresses` | `array<any>` | 否 |  | 专利权人地址列表 |
| `publicationNumber` | `string` | 否 |  | 公开号 |
| `publicationCountry` | `string` | 否 |  | 公开国家 |

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
