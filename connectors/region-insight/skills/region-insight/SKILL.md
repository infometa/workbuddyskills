---
name: region-insight
description: "区域洞察 — POI 检索与围栏分析"
description_zh: "区域洞察 — POI 检索与围栏分析"
description_en: "Region Insight — POI Search and Fence Analysis"
version: "1.0.0"
tools:
  - post_region_insight_poi_location
  - post_region_insight_fence_poi_overview
  - post_region_insight_fence_poi_list
---

# 区域洞察

区域洞察用于定位 POI，并对指定圆形区域内的 POI 进行分析。所有坐标均使用 GCJ02。

## 调用流程

1. 用户只提供地点名称、商圈或地址时，先调用 `post_region_insight_poi_location` 获取候选 POI 和 GCJ02 坐标。
2. 用户需要 POI 数量、分类或品牌分布时，调用 `post_region_insight_fence_poi_overview`。
3. 用户需要具体 POI 明细时，调用 `post_region_insight_fence_poi_list`。

不得将其他坐标系直接当作 GCJ02 使用。地点搜索返回多个候选项且无法确定目标时，应先让用户确认。

## POI 定位

工具：`post_region_insight_poi_location`

- `keyword` 必填。
- 可用 `province_name`、`city_name`、`district_name` 缩小范围。
- `page` 从 1 开始，`page_size` 最大为 50。
- 可按 `brand_name` 或 `category_id` 进一步过滤。
- 返回 `data.count` 和候选项 `data.list`；每个候选项包含 POI ID、名称、地址、行政区划及
  `gcj02_longitude`、`gcj02_latitude`。

## 围栏内 POI 概览

工具：`post_region_insight_fence_poi_overview`

- `circle_fences` 必填，每个围栏包含 `gcj02_longitude`、`gcj02_latitude` 和 `radius`。
- 半径范围为 1 至 5000 米。
- `category_ids` 和 `brand_names` 均最多传入 100 项。
- `group_by_fields` 仅支持 `category_id`、`brand_id`；未指定时按分类聚合。
- `bucket_size` 范围为 1 至 10000。
- 返回 `data.total_hits` 和 `data.buckets`；聚合桶包含分组键、POI 数量及可能存在的子聚合桶。

## 围栏内 POI 列表

工具：`post_region_insight_fence_poi_list`

- 围栏和过滤参数规则与 POI 概览一致。
- 接口不分页，最多返回 10000 条 POI。
- 数据量较大时，优先建议用户增加分类或品牌过滤条件。
- 返回 `data.count` 和 `data.list`；POI 明细包含名称、地址、分类、品牌和 GCJ02 空间信息。
- 服务端接口契约固定：响应中的 `data.list[].coordinate` 表示 GCJ02 点坐标，
  `data.list[].fence_gcj02` 表示 GCJ02 围栏。不得要求服务端修改既有字段。
- 向用户说明、生成结构化结果或传递给后续工具时，必须将 `coordinate` 明确表述为
  `gcj02_coordinates`；不得原样暴露或继续使用含义不明确的 `coordinate` 字段名。

## 鉴权和错误处理

- WorkBuddy 使用用户配置的 `REGION_INSIGHT_API_KEY` 发起 Bearer Token 鉴权。
- HTTP 401：提示用户前往 `https://data.isjike.com/console/keys` 重新生成 API Key，并在
  Connector 设置中替换旧值；不得要求用户在对话中发送 Key。
- HTTP 429：提示调用频率超限，稍后重试。
- 服务端错误或超时：说明查询未完成，可在避免重复并发调用的前提下重试一次。
- 本 Connector 的工具均为只读查询，不会修改或删除业务数据。

## English Guide

- Use `post_region_insight_poi_location` to resolve a place name to candidate POIs and GCJ-02 coordinates.
- Use `post_region_insight_fence_poi_overview` for POI counts and category or brand distributions.
- Use `post_region_insight_fence_poi_list` when individual POI records are required.
- Accept and pass only confirmed GCJ-02 coordinates using explicit `gcj02_*` field names.
- Never ask the user to paste an API Key into the conversation. For HTTP 401, direct the user to
  `https://data.isjike.com/console/keys` and the Connector settings.
- All tools are read-only. Retry a server error or timeout at most once without creating concurrent duplicates.
