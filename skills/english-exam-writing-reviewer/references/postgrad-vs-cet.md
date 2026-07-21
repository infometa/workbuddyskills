# 考研 vs CET：批改逻辑的关键差异

> 本 Skill 统一承担 CET-4 / CET-6 / 考研英语一 / 考研英语二 的作文批改。
> 虽然都是"档次制 + 总体印象评分"，但**底层规则差异显著**，切换 `exam_level` 必须同时切换以下规则集。

---

## 一、档次结构差异

| 维度 | CET-4 / CET-6 | 考研英语一 A | 考研英语一 B | 考研英语二 A | 考研英语二 B |
|------|--------------|------------|------------|-------------|-------------|
| 档次数 | **5 档**（14/11/8/5/2）+ 0 档 | 5 档 + 0 档 | 5 档 + 0 档 | 5 档 + 0 档 | 5 档 + 0 档 |
| 总分 | 15（作文部分） | 10 | 20 | 10 | 15 |
| 档内调节 | **±1**（整数，**严禁半分**） | **1–3 分调节**（允许半分）| **1–3 分调节**（允许半分）| **1–3 分调节** | **1–3 分调节** |
| 最高档分数区间 | 13–15 | 9–10 | 17–20 | 9–10 | 13–15 |
| 换算 | ×7.1 → 106.5 制 | 直接累加到总分 100 | 直接累加 | 直接累加 | 直接累加 |

### Skill 必须按 exam_level 切换的逻辑

```python
def get_score_rules(exam_level):
    return {
        "CET4":      {"bands": [14,11,8,5,2,0], "intra_band": "±1",   "half_allowed": False, "max": 15},
        "CET6":      {"bands": [14,11,8,5,2,0], "intra_band": "±1",   "half_allowed": False, "max": 15},
        "Postgrad1A":{"bands": [5,4,3,2,1,0],   "intra_band": "±1~3", "half_allowed": True,  "max": 10},
        "Postgrad1B":{"bands": [5,4,3,2,1,0],   "intra_band": "±1~3", "half_allowed": True,  "max": 20},
        "Postgrad2A":{"bands": [5,4,3,2,1,0],   "intra_band": "±1~3", "half_allowed": True,  "max": 10},
        "Postgrad2B":{"bands": [5,4,3,2,1,0],   "intra_band": "±1~3", "half_allowed": True,  "max": 15},
    }[exam_level]
```

---

## 二、档次描述符差异

| CET 描述符关键词 | 考研描述符关键词 |
|-----------------|----------------|
| 切题 / 基本切题 / 条理不清 | 完成任务 / 基本完成 / 未能完成 / 未完成 |
| 表达思想清楚 / 不够清楚 / 紊乱 | 包含所有/多数/一些/明显遗漏内容要点 |
| 文字连贯 / 勉强连贯 / 支离破碎 | 衔接手法多样 / 适当 / 简单 / 未采用 |
| 少量/相当多/较多/多 语言错误 | 语法错误极少 / 个别错误 / 一些错误 / 较多错误 |

**核心差异**：

- CET 描述围绕"切题—清晰—连贯—错误"4 个维度，**无显式"格式/语域"**
- 考研描述强调"**任务完成度 + 格式与语域**"，尤其 A 节把"格式与语域"列为显式观察点
- 考研描述更贴合**实际读者效果**（"对目标读者产生了预期的效果"是五档关键标志），CET 不做此要求

---

## 三、字数规则差异

| exam_level | 下限 | 上限 | 不达标扣分逻辑 |
|-----------|------|------|---------------|
| CET-4 | 120 | 180 | shortfall_ratio × 总分上限，详见 `deduction-rules.md` |
| CET-6 | 150 | 200 | 同上 |
| Postgrad1 A | ~100 | — | 酌情扣分，约每 20 词短缺 -1 分 |
| Postgrad1 B | **160** | **200** | 低于 160 酌情扣分，**低于 120 降一档** |
| Postgrad2 A | ~100 | — | 同 Postgrad1 A |
| Postgrad2 B | ~140 | ~160 | 低于 120 酌情扣；高于 180 可能因超量被判"离题" |

---

## 四、A 节（应用文）的特殊规则

### 考研 A 节独有（CET 没有）

1. **Directions 原句照搬扣分**（≥8 词连续一致 → 扣分）
2. **格式分独立考核**：书信缺少 signature / 通知缺少落款机构 → 按"格式与语域"观察点降档
3. **签名约束**：如 Directions 规定用 "Li Ming"，**用真实姓名扣分**

### CET 应用文（若出现）

- 无 Directions 扣分规则
- 格式要求相对宽松，主要考察"切题 + 语言"

### Skill 实现切换

```python
if exam_level.startswith("Postgrad") and section == "A":
    run_directions_copy_detection(essay, directions)
    check_signature_compliance(essay, required_signature="Li Ming")
    check_letter_format(essay, required_format=["greeting", "body", "closing", "signature"])
```

---

## 五、B 节题型差异

| exam_level | B 节题型 | 主评要点 |
|-----------|---------|---------|
| CET-4 / CET-6 | 命题作文 / 图表作文 / 漫画作文 / 应用文等 | 切题 / 清晰 / 连贯 / 错误 |
| Postgrad1 B | **图画作文**（描述 + 寓意 + 论述）| **论述性** + 5 维观察点 |
| Postgrad2 B | **图表作文**（数据解读 + 趋势 + 分析）| **数据描述精准度** + 5 维观察点 |

**英一 B 节 2022 变化**："议论性"→"**论述性**"，对逻辑论证要求更高，Skill 的 `dimension_diagnosis.language_accuracy` 里要明确判断**论证是否单向**（单向=低于论述性标准）。

---

## 六、评分语言 / 反馈风格差异

两者都用中文反馈，但：

- **CET**：面向 CET-4 / CET-6 考生，解释时可以更通俗，允许口语化点评
- **考研**：面向考研考生（通常英语水平更高），术语要更学术，解释要更简洁、逻辑性更强，避免"夸奖"式反馈

Skill 实现：**不同 exam_level 启用不同的反馈语气 prompt**。

---

## 七、常见误判点（Skill 切换时容易错）

1. ❌ 用 CET-4 的 120 词阈值去扣考研英语一 B 节作文 → 错，考研英一最低 160
2. ❌ 把考研半分算成 CET 整数 → 错，考研 `final_score = 14.5` 合法
3. ❌ 用 CET 的 5 档（14/11/8/5/2）编号描述考研 → 错，考研用 "第 5 档/第 4 档..."
4. ❌ 给考研 A 节打分漏了 Directions 原句检测 → 错，这是官方独有规则
5. ❌ 把英一 B 节的"论述性"降格为"议论性"去评分 → 错，2022 起英一 B 节按论述性评分

---

## 八、资源交叉索引

| 场景 | 加载顺序 |
|------|---------|
| CET-4 / CET-6 批改 | `official-rubric.md` → `cet4-vs-cet6.md` → `band-decision-rules.md` |
| 考研英语一/二 批改 | `postgrad-official-rubric.md` → 本文档 → `band-decision-rules.md` |
| 所有级别 Step 6 升档 | `writing-vocabulary.md`（共用）+ `upgrade-paths.md` |
| 横向对比快速决策 | `exam-level-matrix.md`（一张表看所有级别）|
