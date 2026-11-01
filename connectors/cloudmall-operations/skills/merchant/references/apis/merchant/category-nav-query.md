# 商户域 — 分类导航模板查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-category-nav.md`；写操作见 `category-nav-action.md`；前台分类与商品关联见 `category-nav-content-query.md` / `category-nav-content-action.md`；数据统计见 `category-nav-stats.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **核心模型**：模板 = 导航版本容器（状态机 draft→published→offline，已下线可重新发布）；默认兜底模板全租户仅一个（未命中可见性规则的门店走默认模板）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：category-nav.list 模板分页 · category-nav.detail 模板详情 · category-nav.store-visibility.get 门店可见性查询 · category-nav.invalid-store-bindings.check 无效门店绑定检测 · category-nav.export 导出模板

---

## ✅ 模板分页 — ops.merchant.category-nav.list

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..50，默认 10 |
| status | String | 否 | `draft` / `published` / `offline` / `disabled`（小写），省略=全部 |
| storeIds | array&lt;String&gt; | 否 | 门店 ID 列表筛选 |
| updatedBy | String | 否 | 更新人姓名模糊匹配，≤64 字 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 所有 `/{id}` 路径参数）
- **枚举字段**：`status`（draft/published/offline/disabled）、`layoutMode`（CLASSIC/THREE_LEVEL/BRAND，大写）、`storeScope`（ALL/SPECIFIED，大写）、`iconShape`（circle/square，小写）
- **格式敏感字段**：`updatedTime`（yyyy-MM-dd HH:mm:ss）
- **门店信息字段**：`stores[]`（storeScope=SPECIFIED 时为关联门店列表：`id`/`name`；ALL 或无关联时为空列表）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.list","input":{"pageNum":1,"pageSize":10,"status":"published"},"summary":"看下当前在线的分类导航"}
```

---

## ✅ 模板详情 — ops.merchant.category-nav.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | **模板 ID（注意参数名是 `id`，不是 `categoryId`/`navId`/`templateId`）** |

### 出参（原始数据）

- **路径参数来源**：`id`（→ 编辑/发布/复制等操作）
- **枚举字段**：`status`、`layoutMode`、`storeScope`、`iconShape`（同列表）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.detail","input":{"id":"6800012345678901234"},"summary":"看这个导航模板的配置详情"}
```

---

## ✅ 门店可见性查询 — ops.merchant.category-nav.store-visibility.get

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 模板 ID |

### 出参（原始数据）

- `List<string>`（已关联门店 ID 列表）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.store-visibility.get","input":{"id":"6800012345678901234"},"summary":"看这个导航当前对哪些门店可见"}
```

---

## ✅ 无效门店绑定检测 — ops.merchant.category-nav.invalid-store-bindings.check

- **说明**：检测已被删除但仍被模板关联的门店（脏数据治理）。check 无入参。

### 出参（原始数据）

- `hasInvalid` + `invalidBindings[]`（templateId/templateName/shopId）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.invalid-store-bindings.check","input":{},"summary":"检查有没有已删除门店的残留绑定"}
```

---

## ✅ 导出模板 — ops.merchant.category-nav.export

- **说明**：导出指定模板的完整配置 Excel，返回 COS 预签名下载 URL（分钟级时效）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 模板 ID |

### 出参（原始数据）

- **枚举字段**：`mode`（sync/async）
- **展示字段**：`downloadUrl`（COS 预签名下载 URL）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.export","input":{"id":"6800012345678901234"},"summary":"导出这个导航模板的配置"}
```

---

## ⛔ 未开放（分类导航模板）

无——含导出在内的模板管理端点均已开放。
