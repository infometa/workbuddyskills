# WeStock Data - 常见分析场景详解

> **定位**：本文档是 SKILL.md 的 **L3 层补充材料**，提供完整的分析场景示例和详细操作步骤。
>
> **使用方式**：AI 在遇到不确定的分析场景时按需加载本文档。命令列表和基本用法请参见
> [SKILL.md](../SKILL.md)。
>
> **场景总数**：共 74 个场景，按 18 个功能分组组织。

---

## 一、行情（价格序列）

> 命令：`westock quote` `westock minute` `westock kline`

### 1.1 分析成交量趋势

```
用户："分析牧原股份近20天的成交量"
→ westock search 牧原股份 → westock kline sz002714 --period day --limit 20 → 从表格中提取volume → 计算统计指标 → 输出分析报告
```

### 1.2 多股对比（使用批量查询）

```
用户："对比贵州茅台和格力电器近半年走势、财务、资金面"
→ 一次批量（各 1 条；不要 kline/technical 按股拆开）：
   westock quote sh600519,sz000651
   westock kline sh600519,sz000651 --period day --limit 120
   westock technical sh600519,sz000651
   westock finance sh600519,sz000651 --limit 4
   westock fund flow sh600519,sz000651
   westock news list sh600519,sz000651 --limit 5
   westock fund north-holding sh600519,sz000651
→ 所属产业链（仅单股，可并行）：
   westock industry-chain stock sh600519
   westock industry-chain stock sz000651
```

```
用户："对比腾讯和阿里巴巴的市值"
→ westock quote hk00700,usBABA → 一次查询两只股票 → 解析批量查询结果 → 提取市值 → 输出对比
```

### 1.3 指数/板块K线分析

```
用户："上证指数近一个月的走势"
→ westock kline sh000001 --period day --limit 30 → 解析K线 → 输出趋势分析
（走势看趋势用 kline；某天/区间涨跌幅直接用 `westock quote --date` 读 changePercent）

用户："半导体板块近一周的K线走势"
→ westock search 半导体 --type sector → 获取板块代码（如 pt01801081）
→ westock kline pt01801081 --period day --limit 5 → 解析K线 → 输出走势

用户："茅台 2025 年全年的日K"（按日期范围）
→ westock kline sh600519 --start 2025-01-01 --end 2025-12-31 → 解析K线 → 输出年度走势

用户："茅台/英伟达去年全年涨了多少？"（区间收益）
→ westock quote sh600519 --date 2024-12-31  # 取上年末收盘价（基准）
→ westock quote sh600519 --date 2025-12-31  # 取当年末收盘价
→ 年度涨幅 = (年末last - 上年末last) / 上年末last × 100%
（基准取上年末收盘价）
（提示：--start/--end 优先级高于 --limit；仅指定 --start 时 end 默认今天）
```

### 1.4 指数/板块分时走势

```
用户："大盘今天的分时走势怎么样"
→ westock minute sh000001 → 解析分时数据 → 输出走势分析

用户："半导体板块今天的盘中走势"
→ westock search 半导体 --type sector → 获取板块代码（如 pt01801081）
→ westock minute pt01801081 → 解析分时 → 输出走势
```

#### 1.4.1 查"某日某时"的股价

`minute` 用于查看近几日盘中分时走势（--days 1~5）。要查"昨天 10:00""上周三 14:30"这种**具体某日某时**的股价，用 `kline --period m1` + `--start/--end` 精准定位到单日：

```
用户："招行昨天上午 10:00 的股价是多少？"
→ westock kline sh600036 --period m1 --start 2026-07-07 --end 2026-07-07
→ 单日返回 ~240 行 1 分钟 K 线（含 time 列），直接定位 time=10:00 行的 price
```

> 适用范围：分钟 K 线 `m1/m5/m15/m30/m60/m120` 支持除**美股指数**外的所有标的（美股指数仅支持日K，带分钟周期返回 `KLINE_002`），且必须在**近 1 个月内**、强制不复权。美股指数的"某日某时"需求走 `quote --date`。

## 二、技术分析（衍生指标/筹码）

> 命令：`westock technical` `westock chip`

### 2.1 筹码成本分析

```
用户："分析一下茅台的筹码分布情况"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询筹码数据：westock chip sh600519
3. 解析筹码盈利率（chipProfitRate）→ 判断获利盘/套牢盘比例
4. 对比收盘价与平均成本（chipAvgCost）→ 判断当前价位相对筹码成本的位置
5. 分析集中度（chipConcentration90/70）→ 集中度越低，筹码越集中
6. 输出筹码分析结论
```

### 2.2 筹码趋势分析

```
用户："看看招商银行近一个月的筹码变化趋势"

AI 步骤：
1. 搜索股票：westock search 招商银行 → sh600036
2. 查询历史筹码：westock chip sh600036 --start 2026-02-10 --end 2026-03-10
3. 解析 items[] 中每日的筹码数据
4. 分析趋势：
   - 盈利率趋势（上升 = 获利盘增加）
   - 平均成本趋势（上升 = 筹码成本抬升，主力可能在建仓）
   - 集中度趋势（下降 = 筹码趋于集中，可能有主力控盘）
5. 输出筹码变化趋势分析
```

### 2.3 技术指标多周期分析

`westock technical` 支持**日K/周K/月K/季K/年K/分钟K**等周期技术指标；AI 做趋势分析时可同时拉多周期对比（美股指数仅支持日K，非日周期返回 `TECHNICAL_002`）：

```
用户："分析茅台的中长期技术面"
→ westock technical sh600519 --period day               # 日K最新
→ westock technical sh600519 --period week              # 周K技术指标
→ westock technical sh600519 --period month --limit 12  # 月K近12期
→ 对比日线/周线/月线 MACD、KDJ 状态 → 给出多周期共振判断
```

```
用户："茅台 30 分钟级别最近有什么买卖信号？"
→ westock technical sh600519 --period m30 --start 2026-07-09 --end 2026-07-10
→ 返回 30 分钟 K 线的 MA/MACD/KDJ/RSI/BOLL（分钟K需指定 --start/--end，近1个月内，强制不复权）
```

```
用户："想查看技术指标（MA/MACD/KDJ/RSI/BOLL 等）"
→ westock technical sh600519
```

---

## 三、市场（全市场截面/总览/互联互通/新股）

> 命令：`westock lhb` `westock market-overview` `westock connect` `westock ipo`

### 3.1 查询股票基本信息

```
用户："查询腾讯控股的股价"
→ westock search 腾讯控股 → 获取 hk00700 → westock quote hk00700 → 展示价格和涨跌幅
```

### 3.2 新股申购分析

```
用户："最近有什么新股可以申购？"

AI 步骤：
1. 查询沪深新股：westock ipo --market hs
   → 格式化输出按状态分类（即将发行/今日可申购/即将上市/中签号公布/已上市），含发行价、市盈率、申购代码、上市日、可比公司、风险提示等
2. 可选：查询港股新股：westock ipo --market hk
   → 格式化输出按申购日/上市日分类，含入场费、认购倍数、募集金额等
3. 可选：查询美股新股：westock ipo --market us
   → 格式化输出按状态分组（注册中/已定价/已提交等），含行业、发行价、价格区间、承销商等
4. 直接基于格式化输出，输出新股申购机会分析
```

### 3.3 今日市场点评（market-overview summary）

```
用户："今天 A 股市场怎么样？"

AI 步骤：
1. 一键拉取大盘画像：westock market-overview （默认 type=summary）
2. 解析 14 维度得分（估值/情绪/技术/趋势/风格轮动 等）+ 状态文案
3. 综合给出今日市场点评，标注偏强/偏弱维度
4. 如需补充，叠加 --type updown（涨跌停/红绿盘）/ --type margin（两融）/ --type valuation（中证全指 PE 百分位）
```

### 3.4 沪深港通成份股查询（connect）

```
用户："沪股通有哪些标的"

AI 步骤：
1. 拉沪股通成份股：westock connect --exchange sh
2. 分页拉全量：westock connect --exchange sh --limit 100 --offset 0
3. 拉深股通：westock connect --exchange sz
4. 输出标的池（注意：connect 是"标的池"列表，不是资金流量；查北向日度资金流量请用 `westock fund flow sh600000`；查北向季度持仓请用 `westock fund north-holding sh600519`；查申万行业北向分布请用 `westock fund north-holding <板块代码>`）
```

> **职责边界**：`westock connect` = 沪深港通**标的池**（标的列表）；`westock fund flow` = 日度资金流量；`westock fund north-holding` = 北向季度持仓（个股或申万行业）。按需求选择对应命令。

---

## 四、指数（清单/搜索/成份股/行情对比）

> 命令：`westock index list/constituent` + `westock search --type index`；指数行情用 `westock quote` / `westock search --type index`

### 4.1 指数行情查询

```
用户："查一下今天大盘的涨跌情况"
→ westock search 上证指数 → 获取 sh000001 → westock quote sh000001 → 展示涨跌幅和成交额
```

### 4.2 多指数对比

```
用户："对比沪深两市今天的表现"
→ westock quote sh000001,sz399001 → 解析批量查询结果 → 对比涨跌幅 → 输出分析
```

### 4.3 跨市场指数对比

```
用户："对比恒生指数和纳斯达克今天的表现"

AI 步骤：
1. 批量查询行情：westock quote hkHSI,us.IXIC
2. 分别解析各指数的行情数据
3. 对比涨跌幅
4. 输出跨市场指数对比分析
```

### 4.4 查询指数成份股

```
用户："沪深300有哪些成份股？"

AI 步骤：
1. 查询沪深300成份股：westock index constituent sh000300
2. 解析返回的成份股列表
3. 输出成份股列表
4. 可按行业分布统计
```

---

## 五、板块（搜索/成份股/信息/行情榜/经营/估值/预测/财务）

> 命令：`westock search --type sector` / `westock sector constituent/info/ranking/oper/valuation/forecast/finance`

### 5.1 板块行情分析

```
用户："半导体板块今天的涨跌情况"
→ westock search 半导体 --type sector → 获取板块代码（如 pt01801081） → westock quote pt01801081 → 展示涨跌幅和成交额
```

### 5.2 查询概念股列表

```
用户："华为概念有哪些股票？"
用户："AI概念股有哪些？"
用户："新能源汽车概念股"

用 `westock search <关键词> --type sector` 两步查询：

AI 步骤：
1. 搜索概念板块代码：westock search 华为 --type sector
   → 返回匹配的板块列表（如 style_pt01801517 华为概念）
2. 用板块代码查成份股：westock sector constituent style_pt01801517
   → 返回华为概念的全部成份股列表
3. 输出概念股列表（代码、名称）
4. 可选：批量查询行情 westock quote <代码列表> → 补充行情数据
```

> **关键区分**：
> - `westock search 华为 --type sector` → 拿到板块代码后，用 `westock quote`/`westock kline`/`westock minute` 查板块行情
> - `westock search 华为 --type sector` → 再用 `westock sector constituent <代码>` 查成份股

### 5.3 查询行业成份股

```
用户："电子行业有哪些成份股？"

AI 步骤：
1. 查询申万一级电子行业成份股：westock sector constituent pt01801080
2. 解析返回的成份股列表
3. 输出成份股列表（代码、名称）
4. 可补充成份股数量统计
```

### 5.4 板块成份 + 行情联动分析

```
用户："帮我看看半导体板块的成份股，并查看涨幅前5的行情"

AI 步骤：
1. 查询申万二级半导体成份股：westock sector constituent pt01801081
2. 取返回的成份股代码列表
3. 批量查询行情：westock quote <前N只代码逗号分隔>
4. 按涨跌幅排序取前5
5. 输出板块成份 + 涨幅排行分析
```

### 5.5 板块成份股查询

```
用户："半导体板块有哪些成份股"

AI 步骤：
1. 搜索板块代码 → pt01801081
2. 拉取成份股：westock sector constituent pt01801081
3. 输出成份股清单（含代码/名称/涨跌/成交额等）
```

> 命令区别：`westock sector constituent <代码>` 查成份股；`westock sector valuation/forecast/finance <代码>` 查估值/盈利预测/财务；`westock sector info <代码>` 查板块概况。

### 5.6 申万行业基本面三连

```
用户："银行行业现在估值怎么样？盈利前景如何？"
用户："帮我分析一下半导体行业的基本面：财报、估值和一致预期"
用户："电子和银行哪个行业估值更低、盈利增速更好？"

行业基本面按 finance（已披露）→ valuation（贵不贵）→ forecast（未来预期）三段分析。概念/地域板块 `sector finance/valuation/forecast` 仅申万 sw1/sw2/sw3 支持，需先用 `westock search <关键词> --type sector` 取对应申万行业 pt 代码。

AI 步骤：
1. 若用户未给代码：westock search 银行 --type sector
   → 取申万行业 pt 代码（如 pt01801780 银行一级）
2. 同一轮并行查询三条（深研单行业）：
   westock sector finance pt01801780
   westock sector valuation pt01801780
   westock sector forecast pt01801780
3. 解读链条：
   - finance：`revenueTTM` / `netProfitTTM` / `roeTTM` / `debtRatio` → 当下盈利与杠杆
   - valuation：`PeTTM` + `PeTTMPct` 等百分位 → 相对历史贵不贵
   - forecast：未来 3 年 `netProfitYoy` / `pe` / `peg` → 机构一致预期增速与估值
4. 可选历史区间：westock sector finance pt01801780 --start 2020-01-01 --end 2026-03-31
   或 westock sector valuation pt01801780 --start 2026-01-01 --end 2026-06-25
5. 多行业对比：截面命令支持逗号批量
   westock sector valuation pt01801780,pt01801080
   westock sector forecast pt01801780,pt01801080
   westock sector finance pt01801780,pt01801080
6. 输出：基本面→估值→预期三段分析，指出增速与估值是否匹配

> **职责边界**：`westock sector oper` = 行业经营指标（产量/库存等，传行业中文名）；`westock sector finance/valuation/forecast` = 申万行业财报/估值/一致预期（传 pt 代码）。
```

---

## 六、研究（评分/评级/预期/研报）

> 命令：`westock score` `westock rating` `westock consensus` `westock report`

### 6.1 机构评级与一致预期分析

```
用户："看看茅台的机构评级和一致预期"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询评级数据：westock rating sh600519
   → 解析机构评级分布（买入/增持/中性/减持/卖出）
3. 查询一致预期：westock consensus sh600519
   → 解析 EPS/净利润/营收的一致预期值和增长率
4. 查询评分：westock score sh600519
   → 解析综合评分、细分维度评分
5. 输出机构研究综合报告
```

### 6.2 研报查询

```
用户："看看最近有哪些关于茅台的研报"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询研报列表：westock report list sh600519 --limit 10
   → 解析研报标题、机构、分析师、评级、发布时间
3. 输出研报摘要和核心观点
```

---

## 七、事件（事件标签/风险事件/投资日历/停复牌）

> 命令：`westock events` `westock risk` `westock calendar` `westock suspension`

### 7.1 投资日历查询（个股事件日历）

```
用户："本周有哪些个股事件？" / "今天有哪些股票分红/发财报？"

AI 步骤：
1. 查询指定日期的个股事件：westock calendar --date 2026-03-10
   → 按事件类型分组输出（财报发布/分红派息/新股发行/停复牌/会议/限售解禁/增发）
2. 默认查当天，可按 --date 指定日期，--market 指定市场（hs/hk/us）
3. 按事件类型筛选：westock calendar --date 2026-03-10 --event dividend --market hs
   → --event 取值：financial_report/dividend/ipo/trading_halt/meeting/lockup_release/rights_issue/all
4. 多类型用逗号分隔：westock calendar --date 2026-03-10 --event dividend,financial_report
5. 若需查本周，逐天查询周一至周五各天数据，汇总输出
6. 宏观经济日历请使用 westock macro indicator cn_calendar_future|cn_calendar_hist
```

> `westock calendar` 是个股事件日历（查某天哪些股票有分红/财报/IPO等事件）。宏观经济日历用 `westock macro indicator cn_calendar_future|cn_calendar_hist`。
> 与 `westock suspension` 的区别：`suspension` 返回当前全市场停复牌列表，`calendar --event trading_halt` 只返回指定日期有停复牌事件的股票。

### 7.2 个股事件总览（events）

```
用户："最近茅台有什么大事"

AI 步骤：
1. 拉事件标签：westock events sh600519
2. 解析返回的事件 ID 列表（如 7=分红实施 / 23=董监高变动 / 12=限售解禁 等）
3. 按事件分类分组展示（董监高/分红/财报/指数变动/限售解禁等 9 大类）
4. 如需深挖某类，再用 risk 钻取（如 --types pledge 看质押细节）
```

### 7.3 事件 → 风险细查链路（events + risk）

```
用户："看看 sh600519 有没有质押风险"

AI 步骤：
1. 先看事件全貌：westock events sh600519
2. 若含质押/解禁标签，用 risk 钻取明细：
   westock risk sh600519 --types pledge,unlock
3. 解析质押率（已修复 100 倍单位错误）/ 解禁规模 / 解禁日期
4. 输出风险细节
```

### 7.4 高管变动 / 增减持 / 评级变动监控（risk 新类型）

```
用户："最近哪些高管在减持茅台"

AI 步骤：
1. 拉取高管增减持明细：westock risk sh600519 --types executivetransfer
   （别名 executive 也可：--types executive）
2. 解析每条增减持记录：高管姓名、变动数量、变动方向、变动后持股
3. 输出增减持汇总
```

```
其他新增 risk 类型：
- westock risk <code> --types leaderchange     # 高管变动（任免）
- westock risk <code> --types bondrating       # 评级信息（如 AAA/AA+）
```

---

## 八、资讯（新闻、公告、原文）

> 命令：`westock news list/detail` `westock notice list/detail`

### 8.1 公告全文查询

```
用户："查看贵州茅台最近的财务公告内容"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询公告列表：westock notice list sh600519 --type 1
3. 从列表中获取公告ID（如 nos1224809143）
4. 查询公告内容：westock notice detail nos1224809143
   → 格式化输出标题、发布时间、关联股票、相关链接（PDF/原文/翻译），A股/北交所直接展示正文内容，港股/美股展示PDF下载链接
5. 直接基于格式化输出，输出公告内容摘要
```

### 8.2 新闻与资讯查询

```
用户："看看最近有哪些关于茅台的新闻"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询新闻列表：westock news list sh600519 --limit 20
   → 解析新闻标题、来源、发布时间、摘要
3. 可选：查询市场资讯：`westock news list sh000001,sz399001,sz399006 --limit 20`（沪深指数）
   → 解析市场要闻、政策动向
4. 可选：查询新闻详情：westock news detail <newsId>
5. 输出新闻摘要和关键信息
```

---

## 九、资金（二级市场资金）

> 命令：`westock fund flow` / `westock fund short` / `westock fund margin` / `westock fund block` / `westock fund north-holding`

### 9.1 批量资金流向分析

```
用户："对比腾讯和美团的资金流向"
→ westock fund flow hk00700,hk03690 --date 2026-03-10 → 一次查询两只 → 解析批量查询结果 → 对比资金面
```

### 9.2 A股资金流向分析

```
用户："分析中芯国际的资金面"
→ westock fund flow sh688981 → 解析 MainNetFlow/JumboNetFlow → 输出资金面判断
```

### 9.3 港股资金与卖空分析

```
用户："腾讯控股的资金流向情况"
→ westock fund flow hk00700 → 解析 TotalNetFlow/MainNetFlow/RetailNetFlow → 输出资金分析

用户："腾讯控股的卖空情况如何"
→ westock fund short hk00700 → 解析 ShortShares/ShortAmount/ShortRatio → 卖空比率>15%需关注
```

### 9.4 美股卖空数据分析

```
用户："苹果公司的卖空情况"
→ westock fund short usAAPL → 解析 ShortRatio/ShortShares/ShortRecoverDays → ShortRatio>10%或ShortRecoverDays>5天需关注
```

### 9.5 北向资金持仓查询

```
用户："贵州茅台北向资金持仓情况怎么样？"
→ westock fund north-holding sh600519
→ 解析最新季 + 次新季：HoldingCap/HoldingRatio/HoldingShares/CapChgQ/CapChgY
→ 输出季度对比表（持股市值、持股比例、季年变动）

用户："电子行业北向资金持仓分布如何？"
→ 若用户未给代码：westock search 电子 --type sector → 取板块代码
→ westock fund north-holding pt01801080
→ 解析 HoldingCap/CapChgQ/CapChgY
→ 注意：仅支持申万行业，概念/地域板块不支持

用户："今天北向成交最活跃的股票有哪些？"
→ 不在本 Skill：改用 westock screen ranking --type north_active_d（固定 Top20 日榜）
```

---

## 十、简况（公司基本信息/股东/分红/回购）

> 命令：`westock profile` `westock shareholder` `westock dividend/calendar` `westock buyback`

### 10.1 分红数据查询

```
用户："贵州茅台的分红情况如何？"
→ westock search 贵州茅台 → 获取 sh600519
→ westock dividend sh600519 → 解析分红明细（reportEndDate, dividendPlan, cashDiviRMB 等）
→ 输出分红情况分析
```

### 10.2 跨市场分红历史对比

```
用户："对比腾讯和苹果近3年的分红记录"
→ westock dividend hk00700,usAAPL --years 3
→ 解析批量查询结果 中各股票的 plans[]
→ 注意货币差异：港股 cashDivPerShare（港元）、美股 dividend（美元）
→ 输出跨市场分红对比分析
```

### 10.3 A股分红历史查询

```
用户："查看贵州茅台近5年的分红记录"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询分红历史：westock dividend sh600519 --years 5
3. 解析 plans[] 中的分红方案（reportEndDate, cashDiviRMB, dividendPlan）
4. 注意：A股分红数据为"每10股派息"（cashDiviRMB）
5. 分析每年分红趋势（分红金额、分红频次、股利支付率变化）
6. 输出分红历史趋势分析
```

### 10.4 港股分红历史查询

```
用户："查看腾讯近几年的分红记录"

AI 步骤：
1. 查询分红历史：westock dividend hk00700 --years 5
2. 解析 plans[] 中的分红方案
3. 分析每年分红趋势（每股派息、合计派现、分红频次）
4. 输出分红历史趋势分析
```

### 10.5 分红历史自定义年数

```
用户："查看苹果近10年的分红记录"

AI 步骤：
1. 查询分红历史：westock dividend usAAPL --years 10
2. 解析 plans[] 中的分红方案
3. 分析美股季度分红特征（每季度分红金额、年度累计）
4. 注意：美股可能包含 splitInfo（拆合股信息）
5. 输出长期分红趋势分析
```

### 10.6 跨市场分红历史对比

```
用户："对比贵州茅台、腾讯和苹果近3年的分红情况"

AI 步骤：
1. 批量查询分红历史：westock dividend sh600519,hk00700,usAAPL --years 3
2. 解析批量查询结果 中各股票的 plans[]
3. 注意各市场数据格式差异：
   - A股：cashDiviRMB（每10股派息，元）
   - 港股：cashDivPerShare（每股派息，港元）
   - 美股：dividend（每股分红，美元）
4. 统一换算为每股派息金额进行对比
5. 输出跨市场分红对比分析
```

### 10.7 分红除权日查询

```
用户："苹果什么时候除权派息？"

AI 步骤：
1. 搜索股票：westock search 苹果 → usAAPL
2. 查询分红历史：westock dividend usAAPL --years 5
3. 解析 plans[] 中的除权日列表
4. 展示每次的除权日、支付日、每股分红
5. 输出分红除权日历
```

### 10.8 股东研究分析

```
用户："查一下茅台的十大股东"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询股东数据：westock shareholder sh600519
3. 解析 top10Shareholders（十大股东）和 top10FloatShareholders（十大流通股东）
4. 解析 shareholderNum（股东户数）→ 总户数/A股户数/环比变动/户均持股
5. 分析持股集中度、机构/个人占比、持股变动趋势
6. 输出股东结构分析报告
```

### 10.9 港股股东与机构持仓分析

```
用户："腾讯的机构持仓情况怎么样？"

AI 步骤：
1. 查询股东数据：westock shareholder hk00700
2. 解析 shareholderInfo（持股股东）→ 主要股东持股比例
3. 解析 shareholderDist（股东分布）→ 各类机构持股情况
4. 解析 instHoldingStats（机构持仓统计）→ 机构数量变化、增减持趋势
5. 输出机构持仓分析
```

### 10.10 公司回购查询

```
用户："查看小米最近的回购情况"

AI 步骤：
1. 搜索股票：westock search 小米集团 → hk01810
2. 查询回购数据：westock buyback hk01810
3. 解析回购明细：日期、回购股份、回购金额、回购均价
4. 计算累计回购金额、平均回购价格
5. 输出回购分析
```

---

## 十一、财务（三大报表/财报披露日历）

> 命令：`westock finance` `westock disclosure`

### finance 能力速查

- `westock finance <代码>` / `westock finance <代码1>,<代码2>`：默认三大报表（`income` + `balance` + `cashflow`），支持 `--limit` 或 `--start` / `--end`
- `westock finance <代码> --type income|balance|cashflow`：仅拉指定单表

### 使用原则（★ 必读）

> **按用户意图选择 --type 单表**，只在用户明确要求跨表综合分析时才用默认 all。

| 用户意图 | 应查表 | 命令 |
|---------|-------|------|
| 营收/利润/ROE/毛利率/增长率 | **income** | `westock finance <代码> --type income` |
| 资产/负债/偿债能力/ROA | **balance** | `westock finance <代码> --type balance` |
| 经营/投资/筹资现金流 | **cashflow** | `westock finance <代码> --type cashflow` |
| "综合分析""全面财报" | 三大表 all | `westock finance <代码>`（默认） |

常用中文指标 → 英文字段映射：营业收入 = `TotalOperatingRevenue` / `OperatingRevenue`（income 表），归母净利润 = `NPParentCompanyOwners`（income 表），总资产 = `TotalAssets`（balance 表），经营现金流净额 = `NetOperateCashFlow`（cashflow 表）。

**只在用户明确要求跨表综合分析时才用默认 all 模式。**

### 11.1 财务分析

```
用户："分析贵州茅台的盈利能力"
→ westock finance sh600519 --type income --limit 4 → 提取关键指标 → 计算同比/环比 → 输出分析结论

用户："招商银行营业收入是多少"
→ westock finance sh600036 --type income --limit 1
→ 直接读取 TotalOperatingRevenue / OperatingRevenue 列
```

### 11.2 多股财报对比（三大表）

```
用户："对比小米和腾讯的财报"
→ westock finance hk01810,hk00700 --limit 1
→ 解析批量三大表 → 输出对比分析
```

### 11.3 单表多期对比

```
用户："看看浦发银行和招商银行最近4期的利润表"
→ westock finance sh600000,sh600036 --type income --limit 4
→ 解析批量查询结果 → 提取各期营收、净利润、毛利率
→ 计算同比/环比增长率 → 输出两家银行盈利能力对比

用户："查看腾讯最近4期的综合损益表"
→ westock finance hk00700 --type income --limit 4
```

### 11.4 财报披露日查询

```
用户："茅台什么时候发财报？"

AI 步骤：
1. 搜索股票：westock search 贵州茅台 → sh600519
2. 查询财报披露日历：westock disclosure sh600519
3. 解析 items[] 中的披露日列表
4. 区分已披露和预约披露日期
5. 输出最近的财报披露日历
```

---

## 十二、ETF（ETF 全维度）

> 命令：`westock etf profile` / `overview` / `holdings` / `nav`

### 12.1 ETF 全景分析

```
用户："分析一下沪深300ETF的基本情况"

AI 步骤：
1. 搜索 ETF：westock search 沪深300ETF --type etf → sh510300
2. 查询基金档案：westock etf profile sh510300
3. 查询运作概览：westock etf overview sh510300
4. 解析基本信息：类别、成立日期、管理人、托管人、跟踪指数
5. 解析 classification（4 级详细分类）：资产类别 / 投资风格 / 细分领域 / 具体方向 / 跟踪标的
6. 解析 managerHistory（基金经理历史）：当前在任 / 首任 / 任职最长 / 全部历任
7. 解析费用：认购费率、管理费率、托管费率、销售服务费
8. 解析净值/规模：单位净值、溢折率、规模、份额、净申购
9. 解析收益：今年以来、近1月/3月/6月/1年/3年收益率
10. 解析回撤：最大回撤指标
11. 输出 ETF 全景分析报告
```

### 12.2 ETF 持仓分析

```
用户："沪深300ETF的重仓股有哪些？"

AI 步骤：
1. 搜索 ETF：westock search 沪深300ETF --type etf → sh510300（确认 etfDetail=支持）
2. 查询成分股：westock etf holdings sh510300
3. 解析 topStockChanges（重仓股涨跌）与 holdings（申赎清单全量成分）
4. 仅需成分股列表时可用：westock etf holdings sh510300
5. 输出 ETF 持仓分析
```

### 12.3 ETF 净值趋势分析

```
用户："沪深300ETF近一个月净值走势如何？"

AI 步骤：
1. 搜索 ETF：westock search 沪深300ETF --type etf → sh510300
2. 查询净值历史：westock etf nav sh510300 --start 2026-02-10 --end 2026-03-10
3. 解析每日净值、净值涨跌（`navChange`/`navChangePct` 由相邻日 `EtfNav` 差分；区间内首日无前值）
4. 计算区间收益率、最大回撤
5. 输出净值趋势分析
```

### 12.4 ETF 费用对比

```
用户："对比沪深300ETF和创业板ETF的费用"

AI 步骤：
1. 搜索 ETF：westock search 沪深300ETF --type etf → sh510300
2. 搜索 ETF：westock search 创业板ETF --type etf → sz159915
3. 批量查询档案：westock etf profile sh510300,sz159915
4. 对比费用：认购费率、管理费率、托管费率、销售服务费
5. 对比规模、份额、流动性（etf overview）
6. 输出 ETF 费用对比分析
```

### 12.5 ETF 溢折率分析

```
用户："分析一下沪深300ETF的溢折率情况"

AI 步骤：
1. 查询运作概览：westock etf overview sh510300
2. 解析 etfDisc（溢折率）、etfDiscAvg*（同指数平均溢折率）
3. 判断溢价/折价程度及与同类 ETF 的对比
4. 输出溢折率分析
```

### 12.6 ETF 基金经理稳定性分析

```
用户："沪深300ETF的基金经理稳定吗？历任都有谁？"

AI 步骤：
1. 查询基金档案：westock etf profile sh510300
2. 解析 managerHistory：
   - current（当前在任）：与 first（首任）一致 → 经理"超长稳定"
   - longest（任职最长）数组里的人是否仍在 current 内 → 老将仍在岗
   - history（全部历任）数量 → 历任更换次数（少 = 稳定，多 = 频繁更换）
3. 结合 managers 数组（含 intro / experienceYears / returnDuringTenure）补充任职履历和任内回报
4. 输出经理稳定性结论（如"自成立以来仅 1 任经理，柳军任职超 12 年"）
```

---

## 十三、发现（搜索/热搜）

> 命令：`westock search` `westock hot stock/news/board/etf`

### 13.1 查看市场热搜

```
用户："今天市场有哪些热门股票？"

AI 步骤：
1. 查询热搜股票：westock hot stock
   → 格式化输出排名、名称、代码、最新价、涨跌幅
2. 可选：查询热门板块：westock hot sector
3. 可选：查询热搜ETF：westock hot etf
4. 可选：查询热文排名：westock hot news --limit 20
5. 直接基于格式化输出，综合输出市场热点概览
```

### 13.2 行业板块分析

```
用户："今天哪些行业板块涨得好？资金在流向哪里？"

AI 步骤：
1. 查询板块行情榜：westock sector ranking
   → 输出行业/概念板块排行（默认涨幅降序；--type 可切换主力净流入等字段、--order asc 升序）
2. 直接基于格式化输出，输出行业板块资金面和涨幅分析
```

---

## 十四、宏观（宏观指标）

> 命令：`westock macro list/indicator`

### 14.1 查看最新核心宏观指标

```
用户："当前宏观经济面怎么样？"

AI 步骤：
1. 查询最新核心宏观指标：westock macro indicator cn_core
2. 解析返回的各项核心指标数据（会自动返回 p1 和 p2 两个数据集）
3. 从 GDP 增速、CPI/PPI、PMI、社融、M2 等维度综合分析
4. 输出宏观经济面全景概览
```

### 14.2 PMI 趋势分析

```
用户："看看最近半年PMI走势"

AI 步骤：
1. 查询 PMI 区间数据：westock macro indicator cn_pmi --start 2024 --end 2025
2. 提取每月 PMI 数值（制造业/非制造业/综合）
3. 分析 PMI 是否连续处于荣枯线（50）以上
4. 结合子项（新订单、生产、就业等）分析经济景气度变化
5. 输出 PMI 趋势分析报告
```

### 14.3 GDP 全景分析

```
用户："分析一下最新的GDP数据"

AI 步骤：
1. 查询全部 GDP 相关指标：westock macro indicator cn_gdp,cn_cpi_ppi,cn_consumption,cn_investment --year 2025
2. 解析 GDP 增速（实际 vs 名义）
3. 分析 CPI/PPI 价格走势（通胀/通缩信号）
4. 分析消费和投资数据（内需强弱）
5. 输出 GDP 多维度分析报告
```

### 14.4 货币政策环境判断

```
用户："当前货币政策环境如何？"

AI 步骤：
1. 查询货币指标：westock macro indicator cn_financing,cn_fundquantity,cn_fundcost --year 2025
2. 分析社融规模（financing）→ 实体经济融资需求
3. 分析 M1/M2 增速（fundquantity）→ 货币供应宽松度
4. 分析利率水平（fundcost）→ 资金成本变化
5. 综合判断货币政策取向（宽松/中性/偏紧）
6. 输出货币政策环境分析
```

### 14.5 宏观数据 + 市场联动分析

```
用户："PMI下滑对A股有什么影响？"

AI 步骤：
1. 查询 PMI 趋势：westock macro indicator cn_pmi --start 2024 --end 2025
2. 查询同期上证指数走势：westock quote sh000001
3. 对比 PMI 走势与指数走势的相关性
4. 分析 PMI 下行期间哪些板块受影响更大
5. 输出宏观-市场联动分析
```

### 14.6 通胀全景 + CPI/PPI 剪刀差

```
用户："最近通胀压力怎么样？"/"CPI和PPI差距说明什么？"

AI 步骤：
1. 查询价格指标：westock macro indicator cn_cpi_ppi --start 2024 --end 2025
2. 关注核心指标：
   - CPI_YOY（CPI 同比）vs CPI_YOY_CORE（核心 CPI，剔除食品和能源）
   - PPI_YOY（PPI 同比）、PPIRM_YOY（购进价格）
   - PRICE_SCISSORS_CPI_PPI（CPI-PPI 剪刀差）、PRICE_SCISSORS_PPI_PPIRM（PPI-PPIRM 剪刀差）
3. 专业研判：
   - CPI 上升 + 核心 CPI 平稳 → 食品/能源驱动型通胀（暂时性）
   - CPI > PPI（剪刀差为正）→ 下游议价能力强，消费类利润扩张
   - CPI < PPI（剪刀差为负）→ 上游成本压力，下游利润受挤压
   - PPI > PPIRM → 制造业利润率改善
4. 拆分分项：CPI_YOY_FOOD（食品）/ CPI_YOY_NON_FOOD（非食品）/ PPI_YOY_PRODUCE（生产资料）/ PPI_YOY_LIVE（生活资料）
5. 输出通胀压力评估 + 板块影响（消费/上游资源/中游制造）
```

### 14.7 国债收益率曲线与期限结构分析

```
用户："看看国债收益率曲线"/"长短端利差怎么样？"/"是牛陡还是熊平？"

AI 步骤：
1. 查询收益率曲线：westock macro indicator cn_yield_curve --year 2025
2. 查询期限利差与曲线形态：westock macro indicator cn_term_spread --date <最新>
3. 关注核心字段：
   - YTM_YIELD_2Y / 5Y / 10Y / 30Y（关键期限点位）
   - Yield10Y / Yield2Y、TermSpread（10Y-2Y 期限利差，bps）
   - CurveFormD/W/M/Q/Y（日/周/月/季/年形态：牛陡/牛平/熊陡/熊平）
   - LongDifD/W/M/Q/Y、ShortDifD/W/M/Q/Y（长短端多周期变动）
4. 形态语义：
   - **牛陡**（短端下行更快）→ 货币宽松预期、降息周期初期
   - **牛平**（长端下行更快）→ 经济衰退预期、避险买长债
   - **熊陡**（长端上行更快）→ 经济复苏 / 通胀预期上升
   - **熊平**（短端上行更快）→ 流动性收紧、加息周期
5. 期限利差判断：
   - 利差扩大（陡峭化）→ 经济预期改善
   - 利差收窄甚至倒挂 → 衰退信号（参考美债经验）
6. 输出曲线形态判断 + 货币政策含义 + 大类资产建议
```

### 14.8 股债性价比（风险溢价）与大类资产配置

```
用户："现在股票贵不贵？"/"股债怎么选？"/"红利股有性价比吗？"

AI 步骤：
1. 查询溢价率最新水平：westock macro indicator cn_premium_value --date <最新>
2. 查询溢价率历史曲线（约 2400 条日频）：westock macro indicator cn_premium_curve --date <最新>
3. 关注核心字段：
   - DividendPremium（红利溢价率：股息率 - 10Y 国债收益率）
   - EquityPremium（股债溢价率：1/PE - 10Y 国债收益率）
   - DprPct10Y / EprPct10Y（过去 10 年历史百分位）
4. 专业研判：
   - 股债溢价率 10Y 分位 > 80% → 股票相对债券极具吸引力（市场底部信号）
   - 股债溢价率 10Y 分位 < 20% → 股票相对债券偏贵（市场高估区）
   - 红利溢价率 10Y 分位 > 80% → 红利策略性价比高，适合配置高股息蓝筹
   - 红利溢价率持续走高 → 资金"避险"特征，关注银行/煤炭/电力/运营商
5. 历史曲线趋势：
   - 拐点识别：从历史高位回落 → 风险资产开始反攻
   - 持续走低 → 警惕股票泡沫，债券吸引力上升
6. 输出大类资产配置建议（股 vs 债 vs 红利）
```

### 14.9 流动性投放与货币市场利率

```
用户："央行最近在投放还是回笼？"/"MLF 利率怎么走？"

AI 步骤：
1. 查询公开市场操作 MLF：westock macro indicator cn_mlf --year 2025
2. 查询货币市场利率：westock macro indicator cn_fundcost --year 2025
3. 关注核心字段：
   - MLF_OPERATION_3M / 6M / 1Y（不同期限操作金额）
   - MLF_BALANCE_MONTH（月末余额）、MLF_DUE（到期量）、MLF_NET_INJECTION（净投放）
   - SHIBOR_OVERNIGHT / 1W / 1M / 3M / 1Y（同业拆借利率）
   - FDR007 / FR007（银行间回购定盘利率）
4. 专业研判：
   - MLF 净投放为正 + 短端利率下行 → 流动性宽松
   - MLF 净回笼 + SHIBOR 上行 → 流动性边际收紧
   - MLF 操作以 1Y 为主 → 央行引导中长期利率下行
   - SHIBOR 1Y 与 MLF 利差走扩 → 银行负债成本压力
5. 政策信号：
   - MLF 续作量 > 到期量 → 呵护流动性
   - 1Y MLF 利率下调 → 引导 LPR 下调，传导至实体融资成本
6. 输出货币政策操作意图 + 流动性松紧度评估
```

---

## 十五、期货（外盘商品/金融期货 + 港股股指期货）

> 命令：`westock futures detail` + `westock search --type futures` + `westock quote`（支持期货代码）

### 15.1 期货行情查询（关键词→代码→行情）

```
用户："现在国际金价多少？"

AI 步骤：
1. 关键词找代码：westock search 黄金 --type futures → fuGC（COMEX黄金）
2. 查询行情：westock quote fuGC
3. 解析最新价、涨跌幅、货币单位（USD）
4. 说明为延时行情（isDelayed），并给出生成时间
```

### 15.2 期货合约资料查询

```
用户："WTI原油期货的合约规格是怎样的？"

AI 步骤：
1. 关键词找代码：westock search 原油 --type futures → fuCL（WTI原油，NYMEX）
2. 查询合约资料：westock futures detail fuCL
3. 解析交易所、合约规模、货币币种、最小变动单位、交易时间、所在时区
4. 输出合约规格说明
```

---

## 十六、外汇（离岸人民币/主要货币对/美元指数）

> 命令：`westock forex list` + `westock search --type forex` + `westock quote`/`westock kline`/`westock minute`（支持外汇代码 `fx*`）

### 16.1 外汇行情查询（关键词→代码→行情）

```
用户："离岸人民币现在多少？"

AI 步骤：
1. 关键词找代码：westock search 离岸 --type forex → fxCNH（离岸人民币）
2. 查询行情：westock quote fxCNH
3. 解析最新价、涨跌幅
4. 给出生成时间
```

### 16.2 外汇走势查询（K线/分时）

```
用户："美元日元近一个月走势如何？"

AI 步骤：
1. 关键词找代码：westock search 美元日元 --type forex → fxUSDJPY
2. 查询日K：westock kline fxUSDJPY --period day --limit 30
3. 解析区间高低点、涨跌幅，描述趋势
4. 提示：外汇仅提供当日分时（minute），不支持五日分时
```

---

## 十七、债券（可转债 / 可交换债）

> 命令：`westock quote`/`westock minute`/`westock kline`（支持可转债代码 沪 `sh11xxxx`/`sh13xxxx`、深 `sz12xxxx`）+ `bond`（发行要素/条款/现金流）

### 17.1 可转债行情查询（价格 + 转债维度）

```
用户："兴业转债现在行情怎么样？转股价值和溢价率高不高？"

AI 步骤：
1. 查询行情：westock quote sh113052
   （可转债走专属字段集，除价格/成交外额外返回转债维度，单只竖排「项目/内容」表展示）
2. 解析通用字段：最新价、涨跌幅、成交额
3. 解析转债维度：转股价值（bond_equity_value）、转股溢价率（bond_equity_premium）、
   双低（bond_double_low）、转股价（bond_convert_price）、正股代码（bond_stock_code）
4. 结合溢价率高低、双低值给出客观描述（不做投资建议）
5. 提示：行情接口不返回债券简称（name 为空），如需发行人/评级/条款用 bond
```

### 17.2 可转债基本面与条款（行情 + 详情联动）

```
用户："兴业转债的规模、到期日和赎回回售条款是什么？"

AI 步骤：
1. 行情快照看规模/期限：westock quote sh113052
   → 总规模（bond_total_size）、剩余规模（bond_undue_size）、到期日（bond_due_date）、
     到期收益率（bond_ytm）、强赎触发价/回售触发价
2. 详情看完整发行要素与条款：westock bond sh113052
   → 发行人、票面利率、期限、利率变动/现金流/赎回回售明细（默认输出）
3. 综合行情与详情，客观说明规模、到期安排与赎回/回售触发条件
```

---

## 十八、复合分析工作流（多命令编排 · 采样非全量）

> 以下场景需组合多个**原子命令**完成。westock 只提供原子能力、**不含脚本**；复合分析由 AI 编排原子命令实现。为控制调用次数与耗时，统一遵守四条**编排纪律**：
> 1. **批量**：`buyback` / `finance` / `quote` 均支持逗号一次多 code，禁止逐只循环调用；`trade-calendar` 一次拿全年。
> 2. **并行**：无依赖的调用（如按不同日期分组的多条 `quote --date`）同一轮并行发出。
> 3. **限量采样**：开放筛选出池时用小 `--limit`（如 20~30），**基于 Top N 代表性样本**，不做全市场全量。
> 4. **早停降级**：候选池过大先采样；数据不足/缺失直接如实交付边界，改参重跑不超过 1 次。
>
> ⚠️ 交付时须注明「**基于 Top N 样本，非全量统计**」。

### 18.1 事件后收益统计（如"回购披露后普遍表现"）

**候选池来源（决定是否跨技能）**：
- 用户**已给定股票池** → 纯 westock 完成（从第 2 步开始）。
- **开放式筛选**（如"所有做过回购的股票"）→ 出池属选股能力，先由 **westock-screener** 的 `screen event` 筛出并限量，拿到 code 列表再回到本流程（跨技能）。

```
调用链（以 2026 年回购为例，控制在 ~15 次调用内）：
1. 出池并限量（screener，仅开放筛选时）：
   screen event --type buyback --limit 30                 # Top 30 样本（buyback = 回购一月内）
2. 批量补披露日（data，1 次）：
   westock buyback code1,code2,...,code30 --start 2026-01-01 --end 2026-12-31
3. 一次拿全年交易日（data，1 次）：
   westock trade-calendar --year 2026 --trading-only
4. 按披露日分组批量查前复权收盘（data，同一披露日一批，可并行）：
   westock quote codeA,codeB --date <披露日基准交易日>
   westock quote codeC     --date <下一交易日>
5. 本地聚合统计：中位数 / 上涨占比 / 分布
```

**收益口径红线**：
- 基准价 = **披露日当日或此前最近交易日**收盘价；收益 = `(下一交易日收盘 / 基准收盘 − 1)`。
- 用 `quote --date` 取值（指定日期已自动取**前复权**价，`change/change_percent` 亦按前复权重算）；**禁止**用下一交易日 quote 的 `change_percent` 直接代替上述口径。
- **禁止**用自然日/工作日近似替代 `trade-calendar` 定交易日。
- 回购事件取**披露日**（公告日），不用回购实施区间的 `StartDate`/`EndDate`。

### 18.2 多年 ROE 验证（如"连续 5 年 ROE≥15%"）

**候选池来源**：开放筛选 → 先由 **westock-screener** `screen condition` 初筛（跨技能）；已给定池 → 直接从第 2 步开始。

```
调用链（控制在数次调用内）：
1. 初筛并限量（screener，仅开放筛选时）：
   screen condition --expression 'intersect([ROETTM > 15, PE_TTM > 0])' --limit 20
2. 批量取年报（data，1~2 次；必须 --fields all）：
   westock finance code1,...,code20 --fields all --limit 24
3. 本地逐只验证：取年报（EndDate 以 -12-31 结尾）ROE
   （ROEWeighted，或 归母净利润 / 股东权益 推算），按 连续 / 最低 / 平均 N 年判定达标
```

**口径红线**：
- 单期 `ROETTM` ≠ 多年连续 ROE，多年验证**必须读年报序列**。
- `finance` 默认 `core` 窄表**缺股东权益**，多年 ROE 验证必须 `--fields all`。
- 若仅用 `ROETTM` 单期初筛、未做年报验证，答案须标注「**ROETTM 单期初筛，未验证多年连续达标**」。

### 18.3 板块 / 指数成份对比（交集 / 差集 / 重合占比）

纯 westock 完成，无需跨技能。

```
调用链（2 次查询，可并行）：
1. 代码类型判断：
   pt* / sw*_* → 板块，用 sector constituent
   sh/sz 6 位、cs*、hk 字母开头 → 指数，用 index constituent
2. 并行取两边成份（--raw 便于本地做集合运算）：
   westock sector constituent pt02003578 --raw
   westock index  constituent sh000300   --raw
3. 本地对成份代码集合求：交集 / 仅 A / 仅 B / 重合占比（占 A、占 B 各一个百分比）
```

> 只有板块/指数名称时：先 `westock search <关键词> --type sector`（或 `--type index`）取 code；多个关键词可**一轮并行** search，合并去重后再取 code。

---

**记住**：westock 是数据查询工具，AI 负责数据分析和洞察！
