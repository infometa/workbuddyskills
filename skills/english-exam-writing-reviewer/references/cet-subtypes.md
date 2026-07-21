# CET-4 / CET-6 作文题型细分 Rubric

> v1.6.0 新增。CET 命题趋势近 5 年出现多样化，本文件按 6 种 `task_subtype` 给出**审题要点 + 典型失误清单**。

---

## 一、6 种子类型总表

| `task_subtype` | 中文 | 近期真题 | 核心审题动作 |
|---------------|------|---------|------------|
| `prompt_essay` | 命题议论文 | 常年高频 | 立论 + 论据 + 结论 |
| `proverb` | **名言警句作文** | 2006、2009、2013、2023 | **先解释内涵**，再联系实际 |
| `chart` | 图表作文 | 偶尔 | 数据 → 归因 → 对策 |
| `cartoon` | 漫画作文 | 偶尔 | 描述 → 寓意 → 评论（类似考研英一）|
| `news_report` | **新闻报告** | **2023-06 CET4 真题** | **5W1H + 第三人称客观语气** |
| `letter` | 应用文（书信/通知等）| 偶尔 | 格式 + 功能性表达 |
| `report` | 报告（如调查报告）| 偶尔 | 现象 + 数据 + 结论 |

---

## 二、`proverb` 名言警句作文

### 审题流程（与 `prompt_essay` 的关键区别）

```
┌─ Step 1：还原名言字面含义（literal meaning）─ ¶1 前半
├─ Step 2：提炼名言背后的道理（underlying message）─ ¶1 后半
├─ Step 3：举例证明该道理在现实中的体现 ─ ¶2
└─ Step 4：结合自身/当代实际，总结启示 ─ ¶3
```

**与普通议论文的差异**：不能跳过 Step 1-2 直接给观点。**"先解释后引申"**是此题型的判分核心。

### 典型真题

| 年份 | 名言 | 考查要点 |
|------|------|---------|
| 2006 | "If you want knowledge, you must toil for it." | 解释"toil"的含义 + 学习需要努力 |
| 2013 | "A smile is the shortest distance between two people." | 解释比喻 + 人际沟通 |
| 2023 | "Give a man a fish, and you feed him for a day; teach a man to fish..." | 解释"授人以鱼不如授人以渔" |

### `task_subtype = proverb` 专属检查项

| 检查项 | 合格标志 | 失误标志 |
|--------|---------|---------|
| 是否解释名言内涵 | ¶1 有 "means that" / "suggests that" / "implies that" | 直接进入论据，没解释 |
| 是否保留名言原文 | 至少有 1 次引述或明显回指 | 完全不提名言 |
| 例证与名言相关性 | 例证能明确回扣名言主旨 | 例证跑题 |
| 结尾是否回到名言 | 末段有 "This saying reminds us that..." | 结尾泛泛喊口号 |

**若以上 2+ 项不合格** → 触发 `theme_deviation` 标记，降档 1 级。

---

## 三、`news_report` 新闻报告

### 审题流程（2023-06 CET4 真题首次出现）

```
标题（简洁，5-8 词）
    ↓
导语（1-2 句，概括 5W1H）
    ↓
主体（细节展开 + 引语 / 数据）
    ↓
结尾（影响 / 后续 / 意义）
```

### `task_subtype = news_report` 专属检查项

| 检查项 | 合格标志 | 失误标志 |
|--------|---------|---------|
| 是否有标题 | 第 1 行单独为标题 | 无标题，正文直接开始 |
| 5W1H 覆盖 | ≥ 5 项（Who/What/When/Where/Why/How）| 漏 2 项以上（特别是 When/Where） |
| 第三人称客观语气 | 全篇用 he/she/they/the event | 出现 "I" / "we" 等第一人称 |
| 时态 | 过去时（事件已发生）| 全篇现在时或将来时 |
| 无主观评价 | 陈述事实，无 "I think" / "we should" | 夹带个人观点 |

**critical 失误**：

- 用第一人称写（语体完全不符）→ 触发 `register_mismatch` → 直接降至 8 档或以下
- 没有标题（新闻报告的结构硬性要求）→ 触发 `format_violation`

### 典型开头模板

```
Community Library Attracts Young Volunteers

On May 3rd, the university's community library launched a week-long
volunteer program that attracted over 200 student participants from various
departments. According to Zhang Wei, the program coordinator, ...
```

---

## 四、`cartoon` 漫画作文（CET 版）

### 与考研英一 B 节的关键区别

| 维度 | CET cartoon | 考研英一 B cartoon_standard |
|------|------------|-------------------------|
| 字数 | 120-180（CET4）/ 150-200（CET6）| 160-200 |
| 三段论深度 | 可灵活 | **必须**严格三段论 |
| 论述性要求 | 无显式要求 | 2022+ 强制要求辩证 |
| 描述段精细度 | 要素覆盖即可 | 细节忠实 + 隐喻提炼 |
| 字数惩罚 | 轻 | 低于 120 降一档 |

### `task_subtype = cartoon`（CET）专属检查项

| 检查项 | 合格标志 |
|--------|---------|
| 描述画面 | ¶1 涵盖主要要素 |
| 提炼寓意 | ¶2 或结尾点出主题 |
| 表达清晰 | 没有明显跑题 |

**不触发**考研英一 B 的三段论细粒度诊断（`paragraph_diagnosis = null`），用通用 4 维 rubric。

---

## 五、`chart` 图表题（CET 版）

CET 图表题**轻度借用**英二 B 节的图表动词库（见 [`chart-verbs.md`](chart-verbs.md)），但：

1. 不要求数据精准度像英二 B 节那么严格（容忍数据简化）
2. 结尾必须有"启示"或"建议"段（CET 要求"联系实际"）
3. 字数压力更大（CET4 120-180），描述要紧凑

---

## 六、`letter` 应用文（CET 版）

- 不做 Directions 原句照搬检测（这是**考研 A 节独有**）
- 不做 signature 强制约束（CET 相对宽松）
- 用通用 letter 模板（见 [`writing-vocabulary.md`](writing-vocabulary.md) 第五节）
- 不分 `letter_category` 细类（该细分仅考研 A 节使用）

---

## 七、`task_subtype` 自动识别规则（Skill 应用）

| Directions / 题目关键词 | 判为 `task_subtype` |
|------------------------|---------------------|
| 出现具体名言（有双引号引句 + 作者 / "saying"）| `proverb` |
| 出现 "write a news report" / "as a journalist" | `news_report` |
| 出现 "pie chart" / "bar chart" / "figure / table shows" | `chart` |
| 出现 "look at the cartoon / picture" + 漫画类描述 | `cartoon` |
| 出现 "write a letter to" / "email to" | `letter` |
| 出现 "report on" / "survey of" | `report` |
| 默认（纯命题 + 要求论述）| `prompt_essay` |

若 Directions 未给出明确指向 → Skill 回默认 `prompt_essay` 并在 `meta.note` 中注明"自动推断，若有偏差请指定"。

---

## 八、参考

- [cet4-vs-cet6.md](cet4-vs-cet6.md) — CET4/CET6 样卷差异
- [chart-verbs.md](chart-verbs.md) — 图表专用动词库
- 2006-2025 年 CET-4 / CET-6 作文真题
