# 地图与 3D 主题指南

## 地图资源

地图库不再打包进 skill。优先从仓库根 `assets/maps/` 或远端 `weponusa/teachany/main/assets/maps` 按需读取。

```bash
python3 "$TEACHANY_SKILL/scripts/find-map.py" 唐
python3 scripts/find-map.py --era 1500
python3 scripts/find-map.py --base hillshade
python3 scripts/find-map.py --copy <file> <course-dir>/assets/maps/
```

## 历史/地理地图

- 使用 TeachAny 标准历史地图模块，不手写 Leaflet/ECharts/SVG 地图。
- `hillshade.jpg` bounds 固定为 `[[-90,-180],[90,180]]`，再 `fitBounds` 到教学区域。
- 地理课件需要标注投影类型和面积变形提示。

## 3D / Terrain

- 3D 不是所有课件必需项；只有二维无法表达空间关系时才启用 3D。
- 3D 组件必须有明确学习任务、可调参数和反馈，不做装饰。

## PPTX

TeachAny 默认交付互动 HTML。仅用户明确要求 PPTX 时，才从 HTML 派生展示版讲义；PPTX 不替代互动课件。
