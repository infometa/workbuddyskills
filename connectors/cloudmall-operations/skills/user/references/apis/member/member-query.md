# 会员域 — 会员档案查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-profile.md`；档案写操作（创建/编辑/黑名单/打标/积分调整）见 `member-action.md`，导入导出与任务查询见 `member-import-export-query.md` / `member-import-export-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。会员/列表/详情为敏感接口，手机号等字段后端脱敏。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.member.search 会员分页查询 · member.member.detail 会员详情 · member.member.batch-get-by-uids 批量按 uid 反查 · member.member.tags 已绑标签 · member.member.coupons 会员优惠券 · member.member.points-flows 积分流水 · member.member.growth-flows 成长值流水 · member.member.addresses 收货地址

---

## ✅ 会员分页查询 — ops.member.member.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页；pageSize ≤100（默认 10） |
| nickname | String | — | 昵称（模糊） |
| memberNo | String | — | 会员编号（精确） |
| uid | String | — | UID（精确，十进制字符串） |
| phone | String | — | 手机号（精确，1 开头 11 位） |
| source | String | — | 注册来源 |
| registerTimeStart / registerTimeEnd | String | — | 注册时间范围（yyyy-MM-dd HH:mm:ss） |
| level | Integer | — | 会员等级数值 |
| status | Integer | — | 会员状态：0=正常 1=冻结 2=黑名单 3=已注销 |
| sortField | String | — | 排序字段：register_time / last_consume_time |
| sortOrder | String | — | ASC / DESC |

### 出参（原始返回）

`data.records[]` 为会员视图。**关键字段**：`records[].id`（→ 详情/编辑/黑名单/标签/积分/地址等全部子操作路径参数）、`uid`、`memberNo`；**枚举字段**：`status`（0/1/2/3）；**格式敏感字段**：`id`/`uid`（Long→string）、`registerTime`（yyyy-MM-dd HH:mm:ss）；**脱敏字段**：`phone`。

### 调用示例

```json
{"capability":"ops.member.member.search","input":{"pageNum":1,"pageSize":20,"phone":"13800000001"},"summary":"按手机号查询会员"}
```

---

## ✅ 会员详情 — ops.member.member.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID（来自 search 的 `records[].id`） |

### 出参（原始返回）

单个会员详情对象。**关键字段**：`id`（→ 子操作路径参数）、`pointsBalance`（可用积分余额，→ 积分扣减 DECREASE 余额预检）、`growthValue`、`levelId`/`levelName`（⚠️ detail 的 `levelCode` 恒为 null——等级编码以 `ops.member.member.search` 列表返回为准）；**枚举字段**：`status`（0/1/2/3）、`gender`（0=未知 1=男 2=女）；**格式敏感字段**：`id`/`uid`/`pointsBalance`/`growthValue`（Long→string）、`birthday`（yyyy-MM-dd）；**脱敏字段**：`phone`（脱敏）；⚠️ 响应另含**明文手机号 `rawPhone`**（运营端内部字段，未脱敏）——**禁止在答复中复述**，展示时自行脱敏为前 3 后 4。

### 调用示例

```json
{"capability":"ops.member.member.detail","input":{"id":"900000000000000001"},"summary":"查询会员详情"}
```

---

## ✅ 批量按 uid 查会员 — ops.member.member.batch-get-by-uids

- uid 列表批量反查基本信息（如人群包成员核对）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uids | String[] | ✅ | UID 列表（十进制字符串） |

### 出参（原始返回）

`data` 为会员基本信息数组。**关键字段**：`uid`（按它关联请求项——**响应顺序不保证与请求一致**，未返回的 uid 视为未查到）、`name`、`memberNo`、`memberLevel`；**格式敏感字段**：`registerTime`（yyyy-MM-dd HH:mm:ss）、`birthday`（yyyy-MM-dd）；**脱敏字段**：无——该接口返回的 `phone` 为**明文手机号**，仅用于用户明确要求的业务核对场景，答复中不得复述完整号码（展示时自行脱敏为前 3 后 4）。

### 调用示例

```json
{"capability":"ops.member.member.batch-get-by-uids","input":{"uids":["900000000000000001","900000000000000002"]},"summary":"批量反查两个 uid 的会员信息"}
```

---

## ✅ 会员已绑标签 — ops.member.member.tags

- 绑定/解绑后回读核验用

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |

### 出参（原始返回）

`data` 为标签数组。**关键字段**：`tagId`（→ 解绑路径参数）、`tagName`。

### 调用示例

```json
{"capability":"ops.member.member.tags","input":{"id":"900000000000000001"},"summary":"查看会员已绑定标签"}
```

---

## ✅ 会员优惠券 — ops.member.member.coupons

- 经促销域券库查询，促销不可用时**降级返回空页（空 ≠ 无券）**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |
| pageNum / pageSize | Integer | — | 分页；pageSize ≤100，默认 20 |

### 出参（原始返回）

分页对象，`records[]` 为促销域券实例（券名/面额/状态/有效期以返回为准）。

### 调用示例

```json
{"capability":"ops.member.member.coupons","input":{"id":"900000000000000001","pageNum":1,"pageSize":20},"summary":"查询会员持有的优惠券"}
```

---

## ✅ 会员积分流水 — ops.member.member.points-flows

- 已过滤 freeze/rollback 中间态；积分调整后回读核验用

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |
| pageNum / pageSize | Integer | — | 分页；pageSize ≤100，默认 20 |

### 出参（原始返回）

分页对象。**关键字段**：`records[].id`、`direction`（IN=获取 / OUT=消耗）、`amount`（变更数量）、`operateTime`（yyyy-MM-dd HH:mm:ss）、`channelName`/`activityDesc`（来源说明）。

### 调用示例

```json
{"capability":"ops.member.member.points-flows","input":{"id":"900000000000000001","pageNum":1,"pageSize":20},"summary":"查询会员积分流水"}
```

---

## ✅ 会员成长值流水 — ops.member.member.growth-flows

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |
| pageNum / pageSize | Integer | — | 分页；pageSize ≤100，默认 20 |

### 出参（原始返回）

分页对象。**关键字段**：`records[].direction`（IN=获得 / OUT=消耗）、`amount`（变更数量）、`currentGrowth`（操作后余额快照）、`operateTime`（yyyy-MM-dd HH:mm:ss）。

### 调用示例

```json
{"capability":"ops.member.member.growth-flows","input":{"id":"900000000000000001","pageNum":1,"pageSize":20},"summary":"查询会员成长值流水"}
```

---

## ✅ 会员收货地址 — ops.member.member.addresses

- 地址为脱敏展示（姓名仅姓、电话中间四位打码、详情截断）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |

### 出参（原始返回）

`data` 为地址数组。**关键字段**：`addressId`、`isDefault`；**脱敏字段**：`receiver`/`phone`/`detailAddress`（后端脱敏，不得尝试还原）。

### 调用示例

```json
{"capability":"ops.member.member.addresses","input":{"id":"900000000000000001"},"summary":"查询会员收货地址"}
```
