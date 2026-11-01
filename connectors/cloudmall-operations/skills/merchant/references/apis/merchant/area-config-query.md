# 商户域 — 配送区块 / 固定区域 / 行政区划查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-warehouse.md`（区块）与 `references/flows/merchant-entry.md`（固定区域）；写操作见 `area-config-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：delivery-area-block.search 配送区块分页 · delivery-area-block.detail 配送区块详情 · delivery-area-block.all-regions 全部区块区域 · fixed-area.search 固定区域分页 · region.tree 行政区划树

---

## ✅ 配送区块分页搜索 — ops.merchant.delivery-area-block.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| blockName | String | 否 | 区块名称模糊搜索，≤20 字符 |
| status | Integer | 否 | 0=停用 1=启用 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 仓库区块绑定的 blockId、区块详情）
- **枚举字段**：`blockType`（1=自定义 2=系统预设）、`status`（0/1）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.delivery-area-block.search","input":{"pageNum":1,"pageSize":20,"blockName":"科技园","status":1},"summary":"查找启用中的科技园配送区块"}
```

---

## ✅ 配送区块详情 — ops.merchant.delivery-area-block.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 区块ID |

### 出参（原始数据）

- **关键字段来源**：`regions[].id`（→ 区域排除切换的 regionId）、`regions[].coordinates`（多边形顶点 JSON `[[经度,纬度],...]`）
- **枚举字段**：`blockType`、`status`（0/1）、`regions[].isExclude`（0=配送 1=排除）
- **格式敏感字段**：`centerLng`/`centerLat`（定位中心坐标）

### 调用示例

```json
{"capability":"ops.merchant.delivery-area-block.detail","input":{"id":"7700012345678901234"},"summary":"查看配送区块区域构成"}
```

---

## ✅ 全部区块区域 — ops.merchant.delivery-area-block.all-regions

- **语义**：全部区块及其区域（辅助展示/选择），可排除指定区块

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| excludeBlockId | String | 否 | 排除的区块ID |

### 出参（数组）

结构同区块详情（blockName + regions 列表）。

### 调用示例

```json
{"capability":"ops.merchant.delivery-area-block.all-regions","input":{},"summary":"列出全部配送区块区域"}
```

---

## ✅ 固定区域分页搜索 — ops.merchant.fixed-area.search

- **语义**：组织节点 → 推荐地区 映射列表（LBS 进店规则的「固定区域推荐」数据源）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | 默认 1 |
| pageSize | Integer | 否 | 默认 20，最大 100 |
| keyword | String | 否 | 节点名称/编号模糊搜索 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].fixedAreaId`（→ 编辑/删除/删地区的 `input.id`）、`records[].orgNodeId`
- **枚举字段**：`recommendAreas[].level`（province/city/district，小写）、`subStores[].enabled`（boolean）
- `subStoreCount` 为下属门店数、`subStores[]` 为下属门店列表。

### 调用示例

```json
{"capability":"ops.merchant.fixed-area.search","input":{"pageNum":1,"pageSize":20,"keyword":"华南"},"summary":"查询华南固定区域配置"}
```

---

## ✅ 行政区划树 — ops.merchant.region.tree

- **语义**：省/市/区县三级基础数据（编码即建仓/门店/固定区域要用的 provinceCode 等）；不传 parentCode 返回完整树，传则返回该父级的直接子节点

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| parentCode | String | 否 | 父级编码（如 110000 返回北京市下辖区；省略=完整树） |

### 出参（数组，树形）

- **关键字段来源**：`code`（→ 各处 provinceCode/cityCode/districtCode）、`children[].code`
- **枚举字段**：`level`（1=省 2=市 3=区县，整数）

### 调用示例

```json
{"capability":"ops.merchant.region.tree","input":{"parentCode":"110000"},"summary":"查询北京市下级行政区划"}
```

---

## ⛔ 未开放

| 操作 | 原因 |
|------|------|
| 配送区块创建/编辑 | 区域为地图多边形绘制产物（coordinates 顶点数组），无法可靠手工构造 |
| 坐标点归属查询（check-point） | 地图调试辅助面 |
