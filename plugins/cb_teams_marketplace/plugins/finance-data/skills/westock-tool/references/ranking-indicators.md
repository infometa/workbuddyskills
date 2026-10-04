# WeStock Tool - 排行选股完整指标速查

> **定位**：本文档是 [SKILL.md](../SKILL.md) `## 排行选股（ranking）` 章节的 **L3 层补充材料**，收纳完整指标清单与 `--min-<字段>` 字段名速查。命令用法和路由请参见 SKILL.md。
>
> **使用方式**：完整且最新清单**必须**执行 `westock-tool ranking --list`；本文档仅作离线快速对照。

---

## 一、可用指标完整清单（5 大分类）

| 分类 | 指标代码 |
|------|---------|
| 评分 | `CompScore`(综合)/`CapScore`(资金)/`FunmScore`(基本面)/`RiskScore`(风险)/`TecScore`(技术) |
| 涨跌停 | `limitup_days`/`limitup_seal_volume`/`limitdn_days`/`limitdn_seal_volume` |
| 财务排行 | `fin_valuation`(估值)/`fin_growth`(成长)/`fin_profit`(盈利)/`fin_pershare`(每股)/`fin_cash_size`(现金流规模)/`fin_operation`(营运)/`fin_liquidity`(偿债)/`fin_profit_structure`(收入结构) |
| 两融排行 | `margin_balance`(两融余额)/`margin_chg_d/w/m/q/y`(日/周/月/季/年变动)/`margin_in_days`(连续扩大天数)/`margin_out_days`(连续缩小天数) |
| 资金流入 | `cap_main_net`(主力净流入)/`cap_retail_net`(散户净流入)/`cap_main_5d`(主力5日合计)/`cap_in_days`(主力连续净流入天数)/`cap_out_days`(主力连续净流出天数) |

---

## 二、`--min-<字段>` 字段名速查

> ⚠️ 指标代码与 `--min-` 拼接的字段名**不一致**，必须查表，不要凭印象拼。

| 指标代码 | `--min-<字段>` 的字段名（数据列名） |
|---------|------------------------|
| `CompScore` / `CapScore` / `FunmScore` / `RiskScore` / `TecScore` | 同名 |
| `limitup_days` | `LimitUpDays` |
| `margin_chg_d/w/m/q/y` | `MChgD` / `MChgW` / `MChgM` / `MChgQ` / `MChgY` |
| `margin_in_days` / `margin_out_days` | `MtInDays` / `MtOutDays` |
| `cap_main_net` | `MainNetIn` |
| `cap_retail_net` | `RetailNetOut` |
| `cap_main_5d` | `MainSum5d` |
| `cap_in_days` / `cap_out_days` | `MainInDays` / `MainOutDays` |
| `fin_valuation` / `fin_profit` / `fin_pershare` | `PE_TTM` / `RoeTTM` / `EpsTTM` |

---

## 三、范围限定（核心能力）

```bash
westock-tool ranking CompScore --within-label shareholder_central_state    # 央企里评分最高
westock-tool ranking fin_valuation --within-strategy macd_golden           # MACD金叉中估值最低
westock-tool ranking CompScore --within-event shareunlock_next_90          # 限售解禁股评分
westock-tool ranking fin_valuation --universe 11010001                     # 板块内估值排行
westock-tool ranking margin_chg_d --universe 11010001 --limit 10           # 板块内两融加仓
westock-tool ranking cap_main_5d --within-label shareholder_central_state  # 央企里主力5日累计加仓最多
```

> `--within-label|--within-strategy|--within-event` **三者互斥**；`--universe` 与 `--within-*` 不同（前者按板块代码限定，后者按 listcode 限定）。

---

## 四、阈值筛选 / 升序 / 历史 / 分页

```bash
westock-tool ranking CapScore --min-CompScore 70 --limit 10
westock-tool ranking CompScore --asc                       # 评分最低
westock-tool ranking CompScore --date 2026-04-20           # 历史日期
westock-tool ranking limitup_days --limit 50 --offset 20
```

---

## 五、命令样例（按指标族分组）

```bash
# ── 评分（score） ──
westock-tool ranking CompScore --limit 10                 # 综合评分 TOP10
westock-tool ranking CompScore --type weekly              # 评分周变动（cur/weekly/monthly）

# ── 涨跌停（market） ──
westock-tool ranking limitup_days                         # 连续涨停天数
westock-tool ranking limitup_seal_volume                  # 涨停封单量

# ── 财务（financial） ──
westock-tool ranking fin_valuation --limit 10             # 估值排行（默认升序看最低 PE）
westock-tool ranking fin_growth                           # 成长能力
westock-tool ranking fin_profit                           # 盈利能力（ROE）

# ── 两融（margin） ──
westock-tool ranking margin_balance --limit 20            # 两融余额最多
westock-tool ranking margin_chg_d                         # 两融日加仓榜（--asc 看日减仓榜）
westock-tool ranking margin_in_days --min-MtInDays 5      # 两融连续扩大≥5天

# ── 资金流入（capital） ──
westock-tool ranking cap_main_net --limit 20              # 主力净流入榜（--asc 看主力净流出榜）
westock-tool ranking cap_main_5d                          # 主力 5 日合计净流入榜
westock-tool ranking cap_in_days --min-MainInDays 3       # 主力连续净流入≥3天
```
