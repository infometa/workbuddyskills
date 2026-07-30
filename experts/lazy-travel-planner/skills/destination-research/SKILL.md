---
name: destination-research
description: 目的地调研 · 把"江西附近游玩"或"成都"这类输入，转成结构化的目的地候选清单（含特色/季节性/必玩/避雷）。完全调用 search-orchestrator 编排底座，不重复造检索逻辑。
version: 1.0.0
author:
tags: [travel, destination, research, glue]
license: MIT
triggers:
  - intake-clarify 完成后，trip_request.destination_resolved = false
  - 用户说"我想去 X"、"X 附近哪里好玩"、"X 月去哪合适"等需要目的地选型的场景
inputs:
  - name: trip_request
    type: object
    required: true
  - name: user_profile
    type: file
    formats: [json]
    required: true
outputs:
  - name: destination_options
    type: object
    doc: 2-3 个目的地候选 + 每个的特色亮点 / 季节适配 / 数据置信度，给用户挑
---

# 目的地调研（destination-research）

## 我解决什么问题

用户说"江西附近游玩"，通用 AI 只会说"庐山很好"。
我做的是：基于真实坐标 + 真实游记 + 用户偏好，给 2-3 个**有差异化主题**的候选让用户挑。

例：
- 自然风光线（庐山+三清山+龙虎山）
- 文化古韵线（婺源+南昌滕王阁+景德镇）
- 小众探秘线（武功山+明月山+武宁）

## 工作流程

```
trip_request + user_profile
   ↓
调 search-orchestrator (domain=destination)
   ├─ 美团连接器 "景点推荐"
   ├─ online-search（地理搜索）
   ├─ xhs-explore skill 多关键词扩展
   └─ 自动去重 + 排序 + 深读
   ↓ candidates.json
   ↓
本 skill：用 LLM 把候选打包成 2-3 个**有主题**的路线选项
   ├─ 标题 + 一句话理由
   ├─ 包含的城市/景点
   ├─ 季节适配标记
   ├─ 数据置信度
   └─ 适合谁玩（基于 user_profile 匹配度）
   ↓
返回 destination_options
   ↓
阶段 2 让用户挑一个
```

## 输出 schema

```json
{
  "trip_request_id": "uuid",
  "options": [
    {
      "id": "opt-1",
      "name": "自然风光线",
      "tagline": "看山观湖避人潮，户外党的菜",
      "destinations": ["庐山", "三清山", "鄱阳湖"],
      "match_score": 0.85,
      "_match_doc": "对 user_profile 的匹配度，0-1",
      "season_fit": "good",
      "_season_options": ["best", "good", "ok", "bad"],
      "highlights": [
        "庐山五老峰云海（春秋最佳）",
        "三清山日出（户外摄影圣地）",
        "鄱阳湖候鸟季（11-3月）"
      ],
      "warnings": [
        "三清山要爬山（你的 profile 标了 no_long_walk，注意）"
      ],
      "confidence": "green",
      "evidence_count": { "amap": 12, "xhs_notes": 38, "xhs_comments": 156 }
    },
    {
      "id": "opt-2",
      "name": "文化古韵线",
      ...
    }
  ],
  "queried_at": "2026-06-03T17:00:00+08:00"
}
```

## 反模式

- ❌ 不调用 search-orchestrator 自己写检索（违反复用原则）
- ❌ 给 6+ 个选项（用户会选择疲劳，控制在 2-3 个）
- ❌ 选项之间高度重叠（必须有差异化主题）
- ❌ 不标注与 user_profile 的冲突（如用户怕爬山却推荐爬山线）

## 上游怎么用我的输出

在 阶段 2，给用户：
> "看了下江西方向，给你 3 个不同主题的方案：
>   A. 自然风光线（庐山+三清山+鄱阳湖）— 看山观湖
>   B. 文化古韵线（婺源+景德镇）— 古镇瓷器
>   C. 小众探秘线（武功山）— 户外党
> 你想往哪个方向？"

---

_这是个胶水 skill，重点在于"调编排 + 用 LLM 包装成路线"，本身代码很薄。_
