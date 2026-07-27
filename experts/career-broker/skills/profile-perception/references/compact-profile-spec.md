# 缩略版画像规格（含反向索引）

> 缩略版是为**下游 skill 的程序化匹配**服务的：内部机会推荐 / 职业咨询 直接读这份 JSON，不需要解析自评原文。
> 完整版 `profile.json` 是 LLM 上下文 + 给人看的；本缩略版 `profile_compact.json` 是给程序消费的。

---

## 1. 文件位置

```
~/.workbuddy/career-broker/<rtx>/
├── profile.json              # 完整版（详）
├── profile_summary.md        # 完整版（人话）
├── profile_compact.json      # 缩略版（程序）  ★
└── profile_compact.md        # 缩略版（人话）  ★
```

---

## 2. 缩略版顶层结构

```json
{
  "schema_version": "1.1-compact-with-provenance",
  "rtx": "...",
  "version": "v3-real-2026-06-02",
  "generated_at": "...",

  "based_on": {
    "self_assess_periods": [
      { "asId": "...", "name": "2025下半年人才评估" }
    ],
    "tapd_story_count": 15,
    "tapd_workspace": "20455870 / 效率与体验中心",
    "gongfeng": "skipped" | "available"
  },

  "_provenance": {
    "self_assess_objectives": {
      "SA1": "校招核心业务诉求挖掘与落地",
      "SA2": "内部工具体验优化",
      "SA3": "AI+行业 专业能力提升"
    },
    "tapd_stories": {
      "T1":  { "id": "1020455870129655611", "name": "..." },
      "T2":  { "id": "...", "name": "..." }
    }
  },

  "skill_tags":      [ /* 标签 + 权重 + 反向索引 */ ],
  "domain_tags":     [ /* 同上 */ ],
  "project_keywords": { /* 按主题分组的关键词 + 反向索引 */ },
  "trait_tags":      [ /* 软性素质 + 反向索引 */ ],
  "outcome_metrics_top": [ /* 关键指标 + 来源 */ ]
}
```

---

## 3. 反向索引规则（核心）

### 3.1 数据源代号

| 代号前缀 | 含义 |
|---|---|
| `SA{n}` | 自评（Self-Assess）第 n 个 Objective。n 从 1 起，按 objectives[].index 升序 |
| `T{n}` | TAPD 第 n 条 story。n 从 1 起，按 modified 时间倒序排列后编号 |
| `G{n}` | 工蜂第 n 个仓库（如有） |

代号定义放在 `_provenance` 里，每条 SA/T/G 都映射到原始 ID。

### 3.2 每个标签必带的字段

```json
{
  "tag": "内部工具产品迭代",
  "weight": 0.95,            // 0.7~0.95，给匹配算法加权
  "from": ["SA2"],           // 源自哪些自评 Objective
  "tapd": ["T1","T2","T5"]   // 关联的 TAPD story（可空数组）
}
```

**weight 标尺**：
- `0.95` 主线高频出现 + 含量化产出
- `0.85` 主线之一 + 多条证据
- `0.80` 跨多个 Objective 但非主导
- `0.70` 单点提及但有证据

### 3.3 project_keywords 的特殊结构

按"主题分组"组织，每个 kw 同样带 `from / tapd`：

```json
"project_keywords": {
  "内部机会": [
    { "kw": "内部匿名池", "from": ["SA2"], "tapd": ["T8","T12"] },
    { "kw": "内部挂号",   "from": ["SA2"], "tapd": [] }
  ],
  "校招": [...],
  "AI":   [...],
  "学习": [...]
}
```

### 3.4 trait_tags 的特殊字段

```json
{
  "tag": "业务推进力强",
  "from": ["SA1","SA2","SA3"],
  "tapd_evidence": "15/15 已发布"   // 一句话证据，不存 tapd id 列表
}
```

---

## 4. 提炼指引（给 LLM）

让 LLM 在三轴提炼时，**强制每个标签必须给反向索引**：

```
对每个 skill_tag / domain_tag / project_keyword / trait_tag：
  - 必须列出至少 1 个 from（自评 SA 代号）
  - tapd 字段：扫描 TAPD 列表，把"标题或描述匹配该标签语义"的 story 代号填进来
  - 标签不能没有任何来源；如果连 1 个都凑不出，删掉这个标签

对 outcome_metrics_top：
  - 每条只允许来自 1 个 SA（数字本来就只属于一处）

对 trait_tags：
  - tapd_evidence 写一句话总结（不存 id 列表，避免冗长）
```

---

## 5. 下游消费示例

### 5.1 内部机会推荐（如何"为什么推荐"）

```python
profile = json.load(open("profile_compact.json"))
provenance = profile["_provenance"]

for tag in profile["skill_tags"]:
    if tag["tag"] in jd_required_skills:
        # 命中标签
        sa_ids = tag["from"]   # ["SA2"]
        tapd_ids = tag["tapd"] # ["T1","T2",...]

        # 反向溯源
        for sa in sa_ids:
            obj_name = provenance["self_assess_objectives"][sa]
            # → "内部工具体验优化"
        for ti in tapd_ids:
            story = provenance["tapd_stories"][ti]
            # → {"id":"...","name":"【内部机会】小程序新增消息订阅功能"}

        # 推荐文案：
        # "你做过【内部工具体验优化】专项，
        #  含 11 个具体需求（如 小程序新增消息订阅 / 调出审批自动提交 / 录用确认 / ...）"
```

### 5.2 加权打分

```python
score = 0
for tag_obj in profile["skill_tags"]:
    if tag_obj["tag"] in jd_keywords:
        score += tag_obj["weight"]
```

---

## 6. 隐私（与完整版相同）

- 缩略版字段全部为 P2（自由共享）+ 极少 P1（脱敏共享）
- **不包含** outcome 原文、KR 原文、TAPD story description
- 可以上云作为 workbuddy 专家记忆
- 上云时 `_provenance.tapd_stories[].id` 视作 P1，仅本人会话内可读，不外露给其他用户

---

## 7. 何时重新生成缩略版

| 触发条件 | 操作 |
|---|---|
| 完整版 profile.json 更新 | 自动重新生成缩略版 |
| 用户口头修正某个标签（"我没做过 XX"） | 同步删 from/tapd 关联 |
| 新自评周期完成 | profile.json 加新 SA{n+1}，缩略版自动追加新代号 |
| TAPD 新增 owner story | 重跑 stories_get 后追加 T{n+1} |
