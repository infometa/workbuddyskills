# 促销域 — 兑换码写操作契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-coupon.md`
> 批次生效与作废均不可逆；创建后批次为 CREATING（异步生成码），需轮询批次详情到 INACTIVE 后才能生效。
> **兑换码消歧**：本文件用于平台生成优惠券兑换码批次，创建会生成券码并预占库存，不是「仅存互动活动草稿」。品牌方提供码、用户输入码领奖的活动属于营销域 `exchange-code`，见营销技能的 `interactive-activity-action.md`；即使奖品是优惠券，也不改走本文件。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：写 coupon-code.batch-create · batch-activate · batch-void · code-void（🔴 全部高危不可逆）
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：创建前用 `coupon-code-query.md` 的 templates 确认可用模板与库存余量；生效前用 batch-detail 确认已到 INACTIVE。
>
> ⚠️ **ID 格式口径**：`batchId`/`templateId`/`codeId` 必须使用用户明确提供或查询返回的十进制字符串 ID，保持原值，不转 Number，不补齐/截断。约 19 位只是常见外形，不能据长度断言对象不存在或必然 400；参数合法性按当前工具契约处理。非十进制标识先消歧，不猜 ID。写操作仍须读取现值并核对状态、权限与完整对象，不以 ID 能解析代替业务前置。

---

## ✅ 创建兑换码批次 — `ops.promotion.coupon-code.batch-create`

- 🔴 商业影响（发放可兑换资产）
- **前置**：券模板已配置库存；模板对应活动处于未开始/进行中，预热中不允许新制码。**执行前与用户确认批次名称、模板、数量。**
- **执行后回读**：轮询批次详情至 `INACTIVE`（生成完成）确认创建结果；FAILED_RELEASING表示失败资源仍在释放，先核验收敛；确认到FAILED后才可按用户意图另建新批次，不用新ID掩盖处理中/未知结果。
- **幂等**：`createRequestId`（≤96 字符）幂等——超时结果不确定时用同一 ID + 相同参数重试安全；**同 ID 不同参数**会报「createRequestId 已被不同参数使用」。
- 创建后批次为 `CREATING`（异步生成码），需轮询批次详情到 `INACTIVE`（生成完成）后才能生效。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| createRequestId | String | ✅ | 幂等请求 ID，≤96 字符，调用方生成 |
| batchName | String | ✅ | 批次名称，接口≤128字符，运营页面输入≤50字符；服务端trim首尾空格后参与幂等参数比较 |
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| totalCount | Integer | ✅ | 生成数量≥1，默认部署上限100000，可由服务端配置调整，以真实校验为准。⚠️ 必须为**整数字面量**（JSON 字符串数字/小数会被严格反序列化拒绝，报「totalCount 必须为整数」） |

### 出参（原始数据）

- **关键字段来源**：`batchId`（→ 详情/生效/作废/码查询）；含 batchStatus/generationStatus 等批次字段。

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.batch-create","input":{"createRequestId":"cc-batch-20260909-0001","batchName":"国庆门店兑换码","templateId":"4300000000000000001","totalCount":500},"summary":"创建500张满减券兑换码批次"}
```

---

## ✅ 批次生效 — `ops.promotion.coupon-code.batch-activate`

- 🔴 不可逆（生效后码可被领取）；执行前与用户确认批次范围；执行后回读批次详情确认 `ACTIVE`
- **前置**：仅完整生成的 `INACTIVE` 批次可生效（CREATING 中会报"只有完整生成的待生效批次可以生效"）。已 ACTIVE 的批次重复调用幂等返回。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batchId | String | ✅ | 批次 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.batch-activate","input":{"batchId":"4800000000000000001"},"summary":"生效兑换码批次"}
```

---

## ✅ 批次作废 — `ops.promotion.coupon-code.batch-void`

- 🔴 不可逆（未领取的码全部作废）；执行前与用户确认批次与剩余未领取数量；执行后回读批次详情确认 `VOIDED`
- **前置**：待生效/生效中批次可作废；已作废重复调用幂等返回。执行前与用户确认批次名称与剩余可领数量。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batchId | String | ✅ | 批次 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.batch-void","input":{"batchId":"4800000000000000001"},"summary":"作废该兑换码批次"}
```

---

## ✅ 单码作废 — `ops.promotion.coupon-code.code-void`

- 🔴 不可逆；执行前与用户确认目标码及归属批次；执行后回读码状态确认 `VOIDED`
- **前置**：码处于可作废状态（未领取/可用）；已作废幂等返回。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| codeId | String | ✅ | 码 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400；来自码查询的 codeId，不是明文码） | |

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.code-void","input":{"codeId":"5200000000000000001"},"summary":"作废单个兑换码"}
```

---

## 幂等失败与作废中间态

已确认FAILED的批次沿用原createRequestId仍返回创建失败；只有确认失败并重新确认新建意图后才生成新ID。单码或整批释放库存未完成时可能停在VOIDING并报“作废处理中”，存在单码VOIDING时整批也可能等待。保持同一codeId/batchId核验和有限恢复，直到回读VOIDED才报告作废完成；预算耗尽报告处理中，不另建批次或重复宣称失败。
