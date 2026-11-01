# 商户域 — 配送区块 / 固定区域写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-warehouse.md`（区块）与 `references/flows/merchant-entry.md`（固定区域）；现值读取（区块分页/详情/全部区域/固定区域分页/行政区划树）先读 `area-config-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> ⛔ 配送区块创建/编辑未开放（地图多边形绘制产物，无法手工构造）——本文件只含区块启停与区域排除、固定区域维护。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：delivery-area-block.update-status 启停配送区块 🔴 · delivery-area-block.region-exclude 切换区域排除 · fixed-area.create 新增固定区域 · fixed-area.update 编辑固定区域 · fixed-area.delete 删除固定区域 🔴 · fixed-area.delete-area 删除固定区域内单个地区

---

## ✅ 启停配送区块 — ops.merchant.delivery-area-block.update-status

- 🔴 商业影响——停用区块会影响引用它的仓库配送范围

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 区块ID |
| status | Integer | ✅ | 0=停用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.delivery-area-block.update-status","input":{"id":"7700012345678901234","status":0},"summary":"停用配送区块"}
```

---

## ✅ 切换区域排除状态 — ops.merchant.delivery-area-block.region-exclude

- 改变区块内某区域的配送/排除语义

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| blockId | String | ✅ | 区块ID |
| regionId | String | ✅ | 区域ID（来自区块详情 regions[].id） |
| isExclude | Integer | ✅ | 0=配送区域 1=排除区域 |

### 调用示例

```json
{"capability":"ops.merchant.delivery-area-block.region-exclude","input":{"blockId":"7700012345678901234","regionId":"7710012345678901234","isExclude":1},"summary":"把区块内某区域改为排除不配送"}
```

---

## ✅ 新增固定区域 — ops.merchant.fixed-area.create

- **约束**：同一租户下组织节点唯一（一个节点只能配一个固定区域）；地区编码在租户内互斥（不能同时被两个区域推荐）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orgNodeId | String | ✅ | 组织节点ID（来自 org.tree） |
| orgNodeName | String | ✅ | 节点名称（冗余存储） |
| orgNodeCode | String | 否 | 节点编号（冗余展示） |
| recommendAreas | Array | ✅ | 推荐地区列表，≥1 项 |
| recommendAreas[].code | String | ✅ | 行政区划编码（来自 region.tree） |
| recommendAreas[].name | String | ✅ | 地区名称 |
| recommendAreas[].level | String | ✅ | `province`/`city`/`district`（**小写**；服务端不校验枚举——传其他值也会入库，但会导致 C 端区域匹配失配，务必用 region.tree 的层级推导：1=province 2=city 3=district） |

### 出参（原始返回）

`data` 为新建固定区域ID。

### 调用示例

```json
{"capability":"ops.merchant.fixed-area.create","input":{"orgNodeId":"7300012345678901234","orgNodeName":"华南大区","recommendAreas":[{"code":"440000","name":"广东省","level":"province"},{"code":"440300","name":"深圳市","level":"city"}]},"summary":"为华南大区配置推荐地区"}
```

---

## ✅ 编辑固定区域 — ops.merchant.fixed-area.update

- **全量替换**地区列表——先读现状，保留用户未要求移除的地区

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 固定区域ID |
| recommendAreas | Array | ✅ | 新的地区列表（全量，结构同创建） |

### 调用示例

```json
{"capability":"ops.merchant.fixed-area.update","input":{"id":"6300012345678901234","recommendAreas":[{"code":"440000","name":"广东省","level":"province"}]},"summary":"固定区域只保留广东省推荐"}
```

---

## ✅ 删除固定区域 — ops.merchant.fixed-area.delete

- 🔴 不可逆（主记录逻辑删除 + 地区物理删除）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 固定区域ID |

### 调用示例

```json
{"capability":"ops.merchant.fixed-area.delete","input":{"id":"6300012345678901234"},"summary":"删除固定区域配置"}
```

---

## ✅ 删除固定区域内单个地区 — ops.merchant.fixed-area.delete-area

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 固定区域ID |
| areaCode | String | ✅ | 行政区划编码 |

### 调用示例

```json
{"capability":"ops.merchant.fixed-area.delete-area","input":{"id":"6300012345678901234","areaCode":"440300"},"summary":"移除固定区域中的深圳市"}
```
