---
name: budget-balance
description: 预算平衡与取舍 · 按总预算分配交通/住宿/餐饮/门票/购物/备用六大类，超支时主动给"砍哪天/降哪档/换地点"的取舍建议。基于 price_benchmark.json 城市价格基准做合理性校验。
version: 1.0.0
author:
tags: [travel, budget, allocation, tradeoff]
license: MIT
triggers:
  - itinerary-optimize 完成后，自动跑预算合理性检查
  - 用户给定 budget_total 时
  - 用户问"这趟大概多少钱"
inputs:
  - name: trip_request
    type: object
    required: true
  - name: itinerary
    type: object
    required: true
  - name: transport_plan
    type: object
    required: true
  - name: hotel_candidates
    type: array
    required: true
outputs:
  - name: budget_breakdown
    type: object
    doc: 预算明细 + 健康度评估 + 取舍建议
---

# 预算平衡（budget-balance）

## 我解决什么问题

通用 AI 给行程不算账。
我做的：

1. 每天细到品类的预算明细（早/午/晚饭、门票、市内交通、其他）
2. 与 `data/price_benchmark.json` 城市基准对比，标"贵了 / 合理 / 便宜"
3. 总预算超了 → 主动给取舍建议

## 工作流程

### Step 1: 估算

按 trip_request.budget_tier 拿 `price_benchmark.json` 区间，结合 itinerary 真实 POI 门票 + 酒店 + 交通：

```
total = 大交通(transport_plan)
     + 住宿(hotel_candidates × nights)
     + 每日餐饮(price_benchmark.food × tier × duration_days)
     + 门票(itinerary 累加 ticket_price)
     + 市内交通(打车×次数 + 地铁×天数)
     + 备用 10%
```

### Step 2: 健康度评估

按 `price_benchmark.default_ratio_by_tier` 检查占比：
- 住宿占比异常高 → 提示"是否考虑降一档酒店"
- 餐饮占比异常低 → 提示"是不是没安排够餐？"
- 门票太高 → 提示"是不是塞了太多收费景区？"

### Step 3: 超支取舍建议

如果 total > budget_total，按"边际效用最低"原则给 3 套取舍方案：

```json
{
  "shortfall": 800,
  "tradeoffs": [
    {
      "id": "cut-day",
      "label": "缩短 1 天（去掉 D4 - 价值最低的一天）",
      "savings": 1200,
      "impact": "略可惜，D4 主题是郊区古镇，可以并到 D3"
    },
    {
      "id": "downgrade-hotel",
      "label": "酒店降一档（亚朵 S → 亚朵）",
      "savings": 600,
      "impact": "舒适度小幅下降，地段位置不变"
    },
    {
      "id": "swap-restaurant",
      "label": "把 2 顿网红餐厅换成本地家常",
      "savings": 400,
      "impact": "可能错过几个网红，但本地店更地道"
    }
  ]
}
```

## 输出 schema

```json
{
  "currency": "CNY",
  "per_person_total": 4200,
  "party_size": 2,
  "grand_total": 8400,
  "breakdown": {
    "transport_long": 1396,
    "_doc": "去 698 + 回 698",
    "accommodation": 2320,
    "food": 1200,
    "ticket": 380,
    "transport_intra": 200,
    "buffer": 504
  },
  "ratio_check": {
    "_doc": "vs price_benchmark.default_ratio_by_tier",
    "accommodation": { "actual": 0.55, "target": 0.40, "verdict": "too_high" },
    "food":         { "actual": 0.14, "target": 0.30, "verdict": "too_low" }
  },
  "comparison_to_benchmark": "你的住宿单价 580/晚，在标准档区间（420-750）；餐饮人均 60/天，明显偏低（基准 150-300），可能享受不到当地特色",
  "vs_user_budget": {
    "user_budget_per_person": 4000,
    "actual": 4200,
    "shortfall": 200,
    "verdict": "slightly_over"
  },
  "tradeoffs": [...],
  "queried_at": "2026-06-03T17:00:00+08:00"
}
```

## 反模式

- ❌ 不结合真实 itinerary 的门票数据（bench 只是兜底，能拿到真实数就用真实数）
- ❌ 超支不提醒（用户出发前才发现钱不够）
- ❌ 取舍建议只给一种（用户可能不愿意砍天，那要给降档/换地等多种）
- ❌ 不标"参考"（价格随时变，必须明确这是估算）

---

_钱的事不能糊涂。每个数字必须可解释、可调整、可追溯到数据源。_
