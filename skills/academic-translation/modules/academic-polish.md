# 学术润色模块

将 Step 2 / Step 3 中针对"语言层面"的具体规则做集中说明。本模块**不**重复 three-step-translation.md 的算法，只补充**语言层面的具体细则**。

> 设计要点：分三组规则——顶会风格 word choice + Chinglish 校正 + 去 AI 味，分别承担"投稿口吻 / 学术写作正确性 / 自然度"三个层面的把关。

## 章节惯例（按章节类型分流）

详见 [../refs/section-conventions.md](../refs/section-conventions.md)。摘要：

| 章节 | 风格关键 | 字数惯例 | 主要时态 |
|---|---|---|---|
| Abstract | 自含 / 不引文 / 不缩写 | 150-250 词 | 现在时为主 |
| Introduction | 问题→缺口→贡献→简略结果→结构 | 1-2 页 | 现在时 + 现在完成时 |
| Related Work | 按主题分组（不按 paper 分组） | 0.5-1 页 | 过去时为主 |
| Method | 先定义符号再用 | 2-4 页 | 现在时（描述方法） |
| Experiments | 假设→设置→结果 | 2-3 页 | 过去时（描述实验）+ 现在时（结果） |
| Conclusion | 总结贡献 + 局限 + 未来方向 | 0.5 页 | 现在完成时 + 将来时 |

## Word Choice 替换表（顶会偏好）

详见 [../refs/word-choice-table.md](../refs/word-choice-table.md)。下面是高频规则摘要：

| 类型 | Before | After | 原因 |
|---|---|---|---|
| 简洁 | utilize | use | 顶会偏好 |
| 简洁 | demonstrate | show | （除"形式证明"外） |
| 简洁 | a plethora of | many | 简洁 |
| 简洁 | in order to | to | 删冗 |
| 简洁 | it is worth noting that | （删除） | 填充 |
| Hedging | "performs quite well" | "achieves 94.3% accuracy" | 用具体数字代替主观判断 |
| 冗余 | completely eliminate | eliminate | 重复 |
| 冗余 | future plans | plans | 重复 |
| 主动 | The model was trained by us | We trained the model | 主动态更清晰（agent 重要时） |

## Chinglish 校正（中→英时启用）

详见 [../refs/chinglish-patterns.md](../refs/chinglish-patterns.md)。高频规则：

| Chinglish | Correction | 解释 |
|---|---|---|
| in recent years（滥用） | recently / 删除 | "近年来"直译；不要每段都用 |
| play an important role | （视语境改写） | "起重要作用"直译，常空洞；改为具体描述 |
| more and more | increasingly | "越来越"直译 |
| discuss about | discuss | discuss 是及物动词 |
| research on（作动词） | investigate / study | research 在英文更多作名词 |
| the experiment result shows | the experimental results show | 形容词 + 复数 |
| according to（滥用） | based on / 重写 | "根据"直译 |

## 去 AI 味

| 模式 | 问题 | 修正 |
|---|---|---|
| "在本文中，我们..." 开篇 | 模板化、AI 典型 | 视段落作用精简或删除 |
| "首先...其次...最后..." 列表化 | 机器风格 | 改为自然连接（However / Thus） |
| 排比的"我们提出 / 我们设计 / 我们实现" | 重复结构 | 合并或换近义 |
| "重要的是 / 值得注意的是 / 需要指出的是" | 空填充 | 删除 |
| "在很大程度上 / 在某种程度上" | 模糊 | 用具体证据 |
| 大量被动："被提出" "被使用" "被证明" | 翻译腔 | 主动态优先 |

## 段落级流动（Step 3 雅化重点）

不只是单句润色，要看**段落主题句一致性**：

1. **段落开头**：交代该段主题（topic sentence）
2. **段落中段**：每句之间用逻辑连接词（however / thus / nonetheless / moreover / in contrast）
3. **段落结尾**：要么收束本段主旨，要么自然过渡到下一段
4. **避免"句子的水滴"**：5 句话用 5 个独立的"我们...""模型...""结果..."开头，无连接

> 这一层在 Step 1（直译）和 Step 2（反思）都不会修，**只有 Step 3 雅化**会做段落级 reflow。

## 目标会议适配

用户在 Preflight 指定目标会议时（"我要投 NeurIPS"），加载对应 glossary：

| 会议 | Glossary | 风格特点 |
|---|---|---|
| NeurIPS / ICLR / ICML | `refs/glossary/ml-venues.md` | 简洁、公式多、数学化语言 |
| AAAI / IJCAI | `refs/glossary/ml-venues.md` | 同上 + AI 综合性术语 |
| ACL / EMNLP / NAACL | `refs/glossary/nlp-venues.md` | 语言学精度、相关工作详尽 |
| CVPR / ICCV / ECCV | `refs/glossary/cv-venues.md` | 视觉术语、benchmark 表达 |
| SIGIR / WWW / KDD / CIKM | `refs/glossary/ir-data-venues.md` | 问题动机、应用 impact |

未指定会议 → 加载 `refs/glossary/general-cs-terms.md`。

## 用户自定义术语库优先级

```
Priority: User Glossary > Builtin Venue Glossary > Builtin General Glossary
```

用户上传的术语强制使用，与内置库冲突时打印警告但仍服从用户。
配置见 [../config/user-glossary.template.yaml](../config/user-glossary.template.yaml)。
