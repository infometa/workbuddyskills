# 商品域 — FAQ（商详常见问题）写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-detail.md`；现态读取（FAQ 列表）先读 `faq-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：faq.create 新增FAQ · faq.update 编辑FAQ · faq.toggle FAQ启停切换 · faq.reorder FAQ排序 · faq.delete 删除FAQ 🔴

---

## ✅ 新增 FAQ — ops.product.faq.create

- **语义**：新增商详 FAQ；返回新 FAQ 的 `id`（string）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | String | ✅ | 问题（≤30 字） |
| answer | String | ✅ | 答案（≤300 字纯文本） |
| productTypes | List&lt;String&gt; | — | 适用商品形态 |
| sort | Integer | — | 排序号（≥0，越大越靠前；**为空时追加到末尾**） |
| enabled | Boolean | — | 启用状态（默认 true） |
| effectiveStart | String | — | 生效起（yyyy-MM-dd HH:mm:ss；null=永久） |
| effectiveEnd | String | — | 生效止（null=永久；填写时须 ≥ effectiveStart） |

### 调用示例

```json
{"capability":"ops.product.faq.create","input":{"question":"如何预约讲解服务","answer":"下单后可在订单页预约讲解时间。","sort":0,"enabled":true},"summary":"新增讲解服务预约FAQ"}
```

---

## ✅ 编辑 FAQ — ops.product.faq.update

- **语义**：编辑 FAQ；`sort` **为空时保留原值**（非视为 0）——只改答案时不必回传 sort。

### 入参

与 create 同构，另需路径 `id`（FAQ ID）；`question`/`answer` 必填。

### 调用示例

```json
{"capability":"ops.product.faq.update","input":{"id":"2400012345678901234","question":"如何预约讲解服务","answer":"下单后可在订单页预约讲解时间，支持到店改约。"},"summary":"更新FAQ答案补充改约说明"}
```

---

## ✅ FAQ 启停切换 — ops.product.faq.toggle

- **语义**：切换启用状态，返回切换后的**新状态**（boolean）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | FAQ ID（路径参数） |

### 出参

- `data` 为切换后的新状态（true=已启用 / false=已停用）。

### 调用示例

```json
{"capability":"ops.product.faq.toggle","input":{"id":"2400012345678901234"},"summary":"停用该FAQ"}
```

---

## ✅ FAQ 排序 — ops.product.faq.reorder

- **语义**：拖拽排序——`faqIds` 数组顺序即最终展示顺序（服务端按数组顺序重排），≤50 条。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| faqIds | List&lt;String&gt; | ✅ | FAQ ID 列表（非空，≤50；**数组顺序=最终顺序**） |

### 调用示例

```json
{"capability":"ops.product.faq.reorder","input":{"faqIds":["2400012345678901234","2400012345678901235"]},"summary":"把预约FAQ排到第一位"}
```

---

## ✅ 删除 FAQ — ops.product.faq.delete

- 🔴 不可逆；执行前向用户确认问题内容
- **语义**：软删除 FAQ。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | FAQ ID（路径参数） |

### 调用示例

```json
{"capability":"ops.product.faq.delete","input":{"id":"2400012345678901234"},"summary":"删除过期的退款政策FAQ"}
```
