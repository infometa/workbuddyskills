# 商机明细 list_opportunities（T5）

## 入参

| 参数 | 说明 |
|------|------|
| startDate / endDate | 区间 |
| quoteStatus | **0** 未报价 / **1** 已报价 / **3** 已回复 |
| source | 1 群 / 2 全网 / 4 私聊 |
| staffAccountId | 仅管理员筛坐席 |
| queryWord | 关键词 |
| pageNum / pageSize | 分页 |

### 口径注意

- 用户说「报了价客户没回」→ 用 **`quoteStatus=1`**（已报价，尚未成为已回复）。  
- **`quoteStatus=3`** = 客户已回复。  
- 对客勿输出 accountId / openId。

## 出参（可用）

matchTime、originalText、source、aggregateQuoteStatus、representativeStaffName、accurateCount、inaccurateCount、followUpStatus。

## 回答套路

| 意图 | 怎么查 | 怎么讲 |
|------|--------|--------|
| 未报价 / 没接住 | status=0 | 条数+摘要+代表坐席+来源；建议按等待优先 |
| 已报未回 | status=1 | 清单+相对时间；优先跟最久的 |
| 已回复 | status=3 | 客户已回过来的单 |
| 来源对比 | 分 source 查或聚合 | 量表格；不做投放承诺 |
| 识别准不准 | 汇总 accurate/inaccurate | 给占比；误判高则建议抽查 |
| 待办总量 | 分别查 0 与 1 的 total | 两数+合计 |

工具失败不编清单。涉及沉睡/加好友名单 → `list_customer_assets`（见 customer_assets；沉睡为近似）。
