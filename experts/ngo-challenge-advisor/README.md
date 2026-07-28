# NGO 发题顾问 · 题小策

Agent 型 WorkBuddy Expert，附带 `ngo-challenge-designer` Skill。通过点击式自适应访谈，把 NGO 的一个真实工作痛点整理成可用于 WorkBuddy Skill/Expert 比赛的赛题。

## 核心特点

- 第一题选择赛道，第二题直接选择痛点；
- 每次回答后动态预填下一题的 3–4 个点击选项；
- 保留自由输入，不把未确认选项当作事实；
- 自动形成结构化赛题和标题；
- 明确选择「確認提交審批」后才生成提交档；
- 确认后自动提交至平台审批队列；失败时提供完整 JSON 与管理端导入兜底。

## 提交与发布流程

1. 访谈完成并经 NGO 明确确认后，题小策生成并本地校验结构化赛题 JSON；
2. 题小策通过公开提交脚本直接送入平台审批队列，不需要管理员口令，也不能直接发布；
3. 自动提交失败时，才输出 JSON，交由管理员在 `https://skillschallenge.edgeone.dev/admin/import` 导入；
4. 管理员审批通过后，赛题在公开页 `https://skillschallenge.edgeone.dev/` 显示。

## 试用问法

- 我想把 NGO 的一个真实工作痛点整理成比赛赛题
- 帮我从几个 NGO 痛点中选出最适合发题的一个
- 帮我检查这道 NGO 赛题是否已经适合发布

## 文件结构

- `.codebuddy-plugin/plugin.json`：专家展示与资源声明
- `agents/ngo-challenge-advisor.md`：专家角色与工作流程
- `skills/ngo-challenge-designer/`：发题访谈 Skill（含访谈流程、赛题结构、适配规则、示例与本地校验脚本）
- `avatars/expert.png`：专家头像
