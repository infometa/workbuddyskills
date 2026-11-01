# 会员域 — 意见反馈查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-support.md`；反馈处理（写操作）见 `feedback-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.feedback.search 反馈列表

---

## ✅ 反馈列表 — ops.member.feedback.search

- 敏感接口

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页；pageSize ≤100 |
| feedbackType | String | — | 反馈类型（见出参枚举） |
| memberPhone | String | — | 会员手机号（模糊） |
| status | Integer | — | 0=待处理 / 1=已处理 |
| submitTimeStart / submitTimeEnd | String | — | 提交时间范围（yyyy-MM-dd HH:mm:ss） |

### 出参（原始返回）

分页对象。**关键字段**：`records[].id`（→ handle 路径参数）、`content`、`imageUrls[]`（**元素为结构化对象** `{type: "IMAGE"|"VIDEO", url}`，COS 签名地址）、`handleRemark`、`handleTime`；**枚举字段**：`feedbackType`（PRODUCT_PERFORMANCE-产品性能 / FUNCTION_USAGE-功能使用 / UI_INTERACTION-界面交互体验 / CONTENT_RECOMMENDATION-内容推荐问题 / TRANSACTION_PAYMENT-交易支付问题 / OTHER-其他建议）、`status`（0/1）；**脱敏字段**：`memberPhone`/`contactPhone`（按授权动态脱敏，不得尝试还原）。

### 调用示例

```json
{"capability":"ops.member.feedback.search","input":{"pageNum":1,"pageSize":20,"status":0},"summary":"查询待处理的用户反馈"}
```
