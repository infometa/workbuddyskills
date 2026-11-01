# 物流域 — 行政区划查询契约

> 概念知识：`references/domains/logistics.md`；运营流程：`references/flows/logistics.md`
> 区划采用六位标准编码并逐级查询；不要用名称代替编码，也不要自行拼接子级编码。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.logistics.`）：查询 region.provinces · region.children

---

## ✅ 省级区划查询 — ops.logistics.region.provinces

查询全部省级区划。入参为空对象；返回元素含 `code` 与 `name`。

```json
{"capability":"ops.logistics.region.provinces","input":{},"summary":"查询省级行政区划"}
```

---

## ✅ 子级区划查询 — ops.logistics.region.children

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parentCode | String | 是 | 上一级查询结果的六位 `code`，不可用名称代替；六位格式是调用纪律，Java 当前只校验非空 |

返回直属子级的 `code/name` 数组；省编码返回市，市编码返回区。空数组表示无已登记子级。

```json
{"capability":"ops.logistics.region.children","input":{"parentCode":"440000"},"summary":"查询广东省下属城市"}
```
