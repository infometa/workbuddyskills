---
name: report-render
description: ⭐ HTML 行程书生成 · 把上游所有 JSON（itinerary/transport/hotel/budget/risk）渲染成单文件 HTML，含 Leaflet 地图（每天分色路线）+ 时间轴 + POI 卡片 + 预算饼图 + 风险面板 + 行前清单。写到 output/，preview_url 打开。
version: 1.0.0
author:
tags: [travel, render, html, map, report, moat]
license: MIT
triggers:
  - 阶段 3 成稿，所有上游 skill 完成后
  - 用户说"出最终方案"、"给我行程书"
inputs:
  - name: itinerary
    type: object
    required: true
  - name: transport_plan
    type: object
    required: true
  - name: hotel_candidates
    type: array
    required: true
  - name: budget_breakdown
    type: object
    required: true
  - name: risk_report
    type: object
    required: true
outputs:
  - name: html_file
    type: file
    format: html
    path: output/{城市}-{出发日期}-行程书.html
---

# HTML 行程书生成（report-render）⭐

## 🔴 严禁手搓 HTML（最重要的铁律）

**触发本 skill 时，必须使用以下命令生成 HTML，不允许任何例外：**

```bash
python skills/report-render/scripts/render_html.py \
  --itinerary <path>/itinerary.json \
  --transport <path>/transport.json \
  --hotel <path>/hotel.json \
  --budget <path>/budget.json \
  --risk <path>/risk.json \
  --trip <path>/trip.json \
  --xhs-notes <path>/xhs_notes.json \
  --output output/<城市>-<出发日期>-行程书.html
```

**严禁的反模式（实测发现，绝对不可重演）：**
- ❌ 用 Write 工具直接写 HTML 字符串到 `output/xxx.html`
- ❌ 自己拼 `<html>...</html>` 绕过 templates/itinerary.html
- ❌ 觉得"模板太复杂我自己来更快" → 手搓的 HTML 会丢失：
  - Leaflet 地图（变成 `.map-placeholder` 占位 div）
  - 实际道路 polyline 路线
  - 8 大骨架 section（`<section>` 标签全无）
  - 📊 数据完整性面板
  - 📓 小红书参考笔记 section
  - Chart.js 预算饼图

**做法**：上游 6 个 skill 跑完后，把它们的 JSON 输出落到 `data/.cache/run-{id}/` 下，然后调上面的命令。如果某个 JSON 缺，先去补；脚本会自动跑骨架完整性体检并把警告输出到 stderr。

## 这是用户最终拿到手的东西

- 单文件 HTML，所有依赖内联或 CDN+SRI fallback
- 可分享、可打印、可离线看
- 自带 Leaflet 地图（每天分色路线）+ Chart.js 预算饼图
- 渲染由 Python + Jinja2 模板做

## 模块清单（按 HTML 从上到下顺序）

```
┌─ 封面卡（cover.html）──────────────────────
│  目的地 / 日期 / 同行人数 / 总预算 / 整体天气
│  数据生成时间戳
├─ 总览地图（map-overview.html）─────────────
│  Leaflet 1.9 + OSM 瓦片
│  - 所有 POI 标点（按天用不同颜色）
│  - 每天的路线 polyline
│  - 酒店标点（房子图标）
├─ 大交通（transport.html）─────────────────
│  去回程候选卡
│  含价格、时长、订票链接
├─ 住宿（hotel.html）───────────────────────
│  3-5 个酒店候选卡
│  位置评分 / 价位 / 真实评价摘要
├─ 每日行程（day-card.html × N）────────────
│  每天一张可折叠卡：
│  - 当天小地图（只显示当天 POI）
│  - 时间轴
│  - POI 卡（图/评分/营业/门票/排队/拍照机位/用时）
│  - 三餐推荐
│  - 当天预算 + 体力指数
├─ 预算明细（budget-chart.html）────────────
│  Chart.js 饼图 + 表格
│  含 vs 基准的健康度评估
├─ 风险面板（risk-panel.html）──────────────
│  天气 / 限行 / 节假日 / 骗局 / 应急
│  按置信度绿/黄/灰渲染
├─ 行前清单（checklist.html）───────────────
│  按 user_profile 微调过的清单
└─ 备选方案（backup.html）──────────────────
   下雨备选 / 体力不支备选 / 多出半天怎么填
```

## 技术栈

- **Jinja2** 模板引擎（Python 端）
- **Leaflet 1.9** 地图（CDN + SRI）
- **OSM 瓦片**（无需 key）
- **Chart.js 4.x** 预算饼图（CDN）
- **纯 CSS** 无框架，方便打印 + 不依赖网络

## 离线 + 分享友好

- 所有 CDN 都带 fallback 内联代码
- 打印样式（@media print）单独优化
- 不依赖任何后端，HTML 双击即可看

## 输出位置

```
output/
├── 成都-2026-04-15-行程书.html       主文件
└── assets/                           （可选，仅当不内联时）
    └── 2026-04-15-cover-image.jpg
```

文件命名约定：`{主目的地}-{出发日期}-行程书.html`

## 调用流程

```python
import subprocess
# 1. 先把 search-orchestrator 的 evidence 转成 xhs 笔记结构
subprocess.run([
    "python", "skills/report-render/scripts/build_xhs_notes.py",
    "--input", "data/.cache/run-xxx/candidates.json",
    "--output", "data/.cache/run-xxx/xhs_notes.json"
])
# 2. 渲染 HTML
subprocess.run([
    "python", "skills/report-render/scripts/render_html.py",
    "--itinerary", "data/.cache/run-xxx/itinerary.json",
    "--transport", "data/.cache/run-xxx/transport.json",
    "--hotel", "data/.cache/run-xxx/hotel.json",
    "--budget", "data/.cache/run-xxx/budget.json",
    "--risk", "data/.cache/run-xxx/risk.json",
    "--trip", "data/.cache/run-xxx/trip_request.json",
    "--xhs-notes", "data/.cache/run-xxx/xhs_notes.json",
    "--output", "output/成都-2026-04-15-行程书.html"
])
# 3. agent 接着调 preview_url 打开
```

## 数据置信度的视觉化

每个数据点旁渲染色块：
- 🟢 绿色徽章：实时一手数据
- 🟡 黄色徽章：抓取数据
- ⚪ 灰色徽章：静态参考，建议核实

封面顶部加一个"数据可信度面板"，整体说明本行程的数据来源构成：
> 🟢 73%（美团 + 小红书一手）
> 🟡 19%（WebSearch）
> ⚪ 8%（静态知识，建议出行前再核实）

## 反模式

- ❌ 把所有内容塞进聊天框（违反"聊天给摘要、详情进 HTML"原则）
- ❌ 依赖外部网络（必须有 fallback）
- ❌ 不分置信度（用户分不清哪些数据要再查）
- ❌ 过度装饰（实用 > 好看）
- ❌ 渲染失败时不报错（必须 exit 1，让 agent 降级到文本输出）

## 模板版本管理

`templates/itinerary.html` 是主模板，5 个 component 在 `templates/components/`。
新增字段时同时更新模板和 schema 文档（写到 README.md 的"模板字段"章节）。

---

_这个 skill 是用户体验的最后一公里。HTML 质量直接决定 agent 给人的"专业感"。_
