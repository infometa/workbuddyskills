# 会员域 — 积分明细契约（租户维度）

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。单会员维度流水见 `member-query.md` 的 `ops.member.member.points-flows`。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.point-flow.search 积分明细分页查询 · member.point-flow.detail 积分流水详情

---

## ✅ 积分明细分页查询 — ops.member.point-flow.search

- 租户维度流水排查

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页；pageSize ≤100，默认 20 |
| startTime / endTime | String | — | 时间范围（yyyy-MM-dd HH:mm:ss）；**跨度 ≤180 天**（超限报错）；⚠️ 只传单边时间会被静默忽略（等同不过滤），须成对传入 |
| phone | String | — | 手机号（精确） |
| memberId | String | — | 会员/用户 ID（精确，十进制字符串；字段名不用 `userId`：网关视为身份保留字段会拒绝，自动映射回后端 `userId`） |
| tradeType | String | — | 交易类型，小写连字符：`freeze`-冻结 / `rollback`-解冻回滚 / `commit`-核销 / `direct-trans`-直接转账 / `charge`-充值 / `refund`-退款 / `expire`-过期；默认结果已排除 freeze/rollback 中间态与系统平台流水（uid=PLATFORM），**显式指定 tradeType=freeze/rollback 时中间态不再被排除**（运营审计用） |
| channelId | String | — | 活动渠道编码，字符串：`10`=购买商品 / `ADMIN_ADJUST_MARKETING`=运营调整（营销）/ `ADMIN_ADJUST_SHOPPING`=运营调整（购物），其余以返回数据为准 |

### 出参（原始返回）

分页对象。**关键字段**：`records[].id`（→ detail 路径参数）、`direction`（IN/OUT）、`amount`、`orderNo`（关联业务单号，可空）；**格式敏感字段**：`operateTime`（yyyy-MM-dd HH:mm:ss）；**脱敏字段**：`phone`。

### 调用示例

```json
{"capability":"ops.member.point-flow.search","input":{"pageNum":1,"pageSize":20,"startTime":"2026-09-01 00:00:00","endTime":"2026-09-08 23:59:59"},"summary":"查询本周积分流水"}
```

---

## ✅ 积分流水详情 — ops.member.point-flow.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 流水 ID（来自 search 的 `records[].id`） |

### 出参（原始返回）

单条流水对象（字段基本同列表）。⚠️ `userId` 字段**列表有值（Service 显式回填）、详情恒 null**（detail 转换器不设该字段）——按用户排查流水用 `search` 的 `memberId` 筛选，勿依赖 detail。⚠️ 订单类流水（订单积分抵扣/返还，业务单号为 `PF-`/`PR-` 开头的支付单/售后单）后端**不回填 userId**，按 `memberId` 筛选会漏掉这类流水；需要完整口径时改用会员维度 `ops.member.member.points-flows`，或在答复里说明可能遗漏订单类流水。

### 调用示例

```json
{"capability":"ops.member.point-flow.detail","input":{"id":"1400012345678901234"},"summary":"查询积分流水详情"}
```
