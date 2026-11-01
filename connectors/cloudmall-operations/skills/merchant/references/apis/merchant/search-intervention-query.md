# 商户域 — 热搜词与搜索干预查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-search.md`；写操作见 `search-intervention-action.md`；暗纹词与场景见 `placeholder-query.md` / `placeholder-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。⚠️ 本文件枚举**全部小写**（nlu_*、rerank_* 等），与门店域大写枚举不同，严格按参数表取值。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：hot-keyword.search 热搜词分页 · search-intervention.nlu.search NLU 干预规则分页 · search-intervention.rerank.search Rerank 干预规则分页 · search-intervention.operation-logs 干预规则操作日志

---

## ✅ 热搜词分页 — ops.merchant.hot-keyword.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | 默认 1 |
| pageSize | Integer | 否 | 默认 20，最大 100 |
| status | Integer | 否 | null=全部 0=停用 1=启用 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 编辑/启停/删除/排序的 id）
- **枚举字段**：`status`（0/1）、`badgeType`（0=无 1=新 2=热）
- **格式敏感字段**：`startTime`/`endTime`（yyyy-MM-dd HH:mm:ss；null=立即生效/长期有效）、`updatedTime`（同格式）
- `sortWeight` 越小越靠前。

### 调用示例

```json
{"capability":"ops.merchant.hot-keyword.search","input":{"pageNum":1,"pageSize":20,"status":1},"summary":"查看启用中的热搜词"}
```

---

## ✅ NLU 干预规则分页 — ops.merchant.search-intervention.nlu.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | 默认 1 |
| pageSize | Integer | 否 | 默认 20，最大 100 |
| ruleType | String | 否 | `nlu_rewrite`/`nlu_synonym`/`nlu_spell`/`nlu_suffix_replace` |
| status | Integer | 否 | 0=禁用 1=启用 |
| ruleKey | String | 否 | 规则键模糊搜索 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 编辑/启停/删除/操作日志的 ruleId）
- **枚举字段**：`ruleType`（四类小写）、`status`（0/1）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.nlu.search","input":{"pageNum":1,"pageSize":20,"ruleType":"nlu_rewrite","status":1},"summary":"查看启用中的NLU改写规则"}
```

---

## ✅ Rerank 干预规则分页 — ops.merchant.search-intervention.rerank.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | 默认 1 |
| pageSize | Integer | 否 | 默认 20，最大 100 |
| ruleType | String | 否 | `rerank_manual`/`rerank_category_boost`/`rerank_diversity` |
| status | Integer | 否 | 0=禁用 1=启用 |
| queryText | String | 否 | 查询词模糊搜索 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 编辑/启停/删除/操作日志的 ruleId）
- **枚举字段**：`ruleType`（三类小写）、`actionType`（六类小写）、`matchType`（exact/contains）、`status`（0/1）
- **格式敏感字段**：`boostFactor`（数字，>0）、`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.rerank.search","input":{"pageNum":1,"pageSize":20,"ruleType":"rerank_manual","status":1},"summary":"查看启用中的人工干预规则"}
```

---

## ✅ 干预规则操作日志 — ops.merchant.search-intervention.operation-logs

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ruleId | String | ✅ | 规则ID |
| ruleCategory | String | ✅ | `nlu`/`rerank` |

### 出参（数组，原始数据）

- **枚举字段**：`operationType`（字面值为英文码：CREATE/UPDATE/DELETE/ENABLE/DISABLE，即创建/更新/删除/启用/禁用）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）
- `detail` 为变更明细 JSON 文本，按操作类型四形态：CREATE=`{action, after}`、UPDATE=`{action, before, after, changedFields[]}`、DELETE=`{action, before}`、ENABLE/DISABLE=`{action, before, after}`；其中 `before`/`after` 快照键为 `ruleType/ruleKey/ruleValue/description/status`（NLU）或对应 Rerank 字段。

### 调用示例

```json
{"capability":"ops.merchant.search-intervention.operation-logs","input":{"ruleId":"6200012345678901234","ruleCategory":"nlu"},"summary":"查看NLU规则变更历史"}
```
