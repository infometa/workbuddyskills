# 会员域 — 客服配置查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-support.md`；客服开关更新（写操作）见 `customer-service-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.customer-service.config 客服配置查询

---

## ✅ 查询客服配置 — ops.member.customer-service.config

- 商家级微信小程序客服开关；无配置时返回默认 enabled=false

### 入参

无。

### 出参（原始返回）

配置对象：`enabled`（Boolean）、`updatedAt`（yyyy-MM-dd HH:mm:ss）、`updatedBy`。

### 调用示例

```json
{"capability":"ops.member.customer-service.config","input":{},"summary":"查询客服功能开关状态"}
```
