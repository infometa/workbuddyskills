# 会员域 — 升级礼包查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-level.md`；礼包配置保存与全局开关（写操作）见 `upgrade-gift-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。**发放门禁两级**：① 全局开关（本文件 `config`）——发放链路第一步检查；② 各等级 `levelEnabled`（`save` 中按等级配置）。会员权益的 `benefit.status`（UPGRADE_GIFT）仅更新权益行展示口径，**不参与发放判定**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.upgrade-gift.list 升级礼包配置列表 · member.upgrade-gift.config 全局开关查询 · member.upgrade-gift.issue-records 发放记录

---

## ✅ 升级礼包配置列表 — ops.member.upgrade-gift.list

- 全量非分页（按等级左关联，未配置等级也返回行）

### 入参

无。

### 出参（原始返回）

`data` 为各等级礼包配置。**关键字段**：`levelId`（→ save 的 levels[].levelId，来自等级配置）、`levelCode`/`levelName`、`giftPoints`（null=未配置）、`coupons[]`（`couponId`/`couponName`/`quantity`）、`levelEnabled`（该等级礼包开关）。

### 调用示例

```json
{"capability":"ops.member.upgrade-gift.list","input":{},"summary":"查询升级礼包配置"}
```

---

## ✅ 升级礼包全局开关查询 — ops.member.upgrade-gift.config

### 入参

无。

### 出参（原始返回）

对象含 `enabled`（Boolean；**未配置过时返回默认 `enabled=false`**——即功能默认关闭）。

### 调用示例

```json
{"capability":"ops.member.upgrade-gift.config","input":{},"summary":"查询升级礼包全局开关"}
```

---

## ✅ 升级礼包发放记录 — ops.member.upgrade-gift.issue-records

- 发放失败排查

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| memberId | String | — | 会员 ID 筛选（字段名不用 `userId`：网关视为身份保留字段会拒绝，自动映射回后端 `userId`） |
| levelId | String | — | 等级 ID 筛选 |
| issueStatus | Integer | — | 10=待发放 / 20=成功 / 30=失败 |
| giftType | String | — | `POINT` / `COUPON` |
| pageNum / pageSize | Integer | — | 分页（默认 1 / 20） |

### 出参（原始返回）

分页对象。**关键字段**：`records[].userId`、`levelName`、`failReason`（失败原因排查）；**枚举字段**：`giftType`（POINT/COUPON）、`issueStatus`（10/20/30）。

### 调用示例

```json
{"capability":"ops.member.upgrade-gift.issue-records","input":{"pageNum":1,"pageSize":20,"issueStatus":30},"summary":"查询发放失败的礼包记录"}
```
