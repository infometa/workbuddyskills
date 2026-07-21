# 考试级别决策矩阵（Exam Level Matrix）

> 一张表看懂 4 种级别的核心参数，Step 1 接到作文后**第一件事**就是查这张表确认走哪条规则。
> 详细规则各自在：`official-rubric.md`（CET）/ `postgrad-official-rubric.md`（考研）/ `cet4-vs-cet6.md`（四六级差异）/ `postgrad-vs-cet.md`（考研 vs CET 差异）。

---

## Contents

- [一、核心参数速查表](#一核心参数速查表)
- [一(b)、task_subtype 枚举总表](#一btask_subtype-枚举总表v160-新增)
- [二、档次映射：不同级别的"相当水平"](#二档次映射不同级别的相当水平)
- [三、工作流分支表](#三工作流分支表step-1-接到作文后的首要决策)
- [四、输出 schema 差异](#四输出-schema-差异)
- [五、一句话口诀](#五一句话口诀快速记忆)
- [六、异常处理](#六异常处理)

---

## 一、核心参数速查表

| 参数 | CET-4 | CET-6 | Postgrad-1-A | Postgrad-1-B | Postgrad-2-A | Postgrad-2-B |
|------|-------|-------|--------------|--------------|--------------|--------------|
| 官方大纲 | 2016 修订版 | 2016 修订版 | 2026 考研一 | 2026 考研一 | 2026 考研二 | 2026 考研二 |
| 作文总分 | 15 分 | 15 分 | 10 分 | 20 分 | 10 分 | 15 分 |
| 换算总分 | 106.5（×7.1）| 106.5（×7.1）| 累加到 100 | 累加到 100 | 累加到 100 | 累加到 100 |
| 档次数 | 5 档 + 0 档 | 5 档 + 0 档 | 5 档 + 0 档 | 5 档 + 0 档 | 5 档 + 0 档 | 5 档 + 0 档 |
| 档次编号 | 14/11/8/5/2 | 14/11/8/5/2 | 五/四/三/二/一 | 五/四/三/二/一 | 五/四/三/二/一 | 五/四/三/二/一 |
| 档内调节 | ±1（整数）| ±1（整数）| 1–3 分（含 0.5）| 1–3 分（含 0.5）| 1–3 分 | 1–3 分 |
| 最高档分数 | 13–15 | 13–15 | 9–10 | 17–20 | 9–10 | 13–15 |
| 字数下限 | 120 | 150 | ~100 | 160 | ~100 | ~140 |
| 字数上限 | 180 | 200 | — | 200 | — | ~160 |
| 常见题型 | 命题 / 图表 / 漫画 / 应用文 | 同左 | 书信 / 通知 / 告示 / 纪要 | 图画作文（论述性）| 同左 | 图表作文 |
| 特殊规则 | — | 难度参考高等级样卷 | **Directions 原句扣分** + 格式语域独立 | 论述性要求（2022+）| 同 1A | 数据精准度 |
| 反馈语气 | 通俗教练式 | 较学术 | 简洁学术 | 简洁学术 | 简洁学术 | 简洁学术 |
| 半分合法 | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Directions 必需 | 可选 | 可选 | **必需** | 可选 | **必需** | 可选 |

> \* 「摘要 / memorandum」在大纲中保留但近 20 年真题未出现，v1.6.0 起标记为 `low_frequency_theoretical`，触发时走防御分支。

---

## 一(b)、task_subtype 枚举总表（v1.6.0 新增）

每个 `exam_level` 对应的 `task_subtype` 可选值：

| exam_level | task_subtype 枚举 | 校准状态 | 细化文档 |
|-----------|-------------------|---------|---------|
| CET4 / CET6 | `prompt_essay`（默认）/ `proverb` / `chart` / `cartoon` / `news_report` / `letter` / `report` | 全 `fully_calibrated` | [cet-subtypes.md](cet-subtypes.md) |
| Postgrad1A / Postgrad2A | `letter` / `notice` / `announcement` / `memorandum` / `summary` | `letter` / `notice` / `announcement` `fully_calibrated`；`memorandum` / `summary` `low_frequency_theoretical` | [letter-categories.md](letter-categories.md)（letter 子类）|
| Postgrad1B | `cartoon_standard`（默认 99%）/ `descriptive_theoretical` / `narrative_theoretical` / `expository_theoretical` | `cartoon_standard` `fully_calibrated`，其余 `low_frequency_theoretical`（近 20 年 0 次真题）| [postgrad1b-paragraph-rubric.md](postgrad1b-paragraph-rubric.md) |
| Postgrad2B | `bar_chart` / `pie_chart` / `table` / `line_graph` / `multi_bar` / `multi_pie` / `mixed` | 全 `fully_calibrated` | [chart-verbs.md](chart-verbs.md) |

**A 节额外字段**：`task_subtype == "letter"` 时必填 `letter_category`（10 种功能子类，见 [letter-categories.md](letter-categories.md)）。

---

## 二、档次映射：不同级别的"相当水平"

帮助学生理解跨级别对标。**仅供自我定位，不做自动换算**。

| 水平层 | CET-4 | CET-6 | 考研一 A | 考研一 B | 考研二 A | 考研二 B |
|-------|-------|-------|---------|---------|---------|---------|
| 优秀 | 14 档 (13-15) | 14 档 (13-15) | 5 档 (9-10) | 5 档 (17-20) | 5 档 (9-10) | 5 档 (13-15) |
| 良好 | 11 档 (10-12) | 11 档 (10-12) | 4 档 (7-8) | 4 档 (13-16) | 4 档 (7-8) | 4 档 (10-12) |
| 中等 | 8 档 (7-9) | 8 档 (7-9) | 3 档 (5-6) | 3 档 (9-12) | 3 档 (5-6) | 3 档 (7-9) |
| 偏弱 | 5 档 (4-6) | 5 档 (4-6) | 2 档 (3-4) | 2 档 (5-8) | 2 档 (3-4) | 2 档 (4-6) |
| 严重不足 | 2 档 (1-3) | 2 档 (1-3) | 1 档 (1-2) | 1 档 (1-4) | 1 档 (1-2) | 1 档 (1-3) |

**关键警示**：同一篇作文在不同级别下档次会不同。

- CET-4 11 档 → CET-6 通常降到 8 档（用词、句式要求更高）
- CET-6 11 档 → 考研一 B 通常在 3 档中段（论述性要求更高）
- 跨级别对照样例见 `references/calibration/cross-level/README.md`

---

## 三、工作流分支表（Step 1 接到作文后的首要决策）

```
Step 1：输入校验 → 查 exam_level
    │
    ├─ CET4 / CET6
    │    → 字数规则：CET4=120-180 / CET6=150-200
    │    → 档次编号：14/11/8/5/2
    │    → 调节：±1 整数
    │    → 加载：official-rubric.md + cet4-vs-cet6.md
    │    → 反馈语气：通俗教练式
    │
    ├─ Postgrad1A / Postgrad2A（A 节应用文）
    │    → 字数规则：~100 词
    │    → 档次编号：第五/四/三/二/一档
    │    → 调节：1-3 分（允许 0.5）
    │    → 加载：postgrad-official-rubric.md + postgrad-vs-cet.md
    │    → **必须**：Directions 原句检测 + 格式/签名检测
    │    → 反馈语气：简洁学术
    │
    ├─ Postgrad1B（英一 B 节）
    │    → 字数规则：160-200 词
    │    → 档次编号：第五/四/三/二/一档
    │    → 调节：1-3 分
    │    → 加载：postgrad-official-rubric.md + postgrad-vs-cet.md
    │    → **论述性要求**：检查逻辑论证是否单向
    │    → 反馈语气：简洁学术
    │
    └─ Postgrad2B（英二 B 节）
         → 字数规则：~150 词
         → 档次编号：第五/四/三/二/一档
         → **图表作文**：检查数据描述精准度
         → 加载：postgrad-official-rubric.md + postgrad-vs-cet.md
         → 反馈语气：简洁学术
```

---

## 四、输出 schema 差异

| 字段 | CET | Postgrad |
|------|-----|----------|
| `meta.exam_level` | `"CET4"` / `"CET6"` | `"Postgrad1A"` / `"Postgrad1B"` / `"Postgrad2A"` / `"Postgrad2B"` |
| `band` | `14` / `11` / `8` / `5` / `2` / `0` | `5` / `4` / `3` / `2` / `1` / `0` |
| `raw_score` | 整数 0–15 | 整数或 0.5 步进，上限因节而异 |
| `converted_score` | `final_score × 7.1` | `final_score`（直接累加）|
| `dimension_diagnosis` | 4 维：relevance / clarity / coherence / language_accuracy | 5 维：task_completion / grammar_vocabulary / language_accuracy / coherence / **format_register** |
| `directions_copy_check` | — | **必填**（Postgrad A 节）|
| `vocabulary_upgrades` | 基于 writing-vocabulary.md | 同左，tier 目标更高 |

---

## 五、一句话口诀（快速记忆）

> **CET 看档内 ±1，考研有调节 1–3；**
> **四级 120–180，六级 150–200；**
> **考研 A 节 100 词，Directions 禁照搬；**
> **考研英一 B 论述 160-200，英二 B 图表 ~150。**

---

## 六、异常处理

| 情况 | 处理 |
|------|------|
| 用户只给了 essay，没指定 exam_level | **必须追问**，不得默认 |
| 用户说"按考研"但没指定英一/英二 | **必须追问**（分值不同） |
| 考研 A 节但没给 Directions | 警告用户，降级处理（无法做原句照搬检测，在免责中注明）|
| CET 作文字数达到 200+（超上限明显）| 不扣分（无上限惩罚），但在 `issues` 里提醒"CET 考场要求 120-180，超量不加分" |
| `task_subtype ∈ {summary, memorandum, descriptive_theoretical, narrative_theoretical, expository_theoretical}`（v1.6.0 新增） | **继续批改**但：① `calibration_status = "low_frequency_theoretical"`；② 在报告开头加免责声明（见 SKILL.md Step 1 分支）；③ `paragraph_diagnosis = null`（不适用三段论）；④ 分数置信度下调 |
| `task_subtype` 无法识别（超出所有枚举）| `calibration_status = "out_of_calibration"`；仅给出 5 维定性诊断，拒绝给具体分数，`raw_score = null` |
