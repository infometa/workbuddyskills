---
name: transport-plan
description: 交通方案规划 · 大交通（高铁/飞机推荐+备选）+ 市内交通（地铁/打车/公交）。美团连接器 + online-search（火车票查询） 双源校验高铁，机票走 WebSearch 兜底。永远标注"参考价 + 查询时间"。
version: 1.0.0
author:
tags: [travel, transport, train, flight, glue]
license: MIT
triggers:
  - intake-clarify 完成后，destination 已确定且 origin 不同城
  - 用户问"X 到 Y 怎么去最方便"
inputs:
  - name: trip_request
    type: object
    required: true
outputs:
  - name: transport_plan
    type: object
    doc: 大交通方案（去回程各 2-3 选项）+ 市内交通策略
---

# 交通方案规划（transport-plan）

## 我解决什么问题

通用 AI 报机票价 = 它训练时的价 = 多半早就过期了。
我每次实查 + 标注查询时间，并给"双源校验"避免单一数据源出错。

## 工作流程

### 大交通（去 + 回）

```
origin + destination + start_date + duration_days
   ↓
Step 1: 距离判断 → 选交通模式优先级
   ├─ < 800km → 高铁优先
   ├─ 800-1500km → 高铁/飞机比较
   └─ > 1500km → 飞机优先
   ↓
Step 2 (高铁): 美团连接器 "火车票查询" + online-search（火车票查询） 双源校验
   ├─ 美团给的车次和 12306 一致？ → 🟢 green
   ├─ 不一致 → 用 12306 为准 + 标 🟡 yellow
   └─ 12306 报错 → 用美团 + 标 🟡 yellow
   ↓
Step 2 (机票): 美团连接器 "机票"（如有）
   └─ 美团没有 → online-search 兜底 + 给携程/飞猪链接让用户自查
   ↓
Step 3: 排序输出 Top 3 候选（按"性价比 + 时长 + 时段合理"）
```

### 市内交通

调online-search（公交路线） / `maps_direction_driving` 算 POI 间路线，**主要服务于 itinerary-optimize**。
本 skill 主要给"机场/车站到酒店"的接驳建议。

## 输出 schema

```json
{
  "outbound": {
    "mode": "high_speed_rail",
    "options": [
      {
        "rank": 1,
        "train_no": "G88",
        "depart_station": "深圳北",
        "arrive_station": "南昌西",
        "depart_time": "08:42",
        "arrive_time": "13:55",
        "duration_min": 313,
        "ticket_class": "二等座",
        "price_ref": 698,
        "_price_doc": "参考价；查询时间 2026-06-03 17:00；订票请到 12306 / 美团",
        "source": "meituan+online-search",
        "confidence": "green",
        "book_url": "https://kyfw.12306.cn/..."
      }
    ],
    "note": "建议提前 7 天订票，旺季尽早"
  },
  "return": { ... },
  "intra_city": {
    "airport_to_hotel": "T2 机场地铁 1 号线 8 站到 XX 站，约 35 分钟，5 元",
    "hotel_to_attraction_default": "市内地铁覆盖率高，打车 30 元内多数景点可达"
  },
  "queried_at": "2026-06-03T17:00:00+08:00"
}
```

## 永远标的免责声明

每个价格旁必须有：
- 查询时间戳
- 数据源
- 给一个 "去哪里订" 的官方链接

## 反模式

- ❌ 把价格当作决策依据（只能当参考）
- ❌ 不做双源校验直接出方案
- ❌ 不告诉用户"这个价随时变"
- ❌ 不给订票链接（让用户去搜，体验差）

---

_交通方案是用户最容易抓 agent 错的地方（价格变了、车次变了），透明度比准确度更重要。_
