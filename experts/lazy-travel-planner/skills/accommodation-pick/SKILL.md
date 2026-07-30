---
name: accommodation-pick
description: 住宿选型 · 美团连接器一手房态价格为主，xhs-explore skill 拉真实住客评价识别水军，online-search（地理搜索） 评估位置。三维评分（位置 × 价位 × 口碑），输出 3-5 个酒店候选给用户挑。
version: 1.0.0
author:
tags: [travel, accommodation, hotel, glue]
license: MIT
triggers:
  - 03/04 完成后，行程主城市已确定
  - 用户问"在 X 住哪里方便"、"推荐酒店"
inputs:
  - name: city
    type: string
    required: true
  - name: check_in
    type: string
    required: true
  - name: nights
    type: integer
    required: true
  - name: budget_tier
    type: string
    required: true
  - name: anchor_pois
    type: array
    doc: 行程的核心 POI 坐标，用来评估位置（应该住在哪片区）
    required: true
outputs:
  - name: hotel_candidates
    type: array
    doc: 3-5 个酒店候选
---

# 住宿选型（accommodation-pick）

## 我解决什么问题

通用 AI 推酒店：「全季、亚朵、桔子水晶」— 没错但没用。
我做的：基于**用户当天行程的核心 POI 坐标**反推「应该住哪片区」，再交叉口碑筛 3-5 个候选。

## 工作流程

```
city + dates + budget_tier + anchor_pois
   ↓
Step 1: 反推住宿区域
   - 计算 anchor_pois 的地理质心
   - 找质心 3km 内、地铁站 500m 内、价位匹配的酒店类目
   ↓
Step 2: 拉酒店列表
   ├─ 美团连接器 "酒店推荐"（一手房态/价格/评分）
   ├─ online-search 搜索附近酒店
   └─ xhs-explore skill "X 区域 酒店推荐" / "X 酒店 真实体验"
   ↓
Step 3: 三维评分
   - 位置 (40%): 距 anchor_pois 平均距离 + 地铁可达性
   - 价位 (30%): vs price_benchmark.json 的 budget_tier 区间
   - 口碑 (30%): 美团评分 × xhs 评论情感
   ↓
Step 4: 过滤 user_profile 禁忌
   - must_have_starbucks_or_equivalent → 周边必须有
   - no_share_room → 排除青旅多人间
   - needs_accessibility → 必须有无障碍设施
   ↓
Top 3-5 候选
```

## 输出 schema

```json
[
  {
    "rank": 1,
    "name": "亚朵 S 酒店成都春熙路店",
    "type": "boutique_hotel",
    "lat": 30.6594,
    "lng": 104.0816,
    "price_per_night_ref": 580,
    "_price_doc": "参考价；标准房；2026-06-03 17:00 查",
    "rating": {
      "meituan": 4.7,
      "xhs_sentiment": 0.82,
      "_xhs_evidence": "228 条笔记，3 个差评提到隔音"
    },
    "location_score": 0.92,
    "_location_doc": "距 anchor_pois 平均 1.8km；地铁口 200m",
    "amenities": ["前台 24h", "自助早餐", "健身房", "免费 wifi"],
    "warnings": [
      "节假日溢价 30-50%（你的日期是清明小长假，注意）"
    ],
    "book_url": "https://hotels.meituan.com/...",
    "confidence": "green"
  }
]
```

## 反模式

- ❌ 不结合 anchor_pois 推酒店（结果是"网红酒店推荐"，不是"住这里方便"）
- ❌ 只看美团评分（4.5+ 的店一抓一大把，要看真实评论）
- ❌ 忽略节假日溢价（用户预定时被坑）
- ❌ 推青旅给"luxury" 档用户（明显档位不匹配）

## 主城多日的情况

5 天行程在成都市内可能要换酒店：
- 前 2 天玩市区 → 春熙路片区
- 后 3 天去都江堰 → 都江堰民宿

本 skill 输出按"住宿段"分组：
```json
{
  "stays": [
    { "nights": 2, "hotels": [...], "area": "春熙路" },
    { "nights": 3, "hotels": [...], "area": "都江堰" }
  ]
}
```

## 美团连接器未开通时

降级到 online-search + xhs-explore，标注 🟡 yellow，并提醒用户：
> "美团连接器没开，房态/价格不是一手数据。建议在 qclaw 「连接」开通后重跑。"

---

_住宿是用户体验放大器。"住对地方"比"住贵酒店"重要 10 倍。_
