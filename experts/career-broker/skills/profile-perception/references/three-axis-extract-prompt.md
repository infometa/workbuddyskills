# 三轴提炼 prompt 模板

> 这份 prompt 是 profile-perception 的核心 LLM 步骤。把自评原文喂进去，让 LLM 按 schema 输出 skills / experiences / traits。
>
> **同时**：LLM 必须为每个标签输出**反向索引**（from/tapd），用于下游 skill 追溯。详细规格见 `compact-profile-spec.md`。

---

## 输入数据

变量：
- `{basic}` — recruit-mcp infoDetail 基础信息（部门、职位、职级、工作地、员工属性、司龄）
- `{n_periods_total}` — 历史自评总数
- `{recent_periods}` — 近 3 期完整自评 JSON（每期含 dimensions/objectives/kr/outcome/highPriority，司内经历主干）
- `{before_tencent}` — recruit-mcp infoDetail 中的 workExperiences / eduExperiences / projects（入司前经历补充）
- `{earlier_periods_titles}` — 更早 N 期的 oName 拼接（用于汇总）
- `{tapd_top}` — tapd 标签 top 10（可选，做 evidence 补充）
- `{gongfeng_languages}` — 主力语言 top 3（可选）

---

## Prompt 主体

```
你是腾讯员工的职业画像提炼助手。
我会给你某员工的基础信息、入司前经历补充和近期自评数据，请你提炼出 3 类信息：技能 / 经历 / 软性素质。自评是司内经历主干；入司前经历只做背景补充。

【基础信息】
{basic}

【入司前经历补充】
{before_tencent}

【自评总数】
全部 {n_periods_total} 期，其中近 3 期完整数据如下，更早周期只给标题。

【近 3 期完整自评】
{recent_periods}

【更早 N 期标题列表】
{earlier_periods_titles}

【辅助数据】
- tapd 高频标签：{tapd_top}
- 工蜂主力语言：{gongfeng_languages}

【输出要求】

输出严格 JSON，结构如下：

{
  "skills": {
    "technical": [
      { "tag": "...", "level": "高|中|低", "weight": 0.0-1.0,
        "evidence": ["自评原文片段 1", "..."], "source": ["self_assess"] }
    ],
    "domain": [...],
    "tools": [ { "tag": "Python", "source": "gongfeng" } ]
  },
  "experiences": {
    "recent_3_periods": [
      {
        "period_id": "...", "period_name": "...", "status": "...",
        "objectives": [
          { "index": 0, "name": "...", "key_results": "<原文>",
            "outcome": "<原文>", "high_priority": false,
            "outcome_metrics": ["数字+单位 1", "数字+单位 2"],
            "themes": ["主题词 1", "..."] }
        ]
      }
    ],
    "earlier_summary": "<100-200 字汇总，描述更早 N 期司内自评主线脉络>",
    "before_tencent_summary": "<可选，50-120 字概括入司前经历；没有则 null>"
  },
  "traits": {
    "summaries": [
      { "title": "<动态软性素质总结>", "summary": "<一句概括 + 一句证据>", "evidence": ["..."] }
    ],
    "business_drive":  { "level": "...", "evidence": [...], "scope": "across_X_periods" },
    "learning_growth": { ... },
    "influence":       { ... },
    "style": [ { "tag": "...", "evidence": "..." } ],
    "notes": ["self-warning ..."]
  }
}

【提炼规则】

1. **skills.technical** 从 KR 动作词 + 业务系统名提取，避免泛词（"沟通"、"协作"不算 technical）
2. **skills.domain** 从 oName 主题词提取（如"校招招聘"、"AI 产品"）
3. **skills.tools** 主要从工蜂语言 + 自评中明确提及的工具名（如 "Python"、"Figma"）
4. **level**：evidence ≥3 → 高，2 → 中，1 → 低；同时 highPriority=true 的 objective 加权
5. **evidence** 必须是自评原文片段，不要改写、不要美化
6. **outcome_metrics** 严格抽取数字+单位（"26,681 份" / "+1000%" / "412 份"），不做标准化
7. **earlier_summary** 100-200 字，只汇总更早司内自评主线；**before_tencent_summary** 只概括入司前经历，不要混进司内产出
8. **traits**:
   - `summaries` 是给用户看的软性素质总结，title 必须动态生成，不能固定写“业务推进力 / 学习成长 / 影响力 / 风格”。示例："结构化推进型"、"数据敏感、结果导向"、"愿意补短板的学习型"。
   - business_drive 看 outcome 是否有量化结果 + 跨周期是否持续（供内部结构化使用，不直接作为用户可见小标题）
   - learning_growth 看是否有培训 / 跨领域 / 新方向（供内部结构化使用，不直接作为用户可见小标题）
   - influence 看是否有跨部门 / 培训分享 / 推动他人（供内部结构化使用，不直接作为用户可见小标题）
   - style 最多 3 个标签，每个给 1 句 evidence
9. **scope** 标记 evidence 跨越的周期数（across_1/2/3_periods）
10. **慎重**：如果 evidence 不足，level 标 "evidence_insufficient"，**不要编造**
11. **notes** 写 1 条 self-warning（如"判断主要基于近 3 期，更早期未涵盖"）

【特别约束】

- 输出严格 JSON，不要 markdown 包裹
- 不评价员工好坏，不打总分
- 不灌鸡汤、不贴标签（"优秀"、"卓越"等评价词禁止）
- 同义合并：技能标签若已在 v1 中存在则复用，不要造新近义词
```

---

## 期望输出示例（基于真实自评数据 2025H2）

```json
{
  "skills": {
    "technical": [
      {
        "tag": "招聘系统产品设计",
        "level": "高",
        "weight": 0.9,
        "evidence": [
          "推进官网简历增加游戏经历模块改造需求设计及上线",
          "推进特殊青云录用流程改造"
        ],
        "source": ["self_assess"]
      },
      {
        "tag": "内部工具产品迭代",
        "level": "高",
        "weight": 0.85,
        "evidence": [
          "整合推进匿名池用户链路体验优化",
          "梳理内部挂号能力的业务诉求"
        ],
        "source": ["self_assess"]
      },
      {
        "tag": "AI 产品运营",
        "level": "中",
        "weight": 0.7,
        "evidence": [
          "统筹招聘 AI 产品运营",
          "针对 AI 搜索完成精细化运营及反馈收集"
        ],
        "source": ["self_assess"]
      }
    ],
    "domain": [
      { "tag": "校招招聘", "level": "高", "weight": 0.95, "evidence": ["..."], "source": ["self_assess"] },
      { "tag": "内部工具产品", "level": "高", "weight": 0.9, "evidence": ["..."], "source": ["self_assess"] },
      { "tag": "AI 招聘", "level": "中高", "weight": 0.8, "evidence": ["..."], "source": ["self_assess"] }
    ],
    "tools": []
  },
  "experiences": {
    "recent_3_periods": [
      {
        "period_id": "6919912fa78d514eca190634",
        "period_name": "2025下半年人才评估",
        "status": "AssessFinish",
        "objectives": [
          {
            "index": 0,
            "name": "校招核心业务诉求挖掘与落地",
            "outcome_metrics": ["26,681 份简历", "x 单特殊青云"],
            "themes": ["校招", "需求挖掘", "系统改造"],
            "high_priority": false
          }
        ]
      }
    ],
    "earlier_summary": null
  },
  "traits": {
    "business_drive": {
      "level": "强",
      "evidence": [
        "26,681 份简历填写量",
        "内部匿名池活跃用户 5,100+，沟通发起 3,786 次（消息量 +1000%）",
        "412 份集体面试报告 / 84.9% 落位准确率"
      ],
      "scope": "across_1_periods"
    },
    "learning_growth": {
      "level": "中高",
      "evidence": [
        "参与 HR STAR 培训",
        "AI 时代新的产品创新组织研究 - 美图组织研究",
        "对外智能问询产品建设方案设计"
      ],
      "scope": "across_1_periods"
    },
    "influence": {
      "level": "中",
      "evidence": [
        "协同校招业务及研发多次沟通推进用工类型改造",
        "组织面试官能力建设 - 207 位面试官覆盖"
      ],
      "scope": "across_1_periods"
    },
    "style": [
      { "tag": "结构化思考", "evidence": "OKR 描述层级清晰，KR 拆分明确" },
      { "tag": "数据驱动",   "evidence": "outcome 中多次给出具体业务数字" },
      { "tag": "推动力强",   "evidence": "多个跨部门项目最终落地" }
    ],
    "notes": [
      "判断主要基于近 1 期自评（仅 1 期完整数据），跨周期稳健性待补"
    ]
  }
}
```
