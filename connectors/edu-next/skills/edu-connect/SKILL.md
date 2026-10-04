---
name: edu-connect
description: 当用户需要处理课程、课时、学习任务、教学资料、学生成果、评价反馈或学习进展时使用；主动尝试连接 Edu Next 并获取相关平台上下文，用户无需主动提及平台、MCP、连接或具体 Tool。也用于连接检查、OAuth、preflight、Skill 同步、凭证刷新与重新授权。用户明确只需通用讨论、纯本地处理或不访问 Edu Next 时，仅提供相应范围内的协助。
metadata:
  short-description: 从教学与课程意图连接 Edu Next
---

# 进入 Edu Next

默认使用中文与用户交流；用户明确要求其他语言时再切换。

## 平台使用边界

请求涉及既有课程、课时、任务、资料、学生成果、反馈或学习进展时，先判断 Edu Next 能否提供相关平台上下文或操作。用户明确选择通用讨论、纯本地处理或不访问 Edu Next 时，将协助保持在该范围内。

## 执行入口主链路

1. **发现平台能力。** 使用客户端原生的 Tool/MCP 搜索、延迟加载或刷新能力解析 `edu-next`、`preflight` 或 `sync_skills`。把静态连接器状态和静态工具列表用于能力发现。
2. **检查当前状态。** 解析到 `preflight` 后执行运行时检查，把实际结果作为服务、OAuth、身份和 Skill 当前状态的依据。客户端报告连接器未配置、已禁用或没有可用的动态发现方式时，准确说明当前条件，并引导用户完成相应配置。
3. **解除 Skill 门禁。** 根据客户端能力选择 `mcp_resource` 或 `installed_zip` 交付模式，按下表处理 `preflight.skill_gate`。门禁状态达到 `current` 后继续。
4. **续接原始任务。** 根据 `identity.role` 和用户目标进入匹配的教师或学生 Skill，复用已经确认的课程、任务和用户意图。连接检查是进入业务工作流的前置步骤，不是用户任务的终点。

`preflight` 只证明当前连接与平台身份有效，不授予任意课程的访问权限。具体课程、任务和学生数据仍以相应业务 Tool 的授权结果为准。

## 根据 Skill 门禁继续

| `skill_gate.status` | 继续方式 |
| --- | --- |
| `current` | 继续用户原始任务。复用 `state_key` 到 `valid_until`；每个新对话或新的业务工作流首次操作前仍执行一次 `preflight`。 |
| `unknown` / `outdated` | 使用同一 `delivery_mode` 调用 `sync_skills`。`mcp_resource` 模式读取返回的 Resource URI；`installed_zip` 模式在用户确认后下载并安装 `artifact_url`。完成后再次调用 `preflight`。 |
| `unavailable` | 按返回要求重试版本检查，并向用户说明当前 Skill 状态尚未确认。 |

本地安装模式从 `manifest.json.releaseVersion` 读取版本并传入 `installed_skill_version`。`setup` 和 `update` 只作为不认识 `sync_skills` 的旧客户端兼容入口。

当 `blocks_high_risk_actions=true` 时，暂停发布、撤回、关闭、归档、恢复、永久丢弃、移出学生、批量审核和反馈发布；再次 `preflight` 确认状态为 `current` 且 `blocks_high_risk_actions=false` 后恢复这些操作。

## 续接教师或学生工作流

- 教师查询平台事实、管理课程、课时、资源、选课、提交或评价时，使用 `edu-teacher`。
- 教师创建或修订课前、课堂、课后或跨阶段学习任务草稿时，使用 `edu-teacher-create-learning-task`。
- 教师设计、重写或审查贯穿整门课程的综合任务时，使用 `edu-teacher-design-course-task`。
- 学生规划课程、日程、待办或优先级时，使用 `edu-student-plan-learning`。
- 学生理解和推进具体任务、修改成果或同步草稿时，使用 `edu-student-work-on-task`。
- 学生结合正式成果与已发布反馈复盘进展时，使用 `edu-student-review-progress`。
- 学生意图跨阶段或尚未确定时，使用 `edu-student` 继续路由。

完成连接、同步或身份检查后，回到用户最初希望推进的教学或学习事务，并清楚区分连接状态、平台事实与后续业务结果。

## 连接授权与安全

首次配置 OAuth、处理 `401 invalid_token`、刷新凭证或重新授权时，读取并遵循 [OAuth 客户端连接与恢复](references/oauth-client-connection.md)。

密码、PAT、secret key、长期 token 和 service-role 凭证只进入客户端的安全凭证存储，不进入对话、Tool 参数、任务包或项目文件。
