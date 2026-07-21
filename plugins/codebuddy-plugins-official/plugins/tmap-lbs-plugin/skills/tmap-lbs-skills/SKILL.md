---
name: tmap-lbs-skills
description: 腾讯地图位置服务，支持POI搜索、路径规划、旅游规划、周边搜索，轨迹数据可视化和地图数据可视化
---

# 腾讯地图位置服务 Skill

腾讯地图位置服务向开发者提供完整的地图数据服务，包括地点搜索、路径规划、旅游规划等功能。

## 功能特性

- 🔍 POI（地点）搜索功能
- 🏙️ 支持关键词搜索、城市限定、类型筛选
- 📍 支持周边搜索（基于坐标和半径）
- 🛣️ 路径规划（步行、驾车、骑行、公交）
- 🗺️ 智能旅游规划助手
- 📈 轨迹数据可视化展示
- 💾 配置本地持久化存储
- 🎯 自动管理腾讯地图 Web Service Key

## 首次配置

首次使用时需要配置腾讯地图 Web Service Key：

1. 访问 [腾讯位置服务](https://lbs.qq.com/dev/console/key/add) 创建应用并获取 Key
2. 设置环境变量：`export TMAP_WEBSERVICE_KEY=your_key`
3. 或运行时自动提示输入并保存到本地配置文件

当用户想要搜索地址、地点、周边信息（如美食、酒店、景点等）、规划路线时，使用此 skill。

## 触发条件

用户表达了以下意图之一：

- 搜索某类地点或某个确定地点（如"搜美食"、"找酒店"、"天安门在哪"）
- 基于某个位置搜索周边（如"西直门周边美食"、"北京南站附近酒店"）
- 规划路线（如"从天安门到故宫怎么走"、"规划驾车路线"）
- 旅游规划（如"帮我规划北京一日游"、"杭州西湖游览路线"）
- 包含"搜"、"找"、"查"、"附近"、"周边"、"路线"、"规划"等关键词
- 轨迹可视化（如"帮我生成轨迹图"、"上传轨迹数据"、"GPS 轨迹展示"）
- 设置或提供 API Key（如"我的 key 是 xxx"、"设置 key"、用户直接粘贴了一串 key 字符串）

## 场景判断

收到用户请求后，先判断属于哪个场景：

- **场景一**：用户搜索一个**明确的类别**（美食、酒店）或**确定的地点**（天安门、西湖），没有指定"在哪个位置附近"
- **场景二**：用户搜索**某个位置周边或者附近**的某类地点，输入中同时包含「位置」和「搜索类别或者 POI 类型」两个要素（如"西直门周边美食"、"北京南站附近酒店", "搜索亚洲金融大厦附近的奶茶店"）
- **场景三**：POI 详细搜索（使用 Web 服务 API）
- **场景四**：路径规划
- **场景五**：智能旅游规划
- **场景六**：设置 Web Service Key（用户提供了 API Key）
- **场景七**：轨迹可视化（用户提供了轨迹数据地址，想生成轨迹图）

---

## 场景一：明确关键词搜索

直接搜索一个类别或地点，不涉及特定位置的周边搜索。

> 📖 详细的 URL 格式、执行步骤、示例和回复模板请参考 [references/scene1-keyword-search.md](references/scene1-keyword-search.md)

---

## 场景二：基于位置的周边或者附近搜索

用户想搜索**某个位置周边或者附近**的某类地点。需要先通过地理编码 API 获取该位置的经纬度，再拼接带坐标的搜索链接。

**前置条件：** 需要用户提供腾讯位置服务的 API Key。

> 📖 匹配到此场景后，**必须先读取** `references/scene2-nearby-search.md` 获取详细的执行步骤、API 格式、完整示例和回复模板，严格按照文档中的步骤执行。

---

## 场景三：POI 详细搜索

使用腾讯地图 Web 服务 API 通过 shell curl 进行 POI 搜索，支持关键词搜索、城市限定、周边搜索等。

> 📖 详细的 curl 请求格式、参数说明和返回数据格式请参考 [references/scene3-poi-search.md](references/scene3-poi-search.md)

---

## 场景四：路径规划

使用腾讯地图 Web 服务 API 通过 shell curl 规划路线。支持步行、驾车、骑行（自行车）、电动车、公交等多种出行方式。

> 📖 详细的 curl 请求格式、各出行方式的 API 端点、参数说明和返回数据格式请参考 [references/scene4-route-planning.md](references/scene4-route-planning.md)

---

## 场景五：智能旅游规划

用户想去某个城市旅游，提供了多个想去的景点，需要规划最佳行程路线，并可选推荐餐厅、酒店等。需要先通过地理编码 API 获取各景点的经纬度，再拼接旅游规划链接。

**前置条件：** 需要用户提供腾讯位置服务的 API Key。

> 📖 匹配到此场景后，**必须先读取** `references/scene5-travel-planner.md` 获取详细的执行步骤、API 格式、完整示例和回复模板，严格按照文档中的步骤执行。

---

## 场景六：设置 Web Service Key

当用户在对话中提供了腾讯地图 Web Service Key 时，将 Key 保存到环境变量或本地配置文件。

> 📖 详细的触发条件、使用方法、执行步骤和回复模板请参考 [references/scene6-set-key.md](references/scene6-set-key.md)

---

## 场景七：地图数据可视化

当用户有一份包含轨迹坐标的数据，希望在地图上以轨迹图的形式可视化展示。不需要 API Key。

## 触发条件

用户提到"轨迹"、"轨迹图"、"轨迹可视化"、"GPS 轨迹"、"运动轨迹"、"行驶轨迹"等意图，并提供了数据地址或轨迹数据。

> 📖 匹配到此场景后，**必须先读取** `references/scene7-trail-map.md` 获取详细的 URL 格式、执行步骤、完整示例和回复模板，严格按照文档中的步骤执行。

---

## 配置管理

配置文件位于 `config.json`，包含以下内容：

```json
{
  "apiToken": "your_tmap_webservice_key_here"
}
```

设置 Key 的方式：

1. **环境变量**：`export TMAP_WEBSERVICE_KEY=your_key`
2. **手动编辑**：直接编辑 `config.json` 文件

---

## 注意事项

- **场景判断是关键**：区分用户是"直接搜某个东西"、"在某个位置附近搜某个东西"、"规划路线"还是"旅游规划"
- 关键词应尽量精简准确，提取用户真正想搜的内容
- URL 中的中文关键词浏览器会自动处理编码，无需手动 encode
- 场景二、三、四、五需要用户提供腾讯地图 API Key，**必须先获取 Key 后再发起请求**，不能跳过
- 如果 API 返回 `status` 不为 `0`，说明请求失败，需提示用户检查 Key 是否正确或地址是否有效
- 腾讯地图坐标格式为 `纬度,经度`（注意：纬度在前，经度在后），与高德相反
- 场景二的搜索范围默认 1000 米，用户如有需要可调整 `radius` 参数
- 请妥善保管你的 Web Service Key，不要分享给他人
- 腾讯地图 Web 服务 API 有调用频率限制，请合理使用
- 免费用户每日调用量有限制，具体请查看腾讯位置服务平台说明

## 文档引用（references）

各场景的详细操作文档存放在 `references/` 目录下：

| 文件                                                                       | 说明                                                           |
| -------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [references/scene1-keyword-search.md](references/scene1-keyword-search.md) | 场景一：明确关键词搜索 — URL 格式、执行步骤、示例、回复模板    |
| [references/scene2-nearby-search.md](references/scene2-nearby-search.md)   | 场景二：周边/附近搜索 — 执行步骤、API 格式、完整示例、回复模板 |
| [references/scene3-poi-search.md](references/scene3-poi-search.md)         | 场景三：POI 详细搜索 — curl 请求格式、参数说明、返回数据格式   |
| [references/scene4-route-planning.md](references/scene4-route-planning.md) | 场景四：路径规划 — curl 请求格式、API 端点、参数和返回数据说明 |
| [references/scene5-travel-planner.md](references/scene5-travel-planner.md) | 场景五：智能旅游规划 — 使用方法、功能说明                      |
| [references/scene6-set-key.md](references/scene6-set-key.md)               | 场景六：设置 Web Service Key — 触发条件、使用方法、回复模板    |
| [references/scene7-trail-map.md](references/scene7-trail-map.md)           | 场景七：轨迹可视化 — URL 格式、执行步骤、完整示例、回复模板    |

---

## 相关链接

- [腾讯位置服务](https://lbs.qq.com/)
- [创建应用和获取 Key](https://lbs.qq.com/dev/console/application/mine)
- [地点搜索 API 文档](https://lbs.qq.com/service/webService/webServiceGuide/webServiceSearch)
- [Web 服务 API 总览](https://lbs.qq.com/service/webService/webServiceGuide/webServiceOverview)
