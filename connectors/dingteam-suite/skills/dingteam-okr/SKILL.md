---
name: dingteam-okr
description: Teach the AI how to use the DingTalk OKR connector to list periods and objectives, generate alignment charts, and submit or update OKRs.
description_zh: 教 AI 使用钉钉 OKR 连接器查询目标周期与目标、生成对齐图、提交与更新 OKR。
description_en: Teach the AI how to use the DingTalk OKR connector to list periods and objectives, generate alignment charts, and submit or update OKRs.
version: 1.0.0
author: dingteam
---

# 钉钉 OKR 连接器使用说明

## 何时使用

用户提出以下请求时，调用本连接器的工具：

- 查看 / 列出 OKR 周期（季度、月度目标周期）
- 查询某一周期下的 O（目标）与 KR（关键结果）列表
- 查询某人的 OKR、某个部门的 OKR
- 生成目标对齐图 / 对齐关系图
- 查询 OKR 模块设置（是否开启、权重规则等）
- 查询 OKR 相关任务列表与进度
- 提交、更新 OKR 或 KR 进度

## 使用步骤

1. **先定周期**：调用周期列表工具拿到 periodId；用户只说"本季度"时，默认选中当前进行中的周期，并在回答中说明所用周期。
2. **再查目标**：带 periodId 查询目标列表，按用户维度（本人 / 指定人 / 部门）过滤。
3. **对齐关系**：用户想看清"谁支撑谁"时，调用对齐图工具生成图片，并在回答中直接展示。
4. **写操作前确认**：提交 OKR、更新 KR 进度属写操作。调用前复述「周期 + 目标 + 改动内容 + 目标进度值」，得到用户确认后再执行。
5. **结果呈现**：目标列表按「O → 其下 KR → 负责人 → 进度」的层级用 Markdown 列表或表格呈现，不要打平成一段文字。

## 注意事项

- 首次使用需完成钉钉 OAuth 授权；返回 401 / 未授权时引导用户重新登录，不要反复重试。
- 进度类数值以接口返回为准，不要估算或补全缺失字段。
- 提交类操作失败时，原样返回错误原因，不要静默重试第二次。
