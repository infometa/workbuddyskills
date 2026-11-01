# 营销域 — CPS 分销员与绑定关系查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> 分销员是 CPS 分佣的主体（员工或普通用户），通过分组与佣金率体系决定分佣水平；绑定关系记录「消费者 ↔ 分销员」的推广归属。
> 通用约定：列表入参支持 `pageNum`（≥1，默认 1）/`pageSize`（1..100，默认 20）；ID 均为十进制字符串。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-distributor.search 分销员列表（name 模糊/phone/uid 精确） · cps-distributor.detail 分销员详情（含员工关联信息） · cps-distributor.account 分销员佣金账户三余额（元） · cps-distributor.deal-records 分销员账户流水（**pageSize ≤50**） · cps-bind-relation.search CPS 绑定关系列表（消费者↔分销员） · cps.distributor.export 分销员数据异步导出（返回任务 ID）
> 写操作见 `cps-distributor-action.md`。

---

## ⛔ 未开放端点（分销员域）

| 端点 | 不开放理由 |
|------|-----------|
| 下载导入模板（Excel 文件流） | 二进制文件下载，工具无法回传；模板列结构以运营端页面下载为准 |

---

## ✅ 分销员列表 — `ops.marketing.cps-distributor.search`

- **说明**：分页查询租户内分销员；`name` 模糊匹配，`phone`/`uid` 精确匹配。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| name | String | 否 | 姓名模糊搜索，≤100 字符 |
| phone | String | 否 | 手机号，≤20 字符 |
| uid | String | 否 | 用户 UID，≤64 字符 |
| type | Integer | 否 | 分销员类型：1=员工，2=普通用户 |
| groupId | String | 否 | 分组 ID |
| status | Integer | 否 | 状态：0=启用，1=禁用 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].uid`（→ 详情/佣金账户/流水/启停等路径参数）
- **枚举字段**：`type`（1=员工，2=普通用户）、`status`（0=启用，1=禁用）、`openChannel`（1=运营端导入，2=邀请开通，3=自主申请）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）
- 展示型字段 `name/contactPhone/levelName/groupName/level`（业务等级号）可直接透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.search","input":{"pageNum":1,"pageSize":20,"name":"张","status":0},"summary":"分页查看启用状态的姓张分销员"}
```

---

## ✅ 分销员详情 — `ops.marketing.cps-distributor.detail`

- **说明**：按 UID 查询单个分销员详情，含 B 端员工关联信息（员工类型分销员）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uid | String | ✅ | 分销员 UID |

### 出参（原始数据）

- **路径参数来源**：`uid`
- **枚举字段**：`type`（1=员工，2=普通用户）、`status`（0=启用，1=禁用）、`openChannel`（1/2/3 同上）、`employeeStatus`（0=使用中，1=已禁用）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- 展示型字段：`cpsDesc`（分销员描述）、`headUrl`（头像）、`bUid`、`inviter`（邀请人）、`employeeName`/`employeePhone`（员工类型时从用户中心回填）。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.detail","input":{"uid":"900000000000000001"},"summary":"查看分销员详情"}
```

---

## ✅ 分销员佣金账户 — `ops.marketing.cps-distributor.account`

- **说明**：查询分销员佣金账户三余额；从未产生佣金流水的分销员三个金额均返回 0。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uid | String | ✅ | 分销员 UID |

### 出参（原始数据）

- **格式敏感字段**：`withdrawalAmount`（可提现余额，元）、`withdrawingAmount`（提现中金额，元）、`withdrawnAmount`（已提现金额，元）——三个金额字段均为**元**，两位小数。
- 提现中金额与提现单审核/打款链路联动（提现申请冻结余额，驳回/失败回退，打款成功转入已提现）。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.account","input":{"uid":"900000000000000001"},"summary":"查看分销员佣金账户余额"}
```

---

## ✅ 分销员账户流水 — `ops.marketing.cps-distributor.deal-records`

- **说明**：分页查询分销员佣金账户流水（收入/提现变动记录）。注意 `pageSize` 上限是 **50**（与通用 100 不同）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uid | String | ✅ | 分销员 UID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..**50**，默认 10 |
| dealType | Integer | 否 | 流水类型（单选）：1=服务收入，2=资产收入，3=活动奖励，4=提现 |
| dealTypes | Integer[] | 否 | 流水类型（多选），如 [1,2,3] 表示只查收入类；**多选优先生效**，与 dealType 二选一传 |
| dealStatus | Integer | 否 | 流水状态：1=收入，2=冻结，3=回滚，4=扣减（以服务端枚举为准；"冻结/回滚/扣减"均对应提现链路的不同阶段） |
| startTime | String | 否 | 开始时间，格式必须为 yyyy-MM-dd HH:mm:ss（格式错误会报错） |
| endTime | String | 否 | 结束时间，格式同上 |

### 出参（分页，原始数据）

- **枚举字段**：`records[].dealType`（1/2/3/4 同上）、`records[].dealStatus`（1=收入，2=冻结，3=回滚，4=扣减），均有对应 `dealTypeDesc`/`dealStatusDesc` 中文描述可直接透传
- **格式敏感字段**：`records[].dealAmount`（交易金额，元）、`records[].dealTime`（yyyy-MM-dd HH:mm:ss）
- `voucherNum` 为凭证号（订单号/提现单号/活动编号），可透传展示。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.deal-records","input":{"uid":"900000000000000001","pageNum":1,"pageSize":10},"summary":"查看分销员佣金流水"}
```

---

## ✅ 绑定关系列表 — `ops.marketing.cps-bind-relation.search`

- **说明**：分页查询「消费者 ↔ 分销员」推广绑定关系；`cpsUid`/`uid` 均精确匹配，`phone` 为消费者手机号精确匹配（服务端反查用户中心后过滤）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| cpsUid | String | 否 | 分销员 UID（精确） |
| uid | String | 否 | 消费者 UID（精确） |
| phone | String | 否 | 消费者手机号（精确） |
| bindType | Integer | 否 | 绑定类型：1=链接，2=扫码，3=手动 |
| relationType | Integer | 否 | 绑定模式：1=动态，2=专属，3=永久 |

### 出参（分页，原始数据）

- **枚举字段**：`records[].bindType`（1/2/3）、`records[].relationType`（1/2/3），均有中文描述字段
- **格式敏感字段**：`records[].bindTime`/`records[].expireTime`（yyyy-MM-dd HH:mm:ss；`expireTime` 为 null 表示永不过期）
- `valid`（是否有效）为布尔；嵌套的 `distributorInfo`/`memberInfo`/`storeInfo` 为关联摘要（分销员/会员/门店），可直接透传展示。

### 调用示例

```json
{"capability":"ops.marketing.cps-bind-relation.search","input":{"pageNum":1,"pageSize":20,"cpsUid":"900000000000000001"},"summary":"查看该分销员名下的消费者绑定关系"}
```

---

## ✅ 分销员数据导出 — `ops.marketing.cps.distributor.export`

- **说明**：按筛选条件异步导出分销员数据。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。导出为**非幂等操作**（重试创建重复任务），超时先轮询任务状态。**导出内容含手机号等明文 PII，转述需打码、交付提醒保管。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | keyword（关键词）/ groupId（分组）/ status（状态）；导出无分页参数（服务端固定分批拉取，上限 5 万行） |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.cps.distributor.export","input":{},"summary":"导出启用状态的全部分销员"}
```

---
