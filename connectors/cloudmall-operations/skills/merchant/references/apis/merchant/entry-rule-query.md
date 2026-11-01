# 商户域 — 进店规则查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-entry.md`；写操作见 `entry-rule-action.md`。
> 进店规则决定 C 端用户进入哪个门店：按优先级依次尝试（1 最高）。固定区域规则数据见 `area-config-query.md`（固定区域部分）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：entry-rule.list 进店规则列表

---

## ✅ 进店规则列表 — ops.merchant.entry-rule.list

- **语义**：全量规则，按优先级升序返回

### 入参（无）

### 出参（数组，原始数据）

- **关键字段来源**：`id`（→ 状态/参数更新的 `input.id`）、`params`（JSON 字符串，见 `entry-rule-action.md` update-params 参数分支）
- **枚举字段**：`ruleType`（六类，见 `merchant-enums.md` 进店规则字典）、`enabled`（boolean）、`draggable`（boolean，**仅 DEFAULT_STORE 为 false**，PARAM_STORE 可拖拽重排）
- **格式敏感字段**：`priority`（整数，越小优先级越高）、`params`（JSON 字符串，前端负责解析；DEFAULT_STORE 规则的 params 含 defaultStoreId/defaultStoreName）
- `summary` 为服务端聚合的规则摘要文本。

### 调用示例

```json
{"capability":"ops.merchant.entry-rule.list","input":{},"summary":"查看进店规则与当前优先级"}
```

---

## ⛔ 未开放

| 操作 | 原因 |
|------|------|
| 规则新增/删除 | 规则类型为系统预置六类，后端未提供增删端点 |
