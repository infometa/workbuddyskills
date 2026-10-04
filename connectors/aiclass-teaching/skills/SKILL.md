---
name: aiclass-teaching-skill
description: 腾讯未来教室（aiclass）教学服务操作技能
version: "0.1.0"
author: "腾讯未来教室"
---

# 腾讯未来教室 Skill

本 Skill 提供腾讯未来教室（aiclass）教学服务的操作能力。用户安装 Connector 并完成授权后，可通过自然语言调用教学相关工具。

## 可用工具

本 Connector 暴露 3 个工具：

| tool | 作用 | 数据边界 |
| --- | --- | --- |
| get_courses | 查询未来教室课程列表（课程名 + dId） | user_id |
| upload_post | 把 AI 生成的图片以「教学打卡」发布到未来教室小程序 | user_id |
| submit_feedback | 用户对输出结果不满意时，汇总反馈上报后台 | user_id |

## 参数说明

get_courses：无入参。

upload_post：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| course_d_id | string | 是 | 打卡课程 dId，通过 get_courses 查询获得，不要直接让用户提供 |
| images | string[] | 是 | 图片 URL 数组，支持多张 |
| content | string | 否 | 文字说明 |

submit_feedback：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| category | string | 是 | 不满原因分类：content_incorrect / not_expected / incomplete / format_issue / other |
| user_feedback | object | 是 | 用户不满意反馈，字段见下表 |
| skill_name | string | 否 | 当前使用的 skill 名 |
| tool_name | string | 否 | 涉及的 MCP tool 名 |
| error_msg | string | 否 | 简短错误信息（若不满意恰因工具报错） |
| user_query | string | 否 | 用户原始诉求 |
| scenario | string | 否 | 触发场景描述 |
| tool_args | string | 否 | 涉及工具的入参 |
| generated_fragment | string | 否 | 被吐槽的结果片段 |
| attachments | string[] | 否 | 用户补充的截图 URL 列表 |

user_feedback 子字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| summary | string | 是 | 一句话概括用户不满意的核心 |
| points | string[] | 否 | 条目化的具体问题点 |
| raw_dialogue | string | 否 | 多轮对话原文，供追溯 |

## 返回值

| tool | 返回 |
| --- | --- |
| get_courses | `{"courses":[{"d_id":"课程 dId","name":"课程名"}]}` |
| upload_post | `{"post_id":"发布成功的打卡 dId"}` |
| submit_feedback | `{"status":"ok"}` |

## 使用示例

- 上传打卡到指定课程：先调用 get_courses 拿课程列表 → 按用户说的课程名匹配出 dId → 再调用 upload_post(course_d_id, images, content)。
- 用户多次表达「不是我要的结果」后：调用 submit_feedback，category 按实际情况选择，user_feedback.summary 归纳核心不满。

## 错误处理

| 错误提示 | 处理建议 |
| --- | --- |
| 尚未绑定未来教室账号 | 引导用户先完成未来教室绑定 |
| 缺少 course_d_id 或 images | 检查入参，course_d_id 需先通过 get_courses 获取 |
| 反馈参数解析失败 | 检查 category 枚举范围、user_feedback.summary 是否缺失 |
| 查询课程列表失败 / 发布打卡失败 / 反馈提交失败 | 提示稍后重试 |

## 注意事项

- 需要用户完成 MCP 授权后方可使用（联合授权场景下随 Buddy 应用首登一并完成）。
- 如遇到期或未授权错误，提示用户前往设置页重新授权。
- 单次请求超时上限 30 秒，超时请提示用户稍后重试。
