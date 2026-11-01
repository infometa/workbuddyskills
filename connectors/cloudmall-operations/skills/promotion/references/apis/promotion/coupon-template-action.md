# 促销域 — 券模板写操作契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-coupon.md`
> 券模板复用促销审核链：create/update/submit/check 用 **pendingId**（草稿 ID）；生命周期操作（stop/pause/resume/delete/分享物料）用 **templateId**（正式 ID）。两个 ID 不可混用。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 创建/复制/编辑/提审前必须读取 `form-validation.md` 的券模板节：领取窗口与使用窗口是两组不同字段，修改任一窗口须重验组合关系。
> 能力索引（前缀 `ops.promotion.`）：写 coupon-template.create · update · submit · check · stop 🔴 · pause · resume · delete 🔴 · share-qrcode · share-short-link
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：编辑基线用 `pending-query.md` 的 pending.detail（version + 完整表单快照）；分享物料先查 `coupon-template-query.md` 的 share-capability。
>
> ⚠️ **ID 格式口径**：`templateId` 必须使用用户明确提供或查询返回的十进制字符串 ID，保持原值，不转 Number，不补齐/截断。约 19 位只是常见外形，不能据长度断言对象不存在或必然 400；参数合法性按当前工具契约处理。非十进制标识先消歧，不猜 ID。写操作仍须读取现值并核对状态、权限与完整对象，不以 ID 能解析代替业务前置。

---

## ✅ 创建券模板（审核草稿） — `ops.promotion.coupon-template.create`

- 只在用户明确要求并确认关键字段后调用
- **执行语义**：单次提交、原样返回；超时结果不确定时先搜索确认再决定是否重试。创建即产生审核草稿。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionSubCode | String | ✅ | 券类型：`MJ_COUPON`/`ZK_COUPON`/`DH_COUPON`/`MYF_COUPON` |
| title | String | ✅ | 券名称，原页面最终保存与工作副本均≤20字符，输入框显示30不代表可保存30，见 form-validation.md |
| quantity | Integer | 否 | 发行量。⚠️ **未传时审批落库默认 1000**（按限量库存池创建）——当前创建链路无「不限量」显式开关，省略前必须与用户确认 |
| acquireExpireStart / acquireExpireEnd | String | 条件 | 可领取时间窗（毫秒时间戳；服务端按数值接收，传十进制字符串亦可）**提审时必填** |
| useExpireType | Integer | 否 | 1 固定时间段 / 2 领取后 N 秒 |
| useExpireStart / useExpireEnd | String | 条件 | useExpireType=1 时的使用有效期（毫秒时间戳） |
| useExpireDuration | Integer | 条件 | useExpireType=2 时的领取后有效期（**秒**） |
| acquireControl | Integer | 否 | 领取控制：1 自主领取 / 2 仅授权发放；前端要求明确选择，创建缺省按1。与 channelCodes 独立，不能靠改渠道替代领取控制 |
| transferEnabled | Boolean | 否 | 转赠开关，当前前端仅兑换券开放设置；创建缺省false，编辑未指定时保留现值，不擅自开启 |
| channelCodes | Integer[] | 否 | 业务领券渠道，编辑必须保留完整现值，省略会覆盖为空：新建草稿可能静默变为仅内部发放；变更草稿与既有非空渠道不一致时被拒（1 自然曝光 / 2 分销；业务上互斥不应同选——服务端不强制拦截，双渠道按分销优先、自然曝光失效）。⚠️ **空=仅 B 端运营发券等内部链路可发**，C 端领券入口（自然曝光/分销）均不可见、不可领取——面向 C 端发放的券必须显式选渠道 |
| personalLimit | Integer | 否 | 每人总限领，≥0（0/null=不限） |
| personDailyLimit | Integer | 否 | 每人每日限领，≥0 |
| maxStack | Integer | 否 | 同券最多叠加张数1..50，默认1；通用券逻辑可能截断越界值，调用方仍传合法值。**DH_COUPON特例：显式非1直接拒绝，草稿亦如此；省略规范化为1**。运费全免按页面固定1 |
| rules | Array | 否 | 优惠规则（同活动 create 的 rules 结构；满减/折扣券核心配置） |
| stackableExclusions | Array | 否 | 互斥配置 `[{targetSubCode, conflict}]` |
| productScopeType / goodsList / categoryCodes / brandIds / storeIds | - | 否 | 同活动create；storeIds已确认全部时省略/null，正式提交不传[]；范围未知先确认 |
| draft | Boolean | 否 | 默认 true 草稿宽松校验 |
| titleEn / description / descriptionEn / tag / imageUrl / qrcodeUrl | String | 否 | 物料字段 |
| remark | String | 否 | 内部备注 ≤100 字 |

### 出参

- **关键字段来源**：`pendingId`（→ 编辑/提审/审核）、`promotionId`（预分配，→ 审核历史）。此响应不含正式 templateId；审核后按 promotion-coupon.md 的参数来源链获取，不能用 promotionId 替代。

### 调用示例

示例假设商品、门店和人群范围均已确认；券示例还已确认自然曝光渠道及领取控制。时间仅演示结构，真实执行须使用用户确认的窗口并重新检查当前时间，不照抄示例日期。

```json
{"capability":"ops.promotion.coupon-template.create","input":{"promotionSubCode":"MJ_COUPON","title":"满100减10元券","quantity":1000,"acquireExpireStart":"1793498400000","acquireExpireEnd":"1794103200000","useExpireType":1,"useExpireStart":"1793502000000","useExpireEnd":"1796090400000","rules":[{"ruleIndex":1,"thresholdType":"AMOUNT","thresholdValue":10000,"actions":[{"discountType":1,"feeType":1,"discountValue":1000}]}],"productScopeType":"all","draft":true,"channelCodes":[1],"acquireControl":1,"transferEnabled":false},"summary":"创建满100减10元券模板草稿"}
```

---

## ✅ 编辑券模板草稿 — `ops.promotion.coupon-template.update`

- 🟡 可逆写
- **前置**：pending 草稿(0)/已驳回(3)；**version 必传**（来自 pending 详情）。先读详情保留未改动字段。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核 ID |
| version | Integer | ✅ | 乐观锁版本 |
| (其余字段) | - | - | 结构同创建接口（title 必填）。⚠️ **编辑内容不含 promotionSubCode**——券类型由 pending 决定，不可改类型 |

### 调用示例

先查询pending.detail，从couponDetail抽取创建请求形态的可编辑完整快照`editable`，保留领取/使用窗口、有效期模式、规则、渠道、范围、人群、领取控制和转赠现值。以下仅演示合并，不是可直接发送的局部JSON：

```javascript
const input = {
  ...editable,
  pendingId: detail.pendingId,
  version: detail.version,
  quantity: 2000,
  draft: true,
};
delete input.promotionSubCode; // 券类型由pending决定，编辑不可改类型
```

检查完整配置后以该input调用`ops.promotion.coupon-template.update`并回读。省略主要字段可能清空，channelCodes缺省按空比较；acquireControl/transferEnabled未指定时服务端有保留特例，不能因此假定所有字段都按PATCH保留。已有激活券时不能缩短useExpireDuration。

---

## ✅ 券模板提审 — `ops.promotion.coupon-template.submit`

- 两种用法：只传 pendingId 直接提审既有草稿；或同时带完整编辑内容（含 version）先保存再提审。**前置**：草稿(0)/已驳回(3)。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核 ID |
| (编辑内容) | - | 否 | 结构同 update 入参 |

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.submit","input":{"pendingId":"4900000000000000001"},"summary":"提交满减券模板审核"}
```

---

## ✅ 券模板审核（通过/驳回合一） — `ops.promotion.coupon-template.check`

- 🟡 审核动作（approved=true 通过）；🔴 approved=false 为驳回（商业影响——延迟领券上线），与 pending.approve / pending.reject 同一实现的合一入口
- **前置**：pending 待审核(1)。**approved 必填**；驳回时 reason **必填**（服务端强校验非空，≤500 字）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核 ID |
| approved | Boolean | ✅ | true=通过 / false=驳回 |
| reason | String | 条件 | 驳回时**必填**（服务端强校验非空，具体可行动），≤500 字；通过时仅传用户明确提供的意见，未提供则省略 |

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.check","input":{"pendingId":"4900000000000000001","approved":false,"reason":"发行量与预算不符，请核对后重新提审"},"summary":"驳回券模板审核"}
```

---

## ✅ 停用券模板 — `ops.promotion.coupon-template.stop`

- 🔴 商业影响——停止领券，活动进入已结束；已领券的运行态可用性也受活动状态影响，不能承诺继续可用。这不等同逐张退券或将券实例持久状态改为已作废；具体券的运行态以 coupon.detail 或 coupon.library 返回的 usable/runtimeStatus 与不可用原因核验；coupon.check 仅做实例状态、有效期和金额门槛预检，不检查活动/模板运行态，available=true不能证明停模板后仍可使用。
- **前置**：未开始/预热/进行中/已暂停（同活动停用状态集）；存在变更重审 pending（变更审核中）时会被拒绝。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.stop","input":{"templateId":"4300000000000000001"},"summary":"停用满减券模板"}
```

---

## ✅ 暂停券模板 — `ops.promotion.coupon-template.pause`

- 可逆写（resume 恢复）；暂停期间已领券也会因活动暂停而暂不可用，恢复后仍需核对券状态与有效期，不能仅承诺“只暂停领取”。
- **前置**：预热(3)/进行中(4)。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.pause","input":{"templateId":"4300000000000000001"},"summary":"暂停券模板领取"}
```

---

## ✅ 恢复券模板 — `ops.promotion.coupon-template.resume`

- **前置**：仅已暂停(6)；已过可领取/结束时间不可恢复。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.resume","input":{"templateId":"4300000000000000001"},"summary":"恢复券模板领取"}
```

---

## ✅ 删除券模板 — `ops.promotion.coupon-template.delete`

- 🔴 不可逆
- **前置**：仅草稿(1)/未开始(2)；已发放过券的模板不可删除；变更审核中会被拒绝。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.delete","input":{"templateId":"4300000000000000001"},"summary":"删除未发放的券模板"}
```

---

## ✅ 生成分享太阳码 — `ops.promotion.coupon-template.share-qrcode`

- 生成物料（调用微信开放能力）
- **前置**：先用 share-capability 确认 shareAllowed=true；分销券会被拒绝并返回原因。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 出参（原始数据）

- **格式敏感字段**：`qrcode` 是图片 Data URI（`data:image/<实际MIME子类型>;base64,...`，如 image/jpeg 或 image/png），保留返回的真实 MIME，不能固定按 PNG 解释。它不是 HTTP 下载地址；按当前运行时支持的图片交付方式处理，不编造链接、不复制长 Base64 到命令参数；交付受限时如实说明。

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.share-qrcode","input":{"templateId":"4300000000000000001"},"summary":"生成券详情太阳码"}
```

---

## ✅ 生成分享短链接 — `ops.promotion.coupon-template.share-short-link`

- 生成物料（调用微信开放能力）
- **前置**：同太阳码（先查 share-capability）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 出参（原始数据）

- **格式敏感字段**：`shortLink`（短链接 URL）

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.share-short-link","input":{"templateId":"4300000000000000001"},"summary":"生成券详情短链接"}
```

---
