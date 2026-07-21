# westock-tool → westock-mcp 工具映射

本技能通过 **westock-mcp** 连接器的 `tool_*` 系列 MCP Tool 完成选股，不再运行本地 `scripts/`。

返回格式：`{ "ok": true|false, "data": ..., "message": "..." }`。`ok: false` 时原样转述 `message`，禁止编造。

## 核心映射

| 场景 | MCP Tool | 主要参数 |
|------|----------|----------|
| 条件选股 | `tool_filter` | `expression` 或 `preset`, `date`, `limit`, `market`, `orderby`, `order`, `universe` |
| 列出预设 | `tool_list_presets` | 无必填 |
| 策略选股 | `tool_strategy` | `names`(逗号分隔), `date`, `start`, `end`, `limit`, `offset` |
| 列出策略 | `tool_list_strategies` | `group` |
| 标签选股 | `tool_label` | `names`(逗号分隔), `date`, `start`, `end`, `limit`, `offset`, `asset` |
| 列出标签 | `tool_list_labels` | `asset`, `group` |
| 事件驱动选股 | `tool_event` | `names`, `limit` |
| 列出事件 | `tool_list_events` | `group` |
| 多因子排行 | `tool_ranking` | `metric`, `limit`, `min_fields` |
| 列出排行指标 | `tool_list_ranking_metrics` | `asset`, `group` |

## 命令路由

| 用户意图 | 使用 Tool |
|----------|-----------|
| 策略名称（MACD金叉、早晨之星） | `tool_strategy` |
| 分类标签（央企、ST、新股） | `tool_label` |
| 自定义条件（PE<20 且 ROE>15） | `tool_filter` expression |
| 预设函数（低PE、高股息） | `tool_filter` preset |
| 概念股成份股 | ❌ 不属于本技能，用 `data_sector`（westock-data） |

## 表达式语法

| 语法 | 示例 |
|------|------|
| 单条件 | `ClosePrice >= 100` |
| AND | `intersect([PE_TTM > 0, PE_TTM < 20, ROETTM > 15])` |
| OR | `union([ChangePCT > 5, Chg5D > 10])` |

> 多条件 AND **必须用 `intersect([...])`**，不支持 `&` / `&&` / `AND`。

## 市场参数

- 沪深：默认 `market=hs` 或不传
- 港股：`market=hk`
- 美股：`market=us`
- 策略/标签选股仅支持 A 股

## 旧 CLI 对照

| 旧 CLI | 新 MCP |
|--------|--------|
| `westock-tool filter "PE_TTM < 20"` | `tool_filter` expression=... |
| `westock-tool filter --preset LowPE` | `tool_filter` preset=LowPE |
| `westock-tool filter --list-presets` | `tool_list_presets` |
| `westock-tool strategy macd_golden` | `tool_strategy` names=macd_golden |
| `westock-tool strategy --list` | `tool_list_strategies` |
| `westock-tool label shareholder_central_state` | `tool_label` names=shareholder_central_state |
| `westock-tool label --list` | `tool_list_labels` |
