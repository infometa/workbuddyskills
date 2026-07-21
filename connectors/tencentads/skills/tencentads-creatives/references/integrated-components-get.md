# integrated_list_multiaccount/get — 组件模式查询

> 脚本：`scripts/get-integrated-components.mjs`
> 接口：`integrated_list_multiaccount/get`（POST）

按组件粒度查询账户下已有的素材组件，支持按报表指标排序、起量潜力/首发/低质/生成方式筛选。返回 `component_id` 可直接用于 `creative_components`。

---

## 参数

### 必填

| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | string \| number | 广告主 ID |
| `component_sub_types` | string[] | 组件子类型数组（见下方枚举） |

### 可选

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sort_field` | string | `"component.component_id"` | 排序字段（见下方枚举） |
| `sort_type` | string | `"DESCENDING"` | 排序方向 |
| `date_range` | object | 近 7 天 | 报表统计时间范围 |
| `fuzzy_name` | string | — | 模糊搜索组件名称 |
| `potential_status` | string[] | — | 起量潜力筛选（见下方枚举） |
| `first_publication_status` | string[] | — | 首发状态筛选（见下方枚举） |
| `quality_status` | string[] | — | 素材质量筛选（见下方枚举） |
| `generation_type` | string[] | — | 生成方式筛选（见下方枚举） |
| `page` | number | 1 | 页码 |
| `page_size` | number | 20 | 每页数量（最大 100） |
| `organization_id` | number | — | 业务单元 ID，传入后走业务单元维度查询 |

---

## 枚举值

### component_sub_types（组件子类型）

**图片类**：

| 值 | 说明 |
|----|------|
| `IMAGE_16X9` | 横版图片 16:9 |
| `IMAGE_9X16` | 竖版图片 9:16 |
| `IMAGE_1X1` | 方图 1:1 |
| `IMAGE_3X2` | 图片 3:2 |
| `IMAGE_2X3` | 图片 2:3 |
| `IMAGE_16X7` | 图片 16:7 |

**视频类**：

| 值 | 说明 |
|----|------|
| `VIDEO_16X9` | 横版视频 16:9 |
| `VIDEO_9X16` | 竖版视频 9:16 |
| `VIDEO_1X1` | 方形视频 1:1 |
| `VIDEO_3X2` | 视频 3:2 |
| `VIDEO_2X3` | 视频 2:3 |
| `SHORT_VIDEO_9X16` | 短视频 9:16 |
| `SHORT_VIDEO_16X9` | 短视频 16:9 |

**多图/组图类**：

| 值 | 说明 |
|----|------|
| `IMAGE_LIST_16X9` | 多图 16:9 |
| `IMAGE_LIST_1X1` | 多图 1:1 |
| `IMAGE_LIST_3X2` | 多图 3:2 |
| `IMAGE_LIST_16X9_1` | 多图中的单图 16:9 |
| `IMAGE_LIST_1X1_1` | 多图中的单图 1:1 |

**品牌类**：

| 值 | 说明 |
|----|------|
| `BRAND` | 普通品牌形象 |
| `BRAND_WECHAT_CHANNEL` | 视频号品牌形象 |

### sort_field（排序字段）

| 值 | 含义 |
|----|------|
| `component.component_id` | 按创建时间（默认） |
| `report.cost` | 按消耗 |
| `report.view_count` | 按曝光次数 |
| `report.order_roi` | 按下单ROI |
| `report.conversions_rate` | 按转化率 |
| `report.ctr` | 按点击率 |
| `report.conversions_cost` | 按浅层目标转化成本 |
| `report.effective_leads_count` | 按有效线索次数 |
| `report.effective_cost` | 按有效线索成本 |
| `report.effect_leads_purchase_count` | 按有效线索人数 |
| `report.effect_leads_purchase_cost` | 按有效线索成本（人数） |

### sort_type（排序方向）

| 值 | 含义 |
|----|------|
| `DESCENDING` | 降序（默认） |
| `ASCENDING` | 升序 |

### date_range（报表时间范围）

```json
{ "start_date": "2026-05-20", "end_date": "2026-05-26" }
```

不传时默认近 7 天。业务单元模式下最大跨度 15 天。

### potential_status（起量潜力）

| 值 | 含义 | 说明 |
|----|------|------|
| `COMMON_POTENTIAL_STATUS_HIGH` | 高潜 | 经系统预估跑量能力强，推荐使用 |
| `COMMON_POTENTIAL_STATUS_LOW` | 低潜 | 经系统快速探索，跑量效果低且预估不起量，建议不使用 |

适用组件类型：VIDEO / IMAGE / IMAGE_LIST

### first_publication_status（首发状态）

| 值 | 含义 | 说明 |
|----|------|------|
| `FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION` | 首发 | 平台内未出现过相似组件，会获得更多探索机会 |

适用组件类型：VIDEO / IMAGE / IMAGE_LIST

### quality_status（素材质量）

| 值 | 含义 | 说明 |
|----|------|------|
| `QUALITY_STATUS_LOW_QUALITY` | 低质 | 用户体验较差，不符合视频号媒体准入要求，平台会策略打压 |

### generation_type（生成方式）

| 值 | 含义 |
|----|------|
| `COMPONENT_GENERATION_TYPE_USER_CREATE` | 客户自建 |
| `COMPONENT_GENERATION_TYPE_SYSTEM_DERIVE` | 妙思衍生 |
| `COMPONENT_GENERATION_TYPE_ECOLOGICAL_PULL` | 生态拉取 |

适用组件类型：IMAGE_LIST（多图）

---

## 示例

### 基本查询（默认按时间倒序）

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["VIDEO_16X9","VIDEO_9X16"]}'
```

### 按消耗排序 + 指定时间范围

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["IMAGE_16X9"],"sort_field":"report.cost","sort_type":"DESCENDING","date_range":{"start_date":"2026-05-20","end_date":"2026-05-26"}}'
```

### 模糊搜索组件名称

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["VIDEO_16X9","VIDEO_9X16"],"fuzzy_name":"春节"}'
```

### 筛选高潜素材

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["VIDEO_9X16"],"potential_status":["COMMON_POTENTIAL_STATUS_HIGH"],"sort_field":"report.view_count"}'
```

### 筛选首发素材

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["IMAGE_16X9","IMAGE_9X16"],"first_publication_status":["FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION"]}'
```

### 排除低质素材（反向用法：查出低质的以便剔除）

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["VIDEO_9X16"],"quality_status":["QUALITY_STATUS_LOW_QUALITY"]}'
```

### 筛选妙思衍生的多图

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["IMAGE_LIST_16X9"],"generation_type":["COMPONENT_GENERATION_TYPE_SYSTEM_DERIVE"]}'
```

### 业务单元维度查询

```bash
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["VIDEO_16X9"],"organization_id":987654,"sort_field":"report.cost","date_range":{"start_date":"2026-05-20","end_date":"2026-05-26"}}'
```

---

## 输出格式

### 成功

```json
{
  "success": true,
  "list": [
    {
      "component_id": 1905866436402,
      "component_type": "VIDEO",
      "component_sub_type": "VIDEO_16X9",
      "component_sub_type_cn": "横版视频 16:9",
      "component_custom_name": "春节视频素材",
      "component_source_type_cn": "本地上传",
      "component_value": {
        "video": {
          "value": {
            "video_id": "14820035559",
            "cover_id": "6982654321"
          }
        }
      },
      "similarity_status": null,
      "potential_status": "COMMON_POTENTIAL_STATUS_HIGH",
      "first_publication_status": "FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION",
      "quality_status": null,
      "generation_type": "COMPONENT_GENERATION_TYPE_USER_CREATE",
      "cost": 15000,
      "view_count": 500000,
      "order_roi": 2.5,
      "conversions_rate": 0.032,
      "ctr": 0.048,
      "conversions_cost": 4500,
      "effective_leads_count": 120,
      "effective_cost": 125,
      "effect_leads_purchase_count": 80,
      "effect_leads_purchase_cost": 187
    }
  ],
  "page_info": {
    "page": 1,
    "page_size": 20,
    "total_number": 156,
    "total_page": 8
  }
}
```

### 失败

```json
{
  "success": false,
  "error": { "message": "查询组件列表失败: ..." }
}
```
