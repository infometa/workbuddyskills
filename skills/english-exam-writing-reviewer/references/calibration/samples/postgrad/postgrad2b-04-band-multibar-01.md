---
exam_level: Postgrad2B
band: 4
raw_score: 11
task_subtype: multi_bar
task_type: chart
anchor_tags: [v1.6, new-chart-subtype-anchor, multi-bar-comparison]
reference_source: "基于考研英语二 2019 年双柱对比题（城乡居民消费结构）风格自构"
prompt: |
  Write an essay of 150 words based on the bar chart below, in which you should:
  1) describe the chart, and
  2) give your comments.
  The chart compares the consumption structure of urban and rural households in
  China in terms of five categories: food, housing, education, healthcare and others.
---

# 样例作文原文

```
The dual bar chart juxtaposes the consumption structure of urban and rural
households in China across five categories. While the two groups share the same
three priority items—food, housing and education—the proportions diverge markedly.

Specifically, rural households allocate the lion's share of their expenditure to
food (38%), whereas for urban families food accounts for only 25%. Urban
households, by contrast, invest far more in housing (32% versus 18% in rural
areas) and in education (15% versus 9%). Healthcare spending remains roughly
comparable at around 10% for both groups, while other miscellaneous items are
also similar.

The divergence reflects two underlying factors. First, urban residents enjoy
higher disposable incomes, enabling them to spend more on quality housing and
educational resources. Second, rural areas have comparatively lower housing
costs, shifting a greater proportion of expenditure toward necessities such as
food.
```

（正文约 157 词）

---

# 人工阅卷批注（Postgrad2B · multi_bar · 第四档）

## multi_bar 专属检查项（v1.6 新增）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 两组并列明确 | 开头明确"两组对比" | `juxtaposes... urban and rural households... across five categories` | ✅ |
| 相似点 | 必须指出 ≥ 1 处相似 | `share the same three priority items` + `Healthcare... roughly comparable` + `other... also similar` | ✅ 3 处相似 |
| 差异点 | 必须指出 ≥ 2 处差异 + 数据 | food (38% vs 25%) + housing (32% vs 18%) + education (15% vs 9%) = 3 处差异全带定量数据 | ✅ |
| 不可只描述一组 | 两组数据均出现 | ✅ 每个类别都有 urban 和 rural 双数据 | ✅ |
| 结构迁移 / 归因 | 有"反映了什么 + 为什么" | `The divergence reflects two underlying factors. First,... Second,...` | ✅ 双维度归因 |

→ **5/5 项 multi_bar 专属检查全部达标**，这是按 `chart-verbs.md` §2.5 定义的 multi_bar 高档位表现。

## 数据精准度检查（考研英二 B 必做）

| 数据点 | 本文数值 | 检查 |
|-------|---------|------|
| Rural food 38% | 出现 ✅ |
| Urban food 25% | 出现 ✅ |
| Urban housing 32% | 出现 ✅ |
| Rural housing 18% | 出现 ✅ |
| Urban education 15% | 出现 ✅ |
| Rural education 9% | 出现 ✅ |
| Healthcare (both ~10%) | 出现（`around 10%`）✅ |
| Others | 简略带过（`also similar`）——**轻微模糊** | ⚠️ tip 级 |

→ 数据覆盖率 8/9 ≈ 89%，**1 处数据模糊**（others 未给具体数字）。按 `chart-verbs.md` §4 规则，< 2 处数据错位 → 不触发 `data_inaccuracy: critical`。

## 5 维诊断

1. **任务完成度**：包含所有内容要点，两组对比 + 相似 + 差异 + 归因齐全；仅 others 类数据略模糊
2. **语法结构与词汇**：较丰富
   - 非谓语：`enabling them to spend more...` ¶3
   - 对比结构：`whereas / by contrast / while` 三种变体
   - High-tier 词：`juxtaposes / lion's share / diverge markedly / miscellaneous / disposable incomes`
3. **语言准确性**：语言基本准确，仅 1 处 tip 级
4. **衔接与连贯**：`Specifically / by contrast / while / The divergence reflects... First... Second...` 形成清晰递进
5. **格式与语域**：学术正式体，无口语化

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 末 | `other miscellaneous items are also similar` | `other miscellaneous items remain comparable at approximately X% each` | tip | data_inaccuracy（应给具体数值，英二 B 节重视数据精准度）|

合计 0 critical + 0 warning + 1 tip — 符合考研英二 B 节第四档"语言基本准确，只有在试图使用较复杂结构或较高级词汇时才有个别错误"。

## 为什么第四档不是第五档（multi_bar 视角）

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| multi_bar 专属五要素齐全 | 5/5 | 5 |
| 数据覆盖率 | 8/9 ≈ 89%（others 略模糊）| 4（5 档要求 ≥ 95%）|
| 归因深度 | 双维度归因（收入 + 成本结构）| 4-5 边界 |
| 语言丰富度 | `juxtaposes / lion's share / disposable incomes` 3 处 high-tier；但未触及 academic（如 `dichotomy / stratification`）| 4 |
| 复杂结构变体 | 非谓语 ×1 + 对比 ×3，但**无倒装 / 强调句** | 4（5 档期望 ≥ 1 处倒装强调，如 `Only against urban-rural income gap can these patterns be fully understood`）|
| 字数 | 157 词，落在 140-160 区间 | 无扣分 |

→ 结构完整 + 数据精准 + 双维归因 = **第四档（11 分）**，未达第五档是因：
① others 类数据模糊（1 处 tip）
② 词汇未触及 academic tier
③ 无倒装强调结构

## 为什么第四档不是第三档

- ✅ multi_bar 两组全覆盖（第三档常只描述一组 = `critical 失误`，见 `chart-verbs.md` §5）
- ✅ 差异点带完整定量对比（第三档常只说"变大变小"）
- ✅ 有归因段（第三档常止于描述数据）
- ✅ 语言无 critical 错误

→ 明显优于第三档。

## 升档路径（Postgrad2B multi_bar · 4 → 5）

1. **补全 others 数据精准度**：
   - `other miscellaneous items are also similar` → `other miscellaneous items remain comparable, at 7% for urban and 10% for rural families respectively`
2. **加 academic tier 词汇**（1-2 处即可）：
   - `The divergence reflects` → `This dichotomy epitomizes the broader stratification of consumption patterns`
   - `enabling them to spend` → `affording them the latitude to allocate`
3. **加倒装强调**（第五档硬门槛）：
   - `The divergence reflects two underlying factors.` → `Only by examining urban-rural income disparities can such divergence in consumption priorities be adequately explained.`
4. **加"结构迁移"框架词**（multi_bar 第五档特征）：
   - `The divergence reflects` → `What emerges is a structural contrast: urban households pivot toward capital-intensive investment (housing, education), while rural counterparts remain anchored in subsistence expenditure`
5. **结尾加政策启示**（考研英二 B 第五档常见加分点）：
   - 加 1 句 `Bridging this gap calls for concerted policy interventions targeting rural income growth and housing cost containment.`

---

# 该样例用途

- **v1.6 新 chart_subtype = multi_bar 锚点样例**：第一篇 multi_bar 校准
- **multi_bar 高档位金标**：展示"两组并列 + 相似 3 处 + 差异 3 处定量 + 双维归因"五要素齐全的考研英二 B 节典范
- **数据精准度细粒度演示**：8/9 数据覆盖触发 tip 级（而非 critical）→ 不降档但卡在 4 档
- **Step 2 task_subtype 识别**：题目 Directions 含"compares... in terms of five categories"明示多维对比 → Skill 应识别 `task_subtype = "multi_bar"` 并启用专属检查
- **教学价值**：中国考生写 multi_bar 最大雷区是**只描述一组**（"以农村为主，城市如下..."）；本文通过 3 处 `whereas / by contrast / while` 变体示范了正确写法
