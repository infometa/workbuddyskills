# 商品域 — 描述属性写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-dictionary.md`；现态读取（属性台账）先读 `description-attribute-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：description-attribute.create 新增描述属性 · description-attribute.update 编辑描述属性 · description-attribute.delete 删除描述属性 🔴

---

## ✅ 新增描述属性 — ops.product.description-attribute.create

- **语义**：在类目下新增发品描述属性，可一并创建预设值。**同一类目下属性名称唯一**，重名被拒绝。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| attributeName | String | ✅ | 属性名称（≤20 字符） |
| categoryCode | String | ✅ | 类目编码（来自 category.tree） |
| interactionType | String | ✅ | 交互方式：`TEXT_INPUT` / `NUMBER_INPUT` / `SELECT_SINGLE` / `SELECT_MULTIPLE` |
| attributeValues | List | — | 预设值列表（结构见下） |

**attributeValues[] 子结构**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | — | 已有值传 ID；新增值不传 |
| value | String | ✅ | 属性值内容（≤100 字符） |
| sortOrder | Integer | — | 排序（≥0） |

### 调用示例

```json
{"capability":"ops.product.description-attribute.create","input":{"attributeName":"适合年龄","categoryCode":"T900001_C61","interactionType":"SELECT_SINGLE","attributeValues":[{"value":"6-12岁","sortOrder":0}]},"summary":"在研学类目新增适合年龄描述属性"}
```

---

## ✅ 编辑描述属性 — ops.product.description-attribute.update

- **语义**：修改属性名称/类目/交互方式；`attributeValues` 为**全量覆盖**（最多 20 个）——未出现在列表中的旧值会被删除，编辑前先读现态。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 属性 ID（路径参数，来自 page 分页） |
| attributeName | String | ✅ | 属性名称（≤20 字符） |
| categoryCode | String | ✅ | 类目编码 |
| interactionType | String | ✅ | 同 create 枚举 |
| attributeValues | List | — | 属性值**全量覆盖**（≤20 个；结构同 create） |

### 调用示例

```json
{"capability":"ops.product.description-attribute.update","input":{"id":"2200012345678901234","attributeName":"适合年龄","categoryCode":"T900001_C61","interactionType":"SELECT_SINGLE","attributeValues":[{"value":"6-12岁","sortOrder":0},{"value":"12-18岁","sortOrder":1}]},"summary":"为适合年龄属性补充青少年预设值"}
```

---

## ✅ 删除描述属性 — ops.product.description-attribute.delete

- 🔴 不可逆；执行前向用户确认属性名称与所属类目
- **语义**：逻辑删除描述属性（连同预设值一起失效）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 属性 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.description-attribute.delete","input":{"id":"2200012345678901234"},"summary":"删除适合年龄描述属性"}
```
