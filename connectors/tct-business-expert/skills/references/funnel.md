# 漏斗 get_funnel（T1）

## 入参

| 参数 | 说明 |
|------|------|
| startDate / endDate | 区间；可 `yyyy-MM-dd` |
| type | `SALES` 事件 / `CUSTOMER` 联系人，默认 SALES |
| industry | 可选 |

## 出参解读（销售视角常见）

| 含义 | 常见字段 |
|------|----------|
| 商机/询价数 | matchCount |
| 已报价 / 未报价 | quotedCount / unquotedCount |
| 已回复 / 未回复 | repliedCount / unrepliedCount |
| 报价率 / 回复率 | quoteRate / replyRate |

客户视角以实际返回的 customerView 为准。

## 回答套路

1. 先报时间与视角。  
2. 一句话：量 + 两率 +（可选）环比方向。  
3. 漏斗三级；**掉量**：比较 unquotedCount 与 unrepliedCount。  
4. **进量 vs 承接**：量少→获客；量足两率低→承接。  
5. 引导：下钻 T5 清单，或有权限时 T3 看人。

讲解用业务语言，少堆英文字段名。
