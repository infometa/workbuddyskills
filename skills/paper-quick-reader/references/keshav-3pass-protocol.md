# Keshav 三遍阅读法 · 协议文件

> 版本：v0.4.0 · P1-C  
> 适用：`paper-quick-reader` 单篇精读 / 引导模式  
> 触发：`preferences.reading_protocol = "keshav_3pass"`（默认 `auto`）  
> 来源：S. Keshav, *How to Read a Paper*, ACM SIGCOMM CCR, 2007.  
>
> **本文件只定义协议；不写实现代码。**  
> Skill 在生成 `summary_card` / `connection_points` / `deep_dive_answers` 时，
> 若协议被触发，按本文规定的 *字段填充顺序* 与 *停止条件* 工作。

## Contents

- [1. 为什么要把 Keshav 引进来](#1-为什么要把-keshav-引进来)
- [2. 三遍 × 三档 映射表](#2-三遍--三档-映射表)
- [3. 第一遍（First Pass）协议](#3-第一遍first-pass协议)
- [4. 第二遍（Second Pass）协议](#4-第二遍second-pass协议)
- [5. 第三遍（Third Pass）协议](#5-第三遍third-pass协议)
- [6. 停止条件 & 档位切换规则](#6-停止条件--档位切换规则)

---

## 1. 为什么要把 Keshav 引进来

`paper-quick-reader` 现有"三档深度（skim / guided / deep）"基于 *用户输入*
切档；Keshav 三遍阅读法基于 *论文质量与读者目标* 切档，是另一种正交的
"读得多深"策略。两者**不冲突**：

| 维度 | 当前三档 | Keshav 三遍 |
|---|---|---|
| 切档信号 | 用户是否提供 `my_direction` / `specific_question` | 第一遍读完后 *论文质量信号* |
| 主张 | 用户输入决定深度 | 论文价值决定深度 |
| 适用场景 | Agent 自动调档 | 学生/研究者主动决定要不要继续读 |
| 输出风格 | 一次产出多档结果 | 分轮产出，每轮可主动停 |

引入 Keshav 协议的产品价值：让 Skill 在 *第一遍后给出"是否值得继续读"
的判断信号*，让用户基于价值决策，而不是机械读完整篇。

---

## 2. 三遍各自职责

### 第一遍 · Skim Pass（5–10 分钟级）

**目标**：判断这篇论文 *是否值得读第二遍*。

**只看**：
- Title、Abstract、Introduction
- 所有 Section 与 Sub-section 标题
- Conclusion（如果存在）
- Bibliography（粗扫熟悉度）

**产出（强制 5C 字段）**：
1. **Category**：论文类型（measurement / analytical / system / theory / survey ...）
2. **Context**：与哪些已知论文相关？基于什么理论假设？
3. **Correctness**：假设是否合理（Abstract+Intro 层面）？
4. **Contributions**：主要贡献（论文自己声明的，逐条列出）
5. **Clarity**：写作清晰度（粗判 → 影响是否值得读第二遍）

**停止条件**（任一为真则停在第一遍）：
- Category 不在用户感兴趣范围
- Contributions 与用户 `my_direction` 完全无关
- Clarity 极差（例如 Abstract 都看不懂关键假设）

**Skill 实现映射**：第一遍 ≈ 现有 `summary_card`（裸读 6 字段），
但**额外强制**给出"是否建议读第二遍"信号字段：

```json
{
  "keshav_pass1": {
    "category": "measurement",
    "context_papers": ["[1]", "[3]", "[5]"],
    "correctness_assessment": "假设合理 / 存疑 / 不合理",
    "contributions_self_claimed": ["...", "..."],
    "clarity_score": 4,
    "recommend_pass2": true,
    "stop_reason": null
  }
}
```

### 第二遍 · Detail Pass（约 1 小时级）

**目标**：抓住论文 *内容主线*；理解到能 **向他人复述** 的程度。

**只看**：
- 图、表、其他 visual aid（**重点**：figure caption + 数据来源 + axis 是否合理）
- Marked references（特别是用户不熟的引文 → 加入"以后要读"清单）
- 跳过证明 / 推导细节
- 跳过实现细节

**产出**：
- 论文 *核心论点* 的复述（≤ 200 字）
- *证据链*：哪些图/表支撑哪个论点（图号 → 论点的映射）
- *未读引文清单*：需要先读哪些 background paper 才能完整理解
- *疑点*：第二遍理解不了的地方（标记给第三遍 / 或决定不读第三遍）

**停止条件**（任一为真则停在第二遍）：
- 已经能 summarize main thrust → 第二遍目标达成
- 论文超出用户当前知识储备 → 先去读 background → 暂停
- 与 `my_direction` 关联只到"借鉴 idea"层面（不需要复现）

**Skill 实现映射**：第二遍 ≈ 现有 `connection_points` + `deep_dive_answers`
（part of），但**额外要求**：

```json
{
  "keshav_pass2": {
    "main_thrust_restatement": "...",
    "evidence_chain": [
      {"claim": "...", "evidence": "Figure 3", "page": 5}
    ],
    "background_reading_list": [
      {"ref_idx": "[12]", "raw": "Smith et al, 2020", "why_needed": "理解 baseline 推理需要"}
    ],
    "open_questions_for_pass3": ["..."],
    "recommend_pass3": false,
    "stop_reason": "已能复述主线，无需复现"
  }
}
```

### 第三遍 · Virtual Re-implementation Pass（多小时 ~ 数天级）

**目标**：在脑中 *复现* 这篇论文 → 找出 *隐含假设* + *漏洞*。

**只看**：每一处假设、每一个推导步骤、每一处实验设置。

**产出**：
- 隐含假设清单（论文没明说但默认成立的）
- 你的复现版本与论文版本的差异（如果你重做这个工作会怎么改）
- 引用文献中的相关 idea（论文没引但本应引）
- Future work 的具体走向（不是论文 conclusion 那种空泛"未来工作"）

**停止条件**：
- 这篇是你的 reviewer 任务 / 直接 baseline → 必须读完
- 否则第二遍后多数情况不需要第三遍

**Skill 实现映射**：第三遍 ≈ 现有 `deep_dive_answers` + `peer_review`
（v0.2.0 引入的博导审稿视角），但**额外要求**：

```json
{
  "keshav_pass3": {
    "implicit_assumptions": ["..."],
    "reimplementation_diff": "...",
    "missing_citations": [{"topic": "...", "should_cite": "...", "why": "..."}],
    "concrete_future_work": ["..."]
  }
}
```

---

## 3. 与 `paper-quick-reader` 现有架构的关系

**协议级整合（不改 schema 主结构）**：

| 三档深度（输入信号） | Keshav 三遍（论文价值信号） | 组合输出 |
|---|---|---|
| `[skim]` | pass1 only | summary_card + 5C |
| `[skim, guided]` | pass1 + pass2-lite | summary_card + 5C + connection_points + main_thrust |
| `[skim, deep]` | pass1 + pass2 + pass3 | full + implicit_assumptions |
| `[skim, guided, deep]` | pass1 + pass2 + pass3 + peer_review | 上述全部 + 审稿视角 |

**关键约定**：
1. 三遍法**不替代**现有的 `summary_card` / `deep_dive_answers`，而是
   *额外增强* `keshav_pass{1,2,3}` 字段（向后兼容，老调用方读不到这些字段
   也不会坏）。
2. `recommend_pass2` / `recommend_pass3` 是 *建议*，不是 *强制中断*——
   用户仍可通过 `preferences.depth_hint = "force_deep"` 跑完三遍。
3. 第一遍的 `stop_reason` 必须是用户可读的 *人话*，不是错误码。

---

## 4. 输出 schema 增量（可选字段）

```jsonc
"papers": [
  {
    // ...现有字段...
    "keshav_3pass": {
      "protocol_version": "0.4.0",
      "pass1": {
        "category": "...",
        "context_papers": ["[1]", ...],
        "correctness_assessment": "...",
        "contributions_self_claimed": ["...", ...],
        "clarity_score": 1-5,           // 1=不可读, 5=极清晰
        "recommend_pass2": true|false,
        "stop_reason": null|"..."
      },
      "pass2": null | {                  // null 表示协议在 pass1 后停止
        "main_thrust_restatement": "...",
        "evidence_chain": [...],
        "background_reading_list": [...],
        "open_questions_for_pass3": [...],
        "recommend_pass3": true|false,
        "stop_reason": null|"..."
      },
      "pass3": null | {
        "implicit_assumptions": [...],
        "reimplementation_diff": "...",
        "missing_citations": [...],
        "concrete_future_work": [...]
      }
    }
  }
]
```

**硬约束**：
- `pass1` 必填（一旦协议被触发）
- `pass1.recommend_pass2 == false` ⇒ `pass2` 必须为 `null`
- `pass2` 存在 ⇔ `recommend_pass2 == true`（同上对 pass3）
- `clarity_score` ∈ [1, 5]，整数
- `stop_reason` 与 `recommend_*` 互斥：recommend=true 时 stop_reason 必须为 null

---

## 5. 触发与降级

**触发**：
- 显式：`preferences.reading_protocol = "keshav_3pass"`
- 隐式（auto）：暂不开启，**必须显式触发**避免增加默认 token 成本

**降级**：
- 协议无法判定 `category` → 写 `"unknown"` 而非编造
- `bibliography` 为空（image-only PDF 等）→ `context_papers = []` + warnings 记录
- `clarity_score` 不可判（短摘要） → 写 `null` 但 *不允许* 漏字段

---

## 6. NEVER

- **NEVER** 在没有显式 `reading_protocol = "keshav_3pass"` 时主动产出
  `keshav_3pass` 字段（增加无用 token）
- **NEVER** 把现有 `summary_card` 6 基础字段替换成 `keshav_pass1.5C`——
  这是 *增量* 不是 *替代*
- **NEVER** 用三遍法做多篇对比模式（Keshav 协议是单篇语义；多篇请走
  `comparison-dimensions.md` 的 `synthesis_block`）
- **NEVER** 把 `clarity_score` 当 reviewer 给分（这只是 Keshav pass1
  内部判断 *是否值得继续读* 的信号，不是论文质量评分）

---

## 7. 实现状态

- v0.4.0：**仅协议落地**（本文件）。Skill router 不自动触发，
  保持向后兼容。
- v0.5.0+（计划）：在 `output-schema.md` 添加 `keshav_3pass` 可选字段，
  并在 `render_report.py` 增加 *Keshav-mode* 渲染分支。
