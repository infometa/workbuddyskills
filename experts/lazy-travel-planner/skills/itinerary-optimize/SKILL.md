---
name: itinerary-optimize
description: ⭐ 行程运筹核心壁垒 · 把 Top N POI 池转成"地理顺路 + 体力分配 + 时间窗匹配"的可执行行程。三步走：K-Means 地理聚类分天 → TSP 贪心+2-opt 排顺路 → 体力/营业/用时窗适配。这是通用 AI 完全做不好的事。
version: 1.0.0
author:
tags: [travel, itinerary, tsp, clustering, optimization, moat]
license: MIT
triggers:
  - poi-curate 输出 poi_pool 后
  - 用户对某主题路线确认后需要"具体每天怎么走"
inputs:
  - name: poi_pool
    type: object
    required: true
  - name: trip_request
    type: object
    required: true
  - name: user_profile
    type: file
    formats: [json]
    required: true
  - name: hotel_anchor
    type: object
    doc: 当天住宿坐标，作为出发/返回锚点
    required: true
outputs:
  - name: itinerary
    type: object
    doc: N 天行程，每天含时间轴 + POI 顺序 + 路径距离 + 体力指数
---

# 行程运筹（itinerary-optimize）⭐

## 这是 agent 真正的护城河

通用 AI 排行程：「上午去 A，下午去 B」— 你打开地图一看，A 和 B 跨城市了。
我做的：用真实坐标做运筹，每天的 POI 是**真的顺路**。

## 三步算法

### Step 1: geo_cluster.py · K-Means 地理聚类分天

输入：N 个 POI 的坐标
输出：duration_days 个簇，每簇 5-7 个 POI

约束：
- 每天总点数 = 1 个早餐 + 1 个午餐 + 1 个晚餐 + 2-3 个景点 + 1 个咖啡/夜市 = 6-8 个
- 同一天的 POI 地理距离 < 15km（大城市）/ < 50km（小城市/跨景区）
- 第一天和最后一天预留交通时间，POI 减半

### Step 2: optimize_route.py · TSP 顺路

每个簇内部：
- 锚点 = 当天住宿坐标
- 起点 = hotel
- 终点 = hotel（除非要换酒店）
- 中间点 = 簇内 POI

算法：
- 节点 ≤ 10：枚举所有排列（10! = 3.6M，可接受）
- 节点 > 10：贪心最近邻 + 2-opt 优化
- 距离：haversine 球面距离（已知精度有限但够用），并由经验系数估算驾车/步行时长（市区 1.4×，跨城 1.2×；步行 12 min/km，驾车 30 km/h 市区 60 km/h 跨城）
- v2.0 取消高德距离矩阵依赖，运筹精度从"真实驾车时长"退到"haversine + 经验估算"

### Step 3: balance_pace.py · 体力/营业/时间窗适配

输入：顺路后的 POI 序列
输出：带具体时间的行程表

约束：
- 早餐 7:30-9:00
- 上午景点 9:30-12:00（≤ 2 个）
- 午餐 12:00-13:30
- 午休 + 下午景点 14:30-17:30（≤ 2 个）
- 晚餐 18:00-19:30
- 晚间活动（夜市/酒吧/夜景）20:00-22:00（可选）

体力分配规则（按 user_profile.basic.preferred_pace）：
- walker_intense：每天上限 5 个景点 + 暴走
- normal：每天 3-4 个景点
- relaxed：每天 2 个景点 + 大块自由时间

营业时间适配：
- 用 online-search 查 POI 营业时间
- POI 营业时间冲突 → 自动调换日期或顺序
- 周一闭馆景点（博物馆类）自动避开

## 输出 schema

```json
{
  "trip_id": "uuid",
  "days": [
    {
      "day_index": 1,
      "date": "2026-04-15",
      "theme": "市区文化探索",
      "hotel": { "name": "亚朵 S 春熙路", "lat": 30.6594, "lng": 104.0816 },
      "stops": [
        {
          "order": 1,
          "time": "08:00-09:00",
          "type": "breakfast",
          "poi": { "name": "贺记蛋烘糕", "lat": 30.6580, "lng": 104.0820 },
          "duration_min": 60,
          "distance_from_prev": "300m",
          "transport": "walk"
        },
        {
          "order": 2,
          "time": "09:30-12:00",
          "type": "scenic_spot",
          "poi": { "name": "杜甫草堂", ... },
          "duration_min": 150,
          "distance_from_prev": "5.2km",
          "transport": "drive_18min"
        },
        ...
      ],
      "total_distance_km": 22.5,
      "total_walk_steps_est": 14000,
      "fatigue_index": 0.65,
      "_fatigue_doc": "0-1，>0.85 会建议改 relaxed 节奏",
      "weather": { "summary": "晴 18-26℃", "rain_prob": 0.1 }
    }
  ],
  "metadata": {
    "algorithm_version": "1.0",
    "total_poi_used": 18,
    "total_poi_pool": 32,
    "_pool_doc": "用了 18 个，剩 14 个进备选池供用户改"
  }
}
```

## 备选池

剩下没塞进行程的 POI 进 `backup_pool`，用户说"D2 想换一下"时秒切换。

## 跨城多日的处理

5 天 4 城（南昌→婺源→景德镇→庐山）：
- 每个城市独立做 cluster + TSP
- 城市间距离用 haversine 估算
- 换酒店那天 POI 减少（留给路上）

## 反模式

- ❌ 用欧氏距离（球面距离用 haversine，不要用 sqrt(dx²+dy²)）
- ❌ 不考虑营业时间（推到周一去博物馆）
- ❌ 不给体力指数（用户走两天累趴）
- ❌ 不留 backup_pool（用户改一个就要重跑全部）
- ❌ 没有坐标数据时用 online-search 补查，无法补查时标 ⚪ 降级

---

_这是通用 AI 完全做不到的事。这个 skill 的脚本质量直接决定 agent 的核心竞争力。_
