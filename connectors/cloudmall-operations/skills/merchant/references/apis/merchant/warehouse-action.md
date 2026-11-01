# 商户域 — 仓库写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-warehouse.md`；现值读取（分页/统计/详情/已绑配送方式/区块配置）先读 `warehouse-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：warehouse.create 新建仓库 · warehouse.update 编辑仓库 · warehouse.update-status 启停仓库 · warehouse.bind-delivery-methods 绑定配送方式 🔴 · warehouse.bind-delivery-blocks 绑定配送区块 · warehouse.bind-administrative-blocks 绑定行政区域 🔴 · warehouse.bind-block-template 绑定区块模板 · warehouse.complete-fulfillment-config 完成配置 · warehouse.unbind-delivery-block 解绑配送区块

---

## ✅ 新建仓库 — ops.merchant.warehouse.create

- 表单确认后调用；初始 configStatus=UNCONFIGURED；编码全局唯一；超时后先按编码搜索确认是否已创建

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| warehouseName | String | ✅ | ≤100 字符 |
| warehouseCode | String | ✅ | ≤50 字符，仅字母/数字/下划线/横杠，全局唯一 |
| provinceCode / provinceName | String | ✅ | 省编码/名称 |
| cityCode / cityName | String | ✅ | 市编码/名称 |
| districtCode / districtName | String | ✅ | 区编码/名称 |
| address | String | ✅ | 详细地址，≤200 字符 |
| contactName | String | 否 | 联系人，≤50 |
| contactPhone | String | 否 | 联系电话，≤20 |
| capacity | Number | 否 | 库容，≥0，整数 8 位小数 2 位 |
| longitude / latitude | Number | 否 | 地图定位坐标 |
| remark | String | 否 | 备注，≤500 |

### 出参（原始返回）

`data` 为新建仓库ID（十进制字符串）。

### 调用示例

```json
{"capability":"ops.merchant.warehouse.create","input":{"warehouseName":"深圳前置仓一","warehouseCode":"SZ-FC-001","provinceCode":"440000","provinceName":"广东省","cityCode":"440300","cityName":"深圳市","districtCode":"440305","districtName":"南山区","address":"科技园物流园 3 号库"},"summary":"创建深圳前置仓"}
```

---

## ✅ 编辑仓库 — ops.merchant.warehouse.update

- 全量表单提交——先读详情回填，保留用户未要求修改的字段

### 入参

与创建完全一致（全部字段同表，`id` 额外必填）；编辑时编码唯一性校验排除自身。

### 出参（原始返回）

无返回数据；执行后回读详情核验。

### 调用示例

```json
{"capability":"ops.merchant.warehouse.update","input":{"id":"7000012345678901234","warehouseName":"深圳前置仓一","warehouseCode":"SZ-FC-001","provinceCode":"440000","provinceName":"广东省","cityCode":"440300","cityName":"深圳市","districtCode":"440305","districtName":"南山区","address":"科技园物流园 3 号库"},"summary":"编辑仓库基础信息"}
```

---

## ✅ 启停仓库 — ops.merchant.warehouse.update-status

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |
| status | Integer | ✅ | 0=停用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.update-status","input":{"id":"7000012345678901234","status":0},"summary":"停用仓库"}
```

---

## ✅ 绑定配送方式 — ops.merchant.warehouse.bind-delivery-methods

- 🔴 商业影响——**全量替换**：被移除的配送方式下全部区块配置会被级联删除，先查现态再提交
- **约束**：门店仓可绑定骑手/自提/快递/同城快递四种（最多 3 项，其中 `rider_delivery` 与 `self_service` **互斥二选一**，可再叠加快递类）；前置仓/主仓仅可绑定 `express`/`city_express`（最多 2 项）
- **前置**：停用状态（status=0）的仓库不可修改履约配置（会被拒绝）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |
| deliveryIds | String[] | ✅ | 配送方式ID列表（来自 delivery-method.list）；**不可传空数组**（服务端直接拒绝，不支持一次清空全部） |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.bind-delivery-methods","input":{"id":"7000012345678901234","deliveryIds":["7400012345678901234","7400012345678901235"]},"summary":"为仓库绑定快递与同城快递"}
```

---

## ✅ 绑定配送区块 — ops.merchant.warehouse.bind-delivery-blocks

- **全量替换**语义

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |
| deliveryId | String | ✅ | 配送方式ID |
| blockIds | String[] | ✅ | 区块ID列表（来自 delivery-area-block.search）；**必传**，空数组会清空该方式下区块 |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.bind-delivery-blocks","input":{"id":"7000012345678901234","deliveryId":"7400012345678901234","blockIds":["7700012345678901234"]},"summary":"为快递绑定科技园配送区块"}
```

---

## ✅ 绑定行政区域 — ops.merchant.warehouse.bind-administrative-blocks

- 🔴 商业影响——改变实际配送范围，确认区域清单后执行

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |
| deliveryId | String | ✅ | 配送方式ID |
| bindType | Integer | ✅ | `2`=全国可送（regions 不传）；`3`=行政区域（regions 必填） |
| regions | Array | 条件 | bindType=3 时必填，≤500 项 |
| regions[].provinceCode / provinceName | String | ✅ | 省编码/名称（≤20 / ≤50） |
| regions[].cityCode / cityName | String | 否 | 市编码/名称；填到哪一级就按哪一级生效（仅省=省级、省市=市级） |
| regions[].districtCode / districtName | String | 否 | 区编码/名称 |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.bind-administrative-blocks","input":{"id":"7000012345678901234","deliveryId":"7400012345678901234","bindType":3,"regions":[{"provinceCode":"440000","provinceName":"广东省","cityCode":"440300","cityName":"深圳市","districtCode":"440305","districtName":"南山区"}]},"summary":"绑定南山区为同城快递配送范围"}
```

---

## ✅ 绑定区块模板 — ops.merchant.warehouse.bind-block-template

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |
| deliveryId | String | ✅ | 配送方式ID |
| blockId | String | ✅ | 区块ID |
| freightTemplateId | String | 否 | 运费模板ID；传 null=清除 |
| fulfillmentTemplateId | String | 否 | 履约模板ID；传 null=清除；**仅快递（express）配送方式无需此模板，同城快递等其他方式均需** |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.bind-block-template","input":{"id":"7000012345678901234","deliveryId":"7400012345678901234","blockId":"7700012345678901234","freightTemplateId":"7500012345678901234"},"summary":"为区块绑定标准运费模板"}
```

---

## ✅ 完成配置 — ops.merchant.warehouse.complete-fulfillment-config

- **语义**：全量校验（至少绑一个配送方式；每配送方式至少一个区块；每区块运费模板必配——**仅快递 express 豁免履约模板，同城快递 city_express 仍需履约模板**），通过后 configStatus → READY；不通过时报未完成区块数量（具体缺口用 delivery-blocks 查询定位）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.complete-fulfillment-config","input":{"id":"7000012345678901234"},"summary":"完成仓库履约配置并置为就绪"}
```

---

## ✅ 解绑配送区块 — ops.merchant.warehouse.unbind-delivery-block

- **注意**：`blockRecordId` 是**绑定记录ID**（delivery-blocks 返回的 `id`），不是区块本身ID

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |
| deliveryId | String | ✅ | 配送方式ID |
| blockRecordId | String | ✅ | 绑定记录ID |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.unbind-delivery-block","input":{"id":"7000012345678901234","deliveryId":"7400012345678901234","blockRecordId":"7800012345678901234"},"summary":"解绑单个配送区块"}
```
