# Grammar Tag Taxonomy — english-intensive-reader

> AI 在输出 `sentence_analysis.grammar_tags` 时，**必须且只能**使用本文件中的枚举值。
> 严禁自造标签（NEVER N7）。

---

## 一、句子结构类

| 标签 | 说明 | 示例 |
|------|------|------|
| `简单句` | 只有一个主谓结构 | The sun rises. |
| `并列句` | 两个独立分句用并列连词连接 | I came, and I saw. |
| `复合句` | 含一个或多个从句 | I know that he left. |
| `并列复合句` | 既有并列又有从句 | He left, but I knew that he would return. |
| `倒装句-全倒装` | 谓语完全置于主语前 | Here comes the bus. |
| `倒装句-部分倒装` | 助动词/情态动词置于主语前 | Never have I seen such beauty. |
| `强调句` | It is/was ... that/who 结构 | It is hard work that leads to success. |
| `there be 句型` | There is/are 存在句 | There are many challenges ahead. |

---

## 二、从句类

### 2.1 名词性从句

| 标签 | 说明 | 引导词 |
|------|------|--------|
| `主语从句` | 从句充当主语 | that / whether / what / who / how |
| `宾语从句` | 从句充当宾语 | that / whether / what / if |
| `表语从句` | 从句充当表语（系动词后）| that / whether / what / why |
| `同位语从句` | 从句解释说明名词 | that（接抽象名词：fact / idea / news / hope）|

### 2.2 定语从句

| 标签 | 说明 | 引导词 |
|------|------|--------|
| `限制性定语从句` | 修饰名词，不可省略 | who / whom / which / that / whose |
| `非限制性定语从句` | 补充说明，用逗号隔开 | who / whom / which / whose（不用 that）|
| `介词+关系代词定语从句` | 介词提前 | in which / of whom / by which |

### 2.3 状语从句

| 标签 | 说明 | 引导词 |
|------|------|--------|
| `时间状语从句` | 表示时间 | when / while / as / after / before / since / until |
| `条件状语从句` | 表示条件 | if / unless / provided that / as long as |
| `让步状语从句` | 表示让步 | although / though / even if / even though / while |
| `原因状语从句` | 表示原因 | because / since / as / for |
| `结果状语从句` | 表示结果 | so ... that / such ... that |
| `目的状语从句` | 表示目的 | so that / in order that |
| `方式状语从句` | 表示方式 | as / as if / as though |
| `比较状语从句` | 表示比较 | than / as ... as |
| `地点状语从句` | 表示地点 | where / wherever |

---

## 三、非谓语动词类

| 标签 | 说明 | 示例 |
|------|------|------|
| `不定式作主语` | to do 充当主语 | To learn is to grow. |
| `不定式作宾语` | to do 充当宾语 | She wants to leave. |
| `不定式作定语` | to do 修饰名词（后置）| the ability to adapt |
| `不定式作状语` | to do 表目的/结果 | He studied hard to pass the exam. |
| `不定式作宾补` | to do 补充说明宾语 | I asked him to stay. |
| `现在分词作定语` | doing 修饰名词（后置）| issues facing humanity |
| `现在分词作状语` | doing 表时间/原因/方式 | Seeing the result, she smiled. |
| `现在分词作宾补` | doing 补充说明宾语 | I saw him running. |
| `过去分词作定语` | done 修饰名词（后置）| the problems discussed |
| `过去分词作状语` | done 表被动/完成 | Exhausted by the work, he slept. |
| `动名词作主语` | doing 充当主语 | Reading improves vocabulary. |
| `动名词作宾语` | doing 充当宾语 | She enjoys reading. |
| `独立主格结构` | 名词/代词 + 分词，独立成分 | The work done, he left. |

---

## 四、特殊句式类

| 标签 | 说明 | 示例 |
|------|------|------|
| `虚拟语气-与现在事实相反` | If + 过去式, would/could/might + do | If I were you, I would try. |
| `虚拟语气-与过去事实相反` | If + had done, would have done | If he had studied, he would have passed. |
| `虚拟语气-与将来事实相反` | If + were to/should + do | If it were to rain, we'd cancel. |
| `虚拟语气-wish/suggest/insist` | wish + 过去式；suggest + should do | I wish I were there. |
| `被动语态` | be + done | The report was published yesterday. |
| `完成时态` | have/has/had + done | She has finished the project. |
| `进行时态` | be + doing | They are working on it. |
| `情态动词推测` | must/may/might/could + do/have done | He must have left early. |
| `省略句` | 省略重复成分 | She can play piano, and so can he. |
| `插入语` | 句中插入的补充成分 | The report, as expected, was delayed. |
| `同位语` | 对名词的补充说明 | My friend Tom is a doctor. |
| `感叹句` | What/How 引导 | What a beautiful day! |

---

## 五、修辞 / 篇章类（focus=structure 时使用）

| 标签 | 说明 |
|------|------|
| `对比结构` | 两个相反观点并列 |
| `递进结构` | not only ... but also / furthermore |
| `举例结构` | for example / for instance / such as |
| `因果结构` | therefore / thus / as a result |
| `让步转折结构` | however / nevertheless / yet |
| `总分结构` | 先总述后分述 |
| `分总结构` | 先分述后总结 |

---

## 六、修辞手法类（focus=structure 或 level=foreign_press 时使用）

> 融合自 gcse-english-language-tutor 的修辞手法分类体系。
> 这些标签输出到 `sentence_unit.rhetoric_tags` 字段，不影响 `grammar_tags`。

### 6.1 比喻类

| 标签 | 定义 | 对读者的效果 |
|------|------|------------|
| `暗喻` | 把某事物直接说成另一事物 | 创造直接、鲜明的形象 |
| `明喻` | 用 like / as 进行比较 | 同样鲜明，但强调比较行为本身 |
| `拟人` | 赋予非人类事物以人的特征 | 使抽象事物显得生动或威胁 |
| `情景交融` | 用天气/自然环境映射情绪 | 创造与人物心境吹合的氛围 |
| `夸张` | 故意极度夸大 | 强调强度，可制造幽默或紧迫感 |
| `矛盾修辞` | 两个矛盾词语并列 | 制造张力，突出殖义 |
| `象征` | 用具体事物代表更大的概念 | 在表面之下增加意义层次 |

### 6.2 音韵手法类

| 标签 | 定义 |
|------|------|
| `头韵` | 相邻词语首字母相同的辅音重复 |
| `齿音` | s / sh 音的重复，制造嘿声或耳语沙沙的效果 |
| `拟声词` | 词语的发音模拟所描述的声音 |
| `元音` | 词语内元音的重复 |

### 6.3 词汇效果类

| 标签 | 说明 |
|------|------|
| `联想义` | 词语字面之外的联想意义（如 home → 温暖、安全）|
| `语义场` | 共享主题的一组词语（如军事词汇用于描述商业）|
| `语气` | 作者通过语言传达的态度（愤怒/怀旧/讽刺/不吉）|
| `语体` | 语言正式度（正式/非正式/学术/口语）|

### 6.4 结构手法类

| 标签 | 说明 |
|------|------|
| `短句强调` | 短句单独成段，制造强调效果 |
| `长句堆叠` | 长句堆叠细节，建立压迫感 |
| `循环结构` | 结尾呢应开头，制造圈子感或讽刺 |
| `闪回` | 打断时间顺序，对比过去与现在 |
| `对比并置` | 将对立面并列，突出差异 |
| `重复强调` | 强化某一观点；排比（句首重复）|
| `视角转移` | 从全景到特写（或反之），制造镜头感 |

---

## 七、构词法类（vocab_notes.word_formation 使用）

> 融合自 gaokao-english-tutor 的构词法教学。帮助用户通过词根词缀记忆生词。

| 标签 | 说明 | 示例 |
|------|------|------|
| `否定前缀` | un- / dis- / im- / in- / ir- | uncomfortable / disagree / impossible |
| `重复前缀` | re- | rebuild / reconsider / rewrite |
| `过度前缀` | over- | overestimate / overload |
| `不足前缀` | under- | underestimate / undermine |
| `共同前缀` | co- / com- / con- | cooperate / combine / connect |
| `名词后缀` | -tion / -ment / -ness / -ity | education / development / happiness |
| `形容词后缀` | -ful / -less / -able / -ous | helpful / careless / capable / famous |
| `副词后缀` | -ly / -ward / -wise | quickly / forward / likewise |
| `动词后缀` | -ize / -ify / -en | modernize / simplify / strengthen |
| `词根` | 拆解词根含义 | ambition = am(我) + bition(必胜) |

---

## 使用规则

1. 一句话可以有**多个**语法标签（如 `["让步状语从句", "虚拟语气-与现在事实相反"]`）
2. 标签按**重要程度**排序，最核心的放第一位
3. 简单句（无特殊语法）→ `grammar_tags: ["简单句"]`，不留空数组
4. 标签最多 **4 个**，超出时只保留最核心的 4 个
5. **严禁**使用本文件枚举之外的标签（如"复杂句"、"高级句型"等模糊描述）
