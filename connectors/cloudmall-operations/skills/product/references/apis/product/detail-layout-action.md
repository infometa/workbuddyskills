# 商品域 — 商详页装修写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-detail.md`；现态读取（配置与锁状态）先读 `detail-layout-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：detail-layout.lock-acquire 获取编辑锁 · detail-layout.lock-release 释放编辑锁 · detail-layout.config-save 装修配置保存

---

## ✅ 获取编辑锁 — ops.product.detail-layout.lock-acquire

- **语义**：获取商详装修配置的**编辑锁**（Redis 租户级，TTL 10 分钟）。保存配置前必须持锁，否则被拒。
- 拿锁成功 → `locked=false`；被他人持有 → `locked=true, lockedBy=<持锁人 userId>`（仍是 200 + 业务数据，非报错）。
- **同一用户重复 acquire = 续租**（刷新 TTL）；锁 10 分钟无续租自动过期。

### 入参

无（空对象 `{}`）。

### 出参

- `locked`（是否已被他人持有）、`lockedBy`（持锁人；自己拿锁成功时为 null）。

### 调用示例

```json
{"capability":"ops.product.detail-layout.lock-acquire","input":{},"summary":"获取商详配置编辑锁"}
```

---

## ✅ 释放编辑锁 — ops.product.detail-layout.lock-release

- **语义**：释放编辑锁（校验 lockValue=当前用户，非持锁人释放无效）。保存完成后应释放，避免他人等待锁过期。

### 入参

无（空对象 `{}`）。

### 调用示例

```json
{"capability":"ops.product.detail-layout.lock-release","input":{},"summary":"释放商详配置编辑锁"}
```

---

## ✅ 配置保存 — ops.product.detail-layout.config-save

- **语义**：全量替换保存商详模块排序与启停（删旧+插新+写日志）。**服务端强校验当前用户持锁**（未持锁直接拒绝）；模块须覆盖全部 9 个合法 code、sortOrder 1~9 连续不重复、至少 1 个 enabled。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| modules | List | ✅ | 模块列表（⚠️ 当前 DTO 限制恰好 8 个，与服务端 9 模块校验矛盾，见上） |

**modules[] 子结构**：`moduleCode`（9 枚举之一）、`sortOrder`（1~9 整数）、`enabled`（boolean）。

### 前置条件与纪律

1. 先 `lock-acquire` 拿锁（被占用时向用户报告持锁人，不盲目等待）
2. `config-get` 读现态 → 与用户确认调整
3. `config-save` 提交
4. 成功后 `lock-release` 释放

### 调用示例

```json
{"capability":"ops.product.detail-layout.config-save","input":{"modules":[{"moduleCode":"benefit_info","sortOrder":1,"enabled":true}]},"summary":"保存商详模块配置（需先持锁）"}
```
