# 考研英语一 B 节：三段论段落质量诊断 Rubric

> v1.6.0 新增。根据真题趋势修正：**近 20 年英一 B 节真题 100% 是"漫画 + 议论"题型**。
> 本 Rubric 放弃"整篇文体分类"（descriptive/narrative/expository 已降级为理论题型），转而按**三段论段落质量**做细粒度诊断，直击评分痛点。

---

## 一、真题趋势与历史定位

### 为什么放弃"4 种文体"分类

大纲虽然提到"描述、叙述、说明、论述"文体，但：

| 时期 | 实际考法 |
|------|---------|
| 2005-2011 | 漫画 + 议论（固定）|
| 2012-2021 | 漫画 + 议论 → 强调辩证 |
| **2022+** | 漫画 + 议论 → 强调**论述性**（逻辑严谨，单向论证即扣分） |
| **近 20 年** | **未出现过一次纯 descriptive / narrative / expository** |

### 结论

- **默认 `task_subtype = cartoon_standard`**（99% 情境）
- `descriptive_theoretical` / `narrative_theoretical` / `expository_theoretical` 作为防御性枚举保留，触发时：
  - 不调用本 Rubric 的三段论结构（因为结构不适用）
  - 在输出中标记 `calibration_status = "low_frequency_theoretical"` + 免责声明
  - 改用通用 5 维 rubric，分数置信度下调

---

## 二、三段论段落分解（`cartoon_standard` 专用）

真正的评分主轴是**三段论结构完整度**，对应 `paragraph_diagnosis` 3 个子字段：

```
┌─────────────────────────────────────────────────────────┐
│ ¶1 Descriptive（描述图画，约 60-80 词）                    │
│    → 核心动作：客观描述画面要素 + 关键文字/细节              │
│    → 评判字段：para1_descriptive                          │
├─────────────────────────────────────────────────────────┤
│ ¶2 Interpretive（阐释深层含义，约 50-70 词）              │
│    → 核心动作：从画面提取隐喻/象征 → 引申到社会现象         │
│    → 评判字段：para2_interpretive                         │
├─────────────────────────────────────────────────────────┤
│ ¶3 Analytical / Commendatory（评论 / 对策，约 50-60 词）  │
│    → 核心动作：辩证分析 + 给出观点/措施                    │
│    → 评判字段：para3_analytical                           │
└─────────────────────────────────────────────────────────┘
总字数目标：160-200 词（下限 160，低于 120 降一档）
```

---

## 三、段落质量 3 级评分（High / Mid / Low）

### ¶1 Descriptive（描述）

| 档位 | 评判要点 | 典型表现 | `completeness_ratio` |
|------|---------|---------|----------------------|
| **high** | 全画面要素 + 关键文字/对话 + 细节忠实 | 描述人物、动作、场景、文字至少 4 要素 | 0.85-1.0 |
| **mid** | 主要要素覆盖 + 少量细节遗漏 | 描述了主角和动作，但漏掉背景或文字 | 0.55-0.84 |
| **low** | 仅点到为止 / 细节错误 / 主观臆断 | 1-2 句话概括，或描述与图不符 | 0.0-0.54 |

**critical 失误**：

- 完全没有描述（直接跳到阐释）→ `completeness_ratio = 0`
- 描述与图画相悖（如图是"鱼跳龙门"，却描述为"鱼被钓上来"）
- 超过 100 词（挤占后两段）

### ¶2 Interpretive（阐释）

| 档位 | 评判要点 | 典型表现 |
|------|---------|---------|
| **high** | 从具体画面**贴切**提炼抽象主题 + 联系普遍现象 | "此画揭示年轻人对成功的急功近利" |
| **mid** | 能提炼主题但较浅 / 提炼正确但未联系社会 | "这表示我们要努力" |
| **low** | 跑题 / 只重复画面 / 乱升华 | "画上的鱼代表了我们的精神" |

**critical 失误**：

- 主题**完全偏题**（与图表核心寓意不符）→ 全文降一档
- 没有阐释段（直接从描述跳到对策）

### ¶3 Analytical（评论 / 对策）

| 档位 | 评判要点 | 典型表现 |
|------|---------|---------|
| **high** | **辩证**（承认多面）+ 具体可行对策 / 有层次归因 | "诚然...; 然而...; 因此我们应..." |
| **mid** | 单向肯定/否定 + 泛泛对策 | "We should work hard and never give up" |
| **low** | 喊口号 / 套话堆砌 / 没对策 | "Let's embrace a bright future together!" |

**critical 失误**（2022 后专门检查）：

- **论证单向** → 触发"低于论述性标准"降档（由"议论性"→"论述性"改革核心）
- 对策空洞（只有 "work hard" / "we must" 类口号）
- 完全没有对策/评论段

---

## 四、论述性检查（2022+ 核心创新点）

**什么是"论述性"**：不仅表达观点，还要**反驳/让步/对比/归因**呈现论证链。

### 单向论证（旧"议论性"）vs 论述性（新"论述性"）

```diff
- 议论性示例（2021 前合格）：
- Hard work is essential for success. Many examples prove this. Edison worked
- tirelessly. So we must work hard too.
- （观点 → 例证 → 呼吁，线性单向）

+ 论述性示例（2022+ 合格）：
+ Admittedly, talent plays a role in success; nevertheless, sustained effort
+ proves far more decisive. While Edison's genius is often celebrated, it is
+ his 99% perspiration that enabled his breakthroughs. Therefore, young people
+ should prioritize perseverance over innate ability.
+ （让步 → 转折 → 例证 → 结论，多维展开）
```

### Skill 检查点（`para3_analytical.is_dialectical`）

| 检查项 | 正向标志词 | 反向（=非论述） |
|--------|-----------|----------------|
| 有让步 | admittedly / granted / while / although | 无任何让步词 |
| 有转折 | nevertheless / however / yet | 全篇肯定/全篇否定 |
| 多维归因 | multifaceted / several factors / twofold | 只给 1 个原因 |
| 有反驳 | contrary to popular belief / critics argue | 观点与反方 0 交锋 |

**规则**：若 ¶3 触发 3 个以上"反向"标志 → `is_dialectical = false` → 降至三档以下。

---

## 五、output 字段：`paragraph_diagnosis` 完整示例

```json
{
  "paragraph_diagnosis": {
    "para1_descriptive": {
      "quality": "high",
      "completeness_ratio": 0.92,
      "elements_covered": ["主角动作", "关键文字", "背景", "情绪"],
      "elements_missed": ["右下角的时钟细节"],
      "word_count": 68,
      "note": "要素完整，细节忠实，但漏掉时钟暗示'时间压力'的象征"
    },
    "para2_interpretive": {
      "quality": "mid",
      "theme_extracted": "年轻人追求快速成功的浮躁",
      "theme_accuracy": "accurate",
      "social_connection": false,
      "word_count": 52,
      "note": "主题提取准确贴合画面，但未联系当代社会现象，阐释略浅"
    },
    "para3_analytical": {
      "quality": "high",
      "is_dialectical": true,
      "dialectical_markers": ["Admittedly", "nevertheless", "twofold"],
      "has_concrete_measures": true,
      "word_count": 58,
      "note": "有让步-转折-多维归因结构，符合 2022+ 论述性要求"
    }
  },
  "meta": {
    "task_subtype": "cartoon_standard",
    "calibration_status": "fully_calibrated"
  }
}
```

---

## 六、定档映射（三段论 → band）

| 三段综合 | 对应 band | 典型组合 |
|---------|----------|---------|
| 全 high + 论述性达标 | **5 档 (17-20)** | descriptive/interpretive/analytical 全 high + is_dialectical=true |
| 2 高 1 中 + 论述性达标 | **4 档 (13-16)** | 描述高 + 阐释中 + 评论高 |
| 全 mid 或 2 中 1 高 + 论述性弱 | **3 档 (9-12)** | 三段齐全但质量中等，单向论证 |
| 1 高 2 低 / 缺 1 段 | **2 档 (5-8)** | 三段论结构不完整 |
| 全 low 或缺 2+ 段 | **1 档 (1-4)** | 只有描述或只有评论 |

**交叉验证**：此表仅作粗粒度定档，最终分数仍需结合 5 维观察点（`dimension_diagnosis`）和语言准确性做档内调节。

---

## 七、低频题型的防御策略

若 `task_subtype ∈ {descriptive_theoretical, narrative_theoretical, expository_theoretical}`：

1. `paragraph_diagnosis` 字段置 `null`（不适用三段论）
2. `meta.calibration_status = "low_frequency_theoretical"`
3. 在报告开头添加免责声明：
   ```
   ⚠️ 检测到本题目为 {文体}，属于考研英一 B 节大纲中的低频题型
      （近 20 年真题未出现）。本批改基于通用 5 维 rubric 给出，
      分数置信度较常见"漫画+议论"题型低，仅供参考。
   ```
4. 改用通用 5 维 rubric（见 `postgrad-official-rubric.md` 第四节）
5. 不触发本文第四节的论述性检查

---

## 八、参考

- [postgrad-official-rubric.md](postgrad-official-rubric.md) 第二节（5 档描述原文）
- [writing-vocabulary.md](writing-vocabulary.md) 第六节（论述性文章加分表达）
- 2005-2025 年英语一 B 节真题（本 Rubric 的归纳基础）
