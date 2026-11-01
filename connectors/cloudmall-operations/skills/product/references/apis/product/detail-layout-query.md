# 商品域 — 商详页装修查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-detail.md`；写操作（编辑锁/配置保存）见 `detail-layout-action.md`；FAQ 维护见 `faq-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：detail-layout.config-get 装修配置查询 · detail-layout.logs 装修操作日志

---

## ✅ 配置查询 — ops.product.detail-layout.config-get

- **语义**：获取当前租户商详页模块排序与启停配置；无配置时返回默认顺序。返回附带编辑锁状态（`locked`/`lockedBy`）。

### 入参

无（空对象 `{}`）。

### 出参（原始数据）

- **枚举字段**：`modules[].moduleCode`（9 个合法值：`benefit_info` / `delivery_info` / `nearby_store` / `product_params` / `product_review` / `faq` / `collocation` / `product_detail` / `price_explanation`）
- `modules[]`：`moduleCode`、`sortOrder`（1~9）、`enabled`
- `locked`（是否被他人持有编辑锁）、`lockedBy`（持锁人）
- ⚠️ 读侧兼容：`benefit_info` 为 2026-09 新增模块，存量配置自动补全（enabled=true 追加尾部）——返回可能是 9 个模块。

### 调用示例

```json
{"capability":"ops.product.detail-layout.config-get","input":{},"summary":"查看商详页模块配置与锁状态"}
```

---

## ✅ 操作日志 — ops.product.detail-layout.logs

- **语义**：最近 20 条配置操作日志（按时间倒序，无分页），含变更前后快照。

### 入参

无（空对象 `{}`）。

### 出参（数组，原始数据）

- **格式敏感字段**：各时间字段（yyyy-MM-dd HH:mm:ss）
- 条目含操作人、时间、before/after 模块快照。

### 调用示例

```json
{"capability":"ops.product.detail-layout.logs","input":{},"summary":"查看商详配置最近操作记录"}
```
