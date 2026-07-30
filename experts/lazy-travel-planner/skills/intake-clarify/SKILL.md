---
name: intake-clarify
description: 出游需求澄清 · 只问 3 件事（目的地/日期/人数），其余靠 agent 思考-调工具-给选项-必要追问。绝不一次问 10 个问题，绝不静默用默认值。老用户从 user_profile 默认沿用。
version: 1.0.0
author:
tags: [travel, intake, conversation, clarification]
license: MIT
triggers:
  - 用户首次进入对话提出出游需求时
  - 用户说"想去 X 玩"、"X 月想出去"、"帮我规划一下" 等模糊起意
  - 上游需求字段缺失（destination/date/duration/party_size/budget 任一为空）时
inputs:
  - name: user_message
    type: string
    required: true
  - name: user_profile
    type: file
    formats: [json]
    required: true
outputs:
  - name: trip_request
    type: object
    doc: 完整的出行请求 JSON（destination/origin/start_date/duration/party_size/budget_tier/pace/must_have/avoid）
---

# 需求澄清（intake-clarify）

## 我解决什么问题

通用 AI 一次抛 10 个问题（目的地、出发地、日期、人数、预算、偏好、节奏、必去、禁忌、特殊需求…），用户秒退。

我分 2-3 轮，每轮只问最关键的 2-4 个空缺，老用户从画像默认带出来。

## 必问 vs 不必问

### 🔴 必问 3 件事（缺一不可，否则不进阶段 2）

```
目的地 + 日期 + 人数
```

话术：
> "我想确认 3 件事就开干：去哪里？什么时候？几个人？"

唯一例外：用户给的"目的地"是模糊地理意图（如"江西附近""长三角周边"），不强求他指定具体城市，agent 走 search-orchestrator 调 xhs/美团给 2-3 个候选让他挑。

### 🟢 不必问的（agent 思考-调工具-必要才追问）

| 用户没说什么 | 错误做法 | 正确做法 |
|---|---|---|
| 出发地 | 问"从哪出发？" | 看 user_profile.last_known_origin；老用户默认沿用，新用户在阶段 1 第 1 轮**顺便问一下**（这一项可以一起问） |
| 预算 | 问"预算多少？" | 默认 standard 档跑完，方案出来后给"总预算 ¥X，要不要调整"的反馈 |
| 节奏（暴走/正常/躺平）| 问"喜欢什么节奏？" | 看历史；没历史用 normal；阶段 2 出方案后给"觉得太赶要不要砍点？"反馈 |
| 必去清单 | 问"有什么必去？" | 调 xhs/美团查热门组合，给主题候选（如"自然/文化/小众"3 选 1）|
| 禁忌（不爱辣/恐高等）| 问"有什么禁忌？" | 看 user_profile；新用户先做方案，发现可能冲突时再问 |
| 出行方式 | 问"高铁还是飞机？" | 按距离+人数自己算（<500km 一般高铁；>1000km 一般飞机；4 人以上高铁多数性价比高），给具体车次/航班候选让用户挑 |
| 住宿档次 | 问"住几星？" | 按预算档反推（economy=快捷，standard=中档，premium=高端），给 3 家候选 |

### 追问的硬规则

- **每轮最多 1 个开放问题**（"你想要什么风格？"算开放问）
- **优先用选项题代替开放问**（"想要 ①/②/③ 哪个？"是选项题）
- **必须是工具查不到、必须用户拍板的事**才追问
- 对话片段示例：
  ```
  用户："想去婺源"
  agent（错）："想看油菜花还是红叶？想住村里民宿还是镇上酒店？打算几天？预算多少？"
  agent（对）：「思考：婺源主要看花季，先查 11 月有什么玩」
              "11 月正好是婺源红叶季（长溪村/石城最美）+ 晒秋尾声，
               4 天可以这样玩：D1-2 红叶线，D3-4 古村+手作。要这个方向吗？"
  ```

## 输出 schema

```json
{
  "destination": "江西",
  "destination_resolved": false,
  "_resolved_doc": "如果是模糊地理意图，标 false，调 search-orchestrator 走 destination domain 让用户挑",
  "origin": "深圳",
  "start_date": "2026-04-15",
  "duration_days": 4,
  "party_size": 2,
  "party_composition": "couple",
  "budget_tier": "standard",
  "budget_total_per_person": null,
  "_budget_doc": "可选：用户给总预算优先于按 tier 估算",
  "pace": "normal",
  "must_have": [],
  "avoid": [],
  "transport_mode_preference": null,
  "session_id": "uuid",
  "completed_at": "2026-06-03T17:00:00+08:00"
}
```

## 反模式

- ❌ 一段话问 10 个问题
- ❌ 老用户问已知偏好（应该从 user_profile 带出来让他们确认）
- ❌ 用户没回答完就强行进入下一阶段
- ❌ 用户烦了还继续问（"不要再问了直接给方案"时立即用默认值出方案）

## 老用户快通道

当 `user_profile.history.completed_trips` 非空且最近一次在 6 个月内：
> "欢迎回来。上次成都 4 天玩得怎么样？这次想去哪？"
直接进入第 1 轮但跳过偏好类问题。

## 极端用户处理

- 用户：「我想出去玩」→ 反问"国内还是出境？短途周末还是长假？人数？"
- 用户：「随便给个方案」→ 用 `user_profile` 默认值 + 当前月份 + 国内热门 Top 5 给一个备选清单让用户挑
- 用户：「下个月有 5 天假」→ 主动问目的地，并从 `user_profile.history.visited_cities` 反推兴趣方向

---

_这个 skill 决定用户第一印象。重点是「短、准、不啰嗦」。_
