---
name: yj-fin-data
description: 通过自有 MCP 工具集拉取结构化金融数据，覆盖行情（A股/港股/美股日K、分钟K、实时快照、指数、复权因子）、A股资金流向、财务三大报表、主营构成、股东结构、盈利预测一致预期、估值分位、行业与宏观指标（EDB）、公司指标（EDE）、题材指数与板块成分股。输出结构化 JSON，可直接分析、制图或落盘 CSV。当用户要"是多少、把数据拉出来、做个表、算个比率、画个走势"时使用；只要结论文本用 yj-fin-research，找文档原文用 yj-fin-knowledge。
version: 1.0.0
metadata:
  category: data
  domain: finance
  tools_prefix: 
---

# 数据检索

## 前置：连接与授权

本技能用到的全部工具都是受保护资源，**调用必须携带用户授权令牌**。用户首次使用时会被自动引导完成一次云极账号授权（登录 + 同意授权），此后令牌自动续期，不再打扰。

**授权是怎么发生的（AI 不需要参与）**：首次调用未带令牌时，端点会返回 `401`，并在 `WWW-Authenticate` 里带上 `resource_metadata=...`；WorkBuddy 据此发现授权服务器 → 动态注册公共客户端 → 打开浏览器让用户登录并同意 → 交换令牌。整个流程对 AI 透明，**照常发起调用即可**，不要自己去拼授权链接、也不要向用户索要令牌。令牌过期由 WorkBuddy 用 `refresh_token` 自动续期并重试，通常无需处理；只有续期本身也失败时才会落到下表的 `UNAUTHORIZED`，那时才需要引导用户在 WorkBuddy 连接器里重新连接。

**用户隔离**：服务端以内省出的 `subject`（平台用户的匿名稳定标识）做配额与审计，**不暴露真实身份**；同一连接器下不同用户的调用互不影响。

技能侧**不需要也绝不应该**要求用户提供 URL、API Key、Token 或环境变量——这些都是不存在的配置项，让用户去找会让对话卡死。

| 被拒情形 | 处置 |
|---|---|
| `UNAUTHORIZED` | 提示"需在连接器里重新完成云极账号授权"，**停止后续调用** |
| `SCOPE_MISSING` | 提示"请重新完成云极账号授权"，**停止后续调用** |
| `QUOTA_EXCEEDED` | **立刻停止全部调用**，用已取到的数据出部分结果并写明缺口 |
| `UPSTREAM_UNAVAILABLE` / `UPSTREAM_TIMEOUT` | 工具返回**错误**（`ok=false`，不返回降级数据）；退避重试一次，仍失败则该项视为缺失、在报告注明缺口并附 `request_id` 便于排查；AI 生成类**不得重发**（不可重放，会重复计费） |
| `INVALID_ARGUMENT` | 参数错 / 日期错 / 枚举错。**不计费**，修正参数后重试 |
| `ENTITY_NOT_FOUND` | 请求合法，但上游确实没有这份数据（如 13xxxx 族）。告知用户"暂无数据"，**不要反复重试** |

配额按**云极账号**累计且跨会话有效，不要建议用户"换个会话再试"。完整说明见技能包 README 第 3 节。

---

## 概览

本技能以编排为主：默认只调用 `*` MCP 工具取数、返回结构化 JSON；需要落盘时用 `scripts/to_csv.py` 把响应信封写成 CSV / JSON（见「输出规范」）。

- 需要**数值、序列、宽表、可比数据** → 本技能
- 需要**成段的投研结论** → `yj-fin-research`
- 需要**文档原文怎么说的** → `yj-fin-knowledge`

> 当前运行时说明：上述 `yj-fin-research` / `yj-fin-knowledge` 在本环境未单独安装，但其核心取数能力（`knowledge_search` / `fetch_document` / `meeting_summary_list` / `domestic_chief_opinion_list` / `management_discussion` / `qa_list`）**已作为本 MCP 自身工具直接暴露**，调用时一律走 `yj-fin-data`，不要跳转到未安装的独立技能。

**统一信封**：所有工具返回 `{ok, data, error, meta}`。`data` 是要的数，`meta` 里有 `sources`（来源与时点）、`coverage`（覆盖率）、`degraded`（是否降级）、`missing_fields`（缺列）。

---

## 通用规则（每次调用前过一遍）

1. **先解析代码**：任何需要 `security_code` 的工具，先调 `securities_search`，拿到带交易所后缀的代码。一个标的在一次任务里**只解析一次**。
   - A 股 `600519.SH` / `000858.SZ` / `430047.BJ`
   - 港股 `00700.HK`
   - 美股 `AAPL.O`
   - 指数/概念/行业 `000001.SH`、`121000130.FIN`、`CI005001.CI`
2. **检索用证券名称**（不是拼音、不是简称猜测）。服务端有加权匹配，名称命中率最高。
3. **日期用真实当前日期推算**，不要凭印象写年份。
4. **报告期是英文闭集**：`q1`（一季报）/ `interim`（中报）/ `q3`（三季报）/ `annual`（年报）/ `latest`（最新一期，默认）。配合 `fiscal_year: ["2025"]` 定位具体年份的期次。**不要写 `2025Q3` 这种格式**，接口不认。
5. **空结果是答案不是错误**：`{total:0, list:[]}` 直接告诉用户"该区间无数据"，不要换条件反复重查。
6. **缺列照实标注**，绝不补 0。
7. **`volume` 单位是「股」**，`amount` 单位是元。

---

## 高风险操作（需确认）

以下三类调用**发起前先跟用户确认**，不要凭"应该需要"就调：

- **按份计费且不可重放的原文拉取**：`fetch_document` 按份计费、不可重放。取原文前确认用户确实需要**那一份**，避免对大文件 / 多份资料盲目拉取。
- **重参数查询耗时长是正常现象**：`limit` 拉满的日 K、全市场选择器、跨月分钟 K 这类重参数查询耗时较长（契约预算上限 120s），**不要因为短暂无响应就中断或重复发起**——重复发起等于重复计费。
- **涉及费用或不可逆下载时**：先向用户确认范围（要哪几份、多大区间）再调用。

---

## 1. 证券解析 · `securities_search`

一切取数的第一步。

```json
{ "keyword": "贵州茅台", "top": 5 }
```

| 入参 | 类型 | 说明 |
|---|---|---|
| `keyword` | string | 必填。名称/简称/拼音/代码 |
| `top` | int | 1–10，默认 5，**上限 10** |
| `category` | string | 可选，证券类别（如 `index` 只搜指数） |

返回 `data.rows[]`：`{security_code, security_name, abbr, exchange, category, ...}`，按相关度排序。

> 服务端会做强弱匹配过滤：有强匹配时丢弃弱匹配。**返回空或只有一条时就是唯一答案**；多条时取第一条，但要在上下文里说明"命中 N 个候选，取最相关的 X"。

---

## 2. 行情

### 2.1 日 K

| 市场 | 工具 |
|---|---|
| A 股 | `quote_daily` |
| 港股 | `quote_daily_hk` |
| 美股 | `quote_daily_us` |
| 指数（交易所/概念/行业） | `quote_index_daily` |

```json
{
  "security_list": ["600519.SH", "000858.SZ"],
  "start_date": "2026-01-01",
  "end_date": "2026-09-22",
  "limit": 10000,
  "field_list": ["security_code","trade_date","open","high","low","close","pre_close","change","pct_change","volume","amount"]
}
```

- `field_list` **显式传**。不传的语义不稳定，且返回**只包含点名的列**——需要证券代码就必须把它写进去。
- 全市场关键字是 `a_shares` / `hk_stocks` / `us_stocks`，**不是** `all`，且必须单独传。
- `limit` 上限 10000。

### 2.2 分钟 K · `quote_minute`

仅 A 股及指数。`start_date`/`end_date` 带时分秒：`"2026-04-23 10:00:00"`。字段里日期列是 `trade_time` 不是 `trade_date`。

### 2.3 实时快照 · `quote_realtime`

覆盖 A/港/美。字段：`security_code, exchange, trade_date, trade_time, latest_price, open, high, low, pre_close, change, pct_change, volume, amount, amplitude`。

> 实时接口**不再返回**换手率与量比，改为返回 `trade_status`。需要换手率走 EDE（`indicator_time_series`）。
> 日频指标**不覆盖当天实时**。

### 2.4 资金流向 · `quote_fund_flow`

仅 A 股（`.SH`/`.SZ`/`.BJ`），历史数据，**无实时**。含小/中/大/特大单及主力净流入。

```json
{ "security_list": ["600519.SH"], "start_date": "2026-05-01", "end_date": "2026-05-20", "limit": 10000,
  "field_list": ["security_code","trade_date","main_net_inflow","small_inflow","large_inflow"] }
```

### 2.5 复权因子 · `quote_adjust_factor`

```json
{ "security_list": ["600519.SH"], "start_date": "2020-01-01", "end_date": "2026-09-22", "limit": 10000 }
```

> 无 `field_list`。用于把不复权序列换算成前/后复权。⚠️ 本能力尚待上线后实测确认可用性。

---

## 3. 财务三大报表

| 报表 | 工具 |
|---|---|
| 利润表 | `financial_income` |
| 资产负债表 | `financial_balance` |
| 现金流量表 | `financial_cashflow` |

```json
{
  "security_code": "600519.SH",
  "market": "a",
  "period_type": "accumulated",
  "fiscal_year": ["2024","2025"],
  "period": ["annual","latest"],
  "report_type": ["consolidated"],
  "field_list": ["total_op_rev","total_op_cost","net_profit","basic_eps"]
}
```

| 入参 | 说明 |
|---|---|
| `market` | `a`（默认）/ `hk` / `us` |
| `period_type` | `accumulated`（累计，默认）/ `quarterly`（单季）。**港股/美股只有累计**，传 `quarterly` 无效 |
| `period` | 闭集 `q1` / `interim` / `q3` / `annual` / `latest`，默认 `["latest"]`。**与 `fiscal_year` 是"或"的关系**：给 `fiscal_year` 就拿该年份对应期次，不给则按 `period` 取最近一期 |
| `fiscal_year` | 年份数组，如 `["2024","2025"]` |
| `report_type` | 闭集 `consolidated`（合并，默认）/ `consolidated_restated` / `standalone` / `standalone_restated` |
| `field_list` | 建议显式传；不传返回全部科目 |

**四条硬约束**：

- 时点对齐用 **`earliest_annc_date`**（最早公告日期），**不要用财报截止日 `date`**——否则前复权口径下会把尚未披露的期次算进去。
- 港股/美股报表是 **China GAAP** 口径，与美国本土 GAAP 不同。跨市场比较时必须说明。
- 缺失值一律 `null`，不是 0。

报表科目字段名、枚举闭集、行情字段清单见 `references/fields-and-enums.md`；拿到实际响应后回写该文件。

---

## 4. 主营构成 · `business_segments`

```json
{ "security_code": "002594.SZ", "breakdown": "industry", "fiscal_year": ["2025"], "period": ["annual"] }
```

`breakdown`：`product` / `industry` / `region`。**不传则并发拉三种拆分**（成本高三倍，需要哪种就传哪种）。
`period` 仅支持 `interim`（中报）与 `annual`（年报）。

用途：判断行业归属（FDD 第一层）、看产品集中度与毛利率差异。

---

## 5. 股东结构 · `top_holders`

```json
{ "security_code": "600519.SH", "holder_type": "top10", "period": ["latest"] }
```

`holder_type`：`top10`（前十大股东）/ `top10_float`（前十大流通股东）。支持 `start_date`/`end_date` 区间或 `fiscal_year`，可叠加 `period`。

---

## 6. 盈利预测 · `earnings_consensus`

券商一致预期。

```json
{ "security_code": "600519.SH", "start_date": "2026-03-20", "end_date": "2026-03-25",
  "consensus_list": ["net_income","eps","pe"] }
```

`consensus_list` 不传返回全部可选字段。返回展开为 `security_code | date | 预测年份 | ...` 的扁平表。
单日无数据时服务端会向前回退一天重试一次——这是**正常兜底不是降级**，不要据此判 `degraded`。

---

## 7. 估值分析 · `valuation_analysis`

```json
{ "security_code": "600519.SH", "indicator": "pe_ttm",
  "start_date": "2020-01-01", "end_date": "2026-09-22", "limit": 10000,
  "field_list": ["value","percentile_rank"] }
```

`indicator` **闭集**：`pe_ttm` / `ps_ttm` / `pb_mrq` / `peg` / `pcf_ttm` / `em`（企业倍数）。多个指标要分别调（并发扇出 5）。

`percentile_rank` = 在 N 年中所处分位（N=1）。**历史分位比绝对比值更有信息量**——报告里两个都要给。

> 本工具**不暴露 `skipNull`** 参数。它与 `field_list` 组合会把正常数据过滤成 0 行，是已知的静默错数坑。

---

## 8. 行业与宏观指标

两步：**先检索指标 ID，再取数**。

```json
// ① macro_indicator_search
{ "keyword": "新能源汽车销量", "limit": 20 }
// → data[]: {indicator_id, indicator_name, frequency, unit, ...}

// ② macro_indicator_series
{ "indicator_id_list": ["S14001618","S14001620"], "start_date": "2010-01-01", "end_date": "2015-01-01" }
```

**检索技巧（重要）**：

- 中国宏观指标名中**不含"中国"**——指标名没提国家就是中国的。
- 大宗商品别搜"价格"，搜**现货价 / 结算价 / 收盘价**。
- 产品级数据（如某车型销量）只能在 EDB 找到，财报里没有。
- 单次批量上限 **10 个指标**。
- 频率后缀：`daily` / `weekly` / `monthly` / `quarterly` / `halfyearly` / `yearly`。

**分品牌销售这类查不到**：例如"比亚迪分品牌销量"不存在，需要先去知识库查比亚迪有哪些品牌，再对每个品牌单独检索（"比亚迪 元plus 零售量"）。

---

## 9. 公司指标（EDE）

证券级指标库，覆盖行情、财报科目、财务比率、分红、盈利预测、公司属性。**目前仅 A 股。**

```json
// ① indicator_search —— 拿到指标 code 和它的参数定义
{ "keyword": "收盘价", "limit": 20 }
// → data[]: {indicator_code, indicator_name, score, description, scope_markets[],
//            及参数行 param_key / param_name / param_type / param_description / param_required / param_default / param_enum}

// ② indicator_time_series
{ "start_date": "2026-03-31", "end_date": "2026-03-31",
  "indicator_code_list": ["qte_close"], "universe": ["600519.SH"] }
```

语义：**多指标 × 单证券**，或**单指标 × 多证券**。批量按"谁少谁拆"分批。

参数覆盖（`-p` 等价物）：`indicator_param_list` 支持全局参数与单指标参数并存：

```json
{ "indicator_param_list": [
    {"indicator_code":"qte_high","param":{"adjustType":"3"}},
    {"indicator_code":"qte_close","param":{"adjustType":"2"}}
]}
```

**三条硬约束**：

- `calendar_type` **不传时接口默认是 `ND` 不是 `TD`**。给报告期类指标传 `TD` 会整片返 `null` **且不报错**。报告期类指标显式传 `calendar_type`。
- 单次 **3 万单元格**上限。
- 季度日期：`03-31` / `06-30` / `09-30` / `12-31`。
- `indicator_cross_section`（多指标 × 多证券 × 单日期）为 P2 能力，需要横向截面时再用。

---

## 10. 题材指数

```json
// ① concept_search —— 题材名 → concept_id
{ "keyword": "机器人" }

// ② concept_info —— 题材档案（定义/投资逻辑/行业空间/竞争格局）
{ "concept_id": "121000130" }

// ③ concept_securities —— 分组成分股
{ "concept_id": "121000130" }
```

`concept_info` 返回的是**叙事性 Markdown**（定义、投资逻辑、行业空间、竞争格局），不是数值表——这是少见的"文本型"数据工具，可以直接引用进报告。
`concept_securities` 返回 `{summary, rows:[{group_name, security_code, security_name}]}`，按组分。

> ⚠️ 题材档案存在两个版本，上线前需实测确认生效的版本。本工具标 `no-replay`：传输层 5xx **不重放**，否则可能重复计费。

---

## 11. 板块成分股

```json
// ① sector_search
{ "keyword": "半导体", "top": 10 }
// ② sector_constituents
{ "sector_id": "121000130" }
```

关键词唯一高置信命中时可直接取成分股；多命中时**先把候选列给用户确认**，不要自行挑一个。

---

## 12. 排障速查

| 现象 | 判据 | 处置 |
|---|---|---|
| 所有工具都 `UNAUTHORIZED` | `error.code` | 凭据问题，检查 AK/SK。**不要重试**（坏凭据不自愈） |
| 单个工具 401 | 裸 HTTP 401 | token 过期，服务端已自愈一次；再失败才是真问题 |
| `INVALID_ARGUMENT` + `110003` | 超出可查时间范围 | 账号数据权限限制，**换工具绕不过去**，缩短区间 |
| 返回行数少于提交数 | `stock_highlights` | 正常：无看点的证券不在返回列表里 |
| 整片 `null` | EDE 报告期指标 | 八成是 `calendar_type` 传错，改显式传 |
| `meta.degraded=true` | 部分失败 | 报告里必须写明缺什么、为什么 |
| 数据看着完整但可疑 | `total` 可能是 ES 封顶值 | 用 `from=total,size=1` 探针验证；标 `_partial_reason=total_capped` |

---

## 输出规范

- **默认直接把 JSON 放进上下文**，由 LLM 分析/制表。
- 超过 **200 行**或用户明确要文件时，用 `scripts/to_csv.py` 落盘：它消费工具返回的
  **统一信封**（把响应 JSON 存成文件，或用管道从 stdin 送入），按 `data` 形状自动落
  `.csv`（二维表）或 `.json`（非表结构 / 标量 / 取文件 kind），并把**脚本 stdout 打印的
  绝对路径**告知用户：

```bash
# 主路径：先把工具响应信封存成文件，再交给脚本落盘（stdout 只打印产物绝对路径）
python3 scripts/to_csv.py /tmp/quote_daily_response.json

# 也支持从 stdin 读（管道）
cat /tmp/financial_income_response.json | python3 scripts/to_csv.py -

# 需要时覆盖输出目录 / 强制 JSON
python3 scripts/to_csv.py resp.json --out-dir ./out --format json
```

  落盘纪律（与第 6 条「缺列照实标注，绝不补 0」一脉相承）：

  - CSV 一律 **UTF-8 带 BOM**——中文金融表不带 BOM 时 Excel 打开会乱码。
  - `null` 一律写**空单元格**，**绝不补 0**；`missing_fields` 写进 CSV 首行 `#` 注释与
    同名 `.meta.json` 旁注，并在 stderr 提示，**绝不静默丢弃**。
  - 下面「缺失写 `—`」是对**报告正文**的排版约定；落盘 CSV 里缺失用空单元格。
- 制表时**数字右对齐、同比箭头红涨绿跌**（中国市场惯例）、缺失写 `—`。
- 任何来源与时点**从 `meta.sources` 取**，不要自己编。
