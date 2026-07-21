---
exam_level: CET4
band: 8
raw_score: 8
task_subtype: news_report
task_type: news_report
anchor_tags: [v1.6, new-subtype-anchor, mid-band]
reference_source: "基于 CET4 2023-06 真题改写（新闻报告题型首次出现）"
prompt: |
  Directions: For this part, you are allowed 30 minutes to write a news report to your
  campus newspaper on a volunteer activity organized by your Student Union to help elderly
  people in the neighbourhood. You should write at least 120 words but no more than 180
  words.
---

# 样例作文原文

```
Student Union Helps the Elderly

On May 15, 2024, our Student Union held a volunteer activity in the Sunshine
Community near our campus. More than 40 students from different departments joined
this activity. They helped the elderly people clean their rooms, buy daily things
from the supermarket, and also talked with them for a long time.

Li Ming, the head of the Student Union, said this activity was very meaningful. He
told us that some old people live alone and they need help and company from young
people. Many volunteers also said they learned a lot from the old people during the
activity.

The activity lasted about four hours. At the end, the elderly people thanked the
students many times. The Student Union plans to hold this kind of activity every
month in the future. I think it is a good way to connect the young and the old.
```

（正文约 158 词）

---

# 人工阅卷批注（CET-4 · news_report · 8 档）

## 新闻报告题型独有检查项（v1.6 新增硬约束）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 标题 | 独立一行，名词短语，首字母大写 | `Student Union Helps the Elderly` | ✅ 合规 |
| 5W1H 覆盖 | ≥ 5 项 | Who ✅ / What ✅ / When ✅ / Where ✅ / Why ✅ / How ✅ | ✅ 全覆盖 |
| 第三人称客观语气 | 全篇 he/she/they | **末句出现 `I think it is a good way`** | ❌ critical（新闻报告禁第一人称 + 禁主观评价）|
| 时态（过去时为主）| 事件描述用过去时 | 过去时为主 ✅，但 `plans to hold`（现在时 + 将来意义）可接受 | ✅ |
| 无主观评价 | 陈述事实不夹带 `I think` / `we should` | **末句严重违规** | ❌ critical |
| 有直接引语 | ≥ 1 句 Li Ming 引述 | `Li Ming... said this activity was very meaningful` | ✅ 有间接引语 |

→ 关键失误：**末段最后一句 `I think it is a good way...` 同时触发 2 项硬约束**（第一人称 + 主观评价）。按 v1.6 `cet-subtypes.md` §3 规则，这是新闻报告降档至 8 分的典型信号。

## 隐含维度诊断

- **切题度**：基本切题。主题"志愿服务助老"清晰，5W1H 基本覆盖
- **表达清晰度**：思想清楚，三段式结构（事件 → 引述 → 影响）
- **连贯性**：勉强连贯。段内逻辑通顺，段间衔接较弱（无明显过渡词）
- **语言准确度**：1 critical（语体违规）+ 2 warning（语域）+ 2 tip
- **news_report 专有**：第一人称违规 + 非正式动词 `buy daily things`

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶3 末 | `I think it is a good way to connect the young and the old.` | 删除整句，或改为 `The activity was widely praised by participants and residents alike for bridging generational gaps.` | **critical** | **register_mismatch**（新闻报告禁第一人称 + 禁主观评价，双重违规）|
| ¶1 中 | `buy daily things from the supermarket` | `purchase daily necessities from the local supermarket` | warning | lexical（`daily things` 偏口语，新闻报告应用精确名词）|
| ¶1 末 | `talked with them for a long time` | `chatted with them over the course of the afternoon` | warning | lexical（`for a long time` 不精确，新闻报告要有具体时长）|
| ¶2 中 | `some old people live alone and they need help` | `some elderly residents live alone and require assistance` | tip | register（`old people` 略不敬，新闻用 `elderly` / `senior residents`）|
| ¶3 首 | `The activity lasted about four hours.` | 保留，可选升级：`Lasting approximately four hours, the event concluded with...` | tip | syntactic（简单句可升级为非谓语，利于 14 档）|

合计 1 critical + 2 warning + 2 tip — 符合 CET-4 8 档"语言错误相当多，有些严重错误"。

## 为什么 8 分不是 11 分（news_report 视角）

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| 新闻格式合规（标题 + 5W1H）| 合规 | 11 |
| 语体一致性 | **末句第一人称主观评价，违反新闻文体硬约束** | **8**（11 档要求语体统一） |
| 词汇精确度 | `daily things` / `for a long time` 两处不精确 | 8 |
| 句式复杂度 | 全篇简单句+简单并列，无复合/非谓语 | 8 |

→ 末句语体违规是决定性降档因素。按 `cet-subtypes.md` §3 news_report 规则，**"出现第一人称直接降至 8 档或以下"**。

## 为什么 8 分不是 5 分

- ✅ 标题独立存在（5 档常无标题）
- ✅ 5W1H 全覆盖（5 档常漏 When / Where）
- ✅ 有直接/间接引语（新闻报告的文体标志）
- ✅ 时态基本正确
- ✅ 无严重语法错误（仅 1 语体违规）

→ 明显优于 5 档。

## 升档路径（CET-4 8 → 11）

1. **删除末段第一人称主观句**：「I think it is a good way...」→ 改为客观影响陈述
2. **精确化词汇**：`daily things` → `daily necessities`；`for a long time` → `for over two hours`
3. **升级 elderly 相关表达**：`old people` → `elderly residents` / `senior citizens`
4. **加 1 个非谓语结构**：`Lasting approximately four hours, the event...`
5. **升级段间衔接**：末段首加 `According to the Student Union` 或 `Looking ahead,...` 增强新闻体连贯

---

# 该样例用途

- **v1.6 新子类 news_report 中档位锚点样例**：第一篇 `task_subtype = news_report` 校准
- **硬约束金标**：演示"第一人称出现即降档"的 news_report 规则
- **Step 3 定档**：CET-4 8 档新闻报告的典型表现
- **教学价值**：中国学生写新闻报告的最大陷阱就是末尾"表达个人感想"——这是议论文思维的惯性迁移，必须专门训练
