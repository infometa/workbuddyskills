---
name: 新华财经资讯MCP
description: 新华财经公告、新闻、政策数据 MCP 技能。提供股票资讯、板块资讯、热点新闻、资讯搜索、大宗快讯、外汇快讯、股票快讯、上市公司公告关键词检索、政策向量检索等 9 个数据查询工具。
version: "1.0.0"
author: "新华财经"
---

# 新华财经公告、新闻、政策数据 MCP Skill

本 Skill 提供新华财经公告、新闻、政策数据的查询能力，共 9 个工具，覆盖股票资讯、板块资讯、热点新闻、资讯搜索、大宗快讯、外汇快讯、股票快讯、公告检索、政策向量检索等场景。

## 服务信息

| 项目 | 说明 |
|------|------|
| 服务名称 | `xhcj-mcp-announcements-news-policy` |
| 服务类型 | OpenAPI |
| 调用 URL | `https://mcp.cnfic.com.cn/mcp-servers/xhcj-mcp-announcements-news-policy` |
| 认证方式 | `Authorization: Bearer ${XHCJ_API_KEY}` |
| 工具数量 | 9 |

## 认证说明

- 调用前需通过 **API Key 认证**：所有请求需携带 `Authorization: Bearer ${XHCJ_API_KEY}` 请求头
- API Key 由**新华财经**单独下发，如需申领请联系新华财经接口负责人
- 如遇 `401` 或 `403` 错误，说明 Token 无效或已过期，请重新获取并更新 Token

---

## 可用工具

### 1. get_AStock_News_byStockName - 按股票名称提取股票资讯

根据股票名称提取对应的股票资讯。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| stockName | string | 否 | 股票名称，如「京东方A」 |

**输出参数（主要字段）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| ID | char | MD5 唯一标识（ContentID+SecuCode） |
| secuCode | varchar | 证券代码 |
| GilCODE | varchar | 证券代码带市场后缀（BJ/SH/SZ） |
| TagName | varchar | 标签名称 |
| companycode | varchar | 公司代码 |
| ContentID | varchar | 内容 ID |
| Title | varchar | 标题 |
| ContentTxt | longtext | 内容正文 |
| Summary | varchar | 摘要 |
| ModifyTime | datetime | 修改时间 |
| Keyword | varchar | 关键词 |
| Industry | varchar | 行业 |
| FirstIndustryCode/Name | varchar | 一级行业代码/名称 |
| SecondIndustryCode/Name | varchar | 二级行业代码/名称 |
| ThirdIndustryCode/Name | varchar | 三级行业代码/名称 |
| FourthIndustryCode/Name | varchar | 四级行业代码/名称 |
| CompanyCvalMS | varchar | 公司评级描述 |
| TagID | varchar | 标签 ID |

**使用示例**：
- 查询「京东方A」的最新资讯：调用 get_AStock_News_byStockName，设置 stockName = "京东方A"
- 未传股票名称时返回全部股票资讯

---

### 2. search_prodinfo_stockSector_news - 板块资讯搜索

新华财经成品稿板块资讯搜索，支持按时间、标题、内容、标签筛选。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| endTime | string | 否 | 结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| begTime | string | 否 | 开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| title | string | 否 | 标题 |
| contentTxt | string | 否 | 正文内容 |
| tagName | string | 否 | 标签名称 |

**输出参数（主要字段）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| ContentID | string | 成品稿件 ID |
| Title | string | 标题 |
| Author | string | 作者 |
| Editor | string | 编辑 |
| Original | string | 是否原创：0 原创；1 合作；2 转载 |
| ExternalSource | string | 稿件来源 |
| PublishTime | string | 发布时间 |
| ModifyTime | string | 修改时间 |
| LogoFile | string | LOGO 文件地址 |
| Summary | string | 摘要 |
| Keyword | string | 关键字 |
| Genre | string | 体裁：article 文章；image 图片；video 视频 |
| OperType | string | 操作类型 |
| LineName | string | 线路名称 |
| ClassifyName | string | 栏目名称 |
| DictionaryName | string | 字典名称 |
| TagName | string | 标签名称 |
| Content | string | 正文 |
| ResType | string | 附件类型：file 文件；image 图片；video 视频；audio 音频 |
| LineCode | string | 线路编码 |

**使用示例**：
- 按时间范围搜索板块资讯：设置 begTime = "2026-08-01 00:00:00"，endTime = "2026-08-26 23:59:59"
- 按标签搜索：设置 tagName 筛选指定板块标签

---

### 3. get_xhcj_hotNews - 获取新华财经热点新闻

获取新华财经近 10 天的热点新闻。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| begTime | string | 否 | 开始时间（更新时间），如 `2025-05-15 00:00:00` |
| endTime | string | 否 | 结束时间（更新时间），如 `2025-05-25 23:59:59` |

**输出参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| contentID | string | 稿件 ID |
| Title | string | 标题 |
| publishTime | string | 发布时间 |
| summary | string | 摘要 |
| publishorg | string | 出版机构 |
| source | string | 稿源 |
| sourceUrl | string | 原文链接 |
| contentTxt | string | 稿件文字内容 |
| contentHtml | string | 稿件 HTML |
| updateTime | string | 更新时间 |

**使用示例**：
- 获取最近热点新闻：调用 get_xhcj_hotNews，设置 begTime/endTime 为最近 10 天窗口
- 不传时间参数时返回默认时间范围的热点新闻

---

### 4. search_prodinfo - 新华财经资讯搜索

新华财经资讯搜索，支持成品稿和素材。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| title | string | 否 | 标题 |
| contentTxt | string | 否 | 正文内容 |
| tagName | string | 否 | 标签名称 |
| IfProd | string | 否 | 是否生产数据，`y` / `n` |

**输出参数（主要字段）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| ContentID | string | 稿件 ID |
| Title | string | 标题 |
| Author | string | 作者 |
| Editor | string | 编辑 |
| Original | string | 是否原创：0 原创；1 合作；2 转载 |
| ExternalSource | string | 稿件来源 |
| PublishTime | string | 发布时间 |
| ModifyTime | string | 修改时间 |
| LogoFile | string | LOGO 文件地址 |
| Summary | string | 摘要 |
| Keyword | string | 关键字 |
| Genre | string | 体裁：article 文章；image 图片；video 视频 |
| OperType | string | 操作类型 |
| LineName | string | 线路名称 |
| ClassifyName | string | 栏目名称 |
| DictionaryName | string | 字典名称 |
| TagName | string | 标签名称 |
| Content | string | 稿件 |
| ResType | string | 附件类型：file 文件；image 图片；video 视频；audio 音频 |
| LineCode | string | 线路编码 |

**使用示例**：
- 按标题搜索资讯：调用 search_prodinfo，设置 title 参数
- 仅查生产稿：设置 IfProd = "y"

---

### 5. get_newsflash_Commodities - 大宗快讯

通过搜索关键词获取大宗商品相关快讯。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startdate | string | ✅ | 开始日期，如 `2026-05-01` |
| enddate | string | ✅ | 结束日期，如 `2026-05-12` |
| Title | string | ✅ | 资讯标题，如「全国碳市场综合价格」 |
| news_type | string | ✅ | 资讯类型，如「碳市场」 |
| ExternalSource | string | ✅ | 稿件来源，如「新华财经」 |

**输出参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| data | string | 快讯数据 |

**使用示例**：
- 查询碳市场快讯：设置 Title = "全国碳市场综合价格"，news_type = "碳市场"
- 按日期区间限定：startdate/enddate 均必填

---

### 6. get_newsflash_foreign_currency - 外汇自动报价快讯

获取外汇自动报价相关快讯。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startdate | string | ✅ | 开始日期，如 `2026-05-01` |
| enddate | string | ✅ | 结束日期，如 `2026-05-01` |
| Title | string | ✅ | 资讯标题，如「美元指数」 |
| ExternalSource | string | ✅ | 稿件来源，如「新华财经」 |

**输出参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| data | string | 快讯数据 |

**使用示例**：
- 查询美元指数快讯：设置 Title = "美元指数"
- 注意：本工具无 news_type 参数，与大宗快讯/股票快讯不同

---

### 7. get_newsflash_stock - 股票快讯

获取股票相关快讯。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startdate | string | ✅ | 开始日期，如 `2026-05-01` |
| enddate | string | ✅ | 结束日期，如 `2026-05-12` |
| Title | string | ✅ | 资讯标题，如「同仁堂」 |
| news_type | string | ✅ | 资讯类型，如「财报类」 |
| ExternalSource | string | ✅ | 稿件来源，如「新华财经」 |

**输出参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| data | string | 快讯数据 |

**使用示例**：
- 查询某只股票快讯：设置 Title = "同仁堂"
- 按类型筛选：设置 news_type = "财报类"

---

### 8. xhcj-mcp-announce-search - 上市公司公告检索

按关键词查找上市公司公告，覆盖 50 种监控事件。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | 否 | 关键词，如「新华」 |
| start_date | string | 否 | 开始日期，格式 `yyyy-MM-dd HH:mm:ss` |
| end_date | string | 否 | 结束日期，格式 `yyyy-MM-dd HH:mm:ss` |
| topN | integer | 否 | 返回前 N 条（1-100） |

**输出参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| end_date | string | 报告截至日期 |
| secu_abbr | string | 证券简称 |
| info_event_txt | string | 关键事件 |
| info_title | string | 标题 |
| info_publ_date | string | 发布日期 |
| secu_code | string | 证券代码 |
| secu_market | string | 证券市场 |
| info_tag | string | 事件类型 |
| eisdel | string | 0 有效；1 无效 |
| media | string | 发布媒体 |
| listed_sector | string | 上市板块 |
| info_summary | string | 摘要 |
| info_tag_reason | string | 事件类型分析原因 |
| update_time | string | 更新时间 |
| announcement_link | string | 原文 URL |
| id | string | 物理 ID |

**使用示例**：
- 按关键词检索公告：调用 xhcj-mcp-announce-search，设置 keyword = "新华"
- 限定返回数量：设置 topN = 50

---

### 9. get-las-vector - 政策关键字查询

政策关键字向量查询。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | 否 | 关键词 |
| start_date | string | 否 | 开始日期，格式 `yyyy-MM-dd HH:mm:ss` |
| end_date | string | 否 | 结束日期，格式 `yyyy-MM-dd HH:mm:ss` |

**输出参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 物理 ID |
| las_code | string | 关联使用 |
| model | string | 向量模型 |
| title | string | 标题 |
| content_txt | string | 内容 |
| summary_txt | string | 摘要 |
| com_names | string | 发文机关 |
| publish_date | string | 发布日期 |
| execute_date | string | 实施日期 |
| source_url | string | 出处 URL（有可能为非可打开地址） |
| his_json | string | 历史版本描述 |
| href_json | string | 相关引用描述 |

**使用示例**：
- 按关键词查询政策：调用 get-las-vector，设置 keyword 为政策相关词
- 注意 source_url 可能无法直接打开，需结合标题、发文机关、发布日期核对

---

## 工具速查表

| 工具名 | 功能 | 必填参数 |
|--------|------|----------|
| get_AStock_News_byStockName | 按股票名称提取股票资讯 | 无 |
| search_prodinfo_stockSector_news | 板块资讯搜索 | 无 |
| get_xhcj_hotNews | 热点新闻（近 10 天） | 无 |
| search_prodinfo | 资讯搜索（成品稿+素材） | 无 |
| get_newsflash_Commodities | 大宗快讯 | startdate、enddate、Title、news_type、ExternalSource |
| get_newsflash_foreign_currency | 外汇自动报价快讯 | startdate、enddate、Title、ExternalSource |
| get_newsflash_stock | 股票快讯 | startdate、enddate、Title、news_type、ExternalSource |
| xhcj-mcp-announce-search | 上市公司公告检索（50 种事件） | 无 |
| get-las-vector | 政策关键字查询 | 无 |

## 注意事项

- 所有请求需携带 `Authorization: Bearer ${XHCJ_API_KEY}` 请求头，Token 由新华财经单独下发
- 日期格式务必统一：快讯类工具使用 `yyyy-MM-dd`，资讯/公告/政策类使用 `yyyy-MM-dd HH:mm:ss`
- 三个快讯工具（大宗、外汇、股票）参数存在差异：外汇快讯**没有** `news_type` 参数，调用时不要传入
- 公告检索 `topN` 取值范围 1-100，超出范围可能导致错误
- `get-las-vector` 返回的 `source_url` 有可能为非可打开地址，展示时需提示用户
- 若查询结果为空，可尝试放宽时间范围或去除筛选条件后重试
- 遇到认证错误（401/403）时，提示用户更新 API Key
