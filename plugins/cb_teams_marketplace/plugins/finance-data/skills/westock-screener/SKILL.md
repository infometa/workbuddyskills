---
version: 1.0.2
name: westock-screener
description: 选股/选基工具——按条件、策略、标签、事件、排行批量筛选股票或 ETF。用户问「哪些股票/帮我选/排行榜/TOP/筛选/MACD金叉/央企/ST/高股息ETF/技术面选股」时使用。只做批量筛选；单股明细用 westock-data。命令清单见 references/scenarios-guide.md。
display_name: 智能选股
display_name_en: westock-screener
description_zh: 由腾讯自选股团队提供。把用自然语言描述的选股逻辑（如“连续放量上涨的题材股”“低估值高股息蓝筹”）转化为可执行的多指标/多策略扫描条件，在全市场范围内批量筛选，输出符合条件的候选股票池。
description_en: 'Provided by Tencent''s Stock team. The stock selection logic described in natural language (such as "thematic stocks with continuous volume increases" and "undervalued high-dividend blue chips") is transformed into executable multi-indicator/multi-strategy scanning conditions, which are then used to batch screen across the entire market and output a pool of candidate stocks that meet the conditions.'
---

# WeStock Screener

## 安装

本技能依赖 `westock` CLI。**首次使用先安装**；**已安装则先检查版本号**，落后时重新执行安装脚本原地升级。

```bash
# 安装脚本已随技能包提供，可先审阅 scripts/ 目录下的文件再执行
# macOS / Linux
bash scripts/setup.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

# 跨平台（Node ≥ 18）
node scripts/setup.cjs
```

安装后执行 `westock --help` 验证；刚安装完命令找不到时，先 `source` 对应 shell profile（如 `~/.zshrc`）使 PATH 生效，再用 `westock` 调用。

> **升级**：已安装时先执行 `westock version --json` 查看当前版本，若落后于本技能包版本，重新执行上面的安装脚本即可原地升级。

> **安装判断交给脚本**：直接执行 `bash scripts/setup.sh`，无需先手动检查 `westock` 是否存在。
> 若仍报 `command not found`，先 `source` shell profile 使 PATH 生效；
> 不要 `export PATH`、猜路径或 `find /` 找二进制；反复重装仍失败则如实告知。

> **安全说明**：安装脚本自动执行 SHA256 校验（校验值随包内 `scripts/` 或与官方源一同分发），无需手动验证。

---

**调用方式**：`westock <子命令> [参数]`

- 统一 Go CLI；子命令列表见 `westock --help`
- 无脚本入口，只能通过 `westock` 命令调用
- 需网络

```bash
westock screen strategy --type macd_golden --limit 20
westock screen ranking --type CompScore --limit 10
westock screen condition --expression "intersect([PE_TTM > 0, PE_TTM < 20, ROETTM > 15])"

```

---

## 参考文档（仅不确定时查阅，禁止每次任务都读）

- [scenarios-guide.md](./references/scenarios-guide.md) — 路由与场景速查
- [ai_usage_guide.md](./references/ai_usage_guide.md) — 完整命令语法
- [ranking-indicators.md](./references/ranking-indicators.md) — 排行指标与 `--min-<字段>`
- [fields-guide.md](./references/fields-guide.md) — 筛选字段（沪深 vs 港美）
- [etf-pools.md](./references/etf-pools.md) — ETF 主题池与选基指标

---

## 核心铁律

1. **禁止绕过**——不用 HTTP 直连、网页搜索、手搓筛选（先 westock 拉数据再 Python 排序是反模式）。
2. **"哪些 X 可以用"必须 `--list`**——`westock screen event --list` / `westock screen label --list` / `westock screen strategy --list` / `westock screen ranking --list`、`westock screen condition --list-presets`，不要凭记忆列举。
3. **5 命令路由**——条件 → `westock screen condition`（`--preset` 使用预设）；策略 → `westock screen strategy`；标签 → `westock screen label`；事件 → `westock screen event`；排行 → `westock screen ranking`。
4. **概念股 ≠ 选股**——"XX 概念股" 用 `westock search <关键词> --type sector`。

---

## 与 westock 边界

| 用户意图 | 用哪个 |
|---------|--------|
| 哪些股票 XX / 最近 N 天 XX 的股票 | **westock-screener**（event/label/strategy/ranking） |
| 某只股票 XX 明细 / 某天全市场清单 | **westock-data**（calendar/lhb/notice 等） |
| 板块/行业估值、盈利预测、财务 TTM | **westock-data**（`westock sector valuation` / `westock sector forecast` / `westock finance`） |

---

## 已知限制

- 市场：沪深 A股、港股、美股；**不支持北交所**
- 字段名分市场：A股与港美不同（如 `PE_TTM` vs `PeTTM`），**切勿混用**；详见 [fields-guide.md](./references/fields-guide.md)
- PE/PB 负值须排除：A股常用 `PE_TTM > 0`，港美按对应字段写正值约束；港股/美股加 `--market hk` / `--market us`
- 多条件 AND → `intersect([...])`；OR → `union([...])`

---

## 高频命令速查

```bash
westock screen condition --expression "intersect([PE_TTM > 0, PE_TTM < 20, ROETTM > 15])"
westock screen condition --preset WhiteHorseGrowth
westock screen strategy --type macd_golden 
westock screen label --type shareholder_central_state 
westock screen event --type shareunlock_next_90 
westock screen ranking --type CompScore --limit 10
westock screen ranking --type CompScore --within-label shareholder_central_state
westock screen ranking --type north_active_d                    # 北向活跃榜：固定 Top20，勿加 --limit
westock screen label --type high_dividend --asset etf     # 仅 ETF；股票高股息见 westock screen condition --preset HighDividend
westock screen ranking --type size --asset etf --limit 20

```

**通用参数**：`--limit`/`--offset`、`--start`/`--end`

---

## 子命令参数矩阵（与实现一致，禁止跨子命令套用）

| 子命令 | 选择参数 | 时间 | 分页/排序 | 特有参数 |
|--------|----------|------|-----------|----------|
| `screen condition` | `--expression` ｜ `--preset`；`--list-presets` | `--date` | `--limit`、`--orderby [--asc\|--desc]` | `--sector`、`--market hs\|hk\|us`；**无 `--offset`** |
| `screen strategy` | `--type`（逗号多个）、`--list` | `--date` ｜ `--start`/`--end` | `--limit`、`--offset` | — |
| `screen label` | `--type`（逗号多个）、`--list [分组]` | `--date` ｜ `--start`/`--end` | `--limit`、`--offset` | `--asset stock\|etf` |
| `screen event` | `--type`（逗号多个）、`--list [分组]` | **无时间 flag**（窗口内嵌 type 名，如 `_past_30`/`_next_90`） | `--limit`、`--offset` | — |
| `screen ranking` | `--type`、`--list` | `--date` | `--limit`、`--offset`、`--orderby [--asc\|--desc]`、`--period cur\|weekly\|monthly` | `--asset stock\|etf`、`--sector`、`--within-label` / `--within-strategy` / `--within-event`（三者互斥）、`--min-<字段>` |

**并发与输出纪律**：无依赖的筛选/排行可同轮并行；主题未拿到板块 code 前不要并发多条 `screen condition`。**禁止终端截断**——不要用 `| grep`/`| head`/`| tail`/`| sed` 或 `&&`/`;` 链处理 CLI 输出，条数/分页只用上表列出的参数。

---

## ETF 硬性规则筛选（默认路径）

用户给出**固定数值门槛**筛选行业/主题 ETF（规模、日均成交、上市时间、区间涨幅、估值分位、资金等）时：

1. （可选）`screen label --list --asset etf` 仅当需核对主题池名称时调 1 次。
2. **同轮并行** `screen ranking`（`--asset etf`，每条 `--limit` ≤50，禁止超大值翻页穷举）：
   - `westock screen ranking --type size --asset etf`（规模）
   - `westock screen ranking --type qt_chg_interval --asset etf --orderby ChgPct20D`（区间涨幅）
   - `westock screen ranking --type amt_interval --asset etf`（流动性）
   - `westock screen ranking --type valuation_pct --asset etf --orderby PE_TTM_PCT`（估值分位）
3. 在内存中按用户规则取交集得 **≤10 只候选**，再 1～2 次批量 `westock quote` / `westock etf profile` 核验。
4. **候选池形成后即交付**（含数据日期与未验证项）。

---

## 关键提醒

- **`westock screen condition --list-presets` ≠ `westock screen strategy --list`**
- **排行指标名禁止猜**——`--type` 取值以 `westock screen ranking --list` 实时返回为准；ETF 指标（`size` / `qt_chg_interval` / `amt_interval` / `valuation_pct` / `qt_daily` 等）**必须加 `--asset etf`**，否则报「未知指标」。
- **ranking 阈值用 `--min-<字段>`**（如 `--min-CompScore 70`），`--limit` 只是条数
- **"央企"** → `shareholder_central_state`；口语"国企" → `shareholder_local_state`
- **"高股息"同名不同义**——股票 → `westock screen condition --preset HighDividend`（或 `HighDividendLowValuation`）；ETF → `westock screen label --type high_dividend --asset etf`（`high_dividend` 是 **ETF 主题池**，仅 `--asset etf` 适用，勿在股票语境直接用）

---

## 条件选股预设（封闭集，拿不准先 `westock screen condition --list-presets`）

> 预设名是**封闭集**，以 `--list-presets` 实时返回为准，**不要臆造**（如没有 `LowValuation`，低估值用 `LowPE`/`LowPB`）。完整清单直接跑该命令查名。

| 常问预设 | 含义 |
|------|------|
| `HighDividend` | 高股息（**股票**；ETF 高股息见 `westock screen label --type high_dividend --asset etf`） |
| `HighDividendLowValuation` | 高股息 + 低估值 |
| `LowPE` | 低市盈率 |
| `LowPB` | 低市净率 |
| `HighROE` | 高 ROE |
| `HighGrowth` | 高成长 |

---

## 异常与空结果

1. **`command not found`**：重跑 `bash scripts/setup.sh` 后重试。
2. **命令失败（其他）**：如实转述，禁止编造筛选结果。
3. **空列表**：说明「当前条件下无匹配」；检查表达式、字段名、正值约束和市场参数。
4. **禁止**：失败后手搓筛选或改用 web_search。

---

## 重要声明

> 本技能仅提供客观数据筛选，不构成投资建议。数据可能有延迟，以交易所官方为准。投资有风险，决策需谨慎。

**数据来源**：腾讯自选股选股接口