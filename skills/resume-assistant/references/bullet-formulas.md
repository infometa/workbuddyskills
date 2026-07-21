# Bullet 写作公式与量化策略（v0.3.2 新增）

> **吸收来源**：`refs/resume/_picked/resume-bullet-writer/SKILL.md`（L50-198 + L353-393）
>
> **使用场景**：`mode=generate` / `rewrite` / `refine` 写 bullet 时；`mode=diff` 输出格式参考
>
> ⚠️ **重要**：本文件**故意删除**了原 skill 里 L187-190 的"故意把 60% 报成 50%"式"保守估计"——直接违反我们三维 Provenance 第一维。任何"为了不显假"而调低的数字都属编造。

---

## §1 X-Y-Z 公式（Google 风格 · 推荐默认）

```
Accomplished [X] as measured by [Y] by doing [Z]
完成了 [X 成果] · 用 [Y 指标] 量化 · 通过 [Z 行动]
```

### Before / After 例

❌ **Before**: Worked on the user signup flow.
✅ **After**: Increased signup conversion (X) by 27% (Y) by redesigning the multi-step onboarding flow with progressive disclosure (Z).

❌ **Before**: 优化了首页加载速度。
✅ **After**: 把首页 LCP 从 4.2s 降至 1.8s（X+Y）·通过引入图片懒加载 + 关键 CSS 内联（Z）·使日活 PV 提升 12%（追加业务影响）。

### 适用场景

- 技术岗 / 产品岗 / 增长岗（任何**有数字**的成果）
- bullet 长度建议：**1.5-2 行**（≈ 25-40 字中文 / 25-35 词英文）

---

## §2 STAR 与 CAR 公式

### §2.1 STAR（Situation-Task-Action-Result）

完整 STAR 是面试用 **5 句故事**；写进 bullet 时**压缩成一行**：

```
[Situation 简述背景] → [Action 你做了什么] → [Result 结果数字]
```

### §2.2 CAR（Challenge-Action-Result）· STAR 的简化版

适合**故障 / 救火 / 难题**类经历，没有"任务被分配"的语境：

```
Faced [Challenge] → [Action] → [Result]
面对 [挑战] → [行动] → [结果]
```

### §2.3 公式选择树

```
是否有可量化的成果？
├─ 有  → X-Y-Z（首选 · 最简洁）
└─ 没有
   ├─ 是"故事/协作"型（多人参与、有过程）→ STAR 压缩
   ├─ 是"故障/救火"型（短促、技术性） → CAR
   └─ 真的没数 → 见 §5 缺数策略
```

> **没有 PAR**：原 skill 文件里没有 PAR（Problem-Action-Result）的展开定义；如需类似结构请直接用 CAR。

---

## §3 Power Verbs 八类（去重后）

> 来源：`resume-bullet-writer/SKILL.md` L108-140
>
> ⚠️ **必须与 [`ai-phrase-blacklist.json`](ai-phrase-blacklist.json) 交叉对照**——下面列出的部分动词（如 spearheaded / orchestrated / leveraged）已在我们 AI 黑名单里，**不能用**。
>
> 命中 AI 黑名单的动词在表里加 ⛔ 标记，需用同义替代。

### Leadership / 领导

✅ Led, Directed, Managed, Supervised, Mentored, Coached, Guided
⛔ Spearheaded（黑名单）, Orchestrated（黑名单）

### Achievement / 成就

✅ Achieved, Delivered, Exceeded, Surpassed, Won, Secured, Earned, Attained

### Growth / 增长

✅ Increased, Grew, Expanded, Accelerated, Boosted, Scaled, Doubled, Tripled

### Improvement / 优化

✅ Improved, Enhanced, Optimized, Upgraded, Refined, Streamlined, Transformed
⛔ Revolutionized（过誉）, Reimagined（黑名单倾向）

### Creation / 创造

✅ Built, Designed, Developed, Created, Launched, Established, Founded, Pioneered
⛔ Crafted（轻度黑名单）, Architected（黑名单）

### Reduction / 降本

✅ Reduced, Decreased, Cut, Lowered, Saved, Minimized, Eliminated, Consolidated

### Analysis / 分析

✅ Analyzed, Evaluated, Assessed, Investigated, Researched, Identified, Diagnosed
⛔ Leveraged（黑名单）, Utilized（黑名单 · 用 used 替代）

### Collaboration / 协作

✅ Collaborated, Coordinated, Partnered, Aligned, Facilitated, Liaised
⛔ Synergized（黑名单）

### 中文动词（推荐）

主导 / 牵头 / 设计 / 搭建 / 落地 / 推动 / 优化 / 重构 / 提升 / 降低 / 节省 / 沉淀

⛔ 中文黑名单：赋能 / 打造 / 夯实 / 抓手 / 闭环 / 心智 / 颗粒度 / 组合拳 / 链路 / 飞轮 / 顶层设计

---

## §4 量化五维度

每条 bullet 对照下面 5 个维度自检，**至少命中 2 个**：

| 维度 | 例子（英）| 例子（中）|
|---|---|---|
| **金额（Money）**| reduced cost by $80K | 降低运维成本 80 万元 |
| **时间（Time）**| cut release cycle from 14d to 3d | 上线周期从 14 天压缩到 3 天 |
| **比例（%）**| improved CTR by 23% | CTR 提升 23% |
| **数量（Volume）**| migrated 240+ services | 迁移 240+ 个服务 |
| **质量（Quality）**| reduced P0 incidents from 8/mo to 1/mo | 月度 P0 故障从 8 起降至 1 起 |

> **第 6 个隐性维度：频率（Frequency）**——如"每周 release 5 次"——可作为缺数时的活动量替代（见 §5）。

---

## §5 缺数策略（不编造的合法做法）

### §5.1 ✅ 允许的方法（按优先级）

```
1. 主动追问用户
   "这条经历有没有具体数字？例：QPS / 用户数 / 周期 / 涉及的代码行数"
   
2. 用区间或 ~（约等于）
   "提升用户活跃约 20-30%"  / "约 ~50 个商家"
   不允许：把"60%"报"50%"假装保守

3. 用活动量代替成果量
   原：成果未知 → "每周参与 2 次架构评审"（计入活动频率）
   原：用户量未知 → "迭代 8 个版本，覆盖 4 个核心模块"

4. 用"相对比较"代替绝对数
   "上线后该模块成为 P0 故障数最少的模块"（无需具体数字）
   "比上一版迭代速度快 ≥ 1 倍"（用户能确认即可）

5. 留 ____ 占位符 + 在 Provenance 标 [需用户补]
   "为 ____ 个商家提供运营支持"
   产出底部列出全部 ____ 让用户填
```

### §5.2 ❌ 严禁的做法

- **故意低报**："实际 60% → 写 50% 显得保守"——这是编造，违反 Provenance 第一维
- **行业平均代填**："这种项目一般能省 30%，写 30% 吧"——同样编造
- **从大数瞎拆**："公司 GMV 1 亿，我负责 1/4 = 2500 万"——除非你能拿出归因证据
- **用"等"代数**："优化了用户体验等"——AI 味浓，且 ATS 不命中关键词

### §5.3 缺数时的 fallback bullet 长度

`mode=generate` 在缺数时，bullet 自动**变短**（30 字内），避免拉长后被察觉无成果：

❌ Bad: "深度参与了用户增长项目，通过精细化运营策略全方位提升了用户活跃度和留存指标。"（35 字 · 全空话）
✅ OK: "参与用户增长项目（占用户运营组 30% 工作量）。"（17 字 · 标活动量）

---

## §6 Bullet Strength Checklist

> 来源：`resume-bullet-writer/SKILL.md` L353-363。每条 bullet 写完都过一遍。

```
[ ] 1. 以强动词开头（参考 §3，避开 AI 黑名单）
[ ] 2. 包含至少 2 个量化维度（参考 §4）  · 缺数时按 §5 处理
[ ] 3. 句长 1.5-2 行（中文 25-40 字 / 英文 25-35 词）
[ ] 4. 包含工具 / 技术 / 方法（让 ATS 命中硬技能词）
[ ] 5. 包含业务影响（不只是"做了什么"，还有"带来什么"）
[ ] 6. 不用第一人称（"I" / "我"开头删掉）
[ ] 7. 时态：现职用现在时 / 离职用过去时（中英都遵守）
[ ] 8. 没命中 AI 黑名单 ≥ 6 次
```

---

## §7 输出格式（用于 `mode=diff` / `rewrite`）

> 来源：`resume-bullet-writer/SKILL.md` L364-393

每条改动按以下 4 段展示给用户复核：

```markdown
## Bullet #N · {经历标题 / Bullet 序号}

**Original**:
> 优化了首页性能。

**Issues**:
- ❌ 无量化（违反量化第 4 维）
- ❌ 动词"优化"过于泛（参考 §3 推荐"重构 / 重设计"）
- ❌ 无技术细节（ATS 命中率低）

**Improved**:
> 将首页 LCP 从 4.2s 降至 1.8s（57% 提速），通过图片懒加载 + 关键 CSS 内联实现，使日活 PV 提升 12%。

**What Changed**:
- 加入量化（57% / 4.2s→1.8s / 12%）— [Provenance: 数据由用户在 2026-04-27 18:32 确认]
- 替换动词"优化" → "降至 ... 通过 ... 实现"
- 补技术细节（图片懒加载 / 关键 CSS 内联）— 来自原素材项目描述
```

`What Changed` 段必须**逐项标 Provenance**：数字哪来 / 动词为什么换 / 细节是不是用户原话。

---

## §8 NEVER

- **NEVER** 在 bullet 里同时使用 ≥ 2 个 AI 黑名单动词（如 "Spearheaded ... by leveraging ..."）
- **NEVER** 故意低报数字"显得保守"（编造的子集）
- **NEVER** 把 STAR 完整 5 句直接放进 bullet（变成段落，不是 bullet）
- **NEVER** 把 bullet 写成第一人称（"我做了 ..."）
- **NEVER** 同一段经历内 ≥ 3 个 bullet 用同一个开头动词（看着像 AI 批量生成）
