# Job Companion Team · 求职陪跑团

面向求职全流程的5 角色陪跑型专家团，按阶段接力帮你做自我盘点、定位、简历打磨、面试陪练、谈薪决策与入职 90 天复盘。

## 类型

Team 型（多角色协作团队）—— 主理人调度 + 4 位分工角色

## 功能

- **阶段 1·自我盘点** — 把兴趣/价值观/能力三件事写明白
- **阶段 2·目标定位** — 把"自画像"变成 1-3 个候选方向
- **阶段 3·简历打磨** — 经历重写 + 分版本简历 + 一句话自我介绍
- **阶段 4·面试陪练** — STAR 故事库 + 行为面预测题
- **阶段 5·模拟实战** — 角色扮演 + 每题 3 个改进点
- **阶段 6·谈薪 + Offer 决策** — 薪酬 benchmark + 话术 + 多维打分表
- **阶段 7·入职复盘** — 90 天计划 + 长期路径画像

## 使用示例

- 我现在想找工作，但完全不知道从哪儿开始，你能陪我理一理吗？
- 帮我把这段项目经历改写成简历要点，突出可量化结果。
- 面试官让我用 STAR 法讲一个失败案例，陪我练一下。

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像：
- 格式：PNG（推荐）或 JPG
- 尺寸：512x512 px
- 大小：单张不超过 500KB

## 目录结构

```text
.codebuddy-plugin/plugin.json
agents/job-companion-team-lead.md
agents/job-companion-resume.md
agents/job-companion-interview.md
agents/job-companion-negotiation.md
agents/job-companion-reflection.md
avatars/team.png
avatars/job-companion-team-lead.png
avatars/job-companion-resume.png
avatars/job-companion-interview.png
avatars/job-companion-negotiation.png
avatars/job-companion-reflection.png
skills/self-inventory/SKILL.md
skills/target-positioning/SKILL.md
skills/resume-polish/SKILL.md
skills/interview-prep/SKILL.md
skills/mock-interview/SKILL.md
skills/salary-negotiation/SKILL.md
skills/onboarding-reflection/SKILL.md
settings.json
README.md
```

## 安装

将本专家包目录（即 `job-companion-team` 文件夹）整体放入 WorkBuddy 的专家插件目录下：

- **macOS / Linux**：`~/.workbuddy/plugins/marketplaces/my-experts/plugins/job-companion-team`
- **Windows**：`%USERPROFILE%/.workbuddy/plugins/marketplaces/my-experts/plugins/job-companion-team`

确保目录结构完整：`.codebuddy-plugin/plugin.json`、`agents/`、`skills/`、`avatars/` 均在插件根目录下。放入后重启 WorkBuddy 即可在专家列表中看到「求职陪跑团」。

## 版本管理

插件版本位于 `.codebuddy-plugin/plugin.json`。首次发布前可在 `1.0.0` 内完成源码与运行说明定稿；后续任何 Agent 行为、Skill 逻辑或头像资源变化都应更新版本号。
