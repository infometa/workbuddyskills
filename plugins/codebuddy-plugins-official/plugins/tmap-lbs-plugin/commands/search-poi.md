---
description: "搜索地点（POI），支持关键词搜索、城市限定、周边搜索"
argument-hint: "[关键词 城市名]"
---

使用腾讯地图 Web 服务 API 进行 POI 地点搜索。

## 使用说明

用户输入了以下搜索请求：$1

请按照以下步骤执行：

1. 解析用户输入，提取搜索关键词、城市、位置等信息
2. 判断搜索场景：
   - 如果只有关键词和城市 → 使用关键词搜索（场景一）
   - 如果包含"周边"、"附近"等词 → 使用周边搜索（场景二）
3. 调用 tmap-lbs-skills skill 中的搜索功能
4. 返回格式化的搜索结果

## 示例

- `/tmap-lbs-plugin:search-poi 北京 肯德基` — 搜索北京的肯德基
- `/tmap-lbs-plugin:search-poi 西直门附近美食` — 搜索西直门周边美食
- `/tmap-lbs-plugin:search-poi 杭州西湖景点` — 搜索杭州西湖相关景点
