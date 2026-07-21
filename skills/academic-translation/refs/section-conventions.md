# 学术论文章节惯例

> 顶会论文各章节的写作风格、字数、时态等惯例汇总。
>
> 三步翻译的 Step 2 + Step 3 都需要按章节类型应用对应规则。

## Abstract（摘要）

**目标**：在 150-250 词内自包含地交代 问题 / 方法 / 关键结果（带数字）/ 意义。

**惯例**：
- ❌ 不用引文（`\cite{}`）— 摘要应自含
- ❌ 不用未定义的缩写（首次出现要给全称）
- ❌ 不重复标题
- ✅ 主时态：现在时（"This paper proposes..."、"Experiments show..."）
- ✅ 结构：1-2 句问题 + 1 句缺口 + 2-3 句方法 + 2-3 句结果（带数字） + 1 句意义

**英文模板**：
```
[Problem] X is a fundamental problem in Y.
[Gap] However, prior work suffers from Z.
[Method] We propose A, which does B by C.
[Result] On benchmark D, our method achieves E (X% absolute / X.X points / X× faster) compared with the strongest baseline.
[Significance] These results suggest that F.
```

## Introduction（引言）

**目标**：让读者在第一页内理解"做了什么"和"为什么重要"。

**惯例**：
- 5 段 ± 1 段是常见结构
- 每段一个核心论点
- 主时态：现在时（描述领域）+ 现在完成时（描述前人工作）

**5 段结构**：
1. **第 1 段**：领域 + 问题的重要性
2. **第 2 段**：前人工作（"Prior work has shown..."）
3. **第 3 段**：缺口（"However, ..."）
4. **第 4 段**：本文方法 + 关键创新
5. **第 5 段**：贡献列表 + 论文结构

**贡献列表的写法**：
```
Our contributions are summarized as follows:
- We {action}, which is the first {what is novel}.
- We {action}, achieving {specific number} on {benchmark}.
- We open-source code at {URL}.（如适用）
```

> ⚠️ **NEVER 用** "We achieve state-of-the-art results" 作为贡献——SOTA 不是贡献，**新方法 + 具体数字**才是。

## Related Work（相关工作）

**目标**：把领域工作组织成 2-4 个主题，每主题用一段，**最后一句**说明本文如何与该主题不同/超越。

**惯例**：
- ❌ **不要按 paper 分组**（"Smith et al. did A. Jones et al. did B. Wang et al. did C."）
- ✅ **按主题分组**（"Approaches to X fall into two categories. The first... The second..."）
- ✅ 每段最后一句区分本文工作
- 主时态：过去时为主（描述具体工作） + 现在完成时（描述领域趋势）

**反例**：
```
❌ Smith [1] proposed A. Jones [2] proposed B. Wang [3] proposed C.
   ...
```

**正例**：
```
✅ Approaches to {problem} fall into three categories.
   The first {category} relies on {idea} \cite{smith,jones}, but suffers from {limitation}.
   The second {category} addresses this by {idea} \cite{wang}, achieving {result}.
   ...
   In contrast to all of the above, we {how this work is different}.
```

## Method（方法）

**目标**：让读者能复现本文方法。逻辑顺序优先于历史顺序。

**惯例**：
- 先定义符号，再使用（`\mathbf{x}_t \in \mathbb{R}^d` 在第一次出现时定义）
- 公式 + 文字解释**配对**：每个公式之后用 1-2 句话给出**直觉**
- 主时态：现在时（"Our method computes..."）
- 算法用 `algorithm` 环境呈现伪代码

**典型结构**：
1. **3.1 Problem Formulation**：形式化定义 + 符号约定
2. **3.2 Architecture / Approach Overview**：高层框架图（图 + 一段说明）
3. **3.3, 3.4, ...**：各模块详细描述
4. **3.X Training & Inference**：训练目标 / 损失 / 推理流程

## Experiments（实验）

**目标**：先说研究问题（research questions），再说设置，再说结果。

**惯例**：
- 主时态：过去时（描述实验过程）+ 现在时（描述结果）
- 表格 + 图都要 self-contained：caption 让读者不看正文也能理解
- ❌ 不用主观描述（"The model performs well"）
- ✅ 用具体数字（"The model achieves 94.3% accuracy, +2.1 absolute over the baseline"）

**典型结构**：
1. **4.1 Setup**：数据集 / baselines / metrics / 实现细节
2. **4.2 Main Results**：主要 benchmark 表
3. **4.3 Ablation Study**：消融实验
4. **4.4 Analysis**：定性分析 / case study / 图

**Setup 必含**：
- Dataset 来源 + 划分（train/dev/test）+ size
- Baselines 名称 + 引用
- Metrics 定义 + 单位
- Hyperparameters（learning rate / batch size / epochs / hardware）
- Reproducibility（seed / code link）

## Conclusion（结论）

**目标**：总结 + 局限 + 未来方向。**不重复 Abstract**。

**惯例**：
- 0.5 页左右，不超过 1 段长篇
- 主时态：现在完成时（"We have proposed..."） + 将来时（"Future work will..."）
- ✅ 诚实承认 limitation（reviewer 重视这一点）
- ❌ 不引入新内容、新结果、新引文

**结构**：
```
[Summary] We presented X, a Y for Z. Through {extensive experiments / theoretical analysis}, we showed that ...
[Limitation] Our approach has limitations. First, ... Second, ...
[Future Work] Future work could explore A, B, or C.
```

## 各章节首句（topic sentence）模板

| 章节 | 典型首句 |
|---|---|
| Abstract | "{Domain} is/has {problem}." |
| Introduction §1 | "{Problem} is a fundamental challenge in {area}." |
| Introduction §3 (gap) | "However, despite recent progress, {key gap remains}." |
| Related Work | "Approaches to {X} fall into {N} categories." |
| Method overview | "Figure {N} illustrates our approach, which consists of {N} components." |
| Method submodule | "{Module name} computes/handles/aims to..." |
| Experiments setup | "We evaluate {our method} on {datasets} with {baselines}." |
| Experiments results | "Table {N} reports {what}." |
| Conclusion | "We have presented {X}, a {Y} for {Z}." |

## 章节翻译时的特殊处理

| 章节 | 中→英 注意 | 英→中 注意 |
|---|---|---|
| Abstract | 必须现在时；删去引文（如有） | 中文仍用现在时；保留紧凑句式 |
| Intro | 加逻辑连接词（However / Thus）| "在引言中" 这类元指要删 |
| Related Work | 重组成主题分组 | 保持主题分组 |
| Method | 严守符号定义；公式后给直觉 | 中文允许更口语化的"直觉解释" |
| Experiments | 数字 / 单位 / dataset name 一字不改 | 同上 |
| Conclusion | 加 limitations 段（如英文未明显标）| 不要省略 limitations |
