# WeStock Tool - AI 深度参考指南

> **定位**：本文档提供选股工具的详细返回数据格式、分析模板，以及完整的策略/标签代码列表。命令列表和基本用法请参见 [SKILL.md](../SKILL.md)。
> 完整字段列表请参见 [fields-guide.md](./fields-guide.md)。

---

## 一、返回数据格式

### 格式化输出（默认）

输出 Markdown 表格，每行一只股票，列含股票代码、名称、收盘价、涨跌幅及表达式涉及的指标字段：

```
| code | name | ClosePrice | ChangePCT | PE_TTM | ROETTM |
| --- | --- | --- | --- | --- | --- |
| sh600519 | 贵州茅台 | 1690.00 | 1.25 | 28.50 | 32.15 |
| sz000001 | 平安银行 | 12.50 | -0.32 | 5.80 | 16.20 |
...
```

### 原始 JSON（`--raw`）

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "total": 156,
    "returned": 20,
    "items": [
      {
        "SecuCode": "sh600519",
        "SecuName": "贵州茅台",
        "ClosePrice": 1690.00,
        "ChangePCT": 1.25,
        "PE_TTM": 28.50,
        "ROETTM": 32.15,
        "TotalMV": 2123000000000,
        "TurnoverRate": 0.35
      }
    ]
  }
}
```

**字段说明**：

| 字段 | 说明 |
|------|------|
| `code` | 状态码，`0` 表示成功 |
| `data.total` | 符合条件的股票总数 |
| `data.returned` | 实际返回数量 |
| `data.items` | 股票列表，始终包含 `SecuCode`/`SecuName`/`ClosePrice`/`ChangePCT`，动态包含表达式中的字段 |

### 港股/美股字段差异

> 详见 [SKILL.md](../SKILL.md) 「常用字段速查」。

---

## 二、分析模板

### 3.1 价值选股

```bash
# 低PE（PE < 15）
westock-tool filter "intersect([PE_TTM > 0, PE_TTM < 15])" --date 2026-03-12 --limit 20 --orderby PE_TTM --asc

# 高股息（股息率 > 5%）
westock-tool filter "DividendRatioTTM > 5" --date 2026-03-12 --limit 20 --orderby DividendRatioTTM --desc

# PEG策略（净利润增速 > 25%，PEG < 1）
westock-tool filter "intersect([PE_TTM > 0, NetProfitGrowRate > 25, PE_TTM / NetProfitGrowRate < 1])" --date 2026-03-12 --limit 20

# 低估值高ROE（PE < 15，ROE > 15%）
westock-tool filter "intersect([PE_TTM > 0, PE_TTM < 15, ROETTM > 15])" --date 2026-03-12 --limit 20 --orderby ROETTM --desc

# 破净股（PB < 1）
westock-tool filter "intersect([PB > 0, PB < 1])" --date 2026-03-12 --limit 20 --orderby PB --asc
```

**分析要点**：PE_TTM 分布（中位数/均值）、ROETTM 排名、结合市值和行业分类汇总

### 3.2 技术面选股

```bash
# 均线多头排列（MA5 > MA10 > MA20 > MA60）
westock-tool filter "intersect([MA_5 > MA_10, MA_10 > MA_20, MA_20 > MA_60])" --date 2026-03-12 --limit 20

# MACD金叉（DIF > DEA）
westock-tool filter "DIF > DEA" --date 2026-03-12 --limit 20

# KDJ超卖（KDJ_J < 15）
westock-tool filter "KDJ_J < 15" --date 2026-03-12 --limit 20 --orderby KDJ_J --asc

# RSI超卖（RSI_6 < 25）
westock-tool filter "RSI_6 < 25" --date 2026-03-12 --limit 20 --orderby RSI_6 --asc

# 神奇九转绿9信号
westock-tool filter "NineTurn_9 = 1" --date 2026-03-12 --limit 20

# 布林带突破上轨
westock-tool filter "ClosePrice > BollingerUpper" --date 2026-03-12 --limit 20
```

**分析要点**：均线间距（趋势强度）、配合换手率（TurnoverRate）验证、配合 MACD 交叉确认

### 3.3 资金面选股

```bash
# 主力净流入 > 1亿
westock-tool filter "MainNetFlow > 100000000" --date 2026-03-12 --limit 20 --orderby MainNetFlow --desc

# 主力持续流入（5/10/20日均为正）
westock-tool filter "intersect([MainNetFlow5D > 0, MainNetFlow10D > 0, MainNetFlow20D > 0])" --date 2026-03-12 --limit 20

# 主力5日流入 > 5亿
westock-tool filter "MainNetFlow5D > 500000000" --date 2026-03-12 --limit 20 --orderby MainNetFlow5D --desc

# 高换手率（> 5%）
westock-tool filter "TurnoverRate > 5" --date 2026-03-12 --limit 20 --orderby TurnoverRate --desc
```

**分析要点**：资金流入持续性、配合涨跌幅判断是否拉升期、筛选"主力流入但涨幅不大"的潜力股

### 3.4 财务分析选股

```bash
# 高ROE（ROE > 20%）
westock-tool filter "ROETTM > 20" --date 2026-03-12 --limit 20 --orderby ROETTM --desc

# 高成长（营收增速 > 30%，净利润增速 > 40%）
westock-tool filter "intersect([RevenueGrowRate > 30, NetProfitGrowRate > 40])" --date 2026-03-12 --limit 20 --orderby NetProfitGrowRate --desc

# 低负债（资产负债率 < 40%）
westock-tool filter "DebtRatio < 40" --date 2026-03-12 --limit 20 --orderby DebtRatio --asc

# 正经营现金流
westock-tool filter "OCFPS > 0" --date 2026-03-12 --limit 20

# 高ROE低负债（ROE > 15%，负债率 < 50%）
westock-tool filter "intersect([ROETTM > 15, DebtRatio < 50])" --date 2026-03-12 --limit 20 --orderby ROETTM --desc
```

### 3.5 组合策略选股

```bash
# 高股息+低估值（股息率 > 4%，PE < 12，PB < 1.5）
westock-tool filter "intersect([DividendRatioTTM > 4, PE_TTM > 0, PE_TTM < 12, PB > 0, PB < 1.5])" --date 2026-03-12 --limit 20 --orderby DividendRatioTTM --desc

# 白马成长（高ROE + 稳定增长）
westock-tool filter "intersect([ROETTM > 15, RevenueGrowRate > 15, NetProfitGrowRate > 15])" --date 2026-03-12 --limit 20 --orderby ROETTM --desc

# 困境反转（近期跌幅大但开始反弹）
westock-tool filter "intersect([Chg20D < -20, Chg5D > 0, Chg5D < 10])" --date 2026-03-12 --limit 20 --orderby Chg5D --desc

# 小盘价值（市值20-100亿，PE < 20）
westock-tool filter "intersect([TotalMV > 2000000000, TotalMV < 10000000000, PE_TTM > 0, PE_TTM < 20])" --date 2026-03-12 --limit 20 --orderby PE_TTM --asc

# 技术面+基本面组合（均线多头 + 低PE + 高ROE）
westock-tool filter "intersect([MA_5 > MA_10, MA_10 > MA_20, PE_TTM > 0, PE_TTM < 25, ROETTM > 12])" --date 2026-03-12 --limit 20 --orderby ROETTM --desc

# 次新股高成长（上市1年内 + 高增长）
westock-tool filter "intersect([ListDate > 20250317, RevenueGrowRate > 30])" --date 2026-03-12 --limit 20
```

### 3.6 机构评级选股（港股/美股）

```bash
# 港股高机构评级（买入评级 >= 8家）
westock-tool filter "BuyRatingNum >= 8" --date 2026-03-12 --limit 20 --orderby BuyRatingNum --desc --market hk

# 港股目标价上行空间（> 30%）
westock-tool filter "TargetPriceUpside > 30" --date 2026-03-12 --limit 20 --orderby TargetPriceUpside --desc --market hk

# 美股高机构评级
westock-tool filter "BuyRatingNum >= 8" --date 2026-03-12 --limit 20 --orderby BuyRatingNum --desc --market us

# 港股低估值 + 高评级
westock-tool filter "intersect([PeTTM > 0, PeTTM < 15, BuyRatingNum >= 5])" --date 2026-03-12 --limit 20 --market hk
```

### 3.7 按板块筛选

使用 `--universe` 限定选股范围，板块代码通过 `westock-data search <关键词> sector` 获取（去掉 `pt` 前缀）：

```bash
# 在华为概念板块中筛选低PE股票
westock-tool filter "intersect([PE_TTM > 0, PE_TTM < 25])" --date 2026-03-12 --limit 20 --orderby PE_TTM --asc --universe 02021291

# 在人工智能板块中筛选高ROE股票
westock-tool filter "ROETTM > 15" --date 2026-03-12 --limit 20 --orderby ROETTM --desc --universe 02003800
```

**常见板块代码**（可通过 westock-data 搜索获取最新代码）：

| 板块名称 | 代码 | 板块名称 | 代码 |
|---------|------|---------|------|
| 华为概念 | 02021291 | 人工智能 | 02003800 |
| 华为昇腾 | 02GN2032 | 人形机器人 | 02GN2238 |
| 华为鸿蒙 | 02101423 | 低空经济 | 02GN2294 |
| 华为算力 | 02GN2266 | 半导体 | 02003010 |
| AI大模型 | 02GN2228 | 数据要素 | 02GN2200 |
| AI算力芯片 | 02GN2222 | 算力租赁 | 02GN2234 |

### 3.8 港股低估值高股息

```bash
# 港股高股息低估值（股息率 > 6%，PE < 8，PB < 0.8）
westock-tool filter "intersect([PeTTM > 0, PeTTM < 8, DivTTM > 6, PbLF > 0, PbLF < 0.8])" --date 2026-03-12 --limit 20 --orderby DivTTM --desc --market hk

# 港股低估值蓝筹（PE < 10，市值 > 500亿）
westock-tool filter "intersect([PeTTM > 0, PeTTM < 10, TotalMV > 500])" --date 2026-03-12 --limit 20 --orderby TotalMV --desc --market hk

# 美股低估值高股息
westock-tool filter "intersect([PeTTM > 0, PeTTM < 15, DivTTM > 3])" --date 2026-03-12 --limit 20 --orderby DivTTM --desc --market us
```

### 3.9 标签选股

标签选股适用于快速按分类获取股票列表，无需手写表达式。常见场景：

```bash
# 查看央企公司
westock-tool label shareholder_central_state --date 2026-04-10

# 查看国企 + 央企（多标签）
westock-tool label shareholder_central_state,shareholder_local_state --date 2026-04-10 --limit 50

# 查看大基金持仓
westock-tool label shareholder_nicf_phase1,shareholder_nicf_phase2,shareholder_nicf_phase3 --date 2026-04-10

# 查看破净股
westock-tool label valuation_lowpb --date 2026-04-10

# 查看高ROE股票
westock-tool label fin_high_roettm --date 2026-04-10 --limit 50

# 查看业绩预增股
westock-tool label fin_forecast_inc --date 2026-04-10

# 查看千元股
westock-tool label price_up1000 --date 2026-04-10

# 查看超大盘股
westock-tool label marketcap_super_big --date 2026-04-10

# 查看近期次新股
westock-tool label listeddate_3mons --date 2026-04-10

# 查看 ST 股票（风险提示）
westock-tool label risk_st --date 2026-04-10
```

**分析要点**：
- 标签选股返回的是符合该分类的股票列表，适合快速了解某类股票的整体情况
- 可以多个标签组合查询，了解交叉分类的股票
- 标签选股结果可以进一步用 `westock-data` 查询个股详情进行深度分析
- 标签选股仅支持 A 股

**标签 + 条件选股联动**：

```bash
# 先用标签找出央企股票，再用 filter 在其中筛选低估值高股息
westock-tool label shareholder_central_state --date 2026-04-10 --limit 100
# → 从结果中提取股票代码列表
# → westock-data quote <央企代码列表>  # 查看行情进一步筛选
```

### 3.9.1 ETF 选基（label --asset etf）

通过 `--asset etf` 切换 label 命令到 ETF 维度（40+ 个 KYP 主题池）。与默认的股票标签选股职责并列：

```bash
# 列出全部 ETF 主题池
westock-tool label --asset etf --list
westock-tool label --asset etf --list 行情表现             # 按分组筛选

# 单池查询
westock-tool label high_dividend --asset etf               # 高股息 ETF
westock-tool label size_1000 --asset etf                   # 千亿规模 ETF
westock-tool label size_100 --asset etf --limit 50         # 百亿基金（分页）
westock-tool label issue_in_3m --asset etf                 # 近 3 月新发 ETF

# 多池并查（每个池分别返回，非交集）
westock-tool label low_valuation,high_roe --asset etf
westock-tool label commodity,bond,currency --asset etf     # 商品/债券/货币型
```

**主题池分类速查**：

| 分类 | 代表性池 |
|------|----------|
| 上市时间 | `issue_new`(最新发行)、`issue_in_3m/in_1y/over_5y` |
| 规模 | `size_1000`(千亿)、`size_500`、`size_100`(百亿) |
| 行情表现 | `high_dividend`(高股息)、`low_valuation`(低估值) |
| 财务 | `high_roe`、`high_roa`、`high_npttm` |
| 经理 | `manager_long_tenure`(老将)、`manager_high_perf` |
| 类型/策略 | `commodity`(商品型)、`bond`(债券型)、`currency`(货币型)、`strategy_div`(红利) |

> ⚠️ **数据职责边界**：
> - 用户带"标签/主题"（如"高股息 / 千亿基金 / 科创板占比高"）→ 走 `label --asset etf`（横截面筛选）
> - 用户给具体 ETF 代码（如"沪深300ETF详情"）→ 走 `westock-data etf detail`（按代码精查）
>
> ⚠️ **限制**：ETF 选基仅支持单日查询（不支持 `--start/--end` 区间）。

### 3.10 事件选股

事件选股适用于查询发生特定事件的股票列表，事件代码已自带时间窗口（如 `past_30`、`next_90`）：

```bash
# 预计解禁三月内
westock-tool event shareunlock_next_90

# 实际解禁公告后
westock-tool event shareunlock_incoming

# 董监高变动
westock-tool event manager_change

# 董监高增减持
westock-tool event manager_sharechg

# 计划减持未实施
westock-tool event manager_shareplan_sell_incoming

# 回购一月内
westock-tool event buyback

# 大宗交易一月内
westock-tool event block_past_30

# 龙虎榜上榜统计两周内
westock-tool event longhu_statis_past_15

# 将加入重要指数
westock-tool event index_add_incoming

# 重大资产重组
westock-tool event regroup_unclosed

# 分红预案公告后一月
westock-tool event dividend_plan

# 业绩预约一月内披露
westock-tool event earnings_schedule
```

**分析要点**：
- 事件代码已包含时间窗口（如 `past_30` 表示过去30天，`next_90` 表示未来90天）
- 事件选股仅支持 A 股

**事件 + 条件选股联动**：

```bash
# 先用事件找出即将限售解禁的股票，再分析基本面
westock-tool event shareunlock_next_90
# → 从结果中提取股票代码列表
# → westock-data quote <解禁股代码列表>  # 查看行情进一步筛选
```
# → 从结果中提取股票代码列表
# → westock-data quote <解禁股代码列表>  # 查看行情进一步筛选
```

### 3.11 排行选股（ranking）

排行选股是**按指标排序选股**的统一入口，支持**五类指标源**（涨跌停 / 财务 / 评分 / 两融 / 资金流入），核心特色是可在板块、标签、策略、事件结果内做**二次排序**。

```bash
# 查看所有可用指标
westock-tool ranking --list

# ── 评分排行（score 源） ──
westock-tool ranking CompScore --limit 10              # 综合评分 TOP10
westock-tool ranking CapScore --limit 20               # 资金评分 TOP20
westock-tool ranking RiskScore --limit 15              # 风险评分排行
westock-tool ranking CompScore --type weekly           # 评分周变动排行
westock-tool ranking CompScore --type monthly          # 评分月变动排行

# ── 涨跌停排行（market 源） ──
westock-tool ranking limitup_days                      # 连续涨停天数排行
westock-tool ranking limitup_seal_volume               # 涨停封单量排行
westock-tool ranking limitdn_days                      # 连续跌停天数排行
westock-tool ranking limitdn_seal_volume               # 跌停封单量排行

# ── 财务排行（financial 源） ──
westock-tool ranking fin_valuation --limit 10          # 估值排行（默认升序，PE最低）
westock-tool ranking fin_growth --limit 20             # 成长能力排行
westock-tool ranking fin_profit                        # 盈利能力排行
westock-tool ranking fin_pershare                      # 每股指标排行
westock-tool ranking fin_cash_size                     # 现金流规模排行

# ── 两融排行（margin 源） ──
westock-tool ranking margin_balance --limit 20         # 两融余额最多 TOP20
westock-tool ranking margin_chg_d                      # 两融日加仓榜（--asc 看日减仓榜）
westock-tool ranking margin_chg_w                      # 两融周加仓榜
westock-tool ranking margin_chg_m                      # 两融月加仓榜
westock-tool ranking margin_chg_q                      # 两融季加仓榜
westock-tool ranking margin_chg_y                      # 两融年加仓榜
westock-tool ranking margin_in_days --min-MtInDays 5   # 两融连续扩大≥5天
westock-tool ranking margin_out_days                   # 两融连续缩小天数排行

# ── 资金流入排行（capital 源） ──
westock-tool ranking cap_main_net --limit 20           # 主力净流入榜（--asc 看主力净流出榜）
westock-tool ranking cap_retail_net --limit 20         # 散户净流入榜
westock-tool ranking cap_main_5d --limit 20            # 主力 5 日合计净流入榜
westock-tool ranking cap_in_days --min-MainInDays 3    # 主力连续净流入≥3天
westock-tool ranking cap_out_days                      # 主力连续净流出天数排行

# ── 范围限定（核心特色） ──
westock-tool ranking CompScore --within-label shareholder_central_state --limit 10  # 央企里评分最高
westock-tool ranking fin_valuation --within-strategy macd_golden                    # MACD金叉中估值最低
westock-tool ranking CompScore --within-event shareunlock_next_90                   # 限售解禁股评分排行
westock-tool ranking fin_valuation --universe 11010001                              # 半导体板块估值排行
westock-tool ranking margin_chg_d --universe 11010001 --limit 10                    # 半导体板块两融日加仓最多
westock-tool ranking cap_main_5d --within-label shareholder_central_state           # 央企里主力 5 日累计加仓最多

# ── 阈值筛选 ──
westock-tool ranking CapScore --min-CompScore 70 --limit 10   # 综合评分≥70按资金评分排序

# ── 历史日期 / 排序方向 / 分页 ──
westock-tool ranking CompScore --date 2026-04-20
westock-tool ranking CompScore --asc                   # 评分最低
westock-tool ranking limitup_days --limit 50 --offset 20
```

**核心参数**：

| 参数 | 说明 |
|------|------|
| `<指标>` | 位置参数，支持 30 个指标：涨跌停（`limitup_*`/`limitdn_*`，4 个）、财务（`fin_*`，8 个）、评分（`CompScore`/`CapScore`/`FunmScore`/`RiskScore`/`TecScore`，5 个）、两融（`margin_*`，8 个）、资金流入（`cap_*`，5 个） |
| `--type` | 评分类型：`cur`(默认) / `weekly` / `monthly`，仅 score 指标有效 |
| `--within-label` | 限定在指定标签内排行（如 `shareholder_central_state`） |
| `--within-strategy` | 限定在指定策略内排行（如 `macd_golden`） |
| `--within-event` | 限定在指定事件内排行（如 `shareunlock_next_90`） |
| `--universe` | 限定在板块内排行（板块代码） |
| `--min-<字段> 值` | 阈值筛选（如 `--min-MtInDays 5` 两融连续扩大≥5天） |
| `--asc` | 升序（默认降序；估值类默认升序）。变动类指标支持 `--asc` 看反向（如 `cap_main_net --asc` 看主力净流出榜） |
| `--date` | 查询日期，默认今天 |
| `--limit` / `--offset` | 分页 |
| `--list [分组]` | 列出所有指标，可按分组筛选（如 `--list 评分` / `--list 两融排行` / `--list 资金流入`） |

> ⚠️ `--within-label` / `--within-strategy` / `--within-event` **三者互斥**，只能用一个。

**指标维度**：

- **评分维度**：综合(CompScore) / 资金(CapScore) / 基本面(FunmScore) / 风险(RiskScore) / 技术(TecScore)
- **财务维度**：估值 / 成长 / 盈利 / 每股 / 现金流 / 营运 / 偿债 / 收入结构（8 个清单）
- **涨跌停维度**：连续涨跌停天数 + 封单量（4 个指标）
- **两融维度**：余额 / 日周月季年变动 / 连续扩大缩小天数（来自 `peer_cap_margin_daily`/`_interval`/`_days` 三个清单）
- **资金流入维度**：主力净流入 / 散户净流入 / 5日合计 / 连续净流入流出天数（来自 `peer_cap_daily`/`peer_cap_interval_money`/`peer_cap_interval_days` 三个清单）
- **组合查询**：`--within-*` 可与其他选股命令联动（如"MACD金叉中估值最低"、"央企里主力加仓最多"）
- 排行选股仅支持 A 股

#### 两融指标字段说明

来自 `peer_cap_margin_daily`、`peer_cap_margin_interval`、`peer_cap_margin_days` 三个清单：

| 指标 key | sortField | 字段含义 | 默认排序 | --asc 用途 |
|----------|-----------|---------|---------|-----------|
| `margin_balance` | MarginTrade | 最新融资融券余额（万） | desc | 余额最少 |
| `margin_chg_d` | MChgD | 融资融券余额日变动（万） | desc 加仓榜 | **日减仓榜** |
| `margin_chg_w` | MChgW | 融资融券余额周变动（万） | desc 加仓榜 | **周减仓榜** |
| `margin_chg_m` | MChgM | 融资融券余额月变动（万） | desc 加仓榜 | **月减仓榜** |
| `margin_chg_q` | MChgQ | 融资融券余额季变动（万） | desc 加仓榜 | **季减仓榜** |
| `margin_chg_y` | MChgY | 融资融券余额年变动（万） | desc 加仓榜 | **年减仓榜** |
| `margin_in_days` | MtInDays | 两融连续扩大天数（天） | desc | 短的排前 |
| `margin_out_days` | MtOutDays | 两融连续缩小天数（天） | desc | 短的排前 |

> **数据更新**：两融余额 T+1 披露，每日收盘后更新。**单位说明**：变动数额单位为"万元"。

#### 资金流入指标字段说明

来自 `peer_cap_daily`、`peer_cap_interval_money`、`peer_cap_interval_days` 三个清单：

| 指标 key | sortField | 字段含义 | 默认排序 | --asc 用途 |
|----------|-----------|---------|---------|-----------|
| `cap_main_net` | MainNetIn | 主力资金净流入（万） | desc 主力净流入榜 | **主力净流出榜** |
| `cap_retail_net` | RetailNetOut | 散户资金净流入（万） | desc 散户净流入榜 | **散户净流出榜** |
| `cap_main_5d` | MainSum5d（派生） | 主力 5 日合计净流入（万）= MainT0+T1+T2+T3+T4 | desc | **5 日累计净流出榜** |
| `cap_in_days` | MainInDays | 主力连续净流入天数（天） | desc | 短的排前 |
| `cap_out_days` | MainOutDays | 主力连续净流出天数（天） | desc | 短的排前 |

> **数据守恒**：散户净流入榜与主力净流出榜首位通常对应（同一只股票），体现资金流转零和性。
> **派生字段说明**：`MainSum5d` 由客户端聚合 `peer_cap_interval_money` 清单的 T0~T4 五日数据得到，用于"5 日合计净流入榜"排序。
> **数据更新**：盘中实时更新（基于逐笔成交）。**单位说明**：均为"万元"。

**ranking + 数据查询联动**：

```bash
# 先用排行选股找出综合评分最高的股票，再查看个股详情
westock-tool ranking CompScore --limit 5
# → 从结果中提取股票代码
# → westock-data score sh600519       # 查看评分详情及变动
# → westock-data quote sh600519       # 查看行情

# 先找出连续涨停的股票，再查看个股详情
westock-tool ranking limitup_days --limit 10
# → westock-data quote <涨停股代码列表>  # 查看行情

# 先找两融加仓最多的股票，再查融资融券明细
westock-tool ranking margin_chg_d --limit 10
# → westock-data flow margin sh600519   # 查看个股两融详情

# 先找主力 5 日加仓最多的股票，再查资金流向时间序列
westock-tool ranking cap_main_5d --limit 10
# → westock-data fundhold sh600519 --market hs --start 2026-04-15 --end 2026-04-20  # 查看时间序列
```

### 3.11.1 ETF 排行选基（ranking --asset etf）

通过 `--asset etf` 切换 ranking 命令到 ETF 维度（多类 ETF 排行指标，~1530 只 ETF 全市场）。与默认的股票排行职责并列：

```bash
# 列出全部 ETF 排行指标
westock-tool ranking --asset etf --list

# 规模榜
westock-tool ranking size --asset etf --limit 20                 # 默认 TotalAsset 降序

# 估值榜（--orderby 切换字段，--asc 覆盖默认方向）
westock-tool ranking valuation --asset etf --orderby PB --asc         # 按 PB 升序（最低估值）
westock-tool ranking valuation_pct --asset etf --orderby PE_TTM_PCT   # PE 历史百分位最低（默认升序）

# 区间表现
westock-tool ranking qt_chg_interval --asset etf --orderby ChgPct20D --limit 10  # 近 20 日涨幅榜
westock-tool ranking turn_interval --asset etf --orderby EtfTurnoverRAvgM        # 月均换手率榜
westock-tool ranking disc_interval --asset etf --orderby EtfDiscAvgW             # 周均溢价榜
```

**ETF 排行指标速查**：

| 指标 | 中文 | 默认排序字段 | 默认方向 |
|------|------|-----------|---------|
| `size` | ETF 规模 | `TotalAsset` | ↓ |
| `nvsize_interval` | ETF 总规模波动 | `EtfSize` | ↓ |
| `valuation` | 估值 | `PE_TTM` | ↑ |
| `valuation_pct` | 估值历史百分位 | `PE_TTM_PCT` | ↑ |
| `qt_chg_interval` | 区间涨跌幅 | `ChgPct20D` | ↓ |
| `turn_interval` | 区间换手率均值 | `EtfTurnoverRAvgM` | ↓ |
| `disc_interval` | 溢折率波动 | `EtfDiscAvgM` | ↓ |

**核心参数**：

| 参数 | 说明 |
|------|------|
| `<指标>` | ETF 排行指标之一 |
| `--asset etf` | **必填**，切换为 ETF 维度（不传则走股票排行） |
| `--orderby <字段>` | 覆盖默认排序字段（如同一个 valuation 指标可按 PB/PS/DivYield 切换） |
| `--asc` | 覆盖默认方向 |
| `--date` / `--limit` / `--offset` / `--list` | 同股票排行 |

> ⚠️ **数据职责边界**：
> - 用户问"ETF 规模最大/估值最低/涨幅最高"等**横截面排行** → 走 `ranking --asset etf`
> - 用户给具体 ETF 代码问详情 → 走 `westock-data etf detail`（按代码精查）
>
> ⚠️ **限制**：ETF 排行不支持 `--within-label/--within-strategy/--within-event` 范围限定（这些仅作用于股票池）。

---

## 四、预设选股函数完整列表

> `filter --preset` 是 filter 命令的快捷方式，用预设条件表达式筛选，输出含指标列的 Markdown 表格。
> 与 `strategy` 命令的区别：strategy 输出仅含 code/name 的表格，preset 输出含指标列的表格。

#### 估值分析类

| 函数名 | 说明 | 内置默认值 |
|--------|------|------|
| `LowPE` | 低PE筛选 | `maxPE`=20 |
| `LowPB` | 破净股筛选(PB<1) | `maxPB`=1 |
| `HighDividend` | 高股息筛选 | `minDividend`=3% |
| `ValuationPercentile` | 估值百分位低位 | `maxPercentile`=30 |
| `PEG` | PEG策略(PEG<1) | `maxPEG`=1, `minGrowth`=20% |

#### 技术指标类


| 函数名 | 说明 | 内置默认值 |
|--------|------|------|
| `KDJOversold` | KDJ超卖 | `maxJ`=20 |
| `RSIOversold` | RSI超卖 | `maxRSI`=30 |
| `NineTurnGreen9` | 神奇九转绿9信号 | - |

#### 财务分析类

| 函数名 | 说明 | 内置默认值 |
|--------|------|------|
| `HighROE` | 高ROE筛选 | `minROE`=15% |
| `HighGrowth` | 高成长筛选 | `minRevenueGrowth`=20%, `minProfitGrowth`=30% |
| `LowDebt` | 低负债筛选 | `maxDebtRatio`=50% |
| `PositiveCashFlow` | 正现金流筛选 | - |

#### 资金流向类

| 函数名 | 说明 | 内置默认值 |
|--------|------|------|
| `MainInflow` | 主力资金流入 | `minInflow`=1亿 |
| `SustainedInflow` | 主力持续流入(5/10/20日) | - |
| `HighShortRatio` | 高卖空比例 | `minShortRatio`=10% |

#### 机构评级类（港股/美股）

| 函数名 | 说明 | 内置默认值 |
|--------|------|------|
| `HighRating` | 高机构评级 | `minBuyRating`=5 |
| `TargetPriceUpside` | 目标价上行空间 | `minUpside`=20% |

#### 组合策略类

| 函数名 | 说明 | 内置默认值 |
|--------|------|------|
| `HighDividendLowValuation` | 高股息+低估值 | `minDividend`, `maxPE`, `maxPB` |
| `WhiteHorseGrowth` | 白马成长(高ROE+稳定增长) | - |
| `Turnaround` | 困境反转 | `minTurnaround`=50% |
| `SmallCapValue` | 小盘价值(20-100亿市值) | - |
| `TechFundamentalCombo` | 技术面+基本面组合 | - |

> ⚠️ 预设函数的参数均为内置默认值，不支持通过 CLI 传入自定义参数。如需自定义条件，请使用 `filter` 表达式语法手写条件。

---

## 五、错误处理

- 检查返回 JSON 的 `code` 字段，`0` 表示成功，非 `0` 时查看 `msg` 获取原因
- 常见错误：字段名混用（如沪深用了 `PeTTM`）、港股/美股未指定 `--market`、表达式语法错误

---

**记住**：选股查询是 Skill 的职责，数据分析是 AI 的职责！

---

## 六、策略选股完整列表

| 分类 | 策略代码 | 名称 |
|------|---------|------|
| 基本面 | `big_cap` | 行业高增长 |
| 基本面 | `pb_roe` | 高盈利价值 |
| 基本面 | `high_dividend` | 高股息 |
| 基本面 | `food_beverage` | 低估食品饮料 |
| 基本面 | `household_appliances` | 优质家电 |
| 基本面 | `profit_preannounce` | 业绩预增 |
| 大师策略 | `buffet` | 价值龙头 |
| 大师策略 | `trinity` | 三一投资型风格选股法 |
| 大师策略 | `davis` | 估值业绩齐飞 |
| 大师策略 | `derryman` | 逆向投资 |
| 大师策略 | `graham` | 格雷厄姆型风格策略 |
| 大师策略 | `fisher` | 费雪型风格策略 |
| 综合 | `golden_strategy` | 策略金股 |
| 综合 | `increase_holding` | 高管增持 |
| 综合 | `investor_investigation` | 机构调研 |
| K线形态 | `dawn_breaks` | 曙光初现 |
| K线形态 | `up_down_up` | 两阳夹一阴 |
| K线形态 | `morning_star` | 早晨之星 |
| K线形态 | `red_three_solider` | 红三兵 |
| K线形态 | `zthmq` | 涨停回马枪 |
| K线形态 | `rise_big_up` | 跳空向上 |
| K线形态 | `hibiscus_out_of_water` | 出水芙蓉 |
| K线形态 | `over_drop_rebound` | 超跌反弹 |
| K线形态 | `long_red_show_road` | 长阳指路 |
| K线形态 | `xianrenzhilu` | 仙人指路 |
| K线形态 | `open_high_close_low` | 高开低走 |
| 指标信号 | `macd_golden` | MACD金叉 |
| 指标信号 | `kdj_golden` | KDJ金叉 |
| 指标信号 | `bias_golden` | BIAS金叉 |
| 指标信号 | `rsi_golden` | RSI金叉 |
| 指标信号 | `rsi_oversold` | RSI超卖 |
| 指标信号 | `bias_oversold` | BIAS超卖 |
| 指标信号 | `wr_oversold` | WR超卖 |
| 指标信号 | `kdj_super_golden` | 黄金KDJ |
| 指标信号 | `macd_bottom_deviate` | MACD底背离 |
| 指标信号 | `macd_red_wave` | MACD红二波 |
| 指标信号 | `kdj_bottom_deviate` | KDJ底背离 |
| 指标信号 | `bias_bottom_deviate` | BIAS底背离 |
| 指标信号 | `rsi_bottom_deviate` | RSI底背离 |
| 指标信号 | `sar_buy_signal` | SAR买入信号 |
| 均线/布林 | `one_rise_three_ma` | 一阳三线 |
| 均线/布林 | `ma_long` | 均线多头发散 |
| 均线/布林 | `ma_long_boll_bt_mid` | 均线多头+布林中轨突破 |
| 均线/布林 | `boll_bt_upper` | 布林带上轨突破 |
| 均线/布林 | `boll_bt_mid` | 布林带中轨突破 |
| 均线/布林 | `ma_stick` | 均线粘连 |
| 资金面 | `major_force` | 主力抢筹 |
| 资金面 | `institution_chasing` | 机构接盘 |
| 资金面 | `abnormal_trade_at_dayend` | 尾盘掘金 |
| 资金面 | `margin_trade` | 融资追涨 |

---

## 七、标签选股完整列表

| 分类 | 标签代码 | 名称 |
|------|---------|------|
| 股东属性 | `shareholder_central_state` | 央企公司 |
| 股东属性 | `shareholder_local_state` | 国企公司 |
| 股东属性 | `shareholder_private` | 民企公司 |
| 股东属性 | `shareholder_qfii` | 含外资 |
| 股东属性 | `shareholder_nicf_phase1` | 大基金一期 |
| 股东属性 | `shareholder_nicf_phase2` | 大基金二期 |
| 股东属性 | `shareholder_nicf_phase3` | 大基金三期 |
| 股东属性 | `shareholder_hkfund` | 陆股通持股 |
| 股东属性 | `shareholder_huijin` | 汇金持股 |
| 股东属性 | `shareholder_mof` | 财政部持股 |
| 股东属性 | `shareholder_csf` | 证金持股 |
| 风险标签 | `risk_st` | ST与*ST股 |
| 风险标签 | `risk_delisting` | 退市整理期股票 |
| 风险标签 | `risk_remove_st` | 摘星脱帽股 |
| 风险标签 | `risk_broken_ipo` | 破发股 |
| 估值水平 | `valuation_abs_high` | 估值绝对高位股 |
| 估值水平 | `valuation_abs_low` | 估值绝对低位股 |
| 估值水平 | `valuation_rel_high` | 估值相对高位股 |
| 估值水平 | `valuation_rel_low` | 估值相对低位股 |
| 估值水平 | `valuation_lowpb` | 破净股 |
| 估值水平 | `valuation_negpe` | 亏损股 |
| 资产结构 | `fin_asset_high_cash` | 资产结构多现金 |
| 资产结构 | `fin_asset_high_inventory` | 资产结构多库存 |
| 资产结构 | `fin_asset_high_receivable` | 资产结构多应收 |
| 资产结构 | `fin_asset_high_longequity` | 资产结构多长股投 |
| 资产结构 | `fin_asset_high_investprop` | 资产结构多投资性房地产 |
| 资产结构 | `fin_asset_high_fixedasset` | 资产结构多固定资产 |
| 资产结构 | `fin_asset_high_bubble1` | 资产结构多泡沫资产1 |
| 资产结构 | `fin_asset_high_bubble2` | 资产结构多泡沫资产2 |
| 负债结构 | `fin_liability_high_shortdebt` | 负债结构多短债 |
| 负债结构 | `fin_liability_high_estimateliab` | 负债结构多预计负债 |
| 负债结构 | `fin_liability_high_advance` | 负债结构多预收 |
| 利润结构 | `fin_profit_high_cost_sales` | 成本结构多销售费用 |
| 利润结构 | `fin_profit_high_cost_admin` | 成本结构多管理费用 |
| 利润结构 | `fin_profit_high_cost_dev` | 成本结构多研发费用 |
| 利润结构 | `fin_profit_high_cost_financing` | 成本结构多财务费用 |
| 利润结构 | `fin_profit_high_assetimpair` | 利润结构多资产减值 |
| 利润结构 | `fin_profit_high_creditimpair` | 利润结构多信用减值 |
| 利润结构 | `fin_profit_high_assetsell` | 利润结构多资产处置 |
| 利润结构 | `fin_profit_high_discontinue` | 利润结构多终止经营净利润 |
| 利润结构 | `fin_profit_high_oci` | 利润结构多其他综合收益 |
| 利润结构 | `fin_profit_high_nonopincome` | 利润结构多营业外收入 |
| 现金流结构 | `fin_cash_high_cash` | 现金流结构多现金 |
| 现金流结构 | `fin_cash_high_cfo` | 现金流结构多经营现金 |
| 现金流结构 | `fin_cash_high_cfi` | 现金流结构多投资现金 |
| 现金流结构 | `fin_cash_high_cff` | 现金流结构多筹资现金 |
| 现金流结构 | `fin_cash_neg_cfo` | 现金流结构负经营现金 |
| 现金流结构 | `fin_cash_neg_cfi` | 现金流结构负投资现金 |
| 现金流结构 | `fin_cash_neg_cff` | 现金流结构负筹资现金 |
| 财务排名 | `fin_profitablity_high_rk_epsttm` | 盈利能力EPSttm高排序 |
| 财务排名 | `fin_profitablity_high_rk_roettm` | 盈利能力ROEttm高排序 |
| 财务排名 | `fin_profitablity_high_rk_roattm` | 盈利能力ROAttm高排序 |
| 财务排名 | `fin_profitablity_high_rk_gpttm` | 盈利能力毛利率ttm高排序 |
| 财务排名 | `fin_profitablity_high_rk_npttm` | 盈利能力净利率ttm高排序 |
| 财务排名 | `fin_operating_high_rk_receivable_turn` | 营运能力应收周转高排序 |
| 财务排名 | `fin_operating_high_rk_inventory_turn` | 营运能力存货周转高排序 |
| 财务排名 | `fin_operating_high_rk_asset_turn` | 营运能力资产周转高排序 |
| 财务排名 | `fin_growth_high_rk_rev_growth` | 成长能力营收增速高排序 |
| 财务排名 | `fin_growth_high_rk_profit_growth` | 成长能力利润增速高排序 |
| 财务排名 | `fin_growth_high_rk_asset_growth` | 成长能力资产增速高排序 |
| 财务排名 | `fin_liquidity_high_rk_current_ratio` | 偿债能力流动比率高排序 |
| 财务排名 | `fin_liquidity_high_rk_liability_ratio` | 偿债能力负债率高排序 |
| 财务排名 | `fin_liquidity_high_rk_interest_cover` | 偿债能力利息保障倍数高排序 |
| 财务排名 | `fin_profitablity_low_rk_epsttm` | 盈利能力EPSttm低排序 |
| 财务排名 | `fin_profitablity_low_rk_roettm` | 盈利能力ROEttm低排序 |
| 财务排名 | `fin_profitablity_low_rk_roattm` | 盈利能力ROAttm低排序 |
| 财务排名 | `fin_profitablity_low_rk_gpttm` | 盈利能力毛利率ttm低排序 |
| 财务排名 | `fin_profitablity_low_rk_npttm` | 盈利能力净利率ttm低排序 |
| 财务排名 | `fin_operating_low_rk_receivable_turn` | 营运能力应收周转低排序 |
| 财务排名 | `fin_operating_low_rk_inventory_turn` | 营运能力存货周转低排序 |
| 财务排名 | `fin_operating_low_rk_asset_turn` | 营运能力资产周转低排序 |
| 财务排名 | `fin_growth_low_rk_rev_growth` | 成长能力营收增速低排序 |
| 财务排名 | `fin_growth_low_rk_profit_growth` | 成长能力利润增速低排序 |
| 财务排名 | `fin_growth_low_rk_asset_growth` | 成长能力资产增速低排序 |
| 财务排名 | `fin_liquidity_low_rk_current_ratio` | 偿债能力流动比率低排序 |
| 财务排名 | `fin_liquidity_low_rk_liability_ratio` | 偿债能力负债率低排序 |
| 财务排名 | `fin_liquidity_low_rk_interest_cover` | 偿债能力利息保障倍数低排序 |
| 财务特征 | `fin_high_roettm` | 高ROEttm |
| 财务特征 | `fin_high_gpttm` | 高销售毛利率ttm |
| 财务特征 | `fin_high_npttm` | 高销售净利率ttm |
| 财务特征 | `fin_neg_rev_growth` | 营收负增长 |
| 财务特征 | `fin_neg_profit_growth` | 利润负增长 |
| 财务特征 | `fin_neg_asset_growth` | 资产负增长 |
| 财务特征 | `fin_unhealthy_growth` | 增收不增利 |
| 财务特征 | `fin_healthy_growth` | 降本增效股 |
| 财务特征 | `fin_forecast_inc` | 业绩预盈预增股 |
| 财务特征 | `fin_forecast_dec` | 业绩预亏预降股 |
| 财务特征 | `fin_forecast_slower_dec` | 业绩减亏减降股 |
| 财务特征 | `fin_forecast_slower_inc` | 业绩减增股 |
| 上市时间 | `listeddate_5days` | 新股5日内 |
| 上市时间 | `listeddate_3mons` | 近端次新股 |
| 上市时间 | `listeddate_1year` | 远端次新股 |
| 上市时间 | `listeddate_3year` | 上市1年以上3年以内 |
| 上市时间 | `listeddate_3yearplus` | 上市3年以上 |
| 价格与市值 | `price_below1` | 1元股 |
| 价格与市值 | `price_between_1_10` | 1到10元股 |
| 价格与市值 | `price_between_10_100` | 10到100元股 |
| 价格与市值 | `price_between_100_500` | 100到500元股 |
| 价格与市值 | `price_between_500_1000` | 500到1000元股 |
| 价格与市值 | `price_up1000` | 千元股 |
| 价格与市值 | `marketcap_below10` | 10亿以下股 |
| 价格与市值 | `marketcap_between_10_50` | 10到50亿股 |
| 价格与市值 | `marketcap_between_50_100` | 50到100亿股 |
| 价格与市值 | `marketcap_between_100_1000` | 100到1000亿股 |
| 价格与市值 | `marketcap_between_1000_10000` | 1000到10000亿股 |
| 价格与市值 | `marketcap_up10000` | 10000亿以上股 |
| 价格与市值 | `marketcap_super_big` | 超大盘 |
| 价格与市值 | `marketcap_super_small` | 超小盘 |

---

## 八、事件选股完整列表

| 分类 | 事件代码 | 名称 |
|------|---------|------|
| 分红 | `dividend_plan` | 分红预案公告后一月 |
| 分红 | `dividend_solution` | 分红决案公告后一月 |
| 分红 | `dividend_detail` | 分红实施公告后一月 |
| 分红 | `dividend_exdiv` | 分红除权后三日 |
| 业绩 | `earnings_schedule` | 业绩预约一月内披露 |
| 业绩 | `earnings_forecast` | 业绩预告后一月 |
| 业绩 | `earnings_express` | 业绩快报后一月 |
| 业绩 | `earnings_release` | 业绩披露后一周 |
| 定增 | `seo_past_7` | 定增上市前一周 |
| 定增 | `seo_past_30` | 定增上市前一月 |
| 定增 | `seo_next_30` | 定增上市后一月 |
| 定增 | `seo_next_90` | 定增上市后三月 |
| 股东大会 | `meeting_held` | 股东大会一月内召开 |
| 停复牌 | `suspension_now` | 停牌中 |
| 停复牌 | `suspension_over_30` | 停牌超一月 |
| 停复牌 | `resumption_next_3` | 复牌前三日 |
| 停复牌 | `resumption_past_7` | 复牌后一周 |
| 公司变更 | `rename_incoming` | 即将更名 |
| 公司变更 | `rename_past_90` | 更名后三月 |
| 董监高变动 | `manager_change` | 董监高变动 |
| 董监高变动 | `manager_sharechg` | 董监高增减持 |
| 董监高变动 | `manager_shareplan_sell_incoming` | 计划减持未实施 |
| 董监高变动 | `manager_shareplan_buy_incoming` | 计划增持未实施 |
| 董监高变动 | `manager_shareplan_sell_implementing` | 计划减持实施中 |
| 董监高变动 | `manager_shareplan_buy_implementing` | 计划增持实施中 |
| 回购 | `buyback` | 回购一月内 |
| 限售解禁 | `shareunlock_next_90` | 预计解禁三月内 |
| 限售解禁 | `shareunlock_incoming` | 实际解禁公告后 |
| 限售解禁 | `shareunlock_next_15` | 实际解禁两周内 |
| 法律与处罚 | `suitcase` | 诉讼后一月 |
| 法律与处罚 | `deregulation_incoming` | 重大处罚将生效 |
| 法律与处罚 | `deregulation_past_30` | 重大处罚生效一月内 |
| 重大事项 | `merger_unclosed` | 重大吸收合并 |
| 重大事项 | `tender_offer_unclosed` | 重大要约收购 |
| 重大事项 | `regroup_unclosed` | 重大资产重组 |
| 指数变动 | `index_add_incoming` | 将加入重要指数 |
| 指数变动 | `index_add_implemented_prev_7` | 已加入重要指数一周 |
| 指数变动 | `index_del_incoming` | 将踢出重要指数 |
| 指数变动 | `index_del_implemented_prev_7` | 已踢出重要指数一周 |
| 交易异动 | `block_past_30` | 大宗交易一月内 |
| 交易异动 | `longhu_statis_past_15` | 龙虎榜上榜统计两周内 |
| 交易异动 | `longhu_detail_past_15` | 龙虎榜上榜详情两周内 |

---

## 九、排行选股（ranking）完整指标列表

`ranking` 命令支持三类指标源，共 17 个指标：

### 9.1 涨跌停指标（market）

| 分类 | 指标代码 | 名称 | 排序字段 |
|------|---------|------|---------|
| 涨停 | `limitup_days` | 连续涨停天数 | LimitUpDays |
| 涨停 | `limitup_seal_volume` | 收盘涨停封单量 | LimitUpVolume |
| 跌停 | `limitdn_days` | 连续跌停天数 | LimitDnDays |
| 跌停 | `limitdn_seal_volume` | 收盘跌停封单量 | LimitDnVolume |

### 9.2 财务排行指标（financial）

| 指标代码 | 名称 | 默认排序字段 | 默认方向 |
|---------|------|-------------|---------|
| `fin_valuation` | 估值排行 | PE_TTM | 升序（PE低优先） |
| `fin_growth` | 成长能力 | RevenueGrowth | 降序 |
| `fin_profit` | 盈利能力 | RoeTTM | 降序 |
| `fin_pershare` | 每股指标 | EpsTTM | 降序 |
| `fin_cash_size` | 现金流规模 | CFOTTM | 降序 |
| `fin_operation` | 营运能力 | - | 降序 |
| `fin_liquidity` | 偿债能力 | - | 降序 |
| `fin_profit_structure` | 收入结构 | - | 降序 |

### 9.3 评分指标（score）

| 指标代码 | 名称 | 说明 |
|---------|------|------|
| `CompScore` | 综合评分 | 综合资金/基本面/风险/技术四个维度 |
| `CapScore` | 资金评分 | 反映主力资金关注度 |
| `FunmScore` | 基本面评分 | 反映公司财务基本面 |
| `RiskScore` | 风险评分 | 反映风险程度（高分代表低风险） |
| `TecScore` | 技术评分 | 反映技术面状况 |

> 评分指标支持 `--type cur/weekly/monthly` 查看当前值或周/月变动值。

### 9.4 范围限定参数（所有指标通用）

| 参数 | 作用 |
|------|------|
| `--universe <板块代码>` | 限定在板块内排行 |
| `--within-label <标签短名>` | 限定在标签结果内排行（如 `shareholder_central_state`） |
| `--within-strategy <策略短名>` | 限定在策略结果内排行（如 `macd_golden`） |
| `--within-event <事件短名>` | 限定在事件结果内排行（如 `shareunlock_next_90`） |

> ⚠️ `--within-label` / `--within-strategy` / `--within-event` **三者互斥**。

