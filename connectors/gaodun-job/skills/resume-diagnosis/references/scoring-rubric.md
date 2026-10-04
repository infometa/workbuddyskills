# 六维评分规则（Scoring Rubric）

> **规则说明**：本文件定义 6 维评分的全部确定性公式与查表，由 `scripts/resume_pipeline.py`（finalize / build-report）执行；配置值以 `references/resume-score-config.json` 为准。
>
> 总分 = 6 个维度得分直接求和（`sumScore = completeScore + descriptionScore + learningAbilityScore + professionalAbilityScore + creativeLeadershipScore + careerAbilityScore`）。

## 权重配置（真实值，已落盘）

所有权重/映射来自 `references/resume-score-config.json`（已落盘的权威配置）。

`moduleScoreMap`（6 维占比权重，合计 100）：

| 维度 | key | 权重 |
|---|---|---|
| 简历完整度 | `resumeComplete` | **20** |
| 经历描述 | `experienceDesc` | **50** |
| 学习能力 | `learningAbility` | **15** |
| 专业能力 | `professionalAbility` | **5** |
| 创新领导力 | `creativeLeadership` | **5** |
| 职场能力 | `workplaceAbility` | **5** |

所有乘除均为**整数运算**（先乘后除、结果截断取整）。

> ⚠️ **注意**：`professionalAbilityScoreMap` / `creativeLeadershipScoreMap` / `workPlaceScoreMap` 曾出现配置与注释不一致的情况。**一律以本文件的真实配置值为准**。

---

## 维度 1：简历完整度

公式：`完整度分 = 已填字段记录数 × resumeComplete(20) / 可见字段总记录数`（整数截断）。

- 分子：`showFields` 中 `dataFieldValue` 非空白的**记录数**（同一字段 3 段实习算 3 条）。
- 分母：`showFields` 总记录数。
- 权重 key：`resumeComplete` = **20**。
- 异常 → 返回 0。

## 维度 2：经历描述（LLM 评分）

公式：`经历描述分 = (score>0 的模块 LLM 分均值) × experienceDesc(50) / 100`（整数截断）。

- 模块分来自一次 LLM 评分调用（不是逐字段调用），Prompt 原文见 `resume-score-prompt.txt`，协议如下：
  - 输入拼接：按 `scoreGptConfig.fieldList`（moduleName/moduleCode/dataFieldCode）组装，隐藏模块跳过；每个字段拼 `模块名{序号}：\n{字段值}\n`；
  - GPT 返回 `{"score": {"<模块名>": <int>}}`，按 moduleName→moduleCode 映射回填；
  - 只对 `score != null && score > 0` 的模块求均值；无有效模块分 → 返回 0。
- 权重 key：`experienceDesc` = **50**；除以 100。即 `经历描述分 = 模块 LLM 均分 / 2`（整数截断）。
- 任何异常 → 返回 0。

## 维度 3：学习能力

公式：`学习能力分 = 学历最高分 × learningAbility(15) / 10`（整数截断）。

- 只取 `dataFieldCode == qualification` 的记录，取**最高**学历分；无记录 → 0。
- **注意：不使用 `classRank`（成绩排名）**：教育经历的 `classRank` 字段已从配置删除；`classRankScoreMap` 仍存在于评分配置但脚本不引用，本 skill 不计入。
- ⚠️ **精确匹配的前置条件**：表中左列是**入库标准值**。解析阶段必须把自由文本归一化（"本科"→"大学本科"、"硕士"→"硕士研究生"、"大专"→"大学专科"，完整映射见 `analysis-resume-rules.md` §2.1）。**拿着"本科"原文来做这张表的精确匹配，永远得 0 分——这是曾造成总分差 10 分的真实缺陷。**
- 学历值 → 分数的映射链（`PROFESSION_MAP` + 配置 `qualificationScoreMap`，见 `resume_pipeline.py`）：

| 简历中的学历值（必须完全匹配） | map key | 分值 |
|---|---|---|
| 博士研究生 | `doctor` | 10 |
| MBA | `mba` | 9 |
| 硕士研究生 | `master` | 8 |
| 大学本科 | `undergraduate` | 7 |
| 大学专科 | `specialist` | 6 |
| 高中 | `highSchool` | 3 |
| 初中 | `juniorHighSchool` | 配置中无此 key → **0** |
| 小学 | `primarySchool` | 配置中无此 key → **0** |
| 其他/未匹配 | `""` | 0 |

- 例：大学本科 → 7 × 15 / 10 = **10**（int 截断）；硕士研究生 → 8 × 15 / 10 = **12**。
- 权重 key：`learningAbility` = 15；除以 10。
- 异常 → 返回 0。

## 维度 4：专业能力（三项命中制）

命中判定（每类内任一字段非空白即命中 1 次）：

| 类别 | 命中字段（任一非空） |
|---|---|
| 语言 | `languageClassify` / `languageDesc` / `languageSkill` |
| 职业资格 | `certificateName` / `certificateDesc` / `qualificationCertificate` |
| 软件操作 | `softwareName` / `softwareDesc` / `softwareOperation` |

查表 `professionalAbilityScoreMap`（命中数 → 基础分，**真实配置值**）：

| 命中数 | 基础分 |
|---|---|
| 3 | 9 |
| 2 | 8 |
| 1 | 7 |
| 0 | 0 |

公式：`专业能力分 = 命中基础分 × professionalAbility(5) / 10`（整数截断）。

- 权重 key：`professionalAbility` = 5。例：3 项全中 → 9 × 5 / 10 = **4**（整数截断）。异常 → 0。

## 维度 5：创新领导力（四类模块命中制）

命中判定（每个模块内任一字段非空白即命中 1 次）：

1. `projectExperience`（项目经历）
2. `practicalExperience`（实践经历）
3. `competitionExperience`（比赛经历）
4. `campusActivities`（校内活动）

查表 `creativeLeadershipScoreMap`（命中类数 → 基础分，**真实配置值**）：

| 命中类数 | 基础分 |
|---|---|
| 4 | 9 |
| 3 | 9 |
| 2 | 8 |
| 1 | 7 |
| 0 | 0 |

公式：`创新领导力分 = 命中基础分 × creativeLeadership(5) / 10`（整数截断）。

- 权重 key：`creativeLeadership` = 5。例：中 2 类 → 8 × 5 / 10 = **4**。异常 → 0。

## 维度 6：职场能力（总月数阶梯）

**月数计算**——实习与工作分别计算后相加：

1. 取 `internshipStartTime` / `workStartTime` 非空记录；
2. 按 `dataId` 配对同一条记录的 endTime（`internshipEndTime` / `workEndTime`）；**无配对结束时间的记录不计月数**；
3. 起止时间按 `yyyy-MM` 解析，每段月数 = `(结束年−起始年)×12 + (结束月−起始月) + 1`（含起止月）；解析失败该段跳过；
4. `months = 实习总月数 + 工作总月数`。

查表 `workPlaceScoreMap`（**真实配置值**）：key 格式 `"下限--上限"`，命中条件为 **`months > 下限 && months <= 上限`**（首个命中即停）：

| 配置 key | 区间（月） | 基础分 |
|---|---|---|
| `0--6` | 0 < X ≤ 6 | 4 |
| `6--12` | 6 < X ≤ 12 | 5 |
| `12--24` | 12 < X ≤ 24 | 7 |
| `24--99999999` | X > 24 | 9 |
| — | 无数据（0 个月） | 0（`0 > 0` 不成立，不匹配任何区间） |

公式：`职场能力分 = 阶梯基础分 × workplaceAbility(5) / 10`（整数截断）。

- 权重 key：`workplaceAbility` = 5。例：共 8 个月 → 5 × 5 / 10 = **2**（整数截断）。异常 → 0。

---

## 总分

总分 = 六维得分直接求和：

```text
sumScore = completeScore + descriptionScore + learningAbilityScore
         + professionalAbilityScore + creativeLeadershipScore + careerAbilityScore
```

- 与诊断是**两条并行链路**：分数链路与诊断链路互不影响，各自异常时不阻断另一条。
- 报告阶段的分数区间话术（title/describe/beatPercent）见 `diagnose-output-template.md`。
