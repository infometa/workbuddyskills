# 商户域 — 热搜词与搜索干预写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-search.md`；现值读取（热搜词/NLU/Rerank 分页）先读 `search-intervention-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。⚠️ 本文件枚举**全部小写**，与门店域大写枚举不同。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：hot-keyword.create 新增热搜词 · hot-keyword.update 编辑热搜词 · hot-keyword.update-status 启停热搜词 · hot-keyword.delete 删除热搜词 · hot-keyword.sort 热搜词批量排序 · search-intervention.nlu.create 新增NLU规则 · search-intervention.nlu.update 编辑NLU规则 · search-intervention.nlu.delete 删除NLU规则 · search-intervention.nlu.update-status 启停NLU规则 · search-intervention.rerank.create 新增Rerank规则 · search-intervention.rerank.update 编辑Rerank规则 · search-intervention.rerank.delete 删除Rerank规则 · search-intervention.rerank.update-status 启停Rerank规则

---

## ✅ 新增热搜词 — ops.merchant.hot-keyword.create

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | ✅ | ≤20 字符，不允许纯空格 |
| sortWeight | Integer | ✅ | 排序权重，越小越靠前 |
| status | Integer | 否 | 0=停用 1=启用，默认 1 |
| badgeType | Integer | 否 | 0=无 1=新 2=热，默认 0 |
| startTime | String | 否 | 生效开始（yyyy-MM-dd HH:mm:ss），null=立即生效 |
| endTime | String | 否 | 生效结束（yyyy-MM-dd HH:mm:ss），null=长期有效 |

### 出参（原始返回）

`data` 为新建热搜词ID。

### 调用示例

```json
{"capability":"ops.merchant.hot-keyword.create","input":{"keyword":"研学营地","sortWeight":10,"badgeType":1,"startTime":"2026-09-10 00:00:00","endTime":"2026-09-30 23:59:59"},"summary":"新增研学营地热搜词带新角标"}
```

---

## ✅ 编辑热搜词 — ops.merchant.hot-keyword.update

### 入参

同创建（`id` 额外必填）。

### 调用示例

```json
{"capability":"ops.merchant.hot-keyword.update","input":{"id":"6100012345678901234","keyword":"研学营地","sortWeight":5,"badgeType":2,"status":1},"summary":"调整热搜词权重与角标"}
```

---

## ✅ 启停热搜词 — ops.merchant.hot-keyword.update-status

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 热搜词ID |
| status | Integer | ✅ | 0=停用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.hot-keyword.update-status","input":{"id":"6100012345678901234","status":0},"summary":"停用热搜词"}
```

---

## ✅ 删除热搜词 — ops.merchant.hot-keyword.delete

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 热搜词ID |

### 调用示例

```json
{"capability":"ops.merchant.hot-keyword.delete","input":{"id":"6100012345678901234"},"summary":"删除过期热搜词"}
```

---

## ✅ 热搜词批量排序 — ops.merchant.hot-keyword.sort

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | Array | ✅ | ≥1 项：`{id, sortWeight}`，均必填 |

### 调用示例

```json
{"capability":"ops.merchant.hot-keyword.sort","input":{"items":[{"id":"6100012345678901234","sortWeight":1},{"id":"6100012345678901235","sortWeight":2}]},"summary":"批量调整热搜词顺序"}
```

---

## ✅ 新增 NLU 干预规则 — ops.merchant.search-intervention.nlu.create

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ruleType | String | ✅ | `nlu_rewrite`/`nlu_synonym`/`nlu_spell`/`nlu_suffix_replace` |
| ruleKey | String | ✅ | 规则键，≤255 字符 |
| ruleValue | String | 条件 | 规则值——`nlu_suffix_replace` 可空，**其余类型必填**（服务端校验） |
| description | String | 否 | ≤512 字符 |
| status | Integer | 否 | 0=禁用 1=启用，默认 1 |

### 出参（原始返回）

`data` 为新建规则ID。

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.nlu.create","input":{"ruleType":"nlu_synonym","ruleKey":"球鞋","ruleValue":"运动鞋","description":"同义词归一"},"summary":"新增球鞋同义词归一规则"}
```

---

## ✅ 编辑 NLU 干预规则 — ops.merchant.search-intervention.nlu.update

- 规则类型不可改（只更新键值/描述/状态）
- **注意**：编辑侧服务端不做跨字段必填校验（创建侧有）——传空值不会报错但会存入无效配置，按该规则原类型完整传对应字段

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则ID |
| ruleKey | String | 否 | ≤255 字符 |
| ruleValue | String | 否 | — |
| description | String | 否 | ≤512 字符 |
| status | Integer | 否 | 0/1 |

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.nlu.update","input":{"id":"6200012345678901234","ruleValue":"运动鞋/球鞋","status":1},"summary":"补充同义词规则值"}
```

---

## ✅ 删除 NLU 干预规则 — ops.merchant.search-intervention.nlu.delete

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则ID |

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.nlu.delete","input":{"id":"6200012345678901234"},"summary":"删除NLU干预规则"}
```

---

## ✅ 启停 NLU 干预规则 — ops.merchant.search-intervention.nlu.update-status

- 启用/禁用会触发搜索侧规则集合刷新

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则ID |
| status | Integer | ✅ | 0=禁用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.nlu.update-status","input":{"id":"6200012345678901234","status":0},"summary":"禁用NLU干预规则"}
```

---

## ✅ 新增 Rerank 干预规则 — ops.merchant.search-intervention.rerank.create

- 按规则类型条件必填（服务端跨字段校验）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ruleType | String | ✅ | `rerank_manual`/`rerank_category_boost`/`rerank_diversity` |
| queryText | String | 条件 | 查询词，≤255；**rerank_manual 必填** |
| actionType | String | 条件 | **rerank_manual 必填**：`pin_items`/`filter_items`/`boost_items`/`penalty_items`/`boost_factor`/`penalty_factor` |
| actionValue | String | 条件 | **rerank_manual 必填**（如商品ID、加权倍数） |
| fieldName | String | 条件 | **rerank_category_boost 必填**，≤64 |
| matchType | String | 条件 | **rerank_category_boost 必填**：`exact`/`contains` |
| matchValue | String | 条件 | **rerank_category_boost 必填**，≤255 |
| boostFactor | Number | 条件 | **rerank_category_boost 必填且 > 0** |
| description | String | 否 | ≤512 字符 |
| status | Integer | 否 | 0=禁用 1=启用，默认 1 |

`rerank_diversity` 无必填参数（只传 ruleType 即可）。

### 出参（原始返回）

`data` 为新建规则ID。

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.rerank.create","input":{"ruleType":"rerank_manual","queryText":"研学","actionType":"pin_items","actionValue":"2058365707555589633","description":"研学词固定首位"},"summary":"新增研学词置顶干预规则"}
```

---

## ✅ 编辑 Rerank 干预规则 — ops.merchant.search-intervention.rerank.update

- 规则类型不可改
- **注意**：编辑侧服务端不做跨字段必填校验（创建侧有）——按该规则原类型完整传对应字段

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则ID |
| queryText / actionType / actionValue / fieldName / matchType / matchValue / boostFactor / description / status | — | 否 | 同创建的结构；按该规则原类型传对应字段 |

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.rerank.update","input":{"id":"6200012345678901235","actionType":"boost_factor","actionValue":"2.0","status":1},"summary":"调整干预规则为2倍加权"}
```

---

## ✅ 删除 Rerank 干预规则 — ops.merchant.search-intervention.rerank.delete

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则ID |

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.rerank.delete","input":{"id":"6200012345678901235"},"summary":"删除Rerank干预规则"}
```

---

## ✅ 启停 Rerank 干预规则 — ops.merchant.search-intervention.rerank.update-status

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则ID |
| status | Integer | ✅ | 0=禁用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.rerank.update-status","input":{"id":"6200012345678901235","status":1},"summary":"启用Rerank干预规则"}
```
