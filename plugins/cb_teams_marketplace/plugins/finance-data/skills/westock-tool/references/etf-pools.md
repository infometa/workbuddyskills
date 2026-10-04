# WeStock Tool - ETF 选基速查

> **定位**：本文档是 [SKILL.md](../SKILL.md) ETF 选基章节的 **L3 层补充材料**，收纳全部 ETF 主题池与排行指标速查表。命令用法和基本路由请参见 SKILL.md。
>
> **使用方式**：
> - 完整且最新清单**必须**执行 `westock-tool label --asset etf --list` / `westock-tool ranking --list --asset etf`
> - 本文档仅作离线快速对照，**示例性条目**（不全）

---

## 一、ETF 主题池速查（label --asset etf）

| 分类 | 代表性池 |
|------|----------|
| 上市时间 | `issue_new`(最新发行)、`issue_in_3m`(新发3月内)、`issue_in_1y`(新发1年内)、`issue_over_5y`(5年老基) |
| 规模 | `size_1000`(千亿)、`size_500`(500亿)、`size_100`(百亿) |
| 获奖 | `award_golden_bull`(得过金牛)、`award_golden_bull_1y`(刚得金牛)、`award_all`(得过奖)、`award_all_1y`(刚得奖) |
| 持仓特征 | `high_stib_bj`(科创北证占比高)、`high_minicap`(微盘占比高)、`high_supercap`(超级大盘占比高)、`high_price_stocks`(百元股占比高) |
| 行情表现 | `qt_high_chg`(高涨幅)、`qt_high_vol`(高成交)、`qt_high_amp`(高振幅)、`qt_high_volratio`(高量比)、`qt_high_unitnv`(高价) |
| 重仓股表现 | `stocks_high_up`、`stocks_high_super_bullish`(超牛重仓)、`stocks_high_bullish` |
| 主力资金 | `cap_focus_daily/weekly/monthly/quarterly/yearly`(主力看好) |
| 基本面 | `low_valuation`(低估值)、`high_dividend`(高股息)、`high_roe` |
| 诊股评分 | `high_score_comp/tec/cap/sentiment/fundamental/risk` |
| 境外/特殊 | `t0`(可T+0)、`america`、`euro`、`japan`、`hk` |
| 类型/策略 | `commodity`(商品型)、`bond`(债券型)、`currency`(货币型)、`strategy_div`(红利) |

> 完整池清单：`westock-tool label --asset etf --list`

---

## 二、ETF 排行指标速查（ranking --asset etf）

| 指标 | 中文 | 默认排序字段 | 默认方向 | 可选字段 |
|------|------|-----------|---------|---------|
| `size` | ETF 规模 | `TotalAsset` | ↓ | TotalAsset/NetValue/NetValueTotal |
| `nvsize_interval` | ETF 总规模波动 | `EtfSize` | ↓ | EtfSize |
| `valuation` | 估值绝对值 | `PE_TTM` | ↑ | PE_TTM/PB/PS_TTM/PCF_TTM/PEG/ROE/DIV_TTM |
| `valuation_pct` | 估值历史百分位 | `PE_TTM_PCT` | ↑ | PE_TTM_PCT/PB_PCT/PS_TTM_PCT/PCF_TTM_PCT/PEG_PCT/ROE_PCT/DIV_TTM_PCT |
| `qt_daily` | 单日行情 | `ChgPct` | ↓ | ChgPct/TurnoverRate/TurnoverValue |
| `qt_chg_interval` | 区间涨跌 | `ChgPct20D` | ↓ | ChgPct/ChgPct5D/ChgPct20D/ChgPct60D/ChgPct52W/ChgPctYtd |
| `turn_interval` | 换手率波动 | `EtfTurnoverRAvgM` | ↓ | EtfTurnoverR/...AvgW/AvgM/AvgQ/AvgY |
| `amt_interval` | 成交额波动 | `EtfTurnoverAvgM` | ↓ | EtfTurnover/...AvgW/AvgM/AvgQ/AvgY |
| `disc_interval` | 溢折率波动 | `EtfDiscAvgM` | ↓ | EtfDisc/...AvgW/AvgM/AvgQ/AvgY |

> 完整指标清单：`westock-tool ranking --list --asset etf`

---

## 三、常用命令样例

```bash
# 标签筛选（label）
westock-tool label high_dividend --asset etf                   # 高股息 ETF
westock-tool label low_valuation,high_roe --asset etf          # 多池并查
westock-tool label size_100 --asset etf --limit 50 --offset 50 # 百亿基金分页

# 横截面排行（ranking）
westock-tool ranking size --asset etf --limit 20               # 规模榜 TOP20（默认 TotalAsset 降序）
westock-tool ranking valuation --asset etf --orderby PB --asc       # 估值最低（按 PB 升序）
westock-tool ranking valuation_pct --asset etf --orderby PE_TTM_PCT # 估值百分位最低（默认升序）
westock-tool ranking qt_chg_interval --asset etf --orderby ChgPct20D # 近 20 日涨幅榜
westock-tool ranking turn_interval --asset etf --orderby EtfTurnoverRAvgM # 月均换手率榜
westock-tool ranking disc_interval --asset etf --orderby EtfDiscAvgW # 周均溢价榜
```

---

## 四、决策入口

- 用户带"标签/主题"（如"高股息 / 千亿基金 / 科创板占比高"）→ `label ... --asset etf`
- 用户带"排序/榜单"（如"规模最大 / 涨幅前 10 / 估值最低"）→ `ranking ... --asset etf`
- 跨市场行情/单只 ETF 详情 → 改用 `westock-data etf detail/holdings/...`
