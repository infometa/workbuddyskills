# 物流域 — 快递公司查询契约

> 概念知识：`references/domains/logistics.md`；写操作（新增/编辑/启停/删除/微信运力同步）见 `express-company-action.md`；运营流程：`references/flows/logistics.md`
> 快递公司是共享配置；查询只取事实。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.logistics.`）：查询 express-company.search · express-company.enabled-list

---

## ✅ 快递公司搜索 — ops.logistics.express-company.search

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pageNum | Number | 否 | 默认 1，最小 1 |
| pageSize | Number | 否 | 默认 20，1～100 |
| keyword | String | 否 | 名称或编码模糊匹配，最多 50 字符 |
| status | Number | 否 | `0` 停用、`1` 启用 |

返回分页快递公司，关键字段有字符串 `id`、`companyName/companyCode/logoUrl/sortOrder/status/platformMappings[]`。

```json
{"capability":"ops.logistics.express-company.search","input":{"pageNum":1,"pageSize":20,"keyword":"顺丰","status":1},"summary":"查询启用的顺丰快递公司配置"}
```

---

## ✅ 启用快递公司列表 — ops.logistics.express-company.enabled-list

无入参；返回全部启用项的 `companyCode/companyName`，用于发货与售后选择。

```json
{"capability":"ops.logistics.express-company.enabled-list","input":{},"summary":"查询可用于发货的快递公司"}
```
