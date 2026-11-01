# 促销域 — 券实例写操作契约（资金面高危区）

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-coupon.md`
> ⚠️ 本模块为资金面高危区：发券/退券/停用/延期/解锁均直接影响用户资产，全部为单独定级的高危写。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：写 coupon.send · coupon.stop · coupon.cancel · coupon.delay · coupon.unlock（🔴 资金面高危）
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：操作前用 `coupon-runtime-query.md` 的 coupon.detail / coupon.library 确认券实例当前状态与持有人。
>
> ⚠️ **ID 格式口径**：`couponId`/`templateId` 必须使用用户明确提供或查询返回的十进制字符串 ID，保持原值，不转 Number，不补齐/截断。约 19 位只是常见外形，不能据长度断言对象不存在或必然 400；参数合法性按当前工具契约处理。非十进制标识先消歧，不猜 ID。写操作仍须读取现值并核对状态、权限与完整对象，不以 ID 能解析代替业务前置。

---

## ✅ 运营发券 — `ops.promotion.coupon.send`

- 🔴 **资金面高危写（本域最高风险）**
- **⛔ 调用门禁**：调用前**必须已存在一张用户已回答的确认卡**，卡内容逐项含：①券模板名称/面额/门槛 ②会员 ID 清单（逐个列出）③每人数量。**没有确认卡禁止调用**——以下情形均**不构成**发放授权，不得代替确认直接执行：
  - 用户说「建一张定向某人群的券」「定向发放」「配置批量发券」——这是**配置指令**（建模板+设置人群定向），不是执行发券
  - 人群包圈选完成、crowd.members 查到成员名单、标签绑定完成——**数据就绪 ≠ 授权发放**
  - 券模板已创建/已审核通过——**模板就绪 ≠ 授权发放**
  - 正确行为：把配置做完并汇报，然后**发确认卡列出会员名单与数量，等用户回答后再发券**
- **纪律**：执行前与用户逐项确认券模板（名称/面额/门槛）、会员 ID、发放数量；**单次只发一个会员**（memberId 单值，不是批量列表）；执行后回读券库核验。
- **requestId 幂等**：每次操作生成唯一值（如 `ops-send-日期-序号`）；**超时结果不确定时用同一 requestId + 相同参数重试是安全的**（幂等返回已有券），换参数重试会报冲突。
- **前置**（服务端校验，失败如实转述不重试）：模板对应活动进行中且已审核、模板未停用、在可领取时间窗内、库存充足、未超个人限领、人群匹配。

发券提示“发券幂等编号长度超过128”时是拼接参数超长，即使错误码为OUT_OF_STOCK也不能转述为缺货；缩短新操作的requestId前先确认旧请求未执行，未知结果保持原键查证。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| memberId | String | ✅ | 会员 ID（字符串，≤64 字符） |
| channelType | Integer | ✅ | 发券场景（见 CouponClaimChannel：**200 自动领券** 为运营发券默认；100 领券中心/101 商品详情页/102 购物车/300 装修页/400 营销弹窗）。⚠️ 枚举为口径约定——服务端只校验非空不拦截非法值，须自律传合法枚举 |
| requestId | String | ✅ | 幂等ID，调用方生成；实际要求promotionId_memberId_requestId拼接整体≤128字符，即requestId长度≤128−promotionId长度−memberId长度−2。不能只校验requestId≤128 |
| storeId | String | 否 | 发券门店 ID |

### 出参

- **关键字段来源**：返回值为新券实例 `couponId`——按平台 ID 约定一律以字符串处理，禁止转为 JSON Number（超出 JS 安全整数会丢精度）→ 详情/券库核验。

### 调用示例

```json
{"capability":"ops.promotion.coupon.send","input":{"templateId":"4300000000000000001","memberId":"900000000000000001","channelType":200,"requestId":"ops-send-20260909-0001"},"summary":"给指定会员发放满减券"}
```

---

## ✅ 停用券实例 — `ops.promotion.coupon.stop`

- 🔴 资金面高危（用户券立即作废）；执行后回读 `coupon.detail` 确认终态
- **前置**：仅激活态(1) → 已作废(5)。⚠️ 本能力只传 couponId 一个参数。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| couponId | String | ✅ | 券实例 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 调用示例

```json
{"capability":"ops.promotion.coupon.stop","input":{"couponId":"4400000000000000001"},"summary":"作废指定券实例"}
```

---

## ✅ 退券 — `ops.promotion.coupon.cancel`

- 🔴 资金面高危（作废券实例并释放额度）；执行后回读 `coupon.detail` 确认终态
- **前置**：仅激活(1)/锁定(2) 可退（已使用/已过期/已停用不可退，服务端校验）；只有同一cancel已创建逆向operation的状态5才能恢复幂等流程；stop产生的状态5没有该operation会报需人工处理，不能统称重复退券成功。

退券返回PROCESSING表示资源返还未完成，按同一couponId核验/恢复，遵循入口有限重试纪律；仅详情状态5不足以证明库存和额度已经返还，缺逆向证据时停止并如实报告人工处理原因。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| couponId | String | ✅ | 券实例 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| reason | String | 否 | 退券原因，≤200 字 |

### 调用示例

```json
{"capability":"ops.promotion.coupon.cancel","input":{"couponId":"4400000000000000001","reason":"客户投诉补偿误发，运营作废"},"summary":"退券并作废误发的券"}
```

---

## ✅ 券延期 — `ops.promotion.coupon.delay`

- 🔴 资产变更（延长有效期，执行后回读核验）
- **前置**：仅激活态(1)。**按天数顺延**（expireEnd += delayDays 天），不是设置绝对时间戳。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| couponId | String | ✅ | 券实例 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| delayDays | Integer | ✅ | 延期天数，1..365 |

### 调用示例

```json
{"capability":"ops.promotion.coupon.delay","input":{"couponId":"4400000000000000001","delayDays":30},"summary":"该券延期30天"}
```

---

## ✅ 券解锁（批量） — `ops.promotion.coupon.unlock`

- 🔴 资产变更（锁定 → 激活，逐券确认清单）
- **前置**：列表内全部券须为锁定态(2)；任一非锁定整批报错。B 端管理解锁**不校验订单号**。⚠️ 传入但库中不存在的 couponInstanceId 会被**静默忽略**（不报错、不解锁）——解锁后应回读核验实际解锁张数。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| couponInstanceIds | String[] | ✅ | 券实例 ID 列表，1..50 项 |
| orderNo | String | 否 | 关联订单号（B 端解锁可不传） |

### 调用示例

```json
{"capability":"ops.promotion.coupon.unlock","input":{"couponInstanceIds":["4400000000000000001"]},"summary":"解锁订单取消后仍锁定的券"}
```

---
