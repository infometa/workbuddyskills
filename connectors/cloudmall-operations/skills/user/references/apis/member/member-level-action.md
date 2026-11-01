# 会员域 — 会员等级写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-level.md`；等级现值读取（列表/详情/规则/变更流水）先读 `member-level-query.md`。
> 所有 ID 均为十进制字符串；等级为全租户配置，写操作均属高危（🔴）；须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.level.create 新建等级 🔴 · member.level.update 编辑等级 🔴 · member.level.status 等级启停 🔴 · member.level.rule-description-save 保存等级规则描述 🔴 · member.level.downgrade-rule-save 保存降级规则 🔴 · member.level.upload-image 等级图片上传

---

## ✅ 新建等级 — ops.member.level.create

- 🔴 全租户配置——复述影响面后执行

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| levelCode | String | ✅ | 等级编号，正则 `^V\d{1,2}$`（V0~V99），同租户唯一 |
| levelName | String | ✅ | 等级名称（≤10 字符，唯一） |
| growthValue | Integer | ✅ | 所需成长值（≥0，不得与其他等级重复，且须与编号顺序一致——V(n) 的成长值必须大于所有 V(m<n)、小于所有 V(m>n)） |
| pointsMultiplierEnabled / pointsMultiplier | — | — | ⚠️ DTO 兼容保留字段，**当前实现不落库不生效**（列表返回的积分倍率由权益域 POINTS_MULTIPLIER 策略动态计算，不在等级创建/编辑中配置） |
| cardImage / bgImage | String | — | 卡面图/背景图 URL（≤500 字符；先用 `level.upload-image` 上传取回 URL） |
| themeColor | String | — | 等级色（CSS 颜色值，如 #FF6B35，≤20 字符） |

### 出参（原始返回）

创建结果对象（含新等级 `id`）。

### 业务规则（服务端）

- 等级数量上限 **10**（超限报错）。
- growthValue 顺序校验同创建（见入参说明）。

### 调用示例

```json
{"capability":"ops.member.level.create","input":{"levelCode":"V10","levelName":"特邀会员","growthValue":20000,"themeColor":"#FF6B35"},"summary":"新建特邀会员等级"}
```

---

## ✅ 编辑等级 — ops.member.level.update

- 🔴 levelCode 不可改；growthValue 须保持与编号顺序一致

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 等级 ID |
| levelName | String | ✅ | 等级名称（≤10 字符，唯一，排除自身） |
| growthValue | Integer | ✅ | 所需成长值（≥0，不与其他等级重复，顺序一致性同创建） |
| pointsMultiplierEnabled / pointsMultiplier | — | — | ⚠️ 同新建——不落库不生效（倍率由权益域策略驱动） |
| cardImage / bgImage / themeColor | — | — | 同新建 |

### 出参（原始返回）

`data` 为 `null`；回读 `level.list` / `level.detail` 核验。

### 调用示例

```json
{"capability":"ops.member.level.update","input":{"id":"1000012345678901234","levelName":"至尊会员","growthValue":12000},"summary":"调整至尊会员等级成长值门槛"}
```

---

## ✅ 等级启停 — ops.member.level.status

- 🔴 全租户配置——停用等级影响该等级会员的权益命中与升级判定

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 等级 ID |
| status | Integer | ✅ | 0=启用 / 1=停用 |

### 出参（原始返回）

`data` 为 `null`；回读 `level.list` 核验。

### 调用示例

```json
{"capability":"ops.member.level.status","input":{"id":"1000012345678901234","status":1},"summary":"停用一个会员等级"}
```

---

## ✅ 保存等级规则描述 — ops.member.level.rule-description-save

- 🔴 面向 C 端展示的规则说明——upsert 语义（整体覆盖）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | String | — | 富文本 HTML 内容 |

### 出参（原始返回）

`data` 为 `null`；回读 `level.rule-description` 核验。

### 调用示例

```json
{"capability":"ops.member.level.rule-description-save","input":{"content":"<p>成长值达到对应门槛即自动升级，等级有效期见降级规则。</p>"},"summary":"保存等级规则说明"}
```

---

## ✅ 保存降级规则 — ops.member.level.downgrade-rule-save

- 🔴 全租户配置——降级策略影响全体会员等级到期判定；三种策略互斥单选

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| strategyType | Integer | ✅ | 0=不降级 / 1=按发放日过期 / 2=按自然年到期 |
| expiryYears | Integer | 条件 | 策略 1 必填，1~5 |
| expiryNthYear | Integer | 条件 | 策略 2 必填，1~3 |
| expiryMonth | Integer | 条件 | 策略 2 必填，1~12 |
| expiryDay | Integer | 条件 | 策略 2 必填，1~31 |

### 出参（原始返回）

`data` 为 `null`；回读 `level.downgrade-rule` 核验。

### 调用示例

```json
{"capability":"ops.member.level.downgrade-rule-save","input":{"strategyType":1,"expiryYears":1},"summary":"设置成长值按发放一年后过期降级"}
```

---

## ✅ 等级图片上传 — ops.member.level.upload-image

- multipart 图片上传（无业务副作用，产出 COS URL 供 create/update 的 cardImage/bgImage 使用）
- **传输形态特例**：multipart 文件上传

### 入参（multipart 文件）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件 | ✅ | JPG/JPEG/PNG，≤2MB（扩展名与 Content-Type 双重校验） |

### 出参（原始返回）

对象含 `url`（图片访问 URL，→ create/update 的 `cardImage` / `bgImage`）。

### 调用示例

```json
{"capability":"ops.member.level.upload-image","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传等级卡面图（需配合运行时文件上传通道）"}
```
