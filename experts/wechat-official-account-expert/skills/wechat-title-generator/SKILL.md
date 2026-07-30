---
name: wechat-title-generator
description: "公众号标题生成与评估技能。基于已确认的选题、大纲、目标读者和文风 DNA，生成 8 个覆盖不同力度层级的标题候选，筛除低质/违规标题，逐项打分，并推荐 1 个最优标题外加 1 个更稳妥版本和 1 个更强传播版本。适用于写作前或写作后的定题阶段，不负责正文。当用户需要为文章起标题、做标题 A/B 备选或标题打分时使用此技能。"
description_zh: "为公众号文章生成 8 个标题候选并打分推荐最优解（含更稳妥/更强传播备选）"
description_en: "Generate and score 8 WeChat article title candidates and recommend the best one"
version: 0.1.0
allowed-tools: Read,Write
metadata:
  clawdbot:
    emoji: "🎯"
---

# Wechat Title Generator

## 目标
稳定产出高点击意愿、不过度标题党、符合公众号语境的标题，并明确推荐最优解。

## 输入
1. 已确认的选题和大纲（来自 `wechat-topic-outline-planner`）
2. 目标读者
3. 文章目标
4. 文风 DNA（来自 `wechat-style-profiler`）
5. 可选的风险边界

## 工作流
1. 先提炼文章承诺、情绪点、反差点和读者收益。
2. 使用 `references/title-rubric.md` 生成 8 个标题，覆盖不同力度层级。
3. 筛除违反硬约束的标题。
4. 对保留标题逐项评分，并推荐 1 个最佳标题。
5. 同时给出 1 个更稳妥版本和 1 个更强传播版本。

## 输出契约
按以下顺序输出：
1. `Title Strategy`
2. `Title Candidates x8`
3. `Best Title Recommendation`
4. `Safer Alternative`
5. `Stronger Alternative`
6. `Eliminated Titles And Why`

## 硬约束
- 必须生成恰好 8 个标题。
- 标题不能出现引号。
- 标题不能出现冒号。
- 标题不能出现破折号。
- 标题中如果出现两个或以上分句，分句之间必须使用逗号。
- 标题要有情绪或反差。
- 可以适度夸张，允许使用高情绪表达，比如"这是我读过最好的一篇文章""我看到了新世界的大门""我被震到了"这一类强感受句式。
- 夸张必须仍然和正文内容一致，不能靠编造收益或虚构结果制造点击。
- 标题必须和文章真实内容一致。

## 边界
- 不写大纲，不写正文。
- 如果主题还没定，先交给 `wechat-topic-outline-planner`。

## 与本专家其它技能的衔接
- 上游：`wechat-topic-outline-planner`（大纲）、`wechat-draft-writer`（初稿）、`wechat-style-profiler`（文风 DNA）。
- 下游：定题后 → `humanizer`（去 AI 味）→ `mp-draft-push`（推送草稿箱）。

## 参考文件
- 标题评分：`references/title-rubric.md`
