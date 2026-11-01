# 商品域 — 搭配写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-collocation.md`；现态读取（搭配列表/详情/看板/海报配置/投放物料）先读 `collocation-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：collocation.create 创建搭配 · collocation.update 编辑搭配 🔴 · collocation.online 搭配上线 · collocation.offline 搭配下线 · collocation.delete 删除搭配 🔴 · collocation.upload-image 搭配图片上传 · collocation.poster-image 海报主图上传 · collocation.poster-config-save 海报文案保存 · collocation.launch-material-retry 投放物料重试

---

## ✅ 创建搭配 — ops.product.collocation.create

- **语义**：表单先与用户确认（名称/门店/商品清单）后创建

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | ✅ | 归属门店ID |
| name | String | ✅ | 搭配名称，**6~10 个字** |
| recommendation | String | — | 推荐语，0 或 6~40 字 |
| hasMainImage | Boolean | ✅ | 是否有主图 |
| mainImageUrl | String | — | 主图 URL（hasMainImage=true 时非空即可）。⚠️ **服务端当前不校验该 URL 归属**（任意 URL 原样落库）——只使用 `ops.product.collocation.upload-image` 上传返回的 URL 或用户明确提供的可信 URL，不把陌生外链当内部素材；租户目录强校验仅存在于海报配置（poster-config-save） |
| showRecommendInDetail | Boolean | ✅ | 商详搭配推荐是否展示 |
| products | Array | ✅ | 搭配商品列表，**2~3 项**：`[{spuId, sortOrder（必填）, anchorX?, anchorY?, anchorLabel?, anchorDirection?}]`（spuId 来自商品搜索） |

### 出参（原始返回）

create 返回创建结果（含搭配ID）。

### 调用示例

```json
{"capability":"ops.product.collocation.create","input":{"storeId":"6000012345678901234","name":"研学装备搭配","hasMainImage":false,"showRecommendInDetail":true,"products":[{"spuId":"2058365707555589633","sortOrder":1},{"spuId":"2058365707555589634","sortOrder":2}]},"summary":"创建研学装备搭配"}
```

---

## ✅ 编辑搭配 — ops.product.collocation.update

- 🔴 商业影响档位；编辑为**全量覆盖**——先读详情，未列字段按需保留；表单先与用户确认（名称/门店/商品清单）

### 入参

与 create 字段一致，另需必填 `id`：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配ID |
| 其余字段 | — | — | 与创建相同（见 `collocation-action.md` 创建搭配表） |

### 出参（原始返回）

update 为 `null`（Void），以 `collocation.detail` 核验。

### 调用示例

```json
{"capability":"ops.product.collocation.update","input":{"id":"3300012345678901234","storeId":"6000012345678901234","name":"研学装备搭配","hasMainImage":false,"showRecommendInDetail":true,"products":[{"spuId":"2058365707555589633","sortOrder":1},{"spuId":"2058365707555589634","sortOrder":2}]},"summary":"更新搭配商品清单"}
```

---

## ✅ 搭配上线 — ops.product.collocation.online

- **语义**：上线该搭配；执行后以 `collocation.search`/`detail` 回读状态核验

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配ID |

### 调用示例

```json
{"capability":"ops.product.collocation.online","input":{"id":"3300012345678901234"},"summary":"上线该搭配"}
```

---

## ✅ 搭配下线 — ops.product.collocation.offline

- **语义**：下线该搭配；执行后以 `collocation.search`/`detail` 回读状态核验

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配ID |

### 调用示例

```json
{"capability":"ops.product.collocation.offline","input":{"id":"3300012345678901234"},"summary":"下线该搭配"}
```

---

## ✅ 删除搭配 — ops.product.collocation.delete

- 🔴 不可逆档位，执行前确认对象与名称

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配ID |

### 调用示例

```json
{"capability":"ops.product.collocation.delete","input":{"id":"3300012345678901234"},"summary":"删除该搭配"}
```

---

## ✅ 搭配图片上传 — ops.product.collocation.upload-image

- **传输形态**：multipart 文件上传
- **语义**：搭配普通图片上传（创建/编辑搭配的商品图等素材），JPEG/PNG/WebP ≤5MB，返回 COS URL。

### 入参

- 文件部分：`file`（JPEG/PNG/WebP，≤5MB）。

### 出参

- `url`（上传地址）、`key`（COS Key）。

### 调用示例

```json
{"capability":"ops.product.collocation.upload-image","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传搭配商品图"}
```

---

## ✅ 海报主图上传 — ops.product.collocation.poster-image

- **传输形态**：multipart 文件上传
- **语义**：分享海报主图专用上传（与 upload-image 的区别：独立租户目录 + 白名单类型与魔数校验），仅 JPEG/PNG/WebP ≤2MB，返回 **30 分钟时效签名 URL**；该 URL 用作 poster-config-save 的 `mainImageUrl`。

### 入参

- 文件部分：`file`（JPEG/PNG/WebP，≤2MB）。

### 出参

- `url`（30 分钟签名 URL → poster-config-save 的 mainImageUrl）、`key`。

### 调用示例

工作区文件路径（用户上传/工作区产出）：
```json
{"capability":"ops.product.collocation.poster-image","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传海报主图"}
```

素材中心引用（素材选择卡已确认的素材可直传，`material:{素材ID}`；不要下载素材到工作区再传）：
```json
{"capability":"ops.product.collocation.poster-image","input":{"file":"material:2100103386390499329", "fileType":"image"},"summary":"上传海报主图"}
```

---

## ✅ 海报文案配置保存 — ops.product.collocation.poster-config-save

- **语义**：upsert 海报文案配置。⚠️ **`mainImageUrl` 必须来自 `ops.product.collocation.poster-image` 上传结果**（独立租户目录 `product/collocation-poster/{租户ID}/`）——服务端强校验 URL 归属本租户目录，素材中心 URL、跨租户 URL、陌生外链一律被拒。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配 ID（路径参数） |
| mainTitle | String | ✅ | 分享主标题（≤12 字） |
| subTitle | String | — | 分享副标题（≤12 字） |
| promotionCopy | String | — | 投放文案（≤120 字） |
| mainImageUrl | String | ✅ | 海报主图 URL（须来自 poster-image 上传） |

### 调用示例

```json
{"capability":"ops.product.collocation.poster-config-save","input":{"id":"3300012345678901234","mainTitle":"研学好物搭配","mainImageUrl":"https://cos.example.com/product/collocation-poster/1/main.jpg"},"summary":"保存搭配海报文案"}
```

---

## ✅ 投放物料重试 — ops.product.collocation.launch-material-retry

- **语义**：重试生成失败的物料。**仅 FAILED 状态可重试**（否则 409）：二维码重置为 PENDING 重新异步生成，链接强制刷新缓存重新生成。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 搭配 ID（路径参数） |
| envVersion | String | ✅ | 环境版本 |
| materialTypes | List&lt;String&gt; | ✅ | 重试物料类型（如 `["qrcode"]`） |

### 调用示例

```json
{"capability":"ops.product.collocation.launch-material-retry","input":{"id":"3300012345678901234","envVersion":"release","materialTypes":["qrcode"]},"summary":"重试生成失败的太阳码"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 体验版预览码重试（preview-qrcode/retry） | legacy trial 兼容面 |
| 投放操作审计上报（launch-audit） | 前端用户行为埋点（扫码/复制/存海报等），实现仅打日志无业务副作用，非运营能力 |
