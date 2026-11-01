# 营销域 — 奖品模板写操作契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/interactive-activity-flow.md`
> 奖品模板是互动活动奖品池的素材库（积分/优惠券/实物三类）；被“在用”活动引用的模板不可删除。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `prize-template-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：prize-template.create 创建奖品模板 🟡 · prize-template.update 编辑奖品模板 🟡 · prize-template.delete 删除奖品模板 🔴 · prize-template.toggle-status 启用/停用奖品模板 🟡 · prize-template.upload-image 上传奖品图片 🟡

---

## ✅ 创建奖品模板 — `ops.marketing.prize-template.create`

- **风险**：🟡 可逆写（可再编辑/停用）
- **前置**：type 必须是 points/coupon/physical；**type=coupon 时 bizTemplateId 必填**（关联促销域优惠券模板 ID）；奖品名称不可与已有模板重复。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 奖品名称，≤100 字 |
| type | String | ✅ | points / coupon / physical |
| bizTemplateId | String | 条件 | 业务奖品 ID（coupon 必填），≤64 字 |
| description | String | 否 | 奖品描述，≤500 字 |
| image | String | 否 | 奖品图片 URL |
| config | String | 否 | 奖品配置 JSON 字符串。**唯一被服务端消费的键是 `expireSeconds`**（Long，领取有效期秒数；>0 时派奖链路据此计算过期时间，null/≤0=不过期，解析失败降级为不过期）——实物类奖品前端按「有效小时数 ×3600」构造 `{"expireSeconds": 3600}`；积分/优惠券类不传（积分数量走 `quantity`、券模板走 `bizTemplateId`）。其余键服务端不解析（透传存储），不要自行构造 |
| sendDesc | String | 否 | 发放说明，≤500 字 |
| sendDescType | String | 否 | text / image |
| useDesc | String | 否 | 使用说明，≤500 字 |
| useDescType | String | 否 | text / image |
| autoSend | Integer | 否 | 1=自动发放，0=手动 |
| quantity | Integer | 否 | 奖品数量 |

### 出参（原始数据）

- **关键字段来源**：返回对象含 `id`（新奖品模板 ID）→ 供活动奖品池 `prizeList[].templateId` 绑定。

### 调用示例

```json
{"capability":"ops.marketing.prize-template.create","input":{"name":"新人礼包-5元券","type":"coupon","bizTemplateId":"4300000000000000001","description":"新用户注册发放","sendDesc":"中奖后自动发放至卡券包","sendDescType":"text","useDesc":"满30元可用","useDescType":"text","autoSend":1,"quantity":1000},"summary":"创建绑定优惠券的新人礼包奖品"}
```

---

## ✅ 编辑奖品模板 — `ops.marketing.prize-template.update`

- **风险**：🟡 可逆写
- **前置**：先读详情做基线，保留未改动字段；名称仍查重；coupon 类型的 bizTemplateId 规则同创建。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 奖品模板 ID（路径参数） |
| (其余字段) | - | ✅ | 结构同创建（name/type 必填，其余可选），整包覆盖 |

### 出参

- 无 data（成功即已保存）。

### 调用示例

```json
{"capability":"ops.marketing.prize-template.update","input":{"id":"5200000000000000001","name":"新人礼包-5元券","type":"coupon","bizTemplateId":"4300000000000000001","quantity":2000},"summary":"上调新人礼包奖品数量"}
```

---

## ✅ 删除奖品模板 — `ops.marketing.prize-template.delete`

- **风险**：🔴 不可逆（物理删除）
- **前置**：未被"在用"活动引用（活动奖品池 JSON 中含该模板 ID 且活动未结束）；被引用时报"模板使用中"。删除幂等：模板已不存在时不报错。
- **删除后必须回读**：delete 成功响应为空——**必须再 `prize-template.search` 确认目标已不在列表**，以搜索空集为核验，不以"操作成功"为证。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 奖品模板 ID |

### 调用示例

```json
{"capability":"ops.marketing.prize-template.delete","input":{"id":"5200000000000000001"},"summary":"删除未被引用的废弃奖品模板"}
```

---

## ✅ 启用/停用奖品模板 — `ops.marketing.prize-template.toggle-status`

- **风险**：🟡 可逆写
- **说明**：直接设置状态（非切换语义）：1=启用，0=停用；其它值报错。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 奖品模板 ID |
| status | Integer | ✅ | 1=启用，0=停用（query 参数） |

### 调用示例

```json
{"capability":"ops.marketing.prize-template.toggle-status","input":{"id":"5200000000000000001","status":0},"summary":"停用过期的奖品模板"}
```

---

## ✅ 上传奖品图片 — `ops.marketing.prize-template.upload-image`

- **风险**：🟡 可逆写（图片未引用前可忽略）
- **说明**：为奖品模板上传展示图。仅**文件型 capability**（当前运行时提供文件输入时）可执行，本地路径不得放入结构化 input；返回的图片 URL 填入奖品模板的 image 字段。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件（multipart） | ✅ | 图片文件（≤5MiB） |

### 出参（原始数据）

- **路径参数来源**：返回的图片 URL（→ 奖品模板 `image` 字段）

### 调用示例

```json
{"capability":"ops.marketing.prize-template.upload-image","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传奖品展示图"}
```

---
