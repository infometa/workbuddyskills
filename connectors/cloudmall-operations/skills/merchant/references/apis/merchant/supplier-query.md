# 商户域 — 供应商查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-supplier.md`；写操作见 `supplier-action.md`。
> 覆盖供应商（平台运营视角）的检索、详情、草稿摘要与字段配置。出参为上游**原始业务数据**（不裁剪字段）。
> **核心模型**：供应商档案分三个分区（sectionKey）——`account`（账号）/ `enterprise`（企业资质）/ `settlement`（结算），整行乐观锁（`version` 三分区共享，任一分区保存成功后递增）；供应商发起的资料变更不直接生效，而是生成**资料变更单**（profileReview）等待运营**复核**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：supplier.search 供应商分页 · supplier.detail 供应商详情 · supplier.draft.get 草稿状态查询 · supplier.field-config.get 字段配置查询 · supplier.export 导出供应商列表

---

## ✅ 供应商分页 — ops.merchant.supplier.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| keyword | String | 否 | 供应商名称/ID 模糊匹配，≤100 字 |
| auditStatus | String | 否 | `pending` / `approved` / `rejected`（小写） |
| profileReviewOnly | Boolean | 否 | true=仅返回有待复核变更的供应商 |
| status | String | 否 | `enabled` / `disabled`（小写） |
| categoryId | String | 否 | 服务类目筛选 |

### 出参（分页，原始数据）

- **路径参数来源**：`list[].id`（→ 所有 `/{id}` 路径参数；⚠️ 本接口分页信封为 `total` + `list`——与常见 `records[]` 不同，取对象一律从 `list[]` 取）
- **枚举字段**：`auditStatus`（pending/approved/rejected）、`status`（enabled/disabled）、`hasProfileReview`（boolean）
- **格式敏感字段**：`createdTime`/`updatedTime`/`submittedAt`（yyyy-MM-dd HH:mm:ss）
- **脱敏字段**：手机号等由后端脱敏返回（`maskedPhone`），不得尝试还原
- **换绑状态**：`contactRebindStatus`（provisioning=换绑同步中，禁止再编辑手机号 / completed / retryable_failed / terminal_failed，缺省=从未换绑）

### 调用示例

```json
{"capability":"ops.merchant.supplier.search","input":{"pageNum":1,"pageSize":20,"auditStatus":"pending"},"summary":"查一下待审核的供应商"}
```

---

## ✅ 供应商详情 — ops.merchant.supplier.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID（十进制字符串，来自列表出参） |

### 出参（三分区结构化，原始数据）

- **路径参数来源**：`enterpriseInfo.licenseMaterialId`（→ OCR 的 materialId）、`version`（integer → 分区保存/草稿的 expectedVersion）、`profileReviews[].sectionKey`（→ 复核的 sectionKey）
- **枚举字段**：`auditStatus`、`status`、`profileReviews[].status`（reviewing=待复核 / rejected=已驳回）
- **格式敏感字段**：`auditTime`/`createdTime`/`updatedTime`/`operationLogs[].operateTime`（yyyy-MM-dd HH:mm:ss）
- **脱敏字段**：`accountInfo.phoneMasked`/`emailMasked`、`enterpriseInfo.creditCodeMasked`/`contactPhoneMasked`、`settlementInfo.accountNoMasked`/`contactPhoneMasked`——全部后端脱敏，禁止要求用户提供明文还原
- **嵌套结构**：
  - `accountInfo`：`name`、`phoneMasked`、`emailMasked`、`customFields[]`、`contactRebindStatus`、`lastContactRebindError`
  - `enterpriseInfo`：`licenseMaterialId`、`name`、`creditCodeMasked`、`contactName`、`contactPhoneMasked`、`categoryIds[]`、`region`、`expireDate`（yyyy-MM-dd；`longTermValid=true` 时为 null）、`longTermValid`、`warningEnabled`、`warningDays`、`businessLicenseOcr`（OCR 结果对象）、`customFields[]`
  - `settlementInfo`：`permitMaterialId`、`accountName`、`bankName`、`accountNoMasked`、`contactName`、`contactPhoneMasked`、`customFields[]`
  - `bizSummary`：`productCount`/`orderCount`/`afterSaleCount`（Feign 降级时为 null——null ≠ 0）
  - `operationLogs[]`：`operationType`、`operatorName`、`operateTime`、`remark`、`changedFields[]`（fieldName/before/after）
  - `profileReviews[]`：分区分槽变更单（恒为数组）；`sectionKey`（enterprise/settlement）、`status`（reviewing/rejected）、`diffFields[]`（fieldName/before/after）、`rejectReason`/`reviewedAt`/`reviewerName`（rejected 时）
  - `customFields[]` 项：`fieldId`、`name`、`type`（text/number/date/file/select）、`value`（null=未填写）

### 调用示例

```json
{"capability":"ops.merchant.supplier.detail","input":{"id":"6700012345678901234"},"summary":"查看这家供应商的完整档案"}
```

---

## ✅ 草稿状态查询 — ops.merchant.supplier.draft.get

- **说明**：三分区草稿摘要。编辑档案前先调本接口确认是否存在未提交的草稿，避免覆盖他人/往次的暂存内容。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 供应商 ID |

### 出参（原始数据）

- **嵌套结构**：`sections[]`：`sectionKey`、`hasDraft`（boolean）、`content`（无草稿时 null）、`version`（integer，→ 分区保存/草稿保存的 expectedVersion）、`savedAt`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.supplier.draft.get","input":{"id":"6700012345678901234"},"summary":"查这家供应商有没有未提交的草稿"}
```

---

## ✅ 字段配置查询 — ops.merchant.supplier.field-config.get

- **说明**：系统字段（17 项）+ 全部自定义字段，全量非分页；自定义字段创建/编辑表单与档案分区渲染都依赖它。

### 入参

无（身份由连接绑定，全量返回当前租户配置）。

### 出参（原始数据）

- **路径参数来源**：`customFields[].fieldId`、`schemaVersion`（→ required-save 的 expectedSchemaVersion）
- **嵌套结构**：
  - `schemaVersion`（Long，字段配置版本——required-save 的乐观锁依据）
  - `sections[]`（分区 Schema 快照，**required-save 规则 `rules[].fieldId` 的唯一来源**）：`key`（分区 account/enterprise/settlement）+ `fields[]`——`id`（字段 ID，系统字段与自定义字段统一编号，→ rules[].fieldId）、`key`（稳定字段键）、`label`、`type`、`required`、`locked`、`unique`、`options[]`（select 时）、`sortOrder`
  - `systemFields`（Map：key=分区 account/enterprise/settlement）：`fieldKey`（复用 content 字段命名）、`label`、`required`、`locked`（锁定字段恒必填不可配，如 enterprise.name）、`uniqueLabelFixed`——⚠️ 系统字段在此结构**无 fieldId**，要改系统字段必填状态必须从 `sections[].fields[]` 按 key 定位取 `id`
  - `customFields[]`（跨分区，按 sort 排序）：`fieldId`、`section`、`name`、`type`（text/number/date/file/select）、`required`、`unique`、`options[]`（select 时）、`sort`、`hasData`（已有录入数据——true 时禁止变更类型/删除）

### 调用示例

```json
{"capability":"ops.merchant.supplier.field-config.get","input":{},"summary":"查看供应商档案的字段配置"}
```

---

## ✅ 导出供应商列表 — ops.merchant.supplier.export

- **说明**：按查询条件同步导出供应商 Excel，返回 COS 预签名下载 URL（分钟级时效）。

### 入参

同供应商分页查询条件（json-body 全量提交）：keyword、auditStatus、status、profileReviewOnly、categoryId 等。

### 出参（原始数据）

- **枚举字段**：`mode`（sync/async，本期固定 sync）
- **展示字段**：`downloadUrl`（COS 预签名下载 URL）

### 调用示例

```json
{"capability":"ops.merchant.supplier.export","input":{"pageNum":1,"pageSize":20,"auditStatus":"approved"},"summary":"导出已通过的供应商列表"}
```

---

## ⛔ 未开放（供应商）

| 操作 | 不开放理由 |
|------|-----------|
| 导入模板下载（import/template） | 二进制文件流响应；产品决策仅开放 URL 型导出，模板从管理后台下载 |
| 创建邀请码（invitations） | 一次性明文邀请码属敏感凭证面，且超出旧 Skill 对齐基线 |
| 供应商选项（options）/ 凭证素材上传（materials） | 基线外新增端点，未纳入本轮盘点 |
