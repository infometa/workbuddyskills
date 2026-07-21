# yahoo-finance-cli

行情洞察与市场趋势发现专家 —— 基于 WorkBuddy 原生 `westock-data` 能力的全球金融行情查询专家包。

## 简介

本专家包将原 `yahoo-finance-cli`（依赖外部 `yf` CLI 与 `yahoo-finance2`）改造为 **wb-native 接入型**：核心能力完全由 WorkBuddy 内置的 `westock-data` 提供支持。

- 查询时直接调用 `node <SKILL_DIR>/index.js <子命令>`，`<SKILL_DIR>` 为 wb 运行时内置路径。
- 凭证由 WorkBuddy 自动获取，**用户无需提供任何外部 key、无需安装任何软件**。
- 无地域限制，开箱即用。

## 核心能力

| 子命令 | 用途 |
| --- | --- |
| `price <SYMBOL>` | 实时价格快照 |
| `quote <SYMBOL>` | 详细报价（买/卖价、成交量、52 周区间、市值） |
| `fundamentals <SYMBOL>` | 公司资料、PE/EPS/利润率/ROE、企业价值、流通股 |
| `earnings <SYMBOL>` | 下次财报日、EPS 预期、历史业绩惊喜 |
| `ratings <SYMBOL>` | 买入/持有/卖出分布、均值评级、升降级 |
| `insights <SYMBOL>` | 技术面与基本面估值、前景研判 |
| `history <SYMBOL> <RANGE>` | 历史 OHLCV（`1d/5d/1mo/3mo/6mo/1y/2y/5y/10y/ytd/max`） |
| `trending <REGION>` | 当前最热门的交易标的（如 `US`/`HK`/`GB`） |
| `search "<关键词>"` | 按公司/资产名模糊匹配交易标的 |
| `compare <T1>,<T2>,<T3>` | 并排对比价格、涨跌、52 周区间、市值 |

## 符号格式约定

- 美股：`AAPL`
- 港股：`0700.HK`
- 印度 NSE：`RELIANCE.NS`
- 加密货币：`BTC-USD`
- 外汇：`EURUSD=X`
- ETF：`SPY`

## 改造说明

原 skill 通过外部 `yf`（`yahoo-finance2`）CLI 与 `jq` 获取行情。改造后所有外部依赖被 WorkBuddy 原生 `westock-data` 能力替代：

- 原 `yf quote` → `node <SKILL_DIR>/index.js quote`
- 原 `yf quoteSummary '{"modules":[...]}'` → `fundamentals` / `earnings` / `ratings` 模块化命令
- 原 `yf insights` → `node <SKILL_DIR>/index.js insights`
- 原 `yf chart` / `yf historical` → `node <SKILL_DIR>/index.js history`
- 原 `yf trendingSymbols` → `node <SKILL_DIR>/index.js trending`
- 原 `yf search` → `node <SKILL_DIR>/index.js search`

## 免责声明

本专家通过 WorkBuddy 原生 `westock-data` 能力获取行情数据，数据来源于第三方行情源，可能存在延迟；重要决策请以官方交易所数据为准。本专家仅提供客观数据与解读，不构成投资建议。

> ⚠️ 以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。
