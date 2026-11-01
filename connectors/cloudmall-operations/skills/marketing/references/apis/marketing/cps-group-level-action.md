# 营销域 — CPS 分销员分组与等级写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> **分组**：分销员归组，配合「全局/定向 × 分组」佣金率体系决定分佣水平（见 `cps-commission-query.md`）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-group-level-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-group.create 创建分销员分组 🔴 · cps-group.update 编辑分销员分组 🔴 · cps-group.delete 删除分销员分组 🔴 · cps-level.create 新增 CPS 等级 🔴 · cps-level.set-status CPS 等级启用/停用 🔴 · cps-level.batch-update 批量修改 CPS 等级 🔴 · cps-level.save-rule-page 保存等级规则页 🔴

---

## ✅ 创建分组 — `ops.marketing.cps-group.create`

- **风险**：🔴 商业影响（分组参与分组佣金率配置）
- **前置**：分组名称租户内唯一（重名会报错）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 分组名称，≤100 字符，租户内唯一 |
| description | String | 否 | 分组说明，≤100 字符 |

### 出参（原始数据）

- **路径参数来源**：`id`（新建分组 ID，可用于编辑/删除/佣金率配置）
- 展示型字段：`groupName`/`groupDesc`/`memberCount`（初始 0）。

### 调用示例

```json
{"capability":"ops.marketing.cps-group.create","input":{"name":"高佣金分组","description":"月度业绩 TOP 分销员"},"summary":"创建高佣金分组"}
```

---

## ✅ 编辑分组 — `ops.marketing.cps-group.update`

- **风险**：🔴 配置影响
- **前置**：分组存在；名称仍需租户内唯一。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 分组 ID（路径参数） |
| name | String | ✅ | 分组名称，≤100 字符 |
| description | String | 否 | 分组说明，≤100 字符 |

### 出参（原始数据）

- 更新后的分组信息（`id`/`groupName`/`groupDesc`/`memberCount`）。

### 调用示例

```json
{"capability":"ops.marketing.cps-group.update","input":{"id":"5300000000000000001","name":"高佣金分组","description":"月度业绩 TOP 分销员（更新）"},"summary":"更新分组说明"}
```

---

## ✅ 删除分组 — `ops.marketing.cps-group.delete`

- **风险**：🔴 破坏性操作
- **前置**：删除前必须确认分组下已无分销员、且无分组佣金率引用（该分组的佣金记录会失效）；不可恢复，执行前向用户二次确认。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 分组 ID（路径参数） |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-group.delete","input":{"id":"5300000000000000001"},"summary":"删除该分销员分组"}
```

---

## ✅ 新增等级 — `ops.marketing.cps-level.create`

- **风险**：🔴 资金面相关（返佣系数直接放大/缩小分佣金额）
- **前置**：`commissionRatio` 是**返佣系数**——对按佣金率算出的佣金再乘以该系数，1.0000=100%（基准），范围 0..10.00；**不是百分比数字**（填 1 表示 1 倍而非 1%）。新建等级默认为停用态，需按「从低到高」约束另行启用。
- **后果**：业务等级号自动分配（当前最大等级号 +1）；启用后命中该等级的分销员佣金按系数结算。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| levelName | String | ✅ | 等级名称 |
| levelPicture | String | 否 | 等级图片 URL |
| backgroundImage | String | 否 | 背景图 URL |
| commissionRatio | Number | ✅ | 返佣系数，0..10.00（1.0000=100% 基准） |
| levelValue | String | 否 | 考核指标 JSON 字符串，格式 `[{"type":1,"typeValue":"PROMOTE_UV","value":100}, ...]`。**指标枚举**：type=1/PROMOTE_UV 引流人数、type=2/DEAL_COUNT 成交人数、type=3/VALID_GMV 有效 GMV（value 为元金额）；`value` 为考核目标值，**0 或缺省=该项不考核**（新建等级默认三项全 0）。启用时服务端校验**同指标在各启用等级间严格递增**（低等级同指标最大正值须小于当前值，否则报「考核指标不满足递增」）；非最低等级启用须至少一项 >0。列表/详情出参中 `levelValue` 为该 JSON 原文回显 |
| enabled | Integer | ✅ | 初始启用状态：0=停用，1=启用 |

### 出参（原始数据）

- **路径参数来源**：`levelId`（自动分配的业务等级号）
- **枚举字段**：`enabled`（0/1）
- 其余为展示型字段（levelName/commissionRatio/levelValue）。

### 调用示例

```json
{"capability":"ops.marketing.cps-level.create","input":{"levelName":"金牌分销员","commissionRatio":1.2,"levelValue":"[{\"type\":1,\"typeValue\":\"PROMOTE_UV\",\"value\":100}]","enabled":1},"summary":"新增金牌分销员等级，返佣系数1.2倍"}
```

---

## ✅ 等级启用/停用 — `ops.marketing.cps-level.set-status`

- **风险**：🔴 资金面相关（等级启停影响在级分销员的系数结算）
- **前置**：启用须从低到高、停用须从高到低（见文件头顺序约束）；考核指标不满足严格递增等约束时启用会报业务错误。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| levelId | String | ✅ | 业务等级号（路径参数，来自等级列表） |
| enabled | Integer | ✅ | 0=停用，1=启用 |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-level.set-status","input":{"levelId":"2","enabled":0},"summary":"停用2号等级"}
```

---

## ✅ 批量修改等级 — `ops.marketing.cps-level.batch-update`

- **风险**：🔴 资金面相关（批量变更各等级返佣系数与降级规则）
- **前置**：`levels[].version` 为乐观锁版本号，必须来自最近一次等级列表查询结果，版本不符会更新失败；字段名注意——批量项里的返佣系数叫 `commissionRate`（**不是**新增时的 `commissionRatio`）。
- **后果**：整批更新等级信息与降级规则开关；`downgradeEnabled` 决定考核不达标时是否允许降级。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| levels | Array | ✅ | 等级项列表，不允许为空 |
| levels[].levelId | String | ✅ | 业务等级号（0 起） |
| levels[].levelName | String | 否 | 等级名称 |
| levels[].levelPicture | String | 否 | 等级图片 |
| levels[].backgroundImage | String | 否 | 背景图 |
| levels[].commissionRate | Number | 否 | 返佣系数，0..10.00（1.0000=100% 基准） |
| levels[].assessmentMetrics | String | 否 | 考核指标 JSON 字符串——**结构与语义同新增等级的 `levelValue`**（`[{"type":1\|2\|3,"typeValue":"PROMOTE_UV\|DEAL_COUNT\|VALID_GMV","value":Number}]`，0=不考核；启用受同指标严格递增约束）。编辑回显时该值来自列表出参 `levelValue` 字段（JSON 原文） |
| levels[].enabled | Integer | 否 | 0=停用，1=启用 |
| levels[].version | String | 否 | 乐观锁版本号（来自等级列表/详情查询） |
| downgradeEnabled | Boolean | 否 | 是否允许降级 |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-level.batch-update","input":{"levels":[{"levelId":"1","levelName":"银牌分销员","commissionRate":1.1,"enabled":1,"version":2}],"downgradeEnabled":false},"summary":"更新银牌等级返佣系数为1.1倍并关闭降级"}
```

---

## ✅ 保存规则页内容 — `ops.marketing.cps-level.save-rule-page`

- **风险**：🔴 内容发布（直接更新 C 端展示的规则页）
- **前置**：`content` 为富文本 HTML，必填且 ≤65535 字符；内容应以用户提供的原文为准，不要自行改写规则表述。 **硬门禁：直接更新 C 端展示的规则页，提交前必须复述变更内容取得确认。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | String | ✅ | 规则页富文本 HTML，≤65535 字符 |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-level.save-rule-page","input":{"content":"<p>等级规则：连续 30 天推广 UV 达标可升级，升级后佣金按等级系数上浮。</p>"},"summary":"更新等级规则页内容"}
```
