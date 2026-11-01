# 商品域 — 商品扩展字段写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-dictionary.md`；现态读取（字段台账）先读 `extension-field-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：extension-field.create 新增扩展字段 · extension-field.update 编辑扩展字段 · extension-field.set-enabled 扩展字段启停 · extension-field.sort 扩展字段排序 · extension-field.delete 删除扩展字段 🔴

---

## ✅ 新增扩展字段 — ops.product.extension-field.create

- **语义**：新增一个商品扩展字段定义（发品表单可配置字段）。`fieldCode + targetLevel` 组合唯一，重复被拒绝。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fieldCode | String | ✅ | 字段编码：小写字母开头，2-64 位小写字母/数字/下划线（如 `service_duration`） |
| fieldName | String | ✅ | 字段名称（≤64 字符） |
| targetLevel | String | ✅ | 字段层级：`ALL` / `SPU` / `SKU` |
| fieldType | String | ✅ | 字段类型：`TEXT` / `TEXTAREA` / `NUMBER` / `MONEY` / `DATE` / `DATETIME` / `BOOLEAN` / `SINGLE_SELECT` / `MULTI_SELECT` / `CASCADE` / `IMAGE` / `FILE` |
| description | String | — | 字段说明（≤512 字符） |
| placeholder | String | — | 占位提示（≤256 字符） |
| defaultValue | String | — | 默认值 |
| optionConfig | String | — | 选项配置：**JSON 字符串**，内容为数组 `[{"code":"选项值","label":"显示名"}]`（选择类字段 SINGLE_SELECT/MULTI_SELECT/CASCADE 使用） |
| validationConfig | String | — | 校验配置：**服务端不解析**（透传存储与回显，无固定结构约定），不要依赖其产生任何服务端校验效果 |
| requiredMode | String | — | 必填规则：`NONE` / `ALWAYS` / `CONDITION`。⚠️ **服务端仅强制 ALWAYS**（发品时该字段缺失/为空报错）；CONDITION 的条件必填校验**服务端不执行**（linkageConfig 为前端表单联动配置，服务端不解析）——CONDITION 字段发品时不满足条件也不报错 |
| linkageConfig | String | — | 条件必填规则：**JSON 字符串**，内容为数组 `[{"field":"依赖字段编码","operator":"比较符","value":"比较值"}]`（requiredMode=CONDITION 时配）。**服务端不解析该结构**（透传存储与回显，operator 值域由前端表单约定），不要依赖服务端校验其内容 |
| enabled | Boolean | — | 是否启用 |
| editable | Boolean | — | 发品时是否可编辑（系统预置字段常为 false） |
| productListVisible | Boolean | — | 商品列表可见 |
| productFilterable | Boolean | — | 商品列表可筛选 |
| productExportable | Boolean | — | 商品导出包含 |
| sortOrder | Integer | — | 排序 |

### 调用示例

```json
{"capability":"ops.product.extension-field.create","input":{"fieldCode":"service_duration","fieldName":"服务时长","targetLevel":"SPU","fieldType":"NUMBER","requiredMode":"NONE","enabled":true,"editable":true,"sortOrder":1},"summary":"新增 SPU 级服务时长扩展字段"}
```

---

## ✅ 编辑扩展字段 — ops.product.extension-field.update

- **语义**：修改字段定义。入参与 create 同构，另需路径 `id`；编辑前先查分页读现态，保留未要求修改的字段。

### 入参

与 create 同构，另需：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 字段 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.extension-field.update","input":{"id":"2300012345678901234","fieldCode":"service_duration","fieldName":"服务时长","targetLevel":"SPU","fieldType":"NUMBER","requiredMode":"ALWAYS","enabled":true,"editable":true,"sortOrder":1},"summary":"把服务时长字段改为必填"}
```

---

## ✅ 扩展字段启停 — ops.product.extension-field.set-enabled

- **语义**：单独切换字段启用状态（停用后发品表单不再展示该字段）；停用优先于删除。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 字段 ID（路径参数） |
| enabled | Boolean | ✅ | 目标状态 |

### 调用示例

```json
{"capability":"ops.product.extension-field.set-enabled","input":{"id":"2300012345678901234","enabled":false},"summary":"停用服务时长扩展字段"}
```

---

## ✅ 扩展字段排序 — ops.product.extension-field.sort

- **语义**：批量设置字段展示顺序（发品表单与列表的展示顺序）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | List | ✅ | 排序列表（非空） |

**items[] 子结构**：`id`（✅ string，字段 ID）、`sortOrder`（✅ Integer，目标排序值）。

### 调用示例

```json
{"capability":"ops.product.extension-field.sort","input":{"items":[{"id":"2300012345678901234","sortOrder":1}]},"summary":"调整扩展字段展示顺序"}
```

---

## ✅ 删除扩展字段 — ops.product.extension-field.delete

- 🔴 不可逆；优先考虑 `set-enabled` 停用替代删除；删除前向用户确认字段名。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 字段 ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.extension-field.delete","input":{"id":"2300012345678901234"},"summary":"删除服务时长扩展字段"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 系统预置字段批量种入（batch） | schema 初始化/补种运维面（幂等），非日常运营操作 |
