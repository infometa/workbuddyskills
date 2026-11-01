# 商品域 — 评价写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-review.md`；现态读取（评价列表/详情/Tab 计数/关键词/设置现值）先读 `review-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：review.reply 回复评价 · review.audit 评价审核 🔴 · review.batch-audit 评价批量审核 🔴 · review.append-audit 追评审核 🔴 · review.keyword-batch-enable 批量启用关键词 · review.keyword-enable 启用关键词 · review.keyword-disable 停用关键词 · review.keyword-reject 驳回关键词 · review.reply-template-create 新增回复模板 · review.reply-template-update 编辑回复模板 · review.reply-template-delete 删除回复模板 🔴 · review.reply-template-set-default 设默认模板 · review.setting-save 评价设置保存 🔴

---

## ✅ 回复评价 — ops.product.review.reply

- **语义**：回复内容以运营方身份公开可见，文案先给用户过目
- **前置条件**（服务端强制）：仅**审核通过态**（APPROVED/AUTO_APPROVED/TIMEOUT_APPROVED）的评价可回复——对待审核/已拒绝评价回复会被拒绝

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reviewId | String | ✅ | 评价ID |
| content | String | ✅ | 回复内容 |
| appendReviewId | String | — | 追评ID（回复追评时传，来自详情数据） |

### 出参（原始返回）

`data` 为 `null`（Void）；以 `review.detail` 核验回复已展示。

### 调用示例

```json
{"capability":"ops.product.review.reply","input":{"reviewId":"5000012345678901234","content":"感谢您的反馈，已为您跟进处理"},"summary":"回复用户评价"}
```

---

## ✅ 评价审核 — ops.product.review.audit

- 🔴 商业影响档位；审核决定评价是否展示（APPROVE 展示 / REJECT 隐藏）
- **状态流纪律**：驳回仅对**待审核（PENDING_AUDIT）**状态生效；已通过/已拒绝的评价均为**终态，不可再变更**——批量驳回前先按待审核状态过滤 ID 清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 评价ID |
| action | String | ✅ | `APPROVE` / `REJECT` |
| rejectReason | String | REJECT 时必填 | 建议取值：`SPAM`-垃圾评价 / `INAPPROPRIATE`-不当内容 / `IRRELEVANT`-与商品无关 / `OTHER`-其他。⚠️ 服务端只校验非空、**不做枚举强制**（自由字符串落库）——按本表取值保证数据口径，不传其他值 |
| rejectRemark | String | OTHER 时建议 | 驳回补充说明（客户端约定 OTHER 时提供；服务端不强制） |

### 出参（原始返回）

`data` 为 `null`（Void）；以 `review.detail`/`review.search` 回读状态。

### 调用示例

```json
{"capability":"ops.product.review.audit","input":{"id":"5000012345678901234","action":"APPROVE"},"summary":"审核通过该评价"}
```

---

## ✅ 评价批量审核 — ops.product.review.batch-audit

- 🔴 商业影响档位；批量 ≤100，先按待审核状态过滤 ID 清单，超过分批提交
- **状态流纪律**：同单条审核——终态评价计入失败；结果仅计数无逐条明细

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 评价ID列表，≤100 项（先按待审核状态过滤；超过分批提交） |
| action | String | ✅ | `APPROVE` / `REJECT` |
| rejectReason | String | REJECT 时必填 | 同单条审核取值（SPAM/INAPPROPRIATE/IRRELEVANT/OTHER） |
| rejectRemark | String | OTHER 时建议 | 驳回补充说明 |

### 出参（原始返回）

批量为计数结果 `{totalCount, successCount, failCount}`（终态评价计入失败；无逐条明细——有失败时按计数报告并回读列表核对）。

### 调用示例

```json
{"capability":"ops.product.review.batch-audit","input":{"ids":["5000012345678901234","5000012345678901235"],"action":"APPROVE"},"summary":"批量通过两条待审核评价"}
```

---

## ✅ 追评审核 — ops.product.review.append-audit

- 🔴 商业影响档位；**id 为追评记录自身ID**（来自评价详情中追评数据的 id 字段，非主评价ID）
- **语义/状态流纪律**：同评价审核（APPROVE 展示 / REJECT 隐藏；驳回仅对待审核追评生效）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 追评记录自身ID（来自评价详情 `appendReviews[].id`） |
| action | String | ✅ | `APPROVE` / `REJECT` |
| rejectReason | String | REJECT 时必填 | 同评价审核取值（SPAM/INAPPROPRIATE/IRRELEVANT/OTHER） |
| rejectRemark | String | OTHER 时建议 | 驳回补充说明 |

### 出参（原始返回）

`data` 为 `null`（Void）。

### 调用示例

```json
{"capability":"ops.product.review.append-audit","input":{"id":"5000012345678901234","action":"REJECT","rejectReason":"INAPPROPRIATE"},"summary":"以不当内容驳回追评"}
```

---

## ✅ 批量启用关键词 — ops.product.review.keyword-batch-enable

- **语义**：批量启用候选池关键词（`ids` 来自 keyword-candidates 的 `records[].id`）
- ⚠️ **部分失败静默**（个别 ID 启用失败仅记服务端日志，不报错、无失败明细）——执行后用 `review.keywords-enabled` 回读复核启用结果

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 关键词ID列表，≤100 项（来自 keyword-candidates 的 `records[].id`） |

### 出参

`data` 为 `null`（Void）。

### 调用示例

```json
{"capability":"ops.product.review.keyword-batch-enable","input":{"ids":["5100012345678901234","5100012345678901235"]},"summary":"批量启用两个评价关键词"}
```

---

## ✅ 关键词启用 — ops.product.review.keyword-enable

- **语义**：单条置为 ENABLED（词云/筛选项可用）
- ⚠️ **服务端不校验前置状态**（直接覆盖目标状态）——执行前先读现态（keyword-candidates / keywords-enabled），避免重复操作造成口径混乱。批量场景用 `keyword-batch-enable`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 关键词 ID（路径参数，来自候选池/已启用列表） |

### 调用示例

```json
{"capability":"ops.product.review.keyword-enable","input":{"id":"5100012345678901234"},"summary":"启用评价关键词「行程丰富」"}
```

---

## ✅ 关键词停用 — ops.product.review.keyword-disable

- **语义**：单条置为 DISABLED
- ⚠️ **服务端不校验前置状态**（直接覆盖目标状态）——执行前先读现态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 关键词 ID（路径参数，来自候选池/已启用列表） |

### 调用示例

```json
{"capability":"ops.product.review.keyword-disable","input":{"id":"5100012345678901234"},"summary":"停用评价关键词「行程丰富」"}
```

---

## ✅ 关键词驳回 — ops.product.review.keyword-reject

- **语义**：单条置为 REJECTED（候选词驳回）
- ⚠️ **服务端不校验前置状态**（直接覆盖目标状态）——执行前先读现态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 关键词 ID（路径参数，来自候选池/已启用列表） |

### 调用示例

```json
{"capability":"ops.product.review.keyword-reject","input":{"id":"5100012345678901234"},"summary":"驳回候选评价关键词「虚假宣传」"}
```

---

## ✅ 新增回复模板 — ops.product.review.reply-template-create

- **语义**：模板供回复时快速引用（回复仍传最终文案）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 模板名称 |
| content | String | ✅ | 模板内容 |
| sortOrder | Integer | — | 排序 |

### 调用示例

```json
{"capability":"ops.product.review.reply-template-create","input":{"name":"感谢模板","content":"感谢您的评价，我们会继续努力！","sortOrder":1},"summary":"新建感谢类回复模板"}
```

---

## ✅ 编辑回复模板 — ops.product.review.reply-template-update

- **语义**：编辑模板（**全量覆盖**——name/content 一并传全）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |
| name | String | ✅ | 模板名称 |
| content | String | ✅ | 模板内容 |
| sortOrder | Integer | — | 排序 |

### 调用示例

```json
{"capability":"ops.product.review.reply-template-update","input":{"id":"5200012345678901234","name":"感谢模板","content":"感谢您的评价，我们会继续努力！"},"summary":"更新回复模板内容"}
```

---

## ✅ 删除回复模板 — ops.product.review.reply-template-delete

- 🔴 不可逆；执行前向用户确认模板名称

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |

### 调用示例

```json
{"capability":"ops.product.review.reply-template-delete","input":{"id":"5200012345678901234"},"summary":"删除回复模板"}
```

---

## ✅ 设默认回复模板 — ops.product.review.reply-template-set-default

- **语义**：把模板设为默认（新回复的预填来源）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |

### 调用示例

```json
{"capability":"ops.product.review.reply-template-set-default","input":{"id":"5200012345678901234"},"summary":"设为默认回复模板"}
```

---

## ✅ 评价设置保存 — ops.product.review.setting-save

- 🔴 商业影响档位（全局配置）；编辑前先 `setting-get` 读现态；修改范围向用户确认
- **语义**：保存评价全局设置。⚠️ 与商品通用配置（general-config）**同表同源**——此处保存会改写商品通用配置的审核时效字段，向用户说明影响面

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reviewTimeout | Long | ✅ | 审核时效（秒），3600~2592000（1 小时~30 天） |
| defaultReviewEnabled | Boolean | ✅ | 默认好评开关 |
| defaultReviewTimeout | Long | — | 默认好评时间（秒）；启用时范围 86400~7776000（1~90 天） |
| appendReviewWindow | Integer | ✅ | 追评窗口（天），1~90 |
| scoreDimensions | List | — | 评分维度列表（结构见下；`fixed=true` 为客户端约定标记，**服务端无删除保护**——全量覆盖保存，未保留的维度会被移除） |

**scoreDimensions[] 子结构**：`key`（✅ 维度标识，英文 ≤50 字符）、`name`（✅ 维度名称 ≤20 字符）、`fixed`（是否固定维度）、`sortOrder`。

### 调用示例

```json
{"capability":"ops.product.review.setting-save","input":{"reviewTimeout":86400,"defaultReviewEnabled":true,"defaultReviewTimeout":604800,"appendReviewWindow":30},"summary":"保存评价设置（审核时效改为1天）"}
```
