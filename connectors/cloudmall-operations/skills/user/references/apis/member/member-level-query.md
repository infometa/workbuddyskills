# 会员域 — 会员等级查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-level.md`；等级写操作（新建/编辑/启停/规则保存/图片上传）见 `member-level-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。等级为全租户配置。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.level.list 等级列表 · member.level.detail 等级详情 · member.level.rule-description 等级规则描述 · member.level.downgrade-rule 降级规则 · member.level.change-logs 等级变更流水

---

## ✅ 等级列表 — ops.member.level.list

- 全量非分页

### 入参

无。

### 出参（原始返回）

`data` 为等级数组。**关键字段**：`id`（→ 详情/编辑/状态切换路径参数、成长加速/升级礼包的 `levelId`）、`levelCode`（V0/V1...，→ 积分商品 allowedLevels）、`levelName`、`associatedBenefits[]`（关联权益列表）；**枚举字段**：`status`（0=启用 1=停用）；**格式敏感字段**：`growthValue`（整数）、`pointsMultiplier`（小数，**权益域 POINTS_MULTIPLIER 策略动态计算的派生值**，非等级表字段——创建/编辑等级不配置倍率；无启用中的积分倍率权益时为 null）、`pointsMultiplierEnabled`（Boolean，同源派生——与 create/update 入参的同名字段**不落库**语义区分）、`cardImage`/`bgImage`（⚠️ 出口签名口径不同——仅 `bgImage` 出口为 30 分钟时效 COS 预签名 URL，回传时可原样回传（保存时服务端自动剥离签名参数）；`cardImage` 出口**不做签名**、原样返回存储值，且落库**不做签名清洗**——若经手预签名 URL 须自行剥离 `?` 后参数）、`themeColor`。

### 调用示例

```json
{"capability":"ops.member.level.list","input":{},"summary":"查询会员等级列表"}
```

---

## ✅ 等级详情 — ops.member.level.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 等级 ID |

### 出参（原始返回）

单个等级对象（字段同列表）。

### 调用示例

```json
{"capability":"ops.member.level.detail","input":{"id":"1000012345678901234"},"summary":"查询等级详情"}
```

---

## ✅ 等级规则描述 — ops.member.level.rule-description

- 租户级单条富文本

### 入参

无。

### 出参（原始返回）

对象含 `content`（富文本 HTML 字符串）。

### 调用示例

```json
{"capability":"ops.member.level.rule-description","input":{},"summary":"查询等级规则描述"}
```

---

## ✅ 降级规则 — ops.member.level.downgrade-rule

### 入参

无。

### 出参（原始返回）

对象。**枚举字段**：`strategyType`（0=不降级 1=按发放日过期 2=按自然年到期）；`expiryYears`（策略1）、`expiryNthYear`/`expiryMonth`/`expiryDay`（策略2）。

### 调用示例

```json
{"capability":"ops.member.level.downgrade-rule","input":{},"summary":"查询降级规则"}
```

---

## ✅ 等级变更流水 — ops.member.level.change-logs

- 升级/降级历史排查

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| memberId | String | — | 会员 ID 筛选（字段名不用 `userId`：网关视为身份保留字段会拒绝，自动映射回后端 `userId`） |
| changeType | String | — | `UP`-升级 / `DOWN`-降级；空=全部 |
| startTime / endTime | String | — | 变更时间范围（**ISO-8601 含 T**，如 `2026-07-01T00:00:00`） |
| pageNum / pageSize | Integer | — | 分页（默认 1 / 20） |

### 出参（原始返回）

分页对象。**关键字段**：`records[].userId`、`oldLevelCode`/`newLevelCode`、`growthBefore`/`growthAfter`、`changeAmount`；**枚举字段**：`changeType`（UP/DOWN）。

### 调用示例

```json
{"capability":"ops.member.level.change-logs","input":{"pageNum":1,"pageSize":20,"changeType":"DOWN"},"summary":"查询近期的降级流水"}
```
