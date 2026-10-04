---
name: moka-recruiting-ai-tasks
display_name: Moka 招聘专家模式
display_name_en: Moka Recruiting Expert Mode
description: Moka 招聘智能任务工作流。使用当前平台提供的 Moka 连接器发起人才搜索、面试记录分析或面试官表现评估，并持续查询进度直到取得最终结果；也负责在用户明确确认后取消运行中的任务。当用户提出自然语言人才寻访、跨多场面试的分析、面试官质量评估，或追问这些异步任务的进度与结果时使用。
description_zh: 面向招聘负责人与用人团队的智能任务工作流。使用当前平台提供的 Moka 连接器发起人才搜索、面试记录分析或面试官表现评估，并持续查询进度直到取得最终结果；也负责在用户明确确认后取消运行中的任务。当用户提出自然语言人才寻访、跨多场面试的分析、面试官质量评估，或追问这些异步任务的进度与结果时使用。
description_en: AI task workflow for recruiting owners and hiring teams. Launches talent sourcing, interview analysis, or interviewer evaluation tasks through the Moka Connector available on the current platform, keeps polling progress until the final result, and cancels a running task only after the user explicitly confirms. Use it for natural-language talent sourcing, cross-interview analysis, interviewer quality evaluation, or follow-ups on the progress and results of these asynchronous tasks.
category: productivity
version: 1.0.0
author: Moka
---

# Moka 招聘智能任务

把招聘智能任务推进到最终结果。只编排以下四个工具：

- `mcp__moka__search_candidates`
- `mcp__moka__analyze_interviews`
- `mcp__moka__get_recruiting_task_progress`
- `mcp__moka__cancel_recruiting_task`

## 执行规范

不要向用户展示访问令牌、内部标识符、任务句柄或原始技术响应；任务编号和中间过程消息都不是最终答案。

## 选择任务

根据用户目标选择一个发起工具：

- 在企业人才库中按自然语言条件寻找新候选人：使用 `mcp__moka__search_candidates`。
- 对多场历史面试做未通过原因、提问合规、竞品或候选人关注点等分析：使用 `mcp__moka__analyze_interviews`（分析目标保持缺省的面试记录）。
- 评估指定面试官的面试表现：同样使用 `mcp__moka__analyze_interviews`，把分析目标设为面试官（`target="interviewer"`），必须提供 1 至 5 位面试官姓名。

不要用本技能回答已经进入招聘流程的候选人清单、职位详情、招聘需求进度或通知待办。这些问题应由当前可用的其他 Moka 工具处理。

## 发起前

1. 使用 Moka 连接器提供的工具（本技能内的工具名即实际注册名）；连接器未安装或未连接时如实告知用户，不改用其他来源。
2. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
3. 只传用户明确给出的条件，不增加同义词、关联公司、分析维度、职位、日期、面试官或推断条件。
4. 缺少不可推断的必要条件时只问一个关键问题。面试官评估缺少明确姓名时，先询问再发起。
5. 日期范围只在起止日期同时明确时传入；用户没有限定时间时不要自行补时间范围。

## 完成异步任务

1. 调用选定的发起工具，先检查 `blockers`、`taskStatus` 与 `nextAction`。发起阶段返回 `OTHER_COMPLETED` 表示任务未能启动，应如实说明并停止，不进入轮询。
2. 只有任务成功进入运行态时，才保存返回的 `taskId` 与 `sessionId`。
3. 立即调用 `mcp__moka__get_recruiting_task_progress`，首次使用 `cursor=0`。
4. 任务未结束时，按返回的重试提示等待，再使用 `nextCursor` 继续查询。
5. 持续查询，直到状态进入 `COMPLETED`、`OTHER_COMPLETED`、`FAIL`、`CANCELLED` 或 `OTHER_CANCELLED`。轮询阶段的 `OTHER_COMPLETED` 是正常完成状态，按返回的 result 交付结果。
6. 成功时交付最终候选人结果或分析报告；失败或取消时如实说明终态和工具提供的原因。不要把“任务已发起”、任务编号或过程消息当作最终答案。

同一轮进度查询失败时，保留原 cursor 按工具的 retryable/retryAfterMs 提示重试；只有成功取得新结果后才改用 `nextCursor`。

## 处理补充条件

- 发起工具返回 `blockers` 时，向用户询问缺少的信息；补齐后重新调用对应发起工具，产生一个新任务。
- 不要用旧任务的 `taskId` 或 `sessionId` 伪装成已经补充条件。
- 用户追问“刚才的任务怎么样了”时，沿用当前会话中最近一次相关任务的句柄继续查询，不重复发起。

## 取消任务

取消会改变任务状态。只有用户明确要求停止或明确确认取消后，才把发起工具返回的 `sessionId` 传给 `mcp__moka__cancel_recruiting_task`。未获确认时继续查询进度或询问用户，不要擅自取消。

## 结果与权限

- `NOT_ACTIVATED`：当前无可用权益——企业未开通该能力，或当日免费体验次数已用完。逐字转达工具返回的 message，不改写、不弱化，也不追加自行设想的开通路径或替代方案；当天内不要重复发起。
- `MODULE_UNAVAILABLE`：企业已开通但可用额度不足，重试不会恢复。逐字转达工具返回的 message（含其给出的充值引导），不重复发起，也不把它说成未开通。
- `NO_PERMISSION`：当前账号的招聘角色无法使用该功能（该功能可能仅面向 HR 角色开放）。如实转达工具返回的 message，不绕过、不改用其他身份，也不重复发起。
- `EMPTY`：说明当前条件下没有结果，不解释为无权限。
- 任务运行中失败（`FAIL`）：如实说明终态和工具提供的原因（包括运行中途额度不足导致的中断），不把任务编号或中间过程消息当作结果交付。
- 其他失败：按工具返回的 retryable/retryAfterMs 决定是否重试，不根据公开文案猜测技术根因。

输出先给结论，再给关键依据。候选人结果只使用工具返回的字段；分析报告忠实呈现结果，不补写不存在的事实。
