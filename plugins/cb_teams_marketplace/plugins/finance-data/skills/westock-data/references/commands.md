# WeStock Data - 详细命令用法

> 本文档包含所有命令的完整语法、参数说明、使用示例。
> 按功能分组组织，便于快速查找。

> ⚙️ **示例约定**：统一 CLI，格式为 `westock <子命令> [参数]`。

> 📌 **配套文档**：
> - 路由规则、高频意图对照、能力差异速查 → [routing-guide.md](./routing-guide.md)
> - 完整分析场景模板 → [scenarios-guide.md](./scenarios-guide.md)
> - 返回字段说明 → [ai_usage_guide.md](./ai_usage_guide.md)
>
---

## 一、行情

> 价格序列（实时行情、分时、K 线）。含单标的时序数据（`westock quote`/`westock kline`/`westock minute`）。

### 实时行情与 K 线

```bash
westock search 腾讯控股                    # 默认仅搜股票（A股/港股/美股，排除 ETF/可转债/板块/指数等）
westock search 沪深300 --type etf          # 搜索 ETF
westock search 银行 --type sector          # 搜索板块
westock search 黄金 --type futures         # 搜索期货
westock search 离岸 --type forex           # 搜索外汇
westock search 三星电子 --market kr        # 日韩股专用入口（独立于 --type）
westock quote sh600000                    # 实时行情（个股/指数/板块/ETF）
westock quote sh600000 --date 2026-03-20  # 指定历史日行情（涨跌幅/量比/收盘价等，见 ai_usage_guide.md）
westock quote ks005930,t7203              # 日韩股票实时行情（韩股 ks/kq、日股 t，支持批量）
westock kline sh600000 --period day --limit 20    # K线（m1/m5/m15/m30/m60/m120/day/week/month/season/year）
westock kline sz000001 --period day --limit 60 --fq qfq    # 复权（qfq/hfq/bfq，默认不复权；指数/板块/港股/美股/可转债强制不复权）
westock kline sh600000 --start 2025-01-01 --end 2025-12-31    # 按日期范围查K（优先级高于 --limit）
westock kline sh600000 --start 2025-06-01                     # 仅指定起始日（end=今天）
westock minute sh600000 --days 5          # 分时（1~5日）

```

> 实时行情按市场差异化：A股含涨跌停价/盘前竞价/每手/股息TTM；港股含每手/ADR；美股含盘前盘后/EPS TTM。`westock search`/`westock minute` 不支持多代码批量；`westock fund flow` 跨市场须分开查。完整列表见 [SKILL.md](../SKILL.md) 或 [routing-guide.md §六/§九](./routing-guide.md)。
> **K线日期范围**：`westock kline` 支持 `--start` / `--end`（YYYY-MM-DD），优先级高于 `--limit`；范围模式下 `--limit` 仅作为返回条数上限保护，默认放宽到 2000。仅指定 `--start` 时 `end` 默认今天；仅指定 `--end` 时自动按周期回溯一段窗口。**期货/外汇 K 线暂不支持日期范围**，传入会自动降级到 `--limit` 模式并提示。
> **单次查询窗口上限**：单次请求返回的 K 线条数有上限，超过上限时仅返回固定数量的数据。
> ⚠️ **分钟K标的范围**：分钟K（`m1/m5/m15/m30/m60/m120`）支持除**美股指数**外的所有标的；美股指数仅支持日K，带分钟周期会返回 `KLINE_002`。分钟K必须指定 `--start/--end`（近1个月内），强制不复权。
> **统一 `westock search`**：**默认仅搜股票**（A股/港股/美股个股）；用 `--type etf|bond|sector|index|futures|forex` 切换到其它类型，`--type` 支持**逗号分隔多个类型同时搜**（如 `--type etf,index,sector`，按类型分组输出）；日韩股用独立 `--market jp|kr` 入口。⚠️ **港股/美股/沪深不要加 `--market`**（默认搜索已覆盖），`--market` 仅接受 `jp|kr`，传 `hk`/`us`/`hs` 会报错。
> **日韩股票**：`westock quote` 支持韩股 `ks*`/`kq*`（如 `ks005930` 三星电子）、日股 `t*`（如 `t7203` 丰田），可批量；仅支持搜索与实时行情，**不支持** K线/分时/技术指标/筹码等；行情源不直接返回涨跌额/涨跌幅（由最新价与昨收自算），货币为韩元/日元，展示时禁用人民币符号；代码请先用 `westock search --market jp|kr` 获取（日韩股使用独立 `--market` 入口，不归在 `--type` 下）。

---

## 二、技术分析

> 衍生指标与筹码分布（`westock technical`/`westock chip`）。与原始行情数据不同，均为量价推算的分析结果。

### 技术指标与筹码

```bash
westock technical sh600000   # 技术指标（默认返回 MA/MACD/KDJ/RSI/BOLL：均线 MA_5/10/20/60/120/250、MACD(DIF/DEA)、RSI_6/12/24、KDJ_K/D/J、BOLL 上中下轨）
westock technical sh600000 --start 2026-02-01 --end 2026-03-01    # 历史区间
westock chip sh600519                         # 筹码成本（仅沪深京A股）

```

> 技术指标输出截面或历史区间数据；筹码成本仅支持沪深京A股，用于分析获利盘/套牢盘比例。

---

## 三、市场

> 全市场截面/总览/互联互通。含龙虎榜、市场总览（A 股大盘画像）、涨跌分布、沪深港通成份股。

### 龙虎榜（仅A股）

```bash
westock lhb                                  # 全市场龙虎榜（默认，tab=all，当日全部上榜股票）
westock lhb --type all --date 2026-03-20     # 显式指定全市场龙虎榜
westock lhb --type institution,hotmoney      # 分类榜（机构榜/游资榜/活跃席位/高胜率买入/高胜率席位）
westock lhb --type activeseat --date 2026-03-20

```

> 龙虎榜仅支持A股。

> ⚠️ **一级 `lhb` vs `fund lhb` 差异**：`westock lhb`（本段）＝ **全市场龙虎榜榜单**，按 `--type`（机构榜/游资榜/活跃席位等）筛选，**不带个股代码**；`westock fund lhb <代码>`（见 §九 资金）＝ **指定个股**的龙虎榜明细（成交统计 `LhbInfos` + 营业部买卖 `LhbTradingDetails`）。二者不要混用。

### 市场总览（A 股大盘画像）

> `westock market-overview` 是 A 股大盘的"宏观体检"：8个维度（画像总评/收盘/区间/技术/涨跌分布/两融/估值/风格）共用同一组 `market_statis_*` 后端清单。
> 不带 type 时默认输出 **summary 画像总评**（14 维度得分 + 状态文案，含估值/情绪/技术/趋势/风格轮动等），
> 是给 LLM 做"市场点评"最直接的入口。

```bash
westock market-overview                                          # 默认 = summary（市场画像总评）
westock market-overview --type trade                             # 三大指数收盘统计 + 两市成交额多周期均值
westock market-overview --type interval                          # 三大指数 5/10/20/60/120/250D 涨跌 + 52W 高低
westock market-overview --type technical                         # 大盘 MACD/KDJ/RSI/BOLL/MA + 神奇九转
westock market-overview --type updown                            # A 股涨跌停/红绿盘/多周期新高新低数
westock market-overview --type margin                            # 两融余额多周期变动
westock market-overview --type valuation                         # 中证全指 PE/PB/PS + 历史百分位（数据通常滞后 1~4 个交易日）
westock market-overview --type rotation                          # 沪深300/中证1000/成长/价值 风格轮动
westock market-overview --type technical,updown                  # 多类一次拉
westock market-overview --type all --date 2026-05-18             # 全部 8 类
westock market-overview list                                     # 列出全部 type

```

### 沪深港通成份股（互联互通）

```bash
westock connect --exchange sh                              # 沪股通成份股（北向 / 陆股通标的池）
westock connect --exchange sz --limit 50 --offset 50       # 深股通成份股（统一用 --limit/--offset 分页）

```

> ⚠️ **职责边界**：`westock connect` = 沪深港通**标的池**（标的列表）；`westock fund flow sh600000` = 北向资金流量（金额数据）；二者不要混用。

### 新股日历

```bash
westock ipo --market hs                    # 新股日历（--market hs/hk/us）

```

> 新股日历查询新股申购与上市信息，支持沪深/港股/美股三个市场。

### A 股交易日历

```bash
westock trade-calendar                                    # 默认当月
westock trade-calendar --date 2026-06-09                  # 单日是否交易日
westock trade-calendar --start 2026-06-01 --end 2026-06-30  # 区间
westock trade-calendar --year 2026 --trading-only         # 全年仅交易日

```

> ⚠️ **`westock trade-calendar` vs `westock calendar`**：`westock trade-calendar` 查**交易所开市/休市**（清单 `calendar_hsj`）；`westock calendar` 查**个股投资事件**（分红/财报/新股等）。二者不可混用。

### 市场涨跌分布

```bash
westock changedist                         # 沪深A股涨跌分布（涨跌/涨跌停/停牌家数 + 上涨占比情绪 + 涨跌幅区间分布 + 两市成交额）

```

> 涨跌分布为沪深A股全市场截面（实时）：概览含上涨/下跌/平盘、涨停/跌停、停牌家数与上涨占比情绪文案；明细为 11 个涨跌幅区间（涨停→>7%→…→平→…→跌停）的家数分布，并附两市成交额及其较上日变动。

---

## 四、指数

> 指数清单、搜索与成份股（A 股 + 港股）。行情/K 线/分时复用 `westock quote` / `westock kline` / `westock minute`。

```bash
westock index constituent sh000300        # A股指数成份股
westock index constituent hkHSI           # 港股指数成份股（恒生指数）
westock index constituent hkHSCEI,hkHSTECH # 多个港股指数
westock index list                         # 指数清单（支持 --limit/--offset 分页）
westock search 沪深300 --type index        # 搜索指数（统一 search 入口）

```

**常用指数**：`sh000001`(上证)、`sz399001`(深证成指)、`sz399006`(创业板)、`hkHSI`(恒生)、`us.IXIC`(纳斯达克)、`us.INX`(标普500)

---

## 五、板块

> 板块/概念股查询（搜索/成份股/信息/行情榜/经营/估值）。

### 板块成份股（含概念股查询）

> ⚠️ **概念股查询**："华为概念股"、"AI 概念股"等问法 → 用 `westock search <关键词> --type sector` → `westock sector constituent <代码>` 两步查询。

```bash
westock search 华为 --type sector            # 搜索板块代码（华为/AI/新能源等概念）
westock sector constituent pt01801080        # 板块成份股

```

> **板块代码**：使用 `westock search --type sector` 返回的 code（如 `pt01801080`、`pt02GN2328`）。

> **`westock sector constituent <代码>` vs `westock sector info <代码>`**：
> - `westock sector constituent <代码>`：返回板块**全部成份股**（含 SectorCode 字段，可逐只展开分析）
> - `westock sector info <代码>`：返回板块**基础信息 + 区间交易数据**（名称、板块类型、成份股数量、区间涨跌幅、区间成交额等）。**不含成份股**，适合用户问"XX板块怎么样"等总览类问题。
>
> ⚠️ **查个股所属行业/板块**（如"茅台属于哪个板块"）→ 用 `westock profile <代码>`，**不要**用 `westock sector constituent`（方向相反，且不接受 sh/sz 个股代码）。

### 行业经营数据（价格/产量/销量等）

> 查询各行业经营指标的历史序列数据，覆盖20+行业。数据包括价格、产量、销量、收入等经营指标。

```bash
westock sector oper 煤炭
westock sector oper 煤炭 --date 2026-06-15
westock sector oper --list               # 列出所有支持经营数据的行业

```

> **行业标识**（非板块代码 pt*）：`media`(传媒) / `elec`(电力设备) / `eltn`(电子) / `re`(房地产) / `text`(纺织服饰) / `nbfin`(非银金融) / `steel`(钢铁) / `utils`(公用事业) / `dfnse`(国防军工) / `env`(环保) / `mach`(机械设备) / `chem`(基础化工) / `comp`(计算机) / `happl`(家用电器) / `bmat`(建筑材料) / `bldg`(建筑装饰) / `trans`(交通运输) / `coal`(煤炭) / `cosm`(美容护理) / `agri`(农林牧渔) / `auto`(汽车) / `trade`(商贸零售) / `socsv`(社会服务) / `petro`(石油石化) / `food`(食品饮料) / `comm`(通信) / `pharm`(医药生物) / `bank`(银行) / `metal`(有色金属)

> **参数说明**：
> - `<行业>`：支持中文名称（如"煤炭"）或标识（如 `coal`），**不要**传板块代码（如 `pt02021291`）
> - `--list`/`-l`：列出所有支持经营数据的行业
> - `--date`：查询日期 YYYY-MM-DD（默认今天）

---

### 板块行情榜（涨幅 / 资金流向）

```bash
westock sector ranking                     # 行业涨幅榜（默认：industry + changePct + 降序）
westock sector ranking --kind concept      # 概念板块榜
westock sector ranking --type mainNetInflow        # 行业榜按主力净流入排序
westock sector ranking --kind concept --type mainNetInflow --order asc   # 概念榜按主力净流入升序（净流出最多在前）
westock sector ranking --order asc         # 涨幅升序（跌幅榜）

```

**参数**：
- `--kind`：`industry`（行业，默认）/ `concept`（概念）
- `--type` 排序字段：`changePct`（涨跌幅，默认）/ `turnover`（成交额）/ `mainInflow`（主力流入）/ `mainOutflow`（主力流出）/ `mainNetInflow`（主力净流入）/ `mainNetInflow5d`（5日主力净流入）/ `mainNetInflow20d`（20日主力净流入）
- `--order`：`desc`（降序，默认）/ `asc`（升序）

> 金额字段（turnover/mainInflow/mainOutflow/mainNetInflow 等）为**原样数值**（万元），不做单位换算。

> **`westock sector ranking` vs `westock sector constituent/info` vs `westock hot sector` 区分**：
> - `westock sector ranking`：**全市场板块行情榜**（行业/概念，按涨跌幅/成交额/主力资金排序），用于"今天哪些板块在涨/资金在流向哪"类问题
> - `westock sector constituent/info`：**按代码精查**（成份股 / 画像 / 区间交易），用于"消费板块成份股有哪些 / 半导体板块怎么样"类问题
> - `westock hot sector`（hot 子命令）：板块**热度**排名（搜索/讨论度），用于"哪些板块最火"类问题
> - 决策入口：泛问"市场上哪些板块涨得多/资金流向" → `westock sector ranking`；指定"XX 板块的成份股/画像" → `westock sector constituent/info`；问"哪些板块最热" → `westock hot sector`

### 板块估值（PE/PB/PS/PCF/DIV + 历史百分位）

```bash
westock sector valuation pt01801080
westock sector valuation pt01801080,pt01801081
westock sector valuation pt01801080 --date 2026-06-25
westock sector valuation pt01801080 --start 2026-01-01 --end 2026-06-25

```

> **参数说明**：
> - 仅支持 **板块代码**（`pt*`）
> - `--date`：单日精查；`--start` + `--end`：历史序列（每次单板块）

### 行业未来盈利预测

```bash
westock sector forecast pt01801780
westock sector forecast pt01801780,pt01801081
westock sector forecast pt01801780 --date 2026-06-25

```

> **参数说明**：
> - 仅支持 **申万一级/二级行业**板块代码（`pt*`）
> - 输出未来 3 年一致预期表，列含 `year | revenue | netProfit | netAssets | revenueYoy | netProfitYoy | netProfitCagr2Y | pe | pb | ps | roe | peg`（字段说明见 `ai_usage_guide.md` §sector forecast）

### 行业财务指标

```bash
westock sector finance pt01801780
westock sector finance pt01801780,pt01801080
westock sector finance pt01801780 --date 2026-03-31
westock sector finance pt01801780 --start 2020-01-01 --end 2026-03-31

```

> **参数说明**：
> - 支持申万 **一级/二级/三级**行业（`pt*`）
> - 默认最新财务截面；`--start` + `--end` 查询同业内历史变动
> - 聚源概念/地域不支持；字段说明见 `ai_usage_guide.md` §sector finance

---

## 六、研究

> 评分/评级/一致预期/研报。覆盖个股的多维度评估视角。

### 评估与研究

```bash
westock score sh600519                        # 个股评分（综合/资金/基本面/风险/技术 + 周/月/季变动）
                                                   # ↑ 单股查询；评分排行选股请用 westock screen ranking --type CompScore
westock esg sh600519                          # ESG 评级（默认中证+聚源双源）
westock esg sh600519 --source csi             # 仅中证 ESG
westock rating hk00700                       # 机构评级（港股/美股，3段：目标价&评级 / 评级月度趋势 / 价格 vs 目标价）
westock consensus sh600519                    # 一致预期（A股、港股，自动分发）
westock report list sh600000 --limit 20       # 个股研报列表
westock report list pt01801080 --limit 20     # 行业/板块研报列表（支持个股代码与行业代码）
westock report detail <研报ID>                # 研报详情（ID 从研报列表获取）

```

> **`westock report` 命令使用流程**：
> ⚠️ `report` **仅支持 `list` / `detail` 两个子命令**。机构评级、一致预期是**独立顶层命令**，**不要**写成 `report rating` / `report consensus`：
> - 机构评级：`westock rating <代码>`（港股/美股，如 `westock rating hk00700`）
> - 一致预期：`westock consensus <代码>`（A股/港股，如 `westock consensus sh600519`）
> 1. 先通过 `westock report list sh600000`（个股）或 `westock report list pt01801080`（行业）获取研报列表
> 2. 从列表中复制研报 ID（如 `res832471322631`）
> 3. 使用 `westock report detail res832471322631` 查看完整研报内容

---

## 七、事件

> 事件标签/风险事件/投资日历/停复牌。覆盖个股的事件监控、风险明细与交易状态。

### 事件总览（42 类标签）

> **`westock risk` vs `westock events` 决策入口**：
> - 用户**泛问**"XX 公司有什么风险/事件" → **优先 `westock events`**（看全貌，标签化输出，覆盖中性+利好+风险 42 类）
> - 用户**指定**风险细节（如"质押率"、"诉讼明细"、"解禁规模"） → 用 `westock risk --types <类型>`（含明细字段，仅 8 类）
> - 二者关系：`westock events` 是入口与速览，`westock risk` 是钻取与细查；先 events 后 risk 是常规链路

```bash
westock events sh600519                  # 单股事件标签
westock events sh600519,sz000001         # 批量

```

**事件大类**（共 9 组 42 类）：交易异动（大宗/龙虎榜）、股本变动（回购/定增/分红）、业绩披露（快报/预告/财报）、指数变动（纳入/剔除）、董监高（变动/增减持）、股权事件（股东大会/重组/更名/要约）、限售解禁、法律处罚、停复牌。完整 ID→中文映射见下方 `ai_usage_guide.md` 中的 42 类事件 ID 映射表。

### 投资日历

查询个股事件日历，按事件类型分组输出。宏观经济日历请使用 `westock macro indicator cn_calendar_future|cn_calendar_hist`。

```bash
westock calendar                                          # 今天所有类型事件
westock calendar --date 2026-06-04                      # 指定日期
westock calendar --event dividend                          # 只看分红派息
westock calendar --event financial_report --market hs     # 财报发布（沪深）
westock calendar --event ipo --market hk                # 新股发行（港股）
westock calendar --event trading_halt,meeting,lockup_release  # 多类型（逗号分隔）
westock calendar --event all --market us --limit 30     # 美股所有事件，限制30条

```

**参数说明**：

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--date` | 查询日期 YYYY-MM-DD | 今天 |
| `--event` | 事件类型过滤，可选值见下表 | `all` |
| `--market` | 市场：`hs`（沪深）/ `hk`（港股）/ `us`（美股） | `hs` |
| `--limit` | 返回条数 | 10 |

**`--event` 可选值**：

| 英文术语 | 中文标签 | API 短码 |
| --- | --- | --- |
| `financial_report` | 财报发布 | cbfb |
| `westock dividend` | 分红派息 | fh |
| `westock ipo` | 新股发行 | xg |
| `trading_halt` | 停复牌 | tfp |
| `meeting` | 会议 | hy |
| `lockup_release` | 限售解禁 | jj |
| `rights_issue` | 增发 | zf |
| `all` | 全部（不筛选） | all |

> 输出按中文标签分组（财报发布/分红派息/新股发行/停复牌/会议/限售解禁/增发）。

### 风险事件（仅A股，8 种类型）

```bash
westock risk sh600000                            # 全部风险事件
westock risk sz000001 --types pledge,unlock      # 仅指定类型
westock risk sh600000,sz000001 --types pledge    # 批量

```

**8 种类型**：`specialtrade`(ST)、`pledge`(质押)、`unlock`(解禁)、`lawsuit`(诉讼)、`seasonedissue`(增发)、`leaderchange`(高管变动)、`executivetransfer`(高管增减持)、`bondrating`(评级)。

**别名**：`st`/`special`→specialtrade、`addition`→seasonedissue`、`leader`→leaderchange、`executive`→executivetransfer、`westock rating`→bondrating。

> 无效代码或无风险事件的股票会输出"暂无风险事件"。

### 停复牌信息

```bash
westock suspension --market hs             # 停复牌信息（--market hs/hk/us）

```

---

## 八、资讯

> 新闻、公告、原文。含个股新闻/公告和市场资讯。

### 新闻与公告

```bash
westock news list sh600000 --limit 20     # 个股新闻
westock news list sh000001 --limit 20     # 指数资讯（如上证指数）
westock news list sh000001,sz399001,sz399006 --limit 20   # 沪深市场资讯
westock news detail nesSN20260320...           # 新闻详情（id 来自 news 返回）
westock notice list sh600000 --type 1              # 公告列表（--type：0全部/1财务/2配股/3增发/4股权变动/5重大/6风险/7其他）
westock notice detail nos1224809143                # 公告全文（nos沪深→纯文本；nok港股/nou美股→PDF URL）

```

> `westock news list` 除个股外，还支持指数（`sh000001`）、ETF（`sh510300`）、板块（`pt01801081`）、可转债（`sh113052`）、期货（`fuCL`）、外汇（`fxUSDCNH`）等代码；接口不分页，用 `--limit` 控制返回条数。

> **市场/大盘资讯**：传指数代码，勿用个股代码。常用对照：
> - 沪深：`sh000001,sz399001,sz399006`（上证+深成指+创业板指）
> - 沪市：`sh000001,sh000016`；深市：`sz399001,sz399006`
> - 港股：`hkHSI,hkHSTECH`；美股：`us.DJI,us.IXIC`
> - 单指数：如 `westock news list sh000001`
>
> 多指数批量按标的分段展示；热文榜用 `westock hot news`（另一数据源）。

---

## 九、资金

> 二级市场资金数据。含个股资金、卖空数据、融资融券、大宗交易、龙虎榜、北向资金持仓。

### 资金流向（个股/板块）

```bash
# A股：主力资金（单日 / --start..--end 区间）
westock fund flow sh600000
westock fund flow sh600000,sz000001 --start 2026-05-01 --end 2026-05-20

# A股板块：资金流向（支持 pt 开头板块代码）
westock fund flow pt01801081

# 港股：资金流向
westock fund flow hk00700

# 港股：卖空数据（单日 --date / 区间 --start..--end，均支持多代码批量）
westock fund short hk00700
westock fund short hk00700 --date 2026-05-20
westock fund short hk00700 --start 2026-05-01 --end 2026-05-20

# 美股：卖空数据（单日 --date / 区间 --start..--end，均支持多代码批量）
westock fund short usAAPL
westock fund short usAAPL --date 2026-05-20
westock fund short usAAPL --start 2026-05-01 --end 2026-05-20

# 大宗交易（仅沪深）
westock fund block sh600519
westock fund block sh600519,sz000651
westock fund block sh600519 --date 2026-03-20                    # 指定单日
westock fund block sh601318 --start 2026-06-11 --end 2026-08-20   # 时间区间（逐交易日返回，仅含有成交的日期）

# 龙虎榜（仅沪深，按个股）
westock fund lhb sh600519                  # 当日（默认今天）
westock fund lhb sh600519,sz000651         # 多股同日批量
westock fund lhb sh600519 --date 2026-03-20          # 指定日期
westock fund lhb sh600519 --start 2026-05-25 --end 2026-07-24   # 时间区间（合并单表）

# 融资融券（仅沪深）
westock fund margin sh600519
westock fund margin sh600519,sz000651
westock fund margin sh600519 --date 2026-03-20                   # 指定单日（该日未披露会明确报 NOT_DISCLOSED）
westock fund margin sh600519 --start 2026-08-13 --end 2026-08-20  # 时间区间（逐交易日序列，算趋势用这个）

# 北向资金持仓（个股季度明细 / 申万行业分布）
westock fund north-holding sh600519              # 单股：最新季 + 次新季
westock fund north-holding sh600519,sz000651    # 多股批量
westock fund north-holding pt01801080            # 板块裸码（自动识别 sw 级别）
westock fund south-holding hk00700,hk03690       # 港股南下资金持仓

```

> ⚠️ **美股限制**：美股不支持 `westock fund flow`（资金流向），只支持 `westock fund short`（卖空数据）

> ⚠️ **命令区分**：`flow` = 资金流向（主力/散户）；`short` = 卖空；`block` = 大宗交易；`margin` = 融资融券；`lhb` = 个股龙虎榜（成交统计/营业部明细）；`north-holding` = A股北向**季度持仓**；`south-holding` = 港股南下**持仓快照**

> ⚠️ **北向数据职责边界**：
> - `westock connect` = 陆股通**标的池**（哪些股票可被北向交易）
> - `westock fund flow sh600000` = 个股日度**资金流向**
> - `westock fund north-holding sh600519` = A股**季度北向资金持仓**（最新季 + 次新季）
> - `westock fund south-holding hk00700` = 港股**南下资金持仓**（持有比例/日季变动）
> - `westock fund north-holding pt…` = 申万行业**北向资金持仓分布**（**不支持**聚源概念/地域板块）
> - 北向**成交活跃股 / 上榜频次**全市场榜单 → `westock screen ranking --type north_active_d` / `--type north_appear_m`（固定 Top20，不支持 `--limit`）

> ⚠️ **市场限制**：`block`/`margin`/`lhb` 仅支持沪深（sh/sz）；`short` 支持港股和美股；`flow` 支持沪深和港股（美股请用 `westock fund short`）

> ⚠️ **龙虎榜职责边界**：`westock lhb`（市场段）＝ 全市场龙虎榜榜**单**（机构榜/游资榜/活跃席位等，按 `--type` 筛选）；`westock fund lhb <代码>` ＝ **指定个股**的龙虎榜明细（成交统计 `LhbInfos` + 营业部买卖 `LhbTradingDetails`）。二者不要混用。

> 沪深港通成份股（北向 / 陆股通标的池）属于"市场"分组，见第二章；不在资金流量数据范围内。

---

## 十、简况

> 公司基本信息/股东/分红/回购。

### 公司基本信息

```bash
westock profile sh600000                  # 公司简况
westock shareholder sh600519              # 股东结构（A股：十大股东/十大流通/股东户数；港股：持股股东+机构持仓）
westock disclosure sh600519               # 财报披露日历（财报发布前的预约披露日）

```

### 分红数据

```bash
westock dividend sh600519 --years 5                           # 分红派息（A股/港股/美股）
westock dividend sh600519 --all                               # 含未实施的分红方案

```

> ⚠️ **货币单位**：港股返回港元/美元，美股返回美元，展示时必须标注正确货币单位

### 公司回购

```bash
westock buyback sh600519                 # 公司回购（A股/港股）
westock buyback sh600519,hk01810         # 批量回购（A/H 混批分表输出）
westock buyback hk01810 --start 2026-03-01 --end 2026-04-14

```

---

## 十一、财务

> 三大报表/财报披露日历。

### 财务数据

**默认行为**：省略 `--type` 时拉取 `income` + `balance` + `cashflow` 三大报表（单股/批量均支持）。显式 `--type` 时只拉一张表。

**支持参数**：`--type`（`income` \| `balance` \| `cashflow`）、`--limit`（期数）、`--start` / `--end`（日期区间，与 `--limit` 互斥）

| `--type` | 含义 | A股 | 港股 | 美股 |
|----------|------|-----|------|------|
| （省略） | 三大报表 | 利润表+资产负债+现金流 | 同左 | 同左 |
| `income` | 利润表 | 利润表 | 综合损益表 | Income Statement |
| `balance` | 资产负债表 | 资产负债表 | 资产负债表 | Balance Sheet |
| `cashflow` | 现金流量表 | 现金流量表 | 现金流量表 | Cash Flow |

```bash
westock finance sh600000                         # 三大表，最新 1 期
westock finance sh600519,sz000651 --limit 4        # 批量三大表（同市场）
westock finance hk01810,hk00700 --limit 1          # 港股批量三大表
westock finance sh600000 --type income --limit 8   # 仅利润表
westock finance hk00700 --type income --limit 4    # 仅综合损益表

# 按日期区间（与 --limit 互斥）
westock finance sh600000 --start 2024-01-01 --end 2024-12-31              # 三大表区间
westock finance sh600000 --type income --start 2024-01-01 --end 2024-12-31

```

> 跨市场批量对比须**同一市场**（字段口径不同）。

> **参数说明**：`--limit`（期数）与 `--start`/`--end`（日期区间）互斥，请只指定其中一组。日期格式：YYYY-MM-DD。
> **字段范围**：`--fields core`（默认，聚焦约 30 个核心指标）/ `--fields all`（全字段 100+ 列）。

### 财报披露日历

```bash
westock disclosure sh600519               # 财报披露日历（A股/港股/美股；又称业绩预约披露日）

```

---

## 十二、ETF

> 沪深场内 ETF（仅 `sh`/`sz`）。**子命令必填**（`westock profile` / `overview` / `holdings` / `nav`）；数据以 `etf_*` 清单为主，snapshot 补申赎清单/费率/资产配置/回撤，净值时序走 `stock_quote_history`。
>
> 全市场选基/排行 → `westock etf pool` / `westock etf rank`（不在本 skill）。

> ⚠️ **路由**：档案/费率/分类/经理/资产配置 → `westock etf profile`；收益/回撤/规模/溢折率/净申购/估值 → `westock etf overview`；净值历史 → `westock etf nav`（**不是 `westock kline`**）。不要用 `westock quote`/`westock kline` 拼凑基金维度字段。

```bash
westock etf profile sh510300          # 基金档案 + 资产配置 + 分类/经理
westock etf overview sh510300         # 运作概览：行情/规模/溢折率/回撤 + 资金流 + 估值
westock etf holdings sh510300         # 申赎清单成分股 + 重仓股涨跌
westock etf nav sh510300 --start 2026-01-01 --end 2026-03-31

```

> `westock search --type etf` 可能含 LOF/QDII；仅 `etfDetail=支持` 的 sh/sz 可走 `westock etf *`，其余用 `westock quote`/`westock kline`。

> 详细字段说明见 [references/ai_usage_guide.md](./ai_usage_guide.md)

---

## 十三、发现

> 搜索/热搜/股单。这一组命令是**全市场维度**工具（非按代码查个股，也非筛选选股），用于市场资讯浏览、热度发现、榜单查询。

### 市场资讯与热搜

```bash
westock hot stock                   # 热搜（子命令：stock/news/sector/etf；etf=热搜基金含ETF）

```

> 板块行情榜请用 `westock sector ranking`，按代码精查请用本章节的其它 `westock sector` 子命令。
> **日韩股票搜索**：`westock search 关键词 --market jp|kr` 按市场搜日股/韩股，返回统一前缀代码（韩股 `ks*`/`kq*`，日股 `t*`，如 `ks005930`/`t7203`）；`--market` 是 `westock search` 唯一的可选参数，也支持按数字代码搜（如 `westock search 005930 --market kr`）。⚠️ **港股/美股/沪深直接 `westock search 关键词` 即可，切勿加 `--market hk/us/hs`**（仅 `jp|kr` 合法，其它值报「--market 仅支持 jp|kr」）。

---

## 十四、宏观

> 宏观经济指标。覆盖中国（GDP/CPI/PMI/货币/财政/估值/专项）+ 美/港/日/欧主题宏观日历 + 36 个地区海外预期日历。

### 子命令总览

```bash
# 列出指标（可按 region 过滤）
westock macro list                                       # 列全部
westock macro list --region cn                           # 中国（32 个）
westock macro list --region us                           # 美股（29 个）
westock macro list --region jp                           # 日本（6 个）
westock macro list --region eu                           # 欧元区（6 个）
westock macro list --region hk                           # 港股（4 个）
westock macro list --region global                       # 海外预期 36 个地区
westock macro expect list                                # 仅列 36 个地区

# 主题型指标查询（cn/us/hk/jp/eu）
westock macro indicator <短名[,短名...]> [--year Y | --date D | --start S --end E]
westock macro indicator --region <r> [--date D]          # 一键拉某 region 全套

# 海外预期日历（按地区 iso3，按年）
westock macro expect --area <iso3> [--year Y | --start S --end E]

```

### 中国（cn）— 主题型指标

```bash
# 按年（GDP/价格/工业/消费/投资/货币/财政/预测/历史日历）
westock macro indicator cn_gdp --year 2025
westock macro indicator cn_cpi_ppi,cn_pmi --year 2025                 # 多指标
westock macro indicator cn_pmi --start 2023 --end 2025                # 区间趋势
westock macro indicator cn_fiscal --year 2025                          # 财政
westock macro indicator cn_yield_curve --year 2025                     # 国债收益率曲线
westock macro indicator cn_mlf --year 2025                             # MLF 操作

# 按日期（综合 / 估值 / 中国专项）
westock macro indicator cn_core --date 2026-06-09                      # 最新核心（一键 p1+p2）
westock macro indicator cn_premium_curve --date 2026-06-09             # 溢价率曲线
westock macro indicator cn_premium_value --date 2026-06-09             # 溢价率水平（10年分位）
westock macro indicator cn_term_spread --date 2026-06-09               # 期限利差
westock macro indicator cn_calendar_future --date 2026-06-09           # 宏观日历未来
westock macro indicator cn_lpr --date 2026-06-09                       # LPR
westock macro indicator cn_caixin_pmi --date 2026-06-09                # 财新 PMI
westock macro indicator cn_installed_capacity --date 2026-06-09        # 发电装机容量

```

### 美/港/日/欧 — 主题宏观（按日期，事件日历型）

```bash
# 美股
westock macro indicator us_employment --date 2026-06-09                # 美国就业
westock macro indicator us_inflation --date 2026-06-09                 # 美国通胀
westock macro indicator us_employment,us_inflation,us_monetary --date 2026-06-09  # 多指标
westock macro indicator --region us --date 2026-06-09                  # 一键拉美股 29 个
westock macro indicator --region us --date 2026-06-09 --limit 5        # 仅保留最近 5 条

# 港股
westock macro indicator hk_eco_growth --date 2026-06-09
westock macro indicator --region hk --date 2026-06-09                  # 一键拉港股 4 个

# 日本
westock macro indicator jp_inflation --date 2026-06-09
westock macro indicator --region jp --date 2026-06-09                  # 一键拉日本 6 个

# 欧元区
westock macro indicator eu_monetary --date 2026-06-09
westock macro indicator --region eu --date 2026-06-09                  # 一键拉欧元区 6 个

```

> 主题型返回 schema：`IndicatorName / OccurDate / OccurTime / ActualValue / ForecastValue / FormerValue`，按日期降序展示。

### 海外预期日历（global）— 按地区 iso3，按年

```bash
westock macro expect list                                     # 列 36 个地区 iso3 代码
westock macro expect --area chn --year 2025                # 中国
westock macro expect --area usa --year 2025                # 美国
westock macro expect --area jpn --year 2025                # 日本
westock macro expect --area usa --start 2023 --end 2025    # 区间

```

> 海外预期 schema 在主题型基础上多一列 `Importance`（1=低 / 2=中 / 3=高）。

> 短名命名规则与完整短名表（含中文名称、分组、查询方式）见 [macro-fields.md](./macro-fields.md)。

> **三种查询方式**：
> 1. **按年份**（`--year` 或 `--start --end`）：cn_gdp/cn_cpi_ppi/cn_pmi 等绝大多数中国指标，后端按 `YYYY-01-01` 查询
> 2. **按日期**（`--date`）：`cn_core`/`cn_premium_*`/`cn_term_spread`/`cn_calendar_future`/`cn_employment`/`cn_lpr` 等中国日频指标，以及**所有海外主题**（us_/hk_/jp_/eu_）
> 3. **海外预期独立子命令**：`westock macro expect --area <iso3> --year`（按地区归档，36 个地区）
>
> **聚合短名**：`cn_core` 一键拉 `cn_core_p1 + cn_core_p2`（同时返回 7 大核心指标，不要用多次单指标查询拼凑）
>
> **region 一键全套**：`westock macro indicator --region us --date <今天>` 一键拉该 region 全套主题（不传短名 + `--region`）
>
> **mode 校验**：传错 `--year` 给 mode=date 指标会报错；不确定时先 `westock macro list --region <r>` 查 mode

> 专业研究场景（宏观指标组合）见 [scenarios-guide.md](./scenarios-guide.md) 第十四章（14.1~14.23）。


---

## 十五、期货

> 外盘商品/金融期货（CME/COMEX/CBOT/NYMEX/LME 等）+ 港股股指期货。
> 标准代码前缀：`fu*`（外盘长版行情）、`hf_*`（LME 金属）、`r_hd*`（港股股指期货）。

### 合约搜索与资料

```bash
westock search 黄金 --type futures            # 关键词→合约代码（支持 名称/品类/交易所/代码）
westock search 贵金属 --type futures           # 按品类搜（贵金属/基本金属/能源化工/农产品/外汇/利率/股指/港股股指）
westock search 恒指 --type futures             # 港股股指期货
westock futures detail fuGC                   # 合约资料（交易所/规模/币种/最小变动/交易时间等）

```

### 期货行情（复用 quote）

```bash
westock quote fuGC                            # 黄金（COMEX，延时行情）
westock quote hf_CAD                           # 伦铜（LME）
westock quote r_hdHSImain                      # 恒生指数期货
westock quote fuGC,fuCL,fu6E                   # 批量（黄金/原油/欧元）

```

### 期货分时与 K 线（复用 minute / kline）

```bash
westock minute fuCN                            # 富时A50指数期货分时（当日）
westock minute fuCN --days 5                   # 五日分时
westock minute r_hdHSImain                     # 恒指期货分时
westock kline fuGC --period day --limit 30     # 黄金日K（含 OHLC/成交量/持仓量）
westock kline fuCN --period week --limit 20    # 周K（day/week/month/season/year）
westock kline r_hdHSImain --period day         # 恒指期货K线

```

> ⚠️ **期货限制**：外盘期货多为**延时行情**（输出 `isDelayed`）。`westock minute`/`westock kline` 仅支持带 `stockType` 的合约（`fu*` 外盘、`r_hd*` 港股股指）；`hf_*`（LME 金属/伦敦金银现货）**仅支持 `westock quote`**，不支持分时/K线。期货**不支持复权**（`--fq` 对期货无效）与 `westock news`。合约代码请先用 `westock search --type futures` 获取，避免猜测。

---

## 十六、外汇

> 离岸人民币、主要货币对、美元指数等即期现货汇率。
> 标准代码前缀：`fx*`（如 `fxCNH` 离岸人民币、`fxUSDJPY` 美元日元、`fxDINIW` 美元指数）。

### 品种搜索与列表

```bash
westock forex list                            # 列出全部外汇品种（代码/名称）
westock search 美元 --type forex              # 关键词→品种代码（匹配 名称/代码/裸代码）
westock search 离岸 --type forex              # 离岸人民币 → fxCNH
westock search 日元 --type forex              # 含日元的货币对（fxUSDJPY/fxEURJPY 等）

```

### 外汇行情/K线/分时（复用 quote / kline / minute）

```bash
westock quote fxUSDJPY                         # 美元日元即期汇率
westock quote fxCNH,fxEURUSD,fxDINIW           # 批量（离岸人民币/欧元美元/美元指数）
westock kline fxCNH --period day --limit 30    # 离岸人民币日K（day/week/month/season/year）
westock minute fxCNH                           # 离岸人民币当日分时

```

> ⚠️ **外汇限制**：外汇**仅提供当日分时**，`westock minute` 的 `--days 5` 对外汇无效（数据源不支持五日分时，参数会被忽略并返回当日数据）。外汇**不支持复权**（`--fq` 对外汇无效）与 `westock news`。品种代码请先用 `westock search --type forex` 或 `westock forex list` 获取，避免猜测。

## 十七、债券（可转债 / 可交换债）

> 沪深可转债/可交换债。标准代码：沪市 `sh11xxxx`（110/111/113 可转债、118 科创板可转债）、`sh13xxxx`（132 可交换债）；深市 `sz12xxxx`（123/127/128 可转债、120 可交换债）。
> 行情/分时/K线沿用 sh/sz 前缀，直接复用个股通道，无需特殊命令。

### 可转债行情/分时/K线（复用 quote / minute / kline）

```bash
westock quote sh113052                         # 可转债行情（价格/涨跌/涨跌停价 + 转债维度，竖排展示）
westock quote sh113052,sh113044                # 批量
westock minute sh113052                        # 当日分时
westock kline sh113052 --period day --limit 30 # 可转债K线（日/周/月/季/年及分钟K均支持）

```

> 可转债行情在通用价格/成交字段之外，额外返回**转债维度**：转股价值、纯债价值、转股/纯债溢价率、双低、总规模/剩余规模、评级、期限/剩余期限/到期日、到期收益率、是否转股、转股价/转股起始日、到期赎回价/强赎价/强赎触发价、回售触发价/回售起始日、正股 PB/正股代码。单只查询时以竖排「项目/内容」表展示，规模换算为亿元、日期规整为 `YYYY-MM-DD`。

### 可转债详情（bond）

```bash
westock bond sh113052                   # 核心要素：发行/规模/评级/期限利率/转股/赎回回售/关键日期/利率变动/现金流明细
westock bond sh113052,sz123245          # 批量查询

```

> ⚠️ **可转债说明**：行情接口**不返回债券简称**（`westock quote` 的 `name` 为空），可借 `bond` 的发行人/正股代码识别标的。可交换债及临近到期的老券可能缺失部分转股相关（`Kzz_*`）字段。规模金额已统一换算为「亿元」，日期已规整为 `YYYY-MM-DD`。

---

## 十八、产业链

> 产业链主题/图谱/股票所属产业链查询。覆盖产业链上下游分布、相关股票、关联度分析。

### 产业链主题列表

```bash
westock industry-chain list                          # 列出所有产业链主题
westock industry-chain                              # 无参数 = list

```

> 返回产业链主题清单（主题代码、主题名称、主题类型）。

### 产业链图谱

```bash
westock industry-chain graph 超级电容                   # 查询产业链图谱（含上/中/下游节点与关联个股）
westock industry-chain graph 白酒
westock industry-chain graph 集成电路
westock industry-chain graph 超级电容 --category upstream    # 只看上游

```

> **参数说明**：
> - `graph <主题名称>`：必填，产业链主题名称
> - `--category`：可选，按产业链位置过滤（`upstream`=上游 / `midstream`=中游 / `downstream`=下游）
>
> **输出内容**：
> - 上游/中游/下游分类节点
> - 每个节点包含节点名称和相关股票
> - 股票代码和名称映射

### 股票所属产业链

```bash
westock industry-chain stock sh600519                       # 查询股票所属产业链（简洁风格）
westock industry-chain stock sz000001                       # 平安银行

```

> **输出内容**：
> - 所属产业链主题列表（主题名称、主题类型）
> - 所属节点列表（节点名称、产业链位置、关联度、业务描述）
>
> **关联度**：数值类型，表示股票与节点的关联程度（1-10）
> **业务描述**：说明股票与该节点的业务关联关系
