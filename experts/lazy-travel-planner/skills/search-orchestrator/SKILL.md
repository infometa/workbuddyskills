---
name: search-orchestrator
description: 搜索编排底座 · 把"江西附近游玩"这类模糊地理意图转成结构化查询矩阵，调度online-search / 美团连接器 / xhs-explore skill 做 fan-out → fan-in 多源混合检索，输出带置信度的候选地点 + 内容证据池。是 03/04/06/09 的共用底座。
version: 1.0.0
author:
tags: [travel, search, geo-fanout, multi-source, orchestrator]
license: MIT
triggers:
  - 上游 skill 需要基于地理位置做"附近 / 周边 / 区域"模糊搜索时
  - 用户输入"X 附近游玩"、"X 周边自驾"、"X 一日游"等模糊地理意图
  - 03 / 04 / 06 / 09 任一 skill 调用前
inputs:
  - name: intent
    type: string
    doc: 用户原始自然语言意图，如"江西附近游玩 4 天"
    required: true
  - name: user_profile
    type: file
    formats: [json]
    doc: 来自 preference-load 的偏好画像
    required: true
  - name: domain
    type: string
    enum: [destination, poi, accommodation, risk]
    doc: 调用方告诉我搜什么类型，决定查询模板和数据源组合
    required: true
outputs:
  - name: candidates
    type: file
    format: json
    doc: 候选地点 + 每地点的内容证据池（笔记、评论、坐标）+ 数据置信度标记
---

# 搜索编排底座（search-orchestrator）

## 我解决什么问题

通用 AI 看到"江西附近游玩"会笼统说"庐山很好"。
我会做这套事：

1. **地理 fan-out**：调online-search（地理搜索） 拿候选地点池（庐山/婺源/三清山/龙虎山/井冈山/鄱阳湖…）
2. **查询矩阵生成**：对每个候选地点 × 用户偏好 × 季节 生成 15-20 条精准查询
3. **多源串行执行**：美团连接器 + xhs-explore skill（含限速/熔断）+ WebSearch 兜底
4. **去重 + 排序 + 深读**：Top 30 笔记拿全文，Top 5 拿评论
5. **置信度标记**：每条数据都带 🟢🟡⚪

## 工作流程

```
intent + user_profile + domain
   ↓
Step 1: parse_intent.py        解析中心点 / 半径 / 时间
   ↓
Step 2: geo_fanout.py          online-search（地理搜索） → 候选地点 Top 6-10
   ↓
Step 3: query_expand.py        候选 × 偏好 × 季节 → 15-20 条查询
   ↓
Step 4: 并发执行（≤2 worker，带熔断）
        ├─ meituan_search.py   调美团连接器
        ├─ xhs_batch_search.py 调 xhs-explore skill
        └─ web_fallback.py     WebSearch 兜底
   ↓
Step 5: dedupe_rank.py         按 note_id/POI 去重，按 likes×comments 排序
   ↓
Step 6: deep_read.py           Top 30 read 全文 + Top 5 comments
   ↓
candidates.json
   ↓ 返回上游 skill
```

## 查询矩阵生成规则（C: 模板 + LLM 混合）

90% 走 `query_templates.json` 的模板填空：
```json
{
  "destination": [
    "{location} 攻略",
    "{location} 必去",
    "{location} 避雷",
    "{location} {season} 推荐",
    "{location} {duration}日游"
  ],
  "poi": [
    "{location} {category}",
    "{location} 本地人 {category}",
    "{location} {category} 性价比"
  ],
  "accommodation": [
    "{location} {tier_label} 酒店推荐",
    "{location} 民宿 真实体验",
    "{location} 住哪里 方便"
  ],
  "risk": [
    "{location} 避雷",
    "{location} 被坑",
    "{location} 注意事项"
  ]
}
```

10% LLM 创造性扩展：基于 user_profile 的特殊偏好生成 1-2 条规则覆盖不到的查询，
如「江西小众老建筑」「成都 不爬山 拍照机位」。

## 反风控约束（与 xhs-explore skill 协同）

- 并发上限 2，超过会触发 461/471
- 连续 3 次错误 → 立即降级到 WebSearch
- 同目的地 30 天内查询本地缓存（`data/.cache/xhs/`）

## 数据置信度

每条返回的 candidate 必须带：
```json
{
  "name": "庐山",
  "source": "online-search+xhs",
  "confidence": "green",
  "search_data": { ... },
  "xhs_evidence": [ {note_id, snippet, sentiment} ],
  "queried_at": "2026-06-03T17:00:00+08:00"
}
```

`confidence` 取值：
- 🟢 green：MCP/CLI 一手数据
- 🟡 yellow：WebSearch 抓取
- ⚪ gray：references/ 静态兜底

## 上游 skill 怎么调我

```python
# 例：destination-research 调用本 skill
import subprocess, json
result = subprocess.run([
    "python", "skills/search-orchestrator/scripts/orchestrate.py",
    "--intent", "江西附近游玩 4 天",
    "--profile", "data/user_profile.json",
    "--domain", "destination",
    "--output", "data/.cache/run-{run_id}/candidates.json"
], capture_output=True, text=True)
candidates = json.loads(open("data/.cache/run-xxx/candidates.json").read())
```

## 反模式

- ❌ 直接调用各种 MCP / CLI，绕开本 skill（会导致重复发请求 / 没有去重 / 没有熔断）
- ❌ 在上游 skill 自己做查询扩展（应该统一在这里做，保证策略一致）
- ❌ 不带 domain 参数（不知道用哪套查询模板）

---

_这个 skill 是整个 agent 的"检索操作系统"，所有需要外部数据的 skill 都要走这里。_
