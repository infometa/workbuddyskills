# 商户域 — 配送方式与运费/履约模板写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-warehouse.md`；现值读取（列表/分页/详情）先读 `delivery-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> ⚠️ BY_VOLUME（按体积计费）后端暂未开放，创建/编辑会被服务端拒绝——需要按体积计费时如实告知用户不可用。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：delivery-method.create 新增配送方式 · delivery-method.update 编辑配送方式 · delivery-method.update-status 启停配送方式 🔴 · delivery-method.sort 配送方式排序 · freight-template.create 新建运费模板 🔴 · freight-template.update 编辑运费模板 · freight-template.update-status 启停运费模板 · freight-template.delete 删除运费模板 🔴 · fulfillment-template.create 新建履约模板 · fulfillment-template.update 编辑履约模板 · fulfillment-template.update-status 启停履约模板 · fulfillment-template.delete 删除履约模板 🔴

---

## ✅ 新增配送方式 — ops.merchant.delivery-method.create

- **注意**：图标 URL 必填——用户必须提供已在云MALL可访问的图片地址，不接受编造 URL
- **注意**：**iconUrl 不做非空校验**；新建即启用（status=1）；**无删除能力**——误建为租户永久残留（只能停用）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 配送方式名称，≤50 字符 |
| code | String | ✅ | 编码，1~50 位字母/数字/下划线，唯一 |
| sort | Integer | ✅ | 排序权重，≥1 |
| iconUrl | String | ✅ | 图标 URL，≤500 字符 |
| remark | String | 否 | 备注，≤200 字符 |

### 调用示例

```json
{"capability":"ops.merchant.delivery-method.create","input":{"name":"同城闪送","code":"flash_delivery","sort":5,"iconUrl":"https://cos.example.com/icon-flash.png","remark":"一小时达"},"summary":"新增同城闪送配送方式"}
```

---

## ✅ 编辑配送方式 — ops.merchant.delivery-method.update

- 全量提交，先读列表回填

### 入参

同创建（`id` 额外必填）。

### 调用示例

```json
{"capability":"ops.merchant.delivery-method.update","input":{"id":"7400012345678901234","name":"同城闪送","code":"flash_delivery","sort":6,"iconUrl":"https://cos.example.com/icon-flash.png","remark":"一小时达"},"summary":"调整同城闪送排序"}
```

---

## ✅ 启停配送方式 — ops.merchant.delivery-method.update-status

- 🔴 商业影响——停用后 C 端不可选该方式

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 配送方式ID |
| status | Integer | ✅ | 0=停用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.delivery-method.update-status","input":{"id":"7400012345678901234","status":1},"summary":"启用同城闪送"}
```

---

## ✅ 配送方式排序 — ops.merchant.delivery-method.sort

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sortedIds | String[] | ✅ | 按新顺序排列的全部配送方式ID |

### 调用示例

```json
{"capability":"ops.merchant.delivery-method.sort","input":{"sortedIds":["7400012345678901234","7400012345678901235"]},"summary":"调整配送方式展示顺序"}
```

---

## ✅ 新建运费模板 — ops.merchant.freight-template.create

- 🔴 商业影响——计费规则影响订单金额，配置前与用户确认数值
- **出参注意**：响应 data 为空——**不返回新模板 ID**；需通过 `freight-template.search` 按模板名回查获取 ID 后再执行后续操作

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateName | String | ✅ | ≤50 字符 |
| chargeMode | String | ✅ | `BY_QUANTITY`/`BY_WEIGHT`/`FIXED`/`FREE`（`BY_VOLUME` 暂不可用） |
| chargeConfig | String | 条件 | 计费配置 JSON 字符串；FREE 不传，其余必填（结构见下） |
| enabled | Boolean | 否 | **不传默认停用（false）**——需要创建即启用必须显式传 true |
| remark | String | 否 | ≤200 字符 |

`chargeConfig` 按 chargeMode 展开（金额单位**元**、最多 2 位小数、非负）：

| chargeMode | 必填字段 | 说明 |
|-----------|---------|------|
| `BY_QUANTITY` | firstQuantity（>0）、firstFee、additionalQuantity（>0）、additionalFee | 首件数/首费/续件数/续费 |
| `BY_WEIGHT` | firstWeight（>0）、firstFee、additionalWeight（>0）、additionalFee | 首重/续重（kg） |
| `FIXED` | fixedAmount（≥0） | 固定运费 |
| `FREE` | — | 不传 chargeConfig |

可选字段（BY_QUANTITY/BY_WEIGHT/FIXED 模式）：
- `startPrice`：起送金额，≥0、≤1000000、2 位小数，不传=无起送限制；
- `packagingFee`：包装费——FIXED/BY_QUANTITY/BY_WEIGHT 模式下会叠加到计费结果（FREE 模式忽略），不传=0。⚠️ **B 端保存不校验该字段**（负值/超精度可入库），到 **C 端计费时**才报「packagingFee 不能为负数」导致无法计费下单——务必在保存时按 ≥0、≤2 位小数把关。

### 调用示例

```json
{"capability":"ops.merchant.freight-template.create","input":{"templateName":"标准运费","chargeMode":"BY_QUANTITY","chargeConfig":"{\"firstQuantity\":1,\"firstFee\":8.00,\"additionalQuantity\":1,\"additionalFee\":2.00}","enabled":true},"summary":"创建按件计费的标准运费模板"}
```

---

## ✅ 编辑运费模板 — ops.merchant.freight-template.update

- 先读详情回填全量提交

### 入参

同创建（`id` 额外必填）。差异：`enabled` 编辑时不传=**保持原值**（创建时不传=默认停用）。

### 调用示例

```json
{"capability":"ops.merchant.freight-template.update","input":{"id":"7500012345678901234","templateName":"标准运费","chargeMode":"BY_QUANTITY","chargeConfig":"{\"firstQuantity\":1,\"firstFee\":8.00,\"additionalQuantity\":1,\"additionalFee\":2.00}","enabled":true},"summary":"编辑标准运费模板"}
```

---

## ✅ 启停运费模板 — ops.merchant.freight-template.update-status

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |
| enabled | Boolean | ✅ | true=启用 false=停用 |

### 调用示例

```json
{"capability":"ops.merchant.freight-template.update-status","input":{"id":"7500012345678901234","enabled":false},"summary":"停用运费模板"}
```

---

## ✅ 删除运费模板 — ops.merchant.freight-template.delete

- 🔴 不可逆；被仓库区块引用时服务端拒绝并返回绑定信息

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |

### 调用示例

```json
{"capability":"ops.merchant.freight-template.delete","input":{"id":"7500012345678901234"},"summary":"删除未被引用的运费模板"}
```

---

## ✅ 新建履约模板 — ops.merchant.fulfillment-template.create

- 表单确认后调用

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateName | String | ✅ | ≤100 字符 |
| templateType | String | ✅ | 模板类型，当前固定传「`预约配送`」 |
| timeConfig | String | ✅ | 时间配置 JSON 字符串（结构见下）。**服务端不校验其内部结构**——畸形结构不会在创建时报错，而是 C 端解析时降级为空时段；时段先后/重叠需自行把关 |
| description | String | 否 | ≤500 字符 |

`timeConfig` JSON 字符串结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| availableDays | Integer | 可预约天数 |
| preparationTime | Integer | 备货时间（分钟） |
| appointmentPeriods | Array | 预约时间分组 |
| appointmentPeriods[].weekdays | Integer[] | 星期几（1=周一 … 7=周日） |
| appointmentPeriods[].autoSplit | Boolean | 是否自动切分时段 |
| appointmentPeriods[].timeSlots | Array | 时段列表 |
| timeSlots[].startTime / endTime | String | HH:mm:ss |
| timeSlots[].maxOrders | Integer | 时段最大单量 |

### 调用示例

```json
{"capability":"ops.merchant.fulfillment-template.create","input":{"templateName":"次日达预约","templateType":"预约配送","timeConfig":"{\"availableDays\":7,\"appointmentPeriods\":[{\"weekdays\":[1,2,3,4,5],\"autoSplit\":false,\"timeSlots\":[{\"startTime\":\"09:00:00\",\"endTime\":\"12:00:00\",\"maxOrders\":50}]}],\"preparationTime\":120}"},"summary":"创建次日达预约履约模板"}
```

---

## ✅ 编辑履约模板 — ops.merchant.fulfillment-template.update

- 先读详情回填全量提交；已绑定的区块配置会同步使用新配置

### 入参

同创建（`id` 额外必填）。

### 调用示例

```json
{"capability":"ops.merchant.fulfillment-template.update","input":{"id":"7600012345678901234","templateName":"次日达预约","templateType":"预约配送","timeConfig":"{\"availableDays\":7,\"appointmentPeriods\":[{\"weekdays\":[1,2,3,4,5],\"autoSplit\":false,\"timeSlots\":[{\"startTime\":\"09:00:00\",\"endTime\":\"12:00:00\",\"maxOrders\":50}]}],\"preparationTime\":120}"},"summary":"编辑履约模板时段配置"}
```

---

## ✅ 启停履约模板 — ops.merchant.fulfillment-template.update-status

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |
| status | Integer | ✅ | 0=禁用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.fulfillment-template.update-status","input":{"id":"7600012345678901234","status":1},"summary":"启用履约模板"}
```

---

## ✅ 删除履约模板 — ops.merchant.fulfillment-template.delete

- 🔴 不可逆；被仓库区块引用时服务端拒绝并返回绑定信息

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |

### 调用示例

```json
{"capability":"ops.merchant.fulfillment-template.delete","input":{"id":"7600012345678901234"},"summary":"删除未被引用的履约模板"}
```
