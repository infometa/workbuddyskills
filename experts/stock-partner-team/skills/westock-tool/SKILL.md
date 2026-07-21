---
name: westock-tool
description: 通过 westock-mcp 连接器进行条件选股/策略选股/标签选股。触发词：筛选股票、选股、MACD金叉策略、央企有哪些、破净股、低PE高ROE。需已连接 westock-mcp 连接器。查个股详情用 westock-data，查概念成份股用 data_sector。
---

# WeStock Tool（MCP 模式）

**作用**：通过 **westock-mcp** 连接器的 `tool_*` MCP Tool 完成三种选股——条件选股、策略选股、标签选股。

> **前置条件**：专家包已声明 `dependencies.connectors: ["westock-mcp"]`。

> **连接器已连接时（铁律）**：选股**必须且只能**调用连接器的 `tool_*` MCP Tool。**禁止**运行本地 `scripts/`、**禁止** WebSearch 替代选股/筛选结果、**禁止**使用其他 skill 或 MCP 取数。westock-tool 技能仅提供「何时调哪个 Tool」的方法论，实际取数通道只有 westock-mcp。

> **腾讯自选股连接器未连接时**：无法调用 `tool_*` Tool。降级使用 WebSearch 及环境中其他可用 skill/MCP 取数，**筛选能力无法保证**；主理人会在 chat 单独提示「腾讯自选股连接器未连接」。

> **工具分工**：
> - **westock-tool**（本技能）：筛选/选股——找出满足条件的股票列表
> - **westock-data**：查个股详情、板块/概念成份股（`data_sector`）
> - 用户自选股：`portfolio_*` Tool

**返回处理**：MCP 返回 `{ ok, data, message }`。将 `data` 转为 Markdown 表格展示，禁止直接输出原始 JSON。

完整映射见 [references/mcp-tool-map.md](./references/mcp-tool-map.md)。

---

## 命令路由

| 用户说法 | MCP Tool |
|----------|----------|
| 策略名（MACD金叉、早晨之星） | `tool_strategy` |
| 分类标签（央企、ST、新股） | `tool_label` |
| 自定义条件（PE<20 且 ROE>15） | `tool_filter` expression |
| 预设（低PE、高股息） | `tool_filter` preset |
| XX概念有哪些股票 | ❌ 用 `data_sector`（westock-data） |

---

## 条件选股 tool_filter

```
tool_filter  expression=intersect([PE_TTM > 0, PE_TTM < 20, ROETTM > 15])
tool_filter  expression=ClosePrice >= 100  date=2026-03-12  limit=20
tool_filter  expression=...  market=hk      # 港股
tool_filter  expression=...  market=us      # 美股
tool_filter  expression=...  orderby=ROETTM  order=desc
tool_filter  preset=LowPE  limit=20
tool_filter  preset=HighDividend  market=hk
tool_list_presets                           # 列出全部预设
```

| 参数 | 说明 |
|------|------|
| expression / preset | 二选一 |
| date | YYYY-MM-DD，默认今天 |
| limit | 默认 20 |
| market | hs / hk / us |
| orderby / order | 排序字段与方向 |
| universe | 板块码限定范围（先 `data_search` 或 `data_sector` 获取） |

### 表达式语法

| 语法 | 示例 |
|------|------|
| 单条件 | `ClosePrice >= 100` |
| AND | `intersect([PE_TTM > 0, PE_TTM < 20])` |
| OR | `union([ChangePCT > 5, Chg5D > 10])` |

> ⚠️ 多条件 AND **必须用 `intersect([...])`**，不支持 `&` / `AND`

---

## 策略选股 tool_strategy

```
tool_list_strategies                        # 列出全部策略
tool_strategy  names=macd_golden
tool_strategy  names=macd_golden  date=2026-04-10  limit=30
tool_strategy  names=high_dividend,pb_roe   # 多策略分别返回
tool_strategy  names=macd_golden  start=2026-04-01  end=2026-04-10  # 区间
```

仅支持 A 股。查多天趋势用 `start`/`end`，不要多次 `date` 调用。

---

## 标签选股 tool_label

```
tool_list_labels
tool_list_labels  group=股东属性
tool_label  names=shareholder_central_state   # 央企
tool_label  names=risk_st  limit=50           # ST 股
tool_label  names=listeddate_5days            # 新股
tool_label  names=shareholder_central_state  start=2026-04-01  end=2026-04-10
```

仅支持 A 股。多标签逗号分隔时**分别返回**各自列表，不做交集。

---

## 已知限制

| 限制项 | 说明 |
|--------|------|
| 市场 | 条件选股支持 hs/hk/us；策略/标签仅 A 股 |
| 市值单位 | 沪深 `TotalMV` 为元，港美为亿元 |
| 字段名 | 港美估值字段与沪深不同，见 fields-guide |
| PE/PB | 亏损股为负，筛选须 `PE_TTM > 0` |
| 北交所 | 不支持 |

---

## 常用字段速查

| 类别 | 沪深 | 港股 | 美股 |
|------|------|------|------|
| 市盈率 TTM | PE_TTM | PeTTM | PeTTM |
| 市净率 | PB | PbLF | PbLF |
| 收盘价 | ClosePrice | ClosePrice | ClosePrice |
| 涨跌幅 | ChangePCT | ChangePCT | ChangePCT |
| 总市值 | TotalMV(元) | TotalMV(亿) | TotalMV(亿) |
| ROE | ROETTM | RoeWeighted | ROE |

完整字段见 [references/fields-guide.md](./references/fields-guide.md)。

---

## 典型示例

```
tool_strategy  names=macd_golden
tool_label  names=shareholder_central_state
tool_filter  expression=intersect([PE_TTM > 0, PE_TTM < 15, ROETTM > 15])  orderby=ROETTM  order=desc
tool_filter  expression=intersect([PB > 0, PB < 1])
tool_filter  preset=HighDividend  market=hk
```

更多场景见 [references/scenarios-guide.md](./references/scenarios-guide.md)。

---

## 重要声明

> 1. 本技能仅提供客观数据筛选与展示，不构成投资建议。
> 2. 数据每日收盘后更新，可能有延迟。
> 3. 投资有风险，决策需谨慎。

**数据来源**：腾讯自选股 westock-mcp 连接器
