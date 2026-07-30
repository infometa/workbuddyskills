---
name: poi-curate
description: POI 多维加权打分 · 基于美团/online-search的 POI 详情 + 小红书评论 + 用户偏好画像，按 scoring_rules.json 多维度打分，输出每天可塞入的 Top N POI 清单。是 itinerary-optimize 的输入。
version: 1.0.0
author:
tags: [travel, poi, scoring, curate]
license: MIT
triggers:
  - destination-research 已输出选定目的地后
  - 需要为每天行程挑选具体 POI（景点/餐厅/小吃/打卡点）时
inputs:
  - name: destinations
    type: array
    doc: 选定的目的地城市列表
    required: true
  - name: user_profile
    type: file
    formats: [json]
    required: true
  - name: trip_request
    type: object
    required: true
outputs:
  - name: poi_pool
    type: object
    doc: 按城市分组的 POI 池，每个 POI 含坐标/评分/价格/营业/置信度/匹配度
---

# POI 筛选打分（poi-curate）

## 我解决什么问题

通用 AI 推 POI：「成都熊猫基地、宽窄巷子、锦里、春熙路、武侯祠…」 — 全是游客街，没有针对性。
我做的：根据用户**口味/节奏/禁忌/季节/天气**做加权评分，把**真实评价**纳入考量。

## 工作流程

```
destinations + user_profile + trip_request
   ↓
Step 1: 调 search-orchestrator (domain=poi)
   ├─ 美团连接器 "景点推荐" / "本地玩乐"
   ├─ online-search 查 POI 详情
   └─ xhs-explore skill 拉评论（识别水军 + 真实避雷）
   ↓ raw_pois.json
   ↓
Step 2: scripts/score_pois.py
   按 data/scoring_rules.json 多维加权：
   - rating       (20%)
   - xhs_buzz          (15%)
   - xhs_sentiment     (15%) ← 评论情感分析
   - user_pref_match   (30%) ← 与 profile 匹配
   - queuing_factor    (10%)
   - weather_compat    (10%)
   减去 penalties（rejected/visited/no_high_altitude/dietary 冲突）
   加上 boosts（favorites/scene_likes/local_recommended）
   ↓
Step 3: 按城市分组，每类目（景点/餐厅/咖啡/夜市）取 Top N
   ↓
poi_pool.json
   ↓ 给 itinerary-optimize
```

## 输出 schema

```json
{
  "by_city": {
    "成都": {
      "scenic_spot": [
        {
          "id": "poi-001",
          "name": "杜甫草堂",
          "category": "scenic_spot",
          "lat": 30.6622,
          "lng": 104.0218,
          "rating": 4.6,
          "xhs_notes": 1242,
          "xhs_likes": 38900,
          "xhs_sentiment_score": 0.78,
          "_sentiment_doc": "0-1，正/负面词频比",
          "open_hours": "08:00-18:00",
          "ticket_price": 50,
          "est_visit_min": 90,
          "est_queue_min": 10,
          "final_score": 0.82,
          "match_doc": "你喜欢博物馆类（+15）、不爱排队（OK：仅 10 分钟）",
          "warnings": [],
          "confidence": "green",
          "evidence_summary": "1242 篇笔记普遍正面，少数提到讲解差"
        }
      ],
      "restaurant": [...],
      "cafe": [...]
    }
  },
  "metadata": {
    "scoring_rules_version": "1.0",
    "queried_at": "2026-06-03T17:00:00+08:00"
  }
}
```

## scoring_rules.json 是核心数据资产

详细维度/权重在 `data/scoring_rules.json`。
**只在这个 skill 里读它**，避免散落到多处。

## 反模式

- ❌ 把评分逻辑硬编码到 .py（必须从 JSON 读，方便调整）
- ❌ 不做情感分析就用 xhs_buzz（有些点是黑红，buzz 高但负面多）
- ❌ 直接吐 100 个 POI（没有 Top N 筛选会让 07 算不动）
- ❌ 忽略 user_profile.history.rejected_pois（用户讨厌过的不能再推）

## 数据置信度

- 🟢 green：美团连接器 + xhs-explore 三源都有
- 🟡 yellow：只有 1-2 源
- ⚪ gray：仅 WebSearch / references/ 兜底

---

_这个 skill 决定了行程的"质感"。规则用 JSON 数据资产化是核心。_
