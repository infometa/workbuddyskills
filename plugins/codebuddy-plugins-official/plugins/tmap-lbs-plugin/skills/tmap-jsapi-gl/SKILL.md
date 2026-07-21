---
name: tmap-jsapi-gl
description: 腾讯地图 JavaScript GL（JSAPIGL）开发指南。适用于地图应用或者工具的编写。在编写、审查或调试使用腾讯地图 API的代码时应运用此技能。适用于涉及地图初始化、覆盖物展示、图层控制、事件处理、控件交互、可视化渲染、地图工具、检索、路线规划、查地址、行政区划、ip定位、几何计算、三维模型展示、性能优化的任务。当用户提及 腾讯地图、 jsapi、jsapi-gl或相关地图开发需求时自动触发。
---

# TMap JSAPI GL Skill

帮助用户使用腾讯地图 JavaScript API GL 进行地图功能开发，包含基础地图功能和数据可视化功能。

## 目录结构

### API 文档

- **JS API 参考文档**: `references/jsapigl/docs/` (21 个 md 文件)

  - 概述.md - API 总览和索引
  - 地图.md - 地图核心类和配置
  - 点标记.md - 标注点相关 API
  - 矢量图形.md - 折线、多边形、圆形、矩形、椭圆形等矢量图形
  - 文本标记.md - 文本标注 API
  - DOM 覆盖物.md - 自定义 DOM 覆盖物
  - 信息窗体.md - 信息窗口 API
  - 点聚合.md - 点聚合功能
  - 控件.md - 地图控件
  - 自定义图层.md - 自定义栅格/矢量图层
  - 事件.md - 地图事件系统
  - 基础类.md - LatLng、Point 等基础类
  - 室内图.md - 室内地图功能
  - 附加库：地图工具.md - 几何编辑器、测量工具
  - 附加库：几何计算库.md - 距离、面积计算
  - 附加库：服务类库.md - 地点搜索、路线规划等
  - 附加库：地图视角附加库.md - 观察者视角
  - 附加库：模型库.md - GLTF/3DTiles 模型
  - 附加库：天气图层.md - 气象图层
  - 附加库：矢量数据图层.md - GeoJSON/MVT 图层
  - 环境检测.md - 浏览器环境检测

- **可视化参考文档**: `references/visualization/docs/` (15 个 md 文件)
  - 参考手册.md - 可视化 API 总览
  - 弧线图.md - 3D 弧线/流向图
  - 散点图.md - 3D 散点图
  - 热力图.md - 经典热力图
  - 蜂窝热力图.md - 蜂窝聚合热力图
  - 网格热力图.md - 网格聚合热力图
  - 轨迹图.md - 轨迹展示
  - 区域图.md - 区域轮廓图
  - 管道图.md - 3D 管道图
  - 辐射圈.md - 辐射圈效果
  - 围墙面.md - 围墙面效果
  - 水晶体.md - 3D 水晶体效果
  - 行政区划.md - 行政区划展示
  - 事件.md - 可视化事件系统
  - 基础类.md - 可视化基础类

### 示例代码

- **JS API Demos**: `references/jsapigl/demos/` (129 个 html 文件)

  - 按功能分类：地图操作、点标记、文本标记、点聚合、折线、多边形、控件、信息窗口、服务类、个性化地图、几何计算、模型库、应用工具、自定义覆盖物、城市漫游等

- **可视化 Demos**: `references/visualization/demos/` (44 个 html 文件)
  - 按图层类型分类：弧线图、散点图、热力图、轨迹图、蜂窝图、区域图、水晶体等

## 工作流程

### 1. 理解用户需求

当用户询问腾讯地图 API 相关问题时：

- 明确用户需要的功能类型（基础地图/可视化）
- 确定具体要使用的类或功能

### 2. 查询 API 文档

在 `references/jsapigl/docs/` 或 `references/visualization/docs/` 中查找相关 API 文档：

- 搜索关键词（如"点标记"、"热力图"）
- 阅读对应类的说明、配置参数、方法

### 3. 查找示例代码

在对应 demos 目录中查找示例：

- JS API 示例：`references/jsapigl/demos/`
- 可视化示例：`references/visualization/demos/`
- 示例命名格式：`功能分类_具体示例.html`

### 4. 提供解决方案

根据文档和示例，为用户提供：

- API 接口说明
- 代码示例
- 注意事项和最佳实践

## 使用示例

**用户问题**: "如何在地图上添加标记点？"

**执行流程**:

1. 读取 `references/jsapigl/docs/点标记.md` 了解 MultiMarker API
2. 查看 `references/jsapigl/demos/` 中的点标记相关示例
3. 提供完整的代码示例和说明

**用户问题**: "怎么画一个热力图？"

**执行流程**:

1. 读取 `references/visualization/docs/热力图.md` 了解 Heat API
2. 查看 `references/visualization/demos/` 中的热力图示例
3. 说明数据格式和配置选项

## 快速开始模板

基础地图初始化：

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>腾讯地图示例</title>
    <script src="https://map.qq.com/api/gljs?v=3&key=[YOUR_KEY]"></script>
    <!-- 如需可视化功能，添加: &libraries=visualization -->
  </head>
  <body>
    <div id="map" style="width:100%;height:500px;"></div>
    <script>
      var map = new TMap.Map('map', {
        zoom: 12,
        center: new TMap.LatLng(39.984104, 116.307503),
      });
    </script>
  </body>
</html>
```

可视化图层示例（热力图）：

```javascript
// 加载可视化库
// <script src="https://map.qq.com/api/gljs?v=1.beta&libraries=visualization&key=[YOUR_KEY]"></script>

var heat = new TMap.visualization.Heat({
  radius: 50,
  height: 100,
  gradientColor: {
    0: '#13B06A',
    0.4: '#13B06A',
    0.8: '#E9AB1D',
    0.9: '#E9AB1D',
    1: '#E05649',
  },
}).addTo(map);

heat.setData([
  { lat: 39.984104, lng: 116.307503, count: 100 },
  { lat: 39.984504, lng: 116.307803, count: 80 },
]);
```

## 注意事项

### JS API GL

1. **API Key**: 使用腾讯地图 API 需要申请 Key
2. **版本**: 当前为 GL 版本，支持 3D 地图和 WebGL 渲染
3. **浏览器兼容**: 现代浏览器，IE11+（需 polyfill）
4. **坐标系**: 使用 gcj02 坐标系
5. **地图创建（重要）**: 地图创建的容器一定要有固定宽高，尤其是 flex 布局下
6. **API 使用（重要）**: 所有功能的 API 调用都必须使用文档中出现的接口、属性、事件，不能自己编造；
7. **API 传参（重要）**: 所有的 API 传入参数必须严格遵守 api 文档中说明的格式，如果不确定就去看看对应 demo，包括 demo 中的数据格式；
8. **附加库的使用**: 使用附加库需要在 API 加载 URL 中添加 `libraries` 参数

| 附加库         | libraries 值    | 命名空间             | 说明                           |
| -------------- | --------------- | -------------------- | ------------------------------ |
| 地图工具       | `tools`         | `TMap.tools`         | 几何编辑器、测量工具           |
| 几何计算库     | `geometry`      | `TMap.geometry`      | 距离/面积计算、几何关系判断    |
| 服务类库       | `service`       | `TMap.service`       | 地点搜索、路线规划、行政区划等 |
| 地图视角附加库 | `view`          | `TMap` (扩展方法)    | 观察者视角操作地图             |
| 模型库         | `model`         | `TMap.model`         | GLTF/3DTiles/3DMarker 模型     |
| 天气图层       | `weather`       | `TMap.weather`       | 云图、温度图等气象图层         |
| 矢量数据图层   | `vector`        | `TMap.vector`        | GeoJSON/MVT 矢量数据图层       |
| 可视化库       | `visualization` | `TMap.visualization` | 可视化 API 的能力              |

**使用示例**：

```html
<!-- 加载多个附加库 -->
<script src="https://map.qq.com/api/gljs?v=1&libraries=tools,geometry,service,model&key=[YOUR_KEY]"></script>
```

### 可视化 API

1. **数据格式**: 可视化图层需要特定格式的数据输入
2. **性能**: 大数据量时注意性能优化
3. **层级**: 可视化图层可以设置显示层级
4. **事件**: 支持点击、悬停等交互事件
5. **API 使用（重要）**: 所有功能的 API 调用都必须使用文档中出现的接口、属性、事件，不能自己编造
6. **API 传参（重要）**: 所有的 API 传入参数必须严格遵守 api 文档中说明的格式，如果不确定就去看看对应 demo，包括 demo 中的数据格式；

## 最佳实践

1. **模块化加载**: 使用模块化方式按需加载 API
2. **错误处理**: 添加地图加载失败的处理逻辑
3. **内存管理**: 及时销毁不需要的图层和覆盖物
4. **性能优化**: 大数据集使用聚合或抽稀
