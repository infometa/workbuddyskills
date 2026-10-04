---
name: iyiou-data-skill
description: 亿欧数据查询技能
version: "1.0.0"
author: "Yiou"
---

# Yiou Data Skill

本 Skill 用于调用亿欧数据 MCP，查询企业融资事件、批量融资记录和按时间/投资方筛选的融资事件。

## 适用范围

- 企业投融资历史查询
- 多家企业融资记录批量拉取
- 按融资时间区间、投资方筛选融资事件

## 查询原则

- 优先查准，再查全，不要直接拿模糊企业名去查融资事件
- 用户只给企业简称、品牌名、别名、口语名时，先调用 `search_companies`
- 单企业查询优先使用 `comId`，不要优先使用 `comName`
- 只有用户明确要按时间区间或投资方做全局筛选时，才调用 `filter_invest_events`
- 只有用户明确要比较多家企业，或一次性查询多家企业时，才调用 `batch_query_company_invest_events`

## 最优查询路径

### 场景一：查询单家企业融资历史

最优路径：

1. 先调用 `search_companies`
2. 选最匹配的企业，拿到 `comId`
3. 再调用 `query_company_invest_events`

适用说法：

- “查一下字节跳动的融资历史”
- “小红书融过几轮资”
- “帮我看看蔚来的投融资记录”

### 场景二：比较多家企业融资情况

最优路径：

1. 先确认企业名称是否足够精确
2. 企业名不精确时，先分别调用 `search_companies`
3. 名称确认后，调用 `batch_query_company_invest_events`

适用说法：

- “对比下小红书和Keep的融资情况”
- “批量看这几家公司的融资记录”

### 场景三：按时间或投资方全局查融资事件

最优路径：

1. 直接调用 `filter_invest_events`
2. 必须补齐 `invest_time_start` 和 `invest_time_end`
3. 需要按投资方限制时，再传 `investors`

适用说法：

- “查 2025 年 1 月的融资事件”
- “筛选红杉投过的融资项目”
- “看 2025 年上半年发生过哪些融资”

## 不推荐路径

- 不要在只知道简称时直接调用 `query_company_invest_events(comName=...)`
- 不要把 `filter_invest_events` 当成单企业查询工具
- 不要在单企业场景下优先使用批量工具
- 不要遗漏 `filter_invest_events.arguments.page` 和 `page_size`
- 不要只传 `invest_time_start` 或只传 `invest_time_end`

## 可用工具

### search_companies

根据企业简称、全称或关键词搜索企业候选列表，返回 `comId`、企业全称、简称和行业。

优先场景：

- 用户只给了企业简称、品牌名、口语名
- 后续需要拿精确 `comId` 查询融资事件

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| name | string | ✅ | 企业关键词，支持简称、全称、拼音等 |

### query_company_invest_events

查询单家企业的历史投融资事件。

使用原则：

- 优先先调用 `search_companies` 获取 `comId`
- `comId` 和 `comName` 同时传时，以 `comName` 为准
- 仅在无法获得 `comId` 时再使用 `comName`

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| comId | string | - | 企业 ID，推荐使用 |
| comName | string | - | 企业全称精确匹配 |
| page | number | - | 页码，默认 1 |
| pageSize | number | - | 每页条数，默认 20，最大 50 |

### batch_query_company_invest_events

批量查询多家企业的历史融资事件。

使用原则：

- `company_names` 和 `company_ids` 至少传一个
- 同时传时优先使用 `company_names`
- 单次最多 50 家企业
- 分页参数必须放在 `arguments` 对象里

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| arguments.page | number | ✅ | 页码 |
| arguments.page_size | number | ✅ | 每页条数，最大 50 |
| company_names | string[] | - | 企业全称列表 |
| company_ids | string[] | - | 企业 ID 列表 |

### filter_invest_events

按时间区间和投资方筛选融资事件，不限定企业。

使用原则：

- 未传筛选条件时，返回全量分页融资事件
- `invest_time_start` 和 `invest_time_end` 必须同时传
- 分页参数必须放在 `arguments` 对象里

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| arguments.page | number | ✅ | 页码 |
| arguments.page_size | number | ✅ | 每页条数，最大 50 |
| arguments.invest_time_start | string | - | 起始日期，格式 YYYY-MM-DD |
| arguments.invest_time_end | string | - | 截止日期，格式 YYYY-MM-DD |
| arguments.investors | string | - | 投资方名称，多个可用中英文逗号分隔 |

## 推荐调用顺序

1. 用户给的是模糊企业名时，先调用 `search_companies`
2. 拿到 `comId` 后，再调用 `query_company_invest_events`
3. 多企业对比时，使用 `batch_query_company_invest_events`
4. 按时间或投资方全局检索时，使用 `filter_invest_events`

## 歧义处理

- `search_companies` 返回多个候选且都可能匹配时，优先选择简称、行业、企业全称最贴近用户表达的候选
- 如果候选差异较大，不要擅自混用多个 `comId` 进行单企业查询
- 如果用户点名要某个“企业全称”，而工具返回为空，可以提示该名称可能不是系统内的精确全称，并优先改走 `search_companies`

## 返回结果解读

- `query_company_invest_events` 或 `batch_query_company_invest_events` 返回 `总数: 0`，不一定表示接口异常，更常见是企业名不精确或该企业暂无命中记录
- `filter_invest_events` 返回 `总数 > 0` 但本次返回条数较少时，通常只是分页结果，不代表完整结果只有这么多
- 看到 `AUTH_FAILED` 时，应判断为凭证缺失或凭证错误
- 看到 `QUOTA_EXHAUSTED` 时，应判断为上游调用额度不足，不应误判为工具参数错误

## 注意事项

- 本 Connector 依赖 `CLIENT_ID` 和 `CLIENT_SECRET`
- 未配置凭证或凭证错误时，工具会返回鉴权失败
- `search_companies` 可用于前置解析企业名称，减少因企业全称不精确导致的查询失败
- 如凭证失效、轮换或需重新申请，请按凭证说明文档重新获取 `CLIENT_ID` 和 `CLIENT_SECRET`
- 当用户目标是“查准某一家企业的融资历史”时，最优解始终是：`search_companies -> query_company_invest_events(comId)`
