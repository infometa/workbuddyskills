# 商品域 — 研学营期名额写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-tour.md`；现态读取（场次与版本号）先读 `tour-session-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：tour-session-quota.batch-update 批量更新营期名额 🔴

---

## ✅ 批量更新营期名额 — ops.product.tour-session-quota.batch-update

- 🔴 商业影响档位；名额影响可售与超卖风险，执行前向用户复述场次与数值；带版本乐观锁——版本不一致会被拒绝，先重新查询
- 仅平台管理员/运营角色可操作（权限不足返回 PERMISSION_DENIED）

### 入参

**SINGLE_STORE**（逐场次指定，当前唯一可用模式）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scope | String | ✅ | `SINGLE_STORE` |
| updates | Array | ✅ | `[{id, expectedVersion, totalQuota（必填，只改预留时也回传当前值）, reservedQty?}]`（id 来自 list 的场次记录） |
| idempotencyKey | String | — | 幂等键（服务端重复提交保护）。⚠️ 重复 key 返回**空结果**（successCount=0，非原结果重放）——**版本冲突重试时必须换新 key**，复用旧 key 会得到误导性"空成功" |

### 出参（原始返回）

`data` 为批量更新结果（成功/失败明细，含版本冲突项），逐条报告；冲突项需重新查询后重试。

### 调用示例

```json
{"capability":"ops.product.tour-session-quota.batch-update","input":{"scope":"SINGLE_STORE","updates":[{"id":"3200012345678901234","expectedVersion":2,"totalQuota":30}]},"summary":"将指定场次总量调整为30"}
```
