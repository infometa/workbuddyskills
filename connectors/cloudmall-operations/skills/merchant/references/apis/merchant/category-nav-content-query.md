# 商户域 — 前台分类与商品关联查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-category-nav.md`；写操作见 `category-nav-content-action.md`；模板级操作见 `category-nav-query.md` / `category-nav-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **核心模型**：
> - 前台分类支持三级层级（level 1/2/3，parentId="0" 为根）；**分类编辑即时落库（单一数据版本）**——模板未发布前 C 端不可见，publish 后生效。
> - 商品来源两种：**手动添加**（source=manual，逐个 SPU 关联）与**后台类目关联**（linkMode=`dynamic` 动态同步 / `snapshot` 快照导入）。
> - 跨域能力依赖：后台类目编码来自商品域 `ops.product.category.tree`（类目树查询）；候选商品来自 `ops.product.spu.search`（SPU 搜索）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：category-nav.front-category.tree 前台分类树查询 · category-nav.category-products.list 分类商品查询

---

## ✅ 前台分类树查询 — ops.merchant.category-nav.front-category.tree

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | 是 | 模板 ID |

### 出参（树形列表，原始数据）

- **路径参数来源**：`[].id`（→ 分类编辑/商品关联的 categoryId 路径参数）；`[].children[].id` 递归同
- **枚举字段**：`linkMode`（dynamic/snapshot，小写）
- **关联字段**：`backendCategoryCodes[]`（关联的后台类目编码列表）
- **展示字段**：`name`、`iconUrl`、`coverImage`、`sortOrder`、`level`

### 调用示例

```json
{"capability":"ops.merchant.category-nav.front-category.tree","input":{"templateId":"6800012345678901234"},"summary":"看这个导航模板的完整分类树"}
```

---

## ✅ 分类商品查询 — ops.merchant.category-nav.category-products.list

### 入参

categoryId（路径）+ pageNum/pageSize（1..100，默认 20）。

### 出参（分页，原始数据）

- **格式敏感字段**：`records[]`——`spuId`、`spuName`、`mainImage`、`sales`、`sortOrder`、`price`（元，数字）；分页信封。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.category-products.list","input":{"categoryId":"6900012345678901234","pageNum":1,"pageSize":20},"summary":"看下这个分类当前挂了哪些商品"}
```

---

## ⛔ 未开放（前台分类）

无——本模块全部端点已开放。
