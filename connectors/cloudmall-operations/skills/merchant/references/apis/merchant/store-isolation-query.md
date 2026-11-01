# 商户域 — 门店隔离与网店模式查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-store.md`（门店隔离与网店模式节）；隔离写操作见 `store-isolation-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：store-isolation.search 门店隔离分页 · store-isolation.store-ids 已隔离门店ID全集 · store-mode.get 网店模式查询

---

## ✅ 门店隔离分页 — ops.merchant.store-isolation.search

- **说明**：多网点模式下，查询门店与其隔离门店（数据互不可见）的关联配置分页。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 默认 20 |
| storeName | String | 否 | 门店名称模糊筛选 |
| storeCode | String | 否 | 门店编码筛选 |
| isolated | Boolean | 否 | 隔离状态筛选（true=仅隔离生效中 / false=仅已解除） |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 隔离记录的启停/删除路径参数）
- **模型说明**：**一条记录 = 一个被隔离门店**（扁平结构，无主体/被隔离嵌套）；字段含 `storeId`/`storeName`/`storeCode`/`storeAddress`/`storeStatus`/`isolated`（Boolean，是否处于隔离状态）等，以响应为准

### 调用示例

```json
{"capability":"ops.merchant.store-isolation.search","input":{"pageNum":1,"pageSize":20},"summary":"看下当前配置了哪些门店隔离关系"}
```

---

## ✅ 已隔离门店 ID 全集 — ops.merchant.store-isolation.store-ids

- **说明**：全量返回已参与隔离的门店 ID 列表；配置新隔离前先查本接口排除已隔离门店。

### 入参

无。

### 出参（原始数据）

- `List<string>`（已隔离门店 ID 全集）

### 调用示例

```json
{"capability":"ops.merchant.store-isolation.store-ids","input":{},"summary":"查一下哪些门店已经在隔离配置里了"}
```

---

## ✅ 网店模式查询 — ops.merchant.store-mode.get

### 入参

无。

### 出参（原始数据）

- **枚举字段**：`mode`（`single` 单网点 / `multi` 多网点，小写）
- **关键字段来源**：`version`（Long，乐观锁——update 必传）
- 其余配置字段以响应为准。

### 调用示例

```json
{"capability":"ops.merchant.store-mode.get","input":{},"summary":"看下当前是单网点还是多网点模式"}
```
