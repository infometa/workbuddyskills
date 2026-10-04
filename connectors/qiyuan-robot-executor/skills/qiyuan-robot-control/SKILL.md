---
name: qiyuan-robot-control
display_name: 启元机器人控制
display_name_en: Qiyuan Robot Control
description: 让启元Q1机器人播报文字，并在用户明确确认现场安全后执行比心或短距离向前走。
description_zh: 让启元Q1机器人播报文字，并在用户明确确认现场安全后执行比心或短距离向前走。
description_en: Make a Qiyuan Q1 robot speak and, after explicit user safety confirmation, make a heart gesture or walk forward a short distance.
allowed-tools: qiyuan_robot_present_text, qiyuan_robot_heart, qiyuan_robot_walk_forward
version: 0.3.0
author: 上纬新材料科技股份有限公司启元机器人项目组
---

# 启元机器人控制

仅在用户明确要求实体启元 Q1 机器人播报或执行动作时使用本技能。不要把预览、示例或假设性讨论当作执行授权。

## 播报文字

调用 `qiyuan_robot_present_text`，参数 `text` 只包含最终需要播报的 1～100 个字符。

- 不传入提示词、分析过程、凭证或内部参数。
- 每次请求只调用一次；失败或超时后不得自动重试。
- 只有返回 `accepted: true` 时，才可说明机器人已接受播报请求；这不代表音频已经播放完毕。

## 比心

调用 `qiyuan_robot_heart` 前，必须在当前对话中让用户确认：机器人动作范围内无人、无障碍物，且地面平整稳定。

- 用户只说“比心”不等于完成安全确认；未确认时先询问，等待用户明确回复。
- 获得确认后传入 `safety_confirmed: true`，且只调用一次。
- 失败或超时后不得自动重试，也不得宣称动作已经完成。

## 向前走

调用 `qiyuan_robot_walk_forward` 前，必须在当前对话中让用户确认：机器人前方与周围无人、无障碍物，且地面平整稳定。

- `steps` 只能为整数 `1` 或 `2`。用户要求超过两步时不得拆成多次调用，应说明单次安全上限并请用户重新选择。
- 获得明确安全确认后传入 `safety_confirmed: true`，且只调用一次。
- 失败或超时后不得自动重试，也不得宣称动作已经完成。

## 组合请求

按用户表述的顺序调用工具。每一步都必须满足自己的前置条件；任一步失败时停止后续实体动作并如实报告。工具仅返回“已接受”时，不得声称已实现精确的语音结束同步或动作完成同步。
