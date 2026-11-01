# 商户域 — 进店规则写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-entry.md`；现值读取（规则列表）先读 `entry-rule-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：entry-rule.sort 更新进店规则排序 🔴 · entry-rule.update-status 更新进店规则状态 · entry-rule.update-params 更新进店规则参数

---

## ✅ 更新进店规则排序 — ops.merchant.entry-rule.sort

- 🔴 商业影响——改变 C 端进店判定顺序
- **约束**：sortedIds 不得包含 DEFAULT_STORE 的规则 ID（兜底门店优先级固定末位）；传**其余全部规则**（含 PARAM_STORE）的新顺序——PARAM_STORE 也可被重排到非首位

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sortedIds | String[] | ✅ | 排序后规则ID列表（不含 DEFAULT_STORE，**含 PARAM_STORE**） |

### 出参（原始返回）

无返回数据；执行后回读 list 核验顺序。

### 调用示例

```json
{"capability":"ops.merchant.entry-rule.sort","input":{"sortedIds":["6400012345678901234","6400012345678901235","6400012345678901236"]},"summary":"调整进店规则优先级顺序"}
```

---

## ✅ 更新进店规则状态 — ops.merchant.entry-rule.update-status

- **约束**：**仅 DEFAULT_STORE（兜底门店）不可禁用**（服务端拒绝）；PARAM_STORE 可正常启停

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则ID |
| enabled | Boolean | ✅ | true=启用 false=禁用 |

### 调用示例

```json
{"capability":"ops.merchant.entry-rule.update-status","input":{"id":"6400012345678901234","enabled":true},"summary":"启用进店规则"}
```

---

## ✅ 更新进店规则参数 — ops.merchant.entry-rule.update-params

- 先读 list 确认该规则的 ruleType，只传对应分支字段，其余不传

### 入参（按规则类型分支，条件必填）

| 字段 | 类型 | 适用规则 | 必填 | 说明 |
|------|------|---------|------|------|
| id | String | 全部 | ✅ | 规则ID |
| lockMode | String | MEMBER_STORE | 条件 | `LOCKED`/`ALLOW_SWITCH`（锁定门店/允许切换） |
| cacheDays | Integer | CACHE_RECENT | 条件 | 1~90 天 |
| enableFixedAreaRecommend | Boolean | LBS_RECOMMEND | 条件 | 是否启用固定区域推荐 |
| defaultStoreId | String | DEFAULT_STORE | 条件 | 兜底门店ID（来自 store.picker）；**修改此参数等效于直接切换默认门店**（要求目标门店 ACTIVE，自动解除隔离） |
| defaultStoreName | String | DEFAULT_STORE | 否 | 服务端按门店ID自动回填，无需传 |
| — | — | PARAM_STORE / AREA_RECOMMEND | — | 无参数，传 `{id}` 即可 |

### 出参（原始返回）

无返回数据。

### 调用示例

```json
{"capability":"ops.merchant.entry-rule.update-params","input":{"id":"6400012345678901235","cacheDays":30},"summary":"缓存最近访问规则改为30天"}
```
