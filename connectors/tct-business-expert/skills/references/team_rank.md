# 团队榜（T3 / T4）

## get_team_sales（事件维度）

按业务员计询价/报价/回复**条数**（同一客户多次会重复计）。

| sortField | 用途 |
|-----------|------|
| inquiryNum | 谁询价多/少 |
| quoteNum | 产出/勤奋（配合两率） |
| replyNum | 客户已回条数相关量 |

出参：rankNo、staffName、inquiryNum、quoteNum、replyNum、quoteRate、replyRate。  
两率=百分比整数。非管理员仅本人；管理员可 `accountIdList`。

**讲法：** 姓名+数值表；低样本提示；G22 中性；可下钻 T5。

## get_team_customer（联系人维度）

| sortField | 用途 |
|-----------|------|
| inquiryContactNum | 客户活跃（来问的人数） |
| quoteContactNum / replyContactNum | 报价/客户回复人数 |
| newFriendInquiryContactNum / newNonFriendInquiryContactNum | 新好友/非好友询价联系人 |

出参含 quoteContactRate、replyContactRate。  
「已回复联系人」= **客户回过来**。

**客户沉默：** 按 replyContactRate（或 reply/quote）升序取末位。  
**过程质量：** 高回复率+新增等；声明非成交额（G01）。

## 组合

- 两人 PK：T3+T4，同名先确认（G20）。  
- 勤奋：T3 为主；懒/忙：T3+T5 待办。  
- 仅 T4 **不能**替代 T6 的客户名单明细；名单/沉睡/好友转化用 `list_customer_assets`（见 `customer_assets.md`）。
