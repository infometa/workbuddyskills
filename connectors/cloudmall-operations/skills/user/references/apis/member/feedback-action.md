# 会员域 — 意见反馈写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-support.md`；反馈列表检索先读 `feedback-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.feedback.handle 处理反馈

---

## ✅ 处理反馈 — ops.member.feedback.handle

- 仅待处理（status=0）可处理，已处理为终态；处理结论先向用户复述

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 反馈 ID |
| handleRemark | String | ✅ | 处理备注（≤300 字） |

### 出参（原始返回）

`data` 为 `null`；已处理的反馈再次处理返回业务错误。回读 `feedback.search` 核验 status=1。

### 调用示例

```json
{"capability":"ops.member.feedback.handle","input":{"id":"1250012345678901234","handleRemark":"已联系用户核实，问题定位为登录超时，下版本修复"},"summary":"处理一条用户反馈"}
```
