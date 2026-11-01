# 商户域 — 客服配置查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-config.md`；写操作见 `call-service-config-action.md`。
> 客服配置为**租户级单例**：电话客服开关 + 客服电话 + 服务时间文本。出参为上游**原始业务数据**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：call-service-config.get 查询客服配置

---

## ✅ 查询客服配置 — ops.merchant.call-service-config.get

- **语义**：未配置过时 `data` 为 null（不是错误）

### 入参（无）

### 出参（原始数据）

- **枚举字段**：`enabled`（boolean）
- **明文字段**：`phoneNumber` 为**完整明文**返回（运营端编辑回显需要；脱敏仅发生在操作日志中）——向用户展示时注意这是完整号码

### 调用示例

```json
{"capability":"ops.merchant.call-service-config.get","input":{},"summary":"查看电话客服配置"}
```
