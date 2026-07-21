# 动态商品广告模版接口 (MPA/DPA)


**使用场景**：当广告组为 MPA/DPA 模式（`mpa_spec` 非空）且创意形式支持商品模版（`support_mpa_image_template` 或 `support_mpa_video_template` 为 true）时，素材组件通过商品模版生成图片/视频，而非直接上传。

---

## 1. 查询图片模版列表 (dynamic_ad_image_templates/get)

### 请求方式

`GET /v3.0/dynamic_ad_image_templates/get`

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |
| product_catalog_id | integer | 商品库ID（0-2147483647） |
| product_mode | enum | 广告类型: `SINGLE`（SDPA单品）或 `MULTIPLE`（MDPA多品） |
| dynamic_ad_template_width | integer | 模版宽度(px)，1-2000 |
| dynamic_ad_template_height | integer | 模版高度(px)，1-2000 |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dynamic_ad_template_ownership_type | enum | 模版归属: `ALL`(默认) / `SELF_OWNED` / `GRANTED` / `COMMON` / `PRODUCT_CATALOG_OWNED` |
| filtering | struct[] | 过滤条件（最多1个元素） |
| template_id_list | integer[] | 按模版ID过滤 |
| template_name | string | 按模版名称模糊搜索 |
| page | integer | 页码（默认1） |
| page_size | integer | 每页条数（默认10，最大100） |

### 响应核心字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| list[].dynamic_ad_template_id | integer | 模版ID |
| list[].dynamic_ad_template_name | string | 模版名称 |
| list[].dynamic_ad_template_width | integer | 模版宽度 |
| list[].dynamic_ad_template_height | integer | 模版高度 |
| list[].image_url | string | 模版预览图URL |
| list[].product_item_display_quantity | enum | 商品展示数量: `SINGLE` / `MULTIPLE` |
| page_info.total_number | integer | 总条数 |

---

## 2. 生成商品图片 (dynamic_ad_images/add)

### 请求方式

`POST /v3.0/dynamic_ad_images/add`

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |
| product_catalog_id | integer | 商品库ID |
| product_mode | enum | `SINGLE` 或 `MULTIPLE` |
| product_source | string | 商品来源ID（1-128字节）。MULTIPLE 模式为 product_series_id，SINGLE 模式为商品ID |
| dynamic_ad_template_id | integer | 图片模版ID（来自模版列表查询） |
| dynamic_ad_template_size | enum | 尺寸枚举，格式: `SIZE_{width}_{height}` |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| remove_template_id | boolean | SINGLE 模式下移除模版标记（默认 false） |
| image_matting_enabled | boolean | 启用商品抠图（默认 false） |

### dynamic_ad_template_size 枚举值

格式为 `SIZE_{宽度}_{高度}`，常用值:
- `SIZE_1280_720` (16:9 横版)
- `SIZE_720_1280` (9:16 竖版)
- `SIZE_800_800` (1:1 方形)
- `SIZE_480_320` (3:2)
- `SIZE_1080_1920`
- `SIZE_960_334`
- `SIZE_1280_1024`
- `SIZE_1024_1280`
- `SIZE_1280_960`
- `SIZE_960_1280`

### 响应

```json
{
  "code": 0,
  "data": {
    "image_id": "生成的图片ID"
  }
}
```

---

## 3. 查询视频模版列表 (dynamic_ad_video_templates/get)

### 请求方式

`GET /v3.0/dynamic_ad_video_templates/get`

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |
| product_catalog_id | integer | 商品库ID |
| adcreative_template_id | integer | 创意形式ID（来自 get-creative-templates 输出的 template_id） |
| product_mode | enum | `SINGLE` 或 `MULTIPLE`（当前仅支持 MULTIPLE） |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| support_channel | boolean | 是否筛选支持视频号版位的模版 |
| dynamic_ad_template_ownership_type | enum | 模版归属: `SELF_OWNED` / `PRODUCT_VIDEO_STRAIGHT_OUT` |
| template_id_list | integer[] | 按模版ID过滤 |
| template_name | string | 按模版名称模糊搜索 |
| page | integer | 页码（默认1） |
| page_size | integer | 每页条数（默认10，最大100） |

### 响应核心字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| list[].template_id | integer | 视频模版ID |
| list[].template_name | string | 模版名称 |
| list[].cover_image_url | string | 封面图URL |
| list[].intro_video_url | string | 介绍视频URL |
| list[].min_video_duration | integer | 最小视频时长(秒) |
| list[].max_video_duration | integer | 最大视频时长(秒) |
| list[].support_channel | boolean | 是否支持视频号版位 |
| page_info.total_number | integer | 总条数 |

---

## 4. 生成商品视频 (dynamic_ad_video/add)

### 请求方式

`POST /v3.0/dynamic_ad_video/add`

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |
| product_catalog_id | integer | 商品库ID |
| product_mode | enum | `SINGLE` 或 `MULTIPLE` |
| product_source | string | 商品来源ID。MULTIPLE 为 product_series_id，SINGLE 为商品ID |
| dynamic_ad_template_id | integer | 视频模版ID（来自模版列表查询） |

### 响应

```json
{
  "code": 0,
  "data": {
    "video_id": "生成的视频ID",
    "video_preview_image_url": "预览封面图URL",
    "video_preview_image_id": "预览封面图ID"
  }
}
```

---

## 参数来源速查

| 参数 | 来源 | 说明 |
|------|------|------|
| product_catalog_id | `mpa_spec.product_catalog_id`（优先）或 `marketing_asset_outer_spec.marketing_asset_outer_id` | 商品库ID |
| product_source | `mpa_spec.product_series_id`（优先）或 `marketing_asset_outer_spec.marketing_asset_outer_sub_id` | 商品系列/单品ID |
| product_mode | MPA广告组（mpa_spec非空）→ `MULTIPLE`；普通消费品推广广告 → `SINGLE` | 动态广告模式 |
| dynamic_ad_template_width/height | `get-creative-templates` 输出中 image 组件的 `valid.width` / `valid.height` | 图片尺寸要求 |
| dynamic_ad_template_size | `SIZE_{width}_{height}` 格式拼接 | 图片生成尺寸 |
| adcreative_template_id | `get-creative-templates` 输出的 `template_id` | 创意形式ID |
