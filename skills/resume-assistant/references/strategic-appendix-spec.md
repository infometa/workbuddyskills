# 简历后战略附录规格（v0.3.2 新增）

> **吸收来源**：`refs/resume/_picked/tailored-resume-generator/SKILL.md` §7 Strategic Recommendations（L252-271）+ `refs/resume/_picked/interview-prep-generator/SKILL.md` §Questions to Ask（L232-255）
>
> **使用场景**：`mode=tailor` 完成主体后，**默认**在 `resume-output/<version>/` 下产出额外文件 `strategic-appendix.md`，让用户拿到的不只是简历、还有后续投递与面试准备的"教练包"。
>
> **可关闭**：用户在 preflight 里说 "只要简历，不要附录" → 跳过本流程

---

## §1 附录的 4 个固定章节

```
strategic-appendix.md
├── §1  Strengths to Emphasize（投递时强调什么）
├── §2  Gap Analysis（差距与缓解）
├── §3  Interview Prep Tips（面试准备建议）
└── §4  Cover Letter Hooks（求职信切入点）
```

每个章节**严格遵循 Provenance**：所有内容必须可溯到（a）原简历素材，或（b）JD 原文，**不能凭空生成**"建议补一门 XXX 课程"这种用户没说过的事。

---

## §2 章节模板（直接拷贝，按 JD/简历填入）

### §2.1 Strengths to Emphasize

```markdown
## §1 投递时强调的 3-5 个优势

按 JD 优先级匹配你的现有素材，建议你在沟通环节（推荐信 / Cover Letter / 面试自我介绍）重点提到：

1. **{strength_1}** — 命中 JD §{P1_item} `{JD 关键词}`
   - 简历对应：{经历段落 / bullet 序号}
   - 量化锚点：{具体数字}
   - 引文：> "{用户原始素材片段 ≤ 30 字}"

2. **{strength_2}** — 命中 JD §{P1_item}
   - ...

3. ...
```

**Provenance 要求**：每条 strength 都要标"命中 JD 哪条 P1/P2 + 简历对应哪段"。

### §2.2 Gap Analysis

```markdown
## §2 差距分析（按 JD P1/P2/P3 分层）

### P1 必备项（建议先补再投）

| JD 要求 | 你的现状 | 缓解建议（仅当来自用户素材或公开课程时给出）|
|---|---|---|
| {P1_req_A} | ❌ 未命中 | {建议}（来源：{用户提及 / 公开课 / 留空待补}）|
| {P1_req_B} | ⚠️ 部分相关 | 重述简历里 {经历名} 突出与该项目的关联 |

### P2 重要项（可弱命中）

| JD 要求 | 你的现状 | 缓解建议 |
|---|---|---|
| ... | ... | ... |

### P3 加分项（不影响进面试）

无需特别补足，面试时如有则提，没有则跳过。
```

**P0 原则**：缓解建议**必须**给"来源"——用户原话提过的、公开 MOOC、显式可验证。**NEVER** 凭空建议"考个 PMP"或"读读《xxx》这本书"等用户没说要做的事。

### §2.3 Interview Prep Tips

```markdown
## §3 面试准备建议（轻量版）

### §3.1 高概率出现的 3 个行为题

基于你的简历内容 + JD 关键词，预测面试官最可能问：

1. "{predicted_question_1}"
   - 建议用 STAR 回答 · 推荐故事来源：简历 §{经历段落}
   - Result 部分突出：{量化锚点}

2. "{predicted_question_2}"
   - ...

3. ...

### §3.2 单 bullet → STAR 扩写示例（取你最强的一条）

**简历 bullet**：
> {pick 一条用户简历里最强的 bullet，原文}

**面试时 STAR 扩展**（90 秒版本）：
- **Situation**：{扩展，必须基于用户提供的项目背景，不编造}
- **Task**：{用户负责的部分，不编造分工}
- **Action**：{用户实际做的，从素材引}
- **Result**：{已知数字 + 后续业务影响}

> 提示：本扩写中所有事实都来自你的简历素材；面试前请按真实记忆补 1-2 个细节让故事更生动。

### §3.3 Questions to Ask（反问，分对象）

> 来源：`interview-prep-generator/SKILL.md` L232-255。**避免问"福利 / 加班 / 升职速度"**这类侵略性问题。

**问 HR**：
- "团队当前最大的挑战是什么？"
- "新人入职 90 天的预期是什么？"

**问未来直属上级 / 团队**：
- "您希望这个职位的人在头 6 个月做出什么具体成果？"
- "团队当前的技术债 / 业务难点排在哪些方向？"

**问高管 / 二面（按需）**：
- "公司未来 1-2 年在 {JD 提到的业务方向} 上的投入逻辑是什么？"
```

> **重要边界**：本附录只给"轻量版"面试准备（≤ 1 屏内容）。完整面试准备包（题库 / 公司调研 / 模拟面试）属于未来 `mock-interview` 兄弟 skill 的职责，不在 `resume-assistant` 的范围内。

### §2.4 Cover Letter Hooks

```markdown
## §4 求职信切入点（3 个 hook 候选）

> 这些是**短句切入**，不是完整 Cover Letter。完整 CL 请用专门的 skill。

### Hook A：技能 → 业务对接型

> "{1-2 句开场}：在 {经历名} 中，我用 {技术 / 方法} 解决了 {对方业务里类似的痛点}，这正是 {目标公司} {JD 业务方向} 当前需要的。"

### Hook B：故事 → 文化共鸣型

> "{1-2 句开场}：{用户简历里某个体现"主动 / 学习 / 协作"的小故事开头}，与贵司公开提到的 {JD 描述里的文化关键词} 高度共鸣。"

### Hook C：数据 → 成果驱动型

> "{1-2 句开场}：过去 X 年我把 {指标} 提升 {Y%} / 节省 {$Z}，希望把这套方法带到 {目标公司}。"

> 选哪个？建议同一份 JD 准备 A + C 两条；HR 端用 A，业务端用 C。
```

**Provenance 要求**：每个 hook 用到的"故事 / 数据"必须有**简历对应行**，附录底部统一附引文（`from_field` + `text`）。

---

## §3 附录元数据 / 顶部 Header

```markdown
<!--
appendix-version: 1.0
generated-at: 2026-04-27T15:30:00+08:00
linked-resume-version: v3_tailor_byte_llm_algo
linked-jd-source: refs/jd-byte-llm.md
provenance-mode: strict   (所有事实必须可追溯, 不允许 inferred)
-->

# {目标公司} {岗位} · 投递战略附录

本附录基于：
- 简历版本：[`resume-zh.md`](./resume-zh.md) · 派生自 `_master`
- JD 来源：{JD 文件路径或 URL}

附录内容仅作"教练建议"，不修改简历主体；所有建议都标注来源，可逐条核对。
```

---

## §4 Provenance & 不编造规则

| 章节 | 必须可追溯到 | 不允许 |
|---|---|---|
| §1 Strengths | 简历素材片段 + JD 原文行 | 自创"领导力"等 JD 没提的优势 |
| §2 Gap | JD P1/P2/P3 + 简历事实 | 凭空建议补什么课、读什么书（除非用户素材里提过）|
| §3.1 Predicted Q | JD 要求 + 简历经历 | 编造面试官口吻的具体提问句（用模板化句式即可）|
| §3.2 STAR 扩写 | 简历原 bullet + 用户提供的项目背景 | 编造"我加班到凌晨三点"等戏剧化情节 |
| §3.3 Questions to Ask | 通用清单（已审核去除"侵略性"问题）| 编造"听说贵司即将上市"等需要内幕的问题 |
| §4 Cover Hooks | 简历事实 + 公司公开信息（标注来源）| 编造"我从小就喜欢贵司产品"等 |

---

## §5 输出文件位置

```
resume-output/
└── <version_label>/
    ├── resume-zh.md
    ├── resume-en.md (如 language=both)
    ├── result.json
    ├── provenance-audit.json
    ├── diff-report.md
    └── strategic-appendix.md   ← 本规格生成
```

---

## §6 NEVER

- **NEVER** 在附录里"假设"用户简历没说的事实（"看你做过电商，应该懂 GMV"——除非简历里出现过 GMV）
- **NEVER** 把附录写成"励志 / 鸡汤"段落（保持"教练 + 数据"风格）
- **NEVER** 在 §3 Interview Prep 段塞完整题库（≥ 10 个题就该转兄弟 skill）
- **NEVER** 在 §4 Cover Letter Hooks 给完整 CL（只给 1-2 句开场 hook）
- **NEVER** 在 §2 Gap 段建议"伪造经历来补 P1"（哪怕用"轻微夸张"也不行）
- **NEVER** 在附录里改简历主体内容（附录是只读建议，不是 diff）
