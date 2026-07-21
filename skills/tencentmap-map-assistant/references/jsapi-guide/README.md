# 腾讯地图 JSAPI GL 资料（内嵌）

> 本目录是腾讯地图 JS API GL 的完整开发资料，内嵌在本 skill 包里，
> 在需要为旅游攻略 / 多 POI / 路线出 HTML 可视化时直接查阅。
>
> HTML 地图底图使用腾讯地图 JSAPI GL。底图 `<script>` 标签见下方「API Key」段，直接照抄即可。

## 何时读这里

当需要把行程 / POI / 路线渲染成 HTML 地图时，按以下顺序查阅：

1. **底图 key 与 HTML 生成示例** → 下方「API Key」与「HTML 生成示例」段（照抄即可出图）
2. **画路线** → 下方「画路线：polyline 解压」段
3. **JSAPI 核心 API** → `jsapigl/docs/*.md`（下方有完整文件名清单）
4. **可视化扩展库** → `visualization/docs/*.md`（下方有完整文件名清单）
5. **demo 代码** → `*/demos/`

## jsapigl/docs/ 文件清单（21 个核心 API 文档）

| 文档 | 说明 / 何时读 |
|------|--------------|
| `概述.md` | API 总览，第一次接入先看 |
| `地图.md` | 地图初始化、移动、缩放等核心 API |
| `基础类.md` | LatLng / Point 等基础数据类型 |
| `点标记.md` | Marker（POI 标记必读） |
| `点聚合.md` | MarkerCluster（多 POI 聚合） |
| `信息窗体.md` | InfoWindow（POI 弹窗，旅游攻略必读） |
| `矢量图形.md` | Polyline / Polygon（路线连线必读） |
| `文本标记.md` | Label 文字标注 |
| `DOM覆盖物.md` | 自定义 HTML 覆盖物 |
| `事件.md` | 地图/marker 事件处理 |
| `控件.md` | 缩放/比例尺等内置控件 |
| `室内图.md` | 室内地图 |
| `自定义图层.md` | 自定义图层 |
| `环境检测.md` | 浏览器/WebGL 支持检测 |
| `附加库：几何计算库.md` | geometry 库（距离/面积计算） |
| `附加库：地图工具.md` | tools 库（标尺/绘图工具） |
| `附加库：地图视角附加库.md` | view 库（视角控制） |
| `附加库：天气图层.md` | weather 图层 |
| `附加库：服务类库.md` | service 库（地理编码等） |
| `附加库：模型库.md` | model 库（3D GLTF/3DTiles） |
| `附加库：矢量数据图层.md` | vector 库（GeoJSON/MVT） |

## visualization/docs/ 文件清单（15 个可视化扩展）

| 文档 | 说明 / 何时读 |
|------|--------------|
| `参考手册.md` | 可视化扩展库总览 |
| `基础类.md` | 通用基础类 |
| `事件.md` | 可视化层事件 |
| `散点图.md` | 散点图（旅游 POI 可用） |
| `热力图.md` | 热力图 |
| `网格热力图.md` | 网格化热力图 |
| `蜂窝热力图.md` | 六边形热力图 |
| `辐射圈.md` | 辐射圈（POI 影响范围） |
| `弧线图.md` | 弧线（跨城路线视觉化好） |
| `轨迹图.md` | 轨迹动画（旅游路线播放） |
| `管道图.md` | 管道连线 |
| `区域图.md` | 多边形区域 |
| `围墙面.md` | 立体围墙 |
| `水晶体.md` | 立体水晶 |
| `行政区划.md` | 省市区边界 |

## 目录结构

```
jsapi-guide/
├── README.md            本文档
├── jsapigl/
│   ├── docs/            核心 API 文档（上方 21 个 md）
│   └── demos/           核心 API 的 demo HTML
└── visualization/
    ├── docs/            可视化扩展库文档（上方 15 个 md）
    └── demos/           可视化扩展库的 demo HTML
```

## API Key

HTML 地图底图直接用下面这行 `<script>`（URL 与 key 照抄，不要改动、不要自己编 key）：

```html
<script src="https://map.qq.com/api/gljs?v=1&key=OB4BZ-D4W3U-B7VVO-4PJWW-6TKDJ-WPB77"></script>
```

这是腾讯地图公开的 JSAPI GL 加载 key，放进 HTML `<head>` 即可显示底图。使用者若已配置自己的 key，可替换为自己的。

## HTML 生成示例

地图能力使用 `TMap.Map` + `TMap.MultiMarker` + `TMap.MultiPolyline` + `TMap.InfoWindow`。把 POI 数据换成 client 返回的真实坐标即可：

```python
import os, json

# POI 数据（实际用 client 返回的坐标）
pois = [
    {"name": "象鼻山", "lat": 25.2675, "lng": 110.2966},
    {"name": "两江四湖", "lat": 25.2798, "lng": 110.2904},
    {"name": "靖江王府", "lat": 25.2858, "lng": 110.2992},
]
markers_js = json.dumps(
    [{"id": str(i), "position": [p["lat"], p["lng"]], "title": p["name"]} for i, p in enumerate(pois)],
    ensure_ascii=False,
)

html = f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body,#map{{height:100%;margin:0}}</style>
<script src="https://map.qq.com/api/gljs?v=1&key=OB4BZ-D4W3U-B7VVO-4PJWW-6TKDJ-WPB77"></script>
</head><body><div id="map"></div><script>
const pts = {markers_js};
const map = new TMap.Map('map', {{
  center: new TMap.LatLng(pts[0].position[0], pts[0].position[1]), zoom: 12
}});
new TMap.MultiMarker({{ map, geometries: pts.map(p => ({{
  id: p.id, position: new TMap.LatLng(p.position[0], p.position[1]), properties: {{title: p.title}}
}})) }});
new TMap.MultiPolyline({{ map, geometries: [{{
  id: 'route', paths: pts.map(p => new TMap.LatLng(p.position[0], p.position[1]))
}}] }});
</script></body></html>'''

out = os.path.expanduser("~/Documents/itinerary_map.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(out)
```

旅游攻略类 HTML 还可把 `travel_guide` 返回的 `qr_path` 嵌入网页右下角浮窗（约 120×120）；POI 按天分色 + 数字角标 + polyline 连线。

## 画路线：polyline 解压

`direction` 返回腾讯路线接口原生响应（`result.routes`）。驾车/步行/骑行的 `routes[0].polyline` 是**压缩格式的一维数组**，画线前需解压成 `[lat,lng]` 点序列：前两个值是首点真实经纬度，其后每个值是相对前一点的差值（×1e6），逐项累加还原。

```python
def decode_polyline(coors):
    """腾讯压缩 polyline 一维数组 → [[lat,lng], ...]"""
    if not coors or len(coors) < 2:
        return []
    pts = [[coors[0], coors[1]]]
    for i in range(2, len(coors) - 1, 2):
        lat = pts[-1][0] + coors[i] / 1_000_000.0
        lng = pts[-1][1] + coors[i + 1] / 1_000_000.0
        pts.append([round(lat, 6), round(lng, 6)])
    return pts
```

解压后转成 `new TMap.LatLng(lat, lng)` 数组喂给 `MultiPolyline` 的 `paths`。

> 公交 `transit` 的 route 没有顶层 polyline，折线分散在 `steps` 各换乘段里（步行段的 `polyline` 字段、乘车段 `lines[0].polyline`），按需分别解压。
