# 商品域 — 类目与品牌写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-dictionary.md`；现态读取（类目树/品牌选项/品牌详情/关联商品）先读 `category-brand-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：category.batch-save 类目批量维护 🔴 · brand.create 品牌创建 · brand.update 品牌编辑 · brand.delete 品牌删除 🔴 · brand.upload-logo 品牌Logo上传 · brand.bind-spus 品牌绑定商品 · brand.unbind-spus 品牌解绑商品

---

## ✅ 类目批量维护 — ops.product.category.batch-save

- 🔴 商业影响档位（含删除）
- **语义**：一次提交类目结构变更，支持四组操作（可任意组合）：新增 / 编辑 / 删除 / 排序。整批执行，返回 `success` 与 `message`。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| additions | List | — | 新增类目列表（结构见下） |
| updates | List | — | 编辑类目列表（结构见下） |
| deletions | List&lt;String&gt; | — | 要删除的类目编码列表 |
| sortChanges | List | — | 排序变更列表（结构见下） |

**additions[] 子结构**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tempId | String | ✅ | 前端临时 ID（后端不持久化，任意唯一串即可） |
| categoryName | String | ✅ | 类目名称（≤64 字符） |
| parentCode | String | ✅ | 父类目编码；**一级类目传空字符串 `""`** |
| level | Integer | ✅ | 层级 1~5 |
| sortOrder | Integer | ✅ | 同级排序（≥0） |

**updates[] 子结构**：`categoryCode`（✅）、`categoryName`（✅ ≤64）、`sortOrder`（✅ ≥0）。

**sortChanges[] 子结构**：`categoryCode`（✅）、`sortOrder`（✅ ≥0）。

### 出参

- `success`（boolean，是否全部成功）、`message`（结果说明）。

### 前置条件与风险

- 🔴 删除**有子类目**或**挂有商品**的类目会被拒绝——删除前先用 `category.tree` 确认无子节点、用 `spu.search`（按 categoryCode）确认无商品。
- 同级类目名称重复会被拒绝（同级唯一）。
- 层级最深 5 级，超出被拒绝。

### 调用示例

```json
{"capability":"ops.product.category.batch-save","input":{"updates":[{"categoryCode":"T900001_C61","categoryName":"研学旅行","sortOrder":0}]},"summary":"把类目 T900001_C61 更名为研学旅行"}
```

---

## ✅ 品牌创建 — ops.product.brand.create

- **语义**：新建品牌。
- **唯一性预检**：品牌名称全局唯一，创建前先用 `brand.page`/`brand.options` 按名称查重；命中同名时与用户确认换名或复用既有品牌，不直接提交。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 品牌名称（≤50 字符；重名拒绝） |
| logo | String | — | 品牌 logo URL（来自 upload-logo 上传结果） |

### 出参

- 创建成功的品牌 `id`（string）。

### 调用示例

```json
{"capability":"ops.product.brand.create","input":{"name":"云营研学","logo":"https://cos.example.com/brand/logo.png"},"summary":"创建品牌云营研学"}
```

---

## ✅ 品牌编辑 — ops.product.brand.update

- **语义**：修改品牌名称/logo；编辑前先读详情确认现态，重名拒绝。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 品牌 ID（路径参数） |
| name | String | ✅ | 品牌名称（≤50 字符） |
| logo | String | — | 品牌 logo URL |

### 调用示例

```json
{"capability":"ops.product.brand.update","input":{"id":"2100012345678901234","name":"云营研学","logo":"https://cos.example.com/brand/logo.png"},"summary":"更新品牌名称"}
```

---

## ✅ 品牌删除 — ops.product.brand.delete

- 🔴 不可逆；执行前向用户确认品牌名称
- **语义**：删除品牌。🔴 **品牌下仍挂有 SPU 时删除被拒绝**——先解绑全部商品再删。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 品牌 ID（路径参数） |

### 前置条件与风险

- 🔴 不可逆；执行前向用户确认品牌名称。
- 有关联 SPU 时服务端拒绝（`BRAND_HAS_SPU`）——先 `brand.spus` 确认清单并解绑。

### 调用示例

```json
{"capability":"ops.product.brand.delete","input":{"id":"2100012345678901234"},"summary":"删除品牌云营研学"}
```

---

## ✅ 品牌 Logo 上传 — ops.product.brand.upload-logo

- **传输形态**：multipart 文件上传
- **语义**：上传品牌 logo 图片，返回 COS URL 供品牌创建/编辑的 `logo` 字段使用。

### 入参

- 文件部分：`file`（图片）；类型仅 **jpg / jpeg / png**，大小 **≤2MB**（超限或格式不符被拒绝）。

### 出参

- `url`（上传后的 COS 地址，→ brand.create/update 的 `logo`）。

### 调用示例

```json
{"capability":"ops.product.brand.upload-logo","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传品牌 logo 图片"}
```

---

## ✅ 品牌绑定商品 — ops.product.brand.bind-spus

- **语义**：把 SPU 绑定到品牌（更新这些 SPU 的品牌归属）。⚠️ 该接口入参为裸 JSON 对象（无表单 DTO），body 只认 `spuIds` 数组。**服务端无空值/上限校验**（调用纪律非服务端校验）：`spuIds` 缺失或空数组**静默成功但无任何操作**（不报错）；不存在的 SPU 静默跳过、无逐条结果（返回 Void）；元素须为十进制数字字符串（非数字会抛系统错误）；无数量上限。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 品牌 ID（路径参数） |
| spuIds | List&lt;String&gt; | ✅ | 要绑定的 SPU ID 列表（来自 spu.search） |

### 调用示例

```json
{"capability":"ops.product.brand.bind-spus","input":{"id":"2100012345678901234","spuIds":["2058365707555589633"]},"summary":"把商品绑定到云营研学品牌"}
```

---

## ✅ 品牌解绑商品 — ops.product.brand.unbind-spus

- **语义**：解除 SPU 与品牌的关联（清空这些 SPU 的品牌归属）。入参与 bind-spus 同构（`id` + `spuIds`），同样无服务端校验（空列表静默成功、不存在 SPU 静默跳过）；**仅对当前归属该品牌的 SPU 生效**（传入其他品牌归属的 SPU 会被静默忽略）。执行后用 `brand.spus` 回读核验实际生效清单。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 品牌 ID（路径参数） |
| spuIds | List&lt;String&gt; | ✅ | 要解绑的 SPU ID 列表（来自 spu.search/brand.spus） |

### 调用示例

```json
{"capability":"ops.product.brand.unbind-spus","input":{"id":"2100012345678901234","spuIds":["2058365707555589633"]},"summary":"解除商品与品牌的关联"}
```
