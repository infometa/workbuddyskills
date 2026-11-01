# 商户域 — 供应商写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-supplier.md`；现值读取（分页/详情/草稿摘要/字段配置）先读 `supplier-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。**导入为文件型 multipart 传输形态**。
> 能力索引：supplier.audit 入驻审核 🔴 · supplier.update 分区保存 · supplier.status 账户启停 · supplier.delete 删除供应商 🔴 · supplier.profile-review 资料变更复核 🔴 · supplier.license-ocr 营业执照 OCR · supplier.draft.save 草稿保存 · supplier.draft.clear 草稿清除 · supplier.field-config.required-save 字段必填配置 🔴 · supplier.field-config.custom-field.create 自定义字段新增 · supplier.field-config.custom-field.update 自定义字段编辑 · supplier.field-config.custom-field.delete 自定义字段删除 🔴 · supplier.import 批量导入供应商 🔴

---

## ✅ 入驻审核 — ops.merchant.supplier.audit

- 🔴 商业影响（决定供应商能否入驻）
- **前置**：仅 `auditStatus=pending` 可调用（状态机单向，审核后不可回退）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |
| action | String | 是 | `approve` / `reject`（小写） |
| rejectReason | String | 条件必填 | action=reject 时必填，≤500 字 |
| idempotencyKey | String | 是 | **审核幂等键**，16~128 位（建议 UUID）；同一审核操作的确认重提复用同值，新的审核操作重新生成 |

### 调用示例

```json
{"capability":"ops.merchant.supplier.audit","input":{"id":"6700012345678901234","action":"approve","idempotencyKey":"550e8400-e29b-41d4-a716-446655440000"},"summary":"审核通过这家供应商的入驻申请"}
```

执行后回读 `supplier.detail` 的 `auditStatus` 核验。

---

## ✅ 分区保存 — ops.merchant.supplier.update

- 🔴 正式生效（改供应商档案）
- **前置**：仅 `auditStatus=approved` 可调用；乐观锁 `expectedVersion` 必传。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |
| sectionKey | String | 是 | `account` / `enterprise` / `settlement` |
| content | Object | 是 | 分区内容（明文字段；结构见下） |
| expectedVersion | Integer | 是 | 乐观锁版本号 ≥0（来自 detail 的 version 或 draft 的 sections[].version） |
| customFieldValues | array | 否 | `[{fieldId, value}]`（value 为字符串形式） |

**content 分区字段**（字段名 = 详情 VO 字段去掉 Masked 后缀的明文名；用户提供明文，不回写脱敏值）：

| sectionKey | 必填字段 | 可选字段 |
|---|---|---|
| `account` | name、phone | email |
| `enterprise` | name（锁定恒必填）、creditCode（唯一性校验）、contactName、contactPhone | licenseMaterialId、categoryIds[]、region、expireDate（yyyy-MM-dd）、longTermValid（true 时 expireDate 可空）、warningEnabled、warningDays（开启预警时必填） |
| `settlement` | accountName、bankName、accountNo、contactName、contactPhone | permitMaterialId |

### 调用示例

```json
{"capability":"ops.merchant.supplier.update","input":{"id":"6700012345678901234","sectionKey":"enterprise","content":{"name":"示例企业","creditCode":"91440300MA5DA1234X","contactName":"张三","contactPhone":"13800138000"},"expectedVersion":3},"summary":"更新供应商的企业资质分区"}
```

⚠️ 换绑状态 `contactRebindStatus=provisioning` 时禁止编辑手机号。乐观锁冲突时重新读 detail 取新 version，不盲目重试。

---

## ✅ 账户启停 — ops.merchant.supplier.status

- 🔴 商业影响（disabled 供应商端账号无法登录）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |
| status | String | 是 | `enabled` / `disabled`（小写） |

### 调用示例

```json
{"capability":"ops.merchant.supplier.status","input":{"id":"6700012345678901234","status":"disabled"},"summary":"停用这家供应商的账号"}
```

---

## ✅ 删除供应商 — ops.merchant.supplier.delete

- 🔴 不可逆（物理删除）
- **前置**：仅 `auditStatus` 为 rejected/approved 可调用。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |

### 调用示例

```json
{"capability":"ops.merchant.supplier.delete","input":{"id":"6700012345678901234"},"summary":"删除这家已确认作废的供应商"}
```

---

## ✅ 资料变更复核 — ops.merchant.supplier.profile-review

- 🔴 商业影响（决定供应商提交的资料变更是否生效）
- **前置**：目标分区存在 `status=reviewing` 的变更单（从 detail 的 `profileReviews[]` 确认；已驳回的变更单不可重复操作）。enterprise 与 settlement 可并行各持一张变更单，多张并存时必须显式指定 `sectionKey`。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |
| action | String | 是 | `approve` / `reject`（小写） |
| sectionKey | String | 是 | 复核目标分区：`enterprise` / `settlement` |
| rejectReason | String | 条件必填 | action=reject 时必填，≤500 字 |

### 调用示例

```json
{"capability":"ops.merchant.supplier.profile-review","input":{"id":"6700012345678901234","action":"approve","sectionKey":"enterprise"},"summary":"通过这家供应商的企业资料变更"}
```

执行后回读 detail 的 `profileReviews[]` 核验。

---

## ✅ 营业执照 OCR — ops.merchant.supplier.license-ocr

- 🟡 无副作用识别（结果仅作为编辑建议）
- **说明**：对指定素材执行营业执照 OCR 识别。只接受**当前租户素材库**的 materialId（来自 detail 的 `enterpriseInfo.licenseMaterialId`，素材先经素材库上传）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |
| materialId | String | 是 | 营业执照素材 ID（十进制字符串） |

### 出参（原始数据）

- **枚举字段**：`status`（processing/success/failed）
- **嵌套结构**（result）：`enterpriseName`、`creditCode`、`region`、`subjectType`、`validPeriod`、`longTermValid`（OCR 未识别到时为 null——不得据此伪造"非长期有效"）、`legalPerson`、`businessScope`、`warningMessages[]`

### 调用示例

```json
{"capability":"ops.merchant.supplier.license-ocr","input":{"id":"6700012345678901234","materialId":"6500012345678901234"},"summary":"识别这家供应商的营业执照"}
```

---

## ✅ 草稿保存 — ops.merchant.supplier.draft.save

- 🟡 可逆（草稿不生效）
- **说明**：分区暂存草稿（不做必填/唯一校验）；与正式保存互斥。

### 入参

结构同分区保存（id/sectionKey/content/expectedVersion/customFieldValues），草稿态允许部分字段为空。

### 调用示例

```json
{"capability":"ops.merchant.supplier.draft.save","input":{"id":"6700012345678901234","sectionKey":"account","content":{"name":"示例账号","phone":"13800138000"},"expectedVersion":2},"summary":"暂存账号分区草稿"}
```

---

## ✅ 草稿清除 — ops.merchant.supplier.draft.clear

- 🟡 可逆（可重新保存）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |
| sectionKey | String | 否 | 省略=清除全部分区草稿 |

### 调用示例

```json
{"capability":"ops.merchant.supplier.draft.clear","input":{"id":"6700012345678901234","sectionKey":"account"},"summary":"丢弃账号分区草稿"}
```

---

## ✅ 字段必填配置 — ops.merchant.supplier.field-config.required-save

- 🔴 全租户（影响所有供应商的档案校验规则与供应商端填写表单）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| expectedSchemaVersion | Long | 是 | Schema 乐观锁版本（来自 `field-config.get` 出参 `schemaVersion`；并发冲突会报错，重读后再来） |
| rules | array | 是 | 字段规则列表：`[{fieldId, required}]`——fieldId（十进制字符串，**来自 field-config.get 出参 `sections[].fields[].id`**）+ required（Boolean）；系统字段与自定义字段统一用 rules 表达。**校验行为**：≤200 项；fieldId 重复报「字段规则ID不得重复」；不属于当前租户的 fieldId 报「字段ID不属于当前租户」；locked 字段（如 enterprise.name）恒必填——传 required=false 也会被强制置 true |

> `systemFieldRequired`/`customFieldRequired`（两个 Map）为 v1.1.0 前的旧调用形态，仅作兼容保留——**新调用一律传 `rules`**，不要使用这两个字段。

### 出参（原始数据）

- 以响应为准（保存结果信封）。

### 调用示例

```json
{"capability":"ops.merchant.supplier.field-config.required-save","input":{"expectedSchemaVersion":3,"rules":[{"fieldId":"7000012345678901234","required":true}]},"summary":"把这个自定义字段设为必填"}
```

---

## ✅ 自定义字段新增 — ops.merchant.supplier.field-config.custom-field.create

- 🟡 可逆写

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| section | String | 是 | `account` / `enterprise` / `settlement`（创建后不可变更） |
| key | String | 是 | 字段键，`^[a-z][a-z0-9_]{1,63}$`（小写开头，2~64 位） |
| label | String | 是 | 展示名称，≤100 字 |
| type | String | 是 | `text` / `number` / `date` / `file` / `select`（小写） |
| required | Boolean | 是 | 是否必填 |
| unique | Boolean | 是 | 是否唯一 |
| sortOrder | Integer | 是 | 排序值 ≥0 |
| options | array&lt;String&gt; | 条件必填 | type=select 时必填且 ≥2 项 |
| name | String | 否 | ≤50 字（可选别名） |

### 调用示例

```json
{"capability":"ops.merchant.supplier.field-config.custom-field.create","input":{"section":"enterprise","key":"cooperation_level","label":"合作等级","type":"select","required":false,"unique":false,"sortOrder":0,"options":["A","B","C"]},"summary":"给企业分区加一个合作等级下拉字段"}
```

---

## ✅ 自定义字段编辑 — ops.merchant.supplier.field-config.custom-field.update

- 🔴 `hasData=true`（已有录入数据）的字段禁止变更类型——服务端保护，以响应为准

### 入参

fieldId（路径）+ key/label/type/options/unique/required/sortOrder（不含 section）。

### 调用示例

```json
{"capability":"ops.merchant.supplier.field-config.custom-field.update","input":{"fieldId":"7000012345678901234","name":"合作等级","type":"select","options":["A","B","C","D"]},"summary":"给合作等级字段加一个 D 选项"}
```

---

## ✅ 自定义字段删除 — ops.merchant.supplier.field-config.custom-field.delete

- 🔴 不可逆——`hasData=true` 的字段服务端保护拒绝删除，以响应为准

### 入参

fieldId（路径）。

### 调用示例

```json
{"capability":"ops.merchant.supplier.field-config.custom-field.delete","input":{"fieldId":"7000012345678901234"},"summary":"删除这个废弃的自定义字段"}
```

---

## ✅ 批量导入供应商 — ops.merchant.supplier.import

- 🔴 批量写（每行独立事务，单次 ≤200 行）
- **传输形态**：multipart 文件型——文件经 multipart file part 传递（本地路径不入 input）。**模板获取**：管理后台「供应商管理-导入-下载模板」。

### multipart 入参

| part | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 供应商 Excel（.xlsx 或 .xls，≤10MB，≤200 行；.csv 会被拒绝） |

同租户并发导入有服务端锁（已有导入进行中会拒绝，如实转述并稍后再试）。

### 出参（原始数据）

- **展示字段**：`successCount`、`failCount`、`failList[]`（`rowIndex` Excel 行号 / `name` 供应商名称 / `errorMsg` 失败原因——**逐行失败明细直接在响应中**，逐条向用户报告）

### 调用示例

```json
{"capability":"ops.merchant.supplier.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"导入这批供应商 Excel；文件由客户端 multipart 提供"}
```
