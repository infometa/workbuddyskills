# 商品域 — 静态标签写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-tag.md`；现态读取（标签列表/当前关联）先读 `static-tag-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：static-tag.create 新增标签 · static-tag.update 编辑标签 · static-tag.priority 标签优先级 · static-tag.bind-skus 绑定SKU（全量提交）🔴 · static-tag.delete 删除标签 🔴 · static-tag.batch-delete 批量删除标签 🔴

---

## ✅ 新增标签 — ops.product.static-tag.create

- **语义**：新建商品静态标签（SKU 级打标用）。
- **唯一性预检**：标签名称唯一，创建/改名前先用 `static-tag.search` 按名称查重；命中同名时与用户确认换名或复用，不直接提交。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tagName | String | ✅ | 标签名称（≤10 字符） |
| priority | Integer | ✅ | 优先级 1~9999（值越大越靠前，以列表页实际排序为准） |
| validityType | String | ✅ | 有效期类型：`PERMANENT`（永久）/ `CUSTOM`（自定义区间） |
| validFrom | String | — | 有效期开始（`yyyy-MM-dd HH:mm:ss`；validityType=CUSTOM 时必填） |
| validTo | String | — | 有效期结束（CUSTOM 时必填，且 ≥ validFrom） |

### 调用示例

```json
{"capability":"ops.product.static-tag.create","input":{"tagName":"热销","priority":100,"validityType":"PERMANENT"},"summary":"新建热销标签"}
```

---

## ✅ 编辑标签 — ops.product.static-tag.update

- **语义**：编辑标签定义（名称/优先级/有效期）；入参与 create 同构，另需路径 `id`。编辑前先读分页确认现态。

### 入参

与 create 同构，另需：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.static-tag.update","input":{"id":"8000012345678901234","tagName":"限时热销","priority":100,"validityType":"PERMANENT"},"summary":"把热销标签更名为限时热销"}
```

---

## ✅ 标签优先级调整 — ops.product.static-tag.priority

- **语义**：单独调整一个标签的优先级（列表行内编辑口径）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID（路径参数） |
| priority | Integer | ✅ | 新优先级 1~9999 |

### 调用示例

```json
{"capability":"ops.product.static-tag.priority","input":{"id":"8000012345678901234","priority":50},"summary":"把标签优先级调整为50"}
```

---

## ✅ 保存标签-SKU 关联 — ops.product.static-tag.bind-skus

- 🔴 商业影响档位（含清空风险）；**全量提交语义**——`skuIds` 为该标签的最终关联集合，服务端对比当前关联做差量增删；提交前向用户复述新增/移除清单；空数组 = 清空关联，谨慎执行

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签ID |
| skuIds | String[] | ✅ | 最终关联的 SKU 业务ID 全集（空数组 = 清空关联，谨慎执行） |

### 出参（原始返回）

`data` 为 `null`（Void）；以 `static-tag.skus` 核验关联结果。

### 调用示例

```json
{"capability":"ops.product.static-tag.bind-skus","input":{"id":"8000012345678901234","skuIds":["9000012345678901234","9000012345678901235"]},"summary":"将两个SKU设为标签最终关联集合"}
```

---

## ✅ 删除标签 — ops.product.static-tag.delete

- 🔴 不可逆；删除前向用户确认标签名称；有关联 SKU 时建议先看 `static-tag.skus` 评估影响面
- **语义**：删除标签定义（关联关系随之失效）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.static-tag.delete","input":{"id":"8000012345678901234"},"summary":"删除标签「双11限定」"}
```

---

## ✅ 批量删除标签 — ops.product.static-tag.batch-delete

- 🔴 不可逆；删除前向用户确认标签名称清单；有关联 SKU 时先看 `static-tag.skus` 评估影响面
- **语义**：批量删除标签定义（关联关系随之失效）。
- 部分成功时回读 `static-tag.search` 核对实际剩余，向用户报告成功/失败明细。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | List&lt;String&gt; | ✅ | 标签 ID 列表（≤200，来自 static-tag.search） |

### 调用示例

```json
{"capability":"ops.product.static-tag.batch-delete","input":{"ids":["8000012345678901234","8000012345678901235"]},"summary":"删除两个失效活动标签"}
```
