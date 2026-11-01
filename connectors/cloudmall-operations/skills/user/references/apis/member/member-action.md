# 会员域 — 会员档案写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-profile.md`；检索与现值读取（分页/详情/标签/流水）先读 `member-query.md`，导入导出见 `member-import-export-action.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.member.create 新建会员 · member.member.update 编辑会员 · member.member.blacklist 加入黑名单 🔴 · member.member.unblacklist 解除黑名单 🔴 · member.member.bind-tags 绑定标签 · member.member.unbind-tag 解绑标签 · member.member.points-adjust 积分调整 🔴

---

## ✅ 新建会员 — ops.member.member.create

- 表单确认后执行

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | String | ✅ | 手机号，正则 `^1[3-9]\d{9}$` |
| nickname | String | — | 昵称（≤50 字符） |
| gender | Integer | — | 性别：0=未知 1=男 2=女 |
| birthday | String | — | 生日（yyyy-MM-dd） |

### 出参（原始返回）

创建结果对象（仅含新会员 `id`，Long→string；uid 可由 `ops.member.member.detail` 获取）。

### 业务规则（服务端）

- **同租户手机号唯一**（已注销账号除外，允许重新导入）：重复创建返回业务错误。

### 调用示例

```json
{"capability":"ops.member.member.create","input":{"phone":"13900001234","nickname":"张小明","gender":1,"birthday":"1995-06-15"},"summary":"新建会员"}
```

---

## ✅ 编辑会员基本信息 — ops.member.member.update

- 仅昵称/性别/生日可选更新，只传用户要求修改的字段（非全量覆盖语义）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |
| nickname | String | — | 昵称（≤50 字符） |
| gender | Integer | — | 性别：0/1/2 |
| birthday | String | — | 生日（yyyy-MM-dd） |

### 出参（原始返回）

`data` 为 `null`（Void）；以 `ops.member.member.detail` 回读核验。

### 调用示例

```json
{"capability":"ops.member.member.update","input":{"id":"900000000000000001","nickname":"张小明"},"summary":"修改会员昵称"}
```

---

## ✅ 加入黑名单 — ops.member.member.blacklist

- 🔴 用户资产类——执行前复述会员身份并获用户确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |

### 出参（原始返回）

`data` 为 `null`；重复加入（已是黑名单）返回业务错误。以 `ops.member.member.detail` 回读 status=2 核验。⚠️ 状态边界（按实现）：拉黑对 FROZEN(1)/CANCELED(3) 会员**无前置拦截**（任何非黑名单状态均可拉黑——冻结/已注销会员拉黑后其状态变为 2）。

### 调用示例

```json
{"capability":"ops.member.member.blacklist","input":{"id":"900000000000000001"},"summary":"将会员加入黑名单"}
```

---

## ✅ 解除黑名单 — ops.member.member.unblacklist

- 🔴 用户资产类——解除后恢复会员正常权益；执行前复述会员身份获用户确认

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |

### 出参（原始返回）

`data` 为 `null`；非黑名单会员调用返回业务错误。以 `ops.member.member.detail` 回读 status=0 核验。⚠️ **解除后无条件置 status=0（正常）**、不恢复拉黑前的原状态——冻结/已注销会员经「拉黑→解除」会直接变为正常态；仅对原本正常的会员使用解除操作，其他状态解拉黑前须与用户确认状态预期。

### 调用示例

```json
{"capability":"ops.member.member.unblacklist","input":{"id":"900000000000000001"},"summary":"解除会员黑名单"}
```

---

## ✅ 会员绑定标签 — ops.member.member.bind-tags

- 幂等（已绑定跳过；不存在的标签**静默跳过**）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |
| tagIds | String[] | ✅ | 标签 ID 列表（1~50 个，十进制字符串） |

### 出参（原始返回）

`data` 为 `null`。

### ⚠️ 标签双轨警告（执行后必须核验）

标签管理已迁移数据标签域（data-tag-center），本绑定接口校验会员域本地标签表——**来自其他体系的标签 ID 会被静默跳过（返回成功但未绑定）**。tagId 必须来自：① 该会员已绑标签列表（`ops.member.member.tags`）；② 用户明确提供且确认有效的会员域标签 ID。执行后**必须回读 `ops.member.member.tags`** 确认生效，未生效时如实告知用户。

### 调用示例

```json
{"capability":"ops.member.member.bind-tags","input":{"id":"900000000000000001","tagIds":["1500012345678901234"]},"summary":"给会员绑定标签"}
```

---

## ✅ 会员解绑标签 — ops.member.member.unbind-tag

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |
| tagId | String | ✅ | 标签 ID（来自 `ops.member.member.tags` 的 `tagId`） |

### 出参（原始返回）

`data` 为 `null`；未绑定的标签返回业务错误。回读 `ops.member.member.tags` 核验。

### 调用示例

```json
{"capability":"ops.member.member.unbind-tag","input":{"id":"900000000000000001","tagId":"1500012345678901234"},"summary":"解绑会员标签"}
```

---

## ✅ 积分调整 — ops.member.member.points-adjust

- 🔴🔴 用户资产类高危——方向与数量必须用户明确给出，禁止 AI 编造；**超时禁自动重试**（可能重复加减）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 会员 ID |
| category | String | ✅ | 积分类型：`MARKETING`-营销活动 / `SHOPPING`-购物消费（大写） |
| adjustType | String | ✅ | `INCREASE`-增加 / `DECREASE`-扣减（大写） |
| amount | Integer | ✅ | 数量，1~99999 正整数 |
| reason | String | — | 发放说明，**≤10 字符** |

### 出参（原始返回）

`data` 为 `null`；DECREASE 超过可用余额返回业务错误（先以 `ops.member.member.detail` 的 `pointsBalance` 预检）。以 `ops.member.member.points-flows` 回读核验（direction=IN/OUT + amount）。

### 调用示例

```json
{"capability":"ops.member.member.points-adjust","input":{"id":"900000000000000001","category":"MARKETING","adjustType":"INCREASE","amount":100,"reason":"补偿发放"},"summary":"给会员增加100积分"}
```
