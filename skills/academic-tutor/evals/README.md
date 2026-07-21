# Evals · academic-tutor

> 用于 skill-creator / skill-assistant 标准评测的两份契约文件。

| 文件 | 作用 |
|---|---|
| `evals.json` | 端到端 6 用例（5 happy + 1 越界拒答） |
| `trigger-eval.json` | 触发率：8 should-trigger + 8 should-not-trigger（与边界相邻能力紧贴） |

---

## 跑法

```bash
# 通过 skill-assistant 跑（推荐）
> "评测 academic-tutor skill"

# 通过 skill-creator 跑
> "skill-creator 评测 academic-tutor"
```

---

## evals.json · 6 用例总览

| ID | 场景 | 验证点 |
|----|------|-------|
| 1 | 高数不定积分题 | 三段式格式 / 不给答案 / 用户行为动词 |
| 2 | 概念辨析（边际效用） | concept 意图识别 / 类比迁移 |
| 3 | 论文选题（小样本） | paper-topic 意图 / 选题三角 / 可选推荐其它能力 |
| 4 | 论文修改不代写 | NEVER 5 / 诊断而非改写 |
| 5 | 情绪低落共情 | NEVER 8 / tone 临时降档 |
| 6 | 越界拒绝（代写引言） | refusal-boundaries.md 标准话术 |

---

## trigger-eval.json · 16 用例总览

### should-trigger（8）

题目讲解 / 概念辨析 / 论文选题 / 论文论证 / 审稿应对 / 数据结构 / profile 更新 / tone 切换

### should-not-trigger（8）

规划类（备考计划）/ 打卡陪伴类（打卡）/ 知识结构梳理类（整门课）/ 
文献速读类（批量速读）/ 学术翻译类（学术翻译）/ 
应试英语批改类（雅思作文）/ 简历专项（简历）/ 寒暄

---

## expectations 字段命名规范

每条 eval 的 `expectations` 是字符串数组，每条期望应：

- ✅ **可测试**：能通过自动 / 半自动方式判断 pass/fail
- ✅ **简洁**：每条不超过 30 字
- ✅ **聚焦单一约束**：一条只验一件事
- ❌ 不要写"AI 应表现专业""回复要好"这种主观期望
