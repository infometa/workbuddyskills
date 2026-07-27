# profile.json · 三轴画像 schema (v2)

> v2 重组：自评驱动 + 三轴（技能 / 经历 / 软性素质），下游 3 个 skill 全依赖此 schema。
> 任何字段变更必须同步下游。

---

## 0. 顶层结构

```json
{
  "schema_version": "2.0",
  "staff_id": "12345678",
  "rtx": "<your-rtx>",
  "tenure_years": 4.2,
  "data_path": "self_assess" | "resume_upload" | "clarify_only",
  "n_assess_total": 5,           // 历史自评总数
  "n_assess_recent": 3,           // 完整解析的近 N 期数（≤3）
  "generated_at": "2026-06-02T19:00:00+08:00",
  "version": "v2-2026-06-02T19:00:00",
  "last_updated_by": "auto" | "user_clarify" | "user_correct",
  "partial": false,

  "basic":       { ... },        // recruit-mcp infoDetail 映射
  "skills":      { ... },        // 轴 1
  "experiences": { ... },        // 轴 2
  "traits":      { ... },        // 轴 3
  "motivation":  null | { ... }, // 反问
  "blockers":    null | { ... }, // 反问

  "raw_sources": { ... },
  "cloud_sync": {                // 上云状态
    "synced_at": null,
    "synced_version": null
  }
}
```

`data_path`：
- `self_assess` — 有 ≥1 期自评（主路径）
- `resume_upload` — 0 期自评 + 用户上传简历
- `clarify_only` — 0 期自评 + 拒绝上传 + 走对话反问

---

## 1. basic（基础身份）

```json
{
  "name_cn": "张三",
  "name_en": "Zhang San",
  "gender": "M" | "F" | "unknown",
  "dept_path": "TEG/AI Lab/算法组",
  "dept_id": "1001",
  "department_name": "算法组",
  "bg_name": "TEG",
  "clan_name": "产品/项目族（PD）",
  "genus_name": "产品类－PDM",
  "position": "产品策划",
  "position_name": "产品策划",
  "level": "P5",
  "career_level_id": "181",
  "level_sequence": "产品/项目族（PD）",
  "level_channel": "产品类－PDM",
  "staff_property_id": 5,
  "staff_property_name": "非管理者",
  "hire_date": "2022-03-15",
  "tenure_years": 4.2,
  "work_location": "深圳总部",
  "work_location_id": "1",
  "manager_rtx": "lisi"
}
```

来源优先级：recruit-mcp `recruit.huoshui-server.get_personal_api_web_personal_infoDetail` → 自评返回反推 → 用户口头补充。禁止凭对话上下文猜。

---

## 2. 轴 1 · skills（能干什么）

```json
{
  "technical": [
    {
      "tag": "推荐排序",
      "level": "高",
      "weight": 0.9,
      "evidence": ["2025H2 KR1 推动多目标排序模型", "..."],
      "source": ["self_assess", "tapd"]
    }
  ],
  "domain": [
    {
      "tag": "校招招聘",
      "level": "高",
      "weight": 0.9,
      "evidence": ["主导校招核心业务诉求挖掘"],
      "source": ["self_assess"]
    }
  ],
  "tools": [
    { "tag": "Python", "source": "gongfeng" },
    { "tag": "Go",     "source": "gongfeng" }
  ],
  "od_self_score": [
    { "dimension": "算法建模", "score": 4.2, "last_update": "2025-12-01" }
  ]
}
```

提炼规则：
- `technical` 主要从 KR 动作词 + 业务系统名提取（如 "推荐排序"、"埋点平台"）
- `domain` 从 oName 主题词提取（如 "校招招聘"、"内部工具产品"）
- `tools` 从工蜂仓库语言统计 + 自评中明确提及的工具名
- `level`：高/中/低，按 evidence 数量 + 跨周期出现频次判定
- `evidence` 必须是**自评原文片段**，便于追溯，下游 skill 不直接展示

---

## 3. 轴 2 · experiences（干过什么）

```json
{
  "recent_3_periods": [
    {
      "period_id": "6919912fa78d514eca190634",
      "period_name": "2025下半年人才评估",
      "status": "AssessFinish",
      "objectives": [
        {
          "index": 0,
          "name": "校招核心业务诉求挖掘与落地",
          "key_results": "KR1: ...\nKR2: ...\nKR3: ...",
          "outcome": "<原文>",
          "high_priority": false,
          "outcome_metrics": ["26,681 份简历", "12 月内研发评审"],
          "themes": ["校招", "需求挖掘", "系统改造"]
        }
      ]
    }
  ],
  "earlier_summary": "更早 N 期主线脉络（LLM 100-200 字汇总）。",
  "earlier_periods_meta": [
    { "period_id": "...", "period_name": "2024下半年人才评估", "status": "AssessFinish" }
  ],
  "before_tencent": null | {
    "from_source": "recruit_info_detail" | "resume_upload" | "user_clarify",
    "educations": [...],
    "work_experiences": [...],
    "project_experiences": [...]
  },
  "in_tencent_supplements": {
    "tapd_top": [...],            // 仅作 evidence 支撑
    "gongfeng_top": [...]
  }
}
```

> `outcome_metrics` 仅做"提取"，不做"标准化"——保留原文单位（"26,681 份" / "+1000%" / "412 份" 等）。
> `recent_3_periods` / `earlier_summary` 是司内经历主干；`before_tencent` 是入司前经历补充，不能混写成腾讯内部产出。

---

## 4. 轴 3 · traits（是个怎样的人）

```json
{
  "summaries": [
    {
      "title": "结构化推进型",
      "summary": "能把复杂需求拆成可推进的链路，并持续拿结果校验。",
      "evidence": ["2025H2 推动 3 个核心需求落地，含 26,681 份业务量"]
    }
  ],
  "business_drive": {
    "level": "强",                  // 弱 / 中 / 强 / evidence_insufficient
    "evidence": [
      "2025H2 推动 3 个核心需求落地，含 26,681 份业务量",
      "工具体验优化带来活跃用户 +5,100"
    ],
    "scope": "across_3_periods"     // single_period / across_2_periods / across_3_periods
  },
  "learning_growth": {
    "level": "中高",
    "evidence": ["参与 HR STAR 培训", "组内分享 5 次"],
    "scope": "across_2_periods"
  },
  "influence": {
    "level": "中",
    "evidence": ["跨部门协同推动需求", "面试官培训"],
    "scope": "across_2_periods"
  },
  "style": [
    { "tag": "结构化思考", "evidence": "OKR 描述层级清晰" },
    { "tag": "数据驱动",   "evidence": "outcome 多含具体数字" },
    { "tag": "推动力强",   "evidence": "多个跨部门项目落地" }
  ],
  "captured_at": "2026-06-02T19:00:00",
  "captured_by": "llm_inference",
  "notes": [
    "evidence 主要来自最近 3 期自评，未跨越早期阶段"
  ]
}
```

提炼规则（重要）：
- `summaries` 是用户可见的“是个怎样的人”小标题来源，title 必须是动态总结，不要固定写“业务推进力 / 学习成长 / 影响力 / 风格”
- `level` 严格按 evidence 数量（≥3 强、2 中、1 弱、0 evidence_insufficient）
- `scope` 标记证据跨越的周期数，让下游知道判断稳健性
- `style` 不超过 3 个标签
- `notes` 用来给 LLM 一个"自我警示"（这个判断有什么局限）

---

## 5. motivation / blockers（可选 · 反问得到）

参照 v1 schema，结构不变：

```json
"motivation": {
  "preferred_directions": [...],
  "current_satisfaction": 7,
  "satisfaction_reason": "...",
  "anchors": [...],
  "captured_at": "...",
  "captured_by": "user_clarify"
}
```

```json
"blockers": {
  "tech_blocker": "...",
  "business_blocker": null,
  "relation_blocker": null,
  "motivation_blocker": "...",
  "captured_at": "...",
  "captured_by": "user_clarify"
}
```

---

## 6. raw_sources / cloud_sync

```json
"raw_sources": {
  "od": "raw/od.json",
  "self_assess_index": "raw/self_assess_index.json",  // listMyAssessments
  "self_assess_files": [                                 // 近 3 期 + 历史
    { "asId": "<asId>", "period": "2025H2", "path": "raw/self_assess_<asId>.json", "expanded": true },
    { "asId": "...",         "period": "2025H1", "path": "raw/self_assess_<id>.json",      "expanded": true },
    { "asId": "...",         "period": "2024H2", "path": null,                              "expanded": false }
  ],
  "tapd": "raw/tapd.json",
  "gongfeng": "raw/gongfeng.json",
  "workbuddy": "raw/workbuddy.json",
  "resume_upload": "raw/resume.txt"   // 仅 Stage B
}
```

---

## 7. 隐私分级（v2 重要）

| 分级 | 字段 | 共享策略 | 上云？ |
|---|---|---|---|
| **P0 仅本地** | self_assess 原文 / outcome 原文 / 简历附件原文 | 永不外露下游、永不上云 | ❌ |
| **P1 脱敏共享** | skills.*.evidence / experiences.recent_3_periods.outcome_metrics | 共享时只传 tag 和 metric，不传原文 | ⚠️ 仅传 metric，不传 evidence 原文 |
| **P2 自由共享** | basic.* / skills.*.tag/level/weight / experiences.earlier_summary / traits.* / motivation / blockers | 下游 skill 可直接读 | ✅ 全量上云 |

> 上云脚本必须按本表过滤；下游 skill 读 profile.json 时也必须按本表过滤。
