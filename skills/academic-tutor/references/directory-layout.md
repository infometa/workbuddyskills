# academic-tutor 目录结构

> 仅在用户问「目录是怎样的」「文件结构」「这个 skill 含哪些脚本」时加载本文件。

```
academic-tutor/
├── SKILL.md
├── _skill_meta.json
├── references/
│   ├── socratic-question-bank.md     # 苏格拉底式提问模板（按学科 / 场景）
│   ├── hint-strategies.md            # 提示策略（如何不给答案给到位）
│   ├── intent-classifier.md          # 意图分类决策树
│   ├── three-segment-rubric.md       # 三段式回复自评 rubric
│   ├── paper-writing-stages.md       # 论文 8 阶段模板（选题→答辩）
│   ├── attachment-handling.md        # 附件解析约束（不做 OCR / PDF）
│   ├── tone-personas.md              # 4 种人设语调参数
│   ├── refusal-boundaries.md         # 越界拒答标准话术
│   ├── profile-schema.md             # profile / session 数据结构（拆出）
│   ├── scene-examples.md             # A/B/C 三类典型场景示范（拆出）
│   ├── directory-layout.md           # 本文件（目录结构）
│   └── testing-and-eval.md           # 端到端冒烟测试 + 评测说明（拆出）
├── scripts/
│   ├── init_profile.py               # 初始化用户 profile
│   ├── update_profile.py             # 更新专业/年级/课程/论文进度
│   ├── new_session.py                # 开启对话会话
│   ├── append_turn.py                # 追加一轮对话到会话
│   ├── classify_intent.py            # 意图分类（启发式 + 关键词）
│   └── render_three_segments.py      # 三段式回复装配 / 校验
├── tests/
│   └── integration_test.py           # 端到端：profile→session→3 轮对话→归档
├── evals/
│   ├── evals.json                    # 6 用例（5 happy + 1 越界）
│   └── trigger-eval.json             # 触发率：8 should + 8 should-not
└── assets/
```

## 数据目录（运行时生成，不在 skill 包内）

```
~/.workbuddy/data/academic-tutor/        # 默认数据目录（跨平台稳定）
├── profile.json                          # 当前用户 profile
├── sessions/                             # 历史会话归档
│   └── sess-YYYYMMDD-HHMM-<topic>.json
└── archive/                              # 已结束会话只读副本（按月归档）
```

> ⚠️ 数据目录可通过环境变量 `ACADEMIC_TUTOR_DATA_DIR` 覆盖。保留 `~/.workbuddy/` 而非 `.codebuddy/`
> 是有意的：用户家目录跨 skill 迁移稳定，避免 skill 移动 / 重装时丢数据。
