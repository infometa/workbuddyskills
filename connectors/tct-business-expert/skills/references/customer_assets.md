# 客户资产 list_customer_assets（T6）

用于查**客户联系人名单**（与工作台「客户资产」同口径：按联系人去重）。

## assetTab

| 值 | 含义 | 时间/维度 |
|----|------|-----------|
| 1 | 全部资产（至少一名业务员已加好友） | 一般不带 inquiryOccur / dimensions |
| 2 | 潜在资产（范围内均未加好友） | 同上 |
| 3 | 活跃资产（区间内有询价） | 可用 `inquiryOccurStartTime/EndTime`、`dimensions` |

**三类名单互不替代：**
- 问潜在 → 必须 `assetTab=2` 的返回再答；不得用 `assetTab=1` 名单猜谁是潜在。  
- 问活跃 → 必须 `assetTab=3`（通常带时间）的返回再答。  
- `assetTab=2/3` 若为空：只说该类暂无数据；**禁止**拿全部资产结果「凭印象」重分类。  
- 要同时报全部/潜在/活跃数量或名单 → **各查一次**，分别引用各自的 `total`/rows。

## 常用筛参

| 参数 | 说明 |
|------|------|
| friendFlag | 1 好友 / 0 非好友 |
| dimensions | OR：1有询价 2有报价(未回) 3有回复 4未报价 |
| accountIds | 管理员空=全员或单选一人（字符串 accountId）；业务员强制本人 |
| sortName | offer_count / friend_add_time / first_offer_time / last_c2c_match_time 等 |
| keyWord | 昵称/公司 |

## 出参解读（对客）

可用：nickname、company、friendFlag、friendAddTime、firstOfferTime、lastC2cMatchTime、offerCount、quoteCount、replyCount、staffName、staffCount、customerLabel。

**勿对客输出：** qqOpenId、手机、userid、customerId、accountId。

- `orderCount`：不讲成交（走 G01）。
- 「已回复联系人**数**」汇总优先 **T4**；单行 `replyCount` 为日表次数。
- `staffCount>1`：多名业务员关联，展示「N位」，本期不下钻扁平明细。

## 沉睡 / 只询一次 / 转化

| 意图 | 做法 | 限制 |
|------|------|------|
| 沉睡（超 N 天没询价） | 按最后询价时间排序后分页，再按距今天数过滤 | 无法一键筛「刚好超 N 天」的全量；可能不全，须声明近似 |
| 只询一次 | 活跃 Tab + 时间 + 看 offerCount=1，或排序后筛 | 精确全量依赖翻页 |
| 加好友转化 | 拉好友名单，按 offerCount>0 或 firstOffer 相对 friendAdd 聚合 | 注明「按明细聚合、非预置指标」 |
| 白加（加了未跟） | friendFlag=1 且报价相关维度/次数为 0 | 按页解释 |

## 与 T4/T5

- T4：联系人维度**汇总排名**；T6：客户**名单明细**。
- T5：商机事件清单；T6：客户资产联系人。
