# CET-4 vs CET-6 样卷难度差异

> 官方大纲明确：**四级和六级采用相同的档次描述，但参照当次考试的评分样卷**。
> 这意味着档次描述文字完全一样，但样卷的语言水平不同——CET-6 样卷整体水平高于 CET-4。
> 批改时必须按对应级别的样卷基准判定。

---

## 一、基本差异

| 维度 | CET-4 | CET-6 |
|------|-------|-------|
| 字数要求 | 120-180 词 | 150-200 词 |
| 词汇要求 | 约 4500 基础词 + 核心认知词 | 约 6000 基础词 + 更多地道搭配 |
| 句式要求 | 简单/复合句熟练，复杂句基本掌握 | 复杂句多样、非谓语/倒装自如运用 |
| 论证深度 | 清晰表达观点 + 基本例证即可 | 需要辩证 / 对比 / 深入分析 |
| 语域 | 半正式书面体，避免口语化 | 正式书面体，讲究文风一致 |

---

## 二、同档次的 CET4 vs CET6 基准差异

### 14 档（13-15 分）

| 判定点 | CET-4 样卷基准 | CET-6 样卷基准 |
|-------|--------------|--------------|
| 用词 | 词汇准确 + 有个别高级搭配（eg. put one's heart into） | 词汇地道 + 多处高级搭配（eg. strive for、put heart and soul into） |
| 句式 | 以简单+复合为主，**有 1-2 处复杂句** | 复杂句自如（3+ 处），含**非谓语结构** / **倒装** / **强调** |
| 论证 | 观点清晰 + 1-2 个具体例证 | **辩证思考** + 例证层次 + **反驳/让步** |
| 地道程度 | 自然流畅，个别非地道表达可接受 | 接近母语者表达，很少中式表达 |

### 11 档（10-12 分）

| 判定点 | CET-4 | CET-6 |
|-------|-------|-------|
| "少量语言错误"容忍度 | 3-6 处小错 | 2-4 处小错（更严格）|
| 用词 | 常用词熟练使用 | 需要体现词汇丰富度 |

### 8 档（7-9 分）

| 判定点 | CET-4 | CET-6 |
|-------|-------|-------|
| "基本切题"容忍度 | 主题正确，个别段落偏离可 | 主题正确 + 论证逻辑需基本在线 |

### 5 档 / 2 档

- 5/2 档两级的样卷差异较小（都属"不达标"区间）
- CET-6 考生出现 5 档以下通常提示基础严重不足

---

## 三、典型句式差异示例

### 题目：The Value of Doing Small Things Well

**CET-4 14 档典型句式**：

> Excellence doesn't always mean doing great things. Bill Gates and Steve Jobs are few in number. Most of us are ordinary people, but we can still be great by doing small things well.

（简单 + 复合句，个别高级词 `excellence`/`ordinary`）

**CET-6 14 档典型句式**：

> A perfect life doesn't have to be so glorious or sparkling as grand plays performed in theatres. The true value lies in our attitude towards tiny daily issues, of which the repairman working in our community is an ideal example.

（非谓语 `performed`、定语从句 `of which`、抽象名词 `value`、 地道搭配 `lies in`）

两者都是 14 档，但 CET-6 样卷对语言成熟度要求明显更高。

---

## 四、判定时的 prompt 提醒

在 Step 3 / Step 4 判定时，Skill 应该在 rationale 中显式写出对应级别的基准：

```
✅ 正确：
"这篇作文定为 CET-4 11 档。与 CET-4 11 档样卷相比，词汇和句式基本相当，
有 3 处小错（主谓一致、时态），符合'少量语言错误'的描述。"

❌ 错误：
"这篇作文定为 11 档，有少量错误。"
（未指明基准级别，无法解释为什么不是 14 档或 8 档）
```

---

## 五、跨级别"借鉴样本"的做法

- 若用户提交 CET-6 作文但水平明显达不到 CET-4 6 分，定档时仍用**CET-6 的样卷基准**（因为考生选择参加 CET-6）
- 反之，CET-4 作文写得达到 CET-6 水平 → 按 CET-4 14 档顶格给分（15 分），**不能超过 15 分**

---

## 六、报告分（710 分制下的作文分）

CET-4 和 CET-6 的 710 分总分完全相同，作文占 15% = 106.5 分，换算公式相同：

```
报告分 = 原始分 × 7.1
```

由 `scripts/score_to_report.py` 实现。

---

## 七、参考

- [official-rubric.md](official-rubric.md) — 档次描述原文
- [band-decision-rules.md](band-decision-rules.md) — 边界判定清单
- 教育部考试中心《全国大学英语四、六级考试大纲（2016 修订版）》第 4.1 节（四级、六级相同文本）
