---
name: tdx-connector
description: "Query global stock data via Tongdaxin MCP, with screening and research support."
description_zh: "通过通达信 MCP 查询全球股票行情数据、条件选股、研究报告、公告资讯和宏观信息。支持个股基本面分析、同行业对比和智能选股筛查。"
description_en: "Query global stock data via Tongdaxin MCP. Supports screening, reports, and macro analysis."
version: "1.0.0"
---

# TDX Finance Skill

本 Skill 提供通达信 MCP 的完整金融数据查询能力，覆盖全球股票行情、条件选股、研究报告、公告资讯和宏观数据。

## 可用工具总览

| 工具名 | 用途 |
|--------|------|
| `tdx_api_data` | 统一调用 TDX/TQLEX 内部金融 API，支持自动路由、参数模板和结果转换 |
| `tdx_quotes` | 查询股票、指数、板块等实时行情 |
| `tdx_kline` | 查询股票、指数、板块等 K 线数据 |
| `tdx_lookup_stock` | 根据名称、简称或别名检索证券代码和市场代码 |
| `tdx_screener` | 使用自然语言条件选股 |
| `tdx_indicator_select` | 查询股票、指数、基金的结构化指标和资料 |
| `wenda_notice_query` | 查询公司公告、临时公告、定期报告等 |
| `wenda_report_query` | 查询券商研报、评级、目标价和观点摘要 |
| `wenda_news_query` | 查询新闻、快讯、主题资讯和公司资讯 |
| `wenda_macro_query` | 查询宏观经济、产业景气、价格、利率、货币、社融等数据 |

> 实时行情优先用 `tdx_quotes`，K 线优先用 `tdx_kline`，代码查询优先用 `tdx_lookup_stock`，自然语言选股优先用 `tdx_screener`。`tdx_api_data` 作为统一底层入口，适合已知上游 API 名称的高级场景。

---

### tdx_quotes - 查询实时行情

查询股票、指数、板块等的实时行情数据。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| codes | string[] | ✅ | 证券代码列表，如 `["000001", "600519"]` |
| fields | string[] | - | 需要返回的字段列表，默认返回主要字段 |

**使用示例**：
- 查询单只股票行情：调用 tdx_quotes，设置 codes 参数
- 批量查询多只股票：在 codes 中传入多个证券代码

### tdx_kline - 查询 K 线数据

查询股票、指数、板块等的 K 线历史数据。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 证券代码 |
| period | string | ✅ | K 线周期，如 `1m`、`5m`、`day`、`week`、`month` |
| count | number | - | 返回 K 线数量，默认 120 |

**使用示例**：
- 查询日 K 线：调用 tdx_kline，设置 period 为 `day`
- 查询分钟级 K 线：设置 period 为 `1m` 或 `5m`

### tdx_lookup_stock - 检索证券代码

根据名称、简称或别名检索证券代码和市场代码。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | ✅ | 搜索关键词，支持股票名称、简称、别名 |
| market | string | - | 市场筛选，如 `SH`、`SZ`、`HK` |

**使用示例**：
- 搜索"茅台"：调用 tdx_lookup_stock，设置 keyword 为 `"茅台"`
- 按市场筛选：同时传入 market 参数限定交易所

### tdx_screener - 自然语言条件选股

使用自然语言描述筛选条件进行选股。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| query | string | ✅ | 自然语言筛选条件，如"市盈率低于20且ROE高于15%" |
| limit | number | - | 返回数量上限，默认 20 |

**使用示例**：
- 多因子选股：调用 tdx_screener，设置 query 参数
- 行业主题筛选：在 query 中加入行业或主题关键词

### tdx_indicator_select - 查询结构化指标

查询股票、指数、基金的结构化指标和资料数据。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 证券代码 |
| indicators | string[] | - | 指标名称列表，不传则返回默认指标集 |

**使用示例**：
- 查询财务指标：调用 tdx_indicator_select，传入 code 和需要的指标名
- 批量查询：一次传入多个指标名称

### wenda_report_query - 查询研报

查询券商研报、评级、目标价和观点摘要。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 证券代码 |
| keyword | string | - | 研报关键词筛选 |
| date_range | string | - | 时间范围，如 `"last_30_days"` |
| limit | number | - | 返回数量上限，默认 20 |

**使用示例**：
- 查询某股票的最新研报：调用 wenda_report_query，设置 code
- 按关键词筛选：传入 keyword 参数

### wenda_notice_query - 查询公告

查询公司公告、临时公告、定期报告等。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| code | string | ✅ | 证券代码 |
| notice_type | string | - | 公告类型，如 `"临时公告"`、`"定期报告"` |
| date_range | string | - | 时间范围，如 `"last_7_days"` |
| limit | number | - | 返回数量上限，默认 20 |

**使用示例**：
- 查询公司公告：调用 wenda_notice_query，设置 code
- 筛选特定公告类型：传入 notice_type 参数

### wenda_news_query - 查询资讯

查询新闻、快讯、主题资讯和公司资讯。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | ✅ | 资讯关键词 |
| category | string | - | 资讯分类，如 `"公司资讯"`、`"主题资讯"` |
| date_range | string | - | 时间范围 |
| limit | number | - | 返回数量上限，默认 20 |

**使用示例**：
- 查询公司相关新闻：调用 wenda_news_query，设置 keyword
- 按分类筛选：传入 category 参数

### wenda_macro_query - 查询宏观数据

查询宏观经济、产业景气、价格、利率、货币、社融等数据。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| indicator | string | ✅ | 宏观指标名称，如 `"CPI"`、`"社融规模"`、`"PMI"` |
| date_range | string | - | 时间范围 |
| limit | number | - | 返回数量上限，默认 20 |

**使用示例**：
- 查询 CPI 数据：调用 wenda_macro_query，设置 indicator 为 `"CPI"`
- 查询社融数据：设置 indicator 为 `"社融规模"`

---

## tdx_api_data - 统一 API 调用

`tdx_api_data` 是最复杂、最不易被 AI 理解的工具，用于统一调用 TDX/TQLEX 内部金融 API。

**适用场景**：
- 已知上游 `Entry` 名称，需要调用对应内部接口
- 希望工具按字段自动组装上游 `Params` 数组
- 需要把上游 `ResultSets` 转成结构化结果
- 需要在单次调用中覆盖 API 端点、认证方式或响应转换方式

**不适用场景**：实时行情用 `tdx_quotes`，K 线用 `tdx_kline`，代码查询用 `tdx_lookup_stock`，自然语言选股用 `tdx_screener`。

### 参数说明

**常用字段**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| entry | string | ✅ | 上游接口名，如 `TdxSharePCCW.tdxf10_gg_ybpj` |
| code | string | - | 证券代码，如 `000001`、`00700` |
| fixedTag | string | - | 同一 entry 下区分业务子类型 |
| branch | string | - | 板块或分支编号 |
| timeType | string | - | 时间类型，如板块截面中的 `1m` |
| queryType | string | - | 查询类型 |
| targetCode | string | - | 目标代码，常用于板块或行业对比 |
| stockCode | string | - | 股票代码，常用于对比查询 |
| industryCode | string | - | 行业代码 |
| title | string | - | 标题或事件标题 |
| beginDate | string | - | 起始日期，格式 `YYYYMMDD` |
| endDate | string | - | 结束日期，格式 `YYYYMMDD` |
| reportDate | string | - | 报告期，格式 `YYYYMMDD` |
| pageNo | number | - | 页码 |
| pageSize | number | - | 每页数量 |
| cursor | string | - | 游标参数 |
| sortType | number | - | 排序类型 |
| typeValue | string | - | 分类值 |
| queryKey | string | - | 查询模板键 |
| mode | string | - | 显式指定参数排列模式（见下方） |
| params | array | - | `raw` 模式下直接透传的参数数组 |
| responseTransform | object | - | 结果转换规则 |

### 调用方式

**优先使用自动路由**（entry + 判别参数，工具自动推导 mode 和 preset）：

```bash
tdx_api_data entry="TdxSharePCCW.tdxf10_gg_ybpj" code="000001" fixedTag="yzyq"
tdx_api_data entry="TdxSharePCCW.tdxf10_gg_gsgk" fixedTag="0" code="000001"
tdx_api_data entry="TdxSharePCCW.tdxf10_gg_gdyj" code="000001" fixedTag="gdrs" pageNo="1" pageSize="20"
tdx_api_data entry="TdxSharePCCW.skef10_bk_cpbd_jczl" branch="003" code="880976" timeType="1m"
```

**常见自动路由查询**：

| 查询 | 示例 |
|------|------|
| 研报评级一致预期 | `entry="TdxSharePCCW.tdxf10_gg_ybpj" code="000001" fixedTag="yzyq"` |
| 公司基本信息 | `entry="TdxSharePCCW.tdxf10_gg_gsgk" fixedTag="0" code="000001"` |
| 董监高信息 | `entry="TdxSharePCCW.tdxf10_gg_gsgk" fixedTag="20" code="000001"` |
| 股本结构 | `entry="TdxSharePCCW.tdxf10_gg_gbjg" code="000001" fixedTag="gbjg"` |
| 股东人数 | `entry="TdxSharePCCW.tdxf10_gg_gdyj" code="000001" fixedTag="gdrs"` |
| 十大流通股东 | `entry="TdxSharePCCW.tdxf10_gg_gdyj" code="000001" fixedTag="ltgd"` |
| 机构持股明细 | `entry="TdxSharePCCW.tdxf10_gg_gdyj_jgcgmx" code="000001" reportDate="20241231"` |
| 港股损益表 | `entry="TdxSharePCCW.skef10_hk_cwfx" fixedTag="1" code="00700"` |
| 港股资产负债表 | `entry="TdxSharePCCW.skef10_hk_cwfx" fixedTag="2" code="00700"` |
| 港股现金流量表 | `entry="TdxSharePCCW.skef10_hk_cwfx" fixedTag="3" code="00700"` |
| 板块基础资料 | `entry="TdxSharePCCW.skef10_bk_cpbd_jczl" branch="003" code="880976"` |
| 行业产业链 | `entry="TdxSharePCCW.cfg_tk_gethy" industryCode="881155"` |

**显式指定 mode**（自动路由不支持时使用）：

| mode | 上游 Params 形态 |
|------|-------------------|
| `raw` | 直接透传 params |
| `code-only` | `[code]` |
| `code-fixed-tag` | `[code, fixedTag]` |
| `fixed-tag-code` | `[fixedTag, code]` |
| `code-fixed-tag-extra` | `[code, fixedTag, extra]` |
| `fixed-tag-code-extra` | `[fixedTag, code, extra]` |
| `branch-code-time` | `[branch, code, timeType]` |
| `query-type-target-stock` | `[queryType, targetCode, stockCode]` |
| `industry-code` | `[industryCode]` |
| `industry-title` | `[industryCode, title]` |
| `code-date-range-page` | `[code, fixedTag, beginDate, endDate, clickIndex, pageNo, pageSize]` |
| `code-fixed-tag-report-cursor-page` | `[code, fixedTag, "", reportDate, cursor, pageNo, pageSize]` |
| `code-sort-report-type-click-page` | `[code, sortType, reportDate, typeValue, clickIndex, pageNo, pageSize]` |
| `query-key-code-flag` | `[queryKey, code, compareFlag]` |
| `query-key-code-extra` | `[queryKey, code, extra]` |

**raw 兜底调用**（无合适 mode 时直接传 params）：

```bash
tdx_api_data mode="raw" entry="Some.Entry" params=["000001","yzyq"]
```

### 响应转换

命中自动路由时，默认使用 `preset` 转换结果。也可手动指定：

**使用内置 preset**：
```bash
tdx_api_data entry="TdxSharePCCW.tdxf10_gg_rdtc" code="000001" fixedTag="zttzbkz" responseTransform={"kind":"preset","preset":"hot_topic_board_family"}
```

**自定义 ResultSets 转换**：
```bash
tdx_api_data mode="raw" entry="Some.Entry" params=["000001"] responseTransform={"kind":"result-sets","resultSets":[{"name":"overview","index":0,"layout":"table","maxRows":20}]}
```

**自定义转换字段**：

| 字段 | 说明 |
|------|------|
| `kind` | 固定为 `result-sets` |
| `resultSets[].name` | 转换后的结果集名称 |
| `resultSets[].index` | 按结果集下标匹配，`0` 表示第一个 |
| `resultSets[].resultSetKey` | 按上游 `ResultSetKey` 匹配 |
| `resultSets[].fieldMap` | 字段重命名映射 |
| `resultSets[].headers` | 输出字段顺序 |
| `resultSets[].layout` | `record` 或 `table` |
| `resultSets[].maxRows` | 最大展示行数 |

### 返回结果

| 字段 | 说明 |
|------|------|
| `request` | 实际请求的 entry、端点、Params 等上下文 |
| `response.status` | HTTP 状态码 |
| `response.data` | 未转换或转换失败时的原始响应 |
| `response.transformed` | 转换成功后的结构化结果 |

> 传了 `responseTransform` 且转换成功时，优先读取 `response.transformed`。

---

## 使用优先级建议

1. 优先使用自动路由：`entry + code/fixedTag/...`
2. 自动路由不支持时，显式指定 `mode`
3. `mode` 也不适合时，使用 `raw` 直接传 `params`
4. 默认转换不满足时，再传 `responseTransform`

## 排错建议

| 现象 | 检查点 |
|------|--------|
| 提示缺少字段 | 检查当前 mode 需要哪些字段 |
| 返回为空 | 检查 entry、fixedTag、日期范围、分页参数是否正确 |
| 自动路由没有生效 | 检查 entry 和判别参数是否在已支持范围内 |
| 返回原始 ResultSets | 没有命中默认 preset，或显式转换未产生结果 |
| HTTP 认证失败 | 检查 token、`TDX_API_KEY` 或自定义 auth |
| 上游接口地址不对 | 用 `apiEndpoint` 单次覆盖并验证 |

## 注意事项

- 需要确保 MCP 连接器已正确配置并通过授权
- 港股支持代码检索、条件选股、研报资讯，但不支持实时行情和 K 线
- 美股支持有限，主要覆盖 A 股和港股
- 单次查询返回数量建议不超过 100 条，避免数据量过大
