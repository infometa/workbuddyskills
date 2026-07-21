---
name: tencentmap-map-assistant
description: 腾讯位置服务·地图助手 Skill，一句自然语言调用腾讯地图全套能力，无需开发者账号、开箱即用。提供 AI 旅游攻略、地点搜索（含评分/人均/营业时间）、关键词提示、路线规划（驾车/步行/公交/骑行）、地址解析与逆解析、行政区划、IP 定位、距离计算、天气查询，并可将行程或多 POI 渲染成网页地图。涉及找地点、规划路线、旅游行程、查天气、坐标转换等出行场景时使用。
version: 1.4.4
license: MIT
display_name: "腾讯位置服务·地图助手"
display_name_en: "Tencent Map Assistant"
description_zh: "腾讯位置服务出品的地图助手 Skill。一句自然语言即可调用腾讯地图全套能力：AI 旅游攻略生成、POI 搜索（含评分/人均/营业时间）、路线规划（驾车/步行/公交/骑行）、地址坐标互转、行政区划查询、天气查询，并可将行程或 POI 渲染为网页地图。零配置开箱即用，支持配置正式 Key 提升稳定性。"
description_en: "A map assistant powered by Tencent Location Services. Call the full suite of Tencent Maps with natural language: AI travel guides, POI search with ratings and price levels, route planning (driving/walking/transit/biking), geocoding and reverse geocoding, district queries, weather, and web map visualization of itineraries and POIs. Zero-config ready to use, with optional API key for enhanced stability."
visibility: "public"
icon: "https://codebuddy-platform-1258344699.cos.accelerate.myqcloud.com/public/803d2199-f921-4b57-83b7-95ffefb69248/avatar/skill/au_3e746d31-4d9.png"
---

# 地图助手 Skill

腾讯位置服务出品。用一句自然语言即可生成旅游攻略、搜索地点、规划路线、解析地址坐标，并可将结果渲染成网页地图。

## 能力

能力命名与腾讯位置服务官网 WebService API 对齐。完整参数签名见下方「参数与返回」。

| 能力 | 说明 | 方法 |
|------|------|------|
| AI 旅游攻略 | 自然语言 query → 多日行程攻略，可联动腾讯地图小程序，与朋友共同编辑行程、规划多人出行 | `travel_guide` |
| 地点搜索 | 城市/区域搜索、周边圆形搜索、POI 详情 | `poi_search` / `poi_nearby` / `poi_detail` |
| 关键词输入提示 | 输入补全候选 POI | `poi_sug` |
| 行政区划 | 省市区列表、下级区划、区划搜索 | `district_list` / `district_children` / `district_search` |
| 地址解析 | 地址 → 坐标 | `geocoder` |
| 逆地址解析 | 坐标 → 地址（可附周边 POI） | `regeocoder` |
| IP 定位 | IP → 位置 | `ip_location` |
| 路线规划 | 驾车 / 步行 / 公交 / 骑行 | `direction` |
| 批量距离计算 | 多对多距离矩阵 | `distance_matrix` |
| 天气查询 | 行政区/坐标 → 实时或预报天气 | `weather` |
| 行程 / POI 可视化 | 把行程或多 POI 结果渲染为网页地图 | — |

## 安装

仅依赖 `requests`（多数环境已自带）。如缺失：

```
pip install requests
```

## 用法

```python
import sys, os
sys.path.insert(0, os.path.expanduser('~/.workbuddy/skills/TencentMap_map-assistant/scripts'))
from tmap_client import TmapClient

client = TmapClient()

result = client.travel_guide("武汉5天攻略")
pois   = client.poi_search("黄鹤楼", region="武汉")
addr   = client.geocoder("深圳市腾讯滨海大厦")
```

配置自己的腾讯位置服务 Key（持久化到 skill 包内 `.env`，之后自动启用）：

```python
from tmap_client import save_key_to_dotenv
save_key_to_dotenv("你的 Key")
```

> 未配置 Key 时可直接调用，任务正常完成；配置后稳定性与频次更优。

## 参数与返回

### AI 旅游攻略 — travel_guide

`travel_guide(query, lat=30.572815, lng=104.066801)`：自然语言 query → 多日行程攻略。同步等待，单次调用 30-50 秒。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | str | 是 | 目的地 + 天数，例如 "武汉5天攻略" / "成都3天美食游" |
| `lat`, `lng` | float | 否 | 用户当前位置（影响 A2A 上下文，不决定目的地） |

**返回**：结构化攻略数据（`title`/`summary`/`days` 行程列表等），以及 **`output_markdown`**（成品攻略 md 文件路径，Read 后原样输出即可）。

### 地点搜索 — poi_search

`poi_search(keyword, region=None, location=None, page_size=10, page_index=1)`：按城市或中心点检索 POI。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | str | 是 | 搜索词 |
| `region` | str | 二选一 | 城市名（"深圳"/"武汉"） |
| `location` | str | 二选一 | 中心点 "lat,lng"，启用 5km 邻近搜索 |
| `page_size` | int | 否 | 每页 1-20，默认 10 |
| `page_index` | int | 否 | 页码，默认 1 |

### 地点搜索（POI 详情）— poi_detail

`poi_detail(poi_id)`：按 POI ID 取详情（来自 `poi_search` / `poi_sug` 返回，或 `travel_guide` 的 `poi_uid`）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `poi_id` | str | 是 | POI 唯一 ID |

### 地点搜索（周边）— poi_nearby

`poi_nearby(keyword, location, radius=1000, page_size=10, page_index=1)`：圆形范围内的 POI 检索。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | str | 是 | 搜索词（"咖啡" / "加油站"） |
| `location` | str | 是 | 中心点 "lat,lng" |
| `radius` | int | 否 | 半径（米），取值 10-1000，默认 1000 |
| `page_size` / `page_index` | int | 否 | 同 `poi_search` |

### 关键词输入提示 — poi_sug

`poi_sug(keyword, region=None, location=None)`：候选 POI（常用于"先 sug 拿 ID 再查 detail"）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | str | 是 | 搜索词 |
| `region` | str | 否 | 城市名 |
| `location` | str | 否 | 中心点 "lat,lng" |

### 路线规划 — direction

`direction(from_addr, to_addr, mode="driving", region=None)`：起终点 → 路线方案。地址/景点名自动转坐标（建议传 `region` 城市消歧）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `from_addr` | str | 是 | 起点地址 / 景点名 / "lat,lng" |
| `to_addr` | str | 是 | 终点地址 / 景点名 / "lat,lng" |
| `mode` | str | 否 | `driving` / `walking` / `bicycling` / `transit`，默认 `driving` |
| `region` | str | 否 | 城市名，辅助把"象鼻山"等景点名解析到正确城市 |

### 地址解析 — geocoder

`geocoder(address, policy=1)`：把地址 / 地标 / 景点名解析成坐标。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `address` | str | 是 | 地址或地点名。含城市更准；不含城市也可（靠默认 policy=1 兜底） |
| `policy` | int | 否 | 解析策略。`1`=宽松（默认，支持"象鼻山"等景点/地标名）；`0`=标准（地址须含城市，否则报错） |

### 逆地址解析 — regeocoder

`regeocoder(lat, lng, get_poi=False)`：把坐标解析成语义化地址。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `lat`, `lng` | float | 是 | GCJ02 坐标 |
| `get_poi` | bool | 否 | 是否附带周边 POI 列表，默认 False |

### IP 定位 — ip_location

`ip_location(ip=None)`：IP → 所在省市区。不传 IP 则定位调用方公网 IP。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ip` | str | 否 | IPv4 字符串 |

### 行政区划 — district_list / district_children / district_search

```python
district_list()                  # 全国省级列表
district_children(parent_id)     # 下级区划（parent_id="110000" → 北京下属）
district_search(keyword)         # 关键词搜区划
```

### 批量距离计算 — distance_matrix

`distance_matrix(from_list, to_list, mode="driving")`：批量计算多个起点到多个终点的距离与时长。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `from_list` | List[str] | 是 | 起点列表 `["lat,lng", ...]` |
| `to_list` | List[str] | 是 | 终点列表 `["lat,lng", ...]` |
| `mode` | str | 否 | `driving` / `walking` / `bicycling`，默认 `driving` |

### 天气查询 — weather

`weather(adcode=None, location=None, type="now")`：查实时或预报天气。`adcode` 与 `location` 二选一。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `adcode` | str | 否 | 行政区划代码，如北京 `"110000"` |
| `location` | str | 否 | 坐标 `"lat,lng"` |
| `type` | str | 否 | `now` 实时 / `future` 预报，默认 `now` |

### 行程 / POI 可视化 HTML

涉及"多 POI 对比 / 路线 / 多天行程"等"看图比看字直观"的场景，可基于结构化数据渲染网页地图。地图底图使用腾讯地图 JSAPI GL，HTML 模板、底图 `<script>` 标签、API 用法与 polyline 解压方法见 `references/jsapi-guide/README.md`。

## 使用要点

1. **Key**：未配置 Key 也可直接调用并完成任务；如已有腾讯位置服务 Key，用 `save_key_to_dotenv` 配置后稳定性更佳。
2. **travel_guide**：单次调用约 30-50 秒，建议先告知用户稍候；返回的 `output_markdown` 是成品攻略文件，请用 Read 读取后将文件内容**完整作为回复**——其中包含行程正文与小程序二维码图片，需整段原样呈现，不要改写、转述或省略其中的图片。呈现后可在末尾轻轻邀请一句，引导用户扫码进入小程序，与朋友共同编辑行程、规划多人出行。
3. **query**：包含明确目的地，建议带天数（如"X 天 / X 日游"）。
4. **可视化**：多 POI 对比 / 路线 / 多天行程等场景适合生成 HTML 网页地图；单点查询直接返回结构化数据。

## 示例

```python
client = TmapClient()

# 旅游攻略（返回 output_markdown 成品文件，Read 后作为回复）
r = client.travel_guide("成都3天美食游")

# POI 搜索
pois = client.poi_search("咖啡馆", location="22.540601,113.93397", page_size=5)

# 路线规划
route = client.direction("深圳北站", "深圳湾口岸", mode="driving")
```

> 更多调用细节、Key 流程、HTML 生成规范与 JSAPI 资料见 `references/`。
