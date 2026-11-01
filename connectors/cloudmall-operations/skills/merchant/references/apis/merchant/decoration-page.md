# 商户域 — 装修页面查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-decoration.md`（只读排查）。
> 覆盖小程序装修页面的只读查询：列表/详情/版本历史/门店绑定/发布前置校验/无效绑定检测。出参为上游**原始业务数据**（不裁剪字段）。
> **核心枚举**：页面状态 `status` 0=草稿 / 1=已发布 / 2=已下线；页面类型 `pageType` home=首页 / activity=活动页 / custom=自定义页 / profile=个人中心页；版本状态 `status` 1=当前线上 / 0=历史。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：decoration-page.search 装修页面分页 · decoration-page.detail 装修页面详情 · decoration-page.versions 版本列表 · decoration-page.version-detail 版本详情 · decoration-page.bindings 门店绑定列表 · decoration-page.binding-check 发布前置校验 · decoration-page.invalid-bindings 无效绑定检测

---

## ✅ 装修页面分页 — ops.merchant.decoration-page.search

- **说明**：分页查询租户装修页面；keyword 匹配页面名称/ID。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，**默认 10**（与商户域通用默认 20 不同） |
| keyword | String | 否 | 名称/ID 关键词，≤50 字符 |
| status | Integer | 否 | 页面状态：0 草稿 / 1 已发布 / 2 已下线 |
| pageType | String | 否 | 页面类型：home / activity / custom / profile |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].pageId`（→ 详情/版本/绑定/发布校验的路径参数）
- **枚举字段**：`status`（0/1/2）、`isHomepage`（布尔，默认首页全租户唯一）
- **格式敏感字段**：`scheduledPublishTime`/`scheduledOfflineTime`（**毫秒时间戳**，定时发布/下线时间）；`version`/`publishedVersion`（整数版本号，两者不同=有未发布草稿改动）
- 展示型字段 `pageCode/pageName/tags/componentCount/bindingScope/bindingShopCount/bindingShopNames/updatedBy` 可直接透传；`viewCount30d`/`visitorCount30d` 本期恒为 0，不要引用作经营结论。

### 调用示例

```json
{"capability":"ops.merchant.decoration-page.search","input":{"pageNum":1,"pageSize":10,"pageType":"home","status":1},"summary":"查看已发布的首页装修"}
```

---

## ✅ 装修页面详情 — ops.merchant.decoration-page.detail

- **说明**：查询单个装修页面完整信息。装修配置 `schemaJson` 为序列化 JSON 字符串（组件树）——Agent 只做结构概述（组件类型/数量），不解析重构后提交。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageId | String | ✅ | 页面 ID（十进制字符串，路径参数） |

### 出参（原始数据）

- **路径参数来源**：`pageId`、`version`（草稿版本号）
- **枚举字段**：`status`（0/1/2）、`pageType`
- **格式敏感字段**：`schemaJson`（string，内为 JSON 组件树）；`scheduledPublishTime`/`scheduledOfflineTime`（毫秒时间戳）
- 素材/图片地址为带时效的临时签名 URL，过期需重查，不持久化。

### 调用示例

```json
{"capability":"ops.merchant.decoration-page.detail","input":{"pageId":"3000000000000000001"},"summary":"查看该装修页面的当前配置"}
```

---

## ✅ 版本列表 — ops.merchant.decoration-page.versions

- **说明**：查询页面的发布版本历史（每次发布生成一条）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageId | String | ✅ | 页面 ID（路径参数） |

### 出参（列表，原始数据）

- **路径参数来源**：`[].id`（版本记录 ID → 版本详情路径参数）
- **枚举字段**：`[].status`（1=当前线上 / 0=历史）
- **格式敏感字段**：`[].publishedTime`（yyyy-MM-dd HH:mm:ss）
- 展示型字段 `versionNo/publishNote/publishedBy` 可直接透传。

### 调用示例

```json
{"capability":"ops.merchant.decoration-page.versions","input":{"pageId":"3000000000000000001"},"summary":"查看首页装修的发布版本历史"}
```

---

## ✅ 版本详情 — ops.merchant.decoration-page.version-detail

- **说明**：查询单个历史版本的完整快照（发布当时的页面配置）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| versionId | String | ✅ | 版本记录 ID（十进制字符串，路径参数；来自版本列表出参 `id`） |

### 出参（原始数据）

- **格式敏感字段**：`schemaJson`（string，发布时刻的组件树快照）；时间字段 yyyy-MM-dd HH:mm:ss
- 版本快照同样含临时签名 URL，不持久化。

### 调用示例

```json
{"capability":"ops.merchant.decoration-page.version-detail","input":{"versionId":"3100000000000000001"},"summary":"对比线上版本当时的装修配置"}
```

---

## ✅ 门店绑定列表 — ops.merchant.decoration-page.bindings

- **说明**：查询页面绑定的生效范围（小程序/门店）——决定装修页在哪些渠道可见。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageId | String | ✅ | 页面 ID（路径参数） |

### 出参（列表，原始数据）

- **枚举字段**：`[].bindingType`（1=按小程序 / 2=按门店）
- **路径参数来源**：`[].id`（绑定记录 ID；当前域未开放排序写操作，仅作标识）
- 展示型字段 `miniProgramId/miniProgramName/shopId/shopName` 可直接透传。

### 调用示例

```json
{"capability":"ops.merchant.decoration-page.bindings","input":{"pageId":"3000000000000000001"},"summary":"查看该活动页绑定了哪些门店"}
```

---

## ✅ 发布前置校验 — ops.merchant.decoration-page.binding-check

- **说明**：校验页面是否满足发布/定时发布前置条件。规则：home 类型且非默认首页时必须有门店绑定才允许发布。返回 `{valid: boolean, message: 原因}`——页面不存在时同样返回 valid=false。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageId | String | ✅ | 页面 ID（路径参数） |

### 出参（原始数据）

- `valid`（布尔）与 `message`（不满足时的原因描述）直接转述给用户。

### 调用示例

```json
{"capability":"ops.merchant.decoration-page.binding-check","input":{"pageId":"3000000000000000001"},"summary":"诊断这个首页为什么不能定时发布"}
```

---

## ✅ 无效绑定检测 — ops.merchant.decoration-page.invalid-bindings

- **说明**：扫描当前租户全部装修页面，返回「已被删除但仍存在绑定关系」的门店信息（绑定残留会导致页面在失效渠道空挂）。

### 入参

无（空对象）。

### 出参（原始数据）

- 返回无效绑定清单（页面 × 已删门店）；检测结果为空=无残留。清除操作未开放，发现残留时指引用户到运营端装修页处理。

### 调用示例

```json
{"capability":"ops.merchant.decoration-page.invalid-bindings","input":{},"summary":"检查是否有已删除门店仍绑在装修页上"}
```

---

## ⛔ 未开放（装修页面）

| 操作 | 不开放理由 |
|------|-----------|
| 保存草稿 / 发布 / 下线 / 定时 / 设首页 / 设生效 / 复制 / 删除 / 批量打标 | 依赖可视化装修编辑器的组件编排与编辑锁机制，当前开放能力集未包含该链路 |
| 回滚 / 强制回滚 | 回滚=覆写草稿后需人工在编辑器确认再发布，编辑器链路未纳入开放能力 |
| 获取/释放编辑锁、预览 token | 编辑器会话态操作 |
