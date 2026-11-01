# 商户域 — 门店写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-store.md`；检索与现值读取（分页/详情/选项/已绑与可绑仓库自提点）先读 `store-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：store.create 创建门店 · store.update 编辑门店 · store.update-status 门店状态变更 · store.batch-status 批量状态变更 🔴 · store.batch-delete 批量删除门店 🔴 · store.set-default 设默认门店 🔴 · store.bind-warehouse 绑定仓库 · store.unbind-warehouse 解绑仓库 · store.sort-warehouses 仓库排序 · store.bind-pickup-site 绑定自提点 · store.unbind-pickup-site 解绑自提点 · store.import 导入门店 🔴

---

## ✅ 创建门店 — ops.merchant.store.create

- 只在用户明确要求创建并确认表单后调用；执行语义为单次提交、原样返回。**超时/网络错误时结果不确定（可能已创建）——先按门店名搜索确认是否已存在，未创建才可重新提交**
- **副作用**：同事务自动创建 STORE 类型组织节点 + 默认门店仓 + 门店仓绑定，异步创建默认自提点；初始状态 SUSPENDED

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orgNodeId | String | ✅ | 所属区域节点ID（必须为 REGION 类型，来自 org.tree；禁止总部直挂门店） |
| name | String | ✅ | 门店名称，≤200 字 |
| type | String | ✅ | `PHYSICAL`/`VIRTUAL` |
| province / city / district | String | 条件 | PHYSICAL 必填（服务端校验）；名称 |
| provinceCode / cityCode / districtCode | String | 否 | 行政区划编码（来自 region.tree） |
| address | String | 条件 | 详细地址，≤200 字；PHYSICAL 必填 |
| storeCode | String | 否 | 门店编码，1~30 位字母数字；不传自动生成 |
| contactPhone | String | 否 | 联系电话 |
| latitude / longitude | Number | 否 | GCJ-02 坐标（纬度 -90~90、经度 -180~180） |
| businessHoursStart / businessHoursEnd | String | 否 | 营业时间 HH:MM；结束须晚于开始 |

### 出参（原始返回）

`data` 为新建门店对象，含 `id`（门店ID）。

### 调用示例

```json
{"capability":"ops.merchant.store.create","input":{"orgNodeId":"7300012345678901234","name":"科技园一号店","type":"PHYSICAL","province":"广东省","provinceCode":"440000","city":"深圳市","cityCode":"440300","district":"南山区","districtCode":"440305","address":"科技园南路 88 号","contactPhone":"0755-88888888"},"summary":"创建实体门店科技园一号店"}
```

---

## ✅ 编辑门店 — ops.merchant.store.update

- 执行前必须对话确认变更清单
- **执行语义**：乐观锁——建议携带详情返回的 `version`（不传不报错但失去并发保护）；并发携带冲突时报错。编辑时门店编码不可修改；任何状态（含已关店）的门店均可编辑

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 门店ID |
| version | Integer | 建议 | 乐观锁版本号（来自详情）——不传不报错但会**失去并发保护**（他人在此期间的修改会被覆盖）；正常编辑应始终携带 |
| name | String | 否 | ≤200 字 |
| type | String | 否 | `PHYSICAL`/`VIRTUAL`，不传不变更 |
| orgNodeId | String | 否 | 更换所属区域节点 |
| province / city / district / address 及编码 | String | 否 | 同创建；传空可能导致地址丢失，编辑前先读详情回填 |
| contactPhone | String | 否 | — |
| latitude / longitude | Number | 否 | GCJ-02 坐标 |
| businessHoursStart / businessHoursEnd | String | 否 | HH:MM |

### 出参（原始返回）

无返回数据；执行后回读详情核验。

### 调用示例

```json
{"capability":"ops.merchant.store.update","input":{"id":"6000012345678901234","name":"科技园一号店","contactPhone":"0755-88888888","version":3},"summary":"更新门店联系电话"}
```

---

## ✅ 门店状态变更 — ops.merchant.store.update-status

- **执行语义**：状态机校验（见 `merchant-enums.md` 门店状态机），非法流转直接报错；执行后回读详情核验状态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 门店ID |
| status | String | ✅ | `ACTIVE`/`SUSPENDED`/`CLOSED`（CLOSED 为终态，不可恢复） |
| reason | String | 否 | 变更原因，≤500 字 |

### 调用示例

```json
{"capability":"ops.merchant.store.update-status","input":{"id":"6000012345678901234","status":"ACTIVE","reason":"装修完成恢复营业"},"summary":"激活暂停营业的门店"}
```

---

## ✅ 批量变更门店状态 — ops.merchant.store.batch-status

- 🔴 商业影响——执行前与用户确认门店清单与目标状态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 1..200 个门店ID |
| status | String | ✅ | `ACTIVE`/`SUSPENDED`/`CLOSED` |

### 出参（原始返回）

`{successCount, failureCount, ...}`——部分失败逐条向用户报告，未成功门店可单条重试。

### 调用示例

```json
{"capability":"ops.merchant.store.batch-status","input":{"ids":["6000012345678901234","6000012345678901235"],"status":"SUSPENDED"},"summary":"暂停两家门店营业"}
```

---

## ✅ 批量删除门店 — ops.merchant.store.batch-delete

- 🔴 **不可逆**——逻辑删除不可恢复，且会**级联删除该门店的默认门店仓与默认自提点、解除全部仓库/自提点关联（含非默认绑定）**，并触发 C 端定店定仓缓存清洗
- **实际行为（以服务端实现为准）**：仅默认门店（isDefault=1）与不存在的门店会被跳过计入 skippedCount；**其余状态（含营业中）的门店都会被删除**。执行前必须与用户逐店确认清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 1..200 个门店ID |

### 出参（原始返回）

`{deletedCount, skippedCount, ...}`。

### 调用示例

```json
{"capability":"ops.merchant.store.batch-delete","input":{"ids":["6000012345678901234"]},"summary":"删除测试门店及其默认仓与自提点"}
```

---

## ✅ 设置默认门店 — ops.merchant.store.set-default

- 🔴 商业影响——默认门店是 C 端兜底进店，变更影响全量新用户
- **前置**：目标门店必须为 ACTIVE；若门店在隔离列表会被自动移出（服务端联动，无需手动处理）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 门店ID |

### 调用示例

```json
{"capability":"ops.merchant.store.set-default","input":{"id":"6000012345678901234"},"summary":"把科技园一号店设为默认门店"}
```

---

## ✅ 绑定门店仓库 — ops.merchant.store.bind-warehouse

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| warehouseId | String | ✅ | 仓库ID（来自 available-warehouses） |

### 调用示例

```json
{"capability":"ops.merchant.store.bind-warehouse","input":{"storeId":"6000012345678901234","warehouseId":"7000012345678901234"},"summary":"为门店绑定前置仓"}
```

---

## ✅ 解绑门店仓库 — ops.merchant.store.unbind-warehouse

- 默认仓库（isDefault=1）不可解绑，会被拒绝

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| warehouseId | String | ✅ | 仓库ID |

### 调用示例

```json
{"capability":"ops.merchant.store.unbind-warehouse","input":{"storeId":"6000012345678901234","warehouseId":"7000012345678901234"},"summary":"解除门店与仓库的绑定"}
```

---

## ✅ 门店仓库排序 — ops.merchant.store.sort-warehouses

- **语义**：保存扣减库存顺序（值越小优先扣减）；传**当前门店全部关联仓库**的完整有序清单
- **⚠️ ID 语义**：sortedIds 传的是 **store.warehouses 返回的 `id`（门店仓关联记录ID）**，不是 `warehouseId`——传仓库ID不会报错但**排序静默不生效**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| sortedIds | String[] | ✅ | 按新顺序排列的关联记录ID列表（取 store.warehouses 的 `id` 字段） |

### 调用示例

```json
{"capability":"ops.merchant.store.sort-warehouses","input":{"storeId":"6000012345678901234","sortedIds":["7900012345678901234","7900012345678901235"]},"summary":"调整门店仓库扣减库存顺序"}
```

---

## ✅ 绑定门店自提点 — ops.merchant.store.bind-pickup-site

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| pickupSiteId | String | ✅ | 自提点ID（来自 available-pickup-sites） |

### 调用示例

```json
{"capability":"ops.merchant.store.bind-pickup-site","input":{"storeId":"6000012345678901234","pickupSiteId":"7200012345678901234"},"summary":"为门店绑定自提点"}
```

---

## ✅ 解绑门店自提点 — ops.merchant.store.unbind-pickup-site

- 默认自提点（isDefault=1）不可解绑

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 门店ID |
| pickupSiteId | String | ✅ | 自提点ID |

### 调用示例

```json
{"capability":"ops.merchant.store.unbind-pickup-site","input":{"storeId":"6000012345678901234","pickupSiteId":"7200012345678901234"},"summary":"解除门店与自提点的绑定"}
```

---

## ✅ 导入门店 — ops.merchant.store.import

- 🔴 批量写（每行独立事务；单次 ≤500 行；同租户并发导入有服务端锁保护）
- **传输形态**：multipart 文件型——文件由用户先上传到对话/工作区，经 multipart file part 传递（本地路径不得放入结构化 input）。**模板获取**：从管理后台「门店管理-导入-下载模板」获取，或参考导出文件的列结构。
- **模板 7 列**（表头带 `*` 号，列序即此序）：门店所属上级组织ID / 门店名称 / 门店类型 / 省 / 市 / 区 / 门店地址。**门店类型仅 `实体门店`/`虚拟门店` 二值**——预检文件时发现其他值要提示用户修正（服务端会把非法类型静默降级为实体门店，不报失败行，用户意图会被无声改变）

### multipart 入参

| part | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 门店 Excel（.xlsx，≤10MB，≤500 行） |

### 出参（原始数据）

- **枚举字段**：`status`（0=处理中(异步) / 1=已完成 / 2=失败，可空——⚠️ 门店导入为纯同步实现，status 恒为 null，**不要把 null 当「处理中」**，结果以 successCount/failureCount 为准）
- **展示字段**：`taskId`、`totalCount`、`successCount`、`failureCount`、`hasFailureDetail`、`failureDetailUrl`（失败明细文件下载 URL，COS 预签名）
- ⚠️ **部分成功语义**：`failureCount > 0` 时逐项向用户报告成功/失败数，并给出 `failureDetailUrl` 让用户下载失败明细修正后重导。

### 调用示例

```json
{"capability":"ops.merchant.store.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"导入这批门店 Excel；文件由客户端 multipart 提供"}
```
