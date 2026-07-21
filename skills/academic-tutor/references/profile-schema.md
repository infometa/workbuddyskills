# profile / session 数据结构

> 仅在用户触发「查看/编辑 profile」「创建/继续 session」时加载本文件，常规三段式回复流程不需要。

## profile.json

```json
{
  "user_name": "可选",
  "major": "计算机科学与技术",
  "grade": "junior",
  "school_type": "211",
  "in_progress_courses": [
    {"name": "操作系统", "progress": "进度第 5 章 内存管理"},
    {"name": "算法设计", "progress": "动态规划专题"}
  ],
  "thesis": {
    "stage": "proposal",
    "topic_draft": "基于深度学习的小样本图像分类",
    "advisor_style": "严格",
    "deadline": "2026-12-15"
  },
  "preferences": {
    "tone": "neutral",
    "language": "zh",
    "max_hints": 3,
    "skip_questions_after_n_attempts": 5,
    "depth_hint": "auto"
  },
  "history_topics": [
    {"date": "2026-05-01", "topic": "傅里叶变换的物理意义"}
  ]
}
```

## sessions/<session-id>.json

```json
{
  "session_id": "sess-20260507-1530-pde",
  "started_at": "2026-05-07T15:30:00",
  "topic": "偏微分方程 - 分离变量法",
  "turns": [
    {
      "user": "热传导方程怎么用分离变量法解",
      "intent": "proof",
      "ai_response": {
        "questions": ["..."],
        "hints": ["..."],
        "next_step": "..."
      },
      "user_attempt": null
    }
  ],
  "attempt_count": 0,
  "stuck_signals": []
}
```

## 字段说明速查

| 字段 | 必填 | 说明 |
|---|---|---|
| `major` / `grade` / `school_type` | 否但强烈推荐 | Profile Anchoring 必需，缺则降级"普通学生" |
| `thesis.stage` | 论文阶段触发时必填 | 取值见 `paper-writing-stages.md` 8 阶段 |
| `preferences.tone` | 否 | `gentle` / `neutral` / `strict` / `peer`，详见 `tone-personas.md` |
| `preferences.skip_questions_after_n_attempts` | 否 | 默认 5，命中 NEVER 3 简化阈值 |
| `history_topics` | 否 | 记录最近 N 个 topic 供 anchoring 引用 |
| `attempt_count` | session 内累计 | 由 `append_turn.py` 自动维护，命中阈值触发 NEVER 11 |
| `stuck_signals` | session 内累计 | "我不会"/"算了"/"放弃" 等情绪信号，命中 NEVER 8 调档 |
