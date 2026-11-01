# 商户域 — 分类导航统计契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-category-nav.md`（数据表现复盘节）。
> 分类导航模板的数据表现查询：概览、核心指标、趋势与分类维度统计。模板操作见 `category-nav-query.md` / `category-nav-action.md`。出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：category-nav.stats.overview 概览统计 · category-nav.stats.core 核心指标 · category-nav.stats.trend 趋势统计 · category-nav.stats.category 分类维度统计

**公共入参**（四个统计能力共享）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 模板 ID（路径参数） |
| timeDimension | String | 否 | `LAST_7_DAYS` / `LAST_30_DAYS` / `NATURAL_DAY` / `NATURAL_WEEK` / `NATURAL_MONTH`（大写） |
| date | String | 否 | 日期（NATURAL_* 维度用，`yyyy-MM-dd`） |

---

## ✅ 概览统计 — ops.merchant.category-nav.stats.overview

### 出参（原始数据）

- **格式敏感字段**：`productClickRate`（百分比，数字）、`orderConversionRate`（百分比，数字）、`avgStayDuration`（秒，数字）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.stats.overview","input":{"id":"6800012345678901234","timeDimension":"LAST_7_DAYS"},"summary":"看最近7天导航的整体转化概览"}
```

---

## ✅ 核心指标 — ops.merchant.category-nav.stats.core

### 出参（原始数据）

- **格式敏感字段**：`pageViews`/`uniqueVisitors`/`orderCount`（整数计数）；`fanPvRatio`/`fanUvRatio`/`fanOrderRatio`（百分比，数字——粉丝维度占比）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.stats.core","input":{"id":"6800012345678901234","timeDimension":"LAST_30_DAYS"},"summary":"看最近30天的PV UV和订单数"}
```

---

## ✅ 趋势统计 — ops.merchant.category-nav.stats.trend

### 出参（列表，原始数据）

- **格式敏感字段**：`[].statDate`（yyyy-MM-dd）、`[].pageViews`/`[].uniqueVisitors`/`[].orderCount`（整数）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.stats.trend","input":{"id":"6800012345678901234","timeDimension":"NATURAL_WEEK"},"summary":"看本周每天的趋势变化"}
```

---

## ✅ 分类维度统计 — ops.merchant.category-nav.stats.category

### 入参（在公共入参之上）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | 否 | 默认 1/20，pageSize ≤100 |
| sortBy | String | 否 | **白名单**：`categoryClickRate` / `avgProductClickRate`（不合法值服务端报错） |
| sortDirection | String | 否 | **白名单**：`ASC` / `DESC` |

### 出参（分页，原始数据）

- **展示字段**：`records[].categoryName`
- **格式敏感字段**：`records[].categoryClickRate`/`records[].avgProductClickRate`（百分比，数字）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.stats.category","input":{"id":"6800012345678901234","timeDimension":"LAST_7_DAYS","sortBy":"categoryClickRate","sortDirection":"DESC","pageNum":1,"pageSize":20},"summary":"按点击率排序列出表现最好的分类"}
```
