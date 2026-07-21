# Chinglish 模式与校正

> 收录中→英学术翻译中的高频 Chinglish 表达与对应修正。

## 词级问题

| Chinglish | 推荐译法 | 解释 |
|---|---|---|
| in recent years（滥用） | recently / 直接删除 | 直译"近年来"，不要每段都用；多数情况下不必加时间标记 |
| nowadays | recently / today | 太口语，论文一般避免 |
| with the development of | as / due to / 改写 | "随着...的发展" 套话，常空洞 |
| play an important role | （视语境改写） | "起重要作用" 模糊；改为具体动作描述 |
| more and more | increasingly | "越来越" 直译 |
| discuss about | discuss | discuss 是及物动词，无需 about |
| research on（作动词） | investigate / study / examine | research 在英文更多作名词 |
| the experiment result shows | the experimental results show | 形容词 + 复数（结果通常多） |
| according to（滥用） | based on / 重写 | "根据" 直译 |
| as we all know | （直接删除） | 学术写作避免预设读者认知 |
| it is well known that | （直接删除）/ "Prior work shows..." | 同上 |
| various / a variety of（滥用） | several / many / specific list | 太空泛 |
| significantly（滥用） | substantially / considerably / 改写 | 学术上 significantly 隐含统计显著，需谨慎 |

## 句法 / 搭配问题

| Chinglish | Correction | 解释 |
|---|---|---|
| ~~"is widely existed"~~ | "is widespread" / "exists widely" | 被动 + 不及物动词冲突 |
| ~~"can be hardly seen"~~ | "can hardly be seen" / "is rarely seen" | 副词位置 |
| ~~"in this paper, we propose..."~~（每段都用）| 仅在 abstract / intro 用一次 | 中文滥用 "本文" 直译 |
| ~~"as shown in Figure 1"~~（独立句） | 嵌入主句："Figure 1 shows..." 或 "(see Figure 1)" | 中文常单独说"如图 1 所示"，英文要嵌入 |
| ~~"the reason... is because..."~~ | "the reason... is that..." | because 后跟原因，不能跟在 reason 后 |
| ~~"the experiment is consist of"~~ | "the experiment consists of" / "is composed of" | consist 不与 be 连用 |
| ~~"so as to"~~（滥用） | "to" | "so as to" 多余，几乎所有场合都可换 |

## 主谓 / 单复数 / 冠词

英文学术写作中常见错误（中文母语者高频）：

1. **数据集 / results / experiments 是复数**："the results show", "experimental settings"
2. **The 用法**：首次提到一般概念用 a/an，特指用 the；具体方法名通常无 the（"BERT", "ResNet"）
3. **a method / the method**：泛指用 a/an，特指本文方法用 our method 或 the proposed method
4. **research / information / equipment 是不可数**：不用 researches / informations
5. **literatures**（错） → **literature**（不可数）

## 时态规则（学术英文）

| 内容 | 时态 |
|---|---|
| Abstract 写作内容 | 现在时为主："This paper proposes..." |
| Introduction 已有研究 | 现在完成时："Prior work has shown..." |
| Method 描述自己方法 | 现在时："Our method computes..." |
| Experiments 描述实验过程 | 过去时："We trained the model..." |
| Experiments 报告结果 | 现在时："The model achieves 94.3%..." |
| Conclusion 总结贡献 | 现在完成时："We have proposed..." |
| Future Work | 将来时："We will explore..." 或 "Future work could investigate..." |

## 标点规则

中→英时常见错误：

| 中文习惯 | 英文规范 |
|---|---|
| 逗号长句 | 用 ; 或拆为多句 |
| 顿号 "、" | 英文不存在，用逗号或 and |
| 句号 "。" | "." |
| 引号 "" | 英文用 "..." 或 '...' |
| 全角空格 | 英文段落间用半角空格，标点后接半角空格 |

## 校正策略（Step 2 反思应用）

1. **第一遍**：扫描全段是否含上述 Chinglish 模式，列出所有命中
2. **第二遍**：逐条评估上下文，决定 fix / keep（有些"in recent years"在特定语境是恰当的）
3. **第三遍**：fix 后回读全段，确保流畅度提升而非破坏

## 不要矫枉过正

下列**不是** Chinglish，是**正确的英文学术风格**：

- "We propose..." — 学术写作允许第一人称复数
- "The proposed method..." — 自指性表达
- "Furthermore, ..." / "Moreover, ..." — 学术连接词，可保留
- "Specifically, ..." — 引出具体说明，自然
- 长句（含多个从句）— 学术英文允许，只要逻辑清晰

## 自检清单

完成 Step 2 后，逐项确认：

- [ ] 全文 "in recent years" 出现 ≤ 1 次
- [ ] 全文 "play an important role" 出现 = 0 次
- [ ] "discuss about" 全部修正为 "discuss"
- [ ] 所有 "the experiment result" 修正为 "the experimental results"
- [ ] 时态符合 Abstract / Method / Experiments 的章节惯例
- [ ] 数据集 / 复数名词的 s 都正确
- [ ] 段落不以 "在本文中，我们" 直译开头
