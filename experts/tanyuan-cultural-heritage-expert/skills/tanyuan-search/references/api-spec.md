# 探元 Tool API 参考（精简版）

> 本文件是 `tanyuan-search` 技能内部参考资料，供 Agent 在执行时快速查阅接口字段与语义。
> 完整原始文档见项目根目录的 `Tool API调用说明.md`。

## Base URL

```
https://api-ai-creation.tanyuan.qq.com
```

> 正式（生产）环境地址，已在两个脚本的 `BASE_URL` 常量中配置。

## 通用约定

- **鉴权**：无（MVP）。未来若接入 API Key，需要在请求头加 `X-API-Key`
- **Content-Type**：`application/json`
- **`datasourceType`**：
  - `searchRelics`：`0` = 文物数据库（默认），`1` = 世界遗产数据库
  - `searchKnowledge`：`0` = 默认/文物知识源，`1` = 文化遗产知识源

## 1. 文物 / 世界遗产数据库生成式检索

- **Endpoint**：`POST /tanyuanAiAssistant/tool/searchRelics`
- **说明**：后端根据 `datasourceType` 使用对应 Text2SQL prompt，将完整自然语言问题转换为只读 SQL；调用方不写 SQL，也不应把问题压缩成关键词串
- **适用场景**：结构化事实的详情、列表、统计、分组和排行查询

### `datasourceType=0`：文物数据库

后端基于 MySQL 5.7 查询文物及已上架商品资产。调用方构造 query 时应保留：

- 结构化过滤：年代、类型、类别、等级、馆藏机构、创作者、出土地
- 明确文物实体名：完整专名保持完整；简称需明确其不完整性
- 普通文本概念：器类、题材、工艺、文化主题、颜色等保持完整组合词
- 问题形态与返回意图：详情/列表/统计/排行，以及希望返回的业务字段

常用稳定业务字段：`name`、`alias`、`years`、`type`、`category`、`level`、`museum_name`、`creator`、`place`、`size`、`cover`、`basic_introduce`、`feature_introduce`。其中：

- `type` 仅指可移动文物/不可移动文物，青铜器、瓷器、古建筑等属于 `category`
- `museum_name` 是馆藏机构，`place` 是出土地，二者不得混用
- 颜色只能作为普通文本概念；`color` 是数值 JSON 特征向量，不可直接按自然语言颜色过滤
- `goods_id` 等内部标识不应默认要求返回

示例：`馆藏机构为故宫博物院的明代青铜器有哪些？请返回文物名称、年代、类别、馆藏机构和基本介绍`

### `datasourceType=1`：世界遗产数据库

后端基于 PostgreSQL 查询 UNESCO 世界遗产主表及关联数据。主表可查询：名称、国家、洲别、入选年份、类别、评定标准、濒危状态、坐标、缩略图、封面与简介；关联层包括 OUV 声明、保护状态、历史事件、引用、知识卡片、叙事、媒体、每日推荐及用户贡献等。

- 洲别：亚洲、欧洲、非洲、美洲、大洋洲
- 类别：文化、自然、混合、预备名单
- 可按 UNESCO 标准编号（如 `(i)`、`(iv)`）、濒危状态、年份等筛选
- 非遗和传统技艺不属于此结构化数据库；开放问题应使用 `searchKnowledge`

示例：`中国有哪些文化类世界遗产？请返回名称、国家、入选年份、评定标准、濒危状态和简介，并按入选年份倒序`

### 请求体

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `query` | string | 是 | — | 保留全部有效条件、问题形态和返回意图的自然语言问题（后端 NL→SQL） |
| `datasourceType` | integer | 否 | `0` | `0`=文物数据库，`1`=世界遗产数据库 |

### 响应体（成功）

```json
{
  "response": {
    "requestId": "xxxxxxxx",
    "data": {
      "rowCount": 3,
      "rows": [
        "{\"name\":\"青花山水纹瓶\",\"years\":\"清\",\"category\":\"瓷器\",\"museum_name\":\"某博物馆\"}",
        "{\"name\":\"青花缠枝莲盘\",\"years\":\"清\",\"category\":\"瓷器\"}",
        "{\"name\":\"青花人物故事罐\",\"years\":\"清\",\"category\":\"瓷器\"}"
      ]
    }
  }
}
```

**⚠️ `rows` 中每一项是 JSON 字符串**（不是对象），需要再做一次 `JSON.parse` 才能得到结构化对象。`search-relics.js` 脚本已经代为解析，Agent 侧看到的是 `items[]`（对象数组）。

**⚠️ `rowCount` 是本次返回的行数**，受后端检索条数上限约束（常见约 10 条），**并非库中符合条件的匹配总数**；当它达到上限时通常意味着还有更多记录未返回。Agent 不得将其当作总数或全集，也不得据返回的若干条臆造统计结论。

### 响应体（失败）

```json
{
  "response": {
    "requestId": "xxxxxxxx",
    "error": { "code": "...", "message": "..." }
  }
}
```

## 2. 知识库检索

- **Endpoint**：`POST /tanyuanAiAssistant/tool/searchKnowledge`
- **说明**：关键词 + 向量检索 + Rank，返回一段综合文本
- **适用场景**：开放 / 语义性问题（背景、原因、工艺、故事、鉴赏、对比论证、攻略、研学）。快，语义覆盖好，是多数问答首选
- **query 建议**：只保留核心实体 + 单一主要意图，query 宜短、去口语冗余；不要把回答要覆盖的多个维度堆入一次向量检索（会稀释语义），需要多维度时拆成多个精简子 query 分别检索

### 请求体

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `query` | string | 是 | — | 检索问题文本 |
| `datasourceType` | integer | 否 | `0` | `0`=默认/文物，`1`=文化遗产 |

> 请求体不接收 `requestId`。链路 ID 由统一请求上下文处理：可通过 `RequestID` 请求头传入，未传时由后端自动生成。

### 响应体（成功）

```json
{
  "response": {
    "requestId": "xxxxxxxx",
    "data": {
      "text": "……知识库返回的多段落文本（Markdown 或纯文本）……"
    }
  }
}
```

### 响应体（失败）

同 `searchRelics`。

## 脚本 stdout 约定（供 Agent 参考）

`search-relics.js` 与 `search-knowledge.js` 已将上述响应扁平化：

- `search-relics.js` → `{ requestId, rowCount, items: [...] }`（`rowCount` 为本次返回行数、受上限约束，非匹配总数，见上）
- `search-knowledge.js` → `{ requestId, text: "..." }`

失败时 exit code 非 0，stderr 打印 `HTTP <code>: <body>` 或 `API error: <msg>`。参数缺失 exit code = 2。
