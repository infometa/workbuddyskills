# 商品域 — 类目与品牌查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-dictionary.md`；类目结构维护与品牌增改/绑定写操作见 `category-brand-action.md`；描述属性的增改删维护见 `description-attribute-action.md`，商品扩展字段配置见 `extension-field-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：category.tree 类目树 · category.options 类目平铺选项 · category.search 类目搜索 · brand.options 品牌选项 · brand.page 品牌分页 · brand.detail 品牌详情 · brand.spus 品牌关联商品 · description-attribute.by-category 按类目查描述属性

---

## ✅ 类目树 — ops.product.category.tree

- **语义**：全量类目树（1~5 级）；发品与筛选时取 `categoryCode`，**类目名称不能代替编码**

### 入参

无（空对象 `{}`；懒加载单层 `parentCode` 与业务大类 `bizType` 过滤未开放）。

### 出参（递归树，原始数据）

- **关键字段来源**：`categoryCode`（→ 搜索 `categoryCodes[]`、创建/编辑 `categoryCode`）
- **格式敏感字段**：`parentCode`（根节点为空字符串）、`level`（1..5）
- 树节点含 `categoryCode/categoryName/parentCode/level/sortOrder/children[]`（递归）。

### 调用示例

```json
{"capability":"ops.product.category.tree","input":{},"summary":"获取类目树定位目标类目编码"}
```

---

## ✅ 类目平铺选项 — ops.product.category.options

- **语义**：类目平铺选项列表（id + name）；与类目树同源，适合已知类目 ID 反查名称

### 入参

无（空对象 `{}`）。

### 出参（数组，原始数据）

- **关键字段来源**：`id`（类目 ID）、`name`
- 字段：`id`（string）、`name`。

### 调用示例

```json
{"capability":"ops.product.category.options","input":{},"summary":"获取类目平铺选项"}
```

---

## ✅ 类目搜索 — ops.product.category.search

- **语义**：按关键词搜索类目，返回从根到命中节点的完整路径（定位深层类目时比遍历树更快）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | ✅ | 关键词（≤64 字符） |

### 出参（数组，原始数据）

- **关键字段来源**：`categoryCode`（→ 发品 `categoryCode`）
- **格式敏感字段**：`path[]`（从根到该节点的编码列表，用于确认层级位置）
- 字段：`categoryCode`、`categoryName`、`path[]`。

### 调用示例

```json
{"capability":"ops.product.category.search","input":{"keyword":"研学"},"summary":"搜索研学相关类目定位编码"}
```

---

## ✅ 品牌选项 — ops.product.brand.options

- **语义**：品牌下拉选项；发品时取 `id` 作为 `brandId`（PHYSICAL/VIRTUAL 必填），**品牌名不能代替 ID**

### 入参

无（空对象 `{}`）。

### 出参（数组，原始数据）

- **关键字段来源**：`id`（→ 搜索 `brandId`、创建/编辑 `brandId`）
- 选项字段：`id`（→ brandId）、`name`。

### 调用示例

```json
{"capability":"ops.product.brand.options","input":{},"summary":"获取品牌选项定位品牌ID"}
```

---

## ✅ 品牌分页 — ops.product.brand.page

- **语义**：品牌管理分页列表（品牌选项之外的管理视角，可按 ID/名称过滤）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数（≤100） |
| brandId | String | — | 品牌 ID（精确） |
| brandName | String | — | 品牌名称（模糊） |

### 出参（`PageResult`，原始数据）

- **路径参数来源**：`records[].id`（→ brand.detail/delete/update/bind-spus 路径/入参）
- 字段：`id`、`name`、`logo` 等。

### 调用示例

```json
{"capability":"ops.product.brand.page","input":{"pageNum":1,"pageSize":20,"brandName":"研学"},"summary":"分页查找名称含研学的品牌"}
```

---

## ✅ 品牌详情 — ops.product.brand.detail

- **语义**：单个品牌的详情（编辑前读现态）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 品牌 ID（来自 brand.page/options） |

### 出参（原始数据）

- 字段：`id`、`name`、`logo`、关联 SPU 数量等。

### 调用示例

```json
{"capability":"ops.product.brand.detail","input":{"id":"2100012345678901234"},"summary":"查看品牌详情确认现态"}
```

---

## ✅ 品牌关联商品 — ops.product.brand.spus

- **语义**：某品牌下关联 SPU 的分页列表（解绑前确认对象）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 品牌 ID（路径参数） |
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数 |

### 出参（`PageResult`，原始数据）

- **路径参数来源**：`records[].spuId`（→ unbind-spus 的 spuIds）
- 字段：`spuId`、`spuName` 等。

### 调用示例

```json
{"capability":"ops.product.brand.spus","input":{"id":"2100012345678901234","pageNum":1,"pageSize":20},"summary":"查看品牌下关联的商品清单"}
```

---

## ✅ 按类目查描述属性 — ops.product.description-attribute.by-category

- **语义**：发品/编辑前的描述模板参考——该类目下可选的描述属性及预设值

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| categoryCode | String | ✅ | 类目编码（来自 `ops.product.category.tree` 的类目节点） |

### 出参（原始返回）

`data[]` 为描述属性视图（属性名 + 预设值列表）。

### 调用示例

```json
{"capability":"ops.product.description-attribute.by-category","input":{"categoryCode":"STUDY_TOUR"},"summary":"查询研学类目的描述属性"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 平台类目同步（一键复制平台模板类目树） | 一次性初始化/修复运维面（租户已有类目时幂等拒绝），非常规运营操作 |
| 分类导航 ES 索引重建（全量/单分类） | 运维面 |
| 分类导航门店 Redis 缓存重建 | 运维面 |
