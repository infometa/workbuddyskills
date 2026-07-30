# 实证研究团 (Empirical Research Team)

覆盖社会科学实证研究全流程的 AI 专家团队：因果推断、稳健性检验、出版级表图写作与降 AIGC。

## 团队构成

| 成员 | 花名 | 职责 |
|------|------|------|
| 🎯 主理人 | 论笃行 | 研究总编排，需求理解→方法路由→SOP调度→汇编交付 |
| 📊 计量经济学家 | 顾因果 | DID/IV/RDD/SCM/DML 因果推断与建模 |
| 🔧 数据工程师 | 洗澄明 | 数据清洗、变量构建、描述统计、诊断检验 |
| 🛡️ 稳健性审计师 | 严复核 | 安慰剂/规范曲线/Oster/HonestDiD 敏感性 |
| ✍️ 学术写作专家 | 文锦成 | AER 风格论文写作 + 发表级表图 |
| 🔍 降AIGC审稿模拟 | 去伪存 | 中英文去AI + 对抗性审稿 + R&R回复 |

## 覆盖能力

- **因果推断方法**：DID（含交错）、IV/2SLS、RDD、SCM/SDID、DML/因果森林
- **完整流水线**：9 阶段（选题→文献→数据→识别→估计→稳健性→写作→降AIGC→投稿）
- **三种域模式**：应用经济学（默认）/ 流行病学 / ML因果
- **输出标准**：5 必需表格 + 4 必需图形 + 三格式导出（.xlsx/.tex/.docx）

## 快速开始

```
帮我用 DID 方法分析一项政策的处理效应，从数据清洗到发表级表格
```

```
我有一篇完成的中文实证论文初稿，帮我降低 AIGC 检测率
```

```
帮我设计一个 IV 策略并评估工具变量的有效性
```

## 技术栈

**主要（Python）**：
- `pyfixest` — 快速固定效应估计 + etable 导出
- `statsmodels` / `linearmodels` — OLS/IV/面板
- `rdrobust` / `rddensity` — RDD 估计和诊断
- `econml` / `causalml` — DML/元学习器/因果森林
- `matplotlib` / `seaborn` — 发表级图形

**参考（Stata/R）**：
- Stata: `reghdfe`, `ivreg2`, `csdid`, `rdrobust`
- R: `fixest`, `did`, `HonestDiD`, `synthdid`

## 目录结构

```
empirical-research-team/
├── .codebuddy-plugin/
│   └── plugin.json          # 专家配置
├── agents/                   # 团队成员定义
│   ├── empirical-research-team-team-lead.md
│   ├── causal-analyst.md
│   ├── data-engineer.md
│   ├── robustness-auditor.md
│   ├── academic-writer.md
│   └── deaigc-reviewer.md
├── skills/
│   └── aers-reference/      # 方法论参考 & 代码模板
│       ├── SKILL.md
│       ├── references/
│       │   ├── design-selector.md
│       │   ├── output-spec.md
│       │   └── methods-reference.md
│       └── templates/python/
│           ├── did_template.py
│           ├── iv_template.py
│           └── rdd_template.py
├── avatars/                  # 团队头像
├── LICENSE/                  # 许可证文件
│   ├── README.md
│   ├── CC-BY-SA-4.0.txt
│   └── MIT-aer-skills.txt
├── settings.json
└── README.md                 # 本文件
```

## 致谢与开源许可声明

本专家的设计方法论和知识体系参考了以下开源项目，感谢该项目及其贡献者：

**项目名称：** Auto-Empirical Research Skills (AERS)  
**项目地址：** https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills  
**开源许可证：** CC-BY-SA-4.0 (Creative Commons Attribution-ShareAlike 4.0 International)

适用于本专家所参考的开源项目版本的许可证原文，可查阅专家包内 `LICENSE/` 文件夹。

如本专家包含源自上述项目的开源内容，该等内容仍受原开源许可证约束，本声明不改变、替代或限制该等许可证项下的任何权利和义务。用户在使用、修改或分发该等内容时，应自行查阅并遵守原开源许可证，包括其中适用的署名、声明保留、源代码提供及相同许可证授权等要求。

---

### 参考内容索引

本专家团转化了以下具体 Skills 的方法论与工作流设计：

| 来源 Skill | 引用内容 | 查看 |
|------------|---------|------|
| Full Empirical · Python (00.1) | 8步实证流程、代码模板、输出规范 | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/00.1-Full-empirical-analysis-skill_Python) |
| AER-Skills (50) | 15个投稿子skill、识别策略、审稿模拟 | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/50-brycewang-aer-skills) |
| Chinese De-AIGC (48) | 17类中文AI痕迹模式、五步降AIGC | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/48-copaper-ai-chinese-de-aigc) |
| CausalPy (51) | 贝叶斯准实验估计 | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/51-pymc-labs-CausalPy) |
| Causal Inference Mixtape (10) | DID/IV/RDD/SCM模板 | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/10-Jill0099-causal-inference-mixtape) |
| Research Methods (61) | 数据清洗/验证/EDA | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/61-scdenney-research-methods) |
| Econ Writing Skill (56) | 经济学写作指南 | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/56-ariel-saffer-econ-writing-skill) |
| Citation Checker (62) | 引用完整性核验 | [查看](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/skills/62-PHY041-claude-skill-citation-checker) |

> 注：skills/54 (CC-BY-NC-4.0) 因非商用限制未被引用。

### 延伸阅读

- **方法论分类体系**：[TAXONOMY.md](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/blob/main/docs/TAXONOMY.md)
- **现成研究提示词**：[GOLDEN_WORKFLOWS.md](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/blob/main/docs/GOLDEN_WORKFLOWS.md)
- **Skill 搜索界面**：[search.html](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/blob/main/docs/search.html)
- **完整中文文档**：[CONTENT_ZH.md](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/blob/main/docs/CONTENT_ZH.md)
- **数值基准测试**：[benchmark/](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills/tree/main/benchmark)

### 学术引用格式

如需在学术工作中引用 AERS：
```bibtex
@software{aers2026,
  author = {Wang, Bryce},
  title = {Auto-Empirical Research Skills (AERS)},
  year = {2026},
  url = {https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills},
  note = {Stanford REAP × CoPaper.AI}
}
```
