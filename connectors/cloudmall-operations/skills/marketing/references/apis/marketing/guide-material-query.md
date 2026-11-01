# 营销域 — 导购推广素材（业务素材 / 内容素材 / 素材分组）查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-content-flow.md`
> 三类对象：**业务素材**（对优惠券/促销活动/页面/游戏/直播/种草等既有业务对象的引用，控制其在导购工作台的展示）、**内容素材**（运营原创图文/视频内容，带发布生命周期与传播统计）、**素材分组**（content_material 与 speech 各自独立的两级分组树）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-material.business-search 业务素材分页（六类引用） · guide-material.content-search 内容素材分页（groupId 含子分组） · guide-material.content-detail 内容素材详情（附件 URL 30 分钟时效） · guide-material.content-stats 素材传播数据汇总 · guide-material.stats-trend 素材按日传播趋势 · guide-material.stats-store 素材门店维度明细 · guide-material-group.tree 素材分组树（bizType 区分两套体系） · guide.content-material.export-copy 素材复制记录异步导出（返回任务 ID）
> 写操作见 `guide-material-action.md`。

---

## 内容素材发布状态机（写操作前置判定）

```
draft（草稿）── publish ──▶ published（已发布）── unpublish ──▶ unpublished（已取消发布）
     ▲                                                        │
      └──────────────────── publish ───────────────────────────┘
```

- `publish` 前置：当前为 draft 或 unpublished。
- `unpublish` 前置：当前为 published。
- `delete` 前置：**非 published**（已发布素材必须先取消发布才能删除）。
- 定时发布（publishTimeType=scheduled）：系统定时任务到 publishStartTime 自动 draft→published、到 publishEndTime 自动 published→unpublished。

---

---

---

---

## ⛔ 未开放端点

| 端点 | 归属 | 未开放理由 |
|------|------|-----------|
| 素材文件上传 | 素材公共 | 需要文件型 capability 且素材创建链路未纳入能力化范围；素材创建时引用已上传素材的地址 |

---

## ✅ 业务素材分页 — `ops.marketing.guide-material.business-search`

- **说明**：按素材类型/展示状态/关键词分页查询；排序：置顶优先 → 置顶时间倒序 → 创建时间倒序。优惠券/促销类型的标题由后端实时回源富化（回源失败保留冗余标题），title 可能与添加时不一致。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| materialType | String | 否 | coupon（优惠券）/promotion（促销活动）/page（活动页面）/game（游戏）/live（直播）/grass（种草） |
| displayStatus | Integer | 否 | 1=显示 / 0=隐藏（注意是整数，非布尔） |
| keyword | String | 否 | 标题模糊匹配 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 切换显示/置顶 的路径 ID、批量移除 materialIds）
- **枚举字段**：`materialType`（coupon/promotion/page/game/live/grass）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）、`displayStatus`（Boolean，注意与入参整数 1/0 区分）、`isTop`（Boolean）
- **关键字段**：`sourceId`（关联源业务对象 ID，如券模板 ID/促销活动 ID）、`validity`（有效性）

### 调用示例

```json
{"capability":"ops.marketing.guide-material.business-search","input":{"pageNum":1,"pageSize":20,"materialType":"coupon","displayStatus":1,"keyword":"满减券"},"summary":"查询展示中的优惠券类业务素材"}
```

---

## ✅ 内容素材分页 — `ops.marketing.guide-material.content-search`

- **说明**：按内容类型/发布状态/分组/关键词分页查询；**groupId 查询自动包含其子分组**；排序：置顶优先 → 置顶时间倒序 → 创建时间倒序；每行带传播统计（收藏/分享/浏览/下单/导购数）与分组名。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| contentType | String | 否 | image（图片）/poster（海报）/video（视频）/image_poster（图片海报）/custom（自定义） |
| publishStatus | String | 否 | draft/published/unpublished |
| groupId | String | 否 | 分组 ID（**含子分组**） |
| keyword | String | 否 | 标题模糊匹配 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 详情/发布/取消发布/删除/置顶 的路径 ID）
- **枚举字段**：`publishStatus`（见状态机）、`contentType`（image/poster/video/image_poster/custom）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）、`favoriteCount`/`shareCount`/`guideCount`/`viewCount`/`orderCount`（整数统计）、`isTop`（Boolean）

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-search","input":{"pageNum":1,"pageSize":20,"contentType":"image","publishStatus":"published","groupId":"5200000000000000001","keyword":"秋装"},"summary":"查询已发布的秋装图片素材"}
```

---

## ✅ 内容素材详情 — `ops.marketing.guide-material.content-detail`

- **说明**：返回完整素材（文案 + 附件 + 关联内容 + 范围富化名称）；图片/视频地址为**30 分钟有效的临时访问地址**，不要持久化缓存。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |

### 出参（原始数据）

- **关键字段**：`attachment`（附件，见创建接口展开）、`relatedContent`（关联内容：product/coupon/promotion/page/contentMaterial 各为范围对象，product 含富化商品信息）、`scope`（适用范围，store 含富化名称）
- **枚举字段**：`publishStatus`（draft/published/unpublished）、`contentType`、`publishTimeType`（permanent/scheduled）
- **格式敏感字段**：`publishStartTime`/`publishEndTime`/`createdTime`（yyyy-MM-dd HH:mm:ss）、`favoriteCount`/`shareCount`（整数）

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-detail","input":{"id":"5400000000000000001"},"summary":"查看素材完整配置"}
```

---

## ✅ 素材数据统计汇总 — `ops.marketing.guide-material.content-stats`

- **说明**：返回单素材全生命周期的传播数据汇总（不分日期）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| totalFavoriteCount | 总收藏数 |
| totalShareCount | 总分享数 |
| totalViewCount | 客户总浏览次数 |
| totalOrderCount | 通过素材总下单数 |
| storeCoverage | 门店覆盖数 |

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-stats","input":{"id":"5400000000000000001"},"summary":"查看素材传播数据汇总"}
```

---

## ✅ 素材趋势统计 — `ops.marketing.guide-material.stats-trend`

- **说明**：按日聚合的柱状趋势数据；不带日期区间时返回全部。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |
| startDate | String | 否 | 开始日期，yyyy-MM-dd |
| endDate | String | 否 | 结束日期，yyyy-MM-dd |

### 出参（原始数据，数组）

- **格式敏感字段**：`date`（yyyy-MM-dd）、`favoriteCount`/`shareCount`/`viewCount`/`orderCount`（整数）

### 调用示例

```json
{"capability":"ops.marketing.guide-material.stats-trend","input":{"id":"5400000000000000001","startDate":"2026-08-01","endDate":"2026-08-31"},"summary":"查看素材8月按日传播趋势"}
```

---

## ✅ 素材门店明细 — `ops.marketing.guide-material.stats-store`

- **说明**：按门店聚合的传播明细分页（可加日期区间）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |
| startDate | String | 否 | 开始日期，yyyy-MM-dd |
| endDate | String | 否 | 结束日期，yyyy-MM-dd |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **关键字段**：`records[].storeId`（门店 ID）、`records[].storeName`（门店名）、`records[].guideCount`（分享导购数）及 favoriteCount/shareCount/viewCount/orderCount（整数统计）

### 调用示例

```json
{"capability":"ops.marketing.guide-material.stats-store","input":{"id":"5400000000000000001","startDate":"2026-08-01","endDate":"2026-08-31","pageNum":1,"pageSize":20},"summary":"查看素材8月各门店传播明细"}
```

---

## ✅ 分组树 — `ops.marketing.guide-material-group.tree`

- **说明**：返回最多两级的分组树（含各分组素材数量）；**bizType 必传**区分两套独立分组体系（content_material=内容素材 / speech=话术）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| bizType | String | 否 | content_material（内容素材分组，缺省按此统计）/speech（话术分组） |

### 出参（原始数据，树形数组）

- **路径参数来源**：`[].id`（→ 更新/删除分组 的 groupId、内容素材/话术 的 groupId 入参）
- **格式敏感字段**：`level`（1=一级/2=二级）、`sortOrder`（排序值整数）、`materialCount`（该分组下素材数量整数）
- **关键字段**：`parentId`（一级分组为 null）、`children`（子分组数组，递归同构）

### 调用示例

```json
{"capability":"ops.marketing.guide-material-group.tree","input":{"bizType":"content_material"},"summary":"查询内容素材分组树"}
```

---

## ✅ 导出素材复制记录 — `ops.marketing.guide.content-material.export-copy`

- **说明**：按筛选条件异步导出内容素材的**复制记录**（文案被导购复用的留痕数据）。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。筛选字段：keyword / groupId；导出为**非幂等操作**（重试创建重复任务）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | keyword / groupId（导出无分页参数，服务端固定分批拉取） |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.guide.content-material.export-copy","input":{},"summary":"导出双11素材的复制记录"}
```

---
