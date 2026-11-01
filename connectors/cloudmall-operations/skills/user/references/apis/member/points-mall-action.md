# 会员域 — 积分商城配置写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points-mall.md`；商城配置现值读取先读 `points-mall-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.points-mall.config-save 更新积分商城配置 🔴

---

## ✅ 更新积分商城配置 — ops.member.points-mall.config-save

- 🔴 全租户开关；upsert 语义

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Integer | ✅ | 0=关闭 / 1=开启（**整数，不是布尔**） |
| bgImageUrl | String | — | 首页头图 URL（不传（null）**不清除**已有头图——仅可覆盖新值；⚠️ 传**空字符串 ""** 会实际清空头图；首配时不传=用小程序内置默认图） |

### 出参（原始返回）

`data` 为 `null`；回读 `points-mall.config` 核验。

### 调用示例

```json
{"capability":"ops.member.points-mall.config-save","input":{"enabled":1},"summary":"开启积分商城"}
```
