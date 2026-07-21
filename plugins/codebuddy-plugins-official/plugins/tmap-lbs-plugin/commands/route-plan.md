---
description: "规划路线，支持步行、驾车、骑行、公交等出行方式"
argument-hint: "[起点 到 终点 出行方式]"
---

使用腾讯地图 Web 服务 API 进行路径规划。

## 使用说明

用户输入了以下路线规划请求：$1

请按照以下步骤执行：

1. 解析用户输入，提取起点、终点和出行方式
2. 如果用户输入的是地名（非坐标），先通过地理编码获取坐标
3. 根据出行方式选择对应的路线规划 API：
   - 步行 → walk_path
   - 驾车 → drive_path
   - 骑行 → cycle_path
   - 电动车 → ecycle_path
   - 公交 → bus_path
4. 返回格式化的路线规划结果，包含距离、时间和详细步骤

## 示例

- `/tmap-lbs-plugin:route-plan 从天安门到故宫步行` — 规划步行路线
- `/tmap-lbs-plugin:route-plan 北京南站到首都机场驾车` — 规划驾车路线
- `/tmap-lbs-plugin:route-plan 西直门到中关村公交` — 规划公交路线
