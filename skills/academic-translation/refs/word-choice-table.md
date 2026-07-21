# Word Choice 替换表（顶会偏好）

> CS 顶会论文偏好的"简洁 / 直接 / 信达雅"用词替换表。
>
> **使用时机**：Step 3 雅化阶段必读。Step 1 直译 / Step 2 学术规范阶段不应用此表（否则会损失原文信息）。

## 简洁优先（Fancy → Simple）

| Fancy | Simple | 备注 |
|---|---|---|
| utilize | use | 顶会强偏好 |
| demonstrate | show | （除"形式证明"用 demonstrate） |
| commence | start / begin | |
| terminate | end / stop | |
| facilitate | help / enable | |
| endeavor | try | |
| ascertain | determine / find | |
| approximately | about | |
| consequently | so / thus | 视语气 |
| prior to | before | |
| subsequent to | after | |
| in the event that | if | |
| due to the fact that | because | |
| in order to | to | 删冗 |
| with respect to | about / regarding | |
| with the exception of | except | |
| a plethora of | many / numerous | |
| a multitude of | many | |
| a myriad of | many | |
| in the vicinity of | near | |
| at this point in time | now | |
| at that point in time | then | |

## 删除填充（Fluff → Delete）

下列短语**直接删除**，不要替换：

- "It is worth noting that ..."
- "It should be mentioned that ..."
- "It is important to note that ..."
- "In a similar vein, ..."
- "Needless to say, ..."
- "As a matter of fact, ..."
- "It goes without saying that ..."
- "For all intents and purposes, ..."
- "As we have discussed earlier, ..."
- "It can be seen that ..."
- "It is interesting that ..."

> 例外：当填充短语是**段落主题转折**的核心信号时（罕见），可保留一次。

## Hedging 校准（精确度而非保守）

学术写作中的 Hedging（缓和语气）很重要，但要**精确**而非**模糊**：

| Vague Hedging | Calibrated | 何时用哪个 |
|---|---|---|
| ~~"performs quite well"~~ | "achieves 94.3% accuracy, outperforming the strongest baseline by 2.1 points" | 任何能给数字的地方 |
| "may improve" | "can improve" / "improves" | 有充分证据时用 "improves" |
| "could be" | "is" / "can be" | 视证据强度 |
| "appears to" | "does" / "shows" | 实验已证明时去 hedging |
| "tends to" | "consistently does" / "is" | 视证据 |
| "generally" | （删除）/ "in {specific case}" | 如果有反例，明确说 |

**原则**：用 hedging 时必须有理由（如未充分验证、存在反例等）；没有理由就**别 hedge**。

## 主动 vs 被动（学术英文）

学术英文**允许**第一人称复数（we / our），主动态通常更清晰：

| 被动（弱） | 主动（强） |
|---|---|
| "The model was trained by us on ImageNet" | "We trained the model on ImageNet" |
| "It was found that..." | "We find that..." |
| "An algorithm is proposed in this paper" | "We propose an algorithm" / "This paper proposes an algorithm" |

**何时保留被动**：
- agent 不重要："The dataset was collected from public sources"
- agent 是大众："X is widely used"
- 流程性描述："The features are extracted, normalized, and fed into the encoder"

## 冗余消除

| Redundant | Concise |
|---|---|
| completely eliminate | eliminate |
| absolutely necessary | necessary |
| basic fundamentals | fundamentals |
| consensus of opinion | consensus |
| each individual | each |
| end result | result |
| final outcome | outcome |
| free gift | gift |
| future plans | plans |
| general consensus | consensus |
| past history | history |
| period of time | period / time |
| postpone until later | postpone |
| revert back | revert |
| sum total | sum / total |
| true facts | facts |
| unexpected surprise | surprise |

## 转折与连接词

学术段落需要**清晰的逻辑流动**。常用连接词：

| 类型 | 词 | 用法 |
|---|---|---|
| 转折 | However, Yet, Nevertheless, In contrast | 段落或句子开头 |
| 因果 | Thus, Therefore, Consequently, As a result | 段落开头表结论 |
| 递进 | Moreover, Furthermore, Additionally, In addition | 引出补充 |
| 举例 | For instance, For example, Specifically, Notably | 具体说明 |
| 让步 | Although, Despite, While, Even though | 表对立面后承认 |
| 总结 | In summary, Overall, To conclude, In short | 段落或文章结尾 |
| 顺序 | First, Second, Third, Finally | 仅在真正有顺序时用，避免列表化 |

> ⚠️ "First..., Second..., Third..., Finally..." 列表化结构常被认为模板化、AI 味重，**仅在真正有逻辑顺序时使用**，避免单纯为了"分点"而用。

## Hyphenation（合成词连字符）

学术英文复合形容词需正确连字符：

| 错误 | 正确 |
|---|---|
| state of the art method | state-of-the-art method（作形容词时） |
| The state-of-the-art is X | The state of the art is X（作名词时） |
| 5 layer network | 5-layer network |
| well known method | well-known method |
| pre trained model | pre-trained model |
| zero shot learning | zero-shot learning |
| end to end training | end-to-end training |
| in domain data | in-domain data |

## 中文雅化（英→中时）

| Common Chinese | More elegant | 何时用 |
|---|---|---|
| "重要的" | "关键的" / "核心的" / "显著的" | 视语境 |
| "提出了" | "提出" / "引入" / "给出" | 删冗"了" |
| "我们做了实验" | "实验表明" / "我们的实验显示" | 主动 → 客观 |
| "大量的" | "广泛的" / "诸多" | |
| "好的" | "优异的" / "出色的" / "良好的" | |
| "效果不错" | "性能优异" / "效果显著" | |
| "在本文中" | "本文" / "本研究" | 删去"在...中" |
| "可以看到" | "可见" / "由此" / 删除 | |

## 应用顺序

Step 3 雅化时按此顺序应用：

1. 删除填充（Fluff → Delete）
2. 简化用词（Fancy → Simple）
3. 消除冗余
4. Hedging 校准
5. 被动 → 主动（视情况）
6. 加连接词
7. 段落级流动检查

> ⚠️ 应用每条规则前都要看上下文，**不要机械替换**。"utilize" 在某些固定表达（如 "resource utilization"）中是正确的。
