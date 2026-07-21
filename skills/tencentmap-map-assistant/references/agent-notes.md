# 调用指引（供 AI 阅读）

本文件补充 SKILL.md 未展开的调用细节，帮助 AI 稳定完成任务。

## 能力命中本 skill 时，用 client 完成

用户需求涉及旅游攻略、找地点、路线规划、地址坐标转换、行政区划、距离计算等，均通过 `TmapClient` 完成，返回的是腾讯位置服务真实数据。

- client 仅依赖 `requests`，多数环境已自带，可直接调用；仅当报 `ModuleNotFoundError: requests` 时执行 `pip install requests` 后重试。
- 调用报错时，读返回的报错信息（key / 网络 / 参数）定位，对应调整后重试。

## Key 策略：默认体验通道，按需配置正式 Key

每个使用者的腾讯位置服务额度独立。

- **默认直接调用**：未配置 Key 时 client 自动走体验通道，结果照常返回，无需在调用前询问。
- **配置正式 Key**：使用者提供 Key 时，用 `save_key_to_dotenv("Key")` 持久化到 skill 包内 `.env`，重新初始化 client 后自动走正式通道。

```python
from tmap_client import TmapClient, save_key_to_dotenv
c = TmapClient()                 # 未配 Key → 体验通道；已配 → 正式通道
# save_key_to_dotenv("XXX-...")  # 使用者提供 Key 时调用
```

体验通道完成任务后，可在回复末尾轻提一句：如已有正式 Key 可配置，后续走正式通道，稳定性与频次更优。已配正式 Key 时无需提示。

## 返回结构：对齐腾讯位置服务官方

所有 WebService 能力（搜索、提示、详情、地址解析、区划、IP、距离矩阵、路线规划）均返回**腾讯位置服务官方原生响应**，结构与官网文档一致。调用后读取实际返回即可，无需预设字段名。

> 行政区划三个方法（`district_list` / `district_children` / `district_search`）的 `result` 是**二维数组**——`result[0]` 才是区划对象列表（官方分组设计），读取时注意取 `result[0]` 而非 `result`。

路线规划 `direction` 仅在调用前自动把起终点的地址/景点名转成坐标，返回的是路线接口原生响应（`result.routes`）。其中驾车/步行/骑行的 `polyline` 为压缩格式，画线前需解压（解压方法见 `jsapi-guide/README.md`）。

## travel_guide 的回复方式

`travel_guide` 返回的 `output_markdown` 是成品攻略文件（含行程正文与小程序入口二维码图片）。

**必须做的事（缺一不可）：**

1. 用 Read 读取 `result["output_markdown"]`，将文件内容**完整作为回复**——包含末尾的 `![腾讯地图小程序入口图](...)` 图片语法。WorkBuddy 会话渲染器**支持** markdown 图片语法内联显示，图片会直接展示在对话中。
2. **同时**把二维码 PNG 文件复制到当前工作区，调用 `deliver_attachments` 作为产物交付（确保小程序端也能看到）。

文件末尾结构示例：

```markdown
---
![腾讯地图小程序入口图](/path/to/qrcodes/travel_guide_xxx.png)

👆 扫码进入腾讯地图小程序，可联动小程序继续完善攻略、与朋友共同编辑行程、规划多人出行。
```

> ⚠️ Markdown 图片语法 `![...](...)` 可在 WorkBuddy 会话中内联渲染，请务必通过此方式展示二维码图片，而非仅提供文件路径。

## 网页生成（HTML 地图可视化）

涉及"多 POI 对比 / 路线 / 多天行程"等"看图比看字更直观"的场景，可基于结构化数据生成 HTML 网页地图。底图 key、HTML 生成示例、polyline 解压方法、各类 API 与 demo 全部见 `references/jsapi-guide/README.md`，照其中模板生成即可。

## 体验通道技术细节（client 已封装，正常调用无需关心）

未配置正式 Key 时，client 自动走体验通道：

- **后端服务**：域名走 `https://h5gw.map.qq.com`，`key=none`，按接口附带 `apptag`，返回 JSONP（client 自动解包，调用方拿到的是解析好的 dict）。
- **前端地图**：JSAPI GL 底图用公开加载 key（见 `jsapi-guide/README.md` 的 `<script>` 模板），与后端通道无关。
- 体验通道频次与稳定性受限，常规使用建议配置正式 Key。

各接口 `apptag` 对照（client 内置，仅供排查参考）：

| 接口路径 | apptag |
|---------|--------|
| `/ws/place/v1/search` | `h5mutipos_place_search` |
| `/ws/place/v1/suggestion` | `lbsplace_sug` |
| `/ws/place/v1/detail` | `lbsplace_detail` |
| `/ws/geocoder/v1` | `lbs_geocoder` |
| `/ws/location/v1/ip` | `lbslocation_ip` |
| `/ws/district/v1/list` | `lbsdistrict_list` |
| `/ws/district/v1/getchildren` | `lbsdistrict_getchildren` |
| `/ws/district/v1/search` | `lbsdistrict_search` |
| `/ws/direction/v1/driving` | `lbsdirection_driving` |
| `/ws/direction/v1/transit` | `lbsdirection_transit` |
| `/ws/direction/v1/walking` | `lbsdirection_walking` |
| `/ws/direction/v1/bicycling` | `lbsdirection_bicycling` |
| `/ws/distance/v1/matrix` | `lbsdistance_matrix` |
