# 商户域 — 前台分类与商品关联写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-category-nav.md`；现值读取（分类树/分类商品）先读 `category-nav-content-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：category-nav.front-category.batch-save 前台分类批量保存 🔴 · category-nav.category-products.add 分类商品添加 · category-nav.category-products.remove 分类商品移除 · category-nav.link-backend-category.preview 关联后台类目预览 · category-nav.link-backend-category 关联后台类目 🔴 · category-nav.clear-product-config 清空分类商品配置 🔴

---

## ✅ 前台分类批量保存 — ops.merchant.category-nav.front-category.batch-save

- 🔴 结构性变更（单事务处理增/改/删/排序；删除分类会级联删除其商品关联）
- **说明**：同一事务内处理分类的新增、更新、删除、排序变更。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | 是 | 模板 ID |
| additions | array | 否 | 新增分类：`tempId`（前端临时ID，必填）/`name`（≤10 字，必填）/`parentId`（"0"=根，必填）/`level`（1..3，必填）/`sortOrder`（≥0，必填）/`iconUrl`/`coverImage`（三级分类用）/`componentsJson`（结构见下） |
| updates | array | 否 | 更新分类：`categoryId`（必填）+ 可选 name/sortOrder/iconUrl/coverImage/componentsJson |
| deletions | array&lt;String&gt; | 否 | 删除分类 ID 列表 |
| sortChanges | array | 否 | `[{categoryId, sortOrder}]` |

**`componentsJson` 结构**（仅 `layoutMode=BRAND` 品牌布局的二级分类使用；JSON 字符串，≤512 字符；**服务端不解析其业务结构**——仅递归剥除/重签其中 COS URL，其余原样存储并由 C 端消费）：

```json
[{
  "id": "组件ID",
  "type": "categoryBanner | categoryGoodsGrid | categoryGoodsList",
  "props": { /* 按 type 分支 */ }
}]
```

| type | props 字段 |
|---|---|
| `categoryBanner` | `imageUrl`（图片 URL）、`description`（描述文案）、`hotZones[]`（热区：`id`/`x`/`y`/`width`/`height` 坐标 + `linkUrl` 跳转链接） |
| `categoryGoodsGrid` | `productIds[]`（SPU ID 列表）、`maxCount`（最大展示数） |
| `categoryGoodsList` | 同 categoryGoodsGrid |

⚠️ BRAND 布局下分类的商品配置部分承载于组件 `props.productIds`（编辑该分类商品时以 tree/detail 回填的 componentsJson 为基础修改后整体回传，不要丢弃未提及的组件）；非 BRAND 布局不需要该字段。

### 出参（原始数据）

- **映射字段**：`idMapping`（Map：tempId → 实际分类 ID——新增分类的临时 ID 换真实 ID，后续 productChanges 等操作使用真实 ID）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.front-category.batch-save","input":{"templateId":"6800012345678901234","additions":[{"tempId":"tmp-1","name":"秋季新品","parentId":"0","level":1,"sortOrder":0}],"updates":[{"categoryId":"6900012345678901234","name":"冬季新品","sortOrder":1}]},"summary":"新增秋上新一级分类并把原一级分类改名为冬季新品"}
```

---

## ✅ 分类商品添加 — ops.merchant.category-nav.category-products.add

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| categoryId | String | 是 | 前台分类 ID（路径参数） |
| spuIds | array&lt;String&gt; | 是 | SPU ID 列表（来自 `ops.product.spu.search`），1..200 项 |
| source | String | 是 | `manual` / `id_import`（小写） |

### 出参

- `addedCount`（成功数）、`duplicateCount`（重复数）、`invalidIds[]`（无效商品 ID——**部分成功语义**，逐项报告）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.category-products.add","input":{"categoryId":"6900012345678901234","spuIds":["2058365707555589633"],"source":"manual"},"summary":"把研学营这个商品加到秋上新分类"}
```

---

## ✅ 分类商品移除 — ops.merchant.category-nav.category-products.remove

### 入参

categoryId（路径）+ `spuIds`（要移除的 SPU ID 列表，必填）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.category-products.remove","input":{"categoryId":"6900012345678901234","spuIds":["2058365707555589633"]},"summary":"把这个下架商品从分类里移除"}
```

---

## ✅ 关联后台类目预览 — ops.merchant.category-nav.link-backend-category.preview

- 🟡 无副作用（只读预览）
- **说明**：确认关联前预估导入商品数量。**先预览后关联**是本模块的强制流程纪律。

### 入参

同 link-backend-category（categoryId 路径 + backendCategoryCodes/mode）。

### 出参（原始数据）

- **统计字段**：`backendProductCount`（后台类目去重商品数）、`importableProductCount`（预计新增导入数）、`retainedManualProductCount`（保留的手动商品数）、`finalProductCount`（预计最终商品数）、`maxProductCount`（单分类商品上限）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.link-backend-category.preview","input":{"categoryId":"6900012345678901234","backendCategoryCodes":["C1001"],"mode":"dynamic"},"summary":"预览关联研学类目会导入多少商品"}
```

---

## ✅ 关联后台类目 — ops.merchant.category-nav.link-backend-category

- 🔴 商业影响（动态模式下类目商品变化会实时同步进分类）
- **前置**：先执行 preview 并向用户确认预估数量。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| categoryId | String | 是 | 前台分类 ID（路径参数） |
| backendCategoryCodes | array&lt;String&gt; | 是 | 后台类目编码列表（来自 `ops.product.category.tree`；**空列表=清空关联**），每项 ≤64 字 |
| mode | String | 是 | `dynamic`（动态同步）/ `snapshot`（快照导入），小写 |

### 出参（原始数据）

- **统计字段**：`linkedProductCount`（关联的商品数量）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.link-backend-category","input":{"categoryId":"6900012345678901234","backendCategoryCodes":["C1001"],"mode":"dynamic"},"summary":"把研学类目动态关联到这个前台分类"}
```

---

## ✅ 清空分类商品配置 — ops.merchant.category-nav.clear-product-config

- 🔴 不可逆（同时清除商品关联 + 后台类目关联）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| categoryId | String | 是 | 前台分类 ID |

### 调用示例

```json
{"capability":"ops.merchant.category-nav.clear-product-config","input":{"categoryId":"6900012345678901234"},"summary":"清空这个分类的全部商品配置重新来"}
```

---

## ⛔ 未开放（前台分类写操作）

无——本模块全部端点已开放。
