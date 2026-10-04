# 趋势 get_trend（T2）

## 入参

同漏斗：`startDate` / `endDate` / `type=SALES|CUSTOMER`。

## 桶规则（后端，勿自造）

| 条件 | 桶 |
|------|-----|
| 起止同一天，且是今天或昨天 | **小时桶** |
| 其它（近 7 天等） | **日桶** |
| 过长 | 后端约 31 天上限，失败如实转告 |

## 序列字段

| 视角 | 序列 |
|------|------|
| SALES | salesTrend[]：matchCount / quotedCount / repliedCount |
| CUSTOMER | customerTrend[] |

## 回答套路

1. 区间 + 视角 → 整体上行/下行/持平。  
2. 标 1 个异常点。  
3. **今昨同时段**：分别查今天、昨天（各一天），按当前时点对齐累计，勿混整天。  
4. **忙不忙**：今日累计 vs 近 7 日日均（可用日桶算均值）。  
5. 可引导 `get_funnel` 看掉量。
