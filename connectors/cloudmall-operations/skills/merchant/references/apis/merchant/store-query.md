# 商户域 — 门店查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-store.md`；门店写操作见 `store-action.md`，门店隔离与网店模式见 `store-isolation-query.md` / `store-isolation-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。按「关键字段来源 / 枚举 / 格式敏感 / 脱敏」四类标注，未列出的展示型字段以后端实际返回为准，透传给用户即可。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：store.search 门店分页搜索 · store.detail 门店详情 · store.options 营业中门店选项 · store.picker 门店选择器 · store.warehouses 门店已绑仓库 · store.pickup-sites 门店已绑自提点 · store.available-warehouses 门店可绑仓库 · store.available-pickup-sites 门店可绑自提点 · store.fulfillment-tree 全局履约树 · store.fulfillment-blocks 履约区块聚合 · store.export 导出门店列表

---

## ✅ 门店分页搜索 — ops.merchant.store.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| id | String | 否 | 门店ID精确匹配 |
| keyword | String | 否 | 门店名称/编码模糊匹配 |
| type | String | 否 | `PHYSICAL`/`VIRTUAL` |
| status | String | 否 | `DRAFT`/`ACTIVE`/`SUSPENDED`/`CLOSED` |
| orgNodeId | String | 否 | 所属组织节点ID |
| address | String | 否 | 地址模糊匹配 |
| provinceCode / cityCode / districtCode | String | 否 | 行政区划编码精确匹配 |
| createdTimeStart / createdTimeEnd | String | 否 | 创建时间区间（yyyy-MM-dd HH:mm:ss） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 门店详情/编辑/状态变更/设默认门店的 `input.id`）、`records[].warehouses[].warehouseId`（→ 仓库操作）、`records[].pickupSites[].id`（→ 自提点操作）
- **枚举字段**：`type`（PHYSICAL/VIRTUAL）、`status`（DRAFT/ACTIVE/SUSPENDED/CLOSED）、`isDefault`（0/1）、`warehouses[].warehouseType`、`warehouses[].isDefault`、`pickupSites[].isDefault`
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`businessHoursStart`/`businessHoursEnd`（HH:MM）

### 调用示例

```json
{"capability":"ops.merchant.store.search","input":{"pageNum":1,"pageSize":20,"keyword":"科技园","status":"ACTIVE"},"summary":"查找营业中的科技园门店"}
```

---

## ✅ 门店详情 — ops.merchant.store.detail

- 编辑回填与详情查看共用。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 门店ID（取搜索记录的 `id`） |

### 出参（原始数据）

- **关键字段来源**：`orgNodeId`/`parentOrgNodeId`（→ 编辑门店回填/组织树定位）、`version`（→ 编辑门店必传的乐观锁版本）
- **枚举字段**：`type`、`status`、`isDefault`（0/1）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`latitude`/`longitude`（GCJ-02 坐标，数字）
- 详情不含已绑仓库/自提点列表（用 store.warehouses / store.pickup-sites）。

### 调用示例

```json
{"capability":"ops.merchant.store.detail","input":{"id":"6000012345678901234"},"summary":"查看门店详情与乐观锁版本"}
```

---

## ✅ 门店选项列表 — ops.merchant.store.options

- **语义**：全部**营业中（ACTIVE）**门店的轻量下拉（id + 名称 + 地址），供选择器使用

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | 否 | 按门店名称过滤 |

### 出参（数组）

- **关键字段来源**：`id`（→ 各门店操作的 input.id）
- **枚举字段**：`status`（恒 ACTIVE）

### 调用示例

```json
{"capability":"ops.merchant.store.options","input":{"keyword":"科技园"},"summary":"列出营业中的科技园门店选项"}
```

---

## ✅ 门店选择器（进店规则兜底专用） — ops.merchant.store.picker

- **语义**：仅返回 ACTIVE 门店，默认门店固定排在第一页第一条；与 store.search 相互独立

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| keyword | String | 否 | 门店名称/编码模糊匹配 |

### 出参（分页）

- **关键字段来源**：`records[].id`（→ entry-rule.update-params 的 defaultStoreId）
- **枚举字段**：`isDefault`（0/1）

### 调用示例

```json
{"capability":"ops.merchant.store.picker","input":{"pageNum":1,"pageSize":20,"keyword":"默认"},"summary":"为进店规则挑选兜底门店"}
```

---

## ✅ 门店已绑仓库 — ops.merchant.store.warehouses

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | **门店ID（注意参数名是 `id`，不是 `storeId`）** |

### 出参（数组）

- **关键字段来源**：`id`（**门店仓关联记录ID** → 排序操作的 sortedIds 取此字段）、`warehouseId`（→ 解绑/仓库详情与编辑的仓库ID）
- **枚举字段**：`warehouseType`（STORE_WAREHOUSE/FRONT_WAREHOUSE/MAIN_WAREHOUSE）、`status`（ACTIVE/INACTIVE，关联状态）、`isDefault`（0/1，默认仓不可解绑）
- **格式敏感字段**：`sort`（扣减库存顺序，值越小优先级越高）

### 调用示例

```json
{"capability":"ops.merchant.store.warehouses","input":{"id":"6000012345678901234"},"summary":"查看门店已绑定的仓库与扣减顺序"}
```

---

## ✅ 门店已绑自提点 — ops.merchant.store.pickup-sites

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | **门店ID（注意参数名是 `id`，不是 `storeId`）** |

### 出参（数组）

- **关键字段来源**：`id`（→ 自提点操作/解绑）
- **枚举字段**：`status`（1=启用 0=禁用）、`isDefault`（0/1，默认自提点不可解绑）
- **格式敏感字段**：`businessHoursStart`/`businessHoursEnd`（HH:MM）

### 调用示例

```json
{"capability":"ops.merchant.store.pickup-sites","input":{"id":"6000012345678901234"},"summary":"查看门店已绑定的自提点"}
```

---

## ✅ 门店可绑仓库 — ops.merchant.store.available-warehouses

- **语义**：可选仓库分页（已排除门店仓类型），每条带 `isBound` 标记、已绑定的排前面

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| pageNum / pageSize | Integer | 否 | 分页（默认 1/20） |
| keyword | String | 否 | 仓库名称/编码模糊搜索 |
| status | Integer | 否 | 0=停用 1=启用 |
| warehouseType | String | 否 | `FRONT_WAREHOUSE`/`MAIN_WAREHOUSE` 等 |

### 出参（分页）

- **关键字段来源**：`records[].id`（→ store.bind-warehouse 的 warehouseId）
- **枚举字段**：`isBound`（boolean）、`status`（0/1）、`warehouseType`、`configStatus`

### 调用示例

```json
{"capability":"ops.merchant.store.available-warehouses","input":{"storeId":"6000012345678901234","pageNum":1,"pageSize":20,"keyword":"前置仓"},"summary":"查找门店可绑定的前置仓"}
```

---

## ✅ 门店可绑自提点 — ops.merchant.store.available-pickup-sites

- **语义**：可选自提点分页（已排除门店自提点类型），每条带 `isBound` 标记

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| pageNum / pageSize | Integer | 否 | 分页（默认 1/20） |
| name | String | 否 | 自提点名称模糊搜索 |
| status | Integer | 否 | 0=禁用 1=启用 |

### 出参（分页）

- **关键字段来源**：`records[].id`（→ store.bind-pickup-site 的 pickupSiteId）
- **枚举字段**：`isBound`（boolean）、`status`（0/1）、`siteType`（STORE_PICKUP/REGULAR_PICKUP）

### 调用示例

```json
{"capability":"ops.merchant.store.available-pickup-sites","input":{"storeId":"6000012345678901234","pageNum":1,"pageSize":20,"name":"科技园"},"summary":"查找门店可绑定的自提点"}
```

---

## ✅ 全局履约树 — ops.merchant.store.fulfillment-tree

- **语义**：门店 → 仓库 → 配送方式 三级结构懒加载视图，用于总览履约配置

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | 否 | 默认 1 / 20 |
| keyword | String | 否 | 门店名称模糊匹配 |

### 出参（分页，树形）

- **关键字段来源**：`id`（门店ID）、`warehouses[].id`（仓库ID）、`warehouses[].deliveryMethods[]`（配送方式聚合）
- **枚举字段**：`status`（门店状态）

### 调用示例

```json
{"capability":"ops.merchant.store.fulfillment-tree","input":{"pageNum":1,"pageSize":20,"keyword":"科技园"},"summary":"总览科技园门店的履约配置树"}
```

---

## ✅ 履约区块聚合 — ops.merchant.store.fulfillment-blocks

- **语义**：按门店（可叠加仓库/配送方式）聚合查询配送区块配置

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| warehouseId | String | 否 | 仓库ID（缩小范围） |
| deliveryId | String | 否 | 配送方式ID（缩小范围） |

### 出参

- 门店/仓库定位坐标 + 区块列表；区块含类型与区域描述，透传即可。

### 调用示例

```json
{"capability":"ops.merchant.store.fulfillment-blocks","input":{"storeId":"6000012345678901234"},"summary":"查看门店维度的配送区块聚合"}
```

---

## ✅ 导出门店列表 — ops.merchant.store.export

- **说明**：按查询条件同步导出门店 Excel，上传 COS 后返回**预签名下载 URL**（有分钟级时效——告知用户尽快下载，不持久化该 URL）。
- **注意**：**分页参数不生效**，恒按筛选条件全量导出（上限 10000）；无数据时报"没有符合条件的门店数据可导出"。

### 入参

同门店分页搜索的查询条件（json-body 全量提交；不带分页条件=全量导出）：keyword、status、type、orgNodeId 等以门店 search 入参表为准。

### 出参（原始数据）

- **枚举字段**：`mode`（sync/async，本期固定 sync）
- **展示字段**：`downloadUrl`（COS 预签名下载 URL）

### 调用示例

```json
{"capability":"ops.merchant.store.export","input":{"pageNum":1,"pageSize":20,"keyword":"研学"},"summary":"导出门店列表 Excel"}
```

---

## ⛔ 未开放

| 操作 | 原因 |
|------|------|
| 门店导入模板下载（import/template） | 二进制文件流响应；产品决策仅开放 URL 型导出/下载，此型走管理后台「门店管理-导入-下载模板」 |
