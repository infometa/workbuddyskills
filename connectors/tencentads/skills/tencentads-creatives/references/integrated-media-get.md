# integrated_image_list/get & integrated_media_list/get — 素材库模式查询

> 脚本：`scripts/get-integrated-media.mjs`
> 接口：
> - 图片：`integrated_image_list/get`（POST）
> - 视频：`integrated_media_list/get`（POST）

按素材粒度查询单图/视频素材库，支持可用性过滤（比例/宽高/时长）、报表排序、多种筛选条件。返回 `image_id` / `video_id`，需通过 `value` 内联方式传入 `creative_components`。

---

## 参数

### 必填

| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | string \| number | 广告主 ID |
| `type` | string | 素材类型：`IMAGE` 或 `VIDEO` |

### 可选

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sort` | string | `"created_time"` | 排序字段（见下方枚举） |
| `sort_type` | string | `"DESCENDING"` | 排序方向 |
| `date_range` | object | 近 7 天 | 报表统计时间范围 `{ start_date, end_date }` |
| `create_range` | object | — | 素材创建时间范围 `{ start_date, end_date }`（YYYY-MM-DD） |
| `ratios` | string[] | — | 可用比例过滤，需配合 `ratio_valids` |
| `ratio_valids` | object[] | — | 每个比例的规格约束（见下方结构） |
| `fuzzy_name` | string | — | 模糊搜索素材名称/描述 |
| `label_id` | string | — | 内容标签 ID |
| `similarity_status` | string[] | — | 相似度状态筛选 |
| `quality_status` | string[] | — | 素材质量筛选 |
| `first_publication_status` | string[] | — | 首发状态筛选 |
| `generation_type` | string[] | — | 生成方式筛选 |
| `duration` | string | — | 视频时长筛选（仅 VIDEO），如 `"0-15"` / `"16-30"` / `"61"` |
| `watermark` | string | — | 水印筛选：`"true"` / `"false"` |
| `page` | number | 1 | 页码 |
| `page_size` | number | 20 | 每页数量（最大 100） |
| `organization_id` | number | — | 业务单元 ID |

---

## 枚举值

### sort（排序字段）

| 值 | 含义 |
|----|------|
| `created_time` | 按创建时间（默认） |
| `cost` | 按消耗 |
| `view_count` | 按曝光次数 |
| `order_roi` | 按下单ROI |
| `conversions_rate` | 按转化率 |
| `ctr` | 按点击率 |
| `conversions_cost` | 按浅层目标转化成本 |
| `effective_leads_count` | 按有效线索次数 |
| `effective_cost` | 按有效线索成本 |
| `effect_leads_purchase_count` | 按有效线索人数 |
| `effect_leads_purchase_cost` | 按有效线索成本（人数） |

### sort_type（排序方向）

| 值 | 含义 |
|----|------|
| `DESCENDING` | 降序（默认） |
| `ASCENDING` | 升序 |

### similarity_status（相似度状态）

| 值 | 含义 |
|----|------|
| `SIMILARITY_STATUS_APPROVED` | 通过 |
| `SIMILARITY_STATUS_PENDING` | 检测中 |
| `SIMILARITY_STATUS_REJECTED` | 不通过 |

### quality_status（素材质量）

| 值 | 含义 | 说明 |
|----|------|------|
| `QUALITY_STATUS_LOW_QUALITY` | 低质 | 用户体验较差，不符合视频号媒体准入要求，平台会策略打压 |

### first_publication_status（首发状态）

| 值 | 含义 | 说明 |
|----|------|------|
| `FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION` | 首发 | 平台内未出现过相似素材，会获得更多探索机会 |

### generation_type（生成方式）

生成方式的枚举值是动态的（通过 `image_source_list/get` 或 `media_source_list/get` 获取），常见值：

| 值 | 含义 |
|----|------|
| `SOURCE_TYPE_LOCAL` | 本地上传 |
| `SOURCE_TYPE_MUSE` | 妙思生成 |
| `SOURCE_TYPE_DERIVE` | 系统衍生 |
| `SOURCE_TYPE_ECOLOGICAL_PULL` | 生态拉取 |

> 注意：素材模式的 `generation_type` 枚举值与组件模式不同（组件模式用 `COMPONENT_GENERATION_TYPE_*`）。

### duration（视频时长筛选，仅 VIDEO）

| 值 | 含义 |
|----|------|
| `"0-15"` | 0~15 秒 |
| `"16-30"` | 16~30 秒 |
| `"31-45"` | 31~45 秒 |
| `"46-60"` | 46~60 秒 |
| `"61"` | 60 秒以上 |

### watermark（水印）

| 值 | 含义 |
|----|------|
| `"true"` | 已添加水印 |
| `"false"` | 未添加水印 |

---

## ratio_valids 结构

`ratio_valids` 是一个数组，每个元素描述一种可接受的素材规格：

```json
{
  "ratio": "16:9",
  "file_size_kb_limit": 102400,
  "min_width": 1280,
  "min_height": 720,
  "min_duration": 6,
  "max_duration": 900
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ratio` | string | 比例（如 `"16:9"`、`"9:16"`、`"1:1"`） |
| `file_size_kb_limit` | number | 文件大小上限（KB） |
| `min_width` | number | 最小宽度（px），与 `min_height` 配合用 `GREATER_EQUALS` |
| `min_height` | number | 最小高度（px） |
| `width` | number | 精确宽度（px），与 `height` 配合用 `EQUALS`，优先级低于 min_width |
| `height` | number | 精确高度（px） |
| `min_duration` | number | 最小时长（秒，仅 VIDEO） |
| `max_duration` | number | 最大时长（秒，仅 VIDEO） |

当传入 `ratios` + `ratio_valids` 时，脚本会构造 `or_filtering`，只返回满足任一规格约束的素材。

---

## 示例

### 基本查询（按创建时间倒序）

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"VIDEO"}'
```

### 按消耗排序

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"IMAGE","sort":"cost","sort_type":"DESCENDING","date_range":{"start_date":"2026-05-20","end_date":"2026-05-26"}}'
```

### 模糊搜索素材名称

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"IMAGE","fuzzy_name":"产品主图"}'
```

### 可用性过滤（指定比例+宽高+时长）

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"VIDEO","ratios":["16:9"],"ratio_valids":[{"ratio":"16:9","file_size_kb_limit":102400,"min_width":1280,"min_height":720,"min_duration":6,"max_duration":900}]}'
```

### 多个比例的可用性过滤

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"VIDEO","ratios":["16:9","9:16"],"ratio_valids":[{"ratio":"16:9","file_size_kb_limit":102400,"min_width":1280,"min_height":720,"min_duration":6,"max_duration":900},{"ratio":"9:16","file_size_kb_limit":102400,"min_width":720,"min_height":1280,"min_duration":6,"max_duration":900}]}'
```

### 按创建时间范围过滤

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"IMAGE","create_range":{"start_date":"2026-05-01","end_date":"2026-05-26"}}'
```

### 筛选首发素材

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"VIDEO","first_publication_status":["FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION"]}'
```

### 筛选相似度通过的素材

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"IMAGE","similarity_status":["SIMILARITY_STATUS_APPROVED"]}'
```

### 按视频时长过滤（16~30 秒）

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"VIDEO","duration":"16-30"}'
```

### 按标签过滤

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"IMAGE","label_id":"88776655"}'
```

### 组合筛选（首发 + 按曝光排序 + 16:9 可用）

```bash
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"VIDEO","first_publication_status":["FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION"],"sort":"view_count","ratios":["16:9"],"ratio_valids":[{"ratio":"16:9","file_size_kb_limit":102400,"min_width":1280,"min_height":720,"min_duration":6,"max_duration":900}]}'
```

---

## 输出格式

### 成功（图片）

```json
{
  "success": true,
  "list": [
    {
      "image_id": "14820035559",
      "width": 1280,
      "height": 720,
      "ratio": "16:9",
      "file_size_kb": 320,
      "preview_url": "https://...",
      "description": "产品主图",
      "signature": "a1b2c3d4...",
      "similarity_status": "SIMILARITY_STATUS_APPROVED",
      "quality_status": null,
      "first_publication_status": "FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION",
      "generation_type": "SOURCE_TYPE_LOCAL",
      "created_time": 1716700000,
      "cost": 2000,
      "view_count": 80000,
      "order_roi": 3.2,
      "conversions_rate": 0.04,
      "ctr": 0.06,
      "conversions_cost": 50
    }
  ],
  "page_info": { "page": 1, "page_size": 20, "total_number": 89, "total_page": 5 }
}
```

### 成功（视频）

```json
{
  "success": true,
  "list": [
    {
      "video_id": "987654321",
      "width": 1080,
      "height": 1920,
      "ratio": "9:16",
      "file_size_kb": 15360,
      "duration_ms": 15000,
      "preview_url": "https://...",
      "description": "春节促销视频",
      "system_status": "MEDIA_STATUS_VALID",
      "similarity_status": "SIMILARITY_STATUS_APPROVED",
      "quality_status": null,
      "first_publication_status": null,
      "generation_type": "SOURCE_TYPE_MUSE",
      "created_time": 1716700000,
      "cost": 5000,
      "view_count": 200000,
      "order_roi": 2.8,
      "conversions_rate": 0.035,
      "ctr": 0.055,
      "conversions_cost": 143
    }
  ],
  "page_info": { "page": 1, "page_size": 20, "total_number": 42, "total_page": 3 }
}
```

### 失败

```json
{
  "success": false,
  "error": { "message": "查询素材列表失败: ..." }
}
```
