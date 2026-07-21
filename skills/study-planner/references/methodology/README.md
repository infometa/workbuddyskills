# 方法论选型矩阵

本目录收录 4 大学习方法论的完整 reference。AI 在生成 plan.json 时按下表选型。

## 一图选型

```
用户场景                              首选方法论组合
────────────────────────────────  ──────────────────────────
雅思/托福/考研英语 等语言考试     ebbinghaus + pareto + pomodoro
考研政治/法考/医学 大量记忆        ebbinghaus(重度) + pareto
编程/算法/技能习得                feynman(重度) + pomodoro
学科理解（数学/物理/工程）         feynman(标准) + pareto
碎片化时间用户（通勤/课间）         pomodoro + ebbinghaus
追求"真正学懂"而非应试              feynman + pareto(轻量)
```

## 详细矩阵

| 方法论 | 解决什么问题 | 触发关键词 | 强度档位 | 与其他叠加 |
|-------|------------|-----------|---------|-----------|
| [ebbinghaus](./ebbinghaus.md) | 容易忘 | 记忆/单词/公式/术语 | 轻/标/重 | + pareto, + feynman |
| [pareto](./pareto.md) | 时间不够 | 应试/冲刺/抓重点 | 轻/标/重 | + ebbinghaus, + pomodoro |
| [pomodoro](./pomodoro.md) | 专注不够 | 分心/拖延/碎片时间 | 轻/标/深度 | 与所有方法论正交 |
| [feynman](./feynman.md) | 理解不深 | 学懂/编程/skill | 轻/标/重 | + ebbinghaus, + pareto |

## AI 选型决策树

```
Q1：用户是为了「应试拿分」还是「真正掌握」？
├─ 应试 → 必选 pareto + ebbinghaus
└─ 掌握 → 必选 feynman
        └─ 是否含大量记忆？是 → 加 ebbinghaus

Q2：用户每日时间预算多少？
├─ < 60min/天 → 必加 pomodoro（碎片化）
├─ 60-180min   → 可加 pomodoro（标准）
└─ > 180min    → pomodoro 深度档或不加

Q3：用户性格描述？
├─ "容易分心/拖延" → 加 pomodoro
├─ "总是学了忘"   → 加 ebbinghaus
├─ "学不懂/不会用" → 加 feynman
└─ "时间紧任务重" → 加 pareto
```

## plan.json 中如何声明

```json
{
  "methodologies": ["ebbinghaus", "pareto", "pomodoro"],
  "methodology_intensity": {
    "ebbinghaus": "standard",
    "pareto": "standard",
    "pomodoro": "light"
  }
}
```

> 同一计划可声明 1-3 种方法论，**不建议超过 3 种**（认知负担过重，反而降低执行力）。

## 与 examples/ 的对应关系

| 示例文件 | 应用方法论 | 强度 |
|---------|-----------|------|
| example-ielts-30d.json | ebbinghaus + pareto + pomodoro | 标 / 标 / 标 |
| example-kaoyan-120d.json | ebbinghaus + pareto + pomodoro | 重 / 重 / 标 |
| example-react-60d.json | feynman + pomodoro | 重 / 深度 |

参考 examples 时，可同步参考其方法论组合。
