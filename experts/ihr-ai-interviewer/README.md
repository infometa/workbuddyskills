# 利唐智语AI面试官

围绕岗位画像设计面试维度与题库，管理数字人面试模板，校验候选人信息并发起面试，回查面试记录与纪要。

## 专家信息

| 项目 | 内容 |
|---|---|
| 类型 | Agent 型专家 |
| 技术标识 | `ihr-ai-interviewer` |
| 中文名称 | 利唐智语AI面试官 |
| 英文名称 | AI Interviewer |
| 中文职业 | 数字人招聘面试专家 |
| 英文职业 | Digital Avatar Recruitment Interview Specialist |
| 作者 | 利唐智语团队 |
| 联系邮箱 | olivia.zhang@ihr360.com |
| 行业分类 | `09-OperationsHR` 运营人力 |
| 版本 | 1.0.0 |
| 规范基线 | WorkBuddy 专家开发规范 v2.3（2026-06-25） |

## 核心功能

1. 根据岗位职责、招聘类型、面试轮次和候选人层级设计结构化面试方案。
2. 搜索并复用已发布的数字人面试模板。
3. 在用户明确授权后，dry-run 校验并创建发布新的数字人面试模板。
4. 校验唯一候选人的身份与联系方式，安排和发起数字人面试。
5. 搜索历史面试，按权限读取纪要、摘要、待办和完整转写。

## 目录结构

```text
ihr-ai-interviewer/
├── .codebuddy-plugin/
│   └── plugin.json
├── agents/
│   └── ihr-ai-interviewer.md
├── avatars/
│   └── expert.png
├── skills/
│   ├── ihr-shared/
│   ├── ihr-base/
│   └── ihr-conference/
├── README.md
└── SUBMISSION_CHECKLIST.md
```

## 推荐使用方式

- 给 [候选人姓名] 发起一场 [岗位名称] 的数字人面试，要求在 2 天内完成。
- 请帮我给 [候选人姓名/手机号] 配置一场 [岗位名称] 的数字人面试，重点考察 [如：项目管理/沟通能力]，要求24小时内完成，并生成面试邀请
- 请帮我给候选人 [姓名]（[手机号]）配置一场 [岗位名称] 的数字人面试。6道题左右，重点考察 [如：项目管理/沟通能力]，通知候选人在 [如：24小时内] 完成，并自动生成面试邀请通知短信。

## 运行依赖

- `ihr-cli`
- 默认运行环境：`work100-prod`（已确认）
- 首次使用时按 Agent 内置安装指南完成安装、配置与登录。

## 头像

头像位于 `avatars/expert.png`。如需替换，请保持：

- PNG 或 JPG
- 512 × 512 px
- 单张不超过 500KB
- 专业、自然、无侵权或违规元素

## 打包提交

在本目录的上一级执行：

```bash
zip -r ihr-ai-interviewer-workbuddy-v1.0.0.zip ihr-ai-interviewer/
```

提交前请按 `SUBMISSION_CHECKLIST.md` 完成自检。
