# 写作词汇升档库（Writing Vocabulary Upgrade Library）

> 目的：为 Step 6 的 `upgrade_path` 提供**具体、可直接替换**的词汇/短语建议。
> 来源：基础款基于 `kaoyan-english-writing` Skill（Treasoni/kaoyan_skills，MIT），针对 CET-4 / CET-6 / 考研一 / 考研二分级扩充并做适配。
> **使用原则**：只做"替换建议"，不做"逼迫使用"。若学生原句已足够地道，不要机械升档；避免堆砌。
>
> **最后更新**：2026-04-22 · v1.0

---

## Contents

- [分级速查](#分级速查)
- [一、议论文高频词：表达观点](#一议论文高频词表达观点think--believe--state-家族)
- [二、议论文高频词：表示重要性/必要性](#二议论文高频词表示重要性--必要性)
- [三、议论文高频词：因果/转折/让步](#三议论文高频词因果--转折--让步)
- [四、图表作文专用词](#四图表作文专用词考研英语二-b-节--cet-图表题)
- [五、应用文高频模板](#五应用文书信--通知--告示--纪要高频模板)
- [六、考研专属：论述性文章（英一 B 节）加分表达](#六考研专属论述性文章英一-b-节加分表达)
- [七、风险词表](#七风险词表要谨慎使用)
- [八、Step 6 自动升级算法](#八step-6-自动升级算法伪代码)
- [九(b)、CET 特殊子类套话](#九bcet-特殊子类套话v160-新增)
- [九(c)、A 节功能性信函专属](#九ca-节功能性信函专属v160-新增)

---

## 分级速查

- **Low-tier**：基础词，CET-4 2/5 档的典型用词，四级 8 档以下安全可用
- **Mid-tier**：CET-4 11 档 / CET-6 8 档 / 考研三档级别应达到的用词水平
- **High-tier**：CET-4 14 档 / CET-6 11 档 / 考研四档级别开始稳定出现
- **Academic-tier**：CET-6 14 档 / 考研五档、雅思 7.0+，慎用且必须搭配得当

> 定档建议（给 Step 6 upgrade_path 自动挑词时参考）：
> | 目标档 | 合理选择 |
> |-------|---------|
> | CET-4 升到 11 | low → mid |
> | CET-4 升到 14 | mid → high，零星 academic |
> | CET-6 升到 14 | high 为主 + 若干 academic |
> | 考研升到四/五档 | high + academic，注重搭配自然性 |

### v1.6.0 新增：按考试打「最低达标 tier」（英一 vs 英二精细化）

| 目标 band | CET-4 | CET-6 | 考研英一 | 考研英二 |
|----------|-------|-------|---------|---------|
| 二档（偏弱）| low | low-mid | low-mid | low |
| 三档（中等）| mid | mid | mid-high | mid |
| 四档（良好）| mid-high | high | high | mid-high |
| **五档（优秀）** | **high**（零星 academic）| **high + academic** | **academic** | **high** |

**关键差异**：**同一篇作文在英一是 4 档、在英二可能是 5 档**（英二词汇门槛低 0.5 个 tier）。Skill 切换 `exam_level` 时必须同步切换目标 tier。详见 [postgrad1-vs-postgrad2.md](postgrad1-vs-postgrad2.md) 第三节。

---

## 一、议论文高频词：表达观点（think / believe / state 家族）

| Low-tier | Mid-tier | High-tier | Academic-tier | 典型搭配 |
|---------|---------|-----------|---------------|---------|
| think | believe / hold | contend / maintain | posit / postulate | Many scholars **contend** that... |
| say / state | argue / claim | assert / insist | advocate / contend | Critics **assert** that... |
| show / tell | indicate / suggest | demonstrate / reveal | exemplify / typify | This case **exemplifies**... |
| agree / support | endorse | affirm | espouse | I **affirm** the view that... |
| don't agree | disagree / dispute | refute / challenge | repudiate / debunk | This view can be **refuted** by... |

**Skill 常见误用提醒**：

- `contend` / `posit` 适用于**他人观点**或**学术引述**；学生谈自己看法多数情况下用 `argue` / `maintain` 即可。
- 过度使用 `exemplify` 会让句子冗长，CET-4 14 档推荐最多 1 处。

---

## 二、议论文高频词：表示重要性 / 必要性

| Low-tier | Mid-tier | High-tier | Academic-tier | 例句 |
|---------|---------|-----------|---------------|------|
| important | significant / essential | crucial / vital / indispensable | imperative / paramount | It is **crucial** to address this issue. |
| necessary | needed / required | essential | imperative / requisite | It is **imperative** that we take action. |
| big / large | significant / considerable | substantial / profound | far-reaching / seismic | have a **profound** impact on... |
| very big | remarkable / striking | phenomenal / momentous | epochal | a **momentous** change in society |

---

## 三、议论文高频词：因果 / 转折 / 让步

### 因果

| Low-tier | Mid-tier | High-tier |
|---------|---------|-----------|
| because | due to / owing to | attributable to / stem from |
| so | therefore / thus | consequently / accordingly |
| reason | cause | factor / catalyst |
| result | consequence / outcome | ramification / repercussion |

### 转折

| Low-tier | Mid-tier | High-tier |
|---------|---------|-----------|
| but | however / yet | nevertheless / nonetheless |
| although | despite / in spite of | notwithstanding |
| on the other hand | conversely | by contrast |

### 让步

| Low-tier | Mid-tier | High-tier |
|---------|---------|-----------|
| even though | granted that | admitting that |
| still | yet | even so |

---

## 四、图表作文专用词（考研英语二 B 节 / CET 图表题）

### 数据变化动词（上升）

| Low-tier | Mid-tier | High-tier |
|---------|---------|-----------|
| go up / rise | increase / grow | climb / ascend / escalate |
| jump | rise sharply | soar / surge / skyrocket |

### 数据变化动词（下降）

| Low-tier | Mid-tier | High-tier |
|---------|---------|-----------|
| go down / fall | decrease / drop | decline / descend / dwindle |
| drop sharply | fall steeply | plummet / plunge / nosedive |

### 数据变化动词（波动 / 稳定）

| 含义 | Mid-tier | High-tier |
|------|---------|-----------|
| 波动 | vary / change | fluctuate / oscillate |
| 稳定 | stay / keep | stabilize / level off / remain constant |
| 达到峰值 | reach the top | peak at / hit a record high |
| 触底 | reach the bottom | bottom out / hit a record low |

### 程度修饰（描述数据）

| Low-tier | Mid-tier | High-tier |
|---------|---------|-----------|
| big | significant / considerable | substantial / profound |
| small | moderate | marginal / negligible |
| steady | gradual | incremental |
| fast | rapid | dramatic / precipitous |

### 句式模板（考研英语二图表作文常用）

1. **总描**：As is vividly depicted in the chart, the number of X **surged from** A in Year 1 **to** B in Year 2.
2. **对比**：By contrast, Y **exhibited a downward trajectory**, **dwindling from** C **to** D over the same period.
3. **峰谷**：X **peaked at** A in Year 1, only to **bottom out at** B three years later.
4. **因果归纳**：The fluctuation **can be attributable to / is a direct consequence of** + 名词短语.

---

## 五、应用文（书信 / 通知 / 告示 / 纪要）高频模板

> 考研 A 节 + CET 应用文通用。按"语域 register"分层：正式 (formal) / 半正式 (semi-formal) / 口语 (casual)。
> **规则**：CET / 考研应用文默认**半正式到正式**，避免 casual。

### 开头句

| 用途 | Low-tier / casual | High-tier / formal |
|------|------------------|--------------------|
| 询问 | I want to ask about... | I am writing to **inquire about**... |
| 申请 | I want to apply for... | I am writing to **apply for** the position of... |
| 投诉 | I am writing to complain... | I was **dismayed** / **disappointed** to learn that... |
| 感谢 | Thank you for... | I would like to **express my appreciation for**... |
| 建议 | I want to suggest... | I am writing to **put forward some suggestions regarding**... |
| 推荐 | I recommend... | I am writing to **wholeheartedly recommend**... |

### 过渡 / 正文展开

| 用途 | Mid-tier | High-tier |
|------|---------|-----------|
| 给理由 | I think this because... | The reason is twofold. **First and foremost**,... |
| 举例 | For example... | A **case in point** is... / **To illustrate**,... |
| 补充 | Also,... | **What is more**, / **In addition to** + 名词短语,... |

### 结尾句

| 用途 | Mid-tier | High-tier |
|------|---------|-----------|
| 期待回复 | Please reply to me. | I **look forward to your prompt response**. |
| 愿提供信息 | Tell me if you need more info. | Please let me know if you require **any further information**. |
| 感谢协助 | Thank you for your help. | Your assistance in this matter is **greatly appreciated**. |

### 落款（格式要求）

- **书信**：Sincerely, / Yours sincerely, / Yours faithfully, + Li Ming / Zhang Wei（不写真名，**必须用题目指定的 signature**；考研大纲明确若出现真实姓名扣分）
- **通知**：Student Union / The Employment Office / 具体发文单位

---

## 六、考研专属：论述性文章（英一 B 节）加分表达

> 2022 年起考研英语一 B 节要求从"议论性"升级为"**论述性**"，对逻辑论证要求更高。
> 以下为论述性文章的高阶表达。

### 引出观点 / 立论

- **It is widely acknowledged that...** / **It is universally held that...**
- **Conventional wisdom holds that..., yet closer scrutiny reveals...**
- **The phenomenon epitomizes / underscores the broader trend of...**

### 辩证 / 反驳

- **Admittedly,** X has its merits; **nevertheless**,...
- **While proponents argue that...**, **critics counter that...**
- **This argument, however compelling on the surface, overlooks the fact that...**

### 归纳 / 总结

- **In light of the foregoing analysis,** we may reasonably conclude that...
- **By way of conclusion, / To bring the discussion full circle,**...
- **The crux of the matter lies in...**

---

## 七、风险词表（要谨慎使用）

> 以下词汇在中国学生作文中经常被误用，在 Skill 的 `issues` 检查里作为 `severity: tip` 标记。

| 风险词 | 常见误用 | 安全替换 |
|--------|---------|---------|
| obvious / obviously | 滥用作为万能衔接词 | clearly / evidently / it is apparent that |
| so | 作为弱衔接 | therefore / consequently / as a result |
| very / really | 程度修饰过于口语 | considerably / remarkably / substantially |
| many people | 指代模糊 | a growing number of citizens / many observers |
| very important | 两级词叠加 | crucial / vital（单词本身已含"很"的程度）|
| according to me | Chinglish 搭配 | in my view / from my perspective |
| all in all | 轻微口语 | in conclusion / to sum up |
| with the development of society | 万能开头，被严重滥用 | 改用具体现象开篇 |
| play an important role | 被严重滥用 | be instrumental in / serve as a cornerstone of |

---

## 八、Step 6 自动升级算法（伪代码）

```python
def suggest_vocabulary_upgrades(essay, band, target_band, exam_level):
    """
    扫描作文中的 low-tier 词，给出 target_band 级别应使用的替换。
    返回：List[{"original": str, "suggestion": [str], "tier_from": str, "tier_to": str, "location": str}]
    """
    tier_map = load_tier_map("writing-vocabulary.md")
    target_tier = map_band_to_tier(band=target_band, exam_level=exam_level)
    # band→tier 映射表：
    #   CET4-11 / CET6-8 / 考研三档 → mid
    #   CET4-14 / CET6-11 / 考研四档 → high
    #   CET6-14 / 考研五档         → academic

    suggestions = []
    for sentence in tokenize_sentences(essay):
        for word in sentence.words:
            if word.tier < target_tier:
                higher_candidates = tier_map.higher_than(word, target_tier)
                if higher_candidates:
                    suggestions.append({
                        "original": word.text,
                        "suggestion": higher_candidates[:3],  # 最多 3 个候选
                        "tier_from": word.tier,
                        "tier_to": target_tier,
                        "location": sentence.location,
                    })

    # 限制总量：避免堆砌 —— 最多 5 条升级建议
    return rank_by_impact(suggestions)[:5]
```

**关键约束**：

1. **一篇 essay 最多建议 5 条词汇升级**，避免"改面目全非"。
2. 一个词已经在 high-tier 就不必再升级到 academic-tier（除非目标是 CET-6 14 档或考研五档）。
3. 搭配校验：替换后必须搭配自然（如 `make` → `exemplify` 不能机械替换，要结合上下文）。
4. 避免同一词在 essay 中用 2 次就提 2 条建议——**同一词的升级建议只出 1 次**。

---

## 九(b)、CET 特殊子类套话（v1.6.0 新增）

### 9b.1 `news_report` 新闻报告（2023-06 CET4 真题）

**标题**（5-8 词，首字母大写，名词短语，**不加冠词**）：

> ✅ `Community Library Attracts Young Volunteers`
> ❌ `A news report about the community library` （冗长、语气错）

**导语开头**（过去时 + 第三人称）：

| 层级 | 模板 |
|------|------|
| Mid | On [日期], [机构] launched / held / organized [事件]. |
| High | On [日期], a [形容词] [事件] took place at [地点], **drawing** [数量] participants. |
| High + 引语 | According to [职务 + 姓名], "..." |

**结尾**（影响 / 意义，避免主观评价）：

> The event is expected to **foster** a culture of reading across the community.

**严禁**：

- ❌ `I think this is good for...`（出现第一人称直接降档）
- ❌ `We should all join...`（新闻报告不做呼吁）
- ❌ `In conclusion, ...`（新闻无总结段，直接以"影响 / 后续"收尾）

### 9b.2 `proverb` 名言警句（解释 + 引申双核）

**¶1 还原 + 提炼**：

> The saying "[ ]" **literally means** that [字面]. **On a deeper level**, it **suggests** / **implies** that [道理].

**¶2 举例**：

> A case in point is [例子]. [具体事件]. This **exemplifies** the wisdom of this saying.

**¶3 回扣 + 启示**：

> This saying **reminds us** that [启示 → 现代应用].

---

## 九(c)、A 节功能性信函专属（v1.6.0 新增）

详细套话按 10 种 `letter_category` 见 [letter-categories.md](letter-categories.md)。此处仅给**新增高频类别**的核心开头，避免学生混用：

| letter_category | 开头（High-tier 模板）|
|----------------|---------------------|
| `reply` | I am writing **in reply to your letter of** [日期] **regarding** [话题]. |
| `complaint` | I am writing to **express my deep dissatisfaction with** [事由]. |
| `apology` | Please accept my **heartfelt apology** for [失误]. |

**关键**：投诉信用 `dismayed / disappointed`，**绝不用** `angry / furious`（语域失控即扣分）。

---

## 九、致谢 & 引用

- **词汇基础库**引自 `kaoyan-english-writing`（Treasoni/kaoyan_skills, commit `df68bf8`），遵循原仓库 LICENSE。
- 考研论述性文章加分表达参考 2022+ 考研英语大纲官方样卷趋势。
- CET 程度修饰分级参考批改网 2023 年度语料统计 + 教育部《大学英语四、六级考试大纲（2016 修订版）》。
