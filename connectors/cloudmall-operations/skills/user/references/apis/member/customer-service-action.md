# 会员域 — 客服配置写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-support.md`；客服配置现值读取先读 `customer-service-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.customer-service.config-save 更新客服配置

---

## ✅ 更新客服配置 — ops.member.customer-service.config-save

- upsert 语义

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Boolean | ✅ | 客服功能开关（true=开启 / false=关闭，**布尔**） |

### 出参（原始返回）

`data` 为 `null`；回读 `customer-service.config` 核验。

### 调用示例

```json
{"capability":"ops.member.customer-service.config-save","input":{"enabled":true},"summary":"开启小程序在线客服"}
```
